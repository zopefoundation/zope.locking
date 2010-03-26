from setuptools import setup, find_packages

setup(
    name="zope.locking",
    version="1.0b",
    license='ZPL 2.1',
    packages=find_packages('src'),
    package_dir={'':'src'},
    namespace_packages=['zope'],
    include_package_data=True,
    install_requires = ['setuptools'],
    zip_safe = False,
    description=open("README.txt").read(),
    long_description=(
        open('src/zope/locking/CHANGES.txt').read() +
        '\n\n' +
        open("src/zope/locking/README.txt").read()),
    )
