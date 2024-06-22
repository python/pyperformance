"""
Benchmark the Dask scheduler running a large number of simple jobs.

Author: Matt Rocklin, Michael Droettboom
"""

import sys

from dask.distributed import Client, Worker, Scheduler, wait
from dask import distributed

import pyperf


def inc(x):
    return x + 1


async def benchmark():
    async with Scheduler() as scheduler:
        async with Worker(scheduler.address):
            async with Client(scheduler.address, asynchronous=True) as client:

                futures = client.map(inc, range(100))
                for _ in range(10):
                    futures = client.map(inc, futures)

                await wait(futures)


if __name__ == "__main__":
    if distributed.__version__ <= "2024.5.0" and sys.version_info >= (3, 13) and sys.platform == "win32":
        raise RuntimeError("Benchmark doesn't work with Python 3.13 on Windows")

    runner = pyperf.Runner()
    runner.metadata['description'] = "Benchmark dask"
    runner.bench_async_func('dask', benchmark)
