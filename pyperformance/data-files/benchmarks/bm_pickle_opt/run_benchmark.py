"""The background for this benchmark is that the garbage collection in Python 3.14
had a performance regression, see

* https://github.com/python/cpython/issues/140175
* https://github.com/python/cpython/issues/139951

"""

import tempfile
from pathlib import Path

import pyperf


def setup(fname, N):
    import pickle

    x = {}
    for i in range(1, N):
        x[i] = f"ii{i:>07}"

    with open(fname, "wb") as fh:
        pickle.dump(x, fh, protocol=4)


def run(fname):
    import pickletools

    with open(fname, "rb") as fh:
        p = fh.read()

    s = pickletools.optimize(p)

    with open(fname.with_suffix(".out"), "wb") as fh:
        fh.write(s)


if __name__ == "__main__":
    runner = pyperf.Runner()
    N = 1_000_000
    tmp_path = Path(tempfile.mkdtemp())
    fname = tmp_path / "pickle"
    setup(fname, N)
    runner.metadata["description"] = "Pickletools optimize"
    runner.bench_func("pickle_opt", run, fname)
