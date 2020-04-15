==========
System API
==========

The central approach for the package is that locks and freeze tokens must be
created and then registered by a token utility.  The tokens will not work
until they have been registered.  This gives the ability to definitively know,
and thus manipulate, all active tokens in a system.

The first object we'll introduce, then, is the TokenUtility: the utility that
is responsible for the registration and the retrieving of tokens.

    >>> from zope import component, interface
    >>> from zope.locking import interfaces, utility, tokens
    >>> util = utility.TokenUtility()
    >>> from zope.interface.verify import verifyObject
    >>> verifyObject(interfaces.ITokenUtility, util)
    True

The utility only has a few methods--`get`, `iterForPrincipalId`,
`__iter__`, and `register`--which we will look at below.  It is expected to be
persistent, and the included implementation is in fact persistent.Persistent,
and expects to be installed as a local utility.  The utility needs a
connection to the database before it can register persistent tokens.

    >>> from zope.locking.testing import Demo
    >>> lock = tokens.ExclusiveLock(Demo(), 'Fantomas')
    >>> util.register(lock)
    Traceback (most recent call last):
    ...
    AttributeError: 'NoneType' object has no attribute 'add'

    >>> conn = get_connection()
    >>> conn.add(util)

If the token provides IPersistent, the utility will add it to its connection.

    >>> lock._p_jar is None
    True

    >>> lock = util.register(lock)
    >>> lock._p_jar is util._p_jar
    True

    >>> lock.end()
    >>> lock = util.register(lock)


The standard token utility can accept tokens for any object that is adaptable
to IKeyReference.

    >>> import datetime
    >>> import pytz
    >>> before_creation = datetime.datetime.now(pytz.utc)
    >>> demo = Demo()

Now, with an instance of the demo class, it is possible to register lock and
freeze tokens for demo instances with the token utility.

As mentioned above, the general pattern for making a lock or freeze token is
to create it--at which point most of its methods and attributes are
unusable--and then to register it with the token utility.  After registration,
the lock is effective and in place.

The TokenUtility can actually be used with anything that implements
zope.locking.interfaces.IAbstractToken, but we'll look at the four tokens that
come with the zope.locking package: an exclusive lock, a shared lock, a
permanent freeze, and an endable freeze.

Exclusive Locks
===============

Exclusive locks are tokens that are owned by a single principal.  No principal
may be added or removed: the lock token must be ended and another started for
another principal to get the benefits of the lock (whatever they have been
configured to be).

Here's an example of creating and registering an exclusive lock: the principal
with an id of 'john' locks the demo object.

    >>> lock = tokens.ExclusiveLock(demo, 'john')
    >>> res = util.register(lock)
    >>> res is lock
    True

The lock token is now in effect.  Registering the token (the lock) fired an
ITokenStartedEvent, which we'll look at now.

(Note that this example uses an events list to look at events that have fired.
This is simply a list whose `append` method has been added as a subscriber
to the zope.event.subscribers list.  It's included as a global when this file
is run as a test.)

    >>> from zope.component.eventtesting import events
    >>> ev = events[-1]
    >>> verifyObject(interfaces.ITokenStartedEvent, ev)
    True
    >>> ev.object is lock
    True

Now that the lock token is created and registered, the token utility knows
about it.  The utilities `get` method simply returns the active token for an
object or None--it never returns an ended token, and in fact none of the
utility methods do.

    >>> util.get(demo) is lock
    True
    >>> util.get(Demo()) is None
    True

Note that `get` accepts alternate defaults, like a dictionary.get:

    >>> util.get(Demo(), util) is util
    True

The `iterForPrincipalId` method returns an iterator of active locks for the
given principal id.

    >>> list(util.iterForPrincipalId('john')) == [lock]
    True
    >>> list(util.iterForPrincipalId('mary')) == []
    True

The util's `__iter__` method simply iterates over all active (non-ended)
tokens.

    >>> list(util) == [lock]
    True

