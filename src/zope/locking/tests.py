import unittest
import doctest
import zope.locking.testing

def test_suite():

    layer = zope.locking.testing.layer

    def get_connection():
        return layer.db.open()

    def get_db():
        return layer.db

    suite = unittest.TestSuite((
        doctest.DocFileSuite(
            'README.txt',
            globs=dict(
                get_connection=get_connection,
                get_db=get_db
            )),
        doctest.DocFileSuite(
            'annoying.txt',
            globs=dict(
                get_connection=get_connection,
                get_db=get_db
            )),
        doctest.DocFileSuite(
            'cleanup.txt',
            globs=dict(
                get_connection=get_connection,
                get_db=get_db
            )),
        ))
    suite.layer = layer
    return suite
