import logging

from pyperformance.run import run_perf_script


# Benchmark groups. The "default" group is what's run if no -b option is
# specified.
DEFAULT_GROUP = [
    '2to3',
    'chameleon',
    'chaos',
    'crypto_pyaes',
    'deltablue',
    'django_template',
    'dulwich_log',
    'fannkuch',
    'float',
    'genshi',
    'go',
    'hexiom',

    # FIXME: this benchmark fails with:
    # Unable to get the program 'hg' from the virtual environment
    # 'hg_startup',

    'html5lib',
    'json_dumps',
    'json_loads',
    'logging',
    'mako',
    'meteor_contest',
    'nbody',
    'nqueens',
    'pathlib',
    'pickle',
    'pickle_dict',
    'pickle_list',
    'pickle_pure_python',
    'pidigits',
    'pyflate',
    'python_startup',
    'python_startup_no_site',
    'raytrace',
    'regex_compile',
    'regex_dna',
    'regex_effbot',
    'regex_v8',
    'richards',
    'scimark',
    'spectral_norm',
    'sqlalchemy_declarative',
    'sqlalchemy_imperative',
    'sqlite_synth',
    'sympy',
    'telco',
    'tornado_http',
    'unpack_sequence',
    'unpickle',
    'unpickle_list',
    'unpickle_pure_python',
    'xml_etree',
]

BENCH_GROUPS = {
    # get_benchmarks() creates an "all" group which includes every benchmark
    # pyperformance knows about.
    "default": DEFAULT_GROUP,
    "startup": ["normal_startup", "startup_nosite",
                "hg_startup"],
    "regex": ["regex_v8", "regex_effbot", "regex_compile",
              "regex_dna"],
    "serialize": ["pickle_pure_python", "unpickle_pure_python",  # Not for Python 3
                  "pickle", "unpickle",
                  "xml_etree",
                  "json_dumps", "json_loads"],
    "apps": ["2to3", "chameleon", "html5lib", "tornado_http"],
    "math": ["float", "nbody", "pidigits"],
    "template": ["django_template", "mako"],
}


def BM_2to3(python, options):
    return run_perf_script(python, options, "2to3")


# def BM_hg_startup(python, options):
#     return run_perf_script(python, options, "hg_startup")


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


def BM_xml_etree(python, options):
    return run_perf_script(python, options, "xml_etree")


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


def BM_raytrace(python, options):
    return run_perf_script(python, options, "raytrace")


def BM_logging(python, options):
    return run_perf_script(python, options, "logging")


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


def BM_regex_dna(python, options):
    return run_perf_script(python, options, "regex_dna")


def BM_unpack_sequence(python, options):
    return run_perf_script(python, options, "unpack_sequence")


def BM_nbody(python, options):
    return run_perf_script(python, options, "nbody")


# def BM_html5lib(python, options):
#     return run_perf_script(python, options, "html5lib")


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


def BM_pyflate(python, options):
    return run_perf_script(python, options, "pyflate")


def BM_sqlite_synth(python, options):
    return run_perf_script(python, options, "sqlite_synth")


def BM_genshi(python, options):
    return run_perf_script(python, options, "genshi")


def BM_sqlalchemy_declarative(python, options):
    return run_perf_script(python, options, "sqlalchemy_declarative")


def BM_sqlalchemy_imperative(python, options):
    return run_perf_script(python, options, "sqlalchemy_imperative")


def BM_mdp(python, options):
    return run_perf_script(python, options, "mdp")


# End benchmarks, begin main entry point support.

def get_benchmarks():
    bench_funcs = dict((name[3:].lower(), func)
                       for name, func in globals().items()
                       if name.startswith("BM_"))

    bench_groups = BENCH_GROUPS.copy()

    # create the 'all' group
    bench_groups["all"] = sorted(bench_funcs)

    return (bench_funcs, bench_groups)


def expand_benchmark_name(bm_name, bench_groups):
    """Recursively expand name benchmark names.

    Args:
        bm_name: string naming a benchmark or benchmark group.

    Yields:
        Names of actual benchmarks, with all group names fully expanded.
    """
    expansion = bench_groups.get(bm_name)
    if expansion:
        for name in expansion:
            for name in expand_benchmark_name(name, bench_groups):
                yield name
    else:
        yield bm_name


def select_benchmarks(benchmarks, bench_groups):
    legal_benchmarks = bench_groups["all"]
    benchmarks = benchmarks.split(",")
    positive_benchmarks = set(bm.lower()
                              for bm in benchmarks
                              if bm and not bm.startswith("-"))
    negative_benchmarks = set(bm[1:].lower()
                              for bm in benchmarks
                              if bm and bm.startswith("-"))

    should_run = set()
    if not positive_benchmarks:
        should_run = set(expand_benchmark_name("default", bench_groups))

    for name in positive_benchmarks:
        for bm in expand_benchmark_name(name, bench_groups):
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
