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
"""Locking interfaces"""
from zope.interface.interfaces import IObjectEvent
from zope.interface.interfaces import ObjectEvent

from zope import interface
from zope import schema


##############################################################################
# Token utility
##############################################################################


class ITokenUtility(interface.Interface):
    """Responsible for initializing, registering, and finding all active tokens
    """

    def get(obj, default=None):
        """For obj, return active IToken or default.

        Token must be active (not ended), or else return default.
        """

    def iterForPrincipalId(principal_id):
        """Return an iterable of all active tokens held by the principal id.
        """

    def __iter__():
        """Return iterable of active tokens managed by utility.
        """

    def register(token):
        """register an IToken, or a change to a previously-registered token.

        If the token has not yet been assigned a `utility` value, sets the
        `utility` attribute of the token to self, to mark registration.
        Raises ValueError if token has been registered to another utility.

        If lock has never been registered before, fires TokenStartedEvent.
        """


##############################################################################
# General (abstract) token interfaces
##############################################################################


class IAbstractToken(interface.Interface):
    """A token.  Must be registered with token utility to start.

    This is the core token interface.  This core interface is mostly readonly.
    It is used as a base by both tokens and token handlers.
    """

    __parent__ = interface.Attribute(
        """the security context for the token.""")

    context = interface.Attribute(
        """the actual locked object.  readonly.""")

    utility = interface.Attribute(
        """The lock utility in charge of this lock.

        Should *only* ever be set once by ILockUtility.register method.
        When the utility sets this attribute, the `start` attribute should
        be set and the token should be considered active (potentially; see
        IEndable).""")

    principal_ids = interface.Attribute(
        """An immutable iterable of the principal ids that own the lock;
        or None if the object is not locked.   If object is frozen, returns
        an iterable with no members.  Readonly.""")

    started = schema.Datetime(
        description=("""the date and time, with utc timezone, that the token
        was registered with the token utility and became effective.  Required
        after the token has been registered."""),
        required=False, readonly=True)


class IEndable(interface.Interface):
    """A mixin for tokens that may be ended explicitly or timed out.

    Some tokens are endable; locks, for instance, are endable.  Freezes may be
    permanent, so some are not IEndable.
    """

    ended = schema.Datetime(
        description=("""the date and time, with utc timezone, that the token
        ended, explicitly or from expiration."""),
        required=False, readonly=True)

    expiration = schema.Datetime(
        description=(
            """the expiration time, with utc timezone.
            None indicates no expiration.
            Readonly (but see extending interfaces).
            """),
        required=False)

    duration = schema.Timedelta(
        description=(
            """the duration of the token timeout from its start.
            None indicates no expiration.
            Readonly (but see extending interfaces).
            """),
        required=False)

    remaining_duration = schema.Timedelta(
        description=(
            """the remaining effective duration for the token from "now".
            None indicates no expiration.  If the token has ended, return
            a datetime.timedelta of no time.
            Readonly (but see extending interfaces).
            """),
        required=False)

    def end():
        """explicitly expire the token.

        fires TokenEndedEvent if successful, or raises EndedError
        if the token has already ended."""


##############################################################################
# Token interfaces: registered by token utility
##############################################################################

# Abstract token interfaces


class IToken(IAbstractToken):
    """a token that actually stores data.

    This is the sort of token that should be used in the token utility."""

    __parent__ = interface.Attribute(
        """the locked object.  readonly.  Important for security.""")

    annotations = interface.Attribute(
        """Stores arbitrary application data under package-unique keys.

        By "package-unique keys", we mean keys that are are unique by
        virtue of including the dotted name of a package as a prefix.  A
        package name is used to limit the authority for picking names for
        a package to the people using that package.
        """)


class IEndableToken(IToken, IEndable):
    """A standard endable token."""

    expiration = schema.Datetime(
        description=(
            """the expiration time, with utc timezone.
            None indicates no expiration.
            When setting, if token has ended then raise EndedError.
            Otherwise call utility.register, fire ExpirationChangedEvent.
            """),
        required=False)

    duration = schema.Timedelta(
        description=(
            """the duration of the token timeout from its start.
            None indicates no expiration.
            When setting, if token has ended then raise EndedError.
            Otherwise call utility.register, fire ExpirationChangedEvent.
            """),
        required=False)

    remaining_duration = schema.Timedelta(
        description=(
            """the remaining effective duration for the token from "now".
            None indicates no expiration.  If the token has ended, return
            a datetime.timedelta of no time.
            When setting, if token has ended then raise EndedError.
            Otherwise call utility.register, fire ExpirationChangedEvent.
            """),
        required=False)


# Concrete token interfaces


class IExclusiveLock(IEndableToken):
    """a lock held to one and only one principal.

    principal_ids must always have one and only one member."""


class ISharedLock(IEndableToken):
    "a lock held by one or more principals"

    def add(principal_ids):
        """Share this lock with principal_ids.

        Adding principals that already are part of the lock can be ignored.

        If ended, raise EndedError.
        """

    def remove(principal_ids):
        """Remove principal_ids from lock.

        Removing all principals removes the lock: there may not be an effective
        shared lock shared to no one.

        Removing principals that are not part of the lock can be ignored.

        If ended, raise EndedError."""


class IFreeze(IToken):
    """principal_ids must always be empty.

    May not be ended."""


class IEndableFreeze(IFreeze, IEndableToken):
    """May be ended."""


##############################################################################
# Token broker interface
##############################################################################


