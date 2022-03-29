import errno
import importlib.util
import os
import os.path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest


TESTS_ROOT = os.path.realpath(os.path.dirname(__file__))
DATA_DIR = os.path.join(TESTS_ROOT, 'data')
REPO_ROOT = os.path.dirname(os.path.dirname(TESTS_ROOT))
DEV_SCRIPT = os.path.join(REPO_ROOT, 'dev.py')


def run_cmd(cmd, *args, capture=None, onfail='exit', verbose=True):
    # XXX Optionally write the output to a file.
    argv = (cmd,) + args
    if not all(a and isinstance(a, str) for a in argv):
        raise TypeError(f'all args must be non-empty strings, got {argv}')
    argv_str = ' '.join(shlex.quote(a) for a in argv)

    kwargs = dict(
        cwd=REPO_ROOT,
    )
    if capture is True:
        capture = 'both'
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


def _resolve_venv_python(venv):
    if os.name == "nt":
        basename = os.path.basename(sys.executable)
        venv_python = os.path.join(venv, 'Scripts', basename)
    else:
        venv_python = os.path.join(venv, 'bin', 'python3')
    return venv_python


def create_venv(root=None, python=sys.executable, *, verbose=False):
    if not root:
        tmpdir = tempfile.mkdtemp()
        root = os.path.join(tmpdir, 'venv')
        cleanup = (lambda: shutil.rmtree(tmpdir))
    else:
        cleanup = (lambda: None)
    run_cmd(
        python or sys.executable, '-m', 'venv', root,
        capture=not verbose,
        onfail='raise',
        verbose=verbose,
    )
    return root, _resolve_venv_python(root), cleanup


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
# testing fixtures, mixins, and helpers

def apply_to_test_methods(cls, decorator):
    for name, func in vars(cls).items():
        if not name.startswith('test_'):
            continue
        func = decorator(func)
        setattr(cls, name, func)


def mark(label, func=None):
    """Mark the function/class with the given label.

    This may be used as a decorator.
    """
    if func is None:
        def decorator(func):
            return mark(label, func)
        return decorator
    if isinstance(func, type):
        cls = func
        apply_to_test_methods(cls, mark(label))
        return cls
    try:
        func._pyperformance_test_labels.append(label)
    except AttributeError:
        func._pyperformance_test_labels = [label]
    return func


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


#############################
# functional tests

CPYTHON_ONLY = unittest.skipIf(
    sys.implementation.name != 'cpython',
    'CPython-only',
)
NON_WINDOWS_ONLY = unittest.skipIf(os.name == 'nt', 'skipping Windows')

# XXX Provide a way to run slow tests.
SLOW = (lambda f:
            unittest.skip('way too slow')(
                mark('slow', f)))


class Functional(Compat):
    """A mixin for functional tests.

    In this context, "functional" means the test touches the filesystem,
    uses the network, creates subprocesses, etc.  This contrasts with
    true "unit" tests, which are constrained strictly to code execution.
    """

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

        cls._tests_venv = cls._resolve_tests_venv()
        venv_python = _resolve_venv_python(cls._tests_venv)
        if os.path.exists(venv_python):
            cls._venv_python = venv_python
            return

        print('#'*40)
        print('# creating a venv')
        print('#'*40)
        print()

        # Create the venv and update it.
        # XXX Ignore the output (and optionally log it).
        create_venv(cls._tests_venv, verbose=True)
        cls._venv_python = venv_python
        cls.run_pip('install', '--upgrade', 'pip')
        cls.run_pip('install', '--upgrade', 'setuptools', 'wheel')

        print('#'*40)
        print('# DONE: creating a venv')
        print('#'*40)
        print()

    @classmethod
    def _resolve_tests_venv(cls):
        root = os.environ.get('PYPERFORMANCE_TESTS_VENV')
        if not root:
            root = '<reuse>'
        elif not root.startswith('<') and not root.endswith('>'):
            # The user provided an actual root dir.
            return root

        if root == '<temp>':
            # The user is forcing a temporary venv.
            return cls.resolve_tmp('venv')
        elif root == '<fresh>':
            # The user is forcing a fresh venv.
            fresh = True
        elif root == '<reuse>':
            # This is the default.
            fresh = False
        else:
            raise NotImplementedError(repr(root))

        # Resolve the venv root to re-use.
        spec = importlib.util.spec_from_file_location('dev', DEV_SCRIPT)
        dev = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dev)
        root = dev.resolve_venv_root('tests')

        if fresh:
            if os.path.exists(root):
                print('(refreshing existing venv)')
                print()
            try:
                shutil.rmtree(root)
            except FileNotFoundError:
                pass
        return root
