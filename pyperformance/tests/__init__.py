import errno
import os
import os.path
import shlex
import shutil
import subprocess
import sys
import tempfile


TESTS_ROOT = os.path.realpath(os.path.dirname(__file__))
DATA_DIR = os.path.join(TESTS_ROOT, 'data')
REPO_ROOT = os.path.dirname(os.path.dirname(TESTS_ROOT))


def run_cmd(cmd, *args, capture=None, onfail='exit', verbose=True):
    # XXX Optionally write the output to a file.
    argv = (cmd,) + args
    if not all(a and isinstance(a, str) for a in argv):
        raise TypeError(f'all args must be non-empty strings, got {argv}')
    argv_str = ' '.join(shlex.quote(a) for a in argv)

    kwargs = dict(
        cwd=REPO_ROOT,
    )
    if capture in ('both', 'combined', 'stdout'):
        kwargs['stdout'] = subprocess.PIPE
    if capture in ('both', 'stderr'):
        kwargs['stderr'] = subprocess.PIPE
    elif capture == 'combined':
        kwargs['stderr'] = subprocess.STDOUT
    if capture:
        kwargs['encoding'] = 'utf-8'

    if verbose:
        print(f"(tests) Execute: {argv_str}", flush=True)
    proc = subprocess.run(argv, **kwargs)

    exitcode = proc.returncode
    if exitcode:
        if onfail == 'exit':
            sys.exit(exitcode)
        elif onfail == 'raise':
            raise Exception(f'"{argv_str}" failed (exitcode {exitcode})')
        elif onfail is not None:
            raise NotImplementedError(repr(onfail))
    if 'stdout' not in kwargs or 'stderr' not in kwargs:
        print("", flush=True)

    return exitcode, proc.stdout, proc.stderr


def resolve_venv_python(venv):
    if os.name == "nt":
        basename = os.path.basename(sys.executable)
        venv_python = os.path.join(venv, 'Scripts', basename)
    else:
        venv_python = os.path.join(venv, 'bin', 'python3')
    return venv_python


class CleanupFile:
    def __init__(self, filename):
        self.filename = filename
    def __repr__(self):
        return f'{type(self).__name__}({self.filename!r})'
    def __str__(self):
        return self.filename
    def __enter__(self):
        return self.filename
    def __exit__(self, *args):
        self.cleanup()
    def cleanup(self):
        try:
            os.unlink(self.filename)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise


#############################
# fixtures and mixins

class Compat:
    """A mixin that lets older Pythons use newer unittest features."""

    if sys.version_info < (3, 8):
        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            cls._cleanups = []

        @classmethod
        def tearDownClass(cls):
            super().tearDownClass()
            for cleanup in cls._cleanups:
                cleanup()

        @classmethod
        def addClassCleanup(cls, cleanup):
            cls._cleanups.append(cleanup)


class Resources(Compat):
    """A mixin that can create resources."""

    @classmethod
    def resolve_tmp(cls, *relpath, unique=False):
        try:
            tmpdir = cls._tmpdir
        except AttributeError:
            tmpdir = cls._tmpdir = tempfile.mkdtemp()
            cls.addClassCleanup(lambda: shutil.rmtree(tmpdir))
        if unique:
            tmpdir = tempfile.mkdtemp(dir=tmpdir)
        return os.path.join(tmpdir, *relpath)

    def venv(self, python=sys.executable):
        tmpdir = tempfile.mkdtemp()
        venv = os.path.join(tmpdir, 'venv')
        run_cmd(python or sys.executable, '-u', '-m', 'venv', venv)
        self.addCleanup(lambda: shutil.rmtree(tmpdir))
        return venv, resolve_venv_python(venv)


#############################
# functional tests

class Functional(Resources):
    """A mixin for functional tests."""

    ENVVAR = 'PYPERFORMANCE_TESTS_VENV'

    @classmethod
    def ensure_venv(cls):
        if getattr(cls, '_tests_venv', None):
            # ensure_venv() already ran.
            return

        if sys.prefix != sys.exec_prefix:
            # We are already running in a venv and assume it is ready.
            cls._tests_venv = sys.prefix
            cls._venv_python = sys.executable
            return

        print('#'*40)
        print('# creating a venv')
        print('#'*40)
        print()

        cls._tests_venv = os.environ.get(cls.ENVVAR)
        if not cls._tests_venv:
            cls._tests_venv = cls.resolve_tmp('venv')
        venv_python = resolve_venv_python(cls._tests_venv)
        if os.path.exists(venv_python):
            return

        # Create the venv and update it.
        # XXX Ignore the output (and optionally log it).
        run_cmd(sys.executable, '-u', '-m', 'venv', cls._tests_venv)
        cls._venv_python = venv_python
        cls.run_pip('install', '--upgrade', 'pip')
        cls.run_pip('install', '--upgrade', 'setuptools', 'wheel')

        print('#'*40)
        print('# DONE: creating a venv')
        print('#'*40)
        print()

    @classmethod
    def run_python(cls, *args, require_venv=True, **kwargs):
        python = getattr(cls, '_venv_python', None)
        if not python:
            if require_venv:
                raise Exception('cls.ensure_venv() must be called first')
            python = sys.executable
        # We always use unbuffered stdout/stderr to simplify capture.
        return run_cmd(python, '-u', *args, **kwargs)

    @classmethod
    def run_module(cls, module, *args, **kwargs):
        return cls.run_python('-m', module, *args, **kwargs)

    @classmethod
    def run_pip(cls, *args, **kwargs):
        return cls.run_module('pip', *args, **kwargs)
