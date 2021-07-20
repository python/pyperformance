import os.path

from .. import __version__
from .. import benchmark as _benchmark
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
    else:
        filename = os.path.abspath(filename)
    if resolve is None:
        if filename == DEFAULT_MANIFEST:
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
                    bench.metafile = metafile
                return bench
    with open(filename) as infile:
        return _manifest.parse_manifest(infile, resolve=resolve, filename=filename)
