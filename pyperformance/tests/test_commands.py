import os
import os.path
import shutil
import subprocess
import sys
import textwrap
import unittest

import pyperformance
from pyperformance import tests


class FullStackTests(tests.Functional, unittest.TestCase):

    maxDiff = 80 * 100

    @classmethod
    def setUpClass(cls):
        # pyperformance must be installed in order to run,
        # so we make sure it is.
        cls.ensure_venv()
        cls.ensure_pyperformance()
        super().setUpClass()

    @classmethod
    def ensure_pyperformance(cls):
        _, stdout, _ = cls.run_python(
            os.path.join(tests.DATA_DIR, 'find-pyperformance.py'),
            capture='stdout',
            onfail='raise',
            verbose=False,
        )
        stdout = stdout.strip()
        if stdout.strip():
            # It is already installed.
            return

        print('#'*40)
        print('# installing pyperformance into the venv')
        print('#'*40)
        print()

        # Install it.
        reporoot = os.path.dirname(pyperformance.PKG_ROOT)
        # XXX Ignore the output (and optionally log it).
        cls.run_pip('install', '--editable', reporoot)

        # Clean up extraneous files.
        egg_info = "pyperformance.egg-info"
        print(f"(tests) Remove directory {egg_info}", flush=True)
        try:
            shutil.rmtree(egg_info)
        except FileNotFoundError:
            pass
        print()

        print('#'*40)
        print('# DONE: installing pyperformance into the venv')
        print('#'*40)
        print()

    def run_pyperformance(self, cmd, *args,
                          exitcode=0,
                          capture='both',
                          ):
        ec, stdout, stderr = self.run_module(
            'pyperformance', cmd, *args,
            capture=capture,
            onfail=None,
            verbose=False,
        )
        if exitcode is True:
            self.assertGreater(ec, 0, repr(stdout))
        else:
            self.assertEqual(ec, exitcode, repr(stdout))
        if stdout:
            stdout = stdout.rstrip()
        return stdout

    ###################################
    # info

    def test_list(self):
        # XXX Capture and check the output.
        self.run_pyperformance('list', capture=None)

    def test_list_groups(self):
        # XXX Capture and check the output.
        self.run_pyperformance('list_groups', capture=None)

    ###################################
    # run

    def test_run_and_show(self):
        json = os.path.join(self._TMPDIR, 'bench.json')

        # -b all: check that *all* benchmark work
        #
        # --debug-single-value: benchmark results don't matter, we only
        # check that running benchmarks don't fail.
        # XXX Capture and check the output.
        self.run_pyperformance(
            'run',
            '-b', 'all',
            '--debug-single-value',
            '-o', json,
            capture=None,
        )

        # Display slowest benchmarks
        # XXX Capture and check the output.
        tests.run_module('pyperf', 'slowest', json)

    ###################################
    # show

    def test_show(self):
        for filename in (
            os.path.join(tests.DATA_DIR, 'py36.json'),
            os.path.join(tests.DATA_DIR, 'mem1.json'),
        ):
            with self.subTest(filename):
                # XXX Capture and check the output.
                self.run_pyperformance('show', filename, capture=None)

    ###################################
    # compare

    def compare(self, *args,
                exitcode=0,
                dataset='py',
                file2='py38.json',
                **kw
                ):
        if dataset == 'mem':
            file1 = 'mem1.json'
            file2 = 'mem2.json'
        else:
            file1 = 'py36.json'
        marker = file1

        stdout = self.run_pyperformance(
            'compare',
            os.path.join(tests.DATA_DIR, file1),
            os.path.join(tests.DATA_DIR, file2),
            *args,
            exitcode=exitcode,
        )
        if marker in stdout:
            stdout = stdout[stdout.index(marker):]
        return stdout + '\n'

    def test_compare(self):
        stdout = self.compare()
        self.assertEqual(stdout, textwrap.dedent('''
            py36.json
            =========

            Performance version: 1.0.1
            Python version: 3.6.10 (64-bit)
            Report on Linux-5.5.9-200.fc31.x86_64-x86_64-with-fedora-31-Thirty_One
            Number of logical CPUs: 8
            Start date: 2020-03-26 15:50:39.816020
            End date: 2020-03-26 15:50:56.406559

            py38.json
            =========

            Performance version: 1.0.1
            Python version: 3.8.2 (64-bit)
            Report on Linux-5.5.9-200.fc31.x86_64-x86_64-with-glibc2.2.5
            Number of logical CPUs: 8
            Start date: 2020-03-26 15:54:12.331569
            End date: 2020-03-26 15:54:23.900355

            ### telco ###
            Mean +- std dev: 10.7 ms +- 0.5 ms -> 7.2 ms +- 0.3 ms: 1.49x faster
            Significant (t=44.97)
        ''').lstrip())

    def test_compare_wrong_version(self):
        stdout = self.compare(file2='py3_performance03.json', exitcode=1)
        self.assertEqual(stdout, textwrap.dedent('''
            py36.json
            =========

            Performance version: 1.0.1
            Python version: 3.6.10 (64-bit)
            Report on Linux-5.5.9-200.fc31.x86_64-x86_64-with-fedora-31-Thirty_One
            Number of logical CPUs: 8
            Start date: 2020-03-26 15:50:39.816020
            End date: 2020-03-26 15:50:56.406559

            py3_performance03.json
            ======================

            Performance version: 0.3


            Skipped 1 benchmarks only in py36.json: telco

            Skipped 1 benchmarks only in py3_performance03.json: call_simple

            ERROR: Performance versions are different: 1.0.1 != 0.3
            ''').lstrip())

    def test_compare_single_value(self):
        stdout = self.compare(dataset='mem')
        self.assertEqual(stdout, textwrap.dedent('''
            mem1.json
            =========

            Performance version: 0.2

            mem2.json
            =========

            Performance version: 0.2

            ### call_simple ###
            7896.0 kB -> 7900.0 kB: 1.00x larger
        ''').lstrip())

    def test_compare_csv(self):
        expected = textwrap.dedent('''
            Benchmark,Base,Changed
            telco,0.01073,0.00722
            ''').lstrip()
        filename = self.resolve_tmp('outfile.csv', unique=True)
        with tests.CleanupFile(filename):
            self.compare("--csv", filename)
            with open(filename, "r", encoding="utf-8") as infile:
                csv = infile.read()

        self.assertEqual(csv, expected)

    def test_compare_table(self):
        stdout = self.compare("-O", "table")
        self.assertEqual(stdout, textwrap.dedent('''
            py36.json
            =========

            Performance version: 1.0.1
            Python version: 3.6.10 (64-bit)
            Report on Linux-5.5.9-200.fc31.x86_64-x86_64-with-fedora-31-Thirty_One
            Number of logical CPUs: 8
            Start date: 2020-03-26 15:50:39.816020
            End date: 2020-03-26 15:50:56.406559

            py38.json
            =========

            Performance version: 1.0.1
            Python version: 3.8.2 (64-bit)
            Report on Linux-5.5.9-200.fc31.x86_64-x86_64-with-glibc2.2.5
            Number of logical CPUs: 8
            Start date: 2020-03-26 15:54:12.331569
            End date: 2020-03-26 15:54:23.900355

            +-----------+-----------+-----------+--------------+-----------------------+
            | Benchmark | py36.json | py38.json | Change       | Significance          |
            +===========+===========+===========+==============+=======================+
            | telco     | 10.7 ms   | 7.22 ms   | 1.49x faster | Significant (t=44.97) |
            +-----------+-----------+-----------+--------------+-----------------------+
        ''').lstrip())

    def test_compare_table_single_value(self):
        stdout = self.compare("-O", "table", dataset='mem')
        self.assertEqual(stdout, textwrap.dedent('''
            mem1.json
            =========

            Performance version: 0.2

            mem2.json
            =========

            Performance version: 0.2

            +-------------+-----------+-----------+--------------+------------------------------------------+
            | Benchmark   | mem1.json | mem2.json | Change       | Significance                             |
            +=============+===========+===========+==============+==========================================+
            | call_simple | 7896.0 kB | 7900.0 kB | 1.00x larger | (benchmark only contains a single value) |
            +-------------+-----------+-----------+--------------+------------------------------------------+
        ''').lstrip())


if __name__ == "__main__":
    unittest.main()
