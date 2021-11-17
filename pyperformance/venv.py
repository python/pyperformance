import errno
import os
import os.path
import shutil
import subprocess
import sys
import textwrap
import urllib.request
from shlex import quote as shell_quote

import pyperformance
from . import _utils, _pythoninfo


GET_PIP_URL = 'https://bootstrap.pypa.io/get-pip.py'
REQ_OLD_PIP = 'pip==7.1.2'
REQ_OLD_SETUPTOOLS = 'setuptools==18.5'

PERFORMANCE_ROOT = os.path.realpath(os.path.dirname(__file__))
REQUIREMENTS_FILE = os.path.join(pyperformance.DATA_DIR, 'requirements.txt')


def is_build_dir():
    root_dir = os.path.join(PERFORMANCE_ROOT, '..')
    if not os.path.exists(os.path.join(root_dir, 'pyperformance')):
        return False
    return os.path.exists(os.path.join(root_dir, 'setup.py'))


class RequirementsInstallationFailedError(Exception):
    pass


class Requirements(object):

    @classmethod
    def from_file(cls, filename, optional=None):
        self = cls()
        self._add_from_file(filename, optional)
        return self

    @classmethod
    def from_benchmarks(cls, benchmarks):
        self = cls()
        for bench in benchmarks or ():
            filename = bench.requirements_lockfile
            self._add_from_file(filename)
        return self

    def __init__(self):
        # if pip or setuptools is updated:
        # .github/workflows/main.yml should be updated as well

        # pip requirements
        self.pip = [
            # pip 6 is the first version supporting environment markers
            'pip>=6.0',
        ]

        # installer requirements
        self.installer = [
            # html5lib requires setuptools 18.5 or newer
            'setuptools>=18.5',
            # install wheel so pip can cache binary wheel packages locally,
            # and install prebuilt wheel packages from PyPI
            'wheel',
        ]

        # requirements
        self.specs = []

        # optional requirements
        self._optional = set()

    def __len__(self):
        return len(self.specs)

    def iter_non_optional(self):
        for spec in self.specs:
            if spec in self._optional:
                continue
            yield spec

    def iter_optional(self):
        for spec in self.specs:
            if spec not in self._optional:
                continue
            yield spec

    def _add_from_file(self, filename, optional=None):
        if not os.path.exists(filename):
            return
        for line in _utils.iter_clean_lines(filename):
            self._add(line, optional)

    def _add(self, line, optional=None):
        self.specs.append(line)
        if optional:
            # strip env markers
            req = line.partition(';')[0]
            # strip version
            req = req.partition('==')[0]
            req = req.partition('>=')[0]
            if req in optional:
                self._optional.add(line)

    def get(self, name):
        for req in self.specs:
            if req.startswith(name):
                return req
        return None


def safe_rmtree(path):
    if not os.path.exists(path):
        return

    print("Remove directory %s" % path)
    shutil.rmtree(path)


def python_implementation():
    return sys.implementation.name.lower()


def get_venv_program(program):
    bin_path = os.path.dirname(sys.executable)
    bin_path = os.path.realpath(bin_path)

    if not os.path.isabs(bin_path):
        print("ERROR: Python executable path is not absolute: %s"
              % sys.executable)
        sys.exit(1)

    if not os.path.exists(os.path.join(bin_path, 'activate')):
        print("ERROR: Unable to get the virtual environment of "
              "the Python executable %s" % sys.executable)
        sys.exit(1)

    if os.name == 'nt':
        path = os.path.join(bin_path, program)
    else:
        path = os.path.join(bin_path, program)

    if not os.path.exists(path):
        print("ERROR: Unable to get the program %r "
              "from the virtual environment %r"
              % (program, bin_path))
        sys.exit(1)

    return path


def create_environ(inherit_environ):
    env = {}

    copy_env = ["PATH", "HOME", "TEMP", "COMSPEC", "SystemRoot"]
    if inherit_environ:
        copy_env.extend(inherit_environ)

    for name in copy_env:
        if name in os.environ:
            env[name] = os.environ[name]

    return env


def download(url, filename):
    response = urllib.request.urlopen(url)
    with response:
        content = response.read()

    with open(filename, 'wb') as fp:
        fp.write(content)
        fp.flush()


