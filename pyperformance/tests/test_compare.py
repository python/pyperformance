#!/usr/bin/env python3
import io
import os.path
import subprocess
import sys
import textwrap
import unittest

from pyperformance import tests


DATA_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), 'data'))


def run_cmd(cmd):
    print("Execute: %s" % ' '.join(cmd))
    proc = subprocess.Popen(cmd)
    try:
        proc.wait()
    except:   # noqa
        proc.kill()
        proc.wait()
        raise

    exitcode = proc.returncode
    if exitcode:
        sys.exit(exitcode)


class CompareTests(unittest.TestCase):
    maxDiff = 80 * 100

    @classmethod
    def setUpClass(cls):
        cmd = [sys.executable, '-m', 'pyperformance', 'venv', 'create']
        run_cmd(cmd)

    def compare(self, *args, **kw):
        dataset = kw.get('dataset', 'py')
        exitcode = kw.get('exitcode', 0)

        if dataset == 'mem':
            file1 = 'mem1.json'
            file2 = 'mem2.json'
        else:
            file1 = 'py36.json'
            file2 = kw.get('file2', 'py38.json')

        cmd = [sys.executable, '-m', 'pyperformance', 'compare',
               os.path.join(DATA_DIR, file1),
               os.path.join(DATA_DIR, file2)]
        cmd.extend(args)
        proc = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                universal_newlines=True)
        stdout = proc.communicate()[0]
        self.assertEqual(proc.returncode, exitcode, repr(stdout))
        return stdout.rstrip() + "\n"

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

    def test_csv(self):
        with tests.temporary_file() as tmp:
            self.compare("--csv", tmp)

            with io.open(tmp, "r") as fp:
                csv = fp.read()

            self.assertEqual(csv,
                             "Benchmark,Base,Changed\n"
                             "telco,0.01073,0.00722\n")

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