The token utility disallows registration of multiple active tokens for the
same object.

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
    >>> util.register(tokens.Freeze(demo))
    ... # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.RegistrationError: ...

It's also worth looking at the lock token itself.  The registered lock token
implements IExclusiveLock.

    >>> verifyObject(interfaces.IExclusiveLock, lock)
    True

It provides a number of capabilities. Arguably the most important attribute is
whether the token is in effect or not: `ended`. This token is active, so it
has not yet ended:

    >>> lock.ended is None
    True

When it does end, the ended attribute is a datetime in UTC of when the token
ended.  We'll demonstrate that below.

Later, the `creation`, `expiration`, `duration`, and `remaining_duration` will
be important; for now we merely note their existence.

    >>> before_creation <= lock.started <= datetime.datetime.now(pytz.utc)
    True
    >>> lock.expiration is None # == forever
    True
    >>> lock.duration is None # == forever
    True
    >>> lock.remaining_duration is None # == forever
    True

The `end` method and the related ending and expiration attributes are all part
of the IEndable interface--an interface that not all tokens must implement,
as we will also discuss later.

    >>> interfaces.IEndable.providedBy(lock)
    True

The `context` and `__parent__` attributes point to the locked object--demo in
our case.  `context` is the intended standard API for obtaining the object,
but `__parent__` is important for the Zope 3 security set up, as discussed
towards the end of this document.

    >>> lock.context is demo
    True
    >>> lock.__parent__ is demo # important for security
    True

Registering the lock with the token utility set the utility attribute and
initialized the started attribute to the datetime that the lock began.  The
utility attribute should never be set by any code other than the token
utility.

    >>> lock.utility is util
    True

Tokens always provide a `principal_ids` attribute that provides an iterable of
the principals that are part of a token.  In our case, this is an exclusive
lock for 'john', so the value is simple.

    >>> sorted(lock.principal_ids)
    ['john']

The only method on a basic token like the exclusive lock is `end`.  Calling it
without arguments permanently and explicitly ends the life of the token.

    >>> lock.end()

Like registering a token, ending a token fires an event.

    >>> ev = events[-1]
    >>> verifyObject(interfaces.ITokenEndedEvent, ev)
    True
    >>> ev.object is lock
    True

It affects attributes on the token.  Again, the most important of these is
ended, which is now the datetime of ending.

    >>> lock.ended >= lock.started
    True
    >>> lock.remaining_duration == datetime.timedelta()
    True

It also affects queries of the token utility.

    >>> util.get(demo) is None
    True
    >>> list(util.iterForPrincipalId('john')) == []
    True
    >>> list(util) == []
    True

Don't try to end an already-ended token.

    >>> lock.end()
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.EndedError

The other way of ending a token is with an expiration datetime.  As we'll see,
one of the most important caveats about working with timeouts is that a token
that expires because of a timeout does not fire any expiration event.  It
simply starts providing the `expiration` value for the `ended` attribute.

    >>> one = datetime.timedelta(hours=1)
    >>> two = datetime.timedelta(hours=2)
    >>> three = datetime.timedelta(hours=3)
    >>> four = datetime.timedelta(hours=4)
    >>> lock = util.register(tokens.ExclusiveLock(demo, 'john', three))
    >>> lock.duration
    datetime.timedelta(seconds=10800)
    >>> three >= lock.remaining_duration >= two
    True
    >>> lock.ended is None
    True
    >>> util.get(demo) is lock
    True
    >>> list(util.iterForPrincipalId('john')) == [lock]
    True
    >>> list(util) == [lock]
    True

The expiration time of an endable token is always the creation date plus the
timeout.

    >>> lock.expiration == lock.started + lock.duration
    True
    >>> ((before_creation + three) <=
    ...  (lock.expiration) <= # this value is the expiration date
    ...  (before_creation + four))
    True

