from setuptools import setup, find_packages

setup(
    name="zope.locking",
    version="0.1dev",
    packages=find_packages('src'),
    package_dir={'':'src'},
    namespace_packages=['zope'],
    include_package_data=True,
    install_requires = ['setuptools'],
    zip_safe = False
    )
