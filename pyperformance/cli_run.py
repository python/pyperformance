import logging
import os.path
import sys

import pyperf

import pyperformance
from pyperformance.benchmarks import (
    load_manifest,
    get_benchmarks,
    get_benchmark_groups,
    select_benchmarks,
)
from pyperformance.compare import display_benchmark_suite
from pyperformance.run import run_benchmarks


def cmd_run(parser, options):
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

    manifest = load_manifest(options.manifest)
    should_run = select_benchmarks(options.benchmarks, manifest)

    cmd_prefix = [executable]
    suite, errors = run_benchmarks(should_run, cmd_prefix, options)

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
    manifest = load_manifest(options.manifest)
    selected = select_benchmarks(options.benchmarks, manifest)

    print("%r benchmarks:" % options.benchmarks)
    for bench in sorted(selected):
        print("- %s" % bench.name)
    print()
    print("Total: %s benchmarks" % len(selected))


def cmd_list_groups(options):
    manifest = load_manifest(options.manifest)
    bench_groups = get_benchmark_groups(manifest)
    all_benchmarks = set(b.name for b in get_benchmarks(manifest))

    for group, names in sorted(bench_groups.items()):
        known = set(names) & all_benchmarks
        if not known:
            # skip empty groups
            continue

        print("%s (%s):" % (group, len(names)))
        for name in sorted(names):
            print("- %s" % name)
        print()
