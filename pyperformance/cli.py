import argparse
import contextlib
import logging
import os.path
import sys

from pyperformance import _utils, is_installed
from pyperformance.venv import exec_in_virtualenv, cmd_venv


def comma_separated(values):
    values = [value.strip() for value in values.split(',')]
    return list(filter(None, values))


def filter_opts(cmd, *, allow_no_benchmarks=False):
    cmd.add_argument("--manifest", help="benchmark manifest file to use")

    cmd.add_argument("-b", "--benchmarks", metavar="BM_LIST", default='<default>',
                     help=("Comma-separated list of benchmarks to run.  Can"
                           " contain both positive and negative arguments:"
                           "  --benchmarks=run_this,also_this,-not_this.  If"
                           " there are no positive arguments, we'll run all"
                           " benchmarks except the negative arguments. "
                           " Otherwise we run only the positive arguments."))
    cmd.set_defaults(allow_no_benchmarks=allow_no_benchmarks)


def parse_args():
    parser = argparse.ArgumentParser(
        description=("Compares the performance of baseline_python with"
                     " changed_python and prints a report."))

    subparsers = parser.add_subparsers(dest='action')
    cmds = []

    # run
    cmd = subparsers.add_parser(
        'run', help='Run benchmarks on the running python')
    cmds.append(cmd)
    cmd.add_argument("-r", "--rigorous", action="store_true",
                     help=("Spend longer running tests to get more"
                           " accurate results"))
    cmd.add_argument("-f", "--fast", action="store_true",
                     help="Get rough answers quickly")
    cmd.add_argument("--debug-single-value", action="store_true",
                     help="Debug: fastest mode, only compute a single value")
    cmd.add_argument("-v", "--verbose", action="store_true",
                     help="Print more output")
    cmd.add_argument("-m", "--track-memory", action="store_true",
                     help="Track memory usage. This only works on Linux.")
    cmd.add_argument("--affinity", metavar="CPU_LIST", default=None,
                     help=("Specify CPU affinity for benchmark runs. This "
                           "way, benchmarks can be forced to run on a given "
                           "CPU to minimize run to run variation."))
    cmd.add_argument("-o", "--output", metavar="FILENAME",
                     help="Run the benchmarks on only one interpreter and "
                           "write benchmark into FILENAME. "
                           "Provide only baseline_python, not changed_python.")
    cmd.add_argument("--append", metavar="FILENAME",
                     help="Add runs to an existing file, or create it "
                     "if it doesn't exist")
    filter_opts(cmd)

    # show
    cmd = subparsers.add_parser('show', help='Display a benchmark file')
    cmd.add_argument("filename", metavar="FILENAME")

    # compare
    cmd = subparsers.add_parser('compare', help='Compare two benchmark files')
    cmds.append(cmd)
    cmd.add_argument("-v", "--verbose", action="store_true",
                     help="Print more output")
    cmd.add_argument("-O", "--output_style", metavar="STYLE",
                     choices=("normal", "table"),
                     default="normal",
                     help=("What style the benchmark output should take."
                           " Valid options are 'normal' and 'table'."
                           " Default is normal."))
    cmd.add_argument("--csv", metavar="CSV_FILE",
                     action="store", default=None,
                     help=("Name of a file the results will be written to,"
                           " as a three-column CSV file containing minimum"
                           " runtimes for each benchmark."))
    cmd.add_argument("baseline_filename", metavar="baseline_file.json")
    cmd.add_argument("changed_filename", metavar="changed_file.json")

    # list
    cmd = subparsers.add_parser(
        'list', help='List benchmarks of the running Python')
    cmds.append(cmd)
    filter_opts(cmd)

    # list_groups
    cmd = subparsers.add_parser(
        'list_groups', help='List benchmark groups of the running Python')
    cmds.append(cmd)
    cmd.add_argument("--manifest", help="benchmark manifest file to use")

    # compile
    cmd = subparsers.add_parser(
        'compile', help='Compile and install CPython and run benchmarks '
                        'on installed Python')
    cmd.add_argument('config_file',
                     help='Configuration filename')
    cmd.add_argument('revision',
                     help='Python benchmarked revision')
    cmd.add_argument('branch', nargs='?',
                     help='Git branch')
    cmd.add_argument('--patch',
                     help='Patch file')
    cmd.add_argument('-U', '--no-update', action="store_true",
                     help="Don't update the Git repository")
    cmd.add_argument('-T', '--no-tune', action="store_true",
                     help="Don't run 'pyperf system tune' "
                          "to tune the system for benchmarks")
    cmds.append(cmd)

    # compile_all
    cmd = subparsers.add_parser(
        'compile_all',
        help='Compile and install CPython and run benchmarks '
             'on installed Python on all branches and revisions '
             'of CONFIG_FILE')
    cmd.add_argument('config_file',
                     help='Configuration filename')
    cmds.append(cmd)

    # upload
    cmd = subparsers.add_parser(
        'upload', help='Upload JSON results to a Codespeed website')
    cmd.add_argument('config_file',
                     help='Configuration filename')
    cmd.add_argument('json_file',
                     help='JSON filename')
    cmds.append(cmd)

    # venv
    cmd = subparsers.add_parser('venv',
                                help='Actions on the virtual environment')
    cmd.set_defaults(venv_action='show')
    venvsubs = cmd.add_subparsers(dest="venv_action")
    cmd = venvsubs.add_parser('show')
    cmds.append(cmd)
    cmd = venvsubs.add_parser('create')
    filter_opts(cmd, allow_no_benchmarks=True)
    cmds.append(cmd)
    cmd = venvsubs.add_parser('recreate')
    filter_opts(cmd, allow_no_benchmarks=True)
    cmds.append(cmd)
    cmd = venvsubs.add_parser('remove')
    cmds.append(cmd)

    for cmd in cmds:
        cmd.add_argument("--inherit-environ", metavar="VAR_LIST",
                         type=comma_separated,
                         help=("Comma-separated list of environment variable "
                               "names that are inherited from the parent "
                               "environment when running benchmarking "
                               "subprocesses."))
        cmd.add_argument("--inside-venv", action="store_true",
                         help=("Option for internal usage only, don't use "
                               "it directly. Notice that we are already "
                               "inside the virtual environment."))
        cmd.add_argument("-p", "--python",
                         help="Python executable (default: use running Python)",
                         default=sys.executable)
        cmd.add_argument("--venv",
                         help="Path to the virtual environment")

    options = parser.parse_args()

    if options.action == 'run' and options.debug_single_value:
        options.fast = True

    if not options.action:
        # an action is mandatory
        parser.print_help()
        sys.exit(1)

    if hasattr(options, 'python'):
        # Replace "~" with the user home directory
        options.python = os.path.expanduser(options.python)
        # Try to get the absolute path to the binary
        abs_python = os.path.abspath(options.python)
        if not abs_python:
            print("ERROR: Unable to locate the Python executable: %r" %
                  options.python, flush=True)
            sys.exit(1)
        options.python = abs_python

    if hasattr(options, 'benchmarks'):
        if options.benchmarks == '<NONE>':
            if not options.allow_no_benchmarks:
                parser.error('--benchmarks cannot be empty')
            options.benchmarks = None

    return (parser, options)


