import sys
import traceback
try:
    import multiprocessing
except ImportError:
    multiprocessing = None

import pyperf
import pyperformance


class BenchmarkException(Exception):
    pass


# Utility functions

def get_pyperf_opts(options):
    opts = []

    if options.debug_single_value:
        opts.append('--debug-single-value')
    elif options.rigorous:
        opts.append('--rigorous')
    elif options.fast:
        opts.append('--fast')

    if options.verbose:
        opts.append('--verbose')

    if options.affinity:
        opts.append('--affinity=%s' % options.affinity)
    if options.track_memory:
        opts.append('--track-memory')
    if options.inherit_environ:
        opts.append('--inherit-environ=%s' % ','.join(options.inherit_environ))

    return opts


def run_benchmarks(should_run, cmd_prefix, options):
    suite = None
    to_run = sorted(should_run)
    run_count = str(len(to_run))
    errors = []

    pyperf_opts = get_pyperf_opts(options)

    for index, bench in enumerate(to_run):
        name = bench.name
        print("[%s/%s] %s..." %
              (str(index + 1).rjust(len(run_count)), run_count, name))
        sys.stdout.flush()

        def add_bench(dest_suite, obj):
            if isinstance(obj, pyperf.BenchmarkSuite):
                benchmarks = obj
            else:
                benchmarks = (obj,)

            version = pyperformance.__version__
            for res in benchmarks:
                res.update_metadata({'performance_version': version})

                if dest_suite is not None:
                    dest_suite.add_benchmark(res)
                else:
                    dest_suite = pyperf.BenchmarkSuite([res])

            return dest_suite

        try:
            result = bench.run(cmd_prefix, pyperf_opts, verbose=options.verbose)
        except Exception as exc:
            print("ERROR: Benchmark %s failed: %s" % (name, exc))
            traceback.print_exc()
            errors.append(name)
        else:
            suite = add_bench(suite, result)

    print()

    return (suite, errors)
