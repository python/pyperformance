"""Measure full collection of a larger population of cyclic garbage."""

import gc

import pyperf

from run_benchmark import LINKS, create_gc_cycles


CYCLES = 10_000


def benchmark_collection(loops, cycles, links):
    """Time full collections of independent reference cycles.

    loops: Number of measured collections.
    cycles: Number of independent rings in each collection.
    links: Number of nodes added after each ring's first node.
    Return: Total collection wall time in seconds, excluding setup and checks.
    The caller's automatic-GC state is restored on return.
    """
    get_debug = getattr(gc, "get_debug", None)
    if get_debug is not None and get_debug():
        raise RuntimeError("benchmark requires GC debug flags to be disabled")
    was_enabled = gc.isenabled()
    total_time = 0.0
    try:
        for _ in range(loops):
            gc.enable()
            gc.collect()
            if gc.garbage:
                raise RuntimeError("benchmark starts with uncollectable garbage")
            roots = create_gc_cycles(cycles, links)

            # Keep the graph rooted until the explicit collection is ready.
            gc.disable()
            roots = None
            started = pyperf.perf_counter()
            collected = gc.collect()
            total_time += pyperf.perf_counter() - started

            if collected is not None and collected < cycles * (links + 1):
                raise RuntimeError("collection reclaimed fewer nodes than the fixture created")
            if gc.garbage:
                raise RuntimeError("collection produced uncollectable garbage")
    finally:
        if was_enabled:
            gc.enable()
        else:
            gc.disable()
    return total_time


def add_cmdline_args(command, args):
    """Pass the selected graph size to each worker.

    command: Worker command to extend.
    args: Parsed benchmark arguments.
    Return: None.
    """
    command.extend(("--cycles", str(args.cycles)))


if __name__ == "__main__":
    runner = pyperf.Runner(add_cmdline_args=add_cmdline_args)
    runner.argparser.add_argument("--cycles", type=int, default=CYCLES, help="Number of independent reference cycles.")
    args = runner.parse_args()
    if args.cycles < 1:
        runner.argparser.error("--cycles must be positive")
    runner.metadata["description"] = "Full collection of many independent reference cycles"
    runner.metadata["gc_cycles"] = args.cycles
    runner.metadata["gc_links"] = LINKS
    runner.metadata["gc_nodes"] = args.cycles * (LINKS + 1)
    runner.bench_time_func("gc_collect_large", benchmark_collection, args.cycles, LINKS)
