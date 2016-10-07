from __future__ import division, with_statement, print_function, absolute_import

import os
import subprocess

import perf

import performance
from performance.venv import PERFORMANCE_ROOT
from performance.run import (run_perf_script, copy_perf_options,
                             BenchmarkException, CallAndCaptureOutput)


def Relative(*path):
    return os.path.join(PERFORMANCE_ROOT, 'benchmarks', *path)


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
        raise BenchmarkException("pybench does not report memory usage")

    version = performance.__version__
    PYBENCH_PATH = Relative("pybench", "pybench.py")

    args = [PYBENCH_PATH,
            '--with-gc',
            '--with-syscheck']
    copy_perf_options(args, options)
    args.append('--stdout')

    try:
        cmd = python + args
        stdout = CallAndCaptureOutput(cmd, hide_stderr=False)

        suite = perf.BenchmarkSuite.loads(stdout)
        for benchmark in suite:
            benchmark.update_metadata({'performance_version': version})
        return suite
    except subprocess.CalledProcessError as exc:
        return BenchmarkException(exc)


@VersionRange()
def BM_2to3(python, options):
    bm_path = Relative("bm_2to3.py")
    return run_perf_script(python, options, bm_path)


@VersionRange(None, '2.7')
def BM_hg_startup(python, options):
    bm_path = Relative("bm_hg_startup.py")
    return run_perf_script(python, options, bm_path)


