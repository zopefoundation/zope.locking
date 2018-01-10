from setuptools import setup, find_packages

tests_require=[
    'zope.app.appsetup',
    'transaction',
    ]

setup(
    name="zope.locking",
    version="1.3dev",
    license='ZPL 2.1',
    packages=find_packages('src'),
    package_dir={'':'src'},
    namespace_packages=['zope'],
    include_package_data=True,
    install_requires = [
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
    zip_safe = False,
    tests_require=tests_require,
    extras_require={'test': tests_require},
    description=open("README.txt").read(),
    long_description=(
        open('src/zope/locking/CHANGES.txt').read() +
        '\n\n' +
        open("src/zope/locking/README.txt").read()),
    author='Zope Project',
    author_email='zope3-dev@zope.org',
    url='http://pypi.python.org/pypi/zope.locking',
    )