Expirations can be changed while a lock is still active, using any of
the `expiration`, `remaining_duration` or `duration` attributes.  All changes
fire events.  First we'll change the expiration attribute.

    >>> lock.expiration = lock.started + one
    >>> lock.expiration == lock.started + one
    True
    >>> lock.duration == one
    True
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
    >>> lock.remaining_duration -= one
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
    >>> lock.ended == lock.expiration
    True
    >>> util.get(demo) is None
    True
    >>> util.get(demo, util) is util # alternate default works
    True
    >>> lock.remaining_duration == datetime.timedelta()
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

Make sure to register tokens.  Creating a lock but not registering it puts it
in a state that is not fully initialized.

    >>> lock = tokens.ExclusiveLock(demo, 'john')
    >>> lock.started # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.UnregisteredError: ...
    >>> lock.ended # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.UnregisteredError: ...


Shared Locks
============

Shared locks are very similar to exclusive locks, but take an iterable of one
or more principals at creation, and can have principals added or removed while
they are active.

In this example, also notice a convenient characteristic of the TokenUtility
`register` method: it also returns the token, so creation, registration, and
variable assignment can be chained, if desired.

    >>> lock = util.register(tokens.SharedLock(demo, ('john', 'mary')))
    >>> ev = events[-1]
    >>> verifyObject(interfaces.ITokenStartedEvent, ev)
    True
    >>> ev.object is lock
    True

Here, principals with ids of 'john' and 'mary' have locked the demo object.
The returned token implements ISharedLock and provides a superset of the
IExclusiveLock capabilities.  These next operations should all look familiar
from the discussion of the ExclusiveLock tokens above.

    >>> verifyObject(interfaces.ISharedLock, lock)
    True
    >>> lock.context is demo
    True
    >>> lock.__parent__ is demo # important for security
    True
    >>> lock.utility is util
    True
    >>> sorted(lock.principal_ids)
    ['john', 'mary']
    >>> lock.ended is None
    True
    >>> before_creation <= lock.started <= datetime.datetime.now(pytz.utc)
    True
    >>> lock.expiration is None
    True
    >>> lock.duration is None
    True
    >>> lock.remaining_duration is None
    True
    >>> lock.end()
    >>> lock.ended >= lock.started
    True

As mentioned, though, the SharedLock capabilities are a superset of the
ExclusiveLock ones.  There are two extra methods: `add` and `remove`.  These
are able to add and remove principal ids as shared owners of the lock token.

    >>> lock = util.register(tokens.SharedLock(demo, ('john',)))
    >>> sorted(lock.principal_ids)
    ['john']
    >>> lock.add(('mary',))
    >>> sorted(lock.principal_ids)
    ['john', 'mary']
    >>> lock.add(('alice',))
    >>> sorted(lock.principal_ids)
    ['alice', 'john', 'mary']
    >>> lock.remove(('john',))
    >>> sorted(lock.principal_ids)
    ['alice', 'mary']
    >>> lock.remove(('mary',))
    >>> sorted(lock.principal_ids)
    ['alice']

Adding and removing principals fires appropriate events, as you might expect.

    >>> lock.add(('mary',))
    >>> sorted(lock.principal_ids)
    ['alice', 'mary']
    >>> ev = events[-1]
    >>> verifyObject(interfaces.IPrincipalsChangedEvent, ev)
    True
    >>> ev.object is lock
    True
    >>> sorted(ev.old)
    ['alice']
    >>> lock.remove(('alice',))
    >>> sorted(lock.principal_ids)
    ['mary']
    >>> ev = events[-1]
    >>> verifyObject(interfaces.IPrincipalsChangedEvent, ev)
    True
    >>> ev.object is lock
    True
    >>> sorted(ev.old)
    ['alice', 'mary']

Removing all participants in a lock ends the lock, making it ended.

    >>> lock.remove(('mary',))
    >>> sorted(lock.principal_ids)
    []
    >>> lock.ended >= lock.started
    True
    >>> ev = events[-1]
    >>> verifyObject(interfaces.IPrincipalsChangedEvent, ev)
    True
    >>> ev.object is lock
    True
    >>> sorted(ev.old)
    ['mary']
    >>> ev = events[-2]
    >>> verifyObject(interfaces.ITokenEndedEvent, ev)
    True
    >>> ev.object is lock
    True

