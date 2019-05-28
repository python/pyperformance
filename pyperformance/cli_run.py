from __future__ import division, with_statement, print_function, absolute_import

import logging
import os.path
import sys

import pyperf

import pyperformance
from pyperformance.benchmarks import (filter_benchmarks, get_benchmarks,
                                      select_benchmarks)
from pyperformance.compare import display_benchmark_suite
from pyperformance.run import run_benchmarks


def filter_benchmarks_python(benchmarks, bench_funcs):
    return filter_benchmarks(benchmarks, bench_funcs, sys.version_info)


def get_benchmarks_to_run(options):
    bench_funcs, bench_groups = get_benchmarks()
    should_run = select_benchmarks(options.benchmarks, bench_groups)
    should_run = filter_benchmarks_python(should_run, bench_funcs)
    return (bench_funcs, bench_groups, should_run)


def cmd_run(parser, options):
    logging.basicConfig(level=logging.INFO)

    print("Python benchmark suite %s" % pyperformance.__version__)
    print()

    if options.output and os.path.exists(options.output):
        print("ERROR: the output file %s already exists!" % options.output)
        sys.exit(1)

    if not os.path.isabs(sys.executable):
        print("ERROR: sys.executable is not an absolute path")
        sys.exit(1)
    bench_funcs, bench_groups, should_run = get_benchmarks_to_run(options)
    cmd_prefix = [sys.executable]
    suite, errors = run_benchmarks(bench_funcs, should_run, cmd_prefix, options)

    if not suite:
        print("ERROR: No benchmark was run")
        sys.exit(1)

    if options.output:
        suite.dump(options.output)
    if options.append:
        pyperf.add_runs(options.append, suite)
    display_benchmark_suite(suite)

    if errors:
        print("%s benchmarks failed:" % len(errors))
        for name in errors:
            print("- %s" % name)
        print()
        sys.exit(1)


def cmd_list(options):
    bench_funcs, bench_groups, all_funcs = get_benchmarks_to_run(options)

    print("%r benchmarks:" % options.benchmarks)
    for func in sorted(all_funcs):
        print("- %s" % func)
    print()
    print("Total: %s benchmarks" % len(all_funcs))


def cmd_list_groups(options):
    bench_funcs, bench_groups = get_benchmarks()

    funcs = set(bench_groups['all'])
    all_funcs = filter_benchmarks_python(set(funcs), bench_funcs)

    for group, funcs in sorted(bench_groups.items()):
        funcs = set(funcs) & all_funcs
        if not funcs:
            # skip empty groups
            continue

        print("%s (%s):" % (group, len(funcs)))
        for func in sorted(funcs):
            print("- %s" % func)
        print()
