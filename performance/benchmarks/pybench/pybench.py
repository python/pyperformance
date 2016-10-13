#!/usr/bin/env python3

""" A Python Benchmark Suite

"""
# Tests may include features in later Python versions, but these
# should then be embedded in try-except clauses in the configuration
# module Setup.py.
#

from __future__ import print_function

import re
import sys
import time
import platform

import perf

from CommandLine import Application


# pybench Copyright
__copyright__ = """\
Copyright (c), 1997-2006, Marc-Andre Lemburg (mal@lemburg.com)
Copyright (c), 2000-2006, eGenix.com Software GmbH (info@egenix.com)

                   All Rights Reserved.

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee or royalty is hereby
granted, provided that the above copyright notice appear in all copies
and that both that copyright notice and this permission notice appear
in supporting documentation or portions thereof, including
modifications, that you make.

THE AUTHOR MARC-ANDRE LEMBURG DISCLAIMS ALL WARRANTIES WITH REGARD TO
THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
WITH THE USE OR PERFORMANCE OF THIS SOFTWARE !
"""

# Version number; version history: see README file !
__version__ = '2.1'

# Constants

# Second fractions
MILLI_SECONDS = 1e3
MICRO_SECONDS = 1e6
NANO_SECONDS = 1e9

# Percent unit
PERCENT = 100

# Horizontal line length
LINE = 79

# Minimum test run-time
MIN_TEST_RUNTIME = 1e-3

# Number of calibration loops to run for each calibration run
CALIBRATION_LOOPS = 20

# Allow skipping calibration ?
ALLOW_SKIPPING_CALIBRATION = 1

# Print debug information ?
_debug = 0

# Helpers


def get_machine_details():

    if _debug:
        print('Getting machine details...')
    buildno, builddate = platform.python_build()
    python = platform.python_version()
    # XXX this is now always UCS4, maybe replace it with 'PEP393' in 3.3+?
    if sys.maxunicode == 65535:
        # UCS2 build (standard)
        unitype = 'UCS2'
    else:
        # UCS4 build (most recent Linux distros)
        unitype = 'UCS4'
    bits, linkage = platform.architecture()
    return {
        'platform': platform.platform(),
        'processor': platform.processor(),
        'executable': sys.executable,
        'implementation': getattr(platform, 'python_implementation',
                                  lambda: 'n/a')(),
        'python': python,
        'compiler': platform.python_compiler(),
        'buildno': buildno,
        'builddate': builddate,
        'unicode': unitype,
        'bits': bits,
    }


# FIXME: use perf metadata?
def print_machine_details(d, indent=''):

    l = ['Machine Details:',
         '   Platform ID:    %s' % d.get('platform', 'n/a'),
         '   Processor:      %s' % d.get('processor', 'n/a'),
         '',
         'Python:',
         '   Implementation: %s' % d.get('implementation', 'n/a'),
         '   Executable:     %s' % d.get('executable', 'n/a'),
         '   Version:        %s' % d.get('python', 'n/a'),
         '   Compiler:       %s' % d.get('compiler', 'n/a'),
         '   Bits:           %s' % d.get('bits', 'n/a'),
         '   Build:          %s (#%s)' % (d.get('builddate', 'n/a'),
                                          d.get('buildno', 'n/a')),
         '   Unicode:        %s' % d.get('unicode', 'n/a'),
         ]
    joiner = '\n' + indent
    print(indent + joiner.join(l) + '\n')

# Test baseclass


class Test:

    """ All test must have this class as baseclass. It provides
        the necessary interface to the benchmark machinery.

        The tests must set .rounds to a value high enough to let the
        test run between 20-50 seconds. This is needed because
        clock()-timing only gives rather inaccurate values (on Linux,
        for example, it is accurate to a few hundreths of a
        second).

        It is also important to set the .operations variable to a
        value representing the number of "virtual operations" done per
        call of .run().

        If you change a test in some way, don't forget to increase
        its version number.

    """

    # Instance variables that each test should override

    # Version number of the test as float (x.yy); this is important
    # for comparisons of benchmark runs - tests with unequal version
    # number will not get compared.
    version = 2.1

    # The number of abstract operations done in each round of the
    # test. An operation is the basic unit of what you want to
    # measure. The benchmark will output the amount of run-time per
    # operation. Note that in order to raise the measured timings
    # significantly above noise level, it is often required to repeat
    # sets of operations more than once per test round. The measured
    # overhead per test round should be less than 1 second.
    operations = 1

    # Number of inner loops
    inner_loops = 1

    # Internal variables

    # Mark this class as implementing a test
    is_a_test = 1

    # List of test run timings
    times = []

    def __init__(self, runner):
        self.runner = runner
        self.bench = perf.Benchmark()
        self.loops = self.runner.args.loops
        self._calibrate_warmups = None

    def calibrate_test(self, runner):
        if self.loops:
            return
        # FIXME: don't use private methods of the perf modume!
        self.loops, self._calibrate_warmups = runner._calibrate(
            self.bench, self.test)

    def run(self, runner, rounds):
        """ Run the test in two phases: first calibrate, then
            do the actual test. Be careful to keep the calibration
            timing low w/r to the test timing.

        """
        name = 'pybench.%s' % self.__class__.__name__
        loops = self.loops
        total_loops = loops * self.inner_loops

        warmups = []
        if self._calibrate_warmups:
            warmups.extend(self._calibrate_warmups)
        samples = []
        for i in range(rounds):
            dt = self.test(loops)
            dt /= total_loops
            if i < runner.args.warmups:
                warmups.append((loops, dt))
            else:
                samples.append(dt)

        metadata = {'name': name,
                    'pybench_version': __version__,
                    'loops': loops}
        if self.inner_loops != 1:
            metadata['inner_loops'] = self.inner_loops
        run = perf.Run(samples, warmups=warmups, metadata=metadata)
        self.bench.add_run(run)

    def test(self):
        """ Run the test.

            The test needs to run self.rounds executing
            self.operations number of operations each.

        """
        return


