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
    import urllib2 as urllib_request   # Python 3
except ImportError:
    import urllib.request as urllib_request


GET_PIP_URL = 'https://bootstrap.pypa.io/get-pip.py'


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
            if os.curdir not in path:
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
            if normdir not in seen:
                seen.add(normdir)
                for thefile in files:
                    name = os.path.join(dir, thefile)
                    if _access_check(name, mode):
                        return name
        return None


PERFORMANCE_ROOT = os.path.realpath(os.path.dirname(__file__))


def is_build_dir():
    root_dir = os.path.join(PERFORMANCE_ROOT, '..')
    if not os.path.exists(os.path.join(root_dir, 'performance')):
        return False
    return os.path.exists(os.path.join(root_dir, 'setup.py'))


class Requirements(object):
    def __init__(self, filename, installer, indirect_req, optional):
        # pre-requirements (setuptools, pip)
        self.installer = []

        # indirect requirements
        self.indirect_req = []

        # requirements
        self.req = []

        # optional requirements
        self.optional = []

        with open(filename) as fp:
            for line in fp.readlines():
                # strip comment
                line = line.partition('#')[0]
                line = line.rstrip()
                if not line:
                    continue

                # strip env markers
                req = line.partition(';')[0]

                # strip version
                req = req.partition('==')[0]
                req = req.partition('>=')[0]

                if req in installer:
                    self.installer.append(line)
                elif req in optional:
                    self.optional.append(line)
                elif req in indirect_req:
                    self.indirect_req.append(line)
                else:
                    self.req.append(line)


def safe_rmtree(path):
    if not os.path.exists(path):
        return

    print("Remove directory %s" % path)
    shutil.rmtree(path)


def python_implementation():
    if hasattr(sys, 'implementation'):
        # PEP 421, Python 3.3
        name = sys.implementation.name
    else:
        name = platform.python_implementation()
    return name.lower()


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


def download(filename, url):
    print("Download %s into %s" % (url, filename))

    response = urllib_request.urlopen(url)
    with response:
        content = response.read()

    with open(filename, 'wb') as fp:
        fp.write(content)
        fp.flush()


