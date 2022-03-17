# A utility library for getting information about a Python executable.
#
# This may be used as a script.

__all__ = [
    'PythonInfo',
    'SysSnapshot', 'SysImplementationSnapshot', 'SysconfigSnapshot',
    'VenvConfig',
]


from collections import namedtuple
import hashlib
import importlib.util
import json
import os
import os.path
import subprocess
import sys
import sysconfig


class PythonInfo(
        namedtuple('PythonInfo', ('executable sys sysconfig '
                                  'stdlib_dir pyc_magic_number'))):

    _CURRENT = None

    @classmethod
    def from_current(cls):
        if cls._CURRENT is not None:
            return cls._CURRENT
        _sys = SysSnapshot.from_current()
        cls._CURRENT = cls(
            _sys.executable,
            _sys,
            SysconfigSnapshot.from_current(),
            os.path.dirname(os.__file__),
            importlib.util.MAGIC_NUMBER,
        )
        return cls._CURRENT

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
        self = cls(
            executable or data['executable (actual)'],
            SysSnapshot(
                data['executable'],
                data['prefix'],
                data['exec_prefix'],
                data['stdlib_dir'],
                data['base_executable'],
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
            SysconfigSnapshot(
                data['stdlib_dir (sysconfig)'],
                data['is_dev'],
            ),
            data['stdlib_dir (actual)'],
            bytes.fromhex(data['pyc_magic_number']),
        )
        if data['base_executable (actual)']:
            self._base_executable = data['base_executable (actual)']
        return self

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
    def base_executable(self):
        if getattr(self, '_base_executable', None):
            return self._base_executable

        base = self.sys._base_executable
        if self.is_venv:
            # XXX There is probably a bug in venv, since
            # sys._base_executable should be different.
            if not base or base == self.sys.executable:
                venv = VenvConfig.from_root(self.prefix)
                base = venv.executable
        elif not base:
            base = self.executable
        self._base_executable = os.path.realpath(base)
        return self._base_executable

    @property
    def is_venv(self):
        return self.sys.prefix != self.sys.base_prefix

    @property
    def is_dev(self):
        return self.sysconfig.is_python_build()

    @property
    def is_current(self):
        if self is self._CURRENT:
            return True
        # It shouldn't be able to match without being self._CURRENT.
        assert self.executable != os.path.abspath(sys.executable), \
                (self.executable, sys.executable)
        return False

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
            'stdlib_dir': self.sys._stdlib_dir,
            'stdlib_dir (actual)': self.stdlib_dir,
            'stdlib_dir (sysconfig)': self.sysconfig.stdlib,
            # base locations
            'base_executable': self.sys._base_executable,
            'base_executable (actual)': self.base_executable,
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
            # build
            'is_dev': self.sysconfig.is_python_build(),
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
                    'stdlib_dir '
                    # base locations
                    'base_executable '
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
        base_executable = getattr(sys, '_base_executable', None)
        if sys.prefix != sys.base_prefix and base_executable == sys.executable:
            # There is a bug in venv, so figure it out later...
            base_executable = None
        return cls(
            loc(sys.executable),
            loc(sys.prefix),
            loc(sys.exec_prefix),
            loc(getattr(sys, '_stdlib_dir', None)),
            loc(base_executable),
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

    @property
    def _base_executable(self):
        return self.base_executable


class SysImplementationSnapshot(
        namedtuple('SysImplementationSnapshot', 'name version')):

    @classmethod
    def from_current(cls):
        return cls(
            sys.implementation.name,
            sys.implementation.version,
        )


class SysconfigSnapshot(
        namedtuple('SysconfigSnapshot', 'stdlib is_python_build')):
    # It may be helpful to include the build options (e.g. configure flags).

    @classmethod
    def from_current(cls):
        return cls(
            (sysconfig.get_path('stdlib')
             if 'stdlib' in sysconfig.get_path_names()
             else None),
            sysconfig.is_python_build(),
        )

    def is_python_build(self):
        return super().is_python_build


class VenvConfig(
        namedtuple('VenvConfig', ('home executable version '
                                  'system_site_packages command'))):

    @classmethod
    def from_root(cls, root, *, populate_old=True):
        cfgfile = os.path.join(root, 'pyvenv.cfg')
        with open(cfgfile, encoding='utf-8') as infile:
            text = infile.read()
        return cls.parse(text, root)

    @classmethod
    def parse(cls, lines, root=None, *, populate_old=True):
        if isinstance(lines, str):
            lines = lines.splitlines()
        else:
            lines = (l.rstrip(os.linesep) for l in lines)
        # Parse the lines.
        # (We do not validate then).
        kwargs = {}
        for line in lines:
            name, sep, value = line.partition('=')
            if not sep:
                continue
            # We do not check for duplicate names.
            name = name.strip().lower()
            if name == 'include-system-site-packages':
                name = 'system_site_packages'
            if name not in cls._fields:
                # XXX Preserve this anyway?
                continue
            value = value.lstrip()
            if name == 'system_site_packages':
                value = (value == 'true')
            kwargs[name] = value
        # Deal with older Pythons.
        if 'executable' not in kwargs:
            kwargs['executable'] = None
            if populate_old and os.path.isdir(kwargs['home']):
                files = set(os.listdir(kwargs['home']))
                major, minor = kwargs['version'].split('.')[:2]
                _, suffix = os.path.splitext(sys.executable)
                for name in [
                        f'python{major}.{minor}{suffix}',
                        f'python{major}{minor}{suffix}',
                        f'python{major}{suffix}',
                        f'python{suffix}',
                        ]:
                    filename = os.path.join(kwargs['home'], name)
                    if os.path.isfile(filename):
                        kwargs['executable'] = filename
                        break
        if 'command' not in kwargs:
            if populate_old and root and kwargs['executable']:
                kwargs['command'] = f'{kwargs["executable"]} -m venv {root}'
            else:
                kwargs['command'] = None
        # Create the object.
        self = cls(**kwargs)
        if root:
            self._root = root
        return self


#######################################
# use as a script

if __name__ == '__main__':
    info = PythonInfo.from_current()
    data = info.as_jsonable()
    if '--inspect' in sys.argv:
        data['is_venv'] = info.is_venv
    json.dump(data, sys.stdout, indent=4)
    print()