# Load Setup

# This has to be done after the definition of the Test class, since
# the Setup module will import subclasses using this class.

import Setup   # noqa

# Benchmark base class


class Benchmark:

    # Name of the benchmark
    name = ''

    # Number of benchmark rounds to run
    rounds = 1

    # Benchmark version number as float x.yy
    version = 2.1

    # Produce verbose output ?
    verbose = 0

    # Dictionary with the machine details
    machine_details = None

    def __init__(self, runner, name, verbose=None):

        self.name = '%04i-%02i-%02i %02i:%02i:%02i' % \
                    (time.localtime(time.time())[:6])
        if verbose is not None:
            self.verbose = verbose

        # Init vars
        self.tests = {}
        if _debug:
            print('Getting machine details...')
        self.machine_details = get_machine_details()

        self.suite = perf.BenchmarkSuite()
        self.runner = runner

    def load_tests(self, args, setupmod):
        limitnames = args.benchmarks
        if limitnames:
            if _debug:
                print('* limiting test names to one with substring "%s"' %
                      limitnames)
            limitnames = re.compile(limitnames, re.I)
        else:
            limitnames = None

        # Add tests
        if self.verbose:
            print('Searching for tests ...')
            print('--------------------------------------')
        for testclass in setupmod.__dict__.values():
            if not hasattr(testclass, 'is_a_test'):
                continue
            name = testclass.__name__
            if name == 'Test':
                continue
            if (limitnames is not None and
                    limitnames.search(name) is None):
                continue
            test = testclass(self.runner)
            self.tests[name] = test
            self.suite.add_benchmark(test.bench)
        l = sorted(self.tests)
        if self.verbose:
            for name in l:
                print('  %s' % name)
            print('--------------------------------------')
            print('  %i tests found' % len(l))
            print()

    def list_benchmarks(self, args):
        self.load_tests(args, Setup)
        tests = sorted(self.tests.items())
        for name, test in tests:
            print(name)
        print()
        print("Total: %s benchmarks" % len(tests))

    def calibrate(self):
        print('Calibrating tests. Please wait...', end=' ')
        sys.stdout.flush()
        if self.verbose:
            print()
            print()
            print('Test                             loops')
            print('-' * LINE)
        tests = sorted(self.tests.items())
        for name, test in tests:
            test.calibrate_test(self.runner)
            if self.verbose:
                # FIXME: remove overhead
                print('%30s:  %s' % (name, test.loops))
        if self.verbose:
            print()
            print('Done with the calibration.')
        else:
            print('done.')
        print()

    def run(self):
        tests = sorted(self.tests.items())
        print('Running %i round(s) of the suite:' % self.rounds)
        print()
        for j in range(len(tests)):
            name, test = tests[j]
            test.run(self.runner, self.rounds)
            print('%30s: %s' % (name, test.bench))
        print()

    def print_header(self, title='Benchmark'):

        print('-' * LINE)
        print('%s: %s' % (title, self.name))
        print('-' * LINE)
        print()
        print('    Rounds: %s' % self.rounds)
        print()
        if self.machine_details:
            print_machine_details(self.machine_details, indent='    ')
            print()

    def print_benchmark(self, limitnames=None):

        print('Test                          '
              '   median')
        print('-' * LINE)
        total_avg_time = 0.0

        for bench in self.suite.get_benchmarks():
            median = bench.median()
            total_avg_time += median
            print('%30s:  %5.0f ns' %
                  (bench.get_name(), median * NANO_SECONDS,))
        print('-' * LINE)
        print('Totals:                        '
              ' %6.1f us' %
              (total_avg_time * MICRO_SECONDS,))
        print()


