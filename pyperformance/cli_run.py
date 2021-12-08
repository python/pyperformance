import logging
import os.path
import sys

import pyperf

import pyperformance
from pyperformance.compare import display_benchmark_suite
from pyperformance.run import run_benchmarks


def cmd_run(options, benchmarks):
    logging.basicConfig(level=logging.INFO)

    print("Python benchmark suite %s" % pyperformance.__version__)
    print()

    if options.output and os.path.exists(options.output):
        print("ERROR: the output file %s already exists!" % options.output)
        sys.exit(1)

    if hasattr(options, 'python'):
        executable = options.python
    else:
        executable = sys.executable
    if not os.path.isabs(executable):
        print("ERROR: \"%s\" is not an absolute path" % executable)
        sys.exit(1)

    suite, errors = run_benchmarks(benchmarks, executable, options)

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


def cmd_list(options, benchmarks):
    print("%r benchmarks:" % options.benchmarks)
    for bench in sorted(benchmarks):
        print("- %s" % bench.name)
    print()
    print("Total: %s benchmarks" % len(benchmarks))


def cmd_list_groups(manifest):
    all_benchmarks = set(manifest.benchmarks)

    groups = sorted(manifest.groups - {'all', 'default'})
    groups[0:0] = ['all', 'default']
    for group in groups:
        specs = list(manifest.resolve_group(group))
        known = set(specs) & all_benchmarks
        if not known:
            # skip empty groups
            continue

        print("%s (%s):" % (group, len(specs)))
        for spec in sorted(specs):
            print("- %s" % spec.name)
        print()
