from __future__ import division, with_statement, print_function, absolute_import

import logging
import subprocess

import perf

import performance
from performance.run import (run_perf_script, copy_perf_options,
                             BenchmarkException, CallAndCaptureOutput,
                             Relative)


# Decorators for giving ranges of supported Python versions.
# Benchmarks without a range applied are assumed to be compatible with all
# (reasonably new) Python versions.

def VersionRange(minver=None, maxver=None):
    def deco(func):
        func._range = minver or '1.0', maxver or '9.9'
        return func
    return deco


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


def BM_2to3(python, options):
    return run_perf_script(python, options, "2to3")


@VersionRange(None, '2.7')
def BM_hg_startup(python, options):
    return run_perf_script(python, options, "hg_startup")


def BM_Chameleon(python, options):
    return run_perf_script(python, options, "chameleon")


def BM_Tornado_Http(python, options):
    return run_perf_script(python, options, "tornado_http")


def BM_Django_Template(python, options):
    return run_perf_script(python, options, "django_template")


def BM_Float(python, options):
    return run_perf_script(python, options, "float")


def BM_mako(python, options):
    return run_perf_script(python, options, "mako")


def BM_pathlib(python, options):
    return run_perf_script(python, options, "pathlib")


def _PickleBenchmark(python, options, *extra_args):
    return run_perf_script(python, options, "pickle",
                           extra_args=list(extra_args))


def BM_FastPickle(python, options):
    return _PickleBenchmark(python, options, "--use_cpickle", "pickle")


def BM_FastUnpickle(python, options):
    return _PickleBenchmark(python, options, "--use_cpickle", "unpickle")


def BM_Pickle_List(python, options):
    return _PickleBenchmark(python, options, "--use_cpickle", "pickle_list")


def BM_Unpickle_List(python, options):
    return _PickleBenchmark(python, options, "--use_cpickle", "unpickle_list")


def BM_Pickle_Dict(python, options):
    return _PickleBenchmark(python, options, "--use_cpickle", "pickle_dict")


@VersionRange(None, '2.7')   # 3.x doesn't have slow pickle
def BM_SlowPickle(python, options):
    return _PickleBenchmark(python, options, "pickle")


@VersionRange(None, '2.7')
def BM_SlowUnpickle(python, options):
    return _PickleBenchmark(python, options, "unpickle")


def MeasureEtree(python, options, arg):
    return run_perf_script(python, options, "elementtree", extra_args=[arg])


def BM_ETree_Parse(python, options):
    return MeasureEtree(python, options, 'parse')


def BM_ETree_IterParse(python, options):
    return MeasureEtree(python, options, 'iterparse')


def BM_ETree_Generate(python, options):
    return MeasureEtree(python, options, 'generate')


def BM_ETree_Process(python, options):
    return MeasureEtree(python, options, 'process')


def _JSONBenchmark(python, options, arg):
    return run_perf_script(python, options, "json", extra_args=[arg])


def BM_JSON_Dump(python, options):
    return _JSONBenchmark(python, options, "json_dump")


def BM_JSON_Load(python, options):
    return _JSONBenchmark(python, options, "json_load")


def BM_JSON_Dump_V2(python, options):
    return run_perf_script(python, options, "json_dump_v2")


def BM_NQueens(python, options):
    return run_perf_script(python, options, "nqueens")


def BM_Chaos(python, options):
    return run_perf_script(python, options, "chaos")


def BM_Fannkuch(python, options):
    return run_perf_script(python, options, "fannkuch")


def BM_Go(python, options):
    return run_perf_script(python, options, "go")


def BM_Meteor_Contest(python, options):
    return run_perf_script(python, options, "meteor_contest")


def BM_Spectral_Norm(python, options):
    return run_perf_script(python, options, "spectral_norm")


def BM_Telco(python, options):
    return run_perf_script(python, options, "telco")


def BM_Hexiom(python, options):
    return run_perf_script(python, options, "hexiom")


def BM_Raytrace(python, options):
    return run_perf_script(python, options, "raytrace")


def _LoggingBenchmark(python, options, arg):
    return run_perf_script(python, options, "logging", extra_args=[arg])


def BM_Silent_Logging(python, options):
    return _LoggingBenchmark(python, options, "no_output")


def BM_Simple_Logging(python, options):
    return _LoggingBenchmark(python, options, "simple_output")


def BM_Formatted_Logging(python, options):
    return _LoggingBenchmark(python, options, "formatted_output")


def BM_normal_startup(python, options):
    return run_perf_script(python, options, "startup")


