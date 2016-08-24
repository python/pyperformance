import perf
import six
from six.moves import xrange

from pybench import Test


if six.PY3:
    long = int


class SimpleIntegerArithmetic(Test):

    version = 2.0
    operations = 5 * (3 + 5 + 5 + 3 + 3 + 3)
    # loop body repeated 5 times
    inner_loops = 5

    def test(self, loops):
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:

            a = 2
            b = 3
            c = 3

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2
            b = 3
            c = 3

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2
            b = 3
            c = 3

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2
            b = 3
            c = 3

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2
            b = 3
            c = 3

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

        return perf.perf_counter() - t0


class SimpleFloatArithmetic(Test):

    version = 2.0
    operations = 5 * (3 + 5 + 5 + 3 + 3 + 3)
    # loop body repeated 5 times
    inner_loops = 5

    def test(self, loops):
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:

            a = 2.1
            b = 3.3332
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2.1
            b = 3.3332
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2.1
            b = 3.3332
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2.1
            b = 3.3332
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2.1
            b = 3.3332
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

        return perf.perf_counter() - t0


class SimpleIntFloatArithmetic(Test):

    version = 2.0
    operations = 5 * (3 + 5 + 5 + 3 + 3 + 3)
    inner_loops = 5

    def test(self, loops):
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:

            a = 2
            b = 3
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2
            b = 3
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2
            b = 3
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2
            b = 3
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2
            b = 3
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

        return perf.perf_counter() - t0


class SimpleLongArithmetic(Test):

    version = 2.0
    operations = 5 * (3 + 5 + 5 + 3 + 3 + 3)
    inner_loops = 5

    def test(self, loops):
        A = long(2220001)
        B = long(100001)
        C = long(30005)
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:

            a = A
            b = B
            c = C

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = A
            b = B
            c = C

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = A
            b = B
            c = C

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = A
            b = B
            c = C

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = A
            b = B
            c = C

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

        return perf.perf_counter() - t0


class SimpleComplexArithmetic(Test):

    version = 2.0
    operations = 5 * (3 + 5 + 5 + 3 + 3 + 3)
    inner_loops = 5

    def test(self, loops):
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:

            a = 2 + 3j
            b = 2.5 + 4.5j
            c = 1.2 + 6.2j

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2 + 3j
            b = 2.5 + 4.5j
            c = 1.2 + 6.2j

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2 + 3j
            b = 2.5 + 4.5j
            c = 1.2 + 6.2j

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2 + 3j
            b = 2.5 + 4.5j
            c = 1.2 + 6.2j

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2 + 3j
            b = 2.5 + 4.5j
            c = 1.2 + 6.2j

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

        return perf.perf_counter() - t0
