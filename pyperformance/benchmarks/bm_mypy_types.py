# This benchmark is adapted from the Pyston python-macrobenchmarks repo,
# licensed under the MIT license.
# source: https://github.com/pyston/python-macrobenchmarks/blob/main/benchmarks/mypy_bench.py
# commit: 0fcc5299e6fefba7eefcacd4aceb112971d48c7b on 21 Oct 2020.
# license: https://github.com/pyston/python-macrobenchmarks/blob/main/LICENSE
# It has been updated and modified for pyperformance.
# The benchmark runs mypy against its own types file multiple times.

import os

import pyperf

from mypy.main import main


def typecheck_targets(targets):
    with open(os.devnull, 'w') as devnull:
        try:
            main(None, devnull, devnull, targets)
        except SystemExit:
            pass


if __name__ == '__main__':
    runner = pyperf.Runner()
    runner.metadata['description'] = ('Mypy benchmark: '
                                      'type-check mypy/types.py')
    target_path = os.path.join(os.path.dirname(__file__), 'data',
                               'bm_mypy_target.py')
    runner.bench_func('mypy_types', typecheck_targets, [target_path])

