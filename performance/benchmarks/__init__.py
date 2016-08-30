from __future__ import division, with_statement, print_function, absolute_import

import glob
import logging
import os
import subprocess
import time

import perf


from performance.venv import get_virtualenv, ROOT_DIR
from performance.run import (MeasureGeneric, BuildEnv, SimpleBenchmark,
                            BenchmarkError, RemovePycs, CallAndCaptureOutput,
                            GetChildUserTime)


info = logging.info


def Relative(*path):
    return os.path.join(ROOT_DIR, 'performance', 'benchmarks', *path)


# Decorators for giving ranges of supported Python versions.
# Benchmarks without a range applied are assumed to be compatible with all
# (reasonably new) Python versions.

def VersionRange(minver=None, maxver=None):
    def deco(func):
        func._range = minver or '2.0', maxver or '9.0'
        return func
    return deco


@VersionRange()
def BM_PyBench(python, options):
    if options.track_memory:
        return BenchmarkError("Benchmark does not report memory usage yet")

    PYBENCH_PATH = Relative("pybench", "pybench.py")

    args = [PYBENCH_PATH,
            '--with-gc',
            '--with-syscheck',
            '--stdout']
    if options.debug_single_sample:
        args.append("--debug-single-sample")
    elif options.fast:
        args.append("--fast")
    elif options.rigorous:
        args.append("--rigorous")
    if options.verbose:
        args.append('-v')

    try:
        RemovePycs()
        cmd = python + args
        stdout = CallAndCaptureOutput(cmd, inherit_env=options.inherit_env,
                                      hide_stderr=False)
        return perf.BenchmarkSuite.loads(stdout)
    except subprocess.CalledProcessError as exc:
        return BenchmarkError(exc)


def MeasureCommand(name, command, iterations, env, track_memory):
    """Helper function to run arbitrary commands multiple times.

    Differences from MeasureGeneric():
        - MeasureGeneric() works with the performance/bm_*.py scripts.
        - MeasureCommand() does not echo every command run; it is intended for
          high-volume commands, like startup benchmarks

    Args:
        command: list of strings to be passed to Popen.
        iterations: number of times to run the command.
        env: environment vars dictionary.
        track_memory: bool to indicate whether to track memory usage.

    Returns:
        RawData instance. Note that we take instrumentation data from the final
        run; merging instrumentation data between multiple runs is
        prohibitively difficult at this point.

    Raises:
        RuntimeError: if the command failed.
    """
    # FIXME: collect metadata in worker processes
    bench = perf.Benchmark()
    with open(os.devnull, "wb") as dev_null:
        RemovePycs()

        # Priming run (create pyc files, etc).
        CallAndCaptureOutput(command, env=env)

        an_s = "s"
        if iterations == 1:
            an_s = ""
        info("Running `%s` %d time%s", " ".join(command), iterations, an_s)

        times = []
        for _ in range(iterations):
            # FIXME: use perf.perf_counter()?
            start_time = GetChildUserTime()
            subproc = subprocess.Popen(command,
                                       stdout=dev_null,
                                       stderr=subprocess.PIPE,
                                       env=env)
            _, stderr = subproc.communicate()
            if subproc.returncode != 0:
                raise RuntimeError("Benchmark died: " + stderr)
            end_time = GetChildUserTime()
            elapsed = end_time - start_time
            assert elapsed != 0
            times.append(elapsed)

    # FIXME: track_memory
    # FIXME: use at least 1 warmup
    run = perf.Run(times,
                   metadata={'name': name},
                   # FIXME: collect metadata in the worker
                   collect_metadata=False)
    bench.add_run(run)
    return bench


def Measure2to3(python, options):
    target = Relative('data', '2to3')
    pyfiles = glob.glob(os.path.join(target, '*.py.txt'))
    env = BuildEnv(None, inherit_env=options.inherit_env)

    # This can be compressed, but it's harder to understand.
    if options.debug_single_sample:
        trials = 1
    elif options.fast:
        trials = 5
    elif options.rigorous:
        trials = 25
    else:
        trials = 10

    command = python + ["-m", "lib2to3", "-f", "all"] + pyfiles
    return MeasureCommand("2to3", command, trials, env, options.track_memory)

@VersionRange()
def BM_2to3(*args, **kwargs):
    return SimpleBenchmark(Measure2to3, *args, **kwargs)


