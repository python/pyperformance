from __future__ import division, with_statement, print_function, absolute_import

import argparse
import os.path
import sys

from performance.venv import exec_in_virtualenv, which, cmd_venv


def comma_separated(values):
    values = [value.strip() for value in values.split(',')]
    return list(filter(None, values))


def _add_run_options(cmd):
    cmd.add_argument("-r", "--rigorous", action="store_true",
                     help=("Spend longer running tests to get more" +
                           " accurate results"))
    cmd.add_argument("-f", "--fast", action="store_true",
                     help="Get rough answers quickly")
    cmd.add_argument("--debug-single-sample", action="store_true",
                     help="Debug: fastest mode, only collect a single sample")
    cmd.add_argument("-v", "--verbose", action="store_true",
                     help="Print more output")
    cmd.add_argument("-m", "--track-memory", action="store_true",
                     help="Track memory usage. This only works on Linux.")
    cmd.add_argument("-a", "--args", default="",
                     help=("Pass extra arguments (interpreted as a "
                           "space-separated list) to the python binary."))
    cmd.add_argument("-b", "--benchmarks", metavar="BM_LIST", default="",
                     help=("Comma-separated list of benchmarks to run.  Can"
                           " contain both positive and negative arguments:"
                           "  --benchmarks=run_this,also_this,-not_this.  If"
                           " there are no positive arguments, we'll run all"
                           " benchmarks except the negative arguments. "
                           " Otherwise we run only the positive arguments."))
    cmd.add_argument("--inherit-environ", metavar="VAR_LIST",
                     type=comma_separated,
                     help=("Comma-separated list of environment variable names"
                           " that are inherited from the parent environment"
                           " when running benchmarking subprocesses."))
    cmd.add_argument("--affinity", metavar="CPU_LIST", default=None,
                     help=("Specify CPU affinity for benchmark runs. This "
                           "way, benchmarks can be forced to run on a given "
                           "CPU to minimize run to run variation."))


def _add_compare_options(cmd):
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


def parse_args():

    parser = argparse.ArgumentParser(
        description=("Compares the performance of baseline_python with" +
                     " changed_python and prints a report."))

    subparsers = parser.add_subparsers(dest='action')
    cmds = []

    # run
    cmd = subparsers.add_parser(
        'run', help='Run benchmarks on the running python')
    cmds.append(cmd)
    _add_run_options(cmd)
    cmd.add_argument("-o", "--output", metavar="FILENAME",
                     help="Run the benchmarks on only one interpreter and "
                           "write benchmark into FILENAME. "
                           "Provide only baseline_python, not changed_python.")
    cmd.add_argument("--append", metavar="FILENAME",
                     help="Add runs to an existing file, or create it "
                     "if it doesn't exist")

    # show
    cmd = subparsers.add_parser('show', help='Display a benchmark file')
    cmd.add_argument("filename", metavar="FILENAME")
    cmds.append(cmd)

    # compare
    cmd = subparsers.add_parser('compare', help='Compare two benchmark files')
    cmds.append(cmd)
    cmd.add_argument("-v", "--verbose", action="store_true",
                     help="Print more output")
    _add_compare_options(cmd)
    cmd.add_argument("baseline_filename", metavar="baseline_file.json")
    cmd.add_argument("changed_filename", metavar="changed_file.json")

    # list
    cmd = subparsers.add_parser(
        'list', help='List benchmarks of the running Python')
    cmds.append(cmd)

    # list_groups
    cmd = subparsers.add_parser(
        'list_groups', help='List benchmark groups of the running Python')
    cmds.append(cmd)

    # venv
    cmd = subparsers.add_parser('venv',
                                help='Actions on the virtual environment')
    cmd.add_argument("venv_action", nargs="?",
                     choices=('show', 'create', 'recreate', 'remove'),
                     default='show')
    cmds.append(cmd)

    for cmd in cmds:
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

    if options.action == 'run' and options.debug_single_sample:
        options.fast = True

    if not options.action:
        # an action is mandatory
        parser.print_help()
        sys.exit(1)

    # Replace "~" with the user home directory
    options.python = os.path.expanduser(options.python)
    # Try to the absolute path to the binary
    abs_python = which(options.python)
    if not abs_python:
        print("ERROR: Unable to locate the Python executable: %r" %
              options.python)
        sys.exit(1)
    options.python = os.path.realpath(abs_python)

    return (parser, options)


def _main():
    parser, options = parse_args()

    if options.action == 'venv':
        cmd_venv(options)
        sys.exit()

    if not options.inside_venv:
        exec_in_virtualenv(options)

    from performance.run import cmd_run, cmd_list
    from performance.compare import cmd_compare, cmd_show
    from performance.benchmarks import get_benchmark_groups

    if options.action == 'run':
        bench_funcs, bench_groups = get_benchmark_groups()
        cmd_run(parser, options, bench_funcs, bench_groups)
    elif options.action == 'show':
        cmd_show(options)
    elif options.action == 'compare':
        cmd_compare(options)
    elif options.action in ('list', 'list_groups'):
        bench_funcs, bench_groups = get_benchmark_groups()
        cmd_list(options, bench_funcs, bench_groups)
    else:
        parser.print_help()
        sys.exit(1)


def main():
    try:
        _main()
    except KeyboardInterrupt:
        print("Benchmark suite interrupted: exit!")
        sys.exit(1)
