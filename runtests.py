#!/usr/bin/env python3
from __future__ import division, with_statement, print_function, absolute_import

import os.path
import shutil
import subprocess
import sys
import tempfile

def run_cmd(cmd):
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


def _main(venv):
    # Move to the root directly
    root = os.path.dirname(__file__)
    if root:
        os.chdir(root)

    python = sys.executable
    script = 'pyperformance'

    def run_bench(*cmd):
        cmd = cmd + ('--venv', venv)
        run_cmd(cmd)

    run_bench(python, script, 'venv', 'create')
    run_bench(python, script, 'venv')
    run_bench(python, script, 'list')
    run_bench(python, script, 'list_groups')

    # -b all: check that *all* benchmark work
    #
    # --debug-single-sample: benchmark results don't matter, we only
    # check that running benchmarks don't fail.
    run_bench(python, script, 'run', '-b', 'all', '--debug-single-sample')

    run_bench(python, script, 'venv', 'remove')


def main():
    tmpdir = tempfile.mkdtemp()
    try:
        venv = os.path.join(tmpdir, 'perf_test_venv')
        _main(venv)
    finally:
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)


if __name__ == "__main__":
    main()
