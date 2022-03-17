import importlib.util
import os
import sys
import sysconfig
import unittest

from pyperformance import tests, _pythoninfo


IS_VENV = sys.prefix != sys.base_prefix
CURRENT = {
    'executable': sys.executable,
    'executable (actual)': sys.executable,
    'base_executable': getattr(sys, '_base_executable', None),
    'base_executable (actual)': os.path.realpath(sys.executable),
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
    'stdlib_dir': getattr(sys, '_stdlib_dir', None),
    'stdlib_dir (actual)': os.path.dirname(os.__file__),
    'stdlib_dir (sysconfig)': sysconfig.get_path('stdlib'),
    'is_dev': sysconfig.is_python_build(),
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
                BASE = os.path.realpath(filename)
                CURRENT['base_executable (actual)'] = BASE
                break
        del major, minor, suffix, name, filename
else:
    BASE = CURRENT['base_executable (actual)']


class PythonInfoTests(tests.Resources, unittest.TestCase):

    def test_is_dev(self):
        data = dict(CURRENT)
        expected = CURRENT['is_dev']
        info = _pythoninfo.PythonInfo.from_jsonable(data)

        isdev = info.is_dev
        self.assertIs(isdev, expected)

        expected = not expected
        data['is_dev'] = not data['is_dev']
        info = _pythoninfo.PythonInfo.from_jsonable(data)

        isdev = info.is_dev
        self.assertIs(isdev, expected)

    def test_is_venv(self):
        data = dict(CURRENT)
        expected = IS_VENV
        info = _pythoninfo.PythonInfo.from_jsonable(data)

        isvenv = info.is_venv
        self.assertIs(isvenv, expected)

        expected = not expected
        if IS_VENV:
            data['prefix'] = data['base_prefix']
        else:
            data['prefix'] = data['base_prefix'] + '-spam'
        info = _pythoninfo.PythonInfo.from_jsonable(data)

        isvenv = info.is_venv
        self.assertIs(isvenv, expected)

    def test_base_executable_normal(self):
        base_expected = BASE
        if IS_VENV:
            python = BASE
        else:
            python = sys.executable
        info = _pythoninfo.PythonInfo.from_executable(python)

        base = info.base_executable

        self.assertEqual(base, base_expected)

    def test_base_executable_venv(self):
        base_expected = BASE
        assert base_expected
        if IS_VENV:
            python = sys.executable
        else:
            _, python = self.venv(base_expected)
        info = _pythoninfo.PythonInfo.from_executable(python)

        base = info.base_executable

        self.assertEqual(base, base_expected)


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

    INFO = {
        'executable': '/a/b/c/bin/spam-python',
        'version_str': '3.8.10 (default, May  5 2021, 03:01:07) \n[GCC 7.5.0]',
        'version_info': (3, 8, 10, 'final', 0),
        'api_version': 1013,
        'pyc_magic_number': b'U\r\r\n'.hex(),
        'implementation_name': 'cpython',
        'implementation_version': (3, 8, 10, 'final', 0),
    }
    ID = '334c63e71d63'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.INFO.update((k, '') for k in CURRENT if k not in cls.INFO)

    def test_no_prefix(self):
        info = dict(self.INFO)
        expected = self.ID

        pyid = _pythoninfo.get_python_id(
            _pythoninfo.PythonInfo.from_jsonable(info),
        )

        self.assertEqual(pyid, expected)

    def test_true_prefix(self):
        info = dict(self.INFO)
        expected = f'cpython3.8-{self.ID}'

        pyid = _pythoninfo.get_python_id(
            _pythoninfo.PythonInfo.from_jsonable(info),
            prefix=True,
        )

        self.assertEqual(pyid, expected)

    def test_given_prefix(self):
        info = dict(self.INFO)
        expected = f'spam-{self.ID}'

        pyid = _pythoninfo.get_python_id(
            _pythoninfo.PythonInfo.from_jsonable(info),
            prefix='spam-',
        )

        self.assertEqual(pyid, expected)
