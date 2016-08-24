#!/usr/bin/env python3
import subprocess
import sys

def run_bench(*cmd):
    print("Execute: %s" % ' '.join(cmd))
    proc = subprocess.Popen(cmd)
    try:
        proc.wait()
    except:
        proc.kill()
        proc.wait()
        raise
    exitcode = proc.returncode
    if exitcode:
        sys.exit(exitcode)
    print("")


def runtests():
    python = sys.executable
    bench = 'bench.py'

    # The first command creates the virtual environment
    run_bench(python, bench, 'list')

    run_bench(python, bench, 'list_groups')

    # -b all: check that *all* benchmark work
    #
    # --debug-single-sample: benchmark results don't matter, we only
    # check that running benchmarks don't fail.
    run_bench(python, bench, 'run', '-b', 'all', '--debug-single-sample')


def main():
    runtests()


if __name__ == "__main__":
    main()
