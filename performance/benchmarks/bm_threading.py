"""
Benchmark threading module.
"""

import perf
from six.moves import xrange
import threading


def add_cmdline_args(cmd, args):
    if args.benchmark:
        cmd.append(args.benchmark)


def consumer(cond):
    with cond:
        cond.wait()


def producer(cond):
    with cond:
        cond.notifyAll()


# This does not favour py2 or py3
def worker():
    pass


def bench_basic_threading(loops):
    range_it = xrange(loops)
    t0 = perf.perf_counter()

    for _ in range_it:
        for i in xrange(3):
            t = threading.Thread()
            t.start()

        current_thread = threading.current_thread()
        for t in threading.enumerate():
            if t is current_thread:
                continue
            t.join()

    dt = perf.perf_counter() - t0

    return dt


def bench_timer_threading(loops):
    range_it = xrange(loops)
    t0 = perf.perf_counter()

    for _ in range_it:
        t = threading.Timer(0, worker)
        t.start()

    dt = perf.perf_counter() - t0

    return dt


def bench_lock_threading(loops):
    range_it = xrange(loops)
    t0 = perf.perf_counter()

    LOCK_OBJECT = threading.Lock()

    for _ in range_it:
        LOCK_OBJECT.acquire()
        LOCK_OBJECT.release()

    dt = perf.perf_counter() - t0

    return dt


def bench_rlock_threading(loops):
    range_it = xrange(loops)
    t0 = perf.perf_counter()

    LOCK_OBJECT = threading.RLock()

    for _ in range_it:
        LOCK_OBJECT.acquire()
        LOCK_OBJECT.release()

    dt = perf.perf_counter() - t0

    return dt


def bench_condition_threading(loops):
    range_it = xrange(loops)
    t0 = perf.perf_counter()

    CONDITION_OBJECT = threading.Condition()

    for _ in range_it:
        CONDITION_OBJECT.acquire()
        CONDITION_OBJECT.release()

    dt = perf.perf_counter() - t0

    return dt


def bench_notify_threading(loops):
    range_it = xrange(loops)
    t0 = perf.perf_counter()

    condition = threading.Condition()

    for _ in range_it:
        c = threading.Thread(target=consumer,
                             args=(condition,))
        p = threading.Thread(target=producer,
                             args=(condition,))

        c.start()
        p.start()
    dt = perf.perf_counter() - t0

    return dt


def bench_semaphore_threading(loops):
    range_it = xrange(loops)
    t0 = perf.perf_counter()

    SEMAPHORE_OBJECT = threading.Semaphore()

    for _ in range_it:
        SEMAPHORE_OBJECT.acquire()
        SEMAPHORE_OBJECT.release()

    dt = perf.perf_counter() - t0

    return dt


BENCHMARKS = {
    "basic":     bench_basic_threading,
    "timer":     bench_timer_threading,
    "lock":      bench_lock_threading,
    "rlock":     bench_rlock_threading,
    "condition": bench_condition_threading,
    "notify":    bench_notify_threading,
    "semaphore": bench_semaphore_threading,
}

if __name__ == "__main__":
    runner = perf.Runner(add_cmdline_args=add_cmdline_args)

    runner.metadata['description'] = "Performance of the threading module"

    parser = runner.argparser
    parser.add_argument("benchmark", nargs='?', choices=sorted(BENCHMARKS))

    options = runner.parse_args()

    if options.benchmark:
        benchmarks = (options.benchmark,)
    else:
        benchmarks = sorted(BENCHMARKS)

    for bench in benchmarks:
        name = '%s' % bench
        bench_func = BENCHMARKS[bench]

        runner.bench_time_func(name, bench_func, inner_loops=10)