class ITokenBroker(interface.Interface):
    """for one object, create standard endable tokens and get active ITokens.

    Convenient adapter model for security: broker is in context of affected
    object, so security settings for the object can be obtained automatically.
    """

    context = interface.Attribute(
        'The object whose tokens are brokered.  readonly.')

    __parent__ = interface.Attribute(
        """the context.  readonly.  Important for security.""")

    def lock(principal_id=None, duration=None):
        """lock context, and return token.

        if principal_id is None, use interaction's principal; if interaction
        does not have one and only one principal, raise ValueError.

        if principal_id is not None, principal_id must be in interaction,
        or else raise ParticipationError.

        Same constraints as token utility's register method.
        """

    def lockShared(principal_ids=None, duration=None):
        """lock context with a shared lock, and return token.

        if principal_ids is None, use interaction's principals; if interaction
        does not have any principals, raise ValueError.

        if principal_ids is not None, principal_ids must be in interaction,
        or else raise ParticipationError.  Must be at least one id.

        Same constraints as token utility's register method.
        """

    def freeze(duration=None):
        """freeze context with an endable freeze, and return token.
        """

    def get():
        """Get context's active IToken, or None.

        """

##############################################################################
# Token handler interfaces
##############################################################################

# Abstract token handler interfaces.


class ITokenHandler(IAbstractToken, IEndable):
    """give appropriate increased access in a security system.

    Appropriate for endable tokens with one or more principals (for instance,
    neither freezes nor endable freezes."""

    __parent__ = interface.Attribute(
        """the actual token.  readonly.  Important for security.""")

    token = interface.Attribute(
        """the registered IToken that this adapter uses for actual
        data storage""")

    expiration = schema.Datetime(
        description=(
            """the expiration time, with utc timezone.
            None indicates no expiration.
            When setting, if token has ended then raise EndedError.
            If all of the principals in the current interaction are not owners
            of the current token (in principal_ids), raise ParticipationError.
            Otherwise call utility.register, fire ExpirationChangedEvent.
            """),
        required=False)

    duration = schema.Timedelta(
        description=(
            """the duration of the token timeout from its start.
            None indicates no expiration.
            When setting, if token has ended then raise EndedError.
            If all of the principals in the current interaction are not owners
            of the current token (in principal_ids), raise ParticipationError.
            Otherwise call utility.register, fire ExpirationChangedEvent.
            """),
        required=False)

    remaining_duration = schema.Timedelta(
        description=(
            """the remaining effective duration for the token from "now".
            None indicates no expiration.  If the token has ended, return
            a datetime.timedelta of no time.
            When setting, if token has ended then raise EndedError.
            If all of the principals in the current interaction are not owners
            of the current token (in principal_ids), raise ParticipationError.
            Otherwise call utility.register, fire ExpirationChangedEvent.
            """),
        required=False)

    def release(principal_ids=None):  # may only remove ids in interaction.
        """Remove given principal_ids from the token, or all in interaction.

        All explicitly given principal_ids must be in interaction.  Silently
        ignores requests to remove principals who are not currently part of
        token.

        Ends the lock if the removed principals were the only principals.

        Raises EndedError if lock has already ended.
        """


# Concrete principal token interfaces.


class IExclusiveLockHandler(ITokenHandler):
    """an exclusive lock"""


class ISharedLockHandler(ITokenHandler):
    """a shared lock"""

    def join(principal_ids=None):
        """add the given principal_ids to the token, or all in interaction.
        All explicitly given principal_ids must be in interaction.  Silently
        ignores requests to add principal_ids that are already part of the
        token.

        Raises EndedError if lock has already ended.
        """

    def add(principal_ids):
        """Share current shared lock with principal_ids.
        If all of the principals in the current interaction are not owners
        of the current token (in principal_ids), raise ParticipationError."""


##############################################################################
# Events
##############################################################################

# event interfaces


class ITokenEvent(IObjectEvent):
    """a token event"""


class ITokenStartedEvent(ITokenEvent):
    """An token has started"""


class ITokenEndedEvent(ITokenEvent):
    """A token has been explicitly ended.

    Note that this is not fired when a lock expires."""


class IPrincipalsChangedEvent(ITokenEvent):
    """Principals have changed for a token"""

    old = interface.Attribute('a frozenset of the old principals')


class IExpirationChangedEvent(ITokenEvent):
    """Expiration value changed for a token"""

    old = interface.Attribute('the old expiration value')


# events


@interface.implementer(ITokenStartedEvent)
class TokenStartedEvent(ObjectEvent):
    pass


@interface.implementer(ITokenEndedEvent)
class TokenEndedEvent(ObjectEvent):
    pass


@interface.implementer(IPrincipalsChangedEvent)
class PrincipalsChangedEvent(ObjectEvent):
    def __init__(self, object, old):
        super().__init__(object)
        self.old = frozenset(old)


@interface.implementer(IExpirationChangedEvent)
class ExpirationChangedEvent(ObjectEvent):
    def __init__(self, object, old):
        super().__init__(object)
        self.old = old


##############################################################################
# Exceptions
##############################################################################


class TokenRuntimeError(RuntimeError):
    """A general runtime error in the token code."""


class EndedError(TokenRuntimeError):
    """The token has ended"""


class UnregisteredError(TokenRuntimeError):
    """The token has not yet been registered"""


class ParticipationError(TokenRuntimeError):
    """Some or all of the principals in the current interaction do not
    participate in the token"""


class RegistrationError(TokenRuntimeError):
    """The token may not be registered"""
