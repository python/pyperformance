import importlib.util
import os
import sys
import unittest

from pyperformance import tests, _pythoninfo


IS_VENV = sys.prefix != sys.base_prefix
CURRENT = {
    'executable': sys.executable,
    'executable (actual)': sys.executable,
    'base_executable': getattr(sys, '_base_executable', None),
    'base_executable (actual)': sys.executable,
    'version_str': sys.version,
    'version_info': sys.version_info,
    'hexversion': sys.hexversion,
    'api_version': sys.api_version,
    # importlib.util.MAGIC_NUMBER has been around since 3.5.
    'pyc_magic_number': importlib.util.MAGIC_NUMBER.hex(),
    'implementation_name': sys.implementation.name,
    'implementation_version': sys.implementation.version,
    'platform': sys.platform,
    'prefix': sys.prefix,
    'exec_prefix': sys.exec_prefix,
    'base_prefix': sys.base_prefix,
    'base_exec_prefix': sys.base_exec_prefix,
    'platlibdir': getattr(sys, 'platlibdir', None),
    'stdlib_dir': getattr(sys, '_stdlib_dir', None),
    'stdlib_dir (actual)': os.path.dirname(os.__file__),
}
if IS_VENV:
    BASE = CURRENT['base_executable']
    if BASE == sys.executable:  # a bug in venv?
        CURRENT['base_executable'] = None
        CURRENT['base_executable (actual)'] = None
        BASE = None
    if not BASE:
        major, minor = sys.version_info[:2]
        _, suffix = os.path.splitext(sys.executable)
        for name in [
                f'python{major}.{minor}{suffix}',
                f'python{major}{minor}{suffix}',
                f'python{major}{suffix}',
                f'python{suffix}',
                ]:
            filename = os.path.join(sys._home, name)
            if os.path.exists(filename):
                BASE = filename
                CURRENT['base_executable (actual)'] = BASE
                break
        del major, minor, suffix, name, filename
else:
    BASE = sys.executable


class GetPythonInfoTests(tests.Resources, unittest.TestCase):

    maxDiff = 80 * 100

    def test_no_args(self):
        info = _pythoninfo.get_python_info()

        self.assertEqual(info, CURRENT)

    def test_current_python(self):
        info = _pythoninfo.get_python_info(sys.executable)

        self.assertEqual(info, CURRENT)

    def test_venv(self):
        expected = dict(CURRENT)
        if IS_VENV:
            python = sys.executable
        else:
            venv, python = self.venv()
            expected['executable'] = python
            expected['executable (actual)'] = python
            expected['prefix'] = venv
            expected['exec_prefix'] = venv
            expected['version_info'] = tuple(expected['version_info'])
            (expected['implementation_version']
             ) = tuple(expected['implementation_version'])

        info = _pythoninfo.get_python_info(python)

        # We have to work around an apparent bug in venv.
        if not info['base_executable']:
            expected['base_executable'] = None
        self.assertEqual(info, expected)


class GetPythonIDTests(unittest.TestCase):

    INFO = dict(CURRENT, **{
        'executable': '/a/b/c/bin/spam-python',
        'version_str': '3.8.10 (default, May  5 2021, 03:01:07) \n[GCC 7.5.0]',
        'version_info': (3, 8, 10, 'final', 0),
        'api_version': 1013,
        'pyc_magic_number': b'U\r\r\n'.hex(),
        'implementation_name': 'cpython',
        'implementation_version': (3, 8, 10, 'final', 0),
    })
    ID = '7f16883789f5' if IS_VENV else '736789ab47e4'

    def test_no_prefix(self):
        pyid = _pythoninfo.get_python_id(self.INFO)

        self.assertEqual(pyid, self.ID)

    def test_true_prefix(self):
        pyid = _pythoninfo.get_python_id(self.INFO, prefix=True)

        self.assertEqual(pyid, f'cpython3.8-{self.ID}')

    def test_given_prefix(self):
        pyid = _pythoninfo.get_python_id(self.INFO, prefix='spam-')

        self.assertEqual(pyid, f'spam-{self.ID}')


def read_venv_config(venv):
    filename = os.path.join(venv, 'pyvenv.cfg')
    with open(filename, encoding='utf-8') as infile:
        text = infile.read()
    cfg = {}
    for line in text.splitlines():
        name, sep, value = line.partition(' = ')
        if sep:
            cfg[name.strip()] = value.strip()
    return cfg


def get_venv_base(venv):
    cfg = read_venv_config(sys.prefix)
    if 'executable' in cfg:
        return cfg['executable']
    elif 'home' in cfg:
        major, minor = cfg['version'].split('.')[:2]
        base = f'python{major}.{minor}'
        return os.path.join(cfg['home'], base)
    else:
        return None


class InspectPythonInstallTests(tests.Resources, unittest.TestCase):

    def test_info(self):
        info = dict(CURRENT)
        if IS_VENV:
            info['prefix'] = info['base_prefix']
            info['exec_prefix'] = info['base_exec_prefix']
        (base, isdev, isvenv,
         ) = _pythoninfo.inspect_python_install(info)

        self.assertEqual(base, BASE)
        self.assertFalse(isdev)
        self.assertFalse(isvenv)

    def test_normal(self):
        if IS_VENV:
            try:
                python = sys._base_executable
            except AttributeError:
                python = sys.executable
            if python == sys.executable:
                python = get_venv_base(sys.prefix)
                assert python
        else:
            python = sys.executable
        (base, isdev, isvenv,
         ) = _pythoninfo.inspect_python_install(python)

        self.assertEqual(base, python)
        self.assertFalse(isdev)
        self.assertFalse(isvenv)

    def test_venv(self):
        if IS_VENV:
            python = sys.executable
            try:
                base_expected = sys._base_executable
            except AttributeError:
                base_expected = sys.executable
            if base_expected == sys.executable:
                base_expected = get_venv_base(sys.prefix)
                assert base_expected
        else:
            base_expected = sys.executable
            _, python = self.venv(base_expected)
        (base, isdev, isvenv,
         ) = _pythoninfo.inspect_python_install(python)

        self.assertEqual(base, base_expected)
        self.assertFalse(isdev)
        self.assertTrue(isvenv)

    @unittest.skip('needs platform-specific testing')
    def test_dev(self):
        # XXX
        raise NotImplementedError
