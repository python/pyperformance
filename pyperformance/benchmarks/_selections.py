from .. import _benchmarks
from .._utils import check_name, parse_name_pattern, parse_tag_pattern
from ..benchmark import parse_benchmark, Benchmark
from ._manifest import expand_benchmark_groups


def parse_selection(selection, *, op=None):
    # "selection" is one of the following:
    # * a benchmark string
    # * a benchmark name
    # * a benchmark pattern
    # * a tag
    # * a tag pattern
    parsed = parse_benchmark(selection, fail=False)
    spec, metafile = parsed if parsed else (None, None)
    if parsed and spec.version:
        kind = 'benchmark'
        spec, metafile = parsed
        if metafile:
            parsed = Benchmark(spec, metafile)
        else:
            parsed = spec
    elif parsed and (spec.origin or metafile):
        raise NotImplementedError(selection)
    else:
        parsed = parse_tag_pattern(selection)
        if parsed:
            kind = 'tag'
        else:
            kind = 'name'
            parsed = parse_name_pattern(selection, fail=True)
#            parsed = parse_name_pattern(selection, fail=False)
            if not parsed:
                raise ValueError(f'unsupported selection {selection!r}')
    return op or '+', selection, kind, parsed


def iter_selections(manifest, selections, *, unique=True):
    byname = {b.name: b for b in manifest.benchmarks}

    # Compose the expanded include/exclude lists.
    seen = set()
    included = []
    excluded = set()
    for op, _, kind, parsed in selections:
        matches = _match_selection(manifest, kind, parsed, byname)
        if op == '+':
            for bench in matches:
                if bench not in seen or not unique:
                    included.append(bench)
                    seen.add(bench)
        elif op == '-':
            for bench in matches:
                excluded.add(bench)
        else:
            raise NotImplementedError(op)
    if not included:
        included = list(_match_selection(manifest, 'tag', 'default', byname))

    funcs, _ = _benchmarks.get_benchmarks()
    for bench in included:
        if bench not in excluded:
            if isinstance(bench, Benchmark):
                # XXX Use the benchmark's "run" script.
                bench._func = funcs[bench.name]
            yield bench


def _match_selection(manifest, kind, parsed, byname):
    if kind == 'benchmark':
        bench = parsed
        # XXX Match bench.metafile too?
        spec = getattr(bench, 'spec', bench)
        # For now we only support selection by name.
        # XXX Support selection by version?
        # XXX Support selection by origin?
        if spec.version or spec.origin:
            raise NotImplementedError(spec)
        if spec.name in byname:
            yield bench
        else:
            # No match!  The caller can handle this as they like.
            yield str(bench)
    elif kind == 'tag':
        # XXX Instad, walk all benchmarks to check the "tags" field?
        groups = []
        if callable(parsed):
            match_tag = parsed
            for group in manifest.groups:
                if match_tag(group):
                    groups.append(group)
        elif parsed in manifest.groups:
            groups.append(parsed)
        else:
            raise ValueError(f'unsupported selection {parsed!r}')
        for group in groups:
            yield from expand_benchmark_groups(group, manifest.groups)
    elif kind == 'name':
        if callable(parsed):
            match_bench = parsed
            for bench in manifest.benchmarks:
                if match_bench(bench.name):
                    yield bench
        else:
            name = parsed
            if name in byname:
                yield byname[name]
            # We also check the groups, for backward compatibility.
            elif name in manifest.groups:
                yield from _match_selection(manifest, 'tag', name, byname)
            else:
                check_name(name)
                # No match!  The caller can handle this as they like.
                yield name
    else:
        raise NotImplementedError(kind)
