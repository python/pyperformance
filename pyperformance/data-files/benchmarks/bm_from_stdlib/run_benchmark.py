"""Various benchmarks previously stored inside the Python stdlib.

Ported here by Oleg Iarygin.
"""

import pyperf


def benchmark_pprint(runner):
    """Moved from `python -m pprint`."""
    from pprint import PrettyPrinter
    printable = [("string", (1, 2), [3, 4], {5: 6, 7: 8})] * 100_000
    p = PrettyPrinter()

    runner.bench_func('_safe_repr', p._safe_repr, printable, {}, None, 0)
    runner.bench_func('pformat', p.pformat, printable)


if __name__ == "__main__":
    runner = pyperf.Runner()
    cmd = runner.argparser

    args = runner.parse_args()
    benchmark_pprint(runner)
