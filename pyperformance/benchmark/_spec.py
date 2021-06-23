from collections import namedtuple


class BenchmarkSpec(namedtuple('BenchmarkSpec', 'name version origin')):

    metafile = None

    def __new__(cls, name, version=None, origin=None, metafile=None):
        self = super().__new__(cls, name, version, origin)
        self.metafile = metafile
        return self


def parse_benchmark(entry):
    name = entry
    version = None
    origin = None
    metafile = None
    if not f'_{name}'.isidentifier():
        raise ValueError(f'unsupported benchmark name in {entry!r}')
    return BenchmarkSpec(name, version, origin, metafile)
