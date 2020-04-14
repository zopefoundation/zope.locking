This file is for annoying tests that were not appropriate for the README but
should be included for completeness.

This is some setup that the tests need.

    >>> from zope.locking import utility, interfaces, tokens
    >>> util = utility.TokenUtility()
    >>> from zope.interface.verify import verifyObject
    >>> verifyObject(interfaces.ITokenUtility, util)
    True

    >>> from zope import interface, component

    >>> conn = get_connection()
    >>> conn.add(util)

    >>> import datetime
    >>> import pytz
    >>> before_creation = datetime.datetime.now(pytz.utc)
    >>> from zope.locking.testing import Demo
    >>> demo = Demo()

----------------------------------
Timed Expirations for Shared Locks
----------------------------------

Timed expirations work the same as with exclusive locks.

    >>> one = datetime.timedelta(hours=1)
    >>> two = datetime.timedelta(hours=2)
    >>> three = datetime.timedelta(hours=3)
    >>> four = datetime.timedelta(hours=4)

    >>> lock = util.register(
    ...     tokens.SharedLock(demo, ('john', 'mary'), duration=three))
    >>> lock.duration
    datetime.timedelta(seconds=10800)
    >>> three >= lock.remaining_duration >= two
    True
    >>> lock.expiration == lock.started + lock.duration
    True
    >>> ((before_creation + three) <=
    ...  (lock.expiration) <=
    ...  (before_creation + four))
    True
    >>> lock.ended is None
    True
    >>> util.get(demo) is lock
    True
    >>> list(util.iterForPrincipalId('john')) == [lock]
    True
    >>> list(util.iterForPrincipalId('mary')) == [lock]
    True
    >>> list(util) == [lock]
    True

Again, expirations can be changed while a lock is still active, using any of
the `expiration`, `remaining_duration` or `duration` attributes.  All changes
fire events.  First we'll change the expiration attribute.

    >>> lock.expiration = lock.started + one
    >>> lock.expiration == lock.started + one
    True
    >>> lock.duration == one
    True
    >>> from zope.component.eventtesting import events
    >>> ev = events[-1]
    >>> verifyObject(interfaces.IExpirationChangedEvent, ev)
    True
    >>> ev.object is lock
    True
    >>> ev.old == lock.started + three
    True

Next we'll change the duration attribute.

    >>> lock.duration = four
    >>> lock.duration
    datetime.timedelta(seconds=14400)
    >>> four >= lock.remaining_duration >= three
    True
    >>> ev = events[-1]
    >>> verifyObject(interfaces.IExpirationChangedEvent, ev)
    True
    >>> ev.object is lock
    True
    >>> ev.old == lock.started + one
    True

Now we'll hack our code to make it think that it is two hours later, and then
check and modify the remaining_duration attribute.

    >>> def hackNow():
    ...     return (datetime.datetime.now(pytz.utc) +
    ...             datetime.timedelta(hours=2))
    ...
    >>> import zope.locking.utils
    >>> oldNow = zope.locking.utils.now
    >>> zope.locking.utils.now = hackNow # make code think it's 2 hours later
    >>> lock.duration
    datetime.timedelta(seconds=14400)
    >>> two >= lock.remaining_duration >= one
    True
    >>> lock.remaining_duration -= datetime.timedelta(hours=1)
    >>> one >= lock.remaining_duration >= datetime.timedelta()
    True
    >>> three + datetime.timedelta(minutes=1) >= lock.duration >= three
    True
    >>> ev = events[-1]
    >>> verifyObject(interfaces.IExpirationChangedEvent, ev)
    True
    >>> ev.object is lock
    True
    >>> ev.old == lock.started + four
    True

Now, we'll hack our code to make it think that it's a day later.  It is very
important to remember that a lock ending with a timeout ends silently--that
is, no event is fired.

    >>> def hackNow():
    ...     return (
    ...         datetime.datetime.now(pytz.utc) + datetime.timedelta(days=1))
    ...
    >>> zope.locking.utils.now = hackNow # make code think it is a day later
    >>> lock.ended >= lock.started
    True
    >>> util.get(demo) is None
    True
    >>> lock.remaining_duration == datetime.timedelta()
    True
    >>> list(util.iterForPrincipalId('john')) == []
    True
    >>> list(util.iterForPrincipalId('mary')) == []
    True
    >>> list(util) == []
    True
    >>> lock.end()
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.EndedError

Once a lock has ended, the timeout can no longer be changed.

    >>> lock.duration = datetime.timedelta(days=2)
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.EndedError

We'll undo the hacks, and also end the lock (that is no longer ended once
the hack is finished).

    >>> zope.locking.utils.now = oldNow # undo the hack
    >>> lock.end()

--------------
EndableFreezes
--------------

An endable freeze token is similar to a lock token except that it grants the
'lock' to no one.

    >>> token = util.register(tokens.EndableFreeze(demo))
    >>> ev = events[-1]
    >>> verifyObject(interfaces.ITokenStartedEvent, ev)
    True
    >>> ev.object is token
    True
    >>> sorted(token.principal_ids)
    []

