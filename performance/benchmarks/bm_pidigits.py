# coding: utf-8
"""
Calculating some of the digits of π.  This benchmark stresses big integer
arithmetic.
"""

# Python imports
import itertools

# Local imports
from six.moves import xrange, map as imap
import perf.text_runner


NDIGITS = 2000


_map = imap
_count = itertools.count
_islice = itertools.islice

# Adapted from code on http://shootout.alioth.debian.org/


def gen_x():
    return _map(lambda k: (k, 4 * k + 2, 0, 2 * k + 1), _count(1))


def compose(a, b):
    aq, ar, as_, at = a
    bq, br, bs, bt = b
    return (aq * bq,
            aq * br + ar * bt,
            as_ * bq + at * bs,
            as_ * br + at * bt)


def extract(z, j):
    q, r, s, t = z
    return (q * j + r) // (s * j + t)


def gen_pi_digits():
    z = (1, 0, 0, 1)
    x = gen_x()
    while 1:
        y = extract(z, 3)
        while y != extract(z, 4):
            z = compose(z, next(x))
            y = extract(z, 3)
        z = compose((10, -10 * y, 0, 1), z)
        yield y


def calc_ndigits(n):
    return list(_islice(gen_pi_digits(), n))


def bench_pidigits(loops):
    range_it = xrange(loops)
    t0 = perf.perf_counter()

    for _ in range_it:
        calc_ndigits(NDIGITS)

    return perf.perf_counter() - t0


if __name__ == "__main__":
    runner = perf.text_runner.TextRunner(name='pidigits')
    runner.metadata['description'] = "Test the performance of pi calculation."
    runner.bench_sample_func(bench_pidigits)
