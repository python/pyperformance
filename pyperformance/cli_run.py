import logging
import os.path
import sys

import pyperf

import pyperformance
from pyperformance.benchmark import parse_benchmark
from pyperformance.benchmarks import (
    load_manifest,
    iter_benchmarks,
    get_benchmarks,
    get_benchmark_groups,
    expand_benchmark_groups,
    select_benchmarks,
)
from pyperformance.compare import display_benchmark_suite
from pyperformance.run import run_benchmarks


def _select_benchmarks(raw, manifest):
    groups = get_benchmark_groups(manifest)
    def expand(parsed, op):
        if isinstance(parsed, str):
            parsed = parse_benchmark(parsed)
        if parsed.name in groups and op == 'remove':
            raise ValueError(f'negative groups not supported: -{parsed.name}')
        yield from expand_benchmark_groups(parsed, groups)

    known = set(b.spec for b in iter_benchmarks(manifest))
    def check_known(parsed, raw):
        if parsed not in known:
            logging.warning(f"no benchmark named {parsed.name!r}")
            return False
        return True

    return select_benchmarks(
        raw,
        manifest,
        expand=expand,
        known=check_known,
    )


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
    should_run = _select_benchmarks(options.benchmarks, manifest)

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
    if 'all' in options.benchmarks.split(','):
        selected = manifest.benchmarks
    else:
        selected = _select_benchmarks(options.benchmarks, manifest)

    print("%r benchmarks:" % options.benchmarks)
    for bench in sorted(selected):
        print("- %s" % bench.name)
    print()
    print("Total: %s benchmarks" % len(selected))


def cmd_list_groups(options):
    manifest = load_manifest(options.manifest)
    bench_groups = get_benchmark_groups(manifest)
    bench_groups['all'] = list(manifest.benchmarks)
    all_benchmarks = set(manifest.benchmarks)

    for group, specs in sorted(bench_groups.items()):
        known = set(specs) & all_benchmarks
        if not known:
            # skip empty groups
            continue

        print("%s (%s):" % (group, len(specs)))
        for spec in sorted(specs):
            print("- %s" % spec.name)
        print()