class VirtualEnvironment(object):

    def __init__(self, python, root=None, *,
                 inherit_environ=None,
                 name=None,
                 usebase=False,
                 ):
        if usebase:
            python, _, _ = _pythoninfo.inspect_python_install(python)

        self.python = python
        self.inherit_environ = inherit_environ or None
        self._name = name or None
        self._venv_path = root or None
        self._pip_program = None
        self._force_old_pip = False
        self._prepared = False

    @property
    def name(self):
        if self._name is None:
            from .run import get_run_id
            runid = get_run_id(self.python)
            self._name = runid.name
        return self._name

    def get_python_program(self):
        venv_path = self.get_path()
        if os.name == "nt":
            python_executable = os.path.basename(self.python)
            return os.path.join(venv_path, 'Scripts', python_executable)
        else:
            return os.path.join(venv_path, 'bin', 'python')

    def run_cmd_nocheck(self, cmd, verbose=True):
        cmd_str = ' '.join(map(shell_quote, cmd))
        if verbose:
            print("Execute: %s" % cmd_str)

        # Explicitly flush standard streams, required if streams are buffered
        # (not TTY) to write lines in the expected order
        sys.stdout.flush()
        sys.stderr.flush()

        env = create_environ(self.inherit_environ)
        try:
            proc = subprocess.Popen(cmd, env=env)
        except OSError as exc:
            if exc.errno == errno.ENOENT:
                # Command not found
                return 127
            raise

        try:
            proc.wait()
        except:   # noqa
            proc.kill()
            proc.wait()
            raise

        exitcode = proc.returncode
        if exitcode and verbose:
            print("Command %s failed with exit code %s" % (cmd_str, exitcode))
        return exitcode

    def run_cmd(self, cmd, verbose=True):
        exitcode = self.run_cmd_nocheck(cmd, verbose=verbose)
        if exitcode:
            sys.exit(exitcode)
        print()

    def get_output_nocheck(self, *cmd):
        cmd_str = ' '.join(map(shell_quote, cmd))
        print("Execute: %s" % cmd_str)

        proc = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                universal_newlines=True)
        stdout = proc.communicate()[0]
        exitcode = proc.returncode
        if exitcode:
            print("Command %s failed with exit code %s" % (cmd_str, exitcode))
        return (exitcode, stdout)

    def get_path(self):
        if not self._venv_path:
            self._venv_path = os.path.abspath(
                os.path.join('venv', self.name),
            )
        return self._venv_path

    def _get_pip_program(self):
        venv_path = self.get_path()
        args = ['--version']

        # python -m pip
        venv_python = self.get_python_program()
        pip_program = [venv_python, '-m', 'pip']
        if self.run_cmd_nocheck(pip_program + args) == 0:
            self._pip_program = pip_program
            return

        # Note: "python -m pip" command doesn't work with pip 1.0

        # pip program
        if os.name == "nt":
            venv_pip = os.path.join(venv_path, 'Scripts', 'pip')
        else:
            venv_pip = os.path.join(venv_path, 'bin', 'pip')
        if not os.path.exists(venv_pip) and os.path.exists(venv_pip + '3'):
            # ensurepip doesn't install "pip" program but only "pip3":
            # so use "pip3"
            venv_pip += '3'

        pip_program = [venv_pip]
        if self.run_cmd_nocheck(pip_program + args) == 0:
            self._pip_program = pip_program
            return

    def get_pip_program(self):
        if self._pip_program is None:
            self._get_pip_program()
        return self._pip_program

    def _get_python_version(self):
        venv_python = self.get_python_program()

        # FIXME: use a get_output() function
        code = 'import sys; print(sys.hexversion)'
        exitcode, stdout = self.get_output_nocheck(venv_python, '-c', code)
        if exitcode:
            print("ERROR: failed to get the Python version")
            sys.exit(exitcode)
        hexversion = int(stdout.rstrip())
        print("Python hexversion: %x" % hexversion)

        # On Python: 3.5a0 <= version < 3.5.0 (final), install pip 7.1.2,
        # the last version working on Python 3.5a0:
        # https://sourceforge.net/p/pyparsing/bugs/100/
        self._force_old_pip = (0x30500a0 <= hexversion < 0x30500f0)

    def install_pip(self):
        venv_python = self.get_python_program()

        # python -m ensurepip
        cmd = [venv_python, '-m', 'ensurepip', '--verbose']
        exitcode = self.run_cmd_nocheck(cmd)
        if not exitcode:
            if self.get_pip_program() is not None:
                return True

        # download get-pip.py
        venv_path = self.get_path()
        filename = os.path.join(os.path.dirname(venv_path), 'get-pip.py')
        if not os.path.exists(filename):
            print("Download %s into %s" % (GET_PIP_URL, filename))
            download(GET_PIP_URL, filename)

        # python get-pip.py
        if self._force_old_pip:
            cmd = [venv_python, '-u', filename, REQ_OLD_PIP]
        else:
            cmd = [venv_python, '-u', filename]
        exitcode = self.run_cmd_nocheck(cmd)
        ok = (exitcode == 0)
        if not ok:
            # get-pip.py was maybe not properly downloaded: remove it to
            # download it again next time
            os.unlink(filename)

        return ok

    def _create_venv_cmd(self, cmd, install_pip=False):
        try:
            exitcode = self.run_cmd_nocheck(cmd)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise

            # run_cmd_nocheck() failed with ENOENT
            print("%s command failed: command not found" % ' '.join(cmd))
            return False

        if exitcode:
            print("%s command failed" % ' '.join(cmd))
            return False

        self._get_python_version()

        if install_pip:
            ok = self.install_pip()
            if not ok:
                print("failed to install pip")
                return False

        if self.get_pip_program() is None:
            print("ERROR: pip doesn't work")
            return False

        return True

    def _create_venv(self):
        venv_path = self.get_path()

        for install_pip, cmd in (
            # python -m venv
            (True, [self.python, '-m', 'venv', '--without-pip']),
            # python -m virtualenv
            (False, [self.python, '-m', 'virtualenv']),
            # virtualenv command
            (False, ['virtualenv', '-p', self.python]),
        ):
            ok = self._create_venv_cmd(cmd + [venv_path], install_pip)
            if ok:
                return True

            # Command failed: remove the directory
            safe_rmtree(venv_path)

        # All commands failed
        print("ERROR: failed to create the virtual environment")
        print()
        print("Make sure that virtualenv is installed:")
        print("%s -m pip install -U virtualenv" % self.python)
        sys.exit(1)

    def exists(self):
        venv_python = self.get_python_program()
        return os.path.exists(venv_python)

    def prepare(self, install=True):
        venv_path = self.get_path()
        print("Installing the virtual environment %s" % venv_path)
        if self._prepared or (self._prepared is None and not install):
            print('(already installed)')
            return
        pip_program = self.get_pip_program()

        if not self._prepared:
            # parse requirements
            basereqs = Requirements.from_file(REQUIREMENTS_FILE, ['psutil'])

            # Upgrade pip
            cmd = pip_program + ['install', '-U']
            if self._force_old_pip:
                cmd.extend((REQ_OLD_PIP, REQ_OLD_SETUPTOOLS))
            else:
                cmd.extend(basereqs.pip)
            self.run_cmd(cmd)

            # Upgrade installer dependencies (setuptools, ...)
            cmd = pip_program + ['install', '-U']
            cmd.extend(basereqs.installer)
            self.run_cmd(cmd)

        if install:
            # install pyperformance inside the virtual environment
            if is_build_dir():
                root_dir = os.path.dirname(PERFORMANCE_ROOT)
                cmd = pip_program + ['install', '-e', root_dir]
            else:
                version = pyperformance.__version__
                cmd = pip_program + ['install', 'pyperformance==%s' % version]
            self.run_cmd(cmd)
            self._prepared = True
        else:
            self._prepared = None

        # Display the pip version
        cmd = pip_program + ['--version']
        self.run_cmd(cmd)

        # Dump the package list and their versions: pip freeze
        cmd = pip_program + ['freeze']
        self.run_cmd(cmd)

    def create(self, install=True):
        venv_path = self.get_path()
        print("Creating the virtual environment %s" % venv_path)
        if self.exists():
            raise Exception(f'virtual environment {venv_path} already exists')
        try:
            self._create_venv()
            self.prepare(install)
        except:   # noqa
            print()
            safe_rmtree(venv_path)
            raise

    def ensure(self, refresh=True, install=True):
        venv_path = self.get_path()
        if self.exists():
            if refresh:
                self.prepare(install)
        else:
            self.create(install)

    def install_reqs(self, requirements=None, *, exitonerror=False):
        venv_path = self.get_path()
        print("Installing requirements into the virtual environment %s" % venv_path)

        # parse requirements
        bench = None
        if requirements is None:
            requirements = Requirements()
        elif hasattr(requirements, 'requirements_lockfile'):
            bench = requirements
            requirements = Requirements.from_benchmarks([bench])

        # Every benchmark must depend on pyperf.
        if requirements and bench is not None:
            if not requirements.get('pyperf'):
                basereqs = Requirements.from_file(REQUIREMENTS_FILE, ['psutil'])
                pyperf_req = basereqs.get('pyperf')
                if not pyperf_req:
                    raise NotImplementedError
                requirements.specs.append(pyperf_req)

        pip_program = self.get_pip_program()
        if not requirements:
            print('(nothing to install)')
        else:
            self.prepare(install=bench is None)

            # install requirements
            cmd = pip_program + ['install']
            reqs = list(requirements.iter_non_optional())
            cmd.extend(reqs)
            exitcode = self.run_cmd_nocheck(cmd)
            if exitcode:
                if exitonerror:
                    sys.exit(exitcode)
                raise RequirementsInstallationFailedError(reqs)

            # install optional requirements
            for req in requirements.iter_optional():
                cmd = pip_program + ['install', '-U', req]
                exitcode = self.run_cmd_nocheck(cmd)
                if exitcode:
                    print("WARNING: failed to install %s" % req)
                    print()

        # Dump the package list and their versions: pip freeze
        cmd = pip_program + ['freeze']
        self.run_cmd(cmd)

        return requirements


