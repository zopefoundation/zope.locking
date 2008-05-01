from setuptools import setup, find_packages

setup(
    name="zope.locking",
    version="1.1b",
    packages=find_packages('src'),
    package_dir={'':'src'},
    namespace_packages=['zope'],
    include_package_data=True,
    install_requires = [
        'setuptools',
        'zope.security',
        'zope.interface',
        'zope.i18nmessageid',
        'zope.component',
        'zope.schema',
        'zope.app.testing',
        'zope.testing',
        'zope.event',
        'ZODB3',
        'zope.app.keyreference',
        'zope.location',
        'zope.publisher',
        'zope.formlib',
        'zope.app.publisher',
        'zc.i18n',
        'pytz',
        ],
    zip_safe = False,
    description=open("README.txt").read(),
    long_description=(
        open('src/zope/locking/CHANGES.txt').read() +
        '\n\n' +
        open("src/zope/locking/README.txt").read()),
    author='Zope Project',
    author_email='zope3-dev@zope.org',
    )
