import os
import os.path
import sys

import pyperformance
from . import _utils, _pythoninfo, _pip, _venv


REQUIREMENTS_FILE = os.path.join(pyperformance.DATA_DIR, 'requirements.txt')


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


# This is used by the hg_startup benchmark.
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


class VenvForBenchmarks(_venv.VirtualEnvironment):

    @classmethod
    def create(cls, root=None, python=None, *,
               inherit_environ=None,
               install=True,
               ):
        env = _get_envvars(inherit_environ)
        try:
            self = super().create(root, python, env=env, withpip=False)
        except _venv.VenvCreationFailedError as exc:
            print(f'ERROR: {exc}')
            sys.exit(1)
        self.inherit_environ = inherit_environ

        try:
            self.ensure_pip()
        except _venv.VenvPipInstallFailedError as exc:
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
        if _venv.venv_exists(root):
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
            except _venv.RequirementsInstallationFailedError:
                if exitonerror:
                    sys.exit(1)
                raise  # re-raise

            # install optional requirements
            for req in requirements.iter_optional():
                try:
                    super().ensure_reqs(req, upgrade=True)
                except _venv.RequirementsInstallationFailedError:
                    print("WARNING: failed to install %s" % req)
                    print()

        # Dump the package list and their versions: pip freeze
        _pip.run_pip('freeze', python=self.python, env=self._env)

        return requirements


def cmd_venv(options, benchmarks=None):
    if not options.venv:
        info = _pythoninfo.get_info(options.python)
        root = _venv.get_venv_root(python=info)
    else:
        root = options.venv
        venv_python = _venv.resolve_venv_python(root)
        if os.path.exists(venv_python):
            info = _pythoninfo.get_info(venv_python)
        else:
            info = None
    exists = _venv.venv_exists(root)

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
            venv_python = _venv.resolve_venv_python(root)
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
