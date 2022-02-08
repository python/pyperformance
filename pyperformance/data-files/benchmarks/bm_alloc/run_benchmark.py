# coding: utf-8
"""
Allocate blocks of memory with bytearray

This benchmark stresses memory allocator. Default sizes are <=
obmalloc small request threshold.
"""

import sys

import pyperf

# see Objects/obmalloc.c
SMALL_REQUEST_THRESHOLD = 512
APPEND_SIZE = 10
SIZEOF_BYTEARRAY = sys.getsizeof(bytearray())

REPEAT_ALLOCS = 100

DEFAULT_SIZES = [
    4,
    8,
    16,
    32,
    64,
    128,
    256,
    # keep below obmalloc threshold
    SMALL_REQUEST_THRESHOLD - SIZEOF_BYTEARRAY - APPEND_SIZE,
]


def allocate(repeat, sizes, alloc_func=bytearray):
    append = alloc_func(APPEND_SIZE)
    for size in sizes:
        append = alloc_func(size)
        for i in range(repeat):
            # malloc()
            block = alloc_func(size)
            # realloc()
            block += append
        # free()
        del block


def add_cmdline_args(cmd, args):
    cmd.extend(("--repeat", str(args.repeat)))
    cmd.extend(tuple(str(s) for s in args.sizes))


if __name__ == "__main__":
    runner = pyperf.Runner(add_cmdline_args=add_cmdline_args)

    cmd = runner.argparser
    cmd.add_argument(
        "--repeat",
        type=int,
        default=REPEAT_ALLOCS,
        help=f"Repeat allocations (default: {REPEAT_ALLOCS})",
    )
    cmd.add_argument(
        "sizes",
        type=int,
        nargs="*",
        default=DEFAULT_SIZES,
        help=f"Block sizes (default: {' '.join(str(s) for s in DEFAULT_SIZES)})",
    )

    args = runner.parse_args()
    runner.metadata["description"] = "Allocate blocks of memory."
    runner.metadata["alloc_repeat"] = args.repeat
    runner.metadata["alloc_sizes"] = ",".join(str(s) for s in args.sizes)
    runner.bench_func("alloc", allocate, args.repeat, args.sizes)
