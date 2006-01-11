
import datetime
import pytz

# this is a small convenience, but is more important as a convenient monkey-
# patch opportunity for the package's README.txt doctest.
def now():
    return datetime.datetime.now(pytz.utc)