def MeasureHgStartup(python, options):
    venv = get_virtualenv()
    if os.name == 'nt':
        hg_bin = os.path.join(venv, 'Scripts', 'hg')
    else:
        hg_bin = os.path.join(venv, 'bin', 'hg')

    if options.debug_single_sample:
        trials = 1
    elif options.rigorous:
        trials = 1000
    elif options.fast:
        trials = 100
    else:
        trials = 500

    command = python + [hg_bin, "help"]
    # FIXME: make env parameter of MeasureCommand optional
    env = None
    # FIXME: add mercurial version to metadata
    return MeasureCommand("hg_startup", command, trials, env, options.track_memory)

@VersionRange(None, '2.7')
def BM_hg_startup(*args, **kwargs):
    return SimpleBenchmark(MeasureHgStartup, *args, **kwargs)


def MeasureChameleon(python, options):
    bm_path = Relative("bm_chameleon.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange('2.7', None)
def BM_Chameleon(*args, **kwargs):
    return SimpleBenchmark(MeasureChameleon, *args, **kwargs)


def MeasureTornadoHttp(python, options):
    bm_path = Relative("bm_tornado_http.py")
    return MeasureGeneric(python, options, bm_path)


@VersionRange()
def BM_Tornado_Http(*args, **kwargs):
    return SimpleBenchmark(MeasureTornadoHttp, *args, **kwargs)


def MeasureDjangoTemplate(python, options):
    bm_path = Relative("bm_django_template.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange('2.7', None)
def BM_Django_Template(*args, **kwargs):
    return SimpleBenchmark(MeasureDjangoTemplate, *args, **kwargs)


def MeasureFloat(python, options):
    bm_path = Relative("bm_float.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_Float(*args, **kwargs):
    return SimpleBenchmark(MeasureFloat, *args, **kwargs)


def MeasureMako(python, options):
    bm_path = Relative("bm_mako.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_mako(*args, **kwargs):
    return SimpleBenchmark(MeasureMako, *args, **kwargs)


def MeasurePathlib(python, options):
    bm_path = Relative("bm_pathlib.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_pathlib(*args, **kwargs):
    return SimpleBenchmark(MeasurePathlib, *args, **kwargs)


def MeasurePickle(python, options, extra_args):
    """Test the performance of Python's pickle implementations.

    Args:
        python: prefix of a command line for the Python binary.
        options: optparse.Values instance.
        extra_args: list of arguments to append to the command line.

    Returns:
        RawData instance.
    """
    bm_path = Relative("bm_pickle.py")
    return MeasureGeneric(python, options, bm_path, extra_args=extra_args)


def _PickleBenchmark(python, options, extra_args):
    """Test the performance of Python's pickle implementations.

    Args:
        python: prefix of a command line for the Python binary.
        options: optparse.Values instance.
        extra_args: list of arguments to append to the command line.

    Returns:
        Summary of whether the experiemental Python is better/worse than the
        baseline.
    """
    return SimpleBenchmark(MeasurePickle, python, options, extra_args)

@VersionRange()
def BM_FastPickle(python, options):
    args = ["--use_cpickle", "pickle"]
    return _PickleBenchmark(python, options, args)

@VersionRange()
def BM_FastUnpickle(python, options):
    args = ["--use_cpickle", "unpickle"]
    return _PickleBenchmark(python, options, args)

@VersionRange()
def BM_Pickle_List(python, options):
    args = ["--use_cpickle", "pickle_list"]
    return _PickleBenchmark(python, options, args)

@VersionRange()
def BM_Unpickle_List(python, options):
    args = ["--use_cpickle", "unpickle_list"]
    return _PickleBenchmark(python, options, args)

@VersionRange()
def BM_Pickle_Dict(python, options):
    args = ["--use_cpickle", "pickle_dict"]
    return _PickleBenchmark(python, options, args)

@VersionRange(None, '2.7')   # 3.x doesn't have slow pickle
def BM_SlowPickle(python, options):
    return _PickleBenchmark(python, options, ["pickle"])

@VersionRange(None, '2.7')
def BM_SlowUnpickle(python, options):
    return _PickleBenchmark(python, options, ["unpickle"])


def MeasureEtree(python, options, extra_args):
    """Test the performance of Python's (c)ElementTree implementations.

    Args:
        python: prefix of a command line for the Python binary.
        options: optparse.Values instance.
        extra_args: list of arguments to append to the command line.

    Returns:
        RawData instance.
    """
    bm_path = Relative("bm_elementtree.py")
    return MeasureGeneric(python, options, bm_path, extra_args=extra_args)

@VersionRange()
def BM_ETree_Parse(python, options):
    extra_args = ['parse']
    return SimpleBenchmark(MeasureEtree, python, options, extra_args)

@VersionRange()
def BM_ETree_IterParse(python, options):
    extra_args = ['iterparse']
    return SimpleBenchmark(MeasureEtree, python, options, extra_args)

@VersionRange()
def BM_ETree_Generate(python, options):
    extra_args = ['generate']
    return SimpleBenchmark(MeasureEtree, python, options, extra_args)

@VersionRange()
def BM_ETree_Process(python, options):
    extra_args = ['process']
    return SimpleBenchmark(MeasureEtree, python, options, extra_args)


def MeasureJSON(python, options, extra_args):
    """Test the performance of Python's json implementation.

    Args:
        python: prefix of a command line for the Python binary.
        options: optparse.Values instance.
        extra_args: list of arguments to append to the command line.

    Returns:
        RawData instance.
    """
    bm_path = Relative("bm_json.py")
    return MeasureGeneric(python, options, bm_path, extra_args=extra_args)


def _JSONBenchmark(python, options, extra_args):
    """Test the performance of Python's json implementation.

    Args:
        base_python: prefix of a command line for the reference
                Python binary.
        changed_python: prefix of a command line for the
                experimental Python binary.
        options: optparse.Values instance.
        extra_args: list of arguments to append to the command line.

    Returns:
        Summary of whether the experiemental Python is better/worse than the
        baseline.
    """
    return SimpleBenchmark(MeasureJSON, python, options, extra_args)

@VersionRange()
def BM_JSON_Dump(python, options):
    args = ["json_dump"]
    return _JSONBenchmark(python, options, args)

@VersionRange()
def BM_JSON_Load(python, options):
    args = ["json_load"]
    return _JSONBenchmark(python, options, args)


def MeasureJSONDumpV2(python, options):
    bm_path = Relative("bm_json_v2.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_JSON_Dump_V2(*args, **kwargs):
    return SimpleBenchmark(MeasureJSONDumpV2, *args, **kwargs)


def MeasureNQueens(python, options):
    """Test the performance of an N-Queens solver.

    Args:
        python: prefix of a command line for the Python binary.
        options: optparse.Values instance.

    Returns:
        RawData instance.
    """
    bm_path = Relative("bm_nqueens.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_NQueens(*args, **kwargs):
    return SimpleBenchmark(MeasureNQueens, *args, **kwargs)


def MeasureChaos(python, options):
    bm_path = Relative("bm_chaos.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_Chaos(*args, **kwargs):
    return SimpleBenchmark(MeasureChaos, *args, **kwargs)


def MeasureFannkuch(python, options):
    bm_path = Relative("bm_fannkuch.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_Fannkuch(*args, **kwargs):
    return SimpleBenchmark(MeasureFannkuch, *args, **kwargs)


def MeasureGo(python, options):
    bm_path = Relative("bm_go.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_Go(*args, **kwargs):
    return SimpleBenchmark(MeasureGo, *args, **kwargs)


def MeasureMeteorContest(python, options):
    bm_path = Relative("bm_meteor_contest.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_Meteor_Contest(*args, **kwargs):
    return SimpleBenchmark(MeasureMeteorContest, *args, **kwargs)


def MeasureSpectralNorm(python, options):
    bm_path = Relative("bm_spectral_norm.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_Spectral_Norm(*args, **kwargs):
    return SimpleBenchmark(MeasureSpectralNorm, *args, **kwargs)


def MeasureTelco(python, options):
    bm_path = Relative("bm_telco.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_Telco(*args, **kwargs):
    return SimpleBenchmark(MeasureTelco, *args, **kwargs)


def MeasureHexiom2(python, options):
    bm_path = Relative("bm_hexiom2.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_Hexiom2(*args, **kwargs):
    return SimpleBenchmark(MeasureHexiom2, *args, **kwargs)


def MeasureRaytrace(python, options):
    bm_path = Relative("bm_raytrace.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_Raytrace(*args, **kwargs):
    return SimpleBenchmark(MeasureRaytrace, *args, **kwargs)


def MeasureLogging(python, options, extra_args):
    """Test the performance of Python's logging module.

    Args:
        python: prefix of a command line for the Python binary.
        options: optparse.Values instance.
        extra_args: list of arguments to append to the command line.

    Returns:
        RawData instance.
    """
    bm_path = Relative("bm_logging.py")
    return MeasureGeneric(python, options, bm_path, extra_args=extra_args)


def _LoggingBenchmark(python, options, extra_args):
    """Test the performance of Python's logging module.

    Args:
        base_python: prefix of a command line for the reference
                Python binary.
        changed_python: prefix of a command line for the
                experimental Python binary.
        options: optparse.Values instance.
        extra_args: list of arguments to append to the command line.

    Returns:
        Summary of whether the experiemental Python is better/worse than the
        baseline.
    """
    return SimpleBenchmark(MeasureLogging, python, options, extra_args)

@VersionRange()
def BM_Silent_Logging(python, options):
    args = ["no_output"]
    return _LoggingBenchmark(python, options, args)

@VersionRange()
def BM_Simple_Logging(python, options):
    args = ["simple_output"]
    return _LoggingBenchmark(python, options, args)

@VersionRange()
def BM_Formatted_Logging(python, options):
    args = ["formatted_output"]
    return _LoggingBenchmark(python, options, args)


@VersionRange()
def BM_normal_startup(python, options):
    bm_path = Relative("bm_startup.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_startup_nosite(python, options):
    bm_path = Relative("bm_startup.py")
    return MeasureGeneric(python, options, bm_path, extra_args=["--no-site"])


def MeasureRegexPerformance(python, options, bm_path):
    """Test the performance of Python's regex engine.

    Args:
        python: prefix of a command line for the Python binary.
        options: optparse.Values instance.
        bm_path: relative path; which benchmark script to run.

    Returns:
        RawData instance.
    """
    return MeasureGeneric(python, options, Relative(bm_path))


def RegexBenchmark(python, options, bm_path):
    return SimpleBenchmark(MeasureRegexPerformance,
                           python, options, bm_path)

@VersionRange()
def BM_regex_v8(python, options):
    bm_path = "bm_regex_v8.py"
    return RegexBenchmark(python, options, bm_path)

@VersionRange()
def BM_regex_effbot(python, options):
    bm_path = "bm_regex_effbot.py"
    return RegexBenchmark(python, options, bm_path)

@VersionRange()
def BM_regex_compile(python, options):
    bm_path = "bm_regex_compile.py"
    return RegexBenchmark(python, options, bm_path)


def MeasureThreading(python, options, bm_name):
    """Test the performance of Python's threading support.

    Args:
        python: prefix of a command line for the Python binary.
        options: optparse.Values instance.
        bm_name: name of the threading benchmark to run.

    Returns:
        RawData instance.
    """
    bm_path = Relative("bm_threading.py")
    return MeasureGeneric(python, options, bm_path, extra_args=[bm_name])


def ThreadingBenchmark(python, options, bm_name):
    return SimpleBenchmark(MeasureThreading,
                           python, options, bm_name)

@VersionRange()
def BM_threaded_count(python, options):
    bm_name = "threaded_count"
    return ThreadingBenchmark(python, options, bm_name)

@VersionRange()
def BM_iterative_count(python, options):
    bm_name = "iterative_count"
    return ThreadingBenchmark(python, options, bm_name)


def MeasureUnpackSequence(python, options):
    """Test the performance of sequence unpacking.

    Args:
        python: prefix of a command line for the Python binary.
        options: optparse.Values instance.

    Returns:
        RawData instance.
    """
    bm_path = Relative("bm_unpack_sequence.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_unpack_sequence(*args, **kwargs):
    return SimpleBenchmark(MeasureUnpackSequence, *args, **kwargs)


def MeasureCallSimple(python, options):
    bm_path = Relative("bm_call_simple.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_call_simple(*args, **kwargs):
    return SimpleBenchmark(MeasureCallSimple, *args, **kwargs)


def MeasureCallMethod(python, options):
    bm_path = Relative("bm_call_method.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_call_method(*args, **kwargs):
    return SimpleBenchmark(MeasureCallMethod, *args, **kwargs)


def MeasureCallMethodUnknown(python, options):
    bm_path = Relative("bm_call_method_unknown.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_call_method_unknown(*args, **kwargs):
    return SimpleBenchmark(MeasureCallMethodUnknown, *args, **kwargs)


def MeasureCallMethodSlots(python, options):
    bm_path = Relative("bm_call_method_slots.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_call_method_slots(*args, **kwargs):
    return SimpleBenchmark(MeasureCallMethodSlots, *args, **kwargs)


def MeasureNbody(python, options):
    """Test the performance of math operations using an n-body benchmark.

    Args:
        python: prefix of a command line for the Python binary.
        options: optparse.Values instance.

    Returns:
        RawData instance.
    """
    bm_path = Relative("bm_nbody.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_nbody(*args, **kwargs):
    return SimpleBenchmark(MeasureNbody, *args, **kwargs)


def MeasureSpamBayes(python, options):
    """Test the performance of the SpamBayes spam filter and its tokenizer.

    Args:
        python: prefix of a command line for the Python binary.
        options: optparse.Values instance.

    Returns:
        RawData instance.
    """
    bm_path = Relative("bm_spambayes.py")
    bm_env = BuildEnv(None, options.inherit_env)
    return MeasureGeneric(python, options, bm_path, bm_env)

@VersionRange(None, '2.7')
def BM_spambayes(*args, **kwargs):
    return SimpleBenchmark(MeasureSpamBayes, *args, **kwargs)


def MeasureHtml5lib(python, options):
    bm_path = Relative("bm_html5lib.py")
    bm_env = BuildEnv(None, options.inherit_env)
    return MeasureGeneric(python, options, bm_path, bm_env)

@VersionRange(None, '2.7')
def BM_html5lib(*args, **kwargs):
    return SimpleBenchmark(MeasureHtml5lib, *args, **kwargs)


def MeasureRichards(python, options):
    bm_path = Relative("bm_richards.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_richards(*args, **kwargs):
    return SimpleBenchmark(MeasureRichards, *args, **kwargs)


def MeasurePiDigits(python, options):
    """Test the performance of big integer arithmetic by calculating the
    first digits of PI.

    Args:
        python: prefix of a command line for the Python binary.
        options: optparse.Values instance.

    Returns:
        RawData instance.
    """
    bm_path = Relative("bm_pidigits.py")
    return MeasureGeneric(python, options, bm_path)

@VersionRange()
def BM_pidigits(*args, **kwargs):
    return SimpleBenchmark(MeasurePiDigits, *args, **kwargs)


### End benchmarks, begin main entry point support.

def _FindAllBenchmarks(namespace):
    return dict((name[3:].lower(), func)
                for (name, func) in sorted(namespace.items())
                if name.startswith("BM_"))

BENCH_FUNCS = _FindAllBenchmarks(globals())

# Benchmark groups. The "default" group is what's run if no -b option is
# specified.
# If you update the default group, be sure to update the module docstring, too.
# An "all" group which includes every benchmark perf.py knows about is generated
# automatically.
BENCH_GROUPS = {"default": ["2to3", "chameleon", "django_template", "nbody",
                            "tornado_http", "fastpickle", "fastunpickle",
                            "regex_v8", "json_dump_v2", "json_load"],
                "startup": ["normal_startup", "startup_nosite",
                            "hg_startup"],
                "regex": ["regex_v8", "regex_effbot", "regex_compile"],
                "threading": ["threaded_count", "iterative_count"],
                "serialize": ["slowpickle", "slowunpickle",  # Not for Python 3
                              "fastpickle", "fastunpickle",
                              "etree",
                              "json_dump_v2", "json_load"],
                "etree": ["etree_generate", "etree_parse",
                          "etree_iterparse", "etree_process"],
                "apps": ["2to3", "chameleon", "html5lib",
                         "spambayes", "tornado_http"],
                "calls": ["call_simple", "call_method", "call_method_slots",
                          "call_method_unknown"],
                "math": ["float", "nbody", "pidigits"],
                "template" : ["django_template", "mako"],
                "logging": ["silent_logging", "simple_logging",
                            "formatted_logging"],
                # These are removed from the "all" group
                "deprecated": ["iterative_count", "json_dump",
                               "threaded_count"],
                }

# Calculate set of 2-and-3 compatible benchmarks.
group2n3 = BENCH_GROUPS["2n3"] = []
group_deprecated = set(BENCH_GROUPS["deprecated"])
for bm, func in BENCH_FUNCS.items():
    if bm in group_deprecated:
        continue
    minver, maxver = getattr(func, '_range', ('2.0', '4.0'))
    if minver <= '2.7' and '3.2' <= maxver:
        group2n3.append(bm)


def CreateBenchGroups(bench_funcs=BENCH_FUNCS, bench_groups=BENCH_GROUPS):
    bench_groups = bench_groups.copy()
    deprecated = bench_groups['deprecated']
    bench_groups["all"] = sorted(b for b in bench_funcs if b not in deprecated)
    return bench_groups


def get_benchmark_groups():
    bench_funcs = BENCH_FUNCS
    # create the 'all' group
    bench_groups = CreateBenchGroups(bench_funcs, BENCH_GROUPS)
    return (bench_funcs, bench_groups)
