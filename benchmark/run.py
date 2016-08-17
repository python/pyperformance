from __future__ import division, with_statement, print_function

import contextlib
import csv
import logging
import math
import os.path
import platform
import subprocess
import sys
import tempfile
import time
try:
    import multiprocessing
except ImportError:
    multiprocessing = None

# Third party imports
import perf
import statistics

from benchmark.venv import interpreter_version, which, ROOT_DIR
from benchmark.compare import BaseBenchmarkResult, compare_results


try:
    import resource
except ImportError:
    # Approximate child time using wall clock time.
    def GetChildUserTime():
        return time.time()
else:
    def GetChildUserTime():
        return resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime


def Relative(path):
    return os.path.join(ROOT_DIR, path)


def check_taskset():
    """Check the taskset command is available.

    Taskset specifies CPU affinity for a given workload, meaning that we can
    run the benchmarks on a given core to minimize run to run variation.

    Return None on success. Return an error message on error.
    """
    with open(os.devnull, "wb") as dev_null:
        # Try to pin a temporary Python process to CPU #0
        command = ["taskset", "--cpu-list", "0",
                   sys.executable, "-c", "pass"]
        try:
            exitcode = subprocess.call(command,
                                       stdout=dev_null, stderr=dev_null)
        except OSError as exc:
            return ("Command taskset not found: %s" % exc)

    if exitcode != 0:
        return ("Command taskset failed with exit code %s" % exitcode)

    return None


class BenchmarkError(BaseBenchmarkResult):
    """Object representing the error from a failed benchmark run."""

    def __init__(self, e):
        self.msg = str(e)

    def __str__(self):
        return self.msg


### Utility functions


def SimpleBenchmark(benchmark_function, python, options,
                    *args, **kwargs):
    """Abstract out the body for most simple benchmarks.

    Example usage:
        def BenchmarkSomething(*args, **kwargs):
            return SimpleBenchmark(MeasureSomething, *args, **kwargs)

    The *args, **kwargs style is recommended so as to minimize the number of
    places that have to be changed if we update benchmark arguments.

    Args:
        benchmark_function: callback that takes (python_path, options) and
            returns a RawData instance.
        python: path to the Python binary.
        options: optparse.Values instance.
        *args, **kwargs: will be passed through to benchmark_function.

    Returns:
        A BenchmarkResult object if the benchmark runs succeeded.
        A BenchmarkError object if either benchmark run failed.
    """
    try:
        return benchmark_function(python, options, *args, **kwargs)
    except subprocess.CalledProcessError as e:
        return BenchmarkError(e)


def _FormatData(num):
    return str(round(num, 2))

def SummarizeData(data, points=100, summary_func=max):
    """Summarize a large data set using a smaller number of points.

    This will divide up the original data set into `points` windows,
    using `summary_func` to summarize each window into a single point.

    Args:
        data: the original data set, as a list.
        points: optional; how many summary points to take. Default is 100.
        summary_func: optional; function to use when summarizing each window.
            Default is the max() built-in.

    Returns:
        List of summary data points.
    """
    window_size = int(math.ceil(len(data) / points))
    if window_size == 1:
        return data

    summary_points = []
    start = 0
    while start < len(data):
        end = min(start + window_size, len(data))
        summary_points.append(summary_func(data[start:end]))
        start = end
    return summary_points


@contextlib.contextmanager
def ChangeDir(new_cwd):
    former_cwd = os.getcwd()
    os.chdir(new_cwd)
    try:
        yield
    finally:
        os.chdir(former_cwd)


def RemovePycs():
    if sys.platform == "win32":
        for root, dirs, files in os.walk('.'):
            for name in files:
                if name.endswith('.pyc') or name.endswith('.pyo'):
                    os.remove(os.path.join(root, name))
    else:
        subprocess.check_call(["find", ".", "-name", "*.py[co]",
                               "-exec", "rm", "-f", "{}", ";"])


def LogCall(command):
    command = list(map(str, command))
    logging.info("Running `%s`", " ".join(command))
    return command


@contextlib.contextmanager
def TemporaryFilename(prefix):
    fd, name = tempfile.mkstemp(prefix=prefix)
    os.close(fd)
    try:
        yield name
    finally:
        os.remove(name)


def BuildEnv(env=None, inherit_env=[]):
    """Massage an environment variables dict for the host platform.

    Massaging performed (in this order):
    - Add any variables named in inherit_env.
    - Copy PYTHONPATH to JYTHONPATH to support Jython.
    - Copy PYTHONPATH to IRONPYTHONPATH to support IronPython.
    - Win32 requires certain env vars to be set.

    Args:
        env: optional; environment variables dict. If this is omitted, start
            with an empty environment.
        inherit_env: optional; iterable of strings, each the name of an
            environment variable to inherit from os.environ, for any
            interpreter as well as for Jython specifically.

    Returns:
        A copy of `env`, possibly with modifications.
    """
    if env is None:
        env = {}
    fixed_env = env.copy()
    for varname in inherit_env:
        fixed_env[varname] = os.environ[varname]
    if "PYTHONPATH" in fixed_env:
        fixed_env["JYTHONPATH"] = fixed_env["PYTHONPATH"]
        fixed_env["IRONPYTHONPATH"] = fixed_env["PYTHONPATH"]
    if sys.platform == "win32":
        # Win32 requires certain environment variables be present,
        # as does Jython under Windows.
        for k in ("COMSPEC", "SystemRoot", "TEMP", "PATH"):
            if k in os.environ and k not in fixed_env:
                fixed_env[k] = os.environ[k]
    return fixed_env


