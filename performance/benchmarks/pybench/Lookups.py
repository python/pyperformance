import perf
from six.moves import xrange

from pybench import Test


class SpecialClassAttribute(Test):

    version = 2.0
    operations = 5 * (12 + 12)
    inner_loops = 5

    def test(self, loops):

        class c:
            pass

        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

        return perf.perf_counter() - t0


class NormalClassAttribute(Test):

    version = 2.0
    operations = 5 * (12 + 12)
    inner_loops = 5

    def test(self, loops):

        class c:
            pass

        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

        return perf.perf_counter() - t0


class SpecialInstanceAttribute(Test):

    version = 2.0
    operations = 5 * (12 + 12)
    inner_loops = 5

    def test(self, loops):

        class c:
            pass
        o = c()

        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

        return perf.perf_counter() - t0


class NormalInstanceAttribute(Test):

    version = 2.0
    operations = 5 * (12 + 12)
    inner_loops = 5

    def test(self, loops):

        class c:
            pass
        o = c()

        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

        return perf.perf_counter() - t0


class BuiltinMethodLookup(Test):

    version = 2.0
    operations = 5 * (3 * 5 + 3 * 5)
    inner_loops = 5

    def test(self, loops):

        l = []
        d = {}

        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:

            l.append
            l.append
            l.append
            l.append
            l.append

            l.insert
            l.insert
            l.insert
            l.insert
            l.insert

            l.sort
            l.sort
            l.sort
            l.sort
            l.sort

            # d.has_key
            # d.has_key
            # d.has_key
            # d.has_key
            # d.has_key

            d.items
            d.items
            d.items
            d.items
            d.items

            d.get
            d.get
            d.get
            d.get
            d.get

            l.append
            l.append
            l.append
            l.append
            l.append

            l.insert
            l.insert
            l.insert
            l.insert
            l.insert

            l.sort
            l.sort
            l.sort
            l.sort
            l.sort

            # d.has_key
            # d.has_key
            # d.has_key
            # d.has_key
            # d.has_key

            d.items
            d.items
            d.items
            d.items
            d.items

            d.get
            d.get
            d.get
            d.get
            d.get

            l.append
            l.append
            l.append
            l.append
            l.append

            l.insert
            l.insert
            l.insert
            l.insert
            l.insert

            l.sort
            l.sort
            l.sort
            l.sort
            l.sort

            # d.has_key
            # d.has_key
            # d.has_key
            # d.has_key
            # d.has_key

            d.items
            d.items
            d.items
            d.items
            d.items

            d.get
            d.get
            d.get
            d.get
            d.get

            l.append
            l.append
            l.append
            l.append
            l.append

            l.insert
            l.insert
            l.insert
            l.insert
            l.insert

            l.sort
            l.sort
            l.sort
            l.sort
            l.sort

            # d.has_key
            # d.has_key
            # d.has_key
            # d.has_key
            # d.has_key

            d.items
            d.items
            d.items
            d.items
            d.items

            d.get
            d.get
            d.get
            d.get
            d.get

            l.append
            l.append
            l.append
            l.append
            l.append

            l.insert
            l.insert
            l.insert
            l.insert
            l.insert

            l.sort
            l.sort
            l.sort
            l.sort
            l.sort

            # d.has_key
            # d.has_key
            # d.has_key
            # d.has_key
            # d.has_key

            d.items
            d.items
            d.items
            d.items
            d.items

            d.get
            d.get
            d.get
            d.get
            d.get

        return perf.perf_counter() - t0
