=======
Changes
=======

4.0 (2025-09-12)
================

- Replace ``pkg_resources`` namespace with PEP 420 native namespace.


3.0 (2025-09-04)
================

- Add support for Python 3.9, 3.10, 3.11, 3.12, 3.13.

- Drop support for Python 2.7, 3.5, 3.6, 3.7, 3.8.


2.1.0 (2020-04-15)
==================

- Fix DeprecationWarnings for ObjectEvent.

- Add support for Python 3.7 and 3.8.

- Drop support for Python 3.3 and 3.4.


2.0.0 (2018-01-23)
==================

- Python 3 compatibility.

- Note: The browser views and related code where removed. You need to provide
  those in application-level code now.

- Package the zcml files.

- Updated dependencies.

- Revived from svn.zope.org


1.2.2 (2011-01-31)
==================

- Consolidate duplicate evolution code.

- Split generations config into its own zcml file.


1.2.1 (2010-01-20)
==================

- Bug fix: the generation added in 1.2 did not properly clean up
  expired tokens, and could leave the token utility in an inconsistent
  state.


1.2 (2009-11-23)
================

- Bug fix: tokens were stored in a manner that prevented them from
  being cleaned up properly in the utility's _principal_ids mapping.
  Make zope.locking.tokens.Token orderable to fix this, as tokens
  are stored as keys in BTrees.

- Add a zope.app.generations Schema Manager to clean up any lingering
  tokens due to this bug.  Token utilities not accessible through the
  component registry can be cleaned up manually with
  zope.locking.generations.fix_token_utility.

- TokenUtility's register method will now add the token to the utility's
  database connection if the token provides IPersistent.

- Clean up the tests and docs and move some common code to testing.py.

- Fix some missing imports.


1.1
===

(series for Zope 3.4; eggs)

1.1b
====

- converted to use eggs


1.0
===

(series for Zope 3.3; no dependencies on Zope eggs)

1.0b
====

Initial non-dev release
