"""Test the performance of pprint.PrettyPrinter.

This benchmark was available as `python -m pprint` until Python 3.12.

Authors: Fred Drake (original), Oleg Iarygin (pyperformance port).
"""

from pprint import PrettyPrinter
import pyperf


def benchmark_pprint(runner):
    printable = [("string", (1, 2), [3, 4], {5: 6, 7: 8})] * 100_000
    p = PrettyPrinter()

    # Support CPython before 3.10 and non-CPython implementations
    if hasattr(p, '_safe_repr'):
        runner.bench_func('_safe_repr', p._safe_repr, printable, {}, None, 0)
    runner.bench_func('pformat', p.pformat, printable)


if __name__ == "__main__":
    runner = pyperf.Runner()

    args = runner.parse_args()
    benchmark_pprint(runner)
