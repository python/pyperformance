"""
Benchmark ``loads()`` function of the ``tomllib`` stdlib module
on a large TOML file of GitHub's real world data.
It heavily exercises string operations such as concatenation,
subscripting and iteration of a real world application.

Author: Kumar Aditya
"""

from pathlib import Path

import pyperf
import tomllib

DATA_FILE = Path(__file__).parent / "data" / "tomllib-bench-data.toml"

def bench_tomllib_loads(loops: int) -> None:
    data = DATA_FILE.read_text('utf-8')
    range_it = range(loops)
    t0 = pyperf.perf_counter()
    for _ in range_it:
        tomllib.loads(data)
    return pyperf.perf_counter() - t0

if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Benchmark tomllib.loads()"
    runner.bench_time_func('tomllib_loads', bench_tomllib_loads)