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
import os.path

from setuptools import setup, find_packages


def read(*rnames):
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        return f.read()


version = '2.0.0'


tests_require = [
    'transaction',
    'zope.app.appsetup',
    'zope.testing',
    'zope.testrunner',
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
    description=(
        'Advisory exclusive locks, shared locks, and freezes '
        '(locked to no-one).'),
    long_description=(
        read('README.rst')
        + '\n\n' +
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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Framework :: Zope3',
        ],
    author='Zope Project',
    author_email='zope3-dev@zope.org',
    url='https://github.com/zopefoundation/zope.locking',
    )
