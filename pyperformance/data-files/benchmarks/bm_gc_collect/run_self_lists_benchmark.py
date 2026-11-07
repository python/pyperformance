"""Measure full collection of synthetic, minimal cyclic containers."""

import gc

import pyperf


CYCLES = 1_000_000


def create_self_lists(cycles):
    """Return rooted one-element lists that each contain themselves.

    cycles: Number of independent self-referential lists.
    Return: An outer list owning every cycle; no child is retained elsewhere.
    """
    roots = []
    for _ in range(cycles):
        node = []
        node.append(node)
        roots.append(node)
    return roots


def benchmark_collection(loops, cycles):
    """Time full collections of independent self-referential lists.

    loops: Number of measured collections.
    cycles: Number of lists in each collection.
    Return: Total collection wall time in seconds, excluding setup and checks.
    The caller's automatic-GC state is restored on return or failure.
    """
    get_debug = getattr(gc, "get_debug", None)
    if get_debug is not None and get_debug():
        raise RuntimeError("benchmark requires GC debug flags to be disabled")
    was_enabled = gc.isenabled()
    total_time = 0.0
    completed = False
    roots = None
    try:
        for _ in range(loops):
            gc.enable()
            gc.collect()
            if gc.garbage:
                raise RuntimeError("benchmark starts with uncollectable garbage")
            roots = create_self_lists(cycles)

            # Keep every cycle rooted until automatic collection is disabled.
            gc.disable()
            roots = None
            started = pyperf.perf_counter()
            collected = gc.collect()
            total_time += pyperf.perf_counter() - started

            if collected is not None and collected < cycles:
                raise RuntimeError("collection reclaimed fewer lists than the fixture created")
            if gc.garbage:
                raise RuntimeError("collection produced uncollectable garbage")
        completed = True
    finally:
        roots = None
        try:
            if not completed:
                # A failed worker should not leave its released cycles behind.
                gc.collect()
        finally:
            if was_enabled:
                gc.enable()
            else:
                gc.disable()
    return total_time


def add_cmdline_args(command, args):
    """Pass the selected population size to each worker.

    command: Worker command to extend.
    args: Parsed benchmark arguments.
    Return: None.
    """
    command.extend(("--cycles", str(args.cycles)))


if __name__ == "__main__":
    runner = pyperf.Runner(add_cmdline_args=add_cmdline_args)
    runner.argparser.add_argument("--cycles", type=int, default=CYCLES, help="Number of independent self-referential lists.")
    args = runner.parse_args()
    if args.cycles < 1:
        runner.argparser.error("--cycles must be positive")
    runner.metadata["description"] = "Full collection of synthetic one-element self-referential lists"
    runner.metadata["gc_cycles"] = args.cycles
    runner.metadata["gc_nodes"] = args.cycles
    runner.metadata["gc_references"] = args.cycles
    runner.bench_time_func("gc_collect_self_lists", benchmark_collection, args.cycles)