@VersionRange('2.7', None)
def BM_Chameleon(python, options):
    bm_path = Relative("bm_chameleon.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_Tornado_Http(python, options):
    bm_path = Relative("bm_tornado_http.py")
    return run_perf_script(python, options, bm_path)


@VersionRange('2.7', None)
def BM_Django_Template(python, options):
    bm_path = Relative("bm_django_template.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_Float(python, options):
    bm_path = Relative("bm_float.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_mako(python, options):
    bm_path = Relative("bm_mako.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_pathlib(python, options):
    bm_path = Relative("bm_pathlib.py")
    return run_perf_script(python, options, bm_path)


def _PickleBenchmark(python, options, *extra_args):
    bm_path = Relative("bm_pickle.py")
    return run_perf_script(python, options, bm_path,
                           extra_args=list(extra_args))


@VersionRange()
def BM_FastPickle(python, options):
    return _PickleBenchmark(python, options, "--use_cpickle", "pickle")


@VersionRange()
def BM_FastUnpickle(python, options):
    return _PickleBenchmark(python, options, "--use_cpickle", "unpickle")


@VersionRange()
def BM_Pickle_List(python, options):
    return _PickleBenchmark(python, options, "--use_cpickle", "pickle_list")


@VersionRange()
def BM_Unpickle_List(python, options):
    return _PickleBenchmark(python, options, "--use_cpickle", "unpickle_list")


@VersionRange()
def BM_Pickle_Dict(python, options):
    return _PickleBenchmark(python, options, "--use_cpickle", "pickle_dict")


@VersionRange(None, '2.7')   # 3.x doesn't have slow pickle
def BM_SlowPickle(python, options):
    return _PickleBenchmark(python, options, "pickle")


@VersionRange(None, '2.7')
def BM_SlowUnpickle(python, options):
    return _PickleBenchmark(python, options, "unpickle")


def MeasureEtree(python, options, arg):
    bm_path = Relative("bm_elementtree.py")
    return run_perf_script(python, options, bm_path, extra_args=[arg])


@VersionRange()
def BM_ETree_Parse(python, options):
    return MeasureEtree(python, options, 'parse')


@VersionRange()
def BM_ETree_IterParse(python, options):
    return MeasureEtree(python, options, 'iterparse')


@VersionRange()
def BM_ETree_Generate(python, options):
    return MeasureEtree(python, options, 'generate')


@VersionRange()
def BM_ETree_Process(python, options):
    return MeasureEtree(python, options, 'process')


def _JSONBenchmark(python, options, arg):
    bm_path = Relative("bm_json.py")
    return run_perf_script(python, options, bm_path, extra_args=[arg])


@VersionRange()
def BM_JSON_Dump(python, options):
    return _JSONBenchmark(python, options, "json_dump")


@VersionRange()
def BM_JSON_Load(python, options):
    return _JSONBenchmark(python, options, "json_load")


@VersionRange()
def BM_JSON_Dump_V2(python, options):
    bm_path = Relative("bm_json_dump_v2.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_NQueens(python, options):
    bm_path = Relative("bm_nqueens.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_Chaos(python, options):
    bm_path = Relative("bm_chaos.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_Fannkuch(python, options):
    bm_path = Relative("bm_fannkuch.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_Go(python, options):
    bm_path = Relative("bm_go.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_Meteor_Contest(python, options):
    bm_path = Relative("bm_meteor_contest.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_Spectral_Norm(python, options):
    bm_path = Relative("bm_spectral_norm.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_Telco(python, options):
    bm_path = Relative("bm_telco.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_Hexiom(python, options):
    bm_path = Relative("bm_hexiom.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_Raytrace(python, options):
    bm_path = Relative("bm_raytrace.py")
    return run_perf_script(python, options, bm_path)


def _LoggingBenchmark(python, options, arg):
    bm_path = Relative("bm_logging.py")
    return run_perf_script(python, options, bm_path, extra_args=[arg])


@VersionRange()
def BM_Silent_Logging(python, options):
    return _LoggingBenchmark(python, options, "no_output")


@VersionRange()
def BM_Simple_Logging(python, options):
    return _LoggingBenchmark(python, options, "simple_output")


@VersionRange()
def BM_Formatted_Logging(python, options):
    return _LoggingBenchmark(python, options, "formatted_output")


@VersionRange()
def BM_normal_startup(python, options):
    bm_path = Relative("bm_startup.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_startup_nosite(python, options):
    bm_path = Relative("bm_startup.py")
    return run_perf_script(python, options, bm_path, extra_args=["--no-site"])


@VersionRange()
def BM_regex_v8(python, options):
    return run_perf_script(python, options, Relative("bm_regex_v8.py"))


@VersionRange()
def BM_regex_effbot(python, options):
    return run_perf_script(python, options, Relative("bm_regex_effbot.py"))


@VersionRange()
def BM_regex_compile(python, options):
    return run_perf_script(python, options, Relative("bm_regex_compile.py"))


def ThreadingBenchmark(python, options, bm_name):
    bm_path = Relative("bm_threading.py")
    return run_perf_script(python, options, bm_path, extra_args=[bm_name])


@VersionRange()
def BM_threaded_count(python, options):
    return ThreadingBenchmark(python, options, "threaded_count")


@VersionRange()
def BM_iterative_count(python, options):
    return ThreadingBenchmark(python, options, "iterative_count")


@VersionRange()
def BM_unpack_sequence(python, options):
    bm_path = Relative("bm_unpack_sequence.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_call_simple(python, options):
    bm_path = Relative("bm_call_simple.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_call_method(python, options):
    bm_path = Relative("bm_call_method.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_call_method_unknown(python, options):
    bm_path = Relative("bm_call_method_unknown.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_call_method_slots(python, options):
    bm_path = Relative("bm_call_method_slots.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_nbody(python, options):
    bm_path = Relative("bm_nbody.py")
    return run_perf_script(python, options, bm_path)


@VersionRange(None, '2.7')
def BM_spambayes(python, options):
    bm_path = Relative("bm_spambayes.py")
    return run_perf_script(python, options, bm_path)


@VersionRange(None, '2.7')
def BM_html5lib(python, options):
    bm_path = Relative("bm_html5lib.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_richards(python, options):
    bm_path = Relative("bm_richards.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_pidigits(python, options):
    bm_path = Relative("bm_pidigits.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_crypto_pyaes(python, options):
    bm_path = Relative("bm_crypto_pyaes.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_sympy_expand(python, options):
    bm_path = Relative("bm_sympy.py")
    return run_perf_script(python, options, bm_path, extra_args=['expand'])


@VersionRange()
def BM_sympy_integrate(python, options):
    bm_path = Relative("bm_sympy.py")
    return run_perf_script(python, options, bm_path, extra_args=['integrate'])


@VersionRange()
def BM_sympy_str(python, options):
    bm_path = Relative("bm_sympy.py")
    return run_perf_script(python, options, bm_path, extra_args=['str'])


@VersionRange()
def BM_sympy_sum(python, options):
    bm_path = Relative("bm_sympy.py")
    return run_perf_script(python, options, bm_path, extra_args=['sum'])


@VersionRange()
def BM_deltablue(python, options):
    bm_path = Relative("bm_deltablue.py")
    return run_perf_script(python, options, bm_path)


@VersionRange()
def BM_scimark_SOR(python, options):
    bm_path = Relative("bm_scimark.py")
    return run_perf_script(python, options, bm_path, extra_args=['SOR'])


@VersionRange()
def BM_scimark_SparseMatMult(python, options):
    bm_path = Relative("bm_scimark.py")
    return run_perf_script(python, options, bm_path, extra_args=['SparseMatMult'])


@VersionRange()
def BM_scimark_MonteCarlo(python, options):
    bm_path = Relative("bm_scimark.py")
    return run_perf_script(python, options, bm_path, extra_args=['MonteCarlo'])


@VersionRange()
def BM_scimark_LU(python, options):
    bm_path = Relative("bm_scimark.py")
    return run_perf_script(python, options, bm_path, extra_args=['LU'])


@VersionRange()
def BM_scimark_FFT(python, options):
    bm_path = Relative("bm_scimark.py")
    return run_perf_script(python, options, bm_path, extra_args=['FFT'])


@VersionRange(None, '2.7')
def BM_dulwich_log(python, options):
    bm_path = Relative("bm_dulwich_log.py")
    return run_perf_script(python, options, bm_path)


@VersionRange(None, '2.7')
def BM_pyflate(python, options):
    bm_path = Relative("bm_pyflate.py")
    return run_perf_script(python, options, bm_path)


# End benchmarks, begin main entry point support.

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
                "template": ["django_template", "mako"],
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
