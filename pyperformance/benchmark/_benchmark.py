from ._spec import parse_benchmark


class Benchmark:

    def __init__(self, spec, run):
        if isinstance(spec, str):
            spec = parse_benchmark(spec)

        self.spec = spec
        self.run = run

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
