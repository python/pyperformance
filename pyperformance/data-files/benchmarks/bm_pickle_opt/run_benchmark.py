"""The background for this benchmark is that the garbage collection in
Python 3.14.0 had a performance regression, see

* https://github.com/python/cpython/issues/140175
* https://github.com/python/cpython/issues/139951

"""

import pickle
import pickletools
import pyperf


def setup(N: int) -> bytes:
    x = {i: f"ii{i:>07}" for i in range(N)}
    return pickle.dumps(x, protocol=4)


def run(p: bytes) -> None:
    pickletools.optimize(p)


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata["description"] = "Pickletools optimize"
    N = 100_000
    payload = setup(N)
    runner.bench_func("pickle_opt", run, payload)
