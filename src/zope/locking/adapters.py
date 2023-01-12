##############################################################################
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

import zope.security.management

from zope import component
from zope import interface
from zope.locking import interfaces
from zope.locking import tokens


@component.adapter(interface.Interface)
@interface.implementer(interfaces.ITokenBroker)
class TokenBroker:

    def __init__(self, context):
        self.context = self.__parent__ = context
        self.utility = component.getUtility(
            interfaces.ITokenUtility, context=context)

    # for subclasses to call, to avoid duplicating code
    def _getLockPrincipalId(self, principal_id):
        interaction_principals = getInteractionPrincipals()
        if principal_id is None:
            if (interaction_principals is None
                    or len(interaction_principals) != 1):
                raise ValueError
            principal_id = next(iter(interaction_principals))
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
            if (interaction_principals is None
                    or len(interaction_principals) < 1):
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
        return {p.principal.id for p in interaction.participations}


class TokenHandler:
    def __init__(self, token):
        self.__parent__ = self.token = token

    def __getattr__(self, name):
        return getattr(self.token, name)

    def _checkInteraction(self):
        if self.token.ended is not None:
            raise interfaces.ExpirationChangedEvent
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

    @property
    def expiration(self):
        return self.token.expiration

    @expiration.setter
    def expiration(self, value):
        self._checkInteraction()
        self.token.expiration = value

    @property
    def duration(self):
        return self.token.duration

    @duration.setter
    def duration(self, value):
        self._checkInteraction()
        self.token.duration = value

    @property
    def remaining_duration(self):
        return self.token.remaining_duration

    @remaining_duration.setter
    def remaining_duration(self, value):
        self._checkInteraction()
        self.token.remaining_duration = value

    def release(self, principal_ids=None):
        raise NotImplementedError


@component.adapter(interfaces.IExclusiveLock)
@interface.implementer(interfaces.IExclusiveLockHandler)
class ExclusiveLockHandler(TokenHandler):

    def release(self, principal_ids=None):
        pids, interaction_pids, token_pids = self._getPrincipalIds(
            principal_ids)
        remaining = token_pids.difference(pids)
        if not remaining:
            self.token.end()


@component.adapter(interfaces.ISharedLock)
@interface.implementer(interfaces.ISharedLockHandler)
class SharedLockHandler(TokenHandler):

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
