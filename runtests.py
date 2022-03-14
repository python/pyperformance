#!/usr/bin/env python3
import os.path
import subprocess
import sys


def main():
    subprocess.run(
        [sys.executable, '-u', '-m', 'pyperformance.tests'],
        cwd=os.path.dirname(__file__) or None,
    )


if __name__ == "__main__":
    main()
