#!python

# Setup file for pybench
#
# This file has to import all tests to be run; it is executed as
# Python source file, so you can do all kinds of manipulations here
# rather than having to edit the tests themselves.
#
# Note: Please keep this module compatible to Python 1.5.2.
#
# Tests may include features in later Python versions, but these
# should then be embedded in try-except clauses in this configuration
# module.

# Defaults
Number_of_rounds = 10

# Import tests
from Arithmetic import *   # noqa
from Calls import *   # noqa
from Constructs import *   # noqa
from Lookups import *   # noqa
from Instances import *   # noqa
try:
    from NewInstances import *   # noqa
except ImportError:
    pass
from Lists import *   # noqa
from Tuples import *   # noqa
from Dict import *   # noqa
from Exceptions import *   # noqa
try:
    from With import *   # noqa
except SyntaxError:
    pass
from Imports import *   # noqa
from Strings import *   # noqa
from Numbers import *   # noqa
try:
    from Unicode import *   # noqa
except (ImportError, SyntaxError):
    pass
