import perf
from six.moves import xrange

from pybench import Test


class TupleSlicing(Test):

    version = 2.0
    operations = 3 * 25 * 10 * 7
    inner_loops = 25 * 30

    def test(self, loops):

        r = range(25)
        t = tuple(range(100))
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:

            for j in r:

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

                m = t[50:]
                m = t[:25]
                m = t[50:55]
                m = t[:-1]
                m = t[1:]
                m = t[-10:]
                m = t[:10]

        return perf.perf_counter() - t0


class SmallTuples(Test):

    version = 2.0
    operations = 5 * (1 + 3 + 6 + 2)
    inner_loops = 5

    def test(self, loops):
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:

            t = (1, 2, 3, 4, 5, 6)

            a, b, c, d, e, f = t
            a, b, c, d, e, f = t
            a, b, c, d, e, f = t

            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]

            l = list(t)
            t = tuple(l)

            t = (1, 2, 3, 4, 5, 6)

            a, b, c, d, e, f = t
            a, b, c, d, e, f = t
            a, b, c, d, e, f = t

            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]

            l = list(t)
            t = tuple(l)

            t = (1, 2, 3, 4, 5, 6)

            a, b, c, d, e, f = t
            a, b, c, d, e, f = t
            a, b, c, d, e, f = t

            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]

            l = list(t)
            t = tuple(l)

            t = (1, 2, 3, 4, 5, 6)

            a, b, c, d, e, f = t
            a, b, c, d, e, f = t
            a, b, c, d, e, f = t

            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]

            l = list(t)
            t = tuple(l)

            t = (1, 2, 3, 4, 5, 6)

            a, b, c, d, e, f = t
            a, b, c, d, e, f = t
            a, b, c, d, e, f = t

            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]
            a, b, c = t[:3]

            l = list(t)
            t = tuple(l)

        return perf.perf_counter() - t0
