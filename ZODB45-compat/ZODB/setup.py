# Setup for stub ZODB/BTrees/persistent/ZEO eggs to depend on ZODB3.
# These are stub packages fro ZODB3 to be forward compatible with ZODB4/5.

from setuptools import setup
from os.path import basename, dirname, join
import re

# find our name (ZODB/BTrees/persistent/ZEO)
NAME = basename(dirname(__file__))  # .../ZODB45-compat/ZODB/setup.py -> ZODB

# find out ZODB3 version

# grep searches text for pattern.
# return re.Match object or raises if pattern was not found.
def grep1(pattern, text):
    rex = re.compile(pattern, re.MULTILINE)
    m = rex.search(text)
    if m is None:
        raise RuntimeError('%r not found' % pattern)
    return m

# read file content
def readfile(path):
    with open(path, 'r') as f:
        return f.read()

_ = readfile(join(dirname(__file__), '../../setup.py'))
_ = grep1('^VERSION = "(.*)"$', _)
VERSION = _.group(1)


# setup stub ZODB/BTrees/... egg that just depends on ZODB3
setup(name=NAME,
      version=VERSION,
      packages = [],
      install_requires = ['ZODB3 == %s' % VERSION],
)