Freezes are otherwise identical to exclusive locks.

The returned token implements IEndableFreeze and provides the same
capabilities as IExclusiveLock.

    >>> verifyObject(interfaces.IEndableFreeze, token)
    True
    >>> token.context is demo
    True
    >>> token.__parent__ is demo # important for security
    True
    >>> token.utility is util
    True
    >>> token.ended is None
    True
    >>> before_creation <= token.started <= datetime.datetime.now(pytz.utc)
    True
    >>> token.expiration is None
    True
    >>> token.duration is None
    True
    >>> token.remaining_duration is None
    True
    >>> token.end()
    >>> token.ended >= token.started
    True
    >>> util.get(demo) is None
    True

Once a token is created, the token utility knows about it.  Notice that an
EndableFreeze will never be a part of an iterable of tokens by principal: by
definition, a freeze is associated with no principals.

    >>> token = util.register(tokens.EndableFreeze(demo))
    >>> util.get(demo) is token
    True
    >>> list(util) == [token]
    True

As part of that knowledge, it disallows another lock or freeze on the same
object.

    >>> util.register(tokens.ExclusiveLock(demo, 'mary'))
    ... # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.RegistrationError: ...
    >>> util.register(tokens.SharedLock(demo, ('mary', 'jane')))
    ... # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.RegistrationError: ...
    >>> util.register(tokens.EndableFreeze(demo))
    ... # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.RegistrationError: ...
    >>> token.end()
    >>> util.get(demo) is None
    True

The other way of ending a token is with an expiration datetime.  As we'll see,
one of the most important caveats about working with timeouts is that a token
that expires because of a timeout does not fire any expiration event.  It
simply starts answering `True` for the `ended` attribute.

    >>> one = datetime.timedelta(hours=1)
    >>> two = datetime.timedelta(hours=2)
    >>> three = datetime.timedelta(hours=3)
    >>> four = datetime.timedelta(hours=4)
    >>> token = util.register(tokens.EndableFreeze(demo, three))
    >>> token.duration
    datetime.timedelta(seconds=10800)
    >>> three >= token.remaining_duration >= two
    True
    >>> token.ended is None
    True
    >>> util.get(demo) is token
    True
    >>> list(util) == [token]
    True

The expiration time of a token is always the creation date plus the timeout.

    >>> token.expiration == token.started + token.duration
    True
    >>> ((before_creation + three) <=
    ...  (token.expiration) <= # this value is the expiration date
    ...  (before_creation + four))
    True

Expirations can be changed while a token is still active, using any of
the `expiration`, `remaining_duration` or `duration` attributes.  All changes
fire events.  First we'll change the expiration attribute.

    >>> token.expiration = token.started + one
    >>> token.expiration == token.started + one
    True
    >>> token.duration == one
    True
    >>> ev = events[-1]
    >>> verifyObject(interfaces.IExpirationChangedEvent, ev)
    True
    >>> ev.object is token
    True
    >>> ev.old == token.started + three
    True

Next we'll change the duration attribute.

    >>> token.duration = four
    >>> token.duration
    datetime.timedelta(seconds=14400)
    >>> four >= token.remaining_duration >= three
    True
    >>> ev = events[-1]
    >>> verifyObject(interfaces.IExpirationChangedEvent, ev)
    True
    >>> ev.object is token
    True
    >>> ev.old == token.started + one
    True

Now we'll hack our code to make it think that it is two hours later, and then
check and modify the remaining_duration attribute.

    >>> def hackNow():
    ...     return (datetime.datetime.now(pytz.utc) +
    ...             datetime.timedelta(hours=2))
    ...
    >>> import zope.locking.utils
    >>> oldNow = zope.locking.utils.now
    >>> zope.locking.utils.now = hackNow # make code think it's 2 hours later
    >>> token.duration
    datetime.timedelta(seconds=14400)
    >>> two >= token.remaining_duration >= one
    True
    >>> token.remaining_duration -= one
    >>> one >= token.remaining_duration >= datetime.timedelta()
    True
    >>> three + datetime.timedelta(minutes=1) >= token.duration >= three
    True
    >>> ev = events[-1]
    >>> verifyObject(interfaces.IExpirationChangedEvent, ev)
    True
    >>> ev.object is token
    True
    >>> ev.old == token.started + four
    True

Now, we'll hack our code to make it think that it's a day later.  It is very
important to remember that a token ending with a timeout ends silently--that
is, no event is fired.

    >>> def hackNow():
    ...     return (
    ...         datetime.datetime.now(pytz.utc) + datetime.timedelta(days=1))
    ...
    >>> zope.locking.utils.now = hackNow # make code think it is a day later
    >>> token.ended >= token.started
    True
    >>> util.get(demo) is None
    True
    >>> token.remaining_duration == datetime.timedelta()
    True
    >>> token.end()
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.EndedError

Once a token has ended, the timeout can no longer be changed.

    >>> token.duration = datetime.timedelta(days=2)
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.EndedError

We'll undo the hacks, and also end the token (that is no longer ended once
the hack is finished).

    >>> zope.locking.utils.now = oldNow # undo the hack
    >>> token.end()
