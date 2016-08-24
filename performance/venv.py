from __future__ import division, with_statement, print_function, absolute_import

import hashlib
import os
import platform
import shutil
import subprocess
import sys

try:
    # Python 3.3
    from shutil import which
except ImportError:
    # Backport shutil.which() from Python 3.6
    def which(cmd, mode=os.F_OK | os.X_OK, path=None):
        """Given a command, mode, and a PATH string, return the path which
        conforms to the given mode on the PATH, or None if there is no such
        file.

        `mode` defaults to os.F_OK | os.X_OK. `path` defaults to the result
        of os.environ.get("PATH"), or can be overridden with a custom search
        path.

        """
        # Check that a given file can be accessed with the correct mode.
        # Additionally check that `file` is not a directory, as on Windows
        # directories pass the os.access check.
        def _access_check(fn, mode):
            return (os.path.exists(fn) and os.access(fn, mode)
                    and not os.path.isdir(fn))

        # If we're given a path with a directory part, look it up directly rather
        # than referring to PATH directories. This includes checking relative to the
        # current directory, e.g. ./script
        if os.path.dirname(cmd):
            if _access_check(cmd, mode):
                return cmd
            return None

        if path is None:
            path = os.environ.get("PATH", os.defpath)
        if not path:
            return None
        path = path.split(os.pathsep)

        if sys.platform == "win32":
            # The current directory takes precedence on Windows.
            if not os.curdir in path:
                path.insert(0, os.curdir)

            # PATHEXT is necessary to check on Windows.
            pathext = os.environ.get("PATHEXT", "").split(os.pathsep)
            # See if the given file matches any of the expected path extensions.
            # This will allow us to short circuit when given "python.exe".
            # If it does match, only test that one, otherwise we have to try
            # others.
            if any(cmd.lower().endswith(ext.lower()) for ext in pathext):
                files = [cmd]
            else:
                files = [cmd + ext for ext in pathext]
        else:
            # On other platforms you don't have things like PATHEXT to tell you
            # what file suffixes are executable, so just pass on cmd as-is.
            files = [cmd]

        seen = set()
        for dir in path:
            normdir = os.path.normcase(dir)
            if not normdir in seen:
                seen.add(normdir)
                for thefile in files:
                    name = os.path.join(dir, thefile)
                    if _access_check(name, mode):
                        return name
        return None


ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))


def python_implementation():
    if hasattr(sys, 'implementation'):
        # PEP 421, Python 3.3
        name = sys.implementation.name
    else:
        name = platform.python_implementation()
    return name.lower()


# FIXME: use version_info format: (int, int)
def interpreter_version(python, _cache={}):
    """Return the interpreter version for the given Python interpreter.
    *python* is the base command (as a list) to execute the interpreter.
    """
    key = tuple(python)
    try:
        return _cache[key]
    except KeyError:
        pass
    code = """import sys; print('.'.join(map(str, sys.version_info[:2])))"""
    subproc = subprocess.Popen(python + ['-c', code],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    out, err = subproc.communicate()
    if subproc.returncode != 0:
        raise RuntimeError("Child interpreter died: " + err.decode())
    version = out.decode().strip()
    if len(version) != 3:
        raise RuntimeError("Strange version printed: %s" % version)
    _cache[key] = version
    return version


def get_virtualenv():
    bin_path = os.path.dirname(sys.executable)
    if not os.path.isabs(bin_path):
        print("ERROR: Python executable path is not absolute: %s"
              % sys.executable)
        sys.exit(1)
    if not os.path.exists(os.path.join(bin_path, 'activate')):
        print("ERROR: Unable to get the virtual environment of "
              "the Python executable %s" % sys.executable)
        sys.exit(1)

    venv = os.path.dirname(bin_path)
    venv = os.path.realpath(venv)
    return venv


def run_cmd(cmd):
    print("Execute: %s" % ' '.join(cmd))
    proc = subprocess.Popen(cmd)
    try:
        proc.wait()
    except:
        proc.kill()
        proc.wait()
        raise
    exitcode = proc.returncode
    if exitcode:
        sys.exit(exitcode)
    print("")


def virtualenv_name():
    data = sys.executable + sys.version

    version = sys.version_info
    implementation = python_implementation()

    if not isinstance(data, bytes):
        data = data.encode('utf-8')
    filename = os.path.join(ROOT_DIR, 'performance', 'requirements.txt')
    with open(filename, 'rb') as fp:
        data += fp.read()
    sha1 = hashlib.sha1(data).hexdigest()

    return ('%s%s.%s-%s'
            % (implementation, version.major, version.minor, sha1[:12]))


def create_virtualenv():
    venv_name = virtualenv_name()
    venv_path = os.path.join('venv', venv_name)
    if os.name == "nt":
        python_executable = os.path.basename(sys.executable)
        venv_python = os.path.join(venv_path, 'Scripts', python_executable)
    else:
        venv_python = os.path.join(venv_path, 'bin', 'python')
    if os.path.exists(venv_path):
        return venv_python

    print("Creating the virtual environment %s" % venv_path)
    try:
        if sys.version_info >= (3, 3):
            cmd = [sys.executable, '-m', 'venv', venv_path]
        else:
            cmd = ['virtualenv', '-p', sys.executable, venv_path]
        run_cmd(cmd)

        # upgrade setuptools and pip to make sure that they support environment
        # marks in requirements.txt
        cmd = [venv_python, '-m', 'pip',
               'install', '-U', 'setuptools>=18.5', 'pip>=6.0']
        run_cmd(cmd)

        requirements = os.path.join(ROOT_DIR, 'performance', 'requirements.txt')
        cmd = [venv_python, '-m', 'pip', 'install', '-r', requirements]
        run_cmd(cmd)

        cmd = [venv_python, '-m', 'pip', 'install', '-e', ROOT_DIR]
        run_cmd(cmd)
    except:
        if os.path.exists(venv_path):
            print("ERROR: Remove virtual environment %s" % venv_path)
            shutil.rmtree(venv_path)
        raise

    return venv_python


def exec_in_virtualenv(options):
    venv_python = create_virtualenv()
    args = [venv_python] + sys.argv + ["--inside-venv"]
    os.execv(args[0], args)
