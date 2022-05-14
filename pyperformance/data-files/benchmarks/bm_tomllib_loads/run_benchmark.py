from pathlib import Path

import pyperf
import tomllib

DATA_FILE = Path(__file__).parent / "data" / "data.toml"

def bench_tomllib_loads(data: str, loops: int) -> float:
    t0 = pyperf.perf_counter()
    for _ in range(loops):
        tomllib.loads(data)
    return pyperf.perf_counter() - t0

if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Benchmark tomllib.loads()"
    data = DATA_FILE.read_text('utf-8')
    runner.bench_time_func('tomllib_loads', bench_tomllib_loads, data, loops=100)
