import logging
import os.path
import sys

import pyperf

import pyperformance
from pyperformance.benchmarks import (
    load_manifest,
    iter_selections,
)
from pyperformance.compare import display_benchmark_suite
from pyperformance.run import run_benchmarks


def _select_benchmarks(selections, manifest):
    groups = manifest.groups
    for op, _, kind, parsed in selections:
        if callable(parsed):
            continue
        name = parsed.name if kind == 'benchmark' else parsed
        if name in manifest.groups and op == '-':
            raise ValueError(f'negative groups not supported: -{parsed.name}')

    selected = []
    for bench in iter_selections(manifest, selections):
        if isinstance(bench, str):
            logging.warning(f"no benchmark named {bench!r}")
            continue
        selected.append(bench)
    return selected


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
    should_run = _select_benchmarks(options.bm_selections, manifest)

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
    for op, _, kind, parsed in options.bm_selections:
        if op == '+':
            name = parsed.name if kind == 'benchmark' else parsed
            if name == 'all':
                selected = manifest.benchmarks
                break
    else:
        selected = _select_benchmarks(options.bm_selections, manifest)

    print("%r benchmarks:" % options.benchmarks)
    for bench in sorted(selected):
        print("- %s" % bench.name)
    print()
    print("Total: %s benchmarks" % len(selected))


def cmd_list_groups(options):
    manifest = load_manifest(options.manifest)
    manifest.groups['all'] = list(manifest.benchmarks)
    all_benchmarks = set(manifest.benchmarks)

    for group, specs in sorted(manifest.groups.items()):
        known = set(specs) & all_benchmarks
        if not known:
            # skip empty groups
            continue

        print("%s (%s):" % (group, len(specs)))
        for spec in sorted(specs):
            print("- %s" % spec.name)
        print()
