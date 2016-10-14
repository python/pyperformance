from __future__ import division, with_statement, print_function, absolute_import

import logging
import subprocess

from perf._bench import _load_suite_from_stdout

from performance.run import (run_perf_script, copy_perf_options,
                             BenchmarkException, run_command,
                             Relative)


# Benchmark groups. The "default" group is what's run if no -b option is
# specified.
# If you update the default group, be sure to update the module docstring, too.
# An "all" group which includes every benchmark perf.py knows about is generated
# automatically.
BENCH_GROUPS = {"default": ["2to3", "chameleon", "django_template", "nbody",
                            "tornado_http", "pickle", "unpickle",
                            "regex_v8", "json_dumps", "json_loads"],
                "startup": ["normal_startup", "startup_nosite",
                            "hg_startup"],
                "regex": ["regex_v8", "regex_effbot", "regex_compile"],
                "threading": ["threading_threaded_count",
                              "threading_iterative_count"],
                "serialize": ["pickle_pure_python", "unpickle_pure_python",  # Not for Python 3
                              "pickle", "unpickle",
                              "etree",
                              "json_dumps", "json_loads"],
                "etree": ["etree_generate", "etree_parse",
                          "etree_iterparse", "etree_process"],
                "apps": ["2to3", "chameleon", "html5lib",
                         "spambayes", "tornado_http"],
                "calls": ["call_simple", "call_method", "call_method_slots",
                          "call_method_unknown"],
                "math": ["float", "nbody", "pidigits"],
                "template": ["django_template", "mako"],
                "logging": ["logging_silent", "logging_simple",
                            "logging_format"],
                # These are removed from the "all" group
                "deprecated": ["threading_iterative_count",
                               "threading_threaded_count"],
                }


def python2_only(func):
    func._python2_only = True
    return func


def BM_PyBench(python, options):
    if options.track_memory:
        raise BenchmarkException("pybench does not report memory usage")

    PYBENCH_PATH = Relative("pybench", "pybench.py")

    args = [PYBENCH_PATH,
            '--with-gc',
            '--with-syscheck']
    copy_perf_options(args, options)
    args.append('--stdout')

    try:
        cmd = python + args
        stdout = run_command(cmd, hide_stderr=False)

        return _load_suite_from_stdout(stdout)
    except subprocess.CalledProcessError as exc:
        return BenchmarkException(exc)


def BM_2to3(python, options):
    return run_perf_script(python, options, "2to3")


@python2_only
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


def pickle_benchmark(python, options, *extra_args):
    return run_perf_script(python, options, "pickle",
                           extra_args=list(extra_args))


def BM_pickle(python, options):
    return pickle_benchmark(python, options, "pickle")


def BM_unpickle(python, options):
    return pickle_benchmark(python, options, "unpickle")


def BM_pickle_list(python, options):
    return pickle_benchmark(python, options, "pickle_list")


def BM_pickle_dict(python, options):
    return pickle_benchmark(python, options, "pickle_dict")


def BM_unpickle_list(python, options):
    return pickle_benchmark(python, options, "unpickle_list")


def BM_pickle_pure_python(python, options):
    return pickle_benchmark(python, options, "--pure-python", "pickle")


def BM_unpickle_pure_python(python, options):
    return pickle_benchmark(python, options, "--pure-python", "unpickle")


def bench_xml_etree(python, options, arg):
    return run_perf_script(python, options, "xml_etree", extra_args=[arg])


def BM_xml_etree_parse(python, options):
    return bench_xml_etree(python, options, 'parse')


def BM_xml_etree_iterparse(python, options):
    return bench_xml_etree(python, options, 'iterparse')


def BM_xml_etree_generate(python, options):
    return bench_xml_etree(python, options, 'generate')


def BM_xml_etree_process(python, options):
    return bench_xml_etree(python, options, 'process')


def BM_json_loads(python, options):
    return run_perf_script(python, options, "json_loads")


def BM_json_dumps(python, options):
    return run_perf_script(python, options, "json_dumps")


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


def BM_hexiom(python, options):
    return run_perf_script(python, options, "hexiom")


def BM_Raytrace(python, options):
    return run_perf_script(python, options, "raytrace")


def bench_logging(python, options, arg):
    return run_perf_script(python, options, "logging", extra_args=[arg])


def BM_logging_silent(python, options):
    return bench_logging(python, options, "silent")


def BM_logging_simple(python, options):
    return bench_logging(python, options, "simple")


def BM_logging_format(python, options):
    return bench_logging(python, options, "format")


def BM_python_startup(python, options):
    return run_perf_script(python, options, "python_startup")


def BM_python_startup_no_site(python, options):
    return run_perf_script(python, options, "python_startup",
                           extra_args=["--no-site"])


def BM_regex_v8(python, options):
    return run_perf_script(python, options, "regex_v8")


def BM_regex_effbot(python, options):
    return run_perf_script(python, options, "regex_effbot")


def BM_regex_compile(python, options):
    return run_perf_script(python, options, "regex_compile")


def bench_threading(python, options, bm_name):
    return run_perf_script(python, options, "threading", extra_args=[bm_name])


def BM_threading_threaded_count(python, options):
    return bench_threading(python, options, "threaded_count")


def BM_threading_iterative_count(python, options):
    return bench_threading(python, options, "iterative_count")


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


@python2_only
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


def BM_sympy(python, options):
    return run_perf_script(python, options, "sympy")


def BM_deltablue(python, options):
    return run_perf_script(python, options, "deltablue")


def BM_scimark(python, options):
    return run_perf_script(python, options, "scimark")


def BM_dulwich_log(python, options):
    return run_perf_script(python, options, "dulwich_log")


@python2_only
def BM_pyflate(python, options):
    return run_perf_script(python, options, "pyflate")


def BM_sqlite_synth(python, options):
    return run_perf_script(python, options, "sqlite_synth")


def BM_genshi(python, options):
    return run_perf_script(python, options, "genshi")


def BM_SQLAlchemy_Declarative(python, options):
    return run_perf_script(python, options, "sqlalchemy_declarative")


# End benchmarks, begin main entry point support.

def get_benchmark_groups():
    bench_funcs = dict((name[3:].lower(), func)
                       for name, func in globals().items()
                       if name.startswith("BM_"))

    bench_groups = BENCH_GROUPS.copy()
    deprecated = set(bench_groups["deprecated"])

    # Calculate set of 2-and-3 compatible benchmarks.
    group2n3 = bench_groups["2n3"] = []
    for bm, func in bench_funcs.items():
        if bm in deprecated:
            continue

        if not getattr(func, '_python2_only', False):
            group2n3.append(bm)

    # create the 'all' group
    bench_groups["all"] = sorted(b for b in bench_funcs if b not in deprecated)

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
        func = bench_funcs[bm]
        if getattr(func, '_python2_only', False):
            if (3, 0) <= base_ver:
                benchmarks.discard(bm)
                logging.info("Skipping Python2-only benchmark %s; "
                             "not compatible with Python %s" % (bm, base_ver))
                continue
    return benchmarks