As you might expect, trying to add (or remove!) users from an ended lock is
an error.

    >>> lock.add(('john',))
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.EndedError
    >>> lock.remove(('john',))
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.EndedError

The token utility keeps track of shared lock tokens the same as exclusive lock
tokens.  Here's a quick summary in code.

    >>> lock = util.register(tokens.SharedLock(demo, ('john', 'mary')))
    >>> util.get(demo) is lock
    True
    >>> list(util.iterForPrincipalId('john')) == [lock]
    True
    >>> list(util.iterForPrincipalId('mary')) == [lock]
    True
    >>> list(util) == [lock]
    True
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
    >>> util.register(tokens.Freeze(demo))
    ... # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.RegistrationError: ...
    >>> lock.end()

Timed expirations work the same as with exclusive locks.  We won't repeat that
here, though look in the annoying.txt document in this package for the actual
repeated tests.


EndableFreezes
==============

An endable freeze token is similar to a lock token except that it grants the
'lock' to no one.

    >>> token = util.register(tokens.EndableFreeze(demo))
    >>> verifyObject(interfaces.IEndableFreeze, token)
    True
    >>> ev = events[-1]
    >>> verifyObject(interfaces.ITokenStartedEvent, ev)
    True
    >>> ev.object is token
    True
    >>> sorted(token.principal_ids)
    []
    >>> token.end()

Endable freezes are otherwise identical to exclusive locks.  See annoying.txt
for the comprehensive copy-and-paste tests duplicating the exclusive lock
tests.  Notice that an EndableFreeze will never be a part of an iterable of
tokens by principal: by definition, a freeze is associated with no principals.


Freezes
=======

Freezes are similar to EndableFreezes, except they are not endable.  They are
intended to be used by system level operations that should permanently disable
certain changes, such as changes to the content of an archived object version.

Creating them is the same...

    >>> token = util.register(tokens.Freeze(demo))
    >>> verifyObject(interfaces.IFreeze, token)
    True
    >>> ev = events[-1]
    >>> verifyObject(interfaces.ITokenStartedEvent, ev)
    True
    >>> ev.object is token
    True
    >>> sorted(token.principal_ids)
    []

But they can't go away...

    >>> token.end()
    Traceback (most recent call last):
    ...
    AttributeError: 'Freeze' object has no attribute 'end'

They also do not have expirations, duration, remaining durations, or ended
dates.  They are permanent, unless you go into the database to muck with
implementation-specific data structures.

There is no API way to end a Freeze.  We'll need to make a new object for the
rest of our demonstrations, and this token will exist through the
remaining examples.

    >>> old_demo = demo
    >>> demo = Demo()

===============================
User API, Adapters and Security
===============================

The API discussed so far makes few concessions to some of the common use cases
for locking.  Here are some particular needs as yet unfulfilled by the
discussion so far.

- It should be possible to allow and deny per object whether users may
  create and register tokens for the object.

- It should often be easier to register an endable token than a permanent
  token.

- All users should be able to unlock or modify some aspects of their own
  tokens, or remove their own participation in shared tokens; but it should be
  possible to restrict access to ending tokens that users do not own (often
  called "breaking locks").

In the context of the Zope 3 security model, the first two needs are intended
to be addressed by the ITokenBroker interface, and associated adapter; the last
need is intended to be addressed by the ITokenHandler, and associated
adapters.


TokenBrokers
============

Token brokers adapt an object, which is the object whose tokens are
brokered, and uses this object as a security context.  They provide a few
useful methods: `lock`, `lockShared`, `freeze`, and `get`.  The TokenBroker
expects to be a trusted adapter.

lock
----

The lock method creates and registers an exclusive lock.  Without arguments,
it tries to create it for the user in the current interaction.

