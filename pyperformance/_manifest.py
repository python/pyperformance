
__all__ = [
    'BenchmarksManifest',
    'load_manifest',
    'parse_manifest',
    'expand_benchmark_groups',
]


from collections import namedtuple
import os.path


from . import __version__, DATA_DIR
from . import _benchmark, _utils


DEFAULTS_DIR = os.path.join(DATA_DIR, 'benchmarks')
DEFAULT_MANIFEST = os.path.join(DEFAULTS_DIR, 'MANIFEST')

BENCH_COLUMNS = ('name', 'metafile')
BENCH_HEADER = '\t'.join(BENCH_COLUMNS)


BenchmarksManifest = namedtuple('BenchmarksManifest', 'benchmarks groups')


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
        return parse_manifest(infile, resolve=resolve, filename=filename)


def parse_manifest(text, *, resolve=None, filename=None):
    if isinstance(text, str):
        lines = text.splitlines()
    else:
        lines = iter(text)
        if not filename:
            # Try getting the filename from a file.
            filename = getattr(text, 'name', None)

    benchmarks = None
    groups = {}
    for section, seclines in _iter_sections(lines):
        if section == 'benchmarks':
            benchmarks = _parse_benchmarks(seclines, resolve, filename)
        elif benchmarks is None:
            raise ValueError('invalid manifest file, expected "benchmarks" section')
        elif section == 'groups':
            for group in seclines:
                _utils.check_name(group)
                groups.setdefault(group, None)
        elif section.startswith('group '):
            _, _, group = section.partition(' ')
            groups[group] = _parse_group(group, seclines, benchmarks)
    _check_groups(groups)
    # XXX Update tags for each benchmark with member groups.
    return BenchmarksManifest(benchmarks, groups)


def expand_benchmark_groups(bench, groups):
    if isinstance(bench, str):
        spec, metafile = _benchmark.parse_benchmark(bench)
        if metafile:
            bench = _benchmark.Benchmark(spec, metafile)
        else:
            bench = spec
    elif isinstance(bench, _benchmark.Benchmark):
        spec = bench.spec
    else:
        spec = bench

    if not groups:
        yield bench
    elif bench.name not in groups:
        yield bench
    else:
        benchmarks = groups[bench.name]
        for bench in benchmarks or ():
            yield from expand_benchmark_groups(bench, groups)


#######################################
# internal implementation

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


def _parse_benchmarks(lines, resolve, filename):
    if not lines:
        lines = ['<empty>']
    lines = iter(lines)
    if next(lines) != BENCH_HEADER:
        raise ValueError('invalid manifest file, expected benchmarks table header')

    localdir = os.path.dirname(filename)

    benchmarks = []
    version = origin = None
    for line in lines:
        try:
            name, metafile = (None if l == '-' else l
                                               for l in line.split('\t'))
        except ValueError:
            raise ValueError(f'bad benchmark line {line!r}')
        spec = _benchmark.BenchmarkSpec(name or None, version, origin)
        if metafile:
            metafile = _resolve_metafile(metafile, name, localdir)
            bench = _benchmark.Benchmark(spec, metafile)
        else:
            bench = spec
        if resolve is not None:
            bench = resolve(bench)
        benchmarks.append(bench)
    return benchmarks


def _resolve_metafile(metafile, name, localdir):
    if not metafile.startswith('<') and not metafile.endswith('>'):
        return metafile

    directive, _, extra = metafile[1:-1].partition(':')
    if directive == 'local':
        if extra:
            rootdir = f'bm_{extra}'
            basename = f'bm_{name}.toml'
        else:
            rootdir = f'bm_{name}'
            basename = 'pyproject.toml'
        return os.path.join(localdir, rootdir, basename)
    else:
        raise ValueError(f'unsupported metafile directive {metafile!r}')


def _parse_group(name, lines, benchmarks):
    byname = {b.name: b for b in benchmarks}
    if name in byname:
        raise ValueError(f'a group and a benchmark have the same name ({name})')

    group = []
    seen = set()
    for line in lines:
        benchname = line
        _benchmark.check_name(benchname)
        if benchname in seen:
            continue
        if benchname in byname:
            group.append(byname[benchname])
        else:
            # It may be a group.  We check later.
            group.append(benchname)
    return group


def _check_groups(groups):
    for group, benchmarks in groups.items():
        for bench in benchmarks or ():
            if not isinstance(bench, str):
                continue
            elif bench not in groups:
                raise ValueError(f'unknown benchmark {name!r} (in group {group!r})')
