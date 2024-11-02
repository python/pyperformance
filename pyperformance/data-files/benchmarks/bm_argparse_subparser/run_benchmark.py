"""
Benchmark the argparse module with multiple subparsers, each with their own 
subcommands, and then parse a series of command-line arguments.

Author: Savannah Ostrowski
"""

import argparse
import pyperf


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A version control system CLI")

    parser.add_argument("--version", action="version", version="1.0")

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a file to the repository")
    add_parser.add_argument("files", nargs="+", help="List of files to add to staging")

    commit_parser = subparsers.add_parser(
        "commit", help="Commit changes to the repository"
    )
    commit_parser.add_argument("-m", "--message", required=True, help="Commit message")

    commit_group = commit_parser.add_mutually_exclusive_group(required=False)
    commit_group.add_argument(
        "--amend", action="store_true", help="Amend the last commit"
    )
    commit_group.add_argument(
        "--no-edit", action="store_true", help="Reuse the last commit message"
    )

    push_parser = subparsers.add_parser(
        "push", help="Push changes to remote repository"
    )

    network_group = push_parser.add_argument_group("Network options")
    network_group.add_argument(
        "--dryrun", action="store_true", help="Do not push changes, only simulate"
    )
    network_group.add_argument(
        "--timeout", type=int, default=30, help="Timeout in seconds"
    )

    auth_group = push_parser.add_argument_group("Authentication options")
    auth_group.add_argument(
        "--username", required=True, help="Username for authentication"
    )
    auth_group.add_argument(
        "--password", required=True, help="Password for authentication"
    )

    global_group = parser.add_mutually_exclusive_group()
    global_group.add_argument("--verbose", action="store_true", help="Verbose output")
    global_group.add_argument("--quiet", action="store_true", help="Quiet output")

    return parser


def bench_argparse(loops: int) -> None:
    argument_lists = [
        ["--verbose", "add", "file1.txt", "file2.txt"],
        ["add", "file1.txt", "file2.txt"],
        ["commit", "-m", "Initial commit"],
        ["commit", "-m", "Add new feature", "--amend"],
        [
            "push",
            "--dryrun",
            "--timeout",
            "60",
            "--username",
            "user",
            "--password",
            "pass",
        ],
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
    runner.metadata["description"] = "Benchmark the argparse program with subparsers"

    runner.bench_time_func("argparse", bench_argparse)
