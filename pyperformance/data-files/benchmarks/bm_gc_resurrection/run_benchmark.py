"""Measure collection when callbacks require garbage to be checked again."""

import gc
import weakref

import pyperf


CYCLES = 10_000
RING_SIZE = 21


class Node:
    """A ring member with a version-independent tracked-object count.

    next: Next ring member.
    prev: Previous ring member.
    __weakref__: Slot used by the weakref callback variant.
    """

    __slots__ = ("next", "prev", "__weakref__")

    def __init__(self):
        """Create an unlinked ring member.

        Return: None.
        """
        self.next = None
        self.prev = None


class Rescuer(Node):
    """A ring member whose finalizer retains a selected part of the graph.

    payload: List of ring roots retained with this object.
    calls: Number of finalizer calls for the current population.
    holder: Preallocated external root slot receiving this object.
    """

    __slots__ = ("payload",)
    calls = 0
    holder = [None]

    def __init__(self, payload):
        """Create an unlinked member carrying the selected roots.

        payload: List of ring roots to retain during finalization.
        Return: None.
        """
        super().__init__()
        self.payload = payload

    def __del__(self):
        """Record finalization and retain this object in the external slot.

        Return: None.
        """
        Rescuer.calls += 1
        Rescuer.holder[0] = self


weakref_calls = 0
weakref_was_cleared = False


def record_weakref(reference):
    """Record one callback without retaining a fixture object.

    reference: Weakref supplied by the collector.
    Return: None.
    """
    global weakref_calls, weakref_was_cleared
    weakref_calls += 1
    weakref_was_cleared = reference() is None


def create_cycles(cycles):
    """Create independent bidirectional rings.

    cycles: Number of rings, each containing RING_SIZE nodes.
    Return: List holding one root for every ring.
    """
    roots = []
    for _ in range(cycles):
        first = Node()
        previous = first
        for _ in range(RING_SIZE - 1):
            node = Node()
            previous.next = node
            node.prev = previous
            previous = node
        previous.next = first
        first.prev = previous
        roots.append(first)
    return roots


def prepare_collection(cycles, mode):
    """Create the selected graph while retaining all its rings.

    cycles: Even number of rings, at least two.
    mode: weakref, partial, or full.
    Return: Construction roots and the retained callback weakref, if any.
    """
    global weakref_calls, weakref_was_cleared
    assert cycles >= 2 and cycles % 2 == 0
    if mode not in ("weakref", "partial", "full"):
        raise ValueError("unknown resurrection mode: " + mode)
    if Rescuer.holder[0] is not None:
        raise RuntimeError("a prior rescued graph is still retained")
    Rescuer.calls = 0
    weakref_calls = 0
    weakref_was_cleared = False
    roots = create_cycles(cycles)
    if mode == "weakref":
        return roots, weakref.ref(roots[0], record_weakref)

    if mode == "partial":
        selected = cycles // 2
    else:
        assert mode == "full"
        selected = cycles
    # Copy even the full set so both modes drop the same construction root.
    rescuer = Rescuer(roots[:selected])
    first = roots[0]
    successor = first.next
    first.next = rescuer
    rescuer.prev = first
    rescuer.next = successor
    successor.prev = rescuer
    return roots, None


def check_events(mode, reference):
    """Check the callback events for one population.

    mode: weakref, partial, or full.
    reference: Retained weakref in weakref mode, otherwise None.
    Return: None after checking event counts and weakref state.
    """
    expected_callbacks = 1 if mode == "weakref" else 0
    expected_finalizers = 0 if mode == "weakref" else 1
    if weakref_calls != expected_callbacks:
        raise RuntimeError(f"observed {weakref_calls} weakref callbacks, expected {expected_callbacks}")
    if Rescuer.calls != expected_finalizers:
        raise RuntimeError(f"observed {Rescuer.calls} finalizers, expected {expected_finalizers}")
    if mode == "weakref":
        if reference is None or reference() is not None or not weakref_was_cleared:
            raise RuntimeError("weakref callback did not observe a cleared reference")
        if Rescuer.holder[0] is not None:
            raise RuntimeError("weakref callback unexpectedly retained a graph")
    else:
        assert mode in ("partial", "full")
        if reference is not None or weakref_was_cleared:
            raise RuntimeError("resurrection unexpectedly recorded a weakref callback")


def check_rescued_graph(cycles, mode, complete):
    """Check ownership and selected links in the rescued graph.

    cycles: Number of rings created for this population.
    mode: partial or full.
    complete: Whether to inspect every retained ring instead of local links.
    Return: Expected number of original ring nodes retained.
    """
    if mode == "partial":
        selected = cycles // 2
    elif mode == "full":
        selected = cycles
    else:
        raise ValueError("unknown rescued-graph mode: " + mode)
    rescuer = Rescuer.holder[0]
    if type(rescuer) is not Rescuer:
        raise RuntimeError("finalizer did not retain its Rescuer")
    roots = rescuer.payload
    if type(roots) is not list or len(roots) != selected:
        raise RuntimeError("rescued payload has an unexpected type or size")
    if rescuer.next.prev is not rescuer or rescuer.prev.next is not rescuer:
        raise RuntimeError("rescued graph lost a link beside its Rescuer")

    if complete:
        rescuer_visits = 0
        for index, root in enumerate(roots):
            current = root
            ring_size = RING_SIZE + 1 if index == 0 else RING_SIZE
            for _ in range(ring_size):
                if current.next.prev is not current or current.prev.next is not current:
                    raise RuntimeError("rescued graph lost a ring link")
                rescuer_visits += current is rescuer
                current = current.next
            if current is not root:
                raise RuntimeError("rescued ring has an unexpected size")
        if rescuer_visits != 1:
            raise RuntimeError("rescued graph has an unexpected Rescuer count")
    return selected * RING_SIZE


