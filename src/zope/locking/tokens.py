import persistent
import datetime
from BTrees.OOBTree import OOBTree

from zope import interface, component, event

from zope.locking import interfaces, utils
from zope.locking.i18n import _

NO_DURATION = datetime.timedelta()

class AnnotationsMapping(OOBTree):
    "a class on which security settings may be hung"

class Token(persistent.Persistent):

    def __init__(self, target):
        self.context = self.__parent__ = target
        self.annotations = AnnotationsMapping()
        self.annotations.__parent__ = self # for security

    _principal_ids = frozenset()
    @property
    def principal_ids(self):
        return self._principal_ids

    _started = None
    @property
    def started(self):
        if self._utility is None:
            raise interfaces.UnregisteredError(self)
        return self._started

    _utility = None
    @apply
    def utility():
        def get(self):
            return self._utility
        def set(self, value):
            if self._utility is not None:
                if value is not self._utility:
                    raise ValueError('cannot reset utility')
            else:
                assert interfaces.ITokenUtility.providedBy(value)
                self._utility = value
                assert self._started is None
                self._started = utils.now()
        return property(get, set)


class EndableToken(Token):

    def __init__(self, target, duration=None):
        super(EndableToken, self).__init__(target)
        self._duration = duration

    @apply
    def utility():
        def get(self):
            return self._utility
        def set(self, value):
            if self._utility is not None:
                if value is not self._utility:
                    raise ValueError('cannot reset utility')
            else:
                assert interfaces.ITokenUtility.providedBy(value)
                self._utility = value
                assert self._started is None
                self._started = utils.now()
                if self._duration is not None:
                    self._expiration = self._started + self._duration
                    del self._duration # to catch bugs
        return property(get, set)

    _expiration = _duration = None
    @apply
    def expiration():
        def get(self):
            if self._started is None:
                raise interfaces.UnregisteredError(self)
            return self._expiration
        def set(self, value):
            if self._started is None:
                raise interfaces.UnregisteredError(self)
            if self.ended:
                raise interfaces.EndedError
            if value is not None:
                if not isinstance(value, datetime.datetime):
                    raise ValueError('expiration must be datetime.datetime')
                elif value.tzinfo is None:
                    raise ValueError('expiration must be timezone-aware')
            old = self._expiration
            self._expiration = value
            if old != self._expiration:
                self.utility.register(self)
                event.notify(interfaces.ExpirationChangedEvent(self, old))
        return property(get, set)

    @apply
    def duration():
        def get(self):
            if self._started is None:
                return self._duration
            if self._expiration is None:
                return None
            return self._expiration - self._started
        def set(self, value):
            if self._started is None:
                self._duration = value
            else:
                if self.ended:
                    raise interfaces.EndedError
                old = self._expiration
                if value is None:
                    self._expiration = value
                elif not isinstance(value, datetime.timedelta):
                    raise ValueError('duration must be datetime.timedelta')
                else:
                    if value < NO_DURATION:
                        raise ValueError('duration may not be negative')
                    self._expiration = self._started + value
                if old != self._expiration:
                    self.utility.register(self)
                    event.notify(interfaces.ExpirationChangedEvent(self, old))
        return property(get, set)

    @apply
    def remaining_duration():
        def get(self):
            if self._started is None:
                raise interfaces.UnregisteredError(self)
            if self.ended is not None:
                return NO_DURATION
            if self._expiration is None:
                return None
            return self._expiration - utils.now()
        def set(self, value):
            if self._started is None:
                raise interfaces.UnregisteredError(self)
            if self.ended:
                raise interfaces.EndedError
            old = self._expiration
            if value is None:
                self._expiration = value
            elif not isinstance(value, datetime.timedelta):
                raise ValueError('duration must be datetime.timedelta')
            else:
                if value < NO_DURATION:
                    raise ValueError('duration may not be negative')
                self._expiration = utils.now() + value
            if old != self._expiration:
                self.utility.register(self)
                event.notify(interfaces.ExpirationChangedEvent(self, old))
        return property(get, set)

    _ended = None
    @property
    def ended(self):
        if self._utility is None:
            raise interfaces.UnregisteredError(self)
        if self._ended is not None:
            return self._ended
        if (self._expiration is not None and
            self._expiration <= utils.now()):
            return self._expiration

    def end(self):
        if self.ended:
            raise interfaces.EndedError
        self._ended = utils.now()
        self.utility.register(self)
        event.notify(interfaces.TokenEndedEvent(self))

class ExclusiveLock(EndableToken):
    interface.implements(interfaces.IExclusiveLock)

    def __init__(self, target, principal_id, duration=None):
        self._principal_ids = frozenset((principal_id,))
        super(ExclusiveLock, self).__init__(target, duration)

class SharedLock(EndableToken):
    interface.implements(interfaces.ISharedLock)

    def __init__(self, target, principal_ids, duration=None):
        self._principal_ids = frozenset(principal_ids)
        super(SharedLock, self).__init__(target, duration)

    def add(self, principal_ids):
        if self.ended:
            raise interfaces.EndedError
        old = self._principal_ids
        self._principal_ids = self._principal_ids.union(principal_ids)
        if old != self._principal_ids:
            self.utility.register(self)
            event.notify(interfaces.PrincipalsChangedEvent(self, old))

    def remove(self, principal_ids):
        if self.ended:
            raise interfaces.EndedError
        old = self._principal_ids
        self._principal_ids = self._principal_ids.difference(principal_ids)
        if not self._principal_ids:
            self.end()
        elif old != self._principal_ids:
            self.utility.register(self)
        else:
            return
        # principals changed if you got here
        event.notify(interfaces.PrincipalsChangedEvent(self, old))

class EndableFreeze(EndableToken):
    interface.implements(interfaces.IEndableFreeze)

class Freeze(Token):
    interface.implements(interfaces.IFreeze)