def prepare_subprocess_args(runner, cmd):
    args = runner.args
    cmd.extend(('--min-time', str(args.min_time)))
    if args.benchmarks:
        cmd.extend(("--benchmarks", args.benchmarks))
    if args.with_gc:
        cmd.append("--with-gc")
    if args.with_syscheck:
        cmd.append("--with-syscheck")


class MyTextRunner(perf.Runner):
    # FIXME: don't override private methods

    def _main(self):
        start_time = perf.monotonic_clock()

        self.parse_args()

        self._cpu_affinity()

        suite = perf.BenchmarkSuite()
        try:
            self._spawn_workers(suite, start_time)
        except KeyboardInterrupt:
            print("Interrupted: exit", file=sys.stderr)
            sys.exit(1)

        return suite

    def _spawn_workers(self, suite, start_time):
        quiet = self.args.quiet
        stream = self._stream()
        nprocess = self.args.processes

        for process in range(1, nprocess + 1):
            start = perf.monotonic_clock()
            run_suite = self._spawn_worker_suite()
            dt = perf.monotonic_clock() - start

            for run_bench in run_suite.get_benchmarks():
                suite._add_benchmark_runs(run_bench)
                # print("Process %s: %s: %s" % (process, run_bench.get_name(), run_bench))

            if not quiet:
                print('* Round %s/%s done in %.1f seconds.'
                      % (process, nprocess, dt))

        if not quiet:
            print(file=stream)


class PyBenchCmdline(Application):

    header = ("PYBENCH - a benchmark test suite for Python "
              "interpreters/compilers.")

    version = __version__

    copyright = __copyright__

    def main(self):
        runner = MyTextRunner(name='pybench')

        # FIXME: add about to argparser help
#         about = """\
# The normal operation is to run the suite and display the
# results. Use -f to save them for later reuse or comparisons.
#
# Examples:
#
# python2.1 pybench.py -f p21.json
# python2.5 pybench.py -f p25.json
# python pybench.py -s p25.json -c p21.json
# """

        parser = runner.argparser
        parser.add_argument(
            "-b", "--benchmarks", metavar="REGEX",
            help='run only tests with names matching REGEX')
        parser.add_argument('--with-gc', action="store_true",
                            help='enable garbage collection')
        parser.add_argument('--with-syscheck', action="store_true",
                            help='use default sys check interval')
        parser.add_argument('--copyright', action="store_true",
                            help='show copyright')
        parser.add_argument('--list', action="store_true",
                            help='display the list of benchmarks and exit')
        runner.prepare_subprocess_args = prepare_subprocess_args

        args = runner.parse_args()
        self.verbose = args.verbose

        orig_stdout = sys.stdout
        if args.stdout:
            # if --stdout is used: redirect all messages to stderr
            sys.stdout = sys.stderr

        # Create benchmark object
        bench = Benchmark(runner, args.output, verbose=runner.args.verbose)
        bench.rounds = runner.args.warmups + runner.args.samples

        if args.copyright:
            self.handle__copyright(None)
            sys.exit()

        if args.list:
            bench.list_benchmarks(args)
            sys.exit()

        if not runner.args.worker:
            bench.print_header()

            bench_suite = runner._main()
            bench.suite = bench_suite

            # Ring bell
            sys.stderr.write('\007')
        else:
            # FIXME: use TextRunner._main(), don't hardcode methods
            runner._cpu_affinity()

            bench_suite = self.worker(bench, runner)

        bench.print_benchmark()

        if args.output:
            bench_suite.dump(args.output)

        if args.append:
            perf.add_runs(args.append, bench_suite)

        if args.stdout:
            bench_suite.dump(orig_stdout)

    def worker(self, bench, runner):
        print('-' * LINE)
        print('PYBENCH %s' % __version__)
        print('-' * LINE)
        print('* using %s %s' % (
            getattr(platform, 'python_implementation', lambda: 'Python')(),
            ' '.join(sys.version.split())))

        # Switch off garbage collection
        if not runner.args.with_gc:
            try:
                import gc
            except ImportError:
                print('* Python version doesn\'t support garbage collection')
            else:
                try:
                    gc.disable()
                except NotImplementedError:
                    print('* Python version doesn\'t support gc.disable')
                else:
                    print('* disabled garbage collection')

        # "Disable" sys check interval
        if not runner.args.with_syscheck:
            # Too bad the check interval uses an int instead of a long...
            value = 2147483647
            try:
                sys.setcheckinterval(value)
            except (AttributeError, NotImplementedError):
                print('* Python version doesn\'t support sys.setcheckinterval')
            else:
                print('* system check interval set to maximum: %s' % value)

        print()

        if runner.args.output:
            print('Creating benchmark: %s (rounds=%i)' %
                  (runner.args.output, bench.rounds))
            print()

        bench.load_tests(runner.args, Setup)
        try:
            bench.calibrate()
            bench.run()
        except KeyboardInterrupt:
            print()
            print('*** KeyboardInterrupt -- Aborting')
            print()
            return
        return bench.suite


if __name__ == '__main__':
    PyBenchCmdline()
