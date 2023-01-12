#############################################################################
#
# Copyright (c) 2018 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import BTrees.OOBTree
import zope.generations.interfaces
import zope.interface

import zope.locking.interfaces
import zope.locking.utils


@zope.interface.implementer(
    zope.generations.interfaces.IInstallableSchemaManager)
class SchemaManager:
    minimum_generation = 2
    generation = 2

    def install(self, context):
        # Clean up cruft in any existing token utilities.
        # This is done here because zope.locking didn't have a
        # schema manager prior to 1.2.
        clean_locks(context)

    def evolve(self, context, generation):
        if generation == 2:
            # Going from generation 1 -> 2, we need to run the token
            # utility fixer again because of a deficiency it had in 1.2.
            clean_locks(context)


schemaManager = SchemaManager()


def get_site_managers(app_root):
    def _get_site_managers(sm):
        yield sm
        for sm in sm.subs:
            yield from _get_site_managers(sm)
    return _get_site_managers(app_root.getSiteManager())


def clean_locks(context):
    """Clean out old locks from token utilities."""
    app = context.connection.root().get('Application')
    if app is not None:
        for util in find_token_utilities(app):
            fix_token_utility(util)


def find_token_utilities(app_root):
    for sm in get_site_managers(app_root):
        for registration in sm.registeredUtilities():
            if registration.provided is zope.locking.interfaces.ITokenUtility:
                yield registration.component


def fix_token_utility(util):
    """ A bug in versions of zope.locking prior to 1.2 could cause
        token utilities to keep references to expired/ended locks.

        This function cleans up any old locks lingering in a token
        utility due to this issue.
    """
    for pid in list(util._principal_ids):
        # iterForPrincipalId only returns non-ended locks, so we know
        # they're still good.
        new_tree = BTrees.OOBTree.OOTreeSet(util.iterForPrincipalId(pid))
        if new_tree:
            util._principal_ids[pid] = new_tree
        else:
            del util._principal_ids[pid]
    now = zope.locking.utils.now()
    for dt, tree in list(util._expirations.items()):
        if dt > now:
            util._expirations[dt] = BTrees.OOBTree.OOTreeSet(tree)
        else:
            del util._expirations[dt]
            for token in tree:
                # Okay, we could just adapt token.context to IKeyReference
                # here...but we don't want to touch token.context,
                # because some wonky objects need a site set before
                # they can be unpickled.
                for key_ref, (_token, _, _) in list(util._locks.items()):
                    if token is _token:
                        del util._locks[key_ref]
                        break
