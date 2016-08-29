from __future__ import division, with_statement, print_function, absolute_import

import errno
import os
import platform
import shutil
import subprocess
import sys
import textwrap

import performance

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


def run_cmd_nocheck(cmd):
    print("Execute: %s" % ' '.join(cmd))
    proc = subprocess.Popen(cmd)
    try:
        proc.wait()
    except:
        proc.kill()
        proc.wait()
        raise

    return proc.returncode


def run_cmd(cmd):
    exitcode = run_cmd_nocheck(cmd)
    if exitcode:
        sys.exit(exitcode)
    print("")


def virtualenv_path(options):
    if options.venv:
        return options.venv

    script = textwrap.dedent("""
        import hashlib
        import platform
        import sys

        performance_version = sys.argv[1]
        requirements = sys.argv[2]

        data = performance_version + sys.executable + sys.version

        pyver= sys.version_info

        if hasattr(sys, 'implementation'):
            # PEP 421, Python 3.3
            implementation = sys.implementation.name
        else:
            implementation = platform.python_implementation()
        implementation = implementation.lower()

        if not isinstance(data, bytes):
            data = data.encode('utf-8')
        with open(requirements, 'rb') as fp:
            data += fp.read()
        sha1 = hashlib.sha1(data).hexdigest()

        name = ('%s%s.%s-%s'
                % (implementation, pyver.major, pyver.minor, sha1[:12]))
        print(name)
    """)

    python = options.python
    requirements = os.path.join(ROOT_DIR, 'performance', 'requirements.txt')
    cmd = (python, '-c', script, performance.__version__, requirements)
    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            universal_newlines=True)
    stdout = proc.communicate()[0]
    if proc.returncode:
        print("ERROR: failed to create the name of the virtual environment")
        sys.exit(1)

    venv_name = stdout.rstrip()
    return os.path.join('venv', venv_name)


def _create_virtualenv(python, venv_path):
    # On Python 3.3 and newer, the venv module could be used, but it looks
    # like it doesn't work when run from a virtual environment on Fedora:
    # ensurepip fails with an error. First, try to use the virtualenv command.

    # Case 1: try virtualenv command
    cmd = ['virtualenv', '-p', python, venv_path]
    try:
        run_cmd(cmd)
        return
    except OSError as exc:
        if exc.errno != errno.ENOENT:
            raise

    print("Command failed: virtualenv program not found!")
    print()

    # Case 2: try python -m virtualenv
    cmd = [python, '-m', 'virtualenv', venv_path]
    exitcode = run_cmd_nocheck(cmd)
    if not exitcode:
        return
    print("%s -m virtualenv failed!" % os.path.basename(python))
    print()

    # Case 3: try python -m venv
    cmd = [python, '-m', 'venv', venv_path]
    exitcode = run_cmd_nocheck(cmd)
    if not exitcode:
        return
    print("%s -m venv failed!" % os.path.basename(python))

    print()
    print("ERROR: failed to create the virtual environment")
    print()
    print("Make sure that virtualenv is installed:")
    print("%s -m pip install -U virtualenv" % python)
    sys.exit(1)

def create_virtualenv(python, venv_path):
    if os.name == "nt":
        python_executable = os.path.basename(python)
        venv_python = os.path.join(venv_path, 'Scripts', python_executable)
    else:
        venv_python = os.path.join(venv_path, 'bin', 'python')
    if os.path.exists(venv_path):
        return venv_python

    print("Creating the virtual environment %s" % venv_path)
    try:
        _create_virtualenv(python, venv_path)

        # upgrade setuptools and pip to make sure that they support environment
        # marks in requirements.txt
        #
        # Install also wheel for faster creation of the virtual environment.
        cmd = [venv_python, '-m', 'pip',
               'install', '-U', 'setuptools>=18.5', 'pip>=6.0', 'wheel']
        run_cmd(cmd)

        # install requirements
        requirements = os.path.join(ROOT_DIR, 'performance', 'requirements.txt')
        cmd = [venv_python, '-m', 'pip', 'install', '-r', requirements]
        run_cmd(cmd)

        # psutil is a C extension written for CPython
        if python_implementation() == 'cpython':
            # try to install psutil
            cmd = [venv_python, '-m', 'pip', 'install', '-U', 'psutil']
            exitcode = run_cmd_nocheck(cmd)
            if exitcode:
                print("WARNING: failed to install psutil")
                print()

        # install performance inside the virtual environment
        version =  performance.__version__
        if version.endswith('dev'):
            cmd = [venv_python, '-m', 'pip', 'install', '-e', ROOT_DIR]
        else:
            cmd = [venv_python, '-m', 'pip',
                   'install', 'performance==%s' % version]
        run_cmd(cmd)
    except:
        if os.path.exists(venv_path):
            print()
            print("ERROR: Remove virtual environment %s" % venv_path)
            shutil.rmtree(venv_path)
        raise

    return venv_python


def exec_in_virtualenv(options):
    venv_path = virtualenv_path(options)
    venv_python = create_virtualenv(options.python, venv_path)

    args = [venv_python, "-m", "performance"] + sys.argv[1:] + ["--inside-venv"]
    # os.execv() is buggy on windows, which is why we use run_cmd/subprocess
    # on windows.
    # * https://bugs.python.org/issue19124
    # * https://github.com/python/benchmarks/issues/5
    if os.name == "nt":
        run_cmd(args)
        sys.exit(0)
    else:
        os.execv(args[0], args)


def cmd_venv(options):
    action = options.venv_action

    venv_path = virtualenv_path(options)

    if action in ('create', 'recreate'):
        recreated = False
        if action == 'recreate' and os.path.exists(venv_path):
            recreated = True
            shutil.rmtree(venv_path)
            print("The old virtual environment %s has been removed" % venv_path)
            print()

        if not os.path.exists(venv_path):
            create_virtualenv(options.python, venv_path)
            print()
            what = 'recreated' if recreated else 'created'
            print("The virtual environment %s has been %s" % (venv_path, what))
        else:
            print("The virtual environment %s already exists" % venv_path)

    elif action == 'remove':
        if os.path.exists(venv_path):
            shutil.rmtree(venv_path)
            print("The virtual environment %s has been removed" % venv_path)
        else:
            print("The virtual environment %s does not exist" % venv_path)

    else:
        # show command
        text = "Virtual environment path: %s" % venv_path
        created = os.path.exists(venv_path)
        if created:
            text += " (already created)"
        else:
            text += " (not created yet)"
        print(text)
        if not created:
            print()
            print("Command to create it:")
            cmd = "%s -m performance venv create" % options.python
            if options.venv:
                cmd += " --venv=%s" % options.venv
            print(cmd)
