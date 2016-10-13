
"""Some simple microbenchmarks for Python's threading support.

Current microbenchmarks:
    - *_count: count down from a given large number. Example used by David
               Beazley in his talk on the GIL (http://blip.tv/file/2232410). The
               iterative version is named iterative_count, the threaded version
               is threaded_count.

Example usage:
    ./bm_threading.py --num_threads=8 --check_interval=1000 threaded_count
"""

# Python imports
import sys
import threading

# Local imports
import perf
from six.moves import xrange


def count(iterations=1000000):
    """Count down from a given starting point."""
    while iterations > 0:
        iterations -= 1


def test_iterative_count(loops, num_threads):
    range_it = xrange(loops)
    t0 = perf.perf_counter()

    for _ in range_it:
        for _ in xrange(num_threads):
            count()

    return perf.perf_counter() - t0


def test_threaded_count(loops, num_threads):
    range_it = xrange(loops)
    t0 = perf.perf_counter()

    for _ in range_it:
        threads = [threading.Thread(target=count)
                   for _ in xrange(num_threads)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    return perf.perf_counter() - t0


def add_cmdline_args(cmd, args):
    if args.num_threads:
        cmd.extend(('--num_threads', str(args.num_threads)))
    if args.check_interval:
        cmd.extend(('--check_interval', str(args.check_interval)))
    cmd.append(args.benchmark)


if __name__ == "__main__":
    runner = perf.Runner(add_cmdline_args=add_cmdline_args)
    runner.metadata[
        'description'] = "Test the performance of Python's threads."

    benchmarks = {"iterative_count": test_iterative_count,
                  "threaded_count": test_threaded_count}

    parser = runner.argparser
    parser.add_argument("--num_threads", action="store", type=int, default=2,
                        dest="num_threads", help="Number of threads to test.")
    parser.add_argument("--check_interval", action="store", type=int,
                        default=sys.getcheckinterval(),
                        dest="check_interval",
                        help="Value to pass to sys.setcheckinterval().")
    runner.argparser.add_argument("benchmark", choices=sorted(benchmarks))
    options = runner.parse_args()

    name = 'threading_%s' % options.benchmark
    bench_func = benchmarks[options.benchmark]

    sys.setcheckinterval(options.check_interval)
    runner.bench_sample_func(name, bench_func, options.num_threads)
