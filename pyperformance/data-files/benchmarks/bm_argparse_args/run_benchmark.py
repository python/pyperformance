"""
Benchmark argparse program with many optional arguments.

Author: Savannah Ostrowski
"""

import pyperf
import argparse

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A CLI tool with many optional and positional arguments"
    )

    parser.add_argument("input_file", type=str, help="The input file")
    parser.add_argument("output_file", type=str, help="The output file")

    for i in range(1000):
        parser.add_argument(f"--option{i}", type=str, help=f"Optional argument {i}")

    return parser

def generate_arguments(i: int) -> list:
    arguments = ["input.txt", "output.txt"]
    for i in range(i):
        arguments.extend([f"--option{i}", f"value{i}"])
    return arguments

def bench_argparse(loops: int) -> None:
    argument_lists = [
        generate_arguments(500),
        generate_arguments(1000),
    ]

    parser = create_parser()
    range_it = range(loops)
    t0 = pyperf.perf_counter()

    for _ in range_it:
        for args in argument_lists:
            parser.parse_args(args)

    return pyperf.perf_counter() - t0

if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Benchmark the argparse program with many optional arguments"

    runner.bench_time_func("argparse", bench_argparse)