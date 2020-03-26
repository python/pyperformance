#!/usr/bin/env python3
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
    except:   # noqa
        proc.kill()
        proc.wait()
        raise
    exitcode = proc.returncode
    if exitcode:
        sys.exit(exitcode)
    print("")


def run_tests(venv):
    # Move to the root directly
    root = os.path.dirname(__file__)
    if root:
        os.chdir(root)

    python = sys.executable
    script = 'pyperformance'
    if os.name == "nt":
        python_executable = os.path.basename(python)
        venv_python = os.path.join(venv, 'Scripts', python_executable)
    else:
        venv_python = os.path.join(venv, 'bin', 'python')

    def run_bench(*cmd):
        cmd = cmd + ('--venv', venv)
        run_cmd(cmd)

    run_bench(python, script, 'venv', 'create')

    egg_info = "pyperformance.egg-info"
    print("Remove directory %s" % egg_info)
    try:
        shutil.rmtree(egg_info)
    except FileNotFoundError:
        pass

    run_bench(python, script, 'venv')

    for filename in (
        os.path.join('pyperformance', 'tests', 'data', 'py36.json'),
        os.path.join('pyperformance', 'tests', 'data', 'mem1.json'),
    ):
        run_cmd((python, script, 'show', filename))

    run_bench(python, script, 'list')
    run_bench(python, script, 'list_groups')

    json = os.path.join(venv, 'bench.json')

    # -b all: check that *all* benchmark work
    #
    # --debug-single-value: benchmark results don't matter, we only
    # check that running benchmarks don't fail.
    run_bench(python, script, 'run', '-b', 'all', '--debug-single-value',
              '-o', json)

    # Display slowest benchmarks
    run_cmd((venv_python, '-m', 'pyperf', 'slowest', json))

    run_bench(python, script, 'venv', 'remove')


def main():
    # Unit tests
    cmd = [sys.executable,
           os.path.join('pyperformance', 'tests', 'test_compare.py')]
    run_cmd(cmd)

    # Functional tests
    tmpdir = tempfile.mkdtemp()
    try:
        run_tests(tmpdir)
    finally:
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)


if __name__ == "__main__":
    main()
