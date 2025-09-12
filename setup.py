##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
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
import os.path

from setuptools import setup


def read(*rnames):
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        return f.read()


version = '4.0'


tests_require = [
    'transaction',
    'zope.app.appsetup',
    'zope.testing',
    'zope.testrunner >= 6.4',
]


setup(
    name="zope.locking",
    version=version,
    license='ZPL-2.1',
    include_package_data=True,
    python_requires='>=3.9',
    install_requires=[
        'BTrees',
        'persistent',
        'pytz',
        'setuptools',
        'zope.component',
        'zope.event',
        'zope.generations',
        'zope.interface >= 3.8',
        'zope.keyreference',
        'zope.location',
        'zope.schema',
        'zope.security',
    ],
    zip_safe=False,
    tests_require=tests_require,
    extras_require={'test': tests_require},
    description=(
        'Advisory exclusive locks, shared locks, and freezes '
        '(locked to no-one).'),
    long_description=(
        read('README.rst')
        + '\n\n.. contents::\n\n' +
        read('src', 'zope', 'locking', 'README.rst')
        + '\n\n' +
        read('CHANGES.rst')
    ),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Framework :: Zope :: 3',
    ],
    author='Zope Project',
    author_email='zope3-dev@zope.org',
    url='https://github.com/zopefoundation/zope.locking',
)
