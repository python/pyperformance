# A utility library for getting information about a Python executable.
#
# This may be used as a script.

__all__ = [
    'PythonInfo', 'SysSnapshot', 'SysImplementationSnapshot',
    'get_python_id',
    'get_python_info',
    'inspect_python_install',
]


from collections import namedtuple
import hashlib
import json
import os
import os.path
import subprocess
import sys


class PythonInfo(
        namedtuple('PythonInfo', 'executable sys stdlib_dir pyc_magic_number')):

    @classmethod
    def from_current(cls):
        try:
            from importlib.util import MAGIC_NUMBER
        except ImportError:
            import _imp
            MAGIC_NUMBER = _imp.get_magic()
        _sys = SysSnapshot.from_current()
        return cls(
            _sys.executable,
            _sys,
            os.path.dirname(os.__file__),
            MAGIC_NUMBER,
        )

    @classmethod
    def from_executable(cls, executable=sys.executable):
        current = os.path.abspath(sys.executable)
        if executable and executable != sys.executable:
            executable = os.path.abspath(executable)
        else:
            executable = current
        if executable == current:
            return cls.from_current()

        # Run _pythoninfo.py to get the raw info.
        try:
            text = subprocess.check_output(
                [executable, __file__],
                universal_newlines=True,
            )
        except subprocess.CalledProcessError:
            raise Exception(f'could not get info for {executable}')
        return cls.from_jsonable(
            json.loads(text),
            executable,
        )

    @classmethod
    def from_jsonable(cls, data, executable=None):
        if isinstance(data, str):
            data = json.loads(data)
        # We would use type(sys.version_info) if it allowed it.
        data['version_info'] = tuple(data['version_info'])
        data['implementation_version'] = tuple(data['implementation_version'])
        return cls(
            executable or data['executable (actual)'],
            SysSnapshot(
                data['executable'],
                data['prefix'],
                data['exec_prefix'],
                data['platlibdir'],
                data['stdlib_dir'],
                data['base_prefix'],
                data['base_exec_prefix'],
                data['version_str'],
                data['version_info'],
                data['hexversion'],
                data['api_version'],
                SysImplementationSnapshot(
                    data['implementation_name'],
                    data['implementation_version'],
                ),
                data['platform'],
            ),
            data['stdlib_dir (actual)'],
            bytes.fromhex(data['pyc_magic_number']),
        )

    def __getattr__(self, name):
        if hasattr(type(self), name):
            raise Exception(f'__getattr__() was accidentally triggered for {name!r}')
        return getattr(self.sys, name)

    @property
    def version_str(self):
        return self.sys.version

    @property
    def stdlib_dir(self):
        return self.sys._stdlib_dir or super().stdlib_dir

    @property
    def platlibdir(self):
        return self.sys.platlibdir or 'lib'

    def get_id(self, prefix=None, *, short=True):
        data = [
            # "executable" represents the install location
            # (and build, to an extent).
            self.executable,
            # sys.version encodes version, git info, build_date, and build_tool.
            self.sys.version,
            self.sys.implementation.name.lower(),
            '.'.join(str(v) for v in self.sys.implementation.version),
            str(self.sys.api_version),
            self.pyc_magic_number.hex(),
        ]
        # XXX Add git info if a dev build.

        h = hashlib.sha256()
        for value in data:
            h.update(value.encode('utf-8'))
        # XXX Also include the sorted output of "python -m pip freeze"?
        py_id = h.hexdigest()
        if short:
            py_id = py_id[:12]

        if prefix:
            if prefix is True:
                major, minor = self.sys.version_info[:2]
                py_id = f'{self.implementation.name}{major}.{minor}-{py_id}'
            else:
                py_id = prefix + py_id

        return py_id

    def as_jsonable(self):
        return {
            # locations
            'executable (actual)': self.executable,
            'executable': self.sys.executable,
            'prefix': self.sys.prefix,
            'exec_prefix': self.sys.exec_prefix,
            'platlibdir': self.sys.platlibdir,
            'stdlib_dir': self.sys._stdlib_dir,
            'stdlib_dir (actual)': self.stdlib_dir,
            # base locations
            'base_prefix': self.sys.base_prefix,
            'base_exec_prefix': self.sys.base_exec_prefix,
            # version
            'version_str': self.sys.version,
            'version_info': self.sys.version_info,
            'hexversion': self.sys.hexversion,
            'api_version': self.sys.api_version,
            # implementation
            'implementation_name': self.sys.implementation.name,
            'implementation_version': self.sys.implementation.version,
            # host
            'platform': self.sys.platform,
            # import system
            'pyc_magic_number': self.pyc_magic_number.hex(),
        }


