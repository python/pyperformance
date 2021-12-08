# A utility library for getting information about a Python executable.
#
# This may be used as a script.

__all__ = [
    'get_python_id',
    'get_python_info',
    'inspect_python_install',
]


import hashlib
import json
import os
import subprocess
import sys


def get_python_id(python=sys.executable, *, prefix=None):
    """Return a unique (str) identifier for the given Python executable."""
    if not python or isinstance(python, str):
        info = get_python_info(python or sys.executable)
    else:
        info = python
        python = info['executable']

    data = [
        # "executable" represents the install location
        # (and build, to an extent).
        info['executable'],
        # sys.version encodes version, git info, build_date, and build_tool.
        info['version_str'],
        info['implementation_name'],
        '.'.join(str(v) for v in info['implementation_version']),
        str(info['api_version']),
        info['magic_number'],
    ]
    # XXX Add git info if a dev build.

    h = hashlib.sha256()
    for value in data:
        h.update(value.encode('utf-8'))
    # XXX Also include the sorted output of "python -m pip freeze"?
    py_id = h.hexdigest()
    # XXX Return the whole string?
    py_id = py_id[:12]

    if prefix:
        if prefix is True:
            major, minor = info['version_info'][:2]
            py_id = f'{info["implementation_name"]}{major}.{minor}-{py_id}'
        else:
            py_id = prefix + py_id

    return py_id


def get_python_info(python=sys.executable):
    if not python or python == sys.executable:
        return _get_raw_info()

    try:
        text = subprocess.check_output(
            [python, __file__],
            universal_newlines=True,
        )
    except subprocess.CalledProcessError:
        raise Exception(f'could not get info for {python}')
    return json.loads(text)


def inspect_python_install(python=sys.executable):
    if isinstance(python, str):
        info = get_python_info(python)
    else:
        info = python
    return _inspect_python_install(**info)


#######################################
# internal implementation

try:
    PLATLIBDIR = sys.platlibdir
except AttributeError:
    PLATLIBDIR = 'lib'
STDLIB_DIR = os.path.dirname(os.__file__)
try:
    from importlib.util import MAGIC_NUMBER
except ImportError:
    import _imp
    MAGIC_NUMBER = _imp.get_magic()


def _inspect_python_install(executable, prefix, base_prefix,
                            platlibdir, stdlib_dir,
                            version_info, platform, implementation_name,
                            **_ignored):
    is_venv = prefix != base_prefix

    if os.path.basename(stdlib_dir) == 'Lib':
        base_executable = os.path.join(os.path.dirname(stdlib_dir), 'python')
        if not os.path.exists(base_executable):
            raise NotImplementedError(base_executable)
        is_dev = True
    else:
        major, minor = version_info[:2]
        python = f'python{major}.{minor}'
        if is_venv:
            if '.' in os.path.basename(executable):
                ext = executable.rpartition('.')[2]
                python_exe = f'{python}.{ext}'
            else:
                python_exe = python
            expected = os.path.join(base_prefix, platlibdir, python)
            if stdlib_dir == expected:
                bindir = os.path.basename(os.path.dirname(executable))
                base_executable = os.path.join(base_prefix, bindir, python_exe)
            else:
                # XXX This is good enough for now.
                base_executable = executable
                #raise NotImplementedError(stdlib_dir)
        elif implementation_name == 'cpython':
            if platform == 'win32':
                expected = os.path.join(prefix, platlibdir)
            else:
                expected = os.path.join(prefix, platlibdir, python)
            if stdlib_dir == expected:
                base_executable = executable
            else:
                raise NotImplementedError(stdlib_dir)
        else:
            base_executable = executable
        is_dev = False

    return base_executable, is_dev, is_venv


def _get_raw_info():
    return {
        'executable': sys.executable,
        'version_str': sys.version,
        'version_info': tuple(sys.version_info),
        'hexversion': sys.hexversion,
        'api_version': sys.api_version,
        'magic_number': MAGIC_NUMBER.hex(),
        'implementation_name': sys.implementation.name.lower(),
        'implementation_version': tuple(sys.implementation.version),
        'platform': sys.platform,
        'prefix': sys.prefix,
        'exec_prefix': sys.exec_prefix,
        'base_prefix': sys.base_prefix,
        'base_exec_prefix': sys.base_exec_prefix,
        'platlibdir': PLATLIBDIR,
        'stdlib_dir': STDLIB_DIR,
        # XXX Also include the build options (e.g. configure flags)?
    }


#######################################
# use as a script

if __name__ == '__main__':
    info = _get_raw_info()
    json.dump(info, sys.stdout, indent=4)
    print()
