import os.path

from .. import __version__
from .. import _benchmarks, benchmark as _benchmark
from . import _manifest

# an alias (but also used here)
from ._parse import parse_benchmarks


DEFAULTS_DIR = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        '_benchmarks')
DEFAULT_MANIFEST = os.path.join(DEFAULTS_DIR, 'MANIFEST')


def load_manifest(filename, *, resolve=None):
    if not filename:
        filename = DEFAULT_MANIFEST
        if resolve is None:
            def resolve(bench):
                if not bench.version:
                    bench = bench._replace(version=__version__)
                if not bench.origin:
                    bench = bench._replace(origin='<default>')
                if not bench.metafile:
                    metafile = os.path.join(DEFAULTS_DIR,
                                            f'bm_{bench.name}',
                                            'METADATA')
                    #bench = bench._replace(metafile=metafile)
                    bench.metafile = metafile
                return bench
    with open(filename) as infile:
        return _manifest.parse_manifest(infile, resolve=resolve)


def iter_benchmarks(manifest):
    # XXX Use the benchmark's "run" script.
    funcs, _ = _benchmarks.get_benchmarks()
    for spec in manifest.benchmarks:
        func = funcs[spec.name]
        yield _benchmark.Benchmark(spec, func)


def get_benchmarks(manifest):
    return list(iter_benchmarks(manifest))


def get_benchmark_groups(manifest):
    return dict(manifest.groups)


def expand_benchmark_groups(parsed, groups):
    if isinstance(parsed, str):
        parsed = _benchmark.parse_benchmark(parsed)

    if not groups:
        yield parsed
    elif parsed.name not in groups:
        yield parsed
    else:
        benchmarks = groups[parsed.name]
        for bench in benchmarks or ():
            yield from expand_benchmark_groups(bench, groups)


def select_benchmarks(raw, manifest, *,
                      expand=None,
                      known=None,
                      ):
    if expand is None:
        groups = get_benchmark_groups(manifest)
        expand = lambda n: expand_benchmark_groups(n, groups)
    if known is None:
        known = get_benchmarks(manifest)
    benchmarks = {b.spec: b for b in get_benchmarks(manifest)}

    included, excluded = parse_benchmarks(raw, expand=expand, known=known)
    if not included:
        included = set(expand('default', 'add'))

    selected = set()
    for spec in included:
        bench = benchmarks[spec]
        selected.add(bench)
    for spec in excluded:
        bench = benchmarks[spec]
        selected.remove(bench)
    return selected
