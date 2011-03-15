
import datetime
import pytz

# this is a small convenience, but is more important as a
# convenient monkey-patch opportunity for the package's doctests.

_now = None

def now():
    if _now is not None:
        return _now
    return datetime.datetime.now(pytz.utc)

def set_now(dt):
    global _now
    _now = dt

def reset():
    global _now
    _now = None

try:
    import zope.testing.cleanup
except ImportError:
    pass
else:
    zope.testing.cleanup.addCleanUp(reset)
