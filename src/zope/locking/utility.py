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

import persistent
import persistent.interfaces
from BTrees.OOBTree import OOBTree
from BTrees.OOBTree import OOTreeSet
from zope.keyreference.interfaces import IKeyReference
from zope.location import Location

from zope import event
from zope import interface
from zope.locking import interfaces
from zope.locking import utils


@interface.implementer(interfaces.ITokenUtility)
class TokenUtility(persistent.Persistent, Location):

    def __init__(self):
        self._locks = OOBTree()
        self._expirations = OOBTree()
        self._principal_ids = OOBTree()

    def _del(self, tree, token, value):
        """remove a token for a value within either of the two index trees"""
        reg = tree[value]
        reg.remove(token)
        if not reg:
            del tree[value]

    def _add(self, tree, token, value):
        """add a token for a value within either of the two index trees"""
        reg = tree.get(value)
        if reg is None:
            reg = tree[value] = OOTreeSet()
        reg.insert(token)

    def _cleanup(self):
        "clean out expired keys"
        expiredkeys = []
        for k in self._expirations.keys(max=utils.now()):
            for token in self._expirations[k]:
                assert token.ended
                for p in token.principal_ids:
                    self._del(self._principal_ids, token, p)
                key_ref = IKeyReference(token.context)
                del self._locks[key_ref]
            expiredkeys.append(k)
        for k in expiredkeys:
            del self._expirations[k]

    def register(self, token):
        assert interfaces.IToken.providedBy(token)
        if token.utility is None:
            token.utility = self
        elif token.utility is not self:
            raise ValueError('Lock is already registered with another utility')
        if persistent.interfaces.IPersistent.providedBy(token):
            self._p_jar.add(token)
        key_ref = IKeyReference(token.context)
        current = self._locks.get(key_ref)
        if current is not None:
            current, principal_ids, expiration = current
            current_endable = interfaces.IEndable.providedBy(current)
            if current is not token:
                if current_endable and not current.ended:
                    raise interfaces.RegistrationError(token)
                # expired token: clean up indexes and fall through
                if current_endable and expiration is not None:
                    self._del(self._expirations, current, expiration)
                for p in principal_ids:
                    self._del(self._principal_ids, current, p)
            else:
                # current is token; reindex and return
                if current_endable and token.ended:
                    if expiration is not None:
                        self._del(self._expirations, token, expiration)
                    for p in principal_ids:
                        self._del(self._principal_ids, token, p)
                    del self._locks[key_ref]
                else:
                    if current_endable and token.expiration != expiration:
                        # reindex timeout
                        if expiration is not None:
                            self._del(self._expirations, token, expiration)
                        if token.expiration is not None:
                            self._add(
                                self._expirations, token, token.expiration)
                    orig = frozenset(principal_ids)
                    new = frozenset(token.principal_ids)
                    removed = orig.difference(new)
                    added = new.difference(orig)
                    for p in removed:
                        self._del(self._principal_ids, token, p)
                    for p in added:
                        self._add(self._principal_ids, token, p)
                    self._locks[key_ref] = (
                        token,
                        frozenset(token.principal_ids),
                        current_endable and token.expiration or None)
                self._cleanup()
                return token
        # expired current token or no current token; this is new
        endable = interfaces.IEndable.providedBy(token)
        self._locks[key_ref] = (
            token,
            frozenset(token.principal_ids),
            endable and token.expiration or None)
        if (endable and
                token.expiration is not None):
            self._add(self._expirations, token, token.expiration)
        for p in token.principal_ids:
            self._add(self._principal_ids, token, p)
        self._cleanup()
        event.notify(interfaces.TokenStartedEvent(token))
        return token

    def get(self, obj, default=None):
        res = self._locks.get(IKeyReference(obj))
        if res is not None and (
                not interfaces.IEndable.providedBy(res[0])
                or not res[0].ended):
            return res[0]
        return default

    def iterForPrincipalId(self, principal_id):
        locks = self._principal_ids.get(principal_id, ())
        for lock in locks:
            assert principal_id in frozenset(lock.principal_ids)
            if not lock.ended:
                yield lock

    def __iter__(self):
        for lock in self._locks.values():
            if (not interfaces.IEndable.providedBy(lock[0])
                    or not lock[0].ended):
                yield lock[0]
