#!/usr/bin/env python3
from __future__ import division, with_statement, print_function, absolute_import

import os.path
import shutil
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


def main():
    # Move to the root directly
    root = os.path.dirname(__file__)
    if root:
        os.chdir(root)

    python = sys.executable
    script = 'pyperformance'

    if os.path.exists('venv'):
        print("Remove venv directory")
        print()
        shutil.rmtree('venv')

    # The first command creates the virtual environment
    run_bench(python, script, 'list')

    run_bench(python, script, 'list_groups')

    # -b all: check that *all* benchmark work
    #
    # --debug-single-sample: benchmark results don't matter, we only
    # check that running benchmarks don't fail.
    run_bench(python, script, 'run', '-b', 'all', '--debug-single-sample')


if __name__ == "__main__":
    main()
