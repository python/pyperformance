# coding: utf-8
"""
Allocate blocks of memory with bytearray

This benchmark stresses memory allocator
"""

import pyperf


ONE_MB = 1024 * 1024

DEFAULT_SIZES = [32, 128, 512, 8192, ONE_MB, 8 * ONE_MB]
REPEAT_ALLOCS = 100


def allocate(repeat, sizes, alloc_func=bytearray):
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
