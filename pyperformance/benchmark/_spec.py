from collections import namedtuple

from .. import _utils


def check_name(name):
    _utils.check_name('_' + name)


def parse_benchmark(entry, *, fail=True):
    name = entry
    version = None
    origin = None
    metafile = None

    if not f'_{name}'.isidentifier():
        if not fail:
            return None
        raise ValueError(f'unsupported benchmark name in {entry!r}')

    bench = BenchmarkSpec(name, version, origin)
    return bench, metafile


class BenchmarkSpec(namedtuple('BenchmarkSpec', 'name version origin')):
    __slots__ = ()

    @classmethod
    def from_raw(cls, raw):
        if isinstance(raw, BenchmarkSpec):
            return raw, None
        elif isinstance(raw, str):
            return parse_benchmark(raw)
        else:
            raise ValueError(f'unsupported raw spec {raw!r}')
