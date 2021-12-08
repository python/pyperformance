#!/usr/bin/env python3
import os.path
import shutil
import subprocess
import sys
import tempfile


def run_cmd(cmd):
    print("(runtests.py) Execute: %s" % ' '.join(cmd), flush=True)
    proc = subprocess.Popen(cmd)
    try:
        proc.wait()
    except:   # noqa
        proc.kill()
        proc.wait()
        raise
    sys.stdout.flush()
    exitcode = proc.returncode
    if exitcode:
        sys.exit(exitcode)
    print("", flush=True)


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

    run_bench(python, '-u', script, 'venv', 'create', '-b', 'all')

    egg_info = "pyperformance.egg-info"
    print("(runtests.py) Remove directory %s" % egg_info, flush=True)
    try:
        shutil.rmtree(egg_info)
    except FileNotFoundError:
        pass

    run_bench(python, '-u', script, 'venv', 'create')

    for filename in (
        os.path.join('pyperformance', 'tests', 'data', 'py36.json'),
        os.path.join('pyperformance', 'tests', 'data', 'mem1.json'),
    ):
        run_cmd((python, script, 'show', filename))

    run_bench(python, '-u', script, 'list')
    run_bench(python, '-u', script, 'list_groups')

    json = os.path.join(venv, 'bench.json')

    # -b all: check that *all* benchmark work
    #
    # --debug-single-value: benchmark results don't matter, we only
    # check that running benchmarks don't fail.
    run_bench(python, '-u', script, 'run', '-b', 'all', '--debug-single-value',
              '-o', json)

    # Display slowest benchmarks
    run_cmd((venv_python, '-u', '-m', 'pyperf', 'slowest', json))

    run_bench(python, '-u', script, 'venv', 'remove')


def main():
    # Unit tests
    cmd = [sys.executable, '-u',
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
