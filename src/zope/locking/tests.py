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

import doctest
import re
import unittest

import zope.testing.renormalizing

import zope.locking.testing


normalizer = zope.testing.renormalizing.RENormalizing([
    (re.compile(r'datetime\.timedelta\(0, (.*)\)'),
     r'datetime.timedelta(seconds=\1)'),
])


def test_suite():

    layer = zope.locking.testing.layer

    def get_connection():
        return layer.db.open()

    def get_db():
        return layer.db

    suite = unittest.TestSuite((
        doctest.DocFileSuite(
            'README.rst',
            optionflags=doctest.IGNORE_EXCEPTION_DETAIL,
            checker=normalizer,
            globs=dict(
                get_connection=get_connection,
                get_db=get_db
            )),
        doctest.DocFileSuite(
            'annoying.rst',
            optionflags=doctest.IGNORE_EXCEPTION_DETAIL,
            checker=normalizer,
            globs=dict(
                get_connection=get_connection,
                get_db=get_db
            )),
        doctest.DocFileSuite(
            'cleanup.rst',
            optionflags=doctest.IGNORE_EXCEPTION_DETAIL,
            checker=normalizer,
            globs=dict(
                get_connection=get_connection,
                get_db=get_db
            )),
    ))
    suite.layer = layer
    return suite
