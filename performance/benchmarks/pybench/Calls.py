import perf
from six.moves import xrange
from pybench import Test


class PythonFunctionCalls(Test):

    version = 2.1
    operations = 5 * (1 + 4 + 4 + 2)
    inner_loops = 5

    def test(self, loops):

        global f, f1, g, h

        # define functions
        def f():
            pass

        def f1(x):
            pass

        def g(a, b, c):
            return a, b, c

        def h(a, b, c, d=1, e=2, f=3):
            return d, e, f

        range_it = xrange(loops)
        t0 = perf.perf_counter()

        # do calls
        for i in range_it:

            f()
            f1(i)
            f1(i)
            f1(i)
            f1(i)
            g(i, i, i)
            g(i, i, i)
            g(i, i, i)
            g(i, i, i)
            h(i, i, 3, i, i)
            h(i, i, i, 2, i, 3)

            f()
            f1(i)
            f1(i)
            f1(i)
            f1(i)
            g(i, i, i)
            g(i, i, i)
            g(i, i, i)
            g(i, i, i)
            h(i, i, 3, i, i)
            h(i, i, i, 2, i, 3)

            f()
            f1(i)
            f1(i)
            f1(i)
            f1(i)
            g(i, i, i)
            g(i, i, i)
            g(i, i, i)
            g(i, i, i)
            h(i, i, 3, i, i)
            h(i, i, i, 2, i, 3)

            f()
            f1(i)
            f1(i)
            f1(i)
            f1(i)
            g(i, i, i)
            g(i, i, i)
            g(i, i, i)
            g(i, i, i)
            h(i, i, 3, i, i)
            h(i, i, i, 2, i, 3)

            f()
            f1(i)
            f1(i)
            f1(i)
            f1(i)
            g(i, i, i)
            g(i, i, i)
            g(i, i, i)
            g(i, i, i)
            h(i, i, 3, i, i)
            h(i, i, i, 2, i, 3)

        return perf.perf_counter() - t0


###

class ComplexPythonFunctionCalls(Test):

    version = 2.0
    operations = 4 * 5
    inner_loops = 5

    def test(self, loops):

        # define functions
        def f(a, b, c, d=1, e=2, f=3):
            return f

        args = 1, 2
        kwargs = dict(c=3, d=4, e=5)

        range_it = xrange(loops)
        t0 = perf.perf_counter()

        # do calls
        for i in range_it:
            f(a=i, b=i, c=i)
            f(f=i, e=i, d=i, c=2, b=i, a=3)
            f(1, b=i, **kwargs)
            f(*args, **kwargs)

            f(a=i, b=i, c=i)
            f(f=i, e=i, d=i, c=2, b=i, a=3)
            f(1, b=i, **kwargs)
            f(*args, **kwargs)

            f(a=i, b=i, c=i)
            f(f=i, e=i, d=i, c=2, b=i, a=3)
            f(1, b=i, **kwargs)
            f(*args, **kwargs)

            f(a=i, b=i, c=i)
            f(f=i, e=i, d=i, c=2, b=i, a=3)
            f(1, b=i, **kwargs)
            f(*args, **kwargs)

            f(a=i, b=i, c=i)
            f(f=i, e=i, d=i, c=2, b=i, a=3)
            f(1, b=i, **kwargs)
            f(*args, **kwargs)

        return perf.perf_counter() - t0


###

class BuiltinFunctionCalls(Test):

    version = 2.0
    operations = 5 * (2 + 5 + 5 + 5)
    inner_loops = 5

    def test(self, loops):

        # localize functions
        f0 = globals
        f1 = hash
        f2 = divmod
        f3 = max

        range_it = xrange(loops)
        t0 = perf.perf_counter()

        # do calls
        for i in range_it:
            f0()
            f0()
            f1(i)
            f1(i)
            f1(i)
            f1(i)
            f1(i)
            f2(1, 2)
            f2(1, 2)
            f2(1, 2)
            f2(1, 2)
            f2(1, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)

            f0()
            f0()
            f1(i)
            f1(i)
            f1(i)
            f1(i)
            f1(i)
            f2(1, 2)
            f2(1, 2)
            f2(1, 2)
            f2(1, 2)
            f2(1, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)

            f0()
            f0()
            f1(i)
            f1(i)
            f1(i)
            f1(i)
            f1(i)
            f2(1, 2)
            f2(1, 2)
            f2(1, 2)
            f2(1, 2)
            f2(1, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)

            f0()
            f0()
            f1(i)
            f1(i)
            f1(i)
            f1(i)
            f1(i)
            f2(1, 2)
            f2(1, 2)
            f2(1, 2)
            f2(1, 2)
            f2(1, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)

            f0()
            f0()
            f1(i)
            f1(i)
            f1(i)
            f1(i)
            f1(i)
            f2(1, 2)
            f2(1, 2)
            f2(1, 2)
            f2(1, 2)
            f2(1, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)
            f3(1, 3, 2)

        return perf.perf_counter() - t0

###


class PythonMethodCalls(Test):

    version = 2.0
    operations = 5 * (6 + 5 + 4)
    inner_loops = 5

    def test(self, loops):

        class c:

            x = 2
            s = 'string'

            def f(self):

                return self.x

            def j(self, a, b):

                self.y = a
                self.t = b
                return self.y

            def k(self, a, b, c=3):

                self.y = a
                self.s = b
                self.t = c

        o = c()
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for i in range_it:

            o.f()
            o.f()
            o.f()
            o.f()
            o.f()
            o.f()
            o.j(i, i)
            o.j(i, i)
            o.j(i, 2)
            o.j(i, 2)
            o.j(2, 2)
            o.k(i, i)
            o.k(i, 2)
            o.k(i, 2, 3)
            o.k(i, i, c=4)

            o.f()
            o.f()
            o.f()
            o.f()
            o.f()
            o.f()
            o.j(i, i)
            o.j(i, i)
            o.j(i, 2)
            o.j(i, 2)
            o.j(2, 2)
            o.k(i, i)
            o.k(i, 2)
            o.k(i, 2, 3)
            o.k(i, i, c=4)

            o.f()
            o.f()
            o.f()
            o.f()
            o.f()
            o.f()
            o.j(i, i)
            o.j(i, i)
            o.j(i, 2)
            o.j(i, 2)
            o.j(2, 2)
            o.k(i, i)
            o.k(i, 2)
            o.k(i, 2, 3)
            o.k(i, i, c=4)

            o.f()
            o.f()
            o.f()
            o.f()
            o.f()
            o.f()
            o.j(i, i)
            o.j(i, i)
            o.j(i, 2)
            o.j(i, 2)
            o.j(2, 2)
            o.k(i, i)
            o.k(i, 2)
            o.k(i, 2, 3)
            o.k(i, i, c=4)

            o.f()
            o.f()
            o.f()
            o.f()
            o.f()
            o.f()
            o.j(i, i)
            o.j(i, i)
            o.j(i, 2)
            o.j(i, 2)
            o.j(2, 2)
            o.k(i, i)
            o.k(i, 2)
            o.k(i, 2, 3)
            o.k(i, i, c=4)

        return perf.perf_counter() - t0


###

class Recursion(Test):

    version = 2.0
    operations = 5
    inner_loops = 5

    def test(self, loops):

        global f

        def f(x):

            if x > 1:
                return f(x - 1)
            return 1

        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:
            f(10)
            f(10)
            f(10)
            f(10)
            f(10)

        return perf.perf_counter() - t0
