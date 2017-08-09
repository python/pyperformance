"""
Benchmark threading module.
"""

# The benchmark is inspired from pymotw.com

import perf
from six.moves import xrange
import threading
import random, time

def worker():
    pause = random.randint(1, 5) / 10
    time.sleep(pause)

def bench_threading():
    for i in xrange(3):
        t = threading.Thread(target=worker)
        t.setDaemon(True)
        t.start()

    current_thread = threading.current_thread()
    for t in threading.enumerate():
        if t is current_thread:
            continue
        t.join()


if __name__ == "__main__":
    runner = perf.Runner()
    runner.metadata['description'] = "Performance of the threading module"
    args = runner.parse_args()
    runner.bench_func('threading', bench_threading)