class SysSnapshot(
        namedtuple('SysSnapshot',
                   (# locations
                    'executable '
                    'prefix '
                    'exec_prefix '
                    'platlibdir '
                    'stdlib_dir '
                    # base locations
                    'base_prefix '
                    'base_exec_prefix '
                    # version
                    'version '
                    'version_info '
                    'hexversion '
                    'api_version '
                    # implementation
                    'implementation '
                    # host
                    'platform '
                    ))):

    @classmethod
    def from_current(cls, *, abspaths=True):
        def loc(filename):
            if not filename:
                return None
            if abspaths:
                return os.path.abspath(filename)
            return filename
        return cls(
            loc(sys.executable),
            loc(sys.prefix),
            loc(sys.exec_prefix),
            getattr(sys, 'platlibdir', None),
            loc(getattr(sys, '_stdlib_dir', None)),
            loc(sys.base_prefix),
            loc(sys.base_exec_prefix),
            sys.version,
            sys.version_info,
            sys.hexversion,
            sys.api_version,
            SysImplementationSnapshot.from_current(),
            sys.platform,
        )

    @property
    def _stdlib_dir(self):
        return self.stdlib_dir


class SysImplementationSnapshot(
        namedtuple('SysImplementationSnapshot', 'name version')):

    @classmethod
    def from_current(cls):
        return cls(
            sys.implementation.name,
            sys.implementation.version,
        )


def get_python_id(python=sys.executable, *, prefix=None, short=True):
    """Return a unique (str) identifier for the given Python executable."""
    if not python or isinstance(python, str):
        info = PythonInfo.from_executable(python)
    elif not isinstance(python, PythonInfo):
        info = PythonInfo.from_jsonable(python)
    else:
        info = python
    return info.get_id(prefix, short=short)


def get_python_info(python=sys.executable):
    info = PythonInfo.from_executable(python)
    return info.as_jsonable()


def inspect_python_install(python=sys.executable):
    if isinstance(python, str):
        info = PythonInfo.from_executable(python)
    elif not isinstance(python, PythonInfo):
        info = PythonInfo.from_jsonable(python)
    else:
        info = python
    return _inspect_python_install(info)


#######################################
# internal implementation

def _is_dev_stdlib(stdlib_dir):
    if os.path.basename(stdlib_dir) != 'Lib':
        return False
    srcdir = os.path.dirname(stdlib_dir)
    for filename in [
        os.path.join(srcdir, 'Python', 'pylifecycle.c'),
        os.path.join(srcdir, 'PCbuild', 'pythoncore.vcxproj'),
    ]:
        if not os.path.exists(filename):
            return False
    return True


def _is_dev_executable(executable, stdlib_dir):
    builddir = os.path.dirname(executable)
    if os.path.exists(os.path.join(builddir, 'pybuilddir.txt')):
        return True
    if os.name == 'nt':
        pcbuild = os.path.dirname(os.path.dirname(executable))
        if os.path.basename(pcbuild) == 'PCbuild':
            srcdir = os.path.dirname(pcbuild)
            if os.path.join(srcdir, 'Lib') == stdlib_dir:
                return True
    return False


def _inspect_python_install(info):
    is_venv = info.prefix != info.base_prefix

    if (_is_dev_stdlib(info.stdlib_dir) and
            _is_dev_executable(info.executable, info.stdlib_dir)):
        # XXX What about venv?
        try:
            base_executable = sys._base_executable
        except AttributeError:
            base_executable = info.executable
        is_dev = True
    else:
        major, minor = info.version_info[:2]
        python = f'python{major}.{minor}'
        if is_venv:
            if '.' in os.path.basename(info.executable):
                ext = info.executable.rpartition('.')[2]
                python_exe = f'{python}.{ext}'
            else:
                python_exe = python
            expected = os.path.join(info.base_prefix, info.platlibdir, python)
            if info.stdlib_dir == expected:
                bindir = os.path.basename(os.path.dirname(info.executable))
                base_executable = os.path.join(info.base_prefix, bindir, python_exe)
            else:
                # XXX This is good enough for now.
                base_executable = info.executable
                #raise NotImplementedError(stdlib_dir)
        elif info.implementation.name.lower() == 'cpython':
            if info.platform == 'win32':
                expected = os.path.join(info.prefix, info.platlibdir)
            else:
                expected = os.path.join(info.prefix, info.platlibdir, python)
            if info.stdlib_dir == expected:
                base_executable = info.executable
            else:
                raise NotImplementedError(stdlib_dir)
        else:
            base_executable = info.executable
        is_dev = False

    return base_executable, is_dev, is_venv


#######################################
# use as a script

if __name__ == '__main__':
    info = PythonInfo.from_current()
    data = info.as_jsonable()
    if '--inspect' in sys.argv:
        (data['_base_executable'], data['_is_dev'], data['_is_venv'],
         ) = _inspect_python_install(info)
    json.dump(data, sys.stdout, indent=4)
    print()
