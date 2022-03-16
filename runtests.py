#!/usr/bin/env python3
import os.path
import subprocess
import sys

from dev import ensure_venv_ready


def main():
    python = ensure_venv_ready(kind='tests')
    if python != sys.executable:
        # Now re-run using the venv.
        os.execv(python, [python, *sys.argv])
        # <unreachable>

    # Now run the tests.
    subprocess.run(
        [sys.executable, '-u', '-m', 'pyperformance.tests'],
        cwd=os.path.dirname(__file__) or None,
    )


if __name__ == "__main__":
    main()
