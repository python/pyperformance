"""
Benchmark Python startup.
"""
import sys

import perf


def add_cmdline_args(cmd, args):
    if args.no_site:
        cmd.append("--no-site")


if __name__ == "__main__":
    runner = perf.Runner(values=10, add_cmdline_args=add_cmdline_args)
    runner.argparser.add_argument("--no-site", action="store_true")

    runner.metadata['description'] = "Performance of the Python startup"
    args = runner.parse_args()
    name = 'python_startup'
    if args.no_site:
        name += "_no_site"

    command = [sys.executable]
    if args.no_site:
        command.append("-S")
    command.extend(("-c", "pass"))

    runner.bench_command(name, command)
