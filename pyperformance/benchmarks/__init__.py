from collections import namedtuple

from .. import _benchmarks


Benchmark = namedtuple('Benchmark', 'name run')


def load_manifest(filename):
    # XXX
    return filename


def iter_benchmarks(manifest):
    # XXX Pull from the manifest.
    funcs, _ = _benchmarks.get_benchmarks()
    for name, func in funcs.items():
        yield Benchmark(name, func)


def get_benchmarks(manifest):
    return list(iter_benchmarks(manifest))


def get_benchmark_groups(manifest):
    # XXX Pull from the manifest.
    # XXX Return more than just bench names.
    _, groups = _benchmarks.get_benchmarks()
    return groups


def select_benchmarks(raw, manifest):
    # XXX Pull from the manifest.
    funcs, groups = _benchmarks.get_benchmarks()
    for name in _benchmarks.select_benchmarks(raw, groups):
        yield Benchmark(name, funcs[name])
