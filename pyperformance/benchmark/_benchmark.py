from ._spec import BenchmarkSpec


class Benchmark:

    def __init__(self, spec, metafile):
        spec, _metafile = BenchmarkSpec.from_raw(spec)
        if not metafile:
            if not _metafile:
                raise ValueError(f'missing metafile for {spec!r}')
            metafile = _metafile

        self.spec = spec
        self.metafile = metafile

    def __repr__(self):
        return f'{type(self).__name__}(spec={self.spec}, run={self.run})'

    def __getattr__(self, name):
        return getattr(self.spec, name)

    def __hash__(self):
        return hash(self.spec)

    def __eq__(self, other):
        try:
            other_spec = other.spec
        except AttributeError:
            return NotImplemented
        return self.spec == other_spec

    def __gt__(self, other):
        try:
            other_spec = other.spec
        except AttributeError:
            return NotImplemented
        return self.spec > other_spec

    def run(self, *args):
        return self._func(*args)
