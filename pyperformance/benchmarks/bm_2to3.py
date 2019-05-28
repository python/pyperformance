import glob
import os.path
import subprocess
import sys

import pyperf


def bench_2to3(command, devnull_out):
    proc = subprocess.Popen(command,
                            stdout=devnull_out,
                            stderr=devnull_out)
    returncode = proc.wait()
    if returncode != 0:
        print("ERROR: 2to3 command failed!")
        sys.exit(1)


if __name__ == "__main__":
    runner = pyperf.Runner()

    runner.metadata['description'] = "Performance of the Python 2to3 program"
    args = runner.parse_args()

    datadir = os.path.join(os.path.dirname(__file__), 'data', '2to3')
    pyfiles = glob.glob(os.path.join(datadir, '*.py.txt'))

    command = [sys.executable, "-m", "lib2to3", "-f", "all"] + pyfiles
    with open(os.devnull, "wb") as devnull_out:
        runner.bench_func('2to3', bench_2to3, command, devnull_out)
