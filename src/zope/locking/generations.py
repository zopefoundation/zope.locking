import BTrees.OOBTree
import zope.app.generations.interfaces
import zope.interface
import zope.keyreference.interfaces
import zope.locking.interfaces
import zope.locking.utils


class SchemaManager(object):

    zope.interface.implements(
        zope.app.generations.interfaces.IInstallableSchemaManager)

    minimum_generation = 3
    generation = 3

    def install(self, context):
        # Clean up cruft in any existing token utilities.
        # This is done here because zope.locking didn't have a
        # schema manager prior to 1.2.
        clean_locks(context)

    def evolve(self, context, generation):
        if generation <= 2:
            # Going from generation 1 -> 2, we need to run the token
            # utility fixer again because of a deficiency it had in 1.2.
            clean_locks(context)


schemaManager = SchemaManager()

def get_site_managers(app_root):
    def _get_site_managers(sm):
        yield sm
        for sm in sm.subs:
            for _sm in _get_site_managers(sm):
                yield _sm
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
        new_tree = BTrees.OOBTree.OOTreeSet()
        for token in util.iterForPrincipalId(pid):
            new_tree.add(zope.keyreference.interfaces.IKeyReference(token))
        if new_tree:
            util._principal_ids[pid] = new_tree
        else:
            del util._principal_ids[pid]
    now = zope.locking.utils.now()
    for dt, tree in list(util._expirations.items()):
        if dt > now:
            new_tree = BTrees.OOBTree.OOTreeSet()
            for token in tree:
                new_tree.add(zope.keyreference.interfaces.IKeyReference(token))
            util._expirations[dt] = new_tree
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
