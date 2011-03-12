from zope import interface, component

import zope.security.management

from zope.locking import interfaces, tokens

class TokenBroker(object):
    component.adapts(interface.Interface)
    interface.implements(interfaces.ITokenBroker)

    def __init__(self, context):
        self.context = self.__parent__ = context
        self.utility = component.getUtility(
            interfaces.ITokenUtility, context=context)

    # for subclasses to call, to avoid duplicating code
    def _getLockPrincipalId(self, principal_id):
        interaction_principals = getInteractionPrincipals()
        if principal_id is None:
            if (interaction_principals is None or
                len(interaction_principals) != 1):
                raise ValueError
            principal_id = iter(interaction_principals).next()
        elif (interaction_principals is None or
              principal_id not in interaction_principals):
            raise interfaces.ParticipationError
        return principal_id

    def lock(self, principal_id=None, duration=None):
        principal_id = self._getLockPrincipalId(principal_id)
        return self.utility.register(
            tokens.ExclusiveLock(self.context, principal_id, duration))

    # for subclasses to call, to avoid duplicating code
    def _getSharedLockPrincipalIds(self, principal_ids):
        interaction_principals = getInteractionPrincipals()
        if principal_ids is None:
            if (interaction_principals is None or
                len(interaction_principals) < 1):
                raise ValueError
            principal_ids = interaction_principals
        elif (interaction_principals is None or
              set(principal_ids).difference(interaction_principals)):
            raise interfaces.ParticipationError
        return principal_ids

    def lockShared(self, principal_ids=None, duration=None):
        principal_ids = self._getSharedLockPrincipalIds(principal_ids)
        return self.utility.register(
            tokens.SharedLock(self.context, principal_ids, duration))

    def freeze(self, duration=None):
        return self.utility.register(
            tokens.EndableFreeze(self.context, duration))

    def get(self):
        return self.utility.get(self.context)

def getInteractionPrincipals():
    interaction = zope.security.management.queryInteraction()
    if interaction is not None:
        return set(p.principal.id for p in interaction.participations)
    # return None

class TokenHandler(object):
    def __init__(self, token):
        self.__parent__ = self.token = token

    def __getattr__(self, name):
        return getattr(self.token, name)

    def _checkInteraction(self):
        if self.token.ended is not None:
            raise interfaces.EndedError
        interaction_principals = getInteractionPrincipals()
        token_principals = frozenset(self.token.principal_ids)
        if interaction_principals is not None:
            omitted = interaction_principals.difference(token_principals)
            if omitted:
                raise interfaces.ParticipationError(omitted)
        return interaction_principals, token_principals

    def _getPrincipalIds(self, principal_ids):
        interaction_principals, token_principals = self._checkInteraction()
        if principal_ids is None:
            principal_ids = interaction_principals or ()
        else:
            for p in principal_ids:
                if p not in interaction_principals:
                    raise ValueError(p)
        return principal_ids, interaction_principals, token_principals

    @apply
    def expiration():
        def get(self):
            return self.token.expiration
        def set(self, value):
            self._checkInteraction()
            self.token.expiration = value
        return property(get, set)

    @apply
    def duration():
        def get(self):
            return self.token.duration
        def set(self, value):
            self._checkInteraction()
            self.token.duration = value
        return property(get, set)

    @apply
    def remaining_duration():
        def get(self):
            return self.token.remaining_duration
        def set(self, value):
            self._checkInteraction()
            self.token.remaining_duration = value
        return property(get, set)

    def release(self, principal_ids=None):
        raise NotImplementedError

class ExclusiveLockHandler(TokenHandler):
    component.adapts(interfaces.IExclusiveLock)
    interface.implements(interfaces.IExclusiveLockHandler)

    def release(self, principal_ids=None):
        pids, interaction_pids, token_pids = self._getPrincipalIds(
            principal_ids)
        remaining = token_pids.difference(pids)
        if not remaining:
            self.token.end()

class SharedLockHandler(TokenHandler):
    component.adapts(interfaces.ISharedLock)
    interface.implements(interfaces.ISharedLockHandler)

    def release(self, principal_ids=None):
        pids, interaction_pids, token_pids = self._getPrincipalIds(
            principal_ids)
        self.token.remove(pids)

    def join(self, principal_ids=None):
        interaction_principals = getInteractionPrincipals()
        if principal_ids is None:
            if interaction_principals is None:
                raise ValueError
            principal_ids = interaction_principals
        elif set(principal_ids).difference(interaction_principals):
            raise interfaces.ParticipationError
        self.token.add(principal_ids)

    def add(self, principal_ids):
        self._checkInteraction()
        self.token.add(principal_ids)
