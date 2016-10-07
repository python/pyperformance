import perf
from six.moves import xrange

from pybench import Test

# Check for new-style class support:
try:
    class c(object):
        pass
except NameError:
    raise ImportError

###


class CreateNewInstances(Test):

    version = 2.0
    operations = 3 + 7 + 4

    def test(self, loops):

        class c(object):
            pass

        class d(object):

            def __init__(self, a, b, c):
                self.a = a
                self.b = b
                self.c = c

        class e(object):

            def __init__(self, a, b, c=4):
                self.a = a
                self.b = b
                self.c = c
                self.d = a
                self.e = b
                self.f = c

        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for i in range_it:
            o = c()           # noqa
            o1 = c()          # noqa
            o2 = c()          # noqa
            p = d(i, i, 3)    # noqa
            p1 = d(i, i, 3)   # noqa
            p2 = d(i, 3, 3)   # noqa
            p3 = d(3, i, 3)   # noqa
            p4 = d(i, i, i)   # noqa
            p5 = d(3, i, 3)   # noqa
            p6 = d(i, i, i)   # noqa
            q = e(i, i, 3)    # noqa
            q1 = e(i, i, 3)   # noqa
            q2 = e(i, i, 3)   # noqa
            q3 = e(i, i)      # noqa

        return perf.perf_counter() - t0