class VirtualEnvironment(object):
    def __init__(self, options):
        self.options = options
        self.python = options.python
        self._venv_path = options.venv
        self._pip_program = None

    def get_python_program(self):
        venv_path = self.get_venv_path()
        if os.name == "nt":
            python_executable = os.path.basename(self.python)
            return os.path.join(venv_path, 'Scripts', python_executable)
        else:
            return os.path.join(venv_path, 'bin', 'python')

    def run_cmd_nocheck(self, cmd, verbose=True):
        if verbose:
            print("Execute: %s" % ' '.join(cmd))

        # Explicitly flush standard streams, required if streams are buffered
        # (not TTY) to write lines in the expected order
        sys.stdout.flush()
        sys.stderr.flush()

        env = create_environ(self.options.inherit_environ)
        try:
            proc = subprocess.Popen(cmd, env=env)
        except OSError as exc:
            if exc.errno == errno.ENOENT:
                # Command not found
                return 127
            raise

        try:
            proc.wait()
        except:
            proc.kill()
            proc.wait()
            raise

        return proc.returncode

    def run_cmd(self, cmd, verbose=True):
        exitcode = self.run_cmd_nocheck(cmd, verbose=verbose)
        if exitcode:
            sys.exit(exitcode)
        print()

    def get_venv_path(self):
        if self._venv_path is not None:
            return self._venv_path

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

        requirements = os.path.join(PERFORMANCE_ROOT, 'requirements.txt')
        cmd = (self.python, '-c', script, performance.__version__, requirements)
        proc = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                universal_newlines=True)
        stdout = proc.communicate()[0]
        if proc.returncode:
            print("ERROR: failed to create the name of the virtual environment")
            sys.exit(1)

        venv_name = stdout.rstrip()
        self._venv_path = venv_path = os.path.join('venv', venv_name)
        return venv_path

    def _get_pip_program(self):
        venv_path = self.get_venv_path()

        # python -m pip
        venv_python = self.get_python_program()
        pip_program = [venv_python, '-m', 'pip']
        if self.run_cmd_nocheck(pip_program + ['--version']) == 0:
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
        if self.run_cmd_nocheck(pip_program + ['--version']) == 0:
            self._pip_program = pip_program
            return

    def get_pip_program(self):
        if self._pip_program is None:
            self._get_pip_program()
        return self._pip_program

    def install_pip(self):
        venv_python = self.get_python_program()

        # python -m ensurepip
        cmd = [venv_python, '-m', 'ensurepip', '--verbose']
        exitcode = self.run_cmd_nocheck(cmd)
        if not exitcode:
            if self.get_pip_program() is not None:
                return True

        venv_path = self.get_venv_path()
        filename = os.path.join(os.path.dirname(venv_path), 'get-pip.py')
        if not os.path.exists(filename):
            download(filename, GET_PIP_URL)

        # python get-pip.py
        cmd = [venv_python, filename]
        exitcode = self.run_cmd_nocheck(cmd)
        ok = (exitcode == 0)
        if not ok:
            # get-pip.py was maybe not properly downloaded: remove it to
            # download it again next time
            os.unlink(filename)

        return ok

    def _create_virtualenv_impl(self, cmd, install_pip=False):
        venv_path = self.get_venv_path()

        cmd = cmd + [venv_path]
        try:
            exitcode = self.run_cmd_nocheck(cmd)
            if exitcode:
                print("%s command failed" % ' '.join(cmd))
            else:
                if install_pip:
                    pip_installed = self.install_pip()
                else:
                    pip_installed = True

                if pip_installed and self.get_pip_program() is not None:
                    return True
                print("pip doesn't work")
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise

            # run_cmd_nocheck() failed with ENOENT
            print("%s command failed: command not found" % ' '.join(cmd))

        print()

        safe_rmtree(venv_path)
        return False

    def _create_virtualenv(self):
        # python -m venv
        cmd = [self.python, '-m', 'venv', '--without-pip']
        if self._create_virtualenv_impl(cmd, install_pip=True):
            return
        print()

        # python -m virtualenv
        cmd = [self.python, '-m', 'virtualenv']
        if self._create_virtualenv_impl(cmd):
            return
        print()

        # virtualenv command
        cmd = ['virtualenv', '-p', self.python]
        if self._create_virtualenv_impl(cmd):
            return

        print("ERROR: failed to create the virtual environment")
        print()
        print("Make sure that virtualenv is installed:")
        print("%s -m pip install -U virtualenv" % self.python)
        sys.exit(1)

    def exists(self):
        venv_python = self.get_python_program()
        return os.path.exists(venv_python)

    def create_virtualenv(self):
        if self.exists():
            return self.get_python_program()

        venv_path = self.get_venv_path()
        venv_python = self.get_python_program()

        filename = os.path.join(PERFORMANCE_ROOT, 'requirements.txt')
        requirements = Requirements(filename,
                                    # FIXME: don't hardcode requirements
                                    ['setuptools', 'pip', 'wheel'],
                                    ['cffi'],
                                    ['psutil', 'dulwich'])

        print("Creating the virtual environment %s" % venv_path)
        try:
            self._create_virtualenv()
            pip_program = self.get_pip_program()

            # Upgrade installer dependencies (pip, setuptools, ...)
            cmd = pip_program + ['install', '-U']
            cmd.extend(requirements.installer)
            self.run_cmd(cmd)

            # install indirect requirements
            cmd = pip_program + ['install']
            cmd.extend(requirements.indirect_req)
            self.run_cmd(cmd)

            # install requirements
            cmd = pip_program + ['install']
            cmd.extend(requirements.req)
            self.run_cmd(cmd)

            # install optional requirements
            for req in requirements.optional:
                cmd = pip_program + ['install', '-U', req]
                exitcode = self.run_cmd_nocheck(cmd)
                if exitcode:
                    print("WARNING: failed to install %s" % req)
                    print()

            # install performance inside the virtual environment
            if is_build_dir():
                root_dir = os.path.dirname(PERFORMANCE_ROOT)
                cmd = pip_program + ['install', '-e', root_dir]
            else:
                version = performance.__version__
                cmd = pip_program + ['install', 'performance==%s' % version]
            self.run_cmd(cmd)

            # pip freeze
            cmd = pip_program + ['freeze']
            self.run_cmd(cmd)
        except:
            print()
            safe_rmtree(venv_path)
            raise

        return venv_python


def exec_in_virtualenv(options):
    venv = VirtualEnvironment(options)

    venv_python = venv.create_virtualenv()

    args = [venv_python, "-m", "performance"] + \
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


def cmd_venv(options):
    action = options.venv_action

    venv = VirtualEnvironment(options)
    venv_path = venv.get_venv_path()

    if action in ('create', 'recreate'):
        recreated = False
        if action == 'recreate' and venv.exists():
            recreated = True
            shutil.rmtree(venv_path)
            print("The old virtual environment %s has been removed" % venv_path)
            print()

        if not venv.exists():
            venv.create_virtualenv()

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
        created = venv.exists()
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
