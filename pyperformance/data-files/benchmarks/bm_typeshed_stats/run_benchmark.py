"""
Gather stats on typeshed using the typeshed-stats package
"""

import sys
from pathlib import Path

import pyperf


TYPESHED_STATS_DIR = str(Path(__file__).parent / "typeshed_stats")
TYPESHED_DIR = str(Path(__file__).parent / "data" / "typeshed")


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata["description"] = __doc__
    args = runner.parse_args()
    sys.path.append(TYPESHED_STATS_DIR)
    command = [sys.executable, "-m", "typeshed_stats", "--typeshed-dir", TYPESHED_DIR]
    runner.bench_command("typeshed_stats", command)