def exec_in_virtualenv(options):
    venv = VirtualEnvironment(
        options.python,
        options.venv,
        inherit_environ=options.inherit_environ,
    )

    venv.ensure()
    venv_python = venv.get_python_program()

    args = [venv_python, "-m", "pyperformance"] + \
        sys.argv[1:] + ["--inside-venv"]
    # os.execv() is buggy on windows, which is why we use run_cmd/subprocess
    # on windows.
    # * https://bugs.python.org/issue19124
    # * https://github.com/python/benchmarks/issues/5
    if os.name == "nt":
        venv.run_cmd(args, verbose=False)
        sys.exit(0)
    else:
        os.execv(args[0], args)


def cmd_venv(options, benchmarks=None):
    action = options.venv_action

    requirements = Requirements.from_benchmarks(benchmarks)

    venv = VirtualEnvironment(
        options.python,
        options.venv,
        inherit_environ=options.inherit_environ,
    )
    venv_path = venv.get_path()
    exists = venv.exists()

    if action == 'create':
        if exists:
            print("The virtual environment %s already exists" % venv_path)
        venv.ensure()
        venv.install_reqs(requirements, exitonerror=True)
        if not exists:
            print("The virtual environment %s has been created" % venv_path)

    elif action == 'recreate':
        if exists:
            if venv.get_python_program() == sys.executable:
                print("The virtual environment %s already exists" % venv_path)
                print("(it matches the currently running Python executable)")
                venv.ensure()
                venv.install_reqs(requirements, exitonerror=True)
            else:
                print("The virtual environment %s already exists" % venv_path)
                shutil.rmtree(venv_path)
                print("The old virtual environment %s has been removed" % venv_path)
                print()
                venv.ensure()
                venv.install_reqs(requirements, exitonerror=True)
                print("The virtual environment %s has been recreated" % venv_path)
        else:
            venv.create()
            venv.install_reqs(requirements, exitonerror=True)
            print("The virtual environment %s has been created" % venv_path)

    elif action == 'remove':
        if os.path.exists(venv_path):
            shutil.rmtree(venv_path)
            print("The virtual environment %s has been removed" % venv_path)
        else:
            print("The virtual environment %s does not exist" % venv_path)

    else:
        # show command
        text = "Virtual environment path: %s" % venv_path
        created = venv.exists()
        if created:
            text += " (already created)"
        else:
            text += " (not created yet)"
        print(text)

        if not created:
            print()
            print("Command to create it:")
            cmd = "%s -m pyperformance venv create" % options.python
            if options.venv:
                cmd += " --venv=%s" % options.venv
            print(cmd)
