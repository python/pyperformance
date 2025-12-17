"""Test the performance of random module.

This benchmark was available as `python -m random --test` in Python 3.13.

Authors: Guido van Rossum (original), Semyon Moroz (pyperformance port).
"""

import random

import pyperf


def bench_func(func, args):
    def wrapper(loops):
        range_it = range(loops)
        t0 = pyperf.perf_counter()

        for _ in range_it:
            func(*args)

        return pyperf.perf_counter() - t0

    return wrapper


BENCHMARKS = (
    # (func, args)
    (random.random, ()),
    (random.normalvariate, (0.0, 1.0)),
    (random.lognormvariate, (0.0, 1.0)),
    (random.vonmisesvariate, (0.0, 1.0)),
    (random.binomialvariate, (15, 0.60)),
    (random.binomialvariate, (100, 0.75)),
    (random.gammavariate, (0.01, 1.0)),
    (random.gammavariate, (0.1, 1.0)),
    (random.gammavariate, (0.1, 2.0)),
    (random.gammavariate, (0.5, 1.0)),
    (random.gammavariate, (0.9, 1.0)),
    (random.gammavariate, (1.0, 1.0)),
    (random.gammavariate, (2.0, 1.0)),
    (random.gammavariate, (20.0, 1.0)),
    (random.gammavariate, (200.0, 1.0)),
    (random.gauss, (0.0, 1.0)),
    (random.betavariate, (3.0, 3.0)),
    (random.triangular, (0.0, 1.0, 1.0 / 3.0)),
)


if __name__ == '__main__':
    runner = pyperf.Runner()
    runner.metadata['description'] = 'random benchmark: core random distributions'

    for func, args in BENCHMARKS:
        name = f'random.{func.__name__}{args}'
        runner.bench_time_func(name, bench_func(func, args))
