import os
import os.path
import shutil
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
        ec, stdout, _ = cls.run_python(
            os.path.join(tests.DATA_DIR, 'find-pyperformance.py'),
            capture='stdout',
            onfail='raise',
            verbose=False,
        )
        assert ec == 0, ec
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
        ec, _, _ = cls.run_pip('install', '--editable', reporoot)
        assert ec == 0, ec

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
                          verbose=True,
                          ):
        ec, stdout, stderr = self.run_module(
            'pyperformance', cmd, *args,
            capture=capture,
            onfail=None,
            verbose=verbose,
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
    # venv

    def test_venv(self):
        # XXX Capture and check the output.
        root = self.resolve_tmp('venv', unique=True)

        def div():
            print()
            print('---')
            print()

        def expect_success(*args):
            text = self.run_pyperformance(
                *args,
                capture=None,
            )

        def expect_failure(*args):
            text = self.run_pyperformance(
                *args,
                capture=None,
                exitcode=1,
            )

        # It doesn't exist yet.
        expect_success('venv', 'show', '--venv', root)
        div()
        # It gets created.
        expect_success('venv', 'create', '--venv', root)
        div()
        expect_success('venv', 'show', '--venv', root)
        div()
        # It alraedy exists.
        expect_failure('venv', 'create', '--venv', root)
        div()
        expect_success('venv', 'show', '--venv', root)
        div()
        # It gets re-created.
        expect_success('venv', 'recreate', '--venv', root)
        div()
        expect_success('venv', 'show', '--venv', root)
        div()
        # It get deleted.
        expect_success('venv', 'remove', '--venv', root)
        div()
        expect_success('venv', 'show', '--venv', root)

    ###################################
    # run

    def test_run_and_show(self):
        filename = self.resolve_tmp('bench.json')

        # -b all: check that *all* benchmark work
        #
        # --debug-single-value: benchmark results don't matter, we only
        # check that running benchmarks don't fail.
        # XXX Capture and check the output.
        text = self.run_pyperformance(
            'run',
            '-b', 'all',
            '--debug-single-value',
            '-o', filename,
            capture=None,
        )

        # Display slowest benchmarks
        # XXX Capture and check the output.
        self.run_module('pyperf', 'slowest', filename)

    def test_run_test_benchmarks(self):
        # Run the benchmarks that exist only for testing
        # in pyperformance/tests/data
        filename = self.resolve_tmp('bench-test.json')

        self.run_pyperformance(
            'run',
            '--manifest', os.path.join(tests.DATA_DIR, 'MANIFEST'),
            '-b', 'all',
            '-o', filename,
            capture=None,
        )

    ###################################
    # compile

    def ensure_cpython_repo(self, reporoot=None):
        if not reporoot:
            reporoot = os.environ.get('PYPERFORMANCE_TESTS_CPYTHON')
            if not reporoot:
                reporoot = os.path.join(tests.DATA_DIR, 'cpython')
        for markerfile in [
            os.path.join(reporoot, '.git'),
            os.path.join(reporoot, 'Python/ceval.c'),
        ]:
            if not os.path.exists(markerfile):
                break
        else:
            return reporoot
        # Clone the repo.
        print('#'*40)
        print('# cloning the cpython repo')
        print('#'*40)
        print()
        tests.run_cmd(
            shutil.which('git'),
            'clone',
            'https://github.com/python/cpython',
            reporoot,
        )
        print('#'*40)
        print('# DONE: cloning the cpython repo')
        print('#'*40)
        print()
        return reporoot

    def create_compile_config(self, *revisions,
                              outdir=None,
                              fast=True,
                              upload=None,
                              ):
        if not outdir:
            outdir = self.resolve_tmp('compile-cmd-outdir', unique=True)
        cpython = self.ensure_cpython_repo()
        text = textwrap.dedent(f'''
            [config]
            json_dir = {outdir}
            debug = {fast}

            [scm]
            repo_dir = {cpython}
            update = False
            git_remote = remotes/origin

            [compile]
            bench_dir = {outdir}
            lto = {not fast}
            pgo = {not fast}
            install = True

            [run_benchmark]
            system_tune = False
            upload = False

            [upload]
            url = {upload}
            ''')
        if revisions:
            text += ''.join(line + os.linesep for line in [
                '',
                '[compile_all_revisions]',
                *(f'{r} =' for r in revisions),
            ])
        cfgfile = os.path.join(outdir, 'compile.ini')
        print(f'(writing config file to {cfgfile})')
        os.makedirs(outdir, exist_ok=True)
        with open(cfgfile, 'w', encoding='utf-8') as outfile:
            outfile.write(text)
        return cfgfile

    @tests.CPYTHON_ONLY
    @tests.NON_WINDOWS_ONLY
    @tests.SLOW
    def test_compile(self):
        cfgfile = self.create_compile_config()
        revision = 'a58ebcc701dd'  # tag: v3.10.2

        # XXX Capture and check the output.
        self.run_pyperformance(
            'compile', cfgfile, revision,
            capture=None,
        )

    @tests.CPYTHON_ONLY
    @tests.NON_WINDOWS_ONLY
    @tests.SLOW
    def test_compile_all(self):
        rev1 = '2cd268a3a934'  # tag: v3.10.1
        rev2 = 'a58ebcc701dd'  # tag: v3.10.2
        cfgfile = self.create_compile_config(rev1, rev2)

        # XXX Capture and check the output.
        self.run_pyperformance(
            'compile_all', cfgfile,
            capture=None,
        )

    @tests.CPYTHON_ONLY
    @tests.NON_WINDOWS_ONLY
    @unittest.expectedFailure
    def test_upload(self):
        url = '<bogus>'
        cfgfile = self.create_compile_config(upload=url)
        resfile = os.path.join(tests.DATA_DIR, 'py36.json')

        # XXX Capture and check the output.
        self.run_pyperformance(
            'upload', cfgfile, resfile,
            capture=None,
        )

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
            verbose=False,
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
            ERROR: Performance versions are different (1.0.1 != 0.3)
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
