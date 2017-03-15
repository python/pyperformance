#!/usr/bin/env python3
""" A Python Benchmark Suite

"""
# Tests may include features in later Python versions, but these
# should then be embedded in try-except clauses in the configuration
# module Setup.py.

from __future__ import print_function

import re
import sys

import perf


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

# Print debug information ?
_debug = 0


# Test baseclass

class Test:

    """ All test must have this class as baseclass. It provides
        the necessary interface to the benchmark machinery.

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

    # Number of inner loops (int)
    inner_loops = None

    # Internal variables

    # Mark this class as implementing a test
    # FIXME: remove this?
    is_a_test = 1

    def __init__(self):
        self.name = self.__class__.__name__

    def run(self, runner):
        name = 'pybench.%s' % self.name

        kw = {}
        if self.inner_loops is not None:
            kw['inner_loops'] = self.inner_loops
        return runner.bench_sample_func(name, self.test, **kw)

    def test(self):
        """ Run the benchmark."""
        return


# Load Setup

# This has to be done after the definition of the Test class, since
# the Setup module will import subclasses using this class.

# FIXME: break this circular dependency
import Setup   # noqa


# Benchmark base class
class Benchmark:

    # Name of the benchmark
    name = ''

    # Benchmark version number as float x.yy
    version = 2.1

    # Produce verbose output ?
    verbose = 0

    def __init__(self, runner, name, verbose=None):

        if verbose is not None:
            self.verbose = verbose

        # Init vars
        self.tests = []

        self.runner = runner

    def load_tests(self, args, setupmod):
        limitnames = args.benchmarks
        if limitnames:
            limitnames = re.compile(limitnames, re.I)
        else:
            limitnames = None

        # Add tests
        for testclass in setupmod.__dict__.values():
            if not hasattr(testclass, 'is_a_test'):
                continue
            name = testclass.__name__
            if name == 'Test':
                continue
            if (limitnames is not None and
                    limitnames.search(name) is None):
                continue
            test = testclass()
            self.tests.append(test)

        # Sort tests by their name
        self.tests.sort(key=lambda test: test.name)

    def list_benchmarks(self, args):
        self.load_tests(args, Setup)
        for test in self.tests:
            print(test.name)
        print()
        print("Total: %s benchmarks" % len(self.tests))

    def run(self):
        for test in self.tests:
            test.run(self.runner)


def add_cmdline_args(cmd, args):
    if args.benchmarks:
        cmd.extend(("--benchmarks", args.benchmarks))
    if args.with_gc:
        cmd.append("--with-gc")
    if args.with_syscheck:
        cmd.append("--with-syscheck")


def main():
    metadata = {'pybench_version': __version__}
    runner = perf.Runner(metadata=metadata,
                         add_cmdline_args=add_cmdline_args)

    cmd = runner.argparser
    cmd.add_argument("-b", "--benchmarks", metavar="REGEX",
                     help='run only tests with names matching REGEX')
    cmd.add_argument('--with-gc', action="store_true",
                     help='enable garbage collection')
    cmd.add_argument('--with-syscheck', action="store_true",
                     help='use default sys check interval')
    cmd.add_argument('--copyright', action="store_true",
                     help='show copyright')
    cmd.add_argument('--list', action="store_true",
                     help='display the list of benchmarks and exit')

    args = runner.parse_args()

    bench = Benchmark(runner, args.output, verbose=runner.args.verbose)

    if args.copyright:
        print(__copyright__.strip())
        print()
        sys.exit()

    if args.list:
        bench.list_benchmarks(args)
        sys.exit()

    # Switch off garbage collection
    if not args.with_gc:
        try:
            import gc
        except ImportError:
            print('* Python version doesn\'t support garbage collection',
                  file=sys.stderr)
        else:
            try:
                gc.disable()
            except NotImplementedError:
                print('* Python version doesn\'t support gc.disable',
                      file=sys.stderr)
            else:
                if args.verbose:
                    print('* disabled garbage collection',
                          file=sys.stderr)

    # "Disable" sys check interval
    if not args.with_syscheck:
        # Too bad the check interval uses an int instead of a long...
        value = 2147483647
        try:
            sys.setcheckinterval(value)
        except (AttributeError, NotImplementedError):
            print('* Python version doesn\'t support sys.setcheckinterval',
                  file=sys.stderr)
        else:
            if args.verbose:
                print('* system check interval set to maximum: %s' % value,
                      file=sys.stderr)

    bench.load_tests(runner.args, Setup)
    try:
        bench.run()
    except KeyboardInterrupt:
        print()
        print('*** KeyboardInterrupt -- Aborting')
        print()
        return


if __name__ == '__main__':
    main()
