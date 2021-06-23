import os.path

from .. import __version__
from .. import _benchmarks, benchmark as _benchmark
from . import _manifest

# aliases
from ._manifest import expand_benchmark_groups
from ._selections import parse_selection, iter_selections


DEFAULTS_DIR = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        '_benchmarks')
DEFAULT_MANIFEST = os.path.join(DEFAULTS_DIR, 'MANIFEST')


def load_manifest(filename, *, resolve=None):
    if not filename:
        filename = DEFAULT_MANIFEST
        if resolve is None:
            def resolve(bench):
                if isinstance(bench, _benchmark.Benchmark):
                    spec = bench.spec
                else:
                    spec = bench
                    bench = _benchmark.Benchmark(spec, '<bogus>')
                    bench.metafile = None

                if not spec.version:
                    spec = spec._replace(version=__version__)
                if not spec.origin:
                    spec = spec._replace(origin='<default>')
                bench.spec = spec

                if not bench.metafile:
                    metafile = os.path.join(DEFAULTS_DIR,
                                            f'bm_{bench.name}',
                                            'pyproject.toml')
                    #bench = bench._replace(metafile=metafile)
                    bench.metafile = metafile
                return bench
    with open(filename) as infile:
        return _manifest.parse_manifest(infile, resolve=resolve)


def iter_benchmarks(manifest):
    # XXX Use the benchmark's "run" script.
    funcs, _ = _benchmarks.get_benchmarks()
    for bench in manifest.benchmarks:
        bench._func = funcs[bench.name]
        yield bench


def get_benchmarks(manifest):
    return list(iter_benchmarks(manifest))
