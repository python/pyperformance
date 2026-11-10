"""Measure B-tree collection after freezing the startup heap."""

import gc
import random

import pyperf

from run_benchmark import NUM_NODES, RANDOM_SEED, add_metadata, make_records, make_tree


def benchmark_collection(loops, nodes):
    """Time full collections of a B-tree created after freezing the heap.

    loops: Number of trees and measured collections.
    nodes: Number of records in each tree.
    Return: Total collection wall time in seconds, excluding setup and checks.
    Requires an empty permanent generation; unfreezes the heap and restores
    the caller's automatic-GC state on return.
    """
    if not all(hasattr(gc, name) for name in ("freeze", "unfreeze", "get_freeze_count")):
        raise RuntimeError("benchmark requires the GC freeze API")
    if gc.get_freeze_count():
        raise RuntimeError("benchmark requires an empty permanent generation")
    get_debug = getattr(gc, "get_debug", None)
    if get_debug is not None and get_debug():
        raise RuntimeError("benchmark requires GC debug flags to be disabled")

    was_enabled = gc.isenabled()
    must_unfreeze = False
    total_time = 0.0
    try:
        gc.enable()
        gc.collect()
        if gc.garbage:
            raise RuntimeError("benchmark starts with uncollectable garbage")
        anchor = []
        if not gc.is_tracked(anchor):
            raise RuntimeError("frozen anchor is not tracked")
        # An interrupted freeze may already have moved objects.
        must_unfreeze = True
        gc.freeze()
        if gc.get_freeze_count() == 0:
            raise RuntimeError("freeze did not populate the permanent generation")

        # The new holder gives the ordinary heap a reference to a frozen object.
        holder = [anchor]
        records = list(make_records(nodes))
        for _ in range(loops):
            gc.enable()
            random.seed(RANDOM_SEED)
            tree = make_tree(nodes, records)
            gc.disable()
            started = pyperf.perf_counter()
            collected = gc.collect()
            total_time += pyperf.perf_counter() - started

            if collected is not None and collected != 0:
                raise RuntimeError(f"live-tree collection reclaimed {collected} objects")
            if len(tree) != nodes:
                raise RuntimeError("collection changed the tree size")
            for index in (0, nodes // 2, nodes - 1):
                if tree[index] is not records[index]:
                    raise RuntimeError(f"collection changed record {index}")
            if holder[0] is not anchor or not gc.is_tracked(holder) or not gc.is_tracked(anchor):
                raise RuntimeError("collection changed the frozen anchor or its holder")
            if gc.get_freeze_count() == 0 or gc.garbage:
                raise RuntimeError("collection lost the permanent generation or produced garbage")
            tree = None
    finally:
        try:
            if must_unfreeze:
                gc.unfreeze()
        finally:
            if was_enabled:
                gc.enable()
            else:
                gc.disable()
    return total_time


def add_cmdline_args(command, args):
    """Pass the selected tree size to each worker.

    command: Worker command to extend.
    args: Parsed benchmark arguments.
    Return: None.
    """
    command.extend(("--nodes", str(args.nodes)))


if __name__ == "__main__":
    runner = pyperf.Runner(add_cmdline_args=add_cmdline_args, processes=1, loops=1, values=3, warmups=1, min_time=0.4)
    runner.argparser.add_argument("--nodes", type=int, default=NUM_NODES, help="Number of records in each B-tree.")
    args = runner.parse_args()
    if args.nodes < 1:
        runner.argparser.error("--nodes must be positive")
    add_metadata(runner)
    runner.metadata["description"] = "Full collection of a B-tree created after freezing the startup heap"
    runner.metadata["btree_num_nodes"] = args.nodes
    runner.bench_time_func("btree_gc_only_frozen", benchmark_collection, args.nodes)
