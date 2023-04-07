"""
A dummy benchmark that uses a local wheel
"""

import pyperf


def bench():
    return 1.0


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "A dummy benchmark that has a local wheel dependency"

    args = runner.parse_args()
    runner.bench_func('local_wheel', bench)

