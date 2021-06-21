from collections import namedtuple

from .. import benchmark as _benchmark


BENCH_COLUMNS = ('name', 'version', 'origin', 'metafile')
BENCH_HEADER = '\t'.join(BENCH_COLUMNS)


BenchmarksManifest = namedtuple('BenchmarksManifest', 'benchmarks groups')


def parse_manifest(text, *, resolve=None):
    if isinstance(text, str):
        lines = text.splitlines()
    else:
        lines = iter(text)

    benchmarks = None
    groups = {}
    for section, seclines in _iter_sections(lines):
        if section == 'benchmarks':
            benchmarks = _parse_benchmarks(seclines, resolve)
        elif benchmarks is None:
            raise ValueError('invalid manifest file, expected "benchmarks" section')
        elif section.startswith('group '):
            _, _, group = section.partition(' ')
            groups[group] = _parse_group(group, seclines, benchmarks)
    return BenchmarksManifest(benchmarks, groups)


def _iter_sections(lines):
    lines = (line.split('#')[0].strip()
             for line in lines)

    name = None
    section = None
    for line in lines:
        if not line:
            continue
        if line.startswith('[') and line.endswith(']'):
            if name:
                yield name, section
            name = line[1:-1].strip()
            section = []
        else:
            if not name:
                raise ValueError(f'expected new section, got {line!r}')
            section.append(line)
    if name:
        yield name, section
    else:
        raise ValueError('invalid manifest file, no sections found')


def _parse_benchmarks(lines, resolve):
    if not lines:
        lines = ['<empty>']
    lines = iter(lines)
    if next(lines) != BENCH_HEADER:
        raise ValueError('invalid manifest file, expected benchmarks header')

    benchmarks = []
    for line in lines:
        try:
            name, version, origin, metafile = line.split('\t')
        except ValueError:
            raise ValueError(f'bad benchmark line {line!r}')
        if not version or version == '-':
            version = None
        if not origin or origin == '-':
            origin = None
        if not metafile or metafile == '-':
            metafile = None
        bench = _benchmark.BenchmarkSpec(name, version, origin, metafile)
        if resolve is not None:
            bench = resolve(bench)
        benchmarks.append(bench)
    return benchmarks


def _parse_group(name, lines, benchmarks):
    benchmarks = set(benchmarks)
    byname = {b.name: b for b in benchmarks}
    group = []
    for line in lines:
        bench = _benchmark.parse_benchmark(line)
        if bench not in benchmarks:
            try:
                bench = byname[bench.name]
            except KeyError:
                raise ValueError(f'unknown benchmark {bench.name!r} ({name})')
        group.append(bench)
    return group


#def render_manifest(manifest):
#    if isinstance(manifest, str):
#        raise NotImplementedError
#        manifest = manifest.splitlines()
#    yield BENCH_HEADER
#    for row in manifest:
#        if isinstance(row, str):
#            row = _parse_manifest_row(row)
#            if isinstance(row, str):
#                yield row
#                continue
#        line _render_manifest_row(row)
#
#    raise NotImplementedError
#
#
#def parse_group_manifest(text):
#    ...
#
#
#def render_group_manifest(group, benchmarks):
#    # (manifest file, bm name)
#    ...
#
#
#def parse_bench_from_manifest(line):
#    raise NotImplementedError
#
#
#def render_bench_for_manifest(benchmark, columns):
#    raise NotImplementedError
#    name, origin, version, metafile = info