This won't work without an interaction, of course.  Notice that we start the
example by registering the utility.  We would normally be required to put the
utility in a site package, so that it would be persistent, but for this
demonstration we are simplifying the registration.

    >>> component.provideUtility(util, provides=interfaces.ITokenUtility)

    >>> import zope.interface.interfaces
    >>> @interface.implementer(zope.interface.interfaces.IComponentLookup)
    ... @component.adapter(interface.Interface)
    ... def siteManager(obj):
    ...     return component.getGlobalSiteManager()
    ...
    >>> component.provideAdapter(siteManager)

    >>> from zope.locking import adapters
    >>> component.provideAdapter(adapters.TokenBroker)
    >>> broker = interfaces.ITokenBroker(demo)
    >>> broker.lock()
    Traceback (most recent call last):
    ...
    ValueError
    >>> broker.lock('joe')
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.ParticipationError

If we set up an interaction with one participation, the lock will have a
better chance.

    >>> import zope.security.interfaces
    >>> @interface.implementer(zope.security.interfaces.IPrincipal)
    ... class DemoPrincipal(object):
    ...     def __init__(self, id, title=None, description=None):
    ...         self.id = id
    ...         self.title = title
    ...         self.description = description
    ...
    >>> joe = DemoPrincipal('joe')
    >>> import zope.security.management
    >>> @interface.implementer(zope.security.interfaces.IParticipation)
    ... class DemoParticipation(object):
    ...     def __init__(self, principal):
    ...         self.principal = principal
    ...         self.interaction = None
    ...
    >>> zope.security.management.endInteraction()
    >>> zope.security.management.newInteraction(DemoParticipation(joe))

    >>> token = broker.lock()
    >>> interfaces.IExclusiveLock.providedBy(token)
    True
    >>> token.context is demo
    True
    >>> token.__parent__ is demo
    True
    >>> sorted(token.principal_ids)
    ['joe']
    >>> token.started is not None
    True
    >>> util.get(demo) is token
    True
    >>> token.end()

You can only specify principals that are in the current interaction.

    >>> token = broker.lock('joe')
    >>> sorted(token.principal_ids)
    ['joe']
    >>> token.end()
    >>> broker.lock('mary')
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.ParticipationError

The method can take a duration.

    >>> token = broker.lock(duration=two)
    >>> token.duration == two
    True
    >>> token.end()

If the interaction has more than one principal, a principal (in the
interaction) must be specified.

    >>> mary = DemoPrincipal('mary')
    >>> participation = DemoParticipation(mary)
    >>> zope.security.management.getInteraction().add(participation)
    >>> broker.lock()
    Traceback (most recent call last):
    ...
    ValueError
    >>> broker.lock('susan')
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.ParticipationError
    >>> token = broker.lock('joe')
    >>> sorted(token.principal_ids)
    ['joe']
    >>> token.end()
    >>> token = broker.lock('mary')
    >>> sorted(token.principal_ids)
    ['mary']
    >>> token.end()
    >>> zope.security.management.endInteraction()

lockShared
----------

The `lockShared` method has similar characteristics, except that it can handle
multiple principals.

Without an interaction, principals are either not found, or not part of the
interaction:

    >>> broker.lockShared()
    Traceback (most recent call last):
    ...
    ValueError
    >>> broker.lockShared(('joe',))
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.ParticipationError

With an interaction, the principals get the lock by default.

    >>> zope.security.management.newInteraction(DemoParticipation(joe))

    >>> token = broker.lockShared()
    >>> interfaces.ISharedLock.providedBy(token)
    True
    >>> token.context is demo
    True
    >>> token.__parent__ is demo
    True
    >>> sorted(token.principal_ids)
    ['joe']
    >>> token.started is not None
    True
    >>> util.get(demo) is token
    True
    >>> token.end()

You can only specify principals that are in the current interaction.

    >>> token = broker.lockShared(('joe',))
    >>> sorted(token.principal_ids)
    ['joe']
    >>> token.end()
    >>> broker.lockShared(('mary',))
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.ParticipationError

