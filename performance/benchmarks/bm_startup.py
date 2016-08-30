import sys
import subprocess

import perf.text_runner
from six.moves import xrange


def bench_startup(loops, command):
    run = subprocess.check_call
    range_it = xrange(loops)
    t0 = perf.perf_counter()

    for _ in range_it:
        run(command)

    return perf.perf_counter() - t0


def prepare_cmd(runner, cmd):
    if runner.args.no_site:
        cmd.append("--no-site")


if __name__ == "__main__":
    runner = perf.text_runner.TextRunner(name='startup', samples=10)
    runner.argparser.add_argument("--no-site", action="store_true")
    runner.prepare_subprocess_args = prepare_cmd

    runner.metadata['description'] = "Performance of the Python startup"
    args = runner.parse_args()
    if args.no_site:
        runner.name += "/no_site"

    command = [sys.executable]
    if args.no_site:
        command.append("-S")
    command.extend(("-c", "pass"))

    runner.bench_sample_func(bench_startup, command)
