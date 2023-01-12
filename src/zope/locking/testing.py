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

import functools

import zope.app.appsetup.testlayer
import zope.component
import zope.interface
import zope.keyreference.interfaces

import zope.locking


class IDemo(zope.interface.Interface):
    """a demonstration interface for a demonstration class"""


@zope.interface.implementer(IDemo)
class Demo:
    pass


@functools.total_ordering
@zope.component.adapter(IDemo)
@zope.interface.implementer(zope.keyreference.interfaces.IKeyReference)
class DemoKeyReference:
    _class_counter = 0

    key_type_id = 'zope.locking.testing.DemoKeyReference'

    def __init__(self, context):
        self.context = context
        class_ = type(self)
        self._id = getattr(context, '__demo_key_reference__', None)
        if self._id is None:
            self._id = class_._class_counter
            context.__demo_key_reference__ = self._id
            class_._class_counter += 1

    def __call__(self):
        return self.context

    def __hash__(self):
        return (self.key_type_id, self._id)

    def __eq__(self, other):
        return (self.key_type_id, self._id) == (other.key_type_id, other._id)

    def __lt__(self, other):
        return (self.key_type_id, self._id) < (other.key_type_id, other._id)


layer = zope.app.appsetup.testlayer.ZODBLayer(zope.locking)