class RawBenchmarkResult(dict):

    def __init__(self, average, min=None, max=None, std_dev=None):
        self['average'] = average
        if min is not None:
            self['min'] = min
        if max is not None:
            self['max'] = max
        if std_dev is not None:
            self['std_dev'] = std_dev

    def __str__(self):
        return '\n'.join('%s: %s' % i for i in sorted(self.items()))


def FormatRawData(bm_data, options):
    # XXX implement track_memory handling?
    times = sorted(bm_data.runtimes)
    average = statistics.median(times)
    mn = mx = std = None
    if len(times) > 1:
        mn = times[0]
        mx = times[-1]
        std = statistics.stdev(times)
    return RawBenchmarkResult(average, mn, mx, std)


def CallAndCaptureOutput(command, env=None, inherit_env=[], hide_stderr=True):
    """Run the given command, capturing stdout.

    Args:
        command: the command to run as a list, one argument per element.
        env: optional; environment variables to set.
        inherit_env: optional; iterable of strings, each the name of an
            environment variable to inherit from os.environ.

    Returns:
        stdout where stdout is the captured stdout as a string.

    Raises:
        RuntimeError: if the command failed. The value of the exception will
        be the error message from the command.
    """
    if hasattr(subprocess, 'DEVNULL'):
        stderr = subprocess.DEVNULL
    else:
        stderr = subprocess.PIPE
    if hide_stderr:
        kw = {'stderr': subprocess.PIPE}
    else:
        kw = {}
    proc = subprocess.Popen(LogCall(command),
                               stdout=subprocess.PIPE,
                               env=BuildEnv(env, inherit_env),
                               universal_newlines=True,
                               **kw)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        if hide_stderr:
            sys.stderr.flush()
            sys.stderr.write(stderr)
            sys.stderr.flush()
        raise RuntimeError("Benchmark died")
    return stdout


def MeasureGeneric(python, options, bm_path, bm_env=None,
                   extra_args=[]):
    """Abstract measurement function for Unladen's bm_* scripts.

    Based on the values of options.fast/rigorous, will pass -n {5,50,100} to
    the benchmark script. MeasureGeneric takes care of parsing out the running
    times from the memory usage data.

    Args:
        python: start of the argv list for running Python.
        options: optparse.Values instance.
        bm_path: path to the benchmark script.
        bm_env: optional environment dict. If this is unspecified or None,
            use an empty enviroment.
        extra_args: optional list of command line args to be given to the
            benchmark script.

    Returns:
        RawData instance.
    """
    if bm_env is None:
        bm_env = {}

    bench_args = [bm_path, "--stdout"]
    if options.debug_single_sample:
        bench_args.append('--debug-single-sample')
    elif options.rigorous:
        bench_args.append('--rigorous')
    elif options.fast:
        bench_args.append('--fast')

    if options.verbose:
        bench_args.append('--verbose')

    RemovePycs()
    command = python + bench_args + extra_args
    stdout = CallAndCaptureOutput(command, bm_env,
                                  inherit_env=options.inherit_env,
                                  hide_stderr=not options.verbose)

    # FIXME: what about mem_usage? store stderr?
    return perf.Benchmark.loads(stdout)


def ParsePythonArgsOption(python_args_opt):
    """Parses the --args option.

    Args:
        python_args_opt: the string passed to the -a option on the command line.

    Returns:
        A pair of lists: (base_python_args, changed_python_args).
    """
    args_pair = python_args_opt.split(",")
    base_args = args_pair[0].split()  # On whitespace.
    changed_args = base_args
    if len(args_pair) == 2:
        changed_args = args_pair[1].split()
    elif len(args_pair) > 2:
        logging.warning("Didn't expect two or more commas in --args flag: %s",
                        python_args_opt)
    return base_args, changed_args


def ParseOutputStyle(option, opt_str, value, parser):
    if value not in ("normal", "table"):
        parser.error("Invalid output style: %r" % value)
    parser.values.output_style = value


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


def ParseBenchmarksOption(benchmarks_opt, bench_groups, fast=False, raw=False):
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


