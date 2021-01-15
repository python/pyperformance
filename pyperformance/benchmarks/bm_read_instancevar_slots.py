"""
Exercise reading instance members defined by __slots__.
"""
import pyperf


REPS = 100000


class Point:
    __slots__ = ("a", "b", "c")
    
    def __init__(self, a=0, b=0, c=0):
        self.a = a
        self.b = b
        self.c = c


def read_vars(p):
    return p.a + p.b + p.c


def benchmark(n):
    p = Point()
    assert read_vars(p) == 0
    for i in range(n):
        read_vars(p)
    assert read_vars(p) == 0


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Read __slots__ benchmark"

    reps = REPS
    runner.bench_func('read_instancevar_slots', benchmark, reps)
