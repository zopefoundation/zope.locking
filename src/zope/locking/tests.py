import unittest
from zope.app.testing import placelesssetup
from zope.testing import doctest 

def setUp(test):
    placelesssetup.setUp(test)
    events = test.globs['events'] = []
    import zope.event
    zope.event.subscribers.append(events.append)

def tearDown(test):
    placelesssetup.tearDown(test)
    events = test.globs.pop('events')
    import zope.event
    assert zope.event.subscribers.pop().__self__ is events
    del events[:] # being paranoid

def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite(
            'README.txt',
            setUp=setUp, tearDown=tearDown),
        doctest.DocFileSuite(
            'annoying.txt',
            setUp=setUp, tearDown=tearDown),
        doctest.DocFileSuite(
            'cleanup.txt',
            setUp=setUp, tearDown=tearDown),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite') 
