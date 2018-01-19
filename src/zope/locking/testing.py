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

import zope.app.appsetup.testlayer
import zope.component
import zope.interface
import zope.keyreference.interfaces
import zope.locking


class IDemo(zope.interface.Interface):
    """a demonstration interface for a demonstration class"""

class Demo(object):
    zope.interface.implements(IDemo)

class DemoKeyReference(object):
    zope.interface.implements(zope.keyreference.interfaces.IKeyReference)
    zope.component.adapts(IDemo)

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

    def __cmp__(self, other):
        if self.key_type_id == other.key_type_id:
            return cmp(self._id, other._id)
        return cmp(self.key_type_id, other.key_type_id)


layer = zope.app.appsetup.testlayer.ZODBLayer(zope.locking)
