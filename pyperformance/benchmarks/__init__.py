from .. import _benchmarks, benchmark as _benchmark
from ._parse import parse_benchmarks


def load_manifest(filename):
    # XXX
    return filename


def iter_benchmarks(manifest):
    # XXX Pull from the manifest.
    funcs, _ = _benchmarks.get_benchmarks()
    for name, func in funcs.items():
        yield _benchmark.Benchmark(name, func)


def get_benchmarks(manifest):
    return list(iter_benchmarks(manifest))


def get_benchmark_groups(manifest):
    # XXX Pull from the manifest.
    # XXX Return more than just bench names.
    _, groups = _benchmarks.get_benchmarks()
    return groups


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
