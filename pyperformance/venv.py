import errno
import os
import os.path
import subprocess
import sys
import types
from shlex import quote as shell_quote

import pyperformance
from . import _utils, _pythoninfo, _pip


REQUIREMENTS_FILE = os.path.join(pyperformance.DATA_DIR, 'requirements.txt')


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


def read_venv_config(root=None):
    """Return the config for the given venv, from its pyvenv.cfg file."""
    if not root:
        if sys.prefix == sys.base_prefix:
            raise Exception('current Python is not a venv')
        root = sys.prefix
    cfgfile = os.path.join(root, 'pyvenv.cfg')
    with open(cfgfile, encoding='utf-8') as infile:
        text = infile.read()
    return parse_venv_config(text, root)


def parse_venv_config(lines, root=None):
    if isinstance(lines, str):
        lines = lines.splitlines()
    else:
        lines = (l.rstrip(os.linesep) for l in lines)

    cfg = types.SimpleNamespace(
        home=None,
        version=None,
        system_site_packages=None,
        prompt=None,
        executable=None,
        command=None,
    )
    fields = set(vars(cfg))
    for line in lines:
        # We do not validate the lines.
        name, sep, value = line.partition('=')
        if not sep:
            continue
        # We do not check for duplicate names.
        name = name.strip().lower()
        if name == 'include-system-site-packages':
            name = 'system_site_packages'
        if name not in fields:
            # XXX Preserve this anyway?
            continue
        value = value.lstrip()
        if name == 'system_site_packages':
            value = (value == 'true')
        setattr(cfg, name, value)
    return cfg


def resolve_venv_python(root):
    python_exe = os.path.basename(sys.executable)
    if os.name == "nt":
        return os.path.join(root, 'Scripts', python_exe)
    else:
        return os.path.join(root, 'bin', python_exe)


