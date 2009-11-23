import BTrees.OOBTree
import zope.interface
import zope.app.generations.interfaces

import zope.locking.interfaces

class SchemaManager(object):

    zope.interface.implements(
        zope.app.generations.interfaces.IInstallableSchemaManager)

    minimum_generation = 1
    generation = 1

    def install(self, context):
        # Clean up cruft in any existing token utilities.
        # This is done here because zope.locking didn't have a
        # schema manager prior to 1.2.
        app = context.connection.root().get('Application')
        if app is not None:
            for util in find_token_utilities(app):
                fix_token_utility(util)

    def evolve(self, context, generation):
        pass


schemaManager = SchemaManager()

def get_site_managers(app_root):
    def _get_site_managers(sm):
        yield sm
        for sm in sm.subs:
            for _sm in _get_site_managers(sm):
                yield _sm
    return _get_site_managers(app_root.getSiteManager())


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
    for dt, tree in list(util._expirations.items()):
        util._expirations[dt] = BTrees.OOBTree.OOTreeSet(tree)
