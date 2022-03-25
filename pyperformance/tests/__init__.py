import contextlib
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


@contextlib.contextmanager
def temporary_file(**kwargs):
    tmp_filename = tempfile.mktemp(**kwargs)
    try:
        yield tmp_filename
    finally:
        try:
            os.unlink(tmp_filename)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise


def run_cmd(*argv, capture=None, onfail='exit', verbose=True):
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
        argv_str = ' '.join(shlex.quote(a) for a in argv)
        print(f"(tests) Execute: {argv_str}", flush=True)
    proc = subprocess.run(argv, **kwargs)

    exitcode = proc.returncode
    if exitcode:
        if onfail == 'exit':
            sys.exit(exitcode)
        elif onfail is not None:
            raise NotImplementedError(repr(onfail))
    if 'stdout' not in kwargs or 'stderr' not in kwargs:
        print("", flush=True)

    return exitcode, proc.stdout, proc.stderr


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
    def resolve_tmp(cls, *relpath):
        try:
            tmpdir = cls._tmpdir
        except AttributeError:
            tmpdir = cls._tmpdir = tempfile.mkdtemp()
            cls.addClassCleanup(lambda: shutil.rmtree(tmpdir))
        return os.path.join(tmpdir, *relpath)

    def venv(self, python=sys.executable):
        tmpdir = tempfile.mkdtemp()
        venv = os.path.join(tmpdir, 'venv')
        run_cmd(python or sys.executable, '-u', '-m', 'venv', venv)
        self.addCleanup(lambda: shutil.rmtree(tmpdir))
        return venv, resolve_venv_python(venv)


def resolve_venv_python(venv):
    if os.name == "nt":
        basename = os.path.basename(sys.executable)
        venv_python = os.path.join(venv, 'Scripts', basename)
    else:
        venv_python = os.path.join(venv, 'bin', 'python3')
    return venv_python


#############################
# functional tests

class Functional:
    """A mixin for functional tests."""

    # XXX Disallow multi-proc or threaded test runs?
    _TMPDIR = None
    _VENV = None
    _COUNT = 0

    maxDiff = 80 * 100

    @classmethod
    def setUpClass(cls):
        tmpdir = Functional._TMPDIR
        if tmpdir is None:
            tmpdir = Functional._TMPDIR = tempfile.mkdtemp()
            venv = Functional._VENV = os.path.join(tmpdir, 'venv')
            run_cmd(
                sys.executable, '-u', '-m', 'pyperformance',
                'venv', 'create',
                '-b', 'all',
                '--venv', venv,
            )

            egg_info = "pyperformance.egg-info"
            print(f"(tests) Remove directory {egg_info}", flush=True)
            try:
                shutil.rmtree(egg_info)
            except FileNotFoundError:
                pass
        Functional._COUNT += 1
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        tmpdir = Functional._TMPDIR
        venv = Functional._VENV
        if Functional._COUNT == 1:
            assert venv
            run_cmd(
                sys.executable, '-u', '-m', 'pyperformance',
                'venv', 'remove',
                '--venv', venv,
            )
            if os.path.exists(tmpdir):
                shutil.rmtree(tmpdir)

    @property
    def venv_python(self):
        return resolve_venv_python(self._VENV)
