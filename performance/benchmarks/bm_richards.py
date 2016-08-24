
"""perf.py wrapper for the classic Richards benchmark.

See richards.py for copyright and history information.
"""

__author__ = "fijall@gmail.com (Maciej Fijalkowski)"
__contact__ = "collinwinter@google.com (Collin Winter)"


# Third party imports
import perf.text_runner
from six.moves import xrange

# Local imports
import richards


def bench_richards(loops):
    r = richards.Richards()

    range_it = xrange(loops)
    t0 = perf.perf_counter()

    for _ in range_it:
        r.run(iterations=1)

    return perf.perf_counter() - t0


if __name__ == "__main__":
    runner = perf.text_runner.TextRunner(name='richards')
    runner.metadata['description'] = ("Test the performance of "
                                      "the Richards benchmark")
    runner.bench_sample_func(bench_richards)
