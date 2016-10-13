
"""Microbenchmark for method call overhead.

This measures simple method calls that are predictable, do not use varargs or
kwargs, and do not use tuple unpacking.
"""

import perf
from six.moves import xrange


class Foo(object):

    def foo(self, a, b, c, d):
        # 20 calls
        self.bar(a, b, c)
        self.bar(a, b, c)
        self.bar(a, b, c)
        self.bar(a, b, c)
        self.bar(a, b, c)
        self.bar(a, b, c)
        self.bar(a, b, c)
        self.bar(a, b, c)
        self.bar(a, b, c)
        self.bar(a, b, c)
        self.bar(a, b, c)
        self.bar(a, b, c)
        self.bar(a, b, c)
        self.bar(a, b, c)
        self.bar(a, b, c)
        self.bar(a, b, c)
        self.bar(a, b, c)
        self.bar(a, b, c)
        self.bar(a, b, c)
        self.bar(a, b, c)

    def bar(self, a, b, c):
        # 20 calls
        self.baz(a, b)
        self.baz(a, b)
        self.baz(a, b)
        self.baz(a, b)
        self.baz(a, b)
        self.baz(a, b)
        self.baz(a, b)
        self.baz(a, b)
        self.baz(a, b)
        self.baz(a, b)
        self.baz(a, b)
        self.baz(a, b)
        self.baz(a, b)
        self.baz(a, b)
        self.baz(a, b)
        self.baz(a, b)
        self.baz(a, b)
        self.baz(a, b)
        self.baz(a, b)
        self.baz(a, b)

    def baz(self, a, b):
        # 20 calls
        self.quux(a)
        self.quux(a)
        self.quux(a)
        self.quux(a)
        self.quux(a)
        self.quux(a)
        self.quux(a)
        self.quux(a)
        self.quux(a)
        self.quux(a)
        self.quux(a)
        self.quux(a)
        self.quux(a)
        self.quux(a)
        self.quux(a)
        self.quux(a)
        self.quux(a)
        self.quux(a)
        self.quux(a)
        self.quux(a)

    def quux(self, a):
        # 20 calls
        self.qux()
        self.qux()
        self.qux()
        self.qux()
        self.qux()
        self.qux()
        self.qux()
        self.qux()
        self.qux()
        self.qux()
        self.qux()
        self.qux()
        self.qux()
        self.qux()
        self.qux()
        self.qux()
        self.qux()
        self.qux()
        self.qux()
        self.qux()

    def qux(self):
        pass


def test_calls(loops):
    f = Foo()
    range_it = xrange(loops)
    t0 = perf.perf_counter()

    for _ in range_it:
        # 20 calls
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)
        f.foo(1, 2, 3, 4)

    return perf.perf_counter() - t0


if __name__ == "__main__":
    runner = perf.Runner()
    runner.metadata['description'] = ("Test the performance of simple "
                                      "Python-to-Python method calls")
    runner.bench_sample_func('call_method', test_calls, inner_loops=20)
