This file explores the cleanup mechanisms of the token utility.  It looks
at implementation-specific details, rather than interface usage.  It will
probably only be of interest to package maintainers, rather than package
users.

The token utility keeps three indexes of the tokens.  The primary index,
`_locks`, is a mapping of

  <key reference to content object>: (
      <token>,
      <frozenset of token principal ids>,
      <token's expiration (datetime or None)>)

The utility's `get` method uses this data structure, for instance.

Another index, `_principal_ids`, maps <principal id> to <set of <tokens>>.
Its use is the `iterForPrincipalId` methods.

The last index, `_expirations`, maps <token expiration datetimes> to <set of
<tokens>>.  Its use is cleaning up expired tokens: every time a new
token is registered, the utility gets rid of expired tokens from all data
structures.

There are three cases in which these data structures need to be updated:

- a new token must be added to the indexes;

- expired tokens should be found and deleted (done at the same time as new
  tokens are added currently); and

- a token changes and needs to be reindexed.

Let's run through some examples and check the data structures as we go.  We'll
need to start with some setup.

    >>> from zope.locking import utility, interfaces, tokens
    >>> from zope.keyreference.interfaces import IKeyReference
    >>> util = utility.TokenUtility()
    >>> conn = get_connection()
    >>> conn.add(util)
    >>> from zope.interface.verify import verifyObject
    >>> verifyObject(interfaces.ITokenUtility, util)
    True

    >>> import datetime
    >>> import pytz
    >>> before_creation = datetime.datetime.now(pytz.utc)
    >>> from zope.locking.testing import Demo
    >>> demo = Demo()

    >>> NO_TIME = datetime.timedelta()
    >>> ONE_HOUR = datetime.timedelta(hours=1)
    >>> TWO_HOURS = datetime.timedelta(hours=2)
    >>> THREE_HOURS = datetime.timedelta(hours=3)
    >>> FOUR_HOURS = datetime.timedelta(hours=4)

As with other files, we will hack the utils module to make the package think
that time has passed.

    >>> offset = NO_TIME
    >>> def hackNow():
    ...     return (datetime.datetime.now(pytz.utc) + offset)
    ...
    >>> import zope.locking.utils
    >>> oldNow = zope.locking.utils.now
    >>> zope.locking.utils.now = hackNow # make code think it's two hours later

Now we simply need to set the `offset` variable to different timedelta values
to make the package think that time has passed.

Initial Token Indexing
----------------------

Let's create a lock.

    >>> lock = util.register(
    ...     tokens.SharedLock(demo, ('john', 'mary'), duration=ONE_HOUR))

Now `_locks` has a single entry: keyreference to (token, principals,
expiration).

    >>> len(util._locks)
    1
    >>> key_ref = next(iter(util._locks))
    >>> key_ref() is demo
    True
    >>> token, principal_ids, expiration = util._locks[key_ref]
    >>> token is lock
    True
    >>> sorted(principal_ids)
    ['john', 'mary']
    >>> expiration == lock.expiration
    True

Similarly, `_principal_ids` has two entries now: one for each principal, which
hold a set of the current locks.

    >>> sorted(util._principal_ids)
    ['john', 'mary']
    >>> list(util._principal_ids['john']) == [lock]
    True
    >>> list(util._principal_ids['mary']) == [lock]
    True

And `_expirations` has a single entry: the one hour duration, mapped to a set
of the one lock.

    >>> len(util._expirations)
    1
    >>> next(iter(util._expirations)) == lock.expiration
    True
    >>> list(util._expirations[lock.expiration]) == [lock]
    True

Token Modification
------------------

If we modify some of the token values, the indexes should be updated
accordingly.

    >>> lock.duration=TWO_HOURS
    >>> lock.add(('susan',))
    >>> lock.remove(('mary', 'john'))

The `_locks` index still has a single entry.

    >>> len(util._locks)
    1
    >>> key_ref = next(iter(util._locks))
    >>> key_ref() is demo
    True
    >>> token, principal_ids, expiration = util._locks[key_ref]
    >>> token is lock
    True
    >>> sorted(principal_ids)
    ['susan']
    >>> expiration == token.started + TWO_HOURS == token.expiration
    True

The `_principal_ids` index also has only one entry now, since susan is the
only lock owner.

    >>> sorted(util._principal_ids)
    ['susan']
    >>> list(util._principal_ids['susan']) == [lock]
    True

And `_expirations` has a single entry: the two hour duration, mapped to a set
of the one lock.

    >>> len(util._expirations)
    1
    >>> next(iter(util._expirations)) == lock.expiration
    True
    >>> list(util._expirations[lock.expiration]) == [lock]
    True

Adding a Freeze
---------------

Let's add a freeze to look at the opposite extreme of indexing: no principals,
and no duration.

    >>> frozen = Demo()
    >>> freeze = util.register(tokens.EndableFreeze(frozen))

Now `_locks` has two indexed objects.

    >>> len(util._locks)
    2
    >>> token, principals, expiration = util._locks[IKeyReference(frozen)]
    >>> token is freeze
    True
    >>> len(principals)
    0
    >>> expiration is None
    True

The other indexes should not have changed, though.

    >>> sorted(util._principal_ids)
    ['susan']
    >>> len(util._expirations)
    1
    >>> list(util._expirations[lock.expiration]) == [lock]
    True

Expiration
----------

Now we'll make the lock expire by pushing the package's effective time two
hours in the future.

    >>> offset = TWO_HOURS

The lock should have ended now.

    >>> lock.ended == lock.expiration
    True
    >>> util.get(demo) is None
    True
    >>> list(iter(util)) == [freeze]
    True
    >>> list(util.iterForPrincipalId('susan'))
    []

However, if we look at the indexes, no changes have been made yet.

    >>> len(util._locks)
    2
    >>> token, principals, expiration = util._locks[IKeyReference(demo)]
    >>> token is lock
    True
    >>> sorted(principals)
    ['susan']
    >>> expiration == token.expiration == token.started + TWO_HOURS
    True
    >>> sorted(util._principal_ids)
    ['susan']
    >>> len(util._expirations)
    1
    >>> list(util._expirations[lock.expiration]) == [lock]
    True

The changes won't be made for the expired lock until we register a new lock.
We'll make this one expire an hour later.

    >>> another_demo = Demo()
    >>> lock = util.register(
    ...     tokens.ExclusiveLock(another_demo, 'john', ONE_HOUR))

Now all the indexes should have removed the references to the old lock.

    >>> sorted(util._locks) == sorted((IKeyReference(frozen),
    ...                                IKeyReference(another_demo)))
    True
    >>> sorted(util._principal_ids)
    ['john']
    >>> len(util._expirations)
    1
    >>> list(util._expirations[lock.expiration]) == [lock]
    True

We just looked at adding a token for one object that removed the index of
an expired token of another object.  Let's make sure that the story holds true
if the new token is the same as an old, expired token--the code paths are a
bit different.

We'll extend the offset by another hour to expire the new lock.  As before, no
changes will have been made.

    >>> offset = THREE_HOURS
    >>> lock.ended == lock.expiration
    True
    >>> len(util._locks)
    2
    >>> token, principals, expiration = util._locks[
    ...     IKeyReference(another_demo)]
    >>> token is lock
    True
    >>> sorted(principals)
    ['john']
    >>> expiration == token.expiration == token.started + ONE_HOUR
    True
    >>> sorted(util._principal_ids)
    ['john']
    >>> len(util._expirations)
    1
    >>> list(util._expirations[lock.expiration]) == [lock]
    True

Now, when we create a new token for the same object, the indexes are again
cleared appropriately.

    >>> new_lock = util.register(
    ...     tokens.ExclusiveLock(another_demo, 'mary', THREE_HOURS))
    >>> len(util._locks)
    2
    >>> token, principals, expiration = util._locks[
    ...     IKeyReference(another_demo)]
    >>> token is new_lock
    True
    >>> sorted(principals)
    ['mary']
    >>> expiration == token.expiration == token.started + THREE_HOURS
    True
    >>> sorted(util._principal_ids)
    ['mary']
    >>> len(util._expirations)
    1
    >>> list(util._expirations[new_lock.expiration]) == [new_lock]
    True

An issue arose when two or more expired locks are stored in the utility. When
we tried to add a third lock token the cleanup method incorrectly tried to
clean up the the lock token we were trying to add.

    >>> second_demo = Demo()
    >>> second_lock = util.register(
    ...    tokens.ExclusiveLock(second_demo, 'john', THREE_HOURS))

    >>> len(util._expirations)
    2

Now expire the two registered tokens. The offset is currently 3 hours from now
and the tokens have a duration of 3 hours so increase by 7 hours.

    >>> offset = THREE_HOURS + FOUR_HOURS

Register the third lock token.

    >>> third_demo = Demo()
    >>> third_lock = util.register(
    ...    tokens.ExclusiveLock(third_demo, 'michael', ONE_HOUR))

    >>> len(util._expirations)
    1
    >>> list(util._expirations[third_lock.expiration]) == [third_lock]
    True

Explicit Ending
---------------

If I end all the tokens, it should remove all records from the indexes.

    >>> freeze.end()
    >>> third_lock.end()
    >>> len(util._locks)
    0
    >>> len(util._principal_ids)
    0
    >>> len(util._expirations)
    0


Demo
----

The following is a regression test for a bug which prevented the token
utility from cleaning up expired tokens correctly; perhaps it is also a
somewhat more realistic demonstration of some interactions with the utility
in that it uses multiple connections to the database.

    >>> offset = NO_TIME
    >>> import persistent
    >>> import transaction

    >>> def populate(principal, conn, duration=None, n=100):
    ...   """Add n tokens for principal to the db using conn as the connection
    ...      to the db.
    ...   """
    ...   t = conn.transaction_manager.begin()
    ...   util = token_util(conn)
    ...   for i in range(n):
    ...     obj = persistent.Persistent()
    ...     conn.add(obj)
    ...     lock = tokens.ExclusiveLock(obj, principal, duration=duration)
    ...     ignored = util.register(lock)
    ...   t.commit()
    >>> def end(principal, conn, n=None):
    ...   """End n tokens for the given principal using conn as the connection
    ...      to the db.
    ...   """
    ...   t = conn.transaction_manager.begin()
    ...   locks = list(token_util(conn).iterForPrincipalId(principal))
    ...   res = len([l.end() for l in locks[:n]])
    ...   t.commit()
    ...   return res
    >>> def get_locks(principal, conn):
    ...   """Retrieves a list of locks for the principal using conn as the
    ...      connection to the db.
    ...   """
    ...   t = conn.transaction_manager.begin()
    ...   try:
    ...     return list(token_util(conn)._principal_ids[principal])
    ...   except KeyError:
    ...     return []

    >>> tm1 = transaction.TransactionManager()
    >>> tm2 = transaction.TransactionManager()

    >>> conn1 = get_db().open(transaction_manager=tm1)
    >>> conn2 = get_db().open(transaction_manager=tm2)

We "install" the token utility.

    >>> conn1.root()['token_util'] = zope.locking.utility.TokenUtility()
    >>> token_util = lambda conn: conn.root()['token_util']
    >>> tm1.commit()

First, we fill the token utility with 100 locks through connection 1
under the principal id of 'Dwight Holly'.

    >>> populate('Dwight Holly', conn1)

Via connection 2, we end 50 of Dwight's locks.

    >>> n = end('Dwight Holly', conn2, 50)

In connection 1, we verify that 50 locks have been removed.

    >>> len(get_locks('Dwight Holly', conn1)) == 100 - n
    True

Now we end the rest of the locks through connection 2.

    >>> ignored = end('Dwight Holly', conn2)

And verify through connection 1 that Dwight now has no locks in the utility.

    >>> get_locks('Dwight Holly', conn1) == []
    True
    >>> 'Dwight Holly' in token_util(conn1)._principal_ids
    False

Dwight gets 100 more locks through connection 1, however this time they are
all set to expire in 10 minutes.

    >>> populate('Dwight Holly', conn1, duration=datetime.timedelta(minutes=10))

We sync connection 2 so we can see that the locks are indeed there.

    >>> conn2.sync()
    >>> util = token_util(conn2)
    >>> 'Dwight Holly' in util._principal_ids
    True
    >>> len(util._expirations) > 0
    True

Now we time-travel one hour into the future, where Dwight's locks have long
since expired.

    >>> offset = ONE_HOUR

Adding a new lock through connection 2 will trigger a cleanup...

    >>> populate('Pete Bondurant', conn2)

...at which point we can see via connection 1 that all of Dwight's locks
are gone.

    >>> conn1.sync()
    >>> util = token_util(conn1)
    >>> len(util._expirations)
    0
    >>> 'Dwight Holly' in util._principal_ids
    False

    >>> conn1.close()
    >>> conn2.close()



Clean Up
--------

    >>> zope.locking.utils.now = oldNow # undo the time hack
