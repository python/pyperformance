from __future__ import division, with_statement, print_function, absolute_import

import logging
import os.path
import platform
import subprocess
import sys
try:
    import multiprocessing
except ImportError:
    multiprocessing = None

import perf

import performance
from performance.compare import display_benchmark_suite
from performance.venv import interpreter_version


class BenchmarkException(Exception):
    pass



### Utility functions


def LogCall(command):
    command = list(map(str, command))
    logging.info("Running `%s`", " ".join(command))
    return command


def CallAndCaptureOutput(command, hide_stderr=True):
    if hide_stderr:
        kw = {'stderr': subprocess.PIPE}
    else:
        kw = {}
    proc = subprocess.Popen(LogCall(command),
                               stdout=subprocess.PIPE,
                               universal_newlines=True,
                               **kw)
    try:
        stdout, stderr = proc.communicate()
    except:
        proc.stdout.close()
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
    return stdout


def copy_perf_options(cmd, options):
    if options.debug_single_sample:
        cmd.append('--debug-single-sample')
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

def run_perf_script(python, options, bm_path, extra_args=[]):
    bench_args = [bm_path]
    copy_perf_options(bench_args, options)
    bench_args.append("--stdout")

    command = python + bench_args + extra_args
    stdout = CallAndCaptureOutput(command, hide_stderr=not options.verbose)

    bench = perf.Benchmark.loads(stdout)
    bench.update_metadata({'performance_version': performance.__version__})
    return bench


def _ExpandBenchmarkName(bm_name, bench_groups):
    """Recursively expand name benchmark names.

    Args:
        bm_name: string naming a benchmark or benchmark group.

    Yields:
        Names of actual benchmarks, with all group names fully expanded.
    """
    expansion = bench_groups.get(bm_name)
    if expansion:
        for name in expansion:
            for name in _ExpandBenchmarkName(name, bench_groups):
                yield name
    else:
        yield bm_name


def ParseBenchmarksOption(benchmarks_opt, bench_groups, fast=False):
    """Parses and verifies the --benchmarks option.

    Args:
        benchmarks_opt: the string passed to the -b option on the command line.
        bench_groups: the collection of benchmark groups to pull from

    Returns:
        A set() of the names of the benchmarks to run.
    """
    legal_benchmarks = bench_groups["all"]
    benchmarks = benchmarks_opt.split(",")
    positive_benchmarks = set(
        bm.lower() for bm in benchmarks if bm and bm[0] != "-")
    negative_benchmarks = set(
        bm[1:].lower() for bm in benchmarks if bm and bm[0] == "-")

    should_run = set()
    if not positive_benchmarks:
        should_run = set(_ExpandBenchmarkName("default", bench_groups))

    for name in positive_benchmarks:
        for bm in _ExpandBenchmarkName(name, bench_groups):
            if bm not in legal_benchmarks:
                logging.warning("No benchmark named %s", bm)
            else:
                should_run.add(bm)
    for bm in negative_benchmarks:
        if bm in bench_groups:
            raise ValueError("Negative groups not supported: -%s" % bm)
        elif bm not in legal_benchmarks:
            logging.warning("No benchmark named %s", bm)
        else:
            should_run.remove(bm)
    return should_run


def FilterBenchmarks(benchmarks, bench_funcs, python):
    """Filters out benchmarks not supported by both Pythons.

    Args:
        benchmarks: a set() of benchmark names
        bench_funcs: dict mapping benchmark names to functions
        python: the interpereter commands (as lists)

    Returns:
        The filtered set of benchmark names
    """
    basever = interpreter_version(python)
    for bm in list(benchmarks):
        minver, maxver = getattr(bench_funcs[bm], '_range', ('2.0', '4.0'))
        if not minver <= basever <= maxver:
            benchmarks.discard(bm)
            logging.info("Skipping benchmark %s; not compatible with "
                         "Python %s" % (bm, basever))
            continue
    return benchmarks


def run_benchmarks(bench_funcs, should_run, cmd_prefix, options):
    suite = perf.BenchmarkSuite()
    to_run = list(sorted(should_run))
    run_count = str(len(to_run))
    for index, name in enumerate(to_run):
        func = bench_funcs[name]
        print("[%s/%s] %s..." %
              (str(index+1).rjust(len(run_count)), run_count, name))
        sys.stdout.flush()

        def add_bench(dest_suite, bench):
            if isinstance(bench, perf.BenchmarkSuite):
                benchmarks = bench.get_benchmarks()
                for bench in benchmarks:
                    dest_suite.add_benchmark(bench)
            else:
                dest_suite.add_benchmark(bench)

        try:
            bench = func(cmd_prefix, options)
        except Exception as exc:
            print("ERROR: Benchmark %s failed: %s" % (name, exc))
            sys.exit(1)

        add_bench(suite, bench)

    print()

    return suite


def cmd_run(parser, options, bench_funcs, bench_groups):
    logging.basicConfig(level=logging.INFO)

    print("Python benchmark suite %s" % performance.__version__)
    print()

    if options.output and os.path.exists(options.output):
        print("ERROR: the output file %s already exists!" % options.output)
        sys.exit(1)

    if not os.path.isabs(sys.executable):
        print("ERROR: sys.executable is not an absolute path")
        sys.exit(1)
    cmd_prefix = [sys.executable] + options.args.split()

    should_run = ParseBenchmarksOption(options.benchmarks, bench_groups,
                                       options.fast or options.debug_single_sample)

    should_run = FilterBenchmarks(should_run, bench_funcs, cmd_prefix)

    suite = run_benchmarks(bench_funcs, should_run, cmd_prefix, options)

    if options.output:
        suite.dump(options.output)

    if options.append:
        perf.add_runs(options.append, suite)

    display_benchmark_suite(suite)


def cmd_list(options, bench_funcs, bench_groups):
    funcs = bench_groups['all']
    python = [sys.executable]
    all_funcs = FilterBenchmarks(set(funcs), bench_funcs, python)

    if options.action == 'list':
        print("%s benchmarks:" % len(all_funcs))
        for func in sorted(all_funcs):
            print("- %s" % func)
    else:
        # list_groups
        for group, funcs in sorted(bench_groups.items()):
            funcs = set(funcs) & all_funcs
            if not funcs:
                # skip empty groups
                continue

            print("%s (%s):" % (group, len(funcs)))
            for func in sorted(funcs):
                print("- %s" % func)
            print()