@contextlib.contextmanager
def _might_need_venv(options):
    try:
        yield
    except ModuleNotFoundError:
        if not options.inside_venv:
            print('switching to a venv.', flush=True)
            exec_in_virtualenv(options)
        raise  # re-raise


def _manifest_from_options(options):
    from pyperformance import _manifest
    return _manifest.load_manifest(options.manifest)


def _benchmarks_from_options(options):
    if not getattr(options, 'benchmarks', None):
        return None
    manifest = _manifest_from_options(options)
    return _select_benchmarks(options.benchmarks, manifest)


def _select_benchmarks(raw, manifest):
    from pyperformance import _benchmark_selections

    # Get the raw list of benchmarks.
    entries = raw.lower()
    parse_entry = (lambda o, s: _benchmark_selections.parse_selection(s, op=o))
    parsed = _utils.parse_selections(entries, parse_entry)
    parsed_infos = list(parsed)

    # Disallow negative groups.
    for op, _, kind, parsed in parsed_infos:
        if callable(parsed):
            continue
        name = parsed.name if kind == 'benchmark' else parsed
        if name in manifest.groups and op == '-':
            raise ValueError(f'negative groups not supported: -{parsed.name}')

    # Get the selections.
    selected = []
    for bench in _benchmark_selections.iter_selections(manifest, parsed_infos):
        if isinstance(bench, str):
            logging.warning(f"no benchmark named {bench!r}")
            continue
        selected.append(bench)
    return selected


def _main():
    parser, options = parse_args()

    if not is_installed():
        assert not options.inside_venv
        print('switching to a venv.', flush=True)
        exec_in_virtualenv(options)

    if options.action == 'venv':
        with _might_need_venv(options):
            benchmarks = _benchmarks_from_options(options)
        cmd_venv(options, benchmarks)
        sys.exit()
    elif options.action == 'compile':
        from pyperformance.compile import cmd_compile
        cmd_compile(options)
        sys.exit()
    elif options.action == 'compile_all':
        from pyperformance.compile import cmd_compile_all
        cmd_compile_all(options)
        sys.exit()
    elif options.action == 'upload':
        from pyperformance.compile import cmd_upload
        cmd_upload(options)
        sys.exit()
    elif options.action == 'show':
        from pyperformance.compare import cmd_show
        cmd_show(options)
        sys.exit()
    elif options.action == 'run':
        with _might_need_venv(options):
            from pyperformance.cli_run import cmd_run
            benchmarks = _benchmarks_from_options(options)
        cmd_run(options, benchmarks)
    elif options.action == 'compare':
        with _might_need_venv(options):
            from pyperformance.compare import cmd_compare
        cmd_compare(options)
    elif options.action == 'list':
        with _might_need_venv(options):
            from pyperformance.cli_run import cmd_list
            benchmarks = _benchmarks_from_options(options)
        cmd_list(options, benchmarks)
    elif options.action == 'list_groups':
        with _might_need_venv(options):
            from pyperformance.cli_run import cmd_list_groups
            manifest = _manifest_from_options(options)
        cmd_list_groups(manifest)
    else:
        parser.print_help()
        sys.exit(1)


def main():
    try:
        _main()
    except KeyboardInterrupt:
        print("Benchmark suite interrupted: exit!", flush=True)
        sys.exit(1)