class VirtualEnvironment(object):

    def __init__(self, python, root=None, *,
                 inherit_environ=None,
                 name=None,
                 ):
        self.python = python
        self._info = _pythoninfo.get_info(python or sys.executable)

        self.inherit_environ = inherit_environ or None
        self._name = name or None
        self._venv_path = root or None
        self._prepared = False

    @property
    def name(self):
        if self._name is None:
            from .run import get_run_id
            runid = get_run_id(self.python)
            self._name = runid.name
        return self._name

    @property
    def _env(self):
        # Restrict the env we use.
        env = {}
        copy_env = ["PATH", "HOME", "TEMP", "COMSPEC", "SystemRoot"]
        if self.inherit_environ:
            copy_env.extend(self.inherit_environ)
        for name in copy_env:
            if name in os.environ:
                env[name] = os.environ[name]
        return env

    def run_cmd_nocheck(self, cmd, verbose=True):
        cmd_str = ' '.join(map(shell_quote, cmd))
        if verbose:
            print("Execute: %s" % cmd_str)

        # Explicitly flush standard streams, required if streams are buffered
        # (not TTY) to write lines in the expected order
        sys.stdout.flush()
        sys.stderr.flush()

        env = self._env
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

    def _create_venv(self):
        venv_path = self.get_path()
        argv = [self.python, '-m', 'venv', '--without-pip', venv_path]
        try:
            ec = self.run_cmd_nocheck(argv)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise
            print("%s command failed: command not found" % ' '.join(cmd))
            ec = 127
        else:
            print("%s command failed" % ' '.join(argv))
            _utils.safe_rmtree(venv_path)
        if ec != 0:
            sys.exit(1)

        # Now install pip.
        venv_python = resolve_venv_python(venv_path)
        ec, _, _ = _pip.install_pip(
            venv_python,
            info=self._info,
            downloaddir=venv_path,
            env=self._env,
        )
        if ec != 0:
            print("failed to install pip")
            return False
        elif not _pip.is_pip_installed(venv_python, env=self._env):
            print("ERROR: pip doesn't work")
            return False
        return True

    def exists(self):
        venv_python = resolve_venv_python(self.get_path())
        return os.path.exists(venv_python)

    def prepare(self, install=True):
        venv_path = self.get_path()
        venv_python = resolve_venv_python(venv_path)
        print("Installing the virtual environment %s" % venv_path)
        if self._prepared or (self._prepared is None and not install):
            print('(already installed)')
            return

        if not self._prepared:
            # parse requirements
            basereqs = Requirements.from_file(REQUIREMENTS_FILE, ['psutil'])

            # Upgrade pip
            ec, _, _ = _pip.upgrade_pip(
                venv_python,
                info=self._info,
                env=self._env,
                installer=True,
            )
            if ec != 0:
                sys.exit(ec)

        # XXX not for benchmark venvs
        if install:
            # XXX
            # install pyperformance inside the virtual environment
            if pyperformance.is_installed():
                root_dir = os.path.dirname(pyperformance.PKG_ROOT)
                ec, _, _ = _pip.install_editable(
                    root_dir,
                    python=self._info,
                    env=self._env,
                )
            else:
                version = pyperformance.__version__
                ec, _, _ = _pip.install_requirements(
                    f'pyperformance=={version}',
                    python=self._info,
                    env=self._env,
                )
            if ec != 0:
                sys.exit(ec)
            self._prepared = True
        else:
            self._prepared = None

        # Display the pip version
        _pip.run_pip('--version', python=venv_python, env=self._env)

        # Dump the package list and their versions: pip freeze
        _pip.run_pip('freeze', python=venv_python, env=self._env)

    def create(self, install=True):
        venv_path = self.get_path()
        print("Creating the virtual environment %s" % venv_path)
        if self.exists():
            raise Exception(f'virtual environment {venv_path} already exists')
        try:
            self._create_venv()
            self.prepare(install)
        except BaseException:
            print()
            _utils.safe_rmtree(venv_path)
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
                # XXX what about psutil?

        if not requirements:
            print('(nothing to install)')
        else:
            self.prepare(install=bench is None)

            # install requirements
            reqs = list(requirements.iter_non_optional())
            ec, _, _ = _pip.install_requirements(
                *reqs,
                python=self._info,
                env=self._env,
                upgrade=False,
            )
            if ec:
                if exitonerror:
                    sys.exit(ec)
                raise RequirementsInstallationFailedError(reqs)

            # install optional requirements
            for req in requirements.iter_optional():
                ec, _, _ = _pip.install_requirements(
                    req,
                    python=self._info,
                    env=self._env,
                    upgrade=True,
                )
                if ec != 0:
                    print("WARNING: failed to install %s" % req)
                    print()

        # Dump the package list and their versions: pip freeze
        _pip.run_pip('freeze', python=venv_python, env=self._env)

        return requirements


def cmd_venv(options, benchmarks=None):
    venv = VirtualEnvironment(
        options.python,
        options.venv,
        inherit_environ=options.inherit_environ,
    )
    venv_path = venv.get_path()
    exists = venv.exists()

    action = options.venv_action
    if action == 'create':
        requirements = Requirements.from_benchmarks(benchmarks)
        if exists:
            print("The virtual environment %s already exists" % venv_path)
        venv.ensure()
        venv.install_reqs(requirements, exitonerror=True)
        if not exists:
            print("The virtual environment %s has been created" % venv_path)

    elif action == 'recreate':
        requirements = Requirements.from_benchmarks(benchmarks)
        if exists:
            venv_python = resolve_venv_python(self.get_path())
            if venv_python == sys.executable:
                print("The virtual environment %s already exists" % venv_path)
                print("(it matches the currently running Python executable)")
                venv.ensure()
                venv.install_reqs(requirements, exitonerror=True)
            else:
                print("The virtual environment %s already exists" % venv_path)
                _utils.safe_rmtree(venv_path)
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
        if _utils.safe_rmtree(venv_path):
            print("The virtual environment %s has been removed" % venv_path)
        else:
            print("The virtual environment %s does not exist" % venv_path)

    else:
        # show command
        text = "Virtual environment path: %s" % venv_path
        if exists:
            text += " (already created)"
        else:
            text += " (not created yet)"
        print(text)

        if not exists:
            print()
            print("Command to create it:")
            cmd = "%s -m pyperformance venv create" % options.python
            if options.venv:
                cmd += " --venv=%s" % options.venv
            print(cmd)
