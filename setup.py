from setuptools import setup, find_packages

setup(
    name="zope.locking",
    version="1.3dev",
    license='ZPL 2.1',
    packages=find_packages('src'),
    package_dir={'':'src'},
    namespace_packages=['zope'],
    include_package_data=True,
    install_requires = [
        'setuptools',
        'ZODB3',
        'pytz',
        'zc.i18n',
        'zope.app.generations',
        'zope.app.keyreference',
        'zope.app.publisher',
        'zope.app.testing',
        'zope.component',
        'zope.event',
        'zope.formlib',
        'zope.i18nmessageid',
        'zope.interface',
        'zope.location',
        'zope.publisher',
        'zope.schema',
        'zope.security',
        'zope.testing',
        ],
    zip_safe = False,
    description=open("README.txt").read(),
    long_description=(
        open('src/zope/locking/CHANGES.txt').read() +
        '\n\n' +
        open("src/zope/locking/README.txt").read()),
    author='Zope Project',
    author_email='zope3-dev@zope.org',
    url='http://pypi.python.org/pypi/zope.locking',
    )
