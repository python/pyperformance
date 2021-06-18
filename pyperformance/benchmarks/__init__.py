from .. import _benchmarks


def load_manifest(filename):
    # XXX
    return filename


def get_benchmarks(manifest):
    # XXX Pull from the manifest.
    _, groups = _benchmarks.get_benchmarks()
    return groups['all']


def get_benchmark_groups(manifest):
    # XXX Pull from the manifest.
    # XXX Return more than just bench names.
    _, groups = _benchmarks.get_benchmarks()
    return groups


def select_benchmarks(raw, manifest):
    # XXX Pull from the manifest.
    _, groups = _benchmarks.get_benchmarks()
    return _benchmarks.select_benchmarks(raw, groups)


# XXX This should go away.
def _get_bench_funcs(manifest):
    funcs, _ = _benchmarks.get_benchmarks()
    return funcs
