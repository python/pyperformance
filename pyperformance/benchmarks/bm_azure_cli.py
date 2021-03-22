"""Test the performance of the Azure CLI.

The test suite is an adequate proxy for regular usage of the CLI.
"""

# The code for this benchmark is based on the manual steps defined
# for the azure-cli repo.

# See:
#  - azure-pipelines.yml
#  - https://github.com/Azure/azure-cli-dev-tools
#
# sudo apt install python3.8
# sudo apt install python3.8-venv
# sudo apt install python3.8-devel
# git clone https://github.com/Azure/azure-cli
# cd azure-cli
# python3.8 -m venv .venv
# source .venv/bin/activate
# python3 -m pip install azdev
# azdev setup --cli .
#
# azdev test
# (PYTHONPATH=tools python3 -m automation test --cli .)
# PYTHONPATH=tools python3 -m automation verify commands
# (./scripts/ci/unittest.sh)
# (./scripts/ci/test_automation.sh)
# (./scripts/ci/test_integration.sh)

import os
import os.path
import pyperf
import shlex
import subprocess
import sys

import pyperformance.venv


AZURE_CLI_UPSTREAM = "https://github.com/Azure/azure-cli"
AZURE_CLI_REPO = os.path.join(os.path.dirname(__file__), 'data', 'azure-cli')


def _run_bench_command_env(runner, name, command, env):
    if runner.args.inherit_environ:
        runner.args.inherit_environ.extend(env)
    else:
        runner.args.inherit_environ = list(env)

    env_before = dict(os.environ)
    os.environ.update(env)
    try:
        return runner.bench_command(name, command)
    finally:
        os.environ.clear()
        os.environ.update(env_before)


def _resolve_virtual_env(pypath=None):
    # This is roughly equivalent to ensuring the env is activated.
    env = pyperformance.venv.resolve_env_vars()

    if pypath:
        if not isinstance(pypath, str):
            pypath = os.pathsep.join(pypath)
        env["PYTHONPATH"] = pypath

    return env


def _run(argv, **kwargs):
    cmd_str = ' '.join(map(shlex.quote, argv))
    print("Execute: %s" % cmd_str)
    sys.stdout.flush()
    sys.stderr.flush()
    proc = subprocess.run(argv, **kwargs)
    proc.check_returncode()


###################
# azure-cli helpers

# This global allows us to only check the install once per proc.
INSTALL_ENSURED = False


def install(force=False):
    global INSTALL_ENSURED

    print("=========================================")
    print("installing for the azure_cli benchmark...")
    if force:
        _install()
    elif INSTALL_ENSURED:
        print("already checked")
    elif _already_installed():
        print("already installed")
    else:
        _install()
    print("...done")
    print("=========================================")

    INSTALL_ENSURED = True


def _already_installed():
    try:
        import azure.cli
    except ImportError:
        return False
    else:
        return True


def _install():
    if os.path.exists(AZURE_CLI_REPO):
        print("local repo already exists (skipping)")
    else:
        _run(["git", "clone", AZURE_CLI_UPSTREAM, AZURE_CLI_REPO])

    print("...setting up...")
    if not os.environ.get("VIRTUAL_ENV"):
        raise Exception("the target venv is not activated")
    # XXX Do not run this again if already done.
    _run(
        [sys.executable, "-m", "azdev", "setup", "--cli", AZURE_CLI_REPO],
        env=_resolve_virtual_env(),
    )


TESTS_FAST = [
    # XXX Is this a good sample of tests (to ~ represent the workload)?
    ("src/azure-cli/azure/cli/command_modules/ams/tests/latest/test_ams_account_scenarios.py",
     "AmsAccountTests.test_ams_check_name"),
]
TESTS_MEDIUM = [
]


def _get_tests_cmd(tests='<fast>'):
    if not tests:
        tests = '<all>'
    if isinstance(tests, str):
        if tests == '<all>':
            tests = []  # slow
        elif tests == '<slow>':
            tests = []  # slow
        elif tests == '<medium>':
            tests = TESTS_MEDIUM
        elif tests == '<fast>':
            tests = TESTS_FAST
        else:
            if tests.startswith('<'):
                raise ValueError('unsupported "test" ({!r})'.format(tests))
            raise NotImplementedError
    else:
        raise NotImplementedError
    testargs = [file + ":" + name for file, name in tests]

    cmd = ["azdev", "test"] + testargs
    return cmd


###################
# benchmarks

def run_sample(runner):
    # For now we run just a small subset of azure-cli test suite.
    env = _resolve_virtual_env()
    cmd = _get_tests_cmd(tests='<fast>')
    return _run_bench_command_env(
        runner,
        "azure_cli",
        cmd,
        env,
    )

    # XXX It may make sense for this test to instead manually invoke
    # the Azure CLI in 3-5 different ways.
    #def func():
    #    raise NotImplementedError
    #return runner.bench_func("azure_cli", func)


def run_tests(runner):
    env = _resolve_virtual_env()
    tests = '<fast>' if runner.args.fast else '<all>'
    cmd = _get_tests_cmd(tests)
    return _run_bench_command_env(
        runner,
        "azure_cli",
        cmd,
        env,
    )


def run_verify(runner):
    pypath = os.path.join(AZURE_CLI_REPO, 'tools')
    env = _resolve_virtual_env(pypath)
    cmd = [
        sys.executable,
        "-m", "automation",
        "verify",
        "commands",
    ]
    if runner.args.fast:
        cmd.extend([
            # XXX Is this a good enough proxy?
            "--prefix", "account",
        ])
    return _run_bench_command_env(
        runner,
        "azure_cli_verify",
        cmd,
        env,
    )


###################
# the script

def get_runner():
    def add_cmdline_args(cmd, args):
        # Preserve --kind.
        kind = getattr(args, 'kind', 'sample')
        cmd.extend(["--kind", kind])
        # Note that we do not preserve --install.  We don't need
        # the worker to duplicate the work.
        if args.fast:
            cmd.append('--fast')

    runner = pyperf.Runner(
        add_cmdline_args=add_cmdline_args,
        metadata={
            "description": "Performance of the Azure CLI",
        },
    )

    runner.argparser.add_argument("--kind",
                                  choices=["sample", "tests", "verify", "install"],
                                  default="sample")
    runner.argparser.add_argument("--install",
                                  action="store_const", const="<ensure>",
                                  default="<ensure>")
    runner.argparser.add_argument("--force-install", dest="install",
                                  action="store_const", const="<force>")
    runner.argparser.add_argument("--no-install", dest="install",
                                  action="store_const", const=None)

    return runner


def main():
    runner = get_runner()
    args = runner.parse_args()

    if args.install == "<ensure>":
        install(force=False)
    elif args.install == "<force>":
        install(force=True)
    elif args.install:
        raise NotImplementedError(args.install)

    if args.kind == "sample":
        # fast(er)
        run_sample(runner)
    elif args.kind == "tests":
        # slow
        #runner.values = 1
        run_tests(runner)
    elif args.kind == "verify":
        # slow
        #runner.values = 1
        run_verify(runner)
    elif args.kind == "install":
        return
    else:
        raise NotImplementedError(args.kind)


if __name__ == '__main__':
    main()