The method can take a duration.

    >>> token = broker.lockShared(duration=two)
    >>> token.duration == two
    True
    >>> token.end()

If the interaction has more than one principal, all are included, unless some
are singled out.

    >>> participation = DemoParticipation(mary)
    >>> zope.security.management.getInteraction().add(participation)
    >>> token = broker.lockShared()
    >>> sorted(token.principal_ids)
    ['joe', 'mary']
    >>> token.end()
    >>> token = broker.lockShared(('joe',))
    >>> sorted(token.principal_ids)
    ['joe']
    >>> token.end()
    >>> token = broker.lockShared(('mary',))
    >>> sorted(token.principal_ids)
    ['mary']
    >>> token.end()
    >>> zope.security.management.endInteraction()

freeze
------

The `freeze` method allows users to create an endable freeze.  It has no
requirements on the interaction.  It should be protected carefully, from a
security perspective.

    >>> token = broker.freeze()
    >>> interfaces.IEndableFreeze.providedBy(token)
    True
    >>> token.context is demo
    True
    >>> token.__parent__ is demo
    True
    >>> sorted(token.principal_ids)
    []
    >>> token.started is not None
    True
    >>> util.get(demo) is token
    True
    >>> token.end()

The method can take a duration.

    >>> token = broker.freeze(duration=two)
    >>> token.duration == two
    True
    >>> token.end()

get
---

The `get` method is exactly equivalent to the token utility's get method:
it returns the current active token for the object, or None.  It is useful
for protected code, since utilities typically do not get security assertions,
and this method can get its security assertions from the object, which is
often the right place.

Again, the TokenBroker does embody some policy; if it is not good policy for
your application, build your own interfaces and adapters that do.


TokenHandlers
=============

TokenHandlers are useful for endable tokens with one or more principals--that
is, locks, but not freezes. They are intended to be protected with a lower
external security permission then the usual token methods and attributes, and
then impose their own checks on the basis of the current interaction. They are
very much policy, and other approaches may be useful. They are intended to be
registered as trusted adapters.

For exclusive locks and shared locks, then, we have token handlers.
Generally, token handlers give access to all of the same capabilities as their
corresponding tokens, with the following additional constraints and
capabilities:

- `expiration`, `duration`, and `remaining_duration` all may be set only if
  all the principals in the current interaction are owners of the wrapped
  token; and

- `release` removes some or all of the principals in the interaction if all
  the principals in the current interaction are owners of the wrapped token.

Note that `end` is unaffected: this is effectively "break lock", while
`release` is effectively "unlock".  Permissions should be set accordingly.

Shared lock handlers have two additional methods that are discussed in their
section.

ExclusiveLockHandlers
---------------------

Given the general constraints described above, exclusive lock handlers will
generally only allow access to their special capabilities if the operation
is in an interaction with only the lock owner.

    >>> zope.security.management.newInteraction(DemoParticipation(joe))
    >>> component.provideAdapter(adapters.ExclusiveLockHandler)
    >>> lock = broker.lock()
    >>> handler = interfaces.IExclusiveLockHandler(lock)
    >>> verifyObject(interfaces.IExclusiveLockHandler, handler)
    True
    >>> handler.__parent__ is lock
    True
    >>> handler.expiration is None
    True
    >>> handler.duration = two
    >>> lock.duration == two
    True
    >>> handler.expiration = handler.started + three
    >>> lock.expiration == handler.started + three
    True
    >>> handler.remaining_duration = two
    >>> lock.remaining_duration <= two
    True
    >>> handler.release()
    >>> handler.ended >= handler.started
    True
    >>> lock.ended >= lock.started
    True
    >>> lock = util.register(tokens.ExclusiveLock(demo, 'mary'))
    >>> handler = interfaces.ITokenHandler(lock) # for joe's interaction still
    >>> handler.duration = two # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.ParticipationError: ...
    >>> handler.expiration = handler.started + three # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.ParticipationError: ...
    >>> handler.remaining_duration = two # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.ParticipationError: ...
    >>> handler.release() # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.ParticipationError: ...
    >>> lock.end()