def collect_population(cycles, mode, complete):
    """Measure reclamation of one population and release its rescued objects.

    cycles: Even number of rings, at least two.
    mode: weakref, partial, or full.
    complete: Whether to inspect every rescued ring outside timing.
    Return: Wall time spent in collections needed to reclaim unrescued garbage.
    Setup, validation, and final cleanup are excluded. Automatic GC is restored.
    """
    get_debug = getattr(gc, "get_debug", None)
    if get_debug is not None and get_debug():
        raise RuntimeError("benchmark requires GC debug flags to be disabled")
    was_enabled = gc.isenabled()
    roots = None
    reference = None
    needs_cleanup = True
    try:
        gc.disable()
        gc.collect()
        if gc.garbage:
            raise RuntimeError("benchmark starts with uncollectable garbage")
        roots, reference = prepare_collection(cycles, mode)
        roots = None
        started = pyperf.perf_counter()
        collected = gc.collect()
        total_time = pyperf.perf_counter() - started
        if type(collected) is not int:
            raise RuntimeError("benchmark requires gc.collect() to report an integer reclamation count")
        check_events(mode, reference)

        nodes = cycles * RING_SIZE
        if mode == "weakref":
            expected_collected = nodes
            expected_cleanup = 0
        else:
            assert mode in ("partial", "full")
            rescued_nodes = check_rescued_graph(cycles, mode, complete)
            expected_collected = nodes - rescued_nodes
            # The Rescuer and its payload list add two tracked objects.
            expected_cleanup = rescued_nodes + 2

        if mode == "partial" and collected == 0:
            # Older collectors defer the whole set when any object resurrects.
            # Include the collection needed to finish the same reclamation work.
            started = pyperf.perf_counter()
            collected = gc.collect()
            total_time += pyperf.perf_counter() - started
            check_events(mode, reference)
            check_rescued_graph(cycles, mode, False)
        if type(collected) is not int or collected != expected_collected:
            raise RuntimeError(f"collection reclaimed {collected} objects, expected {expected_collected}")

        Rescuer.holder[0] = None
        cleanup = gc.collect()
        if type(cleanup) is not int or cleanup != expected_cleanup:
            raise RuntimeError(f"cleanup reclaimed {cleanup} objects, expected {expected_cleanup}")
        check_events(mode, reference)
        if Rescuer.holder[0] is not None or gc.garbage:
            raise RuntimeError("cleanup retained a graph or uncollectable garbage")
        needs_cleanup = False
        return total_time
    finally:
        try:
            roots = None
            reference = None
            Rescuer.holder[0] = None
            if needs_cleanup:
                gc.collect()
        finally:
            Rescuer.holder[0] = None
            if was_enabled:
                gc.enable()
            else:
                gc.disable()


def benchmark_collection(loops, cycles, mode):
    """Time repeated collections with the selected callback outcome.

    loops: Number of measured populations.
    cycles: Even number of rings in each population, at least two.
    mode: weakref, partial, or full.
    Return: Total collection wall time in seconds.
    """
    total_time = 0.0
    for _ in range(loops):
        total_time += collect_population(cycles, mode, False)
    return total_time


def add_cmdline_args(command, args):
    """Pass the selected graph size and callback mode to each worker.

    command: Worker command to extend.
    args: Parsed benchmark arguments.
    Return: None.
    """
    command.extend(("--cycles", str(args.cycles), "--mode", args.mode))


if __name__ == "__main__":
    runner = pyperf.Runner(add_cmdline_args=add_cmdline_args)
    runner.argparser.add_argument("--cycles", type=int, default=CYCLES, help="Even number of independent reference cycles.")
    runner.argparser.add_argument("--mode", choices=("weakref", "partial", "full"), required=True)
    args = runner.parse_args()
    if args.cycles < 2 or args.cycles % 2:
        runner.argparser.error("--cycles must be an even integer of at least two")
    names = {"weakref": "gc_weakref_recheck", "partial": "gc_resurrection_partial", "full": "gc_resurrection_full"}
    runner.metadata["description"] = "GC callback and resurrection benchmark"
    runner.metadata["gc_cycles"] = args.cycles
    runner.metadata["gc_nodes"] = args.cycles * RING_SIZE
    runner.metadata["gc_callback_mode"] = args.mode
    # Each worker proves the lifecycle on a small graph before reporting timings.
    collect_population(2, args.mode, True)
    runner.bench_time_func(names[args.mode], benchmark_collection, args.cycles, args.mode)
