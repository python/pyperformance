import errno
import os
import os.path
import subprocess
import sys
import types
from shlex import quote as shell_quote

import pyperformance
from . import _utils, _pythoninfo, _pip


class VenvCreationFailedError(Exception):
    def __init__(self, root, exitcode, already_existed):
        super().__init__(f'venv creation failed ({root})')
        self.root = root
        self.exitcode = exitcode
        self.already_existed = already_existed


class VenvPipInstallFailedError(Exception):
    def __init__(self, root, exitcode, msg=None):
        super().__init__(msg or f'failed to install pip in venv {root}')
        self.root = root
        self.exitcode = exitcode


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
    python_exe = 'python'
    if sys.executable.endswith('.exe'):
        python_exe += '.exe'
    if os.name == "nt":
        return os.path.join(root, 'Scripts', python_exe)
    else:
        return os.path.join(root, 'bin', python_exe)


def get_venv_root(name=None, venvsdir='venv', *, python=sys.executable):
    """Return the venv root to use for the given name (or given python)."""
    if not name:
        from .run import get_run_id
        runid = get_run_id(python)
        name = runid.name
    return os.path.abspath(
        os.path.join(venvsdir or '.', name),
    )


def venv_exists(root):
    venv_python = resolve_venv_python(root)
    return os.path.exists(venv_python)


def create_venv(root, python=sys.executable, *,
                env=None,
                downloaddir=None,
                withpip=True,
                cleanonfail=True
                ):
    """Create a new venv at the given root, optionally installing pip."""
    already_existed = os.path.exists(root)
    if withpip:
        args = ['-m', 'venv', root]
    else:
        args = ['-m', 'venv', '--without-pip', root]
    ec, _, _ = _utils.run_python(*args, python=python, env=env)
    if ec != 0:
        if cleanonfail and not already_existed:
            _utils.safe_rmtree(root)
        raise VenvCreationFailedError(root, ec, already_existed)
    return resolve_venv_python(root)


class VirtualEnvironment:

    _env = None

    @classmethod
    def create(cls, root=None, python=sys.executable, **kwargs):
        if not python or isinstance(python, str):
            info = _pythoninfo.get_info(python)
        else:
            info = python
        if not root:
            root = get_venv_root(python=info)

        print("Creating the virtual environment %s" % root)
        if venv_exists(root):
            raise Exception(f'virtual environment {root} already exists')

        try:
            venv_python = create_venv(
                root,
                info,
                **kwargs
            )
        except BaseException:
            _utils.safe_rmtree(root)
            raise  # re-raise
        self = cls(root, base=info)
        self._python = venv_python
        return self

    @classmethod
    def ensure(cls, root, python=None, **kwargs):
        if venv_exists(root):
            return cls(root)
        else:
            return cls.create(root, python, **kwargs)

    def __init__(self, root, *, base=None):
        assert os.path.exists(resolve_venv_python(root)), root
        self.root = root
        if base:
            self._base = base

    @property
    def python(self):
        try:
            return self._python
        except AttributeError:
            if not getattr(self, '_info', None):
                return resolve_venv_python(self.root)
            self._python = self.info.sys.executable
            return self._python

    @property
    def info(self):
        try:
            return self._info
        except AttributeError:
            try:
                python = self._python
            except AttributeError:
                python = resolve_venv_python(self.root)
            self._info = _pythoninfo.get_info(python)
            return self._info

    @property
    def base(self):
        try:
            return self._base
        except AttributeError:
            base_exe = self.info.sys._base_executable
            if not base_exe and base_exe != self.info.sys.executable:
                # XXX Use read_venv_config().
                raise NotImplementedError
                base_exe = ...
            self._base = _pythoninfo.get_info(base_exe)
            return self._base

    def ensure_pip(self, downloaddir=None):
        ec, _, _ = _pip.install_pip(
            self.python,
            info=self.info,
            downloaddir=downloaddir or self.root,
            env=self._env,
        )
        if ec != 0:
            raise VenvPipInstallFailedError(root, ec)
        elif not _pip.is_pip_installed(self.python, env=self._env):
            raise VenvPipInstallFailedError(root, 0, "pip doesn't work")

    def ensure_reqs(self, *reqs, upgrade=True):
        print("Installing requirements into the virtual environment %s" % self.root)
        ec, _, _ = _pip.install_requirements(
            *reqs,
            python=self.python,
            env=self._env,
            upgrade=upgrade,
        )
        if ec:
            raise RequirementsInstallationFailedError(reqs)


#######################################
# pyperformance-specific venvs

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


def _get_envvars(inherit=None):
    # Restrict the env we use.
    env = {}
    copy_env = ["PATH", "HOME", "TEMP", "COMSPEC", "SystemRoot"]
    if inherit:
        copy_env.extend(inherit)
    for name in copy_env:
        if name in os.environ:
            env[name] = os.environ[name]
    return env


