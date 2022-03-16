import contextlib
import errno
import os
import os.path
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


def run_cmd(*argv):
    print(f"(tests) Execute: {' '.join(argv)}", flush=True)
    proc = subprocess.Popen(argv, cwd=REPO_ROOT)
    try:
        proc.wait()
    except:   # noqa
        proc.kill()
        proc.wait()
        raise
    sys.stdout.flush()
    exitcode = proc.returncode
    if exitcode:
        sys.exit(exitcode)
    print("", flush=True)


class Resources:
    """A mixin that can create resources."""

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

    def run_pyperformance(self, cmd, *args):
        run_cmd(
            sys.executable, '-u', '-m', 'pyperformance',
            cmd, *args,
        )
