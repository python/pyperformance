import os
import sys
import subprocess

import perf.text_runner
from performance.venv import get_venv_program
from six.moves import xrange


def run(command):
    subprocess.Popen


def bench_startup(loops, command):
    with open(os.devnull, "rb") as devnull_in:
        with open(os.devnull, "wb") as devnull_out:
            range_it = xrange(loops)
            t0 = perf.perf_counter()

            for _ in range_it:
                proc = subprocess.Popen(command,
                                        stdin=devnull_in,
                                        stdout=devnull_out,
                                        stderr=devnull_out)
                returncode = proc.wait()
                if returncode != 0:
                    print("ERROR: Mercurial command failed!")
                    sys.exit(1)

            return perf.perf_counter() - t0


if __name__ == "__main__":
    runner = perf.text_runner.TextRunner(name='hg_startup', samples=25)

    runner.metadata['description'] = "Performance of the Python startup"
    args = runner.parse_args()

    hg_bin = get_venv_program('hg')

    command = [sys.executable, hg_bin, "help"]
    # FIXME: add mercurial version to metadata

    runner.bench_sample_func(bench_startup, command)