def BM_startup_nosite(python, options):
    return run_perf_script(python, options, "startup", extra_args=["--no-site"])


def BM_regex_v8(python, options):
    return run_perf_script(python, options, "regex_v8")


def BM_regex_effbot(python, options):
    return run_perf_script(python, options, "regex_effbot")


def BM_regex_compile(python, options):
    return run_perf_script(python, options, "regex_compile")


def ThreadingBenchmark(python, options, bm_name):
    return run_perf_script(python, options, "threading", extra_args=[bm_name])


def BM_threaded_count(python, options):
    return ThreadingBenchmark(python, options, "threaded_count")


def BM_iterative_count(python, options):
    return ThreadingBenchmark(python, options, "iterative_count")


def BM_unpack_sequence(python, options):
    return run_perf_script(python, options, "unpack_sequence")


def BM_call_simple(python, options):
    return run_perf_script(python, options, "call_simple")


def BM_call_method(python, options):
    return run_perf_script(python, options, "call_method")


def BM_call_method_unknown(python, options):
    return run_perf_script(python, options, "call_method_unknown")


def BM_call_method_slots(python, options):
    return run_perf_script(python, options, "call_method_slots")


def BM_nbody(python, options):
    return run_perf_script(python, options, "nbody")


@VersionRange(None, '2.7')
def BM_spambayes(python, options):
    return run_perf_script(python, options, "spambayes")


def BM_html5lib(python, options):
    return run_perf_script(python, options, "html5lib")


def BM_richards(python, options):
    return run_perf_script(python, options, "richards")


def BM_pidigits(python, options):
    return run_perf_script(python, options, "pidigits")


def BM_crypto_pyaes(python, options):
    return run_perf_script(python, options, "crypto_pyaes")


def BM_sympy_expand(python, options):
    return run_perf_script(python, options, "sympy", extra_args=['expand'])


def BM_sympy_integrate(python, options):
    return run_perf_script(python, options, "sympy", extra_args=['integrate'])


def BM_sympy_str(python, options):
    return run_perf_script(python, options, "sympy", extra_args=['str'])


def BM_sympy_sum(python, options):
    return run_perf_script(python, options, "sympy", extra_args=['sum'])


def BM_deltablue(python, options):
    return run_perf_script(python, options, "deltablue")


def BM_scimark_SOR(python, options):
    return run_perf_script(python, options, "scimark", extra_args=['SOR'])


def BM_scimark_SparseMatMult(python, options):
    return run_perf_script(python, options, "scimark", extra_args=['SparseMatMult'])


def BM_scimark_MonteCarlo(python, options):
    return run_perf_script(python, options, "scimark", extra_args=['MonteCarlo'])


def BM_scimark_LU(python, options):
    return run_perf_script(python, options, "scimark", extra_args=['LU'])


def BM_scimark_FFT(python, options):
    return run_perf_script(python, options, "scimark", extra_args=['FFT'])


def BM_dulwich_log(python, options):
    return run_perf_script(python, options, "dulwich_log")


@VersionRange(None, '2.7')
def BM_pyflate(python, options):
    return run_perf_script(python, options, "pyflate")


def BM_sqlite_synth(python, options):
    return run_perf_script(python, options, "sqlite_synth")


def BM_genshi_text(python, options):
    return run_perf_script(python, options, "genshi", extra_args=["text"])


def BM_genshi_xml(python, options):
    return run_perf_script(python, options, "genshi", extra_args=["xml"])


def BM_SQLAlchemy_Declarative(python, options):
    return run_perf_script(python, options, "sqlalchemy_declarative")


# End benchmarks, begin main entry point support.

def _FindAllBenchmarks(namespace):
    return dict((name[3:].lower(), func)
                for name, func in namespace.items()
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
    minver, maxver = getattr(func, '_range', ('1.0', '9.9'))
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


def filter_benchmarks(benchmarks, bench_funcs, base_ver):
    """Filters out benchmarks not supported by both Pythons.

    Args:
        benchmarks: a set() of benchmark names
        bench_funcs: dict mapping benchmark names to functions
        python: the interpereter commands (as lists)

    Returns:
        The filtered set of benchmark names
    """
    for bm in list(benchmarks):
        minver, maxver = getattr(bench_funcs[bm], '_range', ('2.0', '4.0'))
        if not minver <= base_ver <= maxver:
            benchmarks.discard(bm)
            logging.info("Skipping benchmark %s; not compatible with "
                         "Python %s" % (bm, base_ver))
            continue
    return benchmarks