SharedLockHandlers
------------------

Shared lock handlers let anyone who is an owner of a token set the expiration,
duration, and remaining_duration values. This is a 'get out of the way' policy
that relies on social interactions to make sure all the participants are
represented as they want. Other policies could be written in other adapters.

    >>> component.provideAdapter(adapters.SharedLockHandler)
    >>> lock = util.register(tokens.SharedLock(demo, ('joe', 'mary')))
    >>> handler = interfaces.ITokenHandler(lock) # for joe's interaction still
    >>> verifyObject(interfaces.ISharedLockHandler, handler)
    True
    >>> handler.__parent__ is lock
    True
    >>> handler.expiration is None
    True
    >>> handler.duration = two
    >>> lock.duration == two
    True
    >>> handler.expiration = handler.started + three
    >>> lock.expiration == handler.started + three
    True
    >>> handler.remaining_duration = two
    >>> lock.remaining_duration <= two
    True
    >>> sorted(handler.principal_ids)
    ['joe', 'mary']
    >>> handler.release()
    >>> sorted(handler.principal_ids)
    ['mary']
    >>> handler.duration = two # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.ParticipationError: ...
    >>> handler.expiration = handler.started + three # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.ParticipationError: ...
    >>> handler.remaining_duration = two # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.ParticipationError: ...
    >>> handler.release() # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.ParticipationError: ...

The shared lock handler adds two additional methods to a standard handler:
`join` and `add`.  They do similar jobs, but are separate to allow separate
security settings for each.  The `join` method lets some or all of the
principals in the current interaction join.

    >>> handler.join()
    >>> sorted(handler.principal_ids)
    ['joe', 'mary']
    >>> handler.join(('susan',))
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.ParticipationError

The `add` method lets any principal ids be added to the lock, but all
principals in the current interaction must be a part of the lock.

    >>> handler.add(('susan',))
    >>> sorted(handler.principal_ids)
    ['joe', 'mary', 'susan']
    >>> handler.release()
    >>> handler.add('jake') # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    zope.locking.interfaces.ParticipationError: ...
    >>> lock.end()
    >>> zope.security.management.endInteraction()


Warnings
========

* The token utility will register a token for an object if it can.  It does not
  check to see if it is actually the local token utility for the given object.
  This should be arranged by clients of the token utility, and verified
  externally if desired.

* Tokens are stored as keys in BTrees, and therefore must be orderable
  (i.e., they must implement __cmp__).


Intended Security Configuration
===============================

Utilities are typically unprotected in Zope 3--or more accurately, have
no security assertions and are used with no security proxy--and the token
utility expects to be so.  As such, the broker and handler objects are
expected to be the objects used by view code, and so associated with security
proxies.  All should have appropriate __parent__ attribute values.  The
ability to mutate the tokens--`end`, `add` and `remove` methods, for
instance--should be protected with an administrator-type permission such as
'zope.Security'.  Setting the timeout properties on the token should be
protected in the same way.  Setting the handlers attributes can have a less
restrictive setting, since they calculate security themselves on the basis of
lock membership.

On the adapter, the `end` method should be protected with the same or
similar permission.  Calling methods such as lock and lockShared should be
protected with something like 'zope.ManageContent'.  Getting attributes should
be 'zope.View' or 'zope.Public', and unlocking and setting the timeouts, since
they are already protected to make sure the principal is a member of the lock,
can probably be 'zope.Public'.

These settings can be abused relatively easily to create an insecure
system--for instance, if a user can get an adapter to IPrincipalLockable for
another principal--but are a reasonable start.

    >>> broker.__parent__ is demo
    True
    >>> handler.__parent__ is lock
    True


Random Thoughts
===============

As a side effect of the design, it is conceivable that multiple lock utilities
could be in use at once, governing different aspects of an object; however,
this may never itself be of use.
