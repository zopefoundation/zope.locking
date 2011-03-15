import unittest

import persistent.interfaces
import ZODB.DB
import ZODB.MappingStorage
import transaction
import zope.app.keyreference.interfaces
import zope.app.keyreference.persistent
import zope.app.testing.placelesssetup
import zope.component
import zope.event

import zope.locking.testing
import zope.site.testing

from zope.testing import doctest


def setUp(test):
    zope.site.testing.siteSetUp()
    zope.app.testing.placelesssetup.setUp(test)
    db = test.globs['db'] = ZODB.DB(ZODB.MappingStorage.MappingStorage())
    test.globs['conn'] = db.open()
    test.globs['Demo'] = zope.locking.testing.Demo
    zope.component.provideAdapter(zope.locking.testing.DemoKeyReference)
    zope.component.provideAdapter(
        zope.app.keyreference.persistent.KeyReferenceToPersistent,
        [persistent.interfaces.IPersistent],
        zope.app.keyreference.interfaces.IKeyReference)
    zope.component.provideAdapter(
        zope.app.keyreference.persistent.connectionOfPersistent,
        [persistent.interfaces.IPersistent])
    events = test.globs['events'] = []
    zope.event.subscribers.append(events.append)

def tearDown(test):
    zope.site.testing.siteTearDown()
    zope.app.testing.placelesssetup.tearDown(test)
    transaction.abort()
    test.globs['conn'].close()
    test.globs['db'].close()
    events = test.globs.pop('events')
    assert zope.event.subscribers.pop().__self__ is events
    del events[:] # being paranoid

def test_suite():
    optionflags = doctest.ELLIPSIS
    return unittest.TestSuite(
        doctest.DocFileSuite(
            'README.txt',
            'annoying.txt',
            'cleanup.txt',
            'generations.txt',
            optionflags=optionflags,
            setUp=setUp, tearDown=tearDown),
       )

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
