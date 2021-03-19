import logging
import os.path
import subprocess
import sys
import traceback
try:
    import multiprocessing
except ImportError:
    multiprocessing = None

import pyperf

import pyperformance
from pyperformance.utils import temporary_file
from pyperformance.venv import PERFORMANCE_ROOT


class BenchmarkException(Exception):
    pass


# Utility functions


def Relative(*path):
    return os.path.join(PERFORMANCE_ROOT, 'benchmarks', *path)


def run_command(command, hide_stderr=True):
    if hide_stderr:
        kw = {'stderr': subprocess.PIPE}
    else:
        kw = {}

    logging.info("Running `%s`",
                 " ".join(list(map(str, command))))

    # Explicitly flush standard streams, required if streams are buffered
    # (not TTY) to write lines in the expected order
    sys.stdout.flush()
    sys.stderr.flush()

    proc = subprocess.Popen(command,
                            universal_newlines=True,
                            **kw)
    try:
        stderr = proc.communicate()[1]
    except:   # noqa
        if proc.stderr:
            proc.stderr.close()
        try:
            proc.kill()
        except OSError:
            # process already exited
            pass
        proc.wait()
        raise

    if proc.returncode != 0:
        if hide_stderr:
            sys.stderr.flush()
            sys.stderr.write(stderr)
            sys.stderr.flush()
        raise RuntimeError("Benchmark died")


def copy_perf_options(cmd, options):
    if options.debug_single_value:
        cmd.append('--debug-single-value')
    elif options.rigorous:
        cmd.append('--rigorous')
    elif options.fast:
        cmd.append('--fast')

    if options.verbose:
        cmd.append('--verbose')

    if options.affinity:
        cmd.append('--affinity=%s' % options.affinity)
    if options.track_memory:
        cmd.append('--track-memory')
    if options.inherit_environ:
        cmd.append('--inherit-environ=%s' % ','.join(options.inherit_environ))


def run_perf_script(python, options, name, extra_args=[]):
    bm_path = Relative("bm_%s.py" % name)
    cmd = list(python)
    cmd.append('-u')
    cmd.append(bm_path)
    cmd.extend(extra_args)
    copy_perf_options(cmd, options)

    with temporary_file() as tmp:
        cmd.extend(('--output', tmp))
        run_command(cmd, hide_stderr=not options.verbose)
        return pyperf.BenchmarkSuite.load(tmp)


def run_benchmarks(bench_funcs, should_run, cmd_prefix, options):
    suite = None
    to_run = sorted(should_run)
    run_count = str(len(to_run))
    errors = []

    for index, name in enumerate(to_run):
        func = bench_funcs[name]
        print("[%s/%s] %s..." %
              (str(index + 1).rjust(len(run_count)), run_count, name))
        sys.stdout.flush()

        def add_bench(dest_suite, obj):
            if isinstance(obj, pyperf.BenchmarkSuite):
                benchmarks = obj
            else:
                benchmarks = (obj,)

            version = pyperformance.__version__
            for bench in benchmarks:
                bench.update_metadata({'performance_version': version})

                if dest_suite is not None:
                    dest_suite.add_benchmark(bench)
                else:
                    dest_suite = pyperf.BenchmarkSuite([bench])

            return dest_suite

        try:
            bench = func(cmd_prefix, options)
        except Exception as exc:
            print("ERROR: Benchmark %s failed: %s" % (name, exc))
            traceback.print_exc()
            errors.append(name)
        else:
            suite = add_bench(suite, bench)

    print()

    return (suite, errors)
