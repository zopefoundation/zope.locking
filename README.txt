=======================================================================
Advisory exclusive locks, shared locks, and freezes (locked to no-one).
=======================================================================

The zope.locking package provides three main features:

- advisory exclusive locks for individual objects;

- advisory shared locks for individual objects; and

- frozen objects (locked to no one).

Locks and freezes by themselves are advisory tokens and inherently
meaningless.  They must be given meaning by other software, such as a security
policy.

This package approaches these features primarily from the perspective of a
system API, largely free of policy; and then provides a set of adapters for
more common interaction with users, with some access policy.  We will first
look at the system API, and then explain the policy and suggested use of the
provided adapters.
