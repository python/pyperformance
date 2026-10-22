"""Measure collection of fresh retained tuples containing atomic items."""

import gc

import pyperf


ENTRIES = 200_000
WIDTH = 16


def benchmark_collection(loops, entries, width):
    """Time collections of fresh tuples retained across the collection.

    loops: Number of measured collections.
    entries: Positive number of tuples in each collection.
    width: Positive number of None items in each tuple.
    Return: Total collection wall time in seconds, excluding setup and checks.
    The caller's automatic-GC state is restored on return or failure.
    """
    assert entries > 0 and width > 0
    get_debug = getattr(gc, "get_debug", None)
    if get_debug is not None and get_debug():
        raise RuntimeError("benchmark requires GC debug flags to be disabled")

    was_enabled = gc.isenabled()
    roots = []
    seed = (None,) * width
    total_time = 0.0
    try:
        gc.disable()
        # With the GIL collector, the retained root must be older than the fresh tuples.
        gc.collect()
        if gc.garbage:
            raise RuntimeError("benchmark starts with uncollectable garbage")

        for _ in range(loops):
            try:
                # Going through an iterator creates fresh tuples instead of reusing seed.
                for _ in range(entries):
                    roots.append(tuple(iter(seed)))

                started = pyperf.perf_counter()
                collected = gc.collect(0)
                total_time += pyperf.perf_counter() - started

                if collected is not None and collected != 0:
                    raise RuntimeError(f"survivor collection reclaimed {collected} objects")
                if len(roots) != entries or any(roots[index] != seed for index in (0, entries // 2, entries - 1)):
                    raise RuntimeError("collection changed the retained tuples")
                if gc.garbage:
                    raise RuntimeError("collection produced uncollectable garbage")
            finally:
                roots.clear()
                # Discarded tuples must not carry into the next measured collection.
                gc.collect()
            if gc.garbage:
                raise RuntimeError("cleanup produced uncollectable garbage")
    finally:
        if was_enabled:
            gc.enable()
        else:
            gc.disable()
    return total_time


def add_cmdline_args(command, args):
    """Pass the selected tuple population to each worker.

    command: Worker command to extend.
    args: Parsed benchmark arguments.
    Return: None.
    """
    command.extend(("--entries", str(args.entries), "--width", str(args.width)))


if __name__ == "__main__":
    runner = pyperf.Runner(add_cmdline_args=add_cmdline_args)
    runner.argparser.add_argument("--entries", type=int, default=ENTRIES, help="Number of retained tuples.")
    runner.argparser.add_argument("--width", type=int, default=WIDTH, help="Number of None items in each tuple.")
    args = runner.parse_args()
    if args.entries < 1:
        runner.argparser.error("--entries must be positive")
    if args.width < 1:
        runner.argparser.error("--width must be positive")
    runner.metadata["description"] = "Collection of fresh retained tuples containing only None"
    runner.metadata["gc_tuple_entries"] = args.entries
    runner.metadata["gc_tuple_width"] = args.width
    runner.metadata["gc_tuple_items"] = "none"
    runner.metadata["gc_requested_generation"] = 0
    runner.bench_time_func("gc_tuple_survivors", benchmark_collection, args.entries, args.width)