class VenvForBenchmarks(VirtualEnvironment):

    @classmethod
    def create(cls, root=None, python=None, *,
               inherit_environ=None,
               install=True,
               ):
        env = _get_envvars(inherit_environ)
        try:
            self = super().create(root, python, env=env, withpip=False)
        except VenvCreationFailedError as exc:
            print(f'ERROR: {exc}')
            sys.exit(1)
        self.inherit_environ = inherit_environ

        try:
            self.ensure_pip()
        except VenvPipInstallFailedError as exc:
            print(f'ERROR: {exc}')
            _utils.safe_rmtree(self.root)
            sys.exit(1)
        except BaseException:
            _utils.safe_rmtree(self.root)
            raise

        try:
            self.prepare(install)
        except BaseException:
            print()
            _utils.safe_rmtree(venv.root)
            raise

        return self

    @classmethod
    def ensure(cls, root, python=None, *,
               refresh=True,
               install=True,
               **kwargs
               ):
        if venv_exists(root):
            self = super().ensure(root)
            if refresh:
                self.prepare(install)
            return self
        else:
            return cls.create(root, python, install=install, **kwargs)

    def __init__(self, root, *, base=None, inherit_environ=None):
        super().__init__(root, base=base)
        self.inherit_environ = inherit_environ or None
        self._prepared = False

    @property
    def _env(self):
        # Restrict the env we use.
        return _get_envvars(self.inherit_environ)

    def prepare(self, install=True):
        print("Installing the virtual environment %s" % self.root)
        if self._prepared or (self._prepared is None and not install):
            print('(already installed)')
            return

        if not self._prepared:
            # parse requirements
            basereqs = Requirements.from_file(REQUIREMENTS_FILE, ['psutil'])

            # Upgrade pip
            ec, _, _ = _pip.upgrade_pip(
                self.python,
                info=self.info,
                env=self._env,
                installer=True,
            )
            if ec != 0:
                sys.exit(ec)

        # XXX not for benchmark venvs
        if install:
            # install pyperformance inside the virtual environment
            # XXX This isn't right...
            if pyperformance.is_installed():
                root_dir = os.path.dirname(pyperformance.PKG_ROOT)
                ec, _, _ = _pip.install_editable(
                    root_dir,
                    python=self.info,
                    env=self._env,
                )
            else:
                version = pyperformance.__version__
                ec, _, _ = _pip.install_requirements(
                    f'pyperformance=={version}',
                    python=self.info,
                    env=self._env,
                )
            if ec != 0:
                sys.exit(ec)
            self._prepared = True
        else:
            self._prepared = None

        # Display the pip version
        _pip.run_pip('--version', python=self.python, env=self._env)

        # Dump the package list and their versions: pip freeze
        _pip.run_pip('freeze', python=self.python, env=self._env)

    def ensure_reqs(self, requirements=None, *, exitonerror=False):
        print("Installing requirements into the virtual environment %s" % self.root)

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
            try:
                super().ensure_reqs(
                    *requirements.iter_non_optional(),
                    upgrade=False,
                )
            except RequirementsInstallationFailedError:
                if exitonerror:
                    sys.exit(1)
                raise  # re-raise

            # install optional requirements
            for req in requirements.iter_optional():
                try:
                    super().ensure_reqs(req, upgrade=True)
                except RequirementsInstallationFailedError:
                    print("WARNING: failed to install %s" % req)
                    print()

        # Dump the package list and their versions: pip freeze
        _pip.run_pip('freeze', python=self.python, env=self._env)

        return requirements


def cmd_venv(options, benchmarks=None):
    if not options.venv:
        info = _pythoninfo.get_info(options.python)
        root = get_venv_root(python=info)
    else:
        root = options.venv
        venv_python = resolve_venv_python(root)
        if os.path.exists(venv_python):
            info = _pythoninfo.get_info(venv_python)
        else:
            info = None
    exists = venv_exists(root)

    action = options.venv_action
    if action == 'create':
        requirements = Requirements.from_benchmarks(benchmarks)
        if exists:
            print("The virtual environment %s already exists" % root)
        venv = VenvForBenchmarks.ensure(
            root,
            info,
            inherit_environ=options.inherit_environ,
        )
        venv.ensure_reqs(requirements, exitonerror=True)
        if not exists:
            print("The virtual environment %s has been created" % root)

    elif action == 'recreate':
        requirements = Requirements.from_benchmarks(benchmarks)
        if exists:
            venv_python = resolve_venv_python(root)
            if venv_python == sys.executable:
                print("The virtual environment %s already exists" % root)
                print("(it matches the currently running Python executable)")
                venv = VenvForBenchmarks.ensure(
                    root,
                    info,
                    inherit_environ=options.inherit_environ,
                )
                venv.ensure_reqs(requirements, exitonerror=True)
            else:
                print("The virtual environment %s already exists" % root)
                _utils.safe_rmtree(root)
                print("The old virtual environment %s has been removed" % root)
                print()
                venv = VenvForBenchmarks.ensure(
                    root,
                    info,
                    inherit_environ=options.inherit_environ,
                )
                venv.ensure_reqs(requirements, exitonerror=True)
                print("The virtual environment %s has been recreated" % root)
        else:
            venv = VenvForBenchmarks.create(
                root,
                info,
                inherit_environ=options.inherit_environ,
            )
            venv.ensure_reqs(requirements, exitonerror=True)
            print("The virtual environment %s has been created" % root)

    elif action == 'remove':
        if _utils.safe_rmtree(root):
            print("The virtual environment %s has been removed" % root)
        else:
            print("The virtual environment %s does not exist" % root)

    else:
        # show command
        text = "Virtual environment path: %s" % root
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