def FilterBenchmarks(benchmarks, bench_funcs, base_python, changed_python):
    """Filters out benchmarks not supported by both Pythons.

    Args:
        benchmarks: a set() of benchmark names
        bench_funcs: dict mapping benchmark names to functions
        base_python, changed_python: the interpereter commands (as lists)

    Returns:
        The filtered set of benchmark names
    """
    basever = interpreter_version(base_python)
    if changed_python:
        changedver = interpreter_version(changed_python)
    else:
        changedver = None
    for bm in list(benchmarks):
        minver, maxver = getattr(bench_funcs[bm], '_range', ('2.0', '4.0'))
        if not minver <= basever <= maxver:
            benchmarks.discard(bm)
            logging.info("Skipping benchmark %s; not compatible with "
                         "Python %s" % (bm, basever))
            continue
        if changedver is not None and not minver <= changedver <= maxver:
            benchmarks.discard(bm)
            logging.info("Skipping benchmark %s; not compatible with "
                         "Python %s" % (bm, changedver))
    return benchmarks


def display_suite(bench_suite):
    for bench in bench_suite.get_benchmarks():
        print()
        print("### %s ###" % bench.get_name())
        print(bench)


def check_existing(filename):
    if os.path.exists(filename):
        print("ERROR: the output file %s already exists!" % filename)
        sys.exit(1)


def cmd_run(parser, options, bench_funcs, bench_groups):
    action_run = (options.action == 'run')
    run_compare = (not action_run)

    if action_run:
        base = sys.executable
        changed = None
    else:
        # options.action == 'run_compare'
        base = options.baseline_python
        changed = options.changed_python

    # Get the full path since child processes are run in an empty environment
    # without the PATH variable
    base = which(base)
    if run_compare:
        changed = which(changed)

    if action_run:
        if options.output:
            check_existing(options.output)
    else:
        if options.base_output:
            check_existing(options.base_output)
        if options.changed_output:
            check_existing(options.changed_output)

    options.base_binary = base
    if run_compare:
        options.changed_binary = changed

    if not options.control_label:
        options.control_label = options.base_binary
    if run_compare and not options.experiment_label:
        options.experiment_label = options.changed_binary

    base_args, changed_args = ParsePythonArgsOption(options.args)
    if action_run:
        if base_args != changed_args:
            parser.error('provide args for only one interpreter in raw mode')
        if options.track_memory:
            # XXX this might be worth fixing someday?
            parser.error('raw mode is not compatible with memory tracking')
        if options.csv:
            parser.error('raw mode does not support csv output')
    base_cmd_prefix = [base] + base_args
    if run_compare:
        changed_cmd_prefix = [changed] + changed_args
    else:
        changed_cmd_prefix = None

    # FIXME: use --affinity of perf
    # FIXME: need to convert startup tests to the perf module
    if options.affinity:
        err_msg = check_taskset()
        if err_msg:
            print("ERROR: Option --affinity not available. %s" % err_msg,
                  file=sys.stderr)
            sys.exit(1)

        taskset_prefix = ["taskset", "--cpu-list", options.affinity]
        base_cmd_prefix = taskset_prefix + base_cmd_prefix
        if run_compare:
            changed_cmd_prefix = taskset_prefix + changed_cmd_prefix

    logging.basicConfig(level=logging.INFO)

    if options.track_memory:
        print("FIXME: --track_memory option is currently broken")
        sys.exit(1)

    should_run = ParseBenchmarksOption(options.benchmarks, bench_groups,
                                       options.fast or options.debug_single_sample,
                                       action_run)

    should_run = FilterBenchmarks(should_run, bench_funcs,
                                  base_cmd_prefix, changed_cmd_prefix)

    base_suite = perf.BenchmarkSuite()
    if run_compare:
        changed_suite = perf.BenchmarkSuite()
    to_run = list(sorted(should_run))
    run_count = str(len(to_run))
    for index, name in enumerate(to_run):
        func = bench_funcs[name]
        print("[%s/%s] %s..." %
              (str(index+1).rjust(len(run_count)), run_count, name))
        options.benchmark_name = name  # Easier than threading this everywhere.

        def add_bench(dest_suite, bench):
            if isinstance(bench, perf.BenchmarkSuite):
                benchmarks = bench.get_benchmarks()
                for bench in benchmarks:
                    dest_suite.add_benchmark(bench)
            else:
                dest_suite.add_benchmark(bench)

        if run_compare:
            bench = func(changed_cmd_prefix, options)
            add_bench(changed_suite, bench)

        bench = func(base_cmd_prefix, options)
        add_bench(base_suite, bench)

    print()
    print("Report on %s" % " ".join(platform.uname()))
    if multiprocessing:
        print("Total CPU cores:", multiprocessing.cpu_count())

    if action_run:
        if options.output:
            base_suite.dump(options.output)

        if options.append:
            perf.add_runs(options.append, base_suite)

        display_suite(base_suite)
    else:
        if options.base_output:
            base_suite.dump(options.base_output)
        if options.changed_output:
            changed_suite.dump(options.changed_output)

        results = compare_results(base_suite, changed_suite, options)

        if options.csv:
            with open(options.csv, "w") as f:
                writer = csv.writer(f)
                writer.writerow(['Benchmark', 'Base', 'Changed'])
                for name, result in results:
                    writer.writerow([name] + result.as_csv())


def cmd_list(options, bench_funcs, bench_groups):
    funcs = bench_groups['all']
    python = [sys.executable]
    all_funcs = FilterBenchmarks(set(funcs), bench_funcs, python, python)

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


