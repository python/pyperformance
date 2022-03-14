import os.path
import unittest

from pyperformance import tests


class FunctionalTests(tests.Functional, unittest.TestCase):

    def test_run_and_show(self):
        json = os.path.join(self._TMPDIR, 'bench.json')

        # -b all: check that *all* benchmark work
        #
        # --debug-single-value: benchmark results don't matter, we only
        # check that running benchmarks don't fail.
        self.run_pyperformance('run', '-b', 'all',
                 '--debug-single-value',
                 '-o', json)

        # Display slowest benchmarks
        tests.run_cmd(
            self.venv_python, '-u',
            '-m', 'pyperf',
            'slowest',
            json,
        )


if __name__ == "__main__":
    unittest.main()
