from __future__ import division, with_statement, print_function, absolute_import

import logging
import os.path
import sys

import perf

import performance
from performance.benchmarks import filter_benchmarks
from performance.compare import display_benchmark_suite
from performance.run import select_benchmarks, run_benchmarks
from performance.venv import interpreter_version


def filter_benchmarks_python(benchmarks, bench_funcs, python):
    basever = interpreter_version(python)
    return filter_benchmarks(benchmarks, bench_funcs, basever)


def cmd_run(parser, options, bench_funcs, bench_groups):
    logging.basicConfig(level=logging.INFO)

    print("Python benchmark suite %s" % performance.__version__)
    print()

    if options.output and os.path.exists(options.output):
        print("ERROR: the output file %s already exists!" % options.output)
        sys.exit(1)

    if not os.path.isabs(sys.executable):
        print("ERROR: sys.executable is not an absolute path")
        sys.exit(1)
    cmd_prefix = [sys.executable]

    should_run = select_benchmarks(options.benchmarks, bench_groups)
    should_run = filter_benchmarks_python(should_run, bench_funcs, cmd_prefix)
    suite = run_benchmarks(bench_funcs, should_run, cmd_prefix, options)

    if not suite:
        print("ERROR: No benchmark was run")
        sys.exit(1)

    if options.output:
        suite.dump(options.output)
    if options.append:
        perf.add_runs(options.append, suite)
    display_benchmark_suite(suite)


def cmd_list(options, bench_funcs, bench_groups):
    funcs = bench_groups['all']
    python = [sys.executable]
    all_funcs = filter_benchmarks_python(set(funcs), bench_funcs, python)

    if options.action == 'list':
        print("%s benchmarks:" % len(all_funcs))
        for func in sorted(all_funcs):
            print("- %s" % func)
    else:
        # list_groups
        for group, funcs in sorted(bench_groups.items()):
            funcs = set(funcs) & all_funcs
            if not funcs:
                # skip empty groups
                continue

            print("%s (%s):" % (group, len(funcs)))
            for func in sorted(funcs):
                print("- %s" % func)
            print()
