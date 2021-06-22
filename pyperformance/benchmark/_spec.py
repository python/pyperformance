from collections import namedtuple


BenchmarkSpec = namedtuple('BenchmarkSpec', 'name version origin metafile')


def parse_benchmark(entry):
    name = entry
    version = None
    origin = None
    metafile = None
    if not f'_{name}'.isidentifier():
        raise ValueError(f'unsupported benchmark name in {entry!r}')
    return BenchmarkSpec(name, version, origin, metafile)
