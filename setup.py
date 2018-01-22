##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
# This package is developed by the Zope Toolkit project, documented here:
# http://docs.zope.org/zopetoolkit
# When developing and releasing this package, please follow the documented
# Zope Toolkit policies as described by this documentation.
##############################################################################
"""Setup for zope.locking package
"""
from setuptools import setup, find_packages


version = '1.3+md2.dev0'


tests_require = [
    'transaction',
    'zope.app.appsetup',
    'zope.testing'
    ]


setup(
    name="zope.locking",
    version=version,
    license='ZPL 2.1',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['zope'],
    include_package_data=True,
    install_requires=[
        'BTrees',
        'persistent',
        'pytz',
        'setuptools',
        'zope.component',
        'zope.event',
        'zope.generations',
        'zope.interface',
        'zope.keyreference',
        'zope.location',
        'zope.schema',
        'zope.security',
        ],
    zip_safe=False,
    tests_require=tests_require,
    extras_require={'test': tests_require},
    description=open("README.txt").read(),
    long_description=open('CHANGES.txt').read(),
    author='Zope Project',
    author_email='zope3-dev@zope.org',
    url='http://pypi.python.org/pypi/zope.locking',
    )
