import importlib.util
import os
import sys
import sysconfig
import unittest

from pyperformance import tests, _pythoninfo


IS_VENV = sys.prefix != sys.base_prefix
CURRENT = {
    'executable (sys)': sys.executable,
    'executable (sys;realpath)': os.path.realpath(sys.executable),
    'base_executable': sys.executable,
    'base_executable (sys)': getattr(sys, '_base_executable', None),
    'version_str (sys)': sys.version,
    'version_info (sys)': sys.version_info,
    'hexversion (sys)': sys.hexversion,
    'api_version (sys)': sys.api_version,
    'pyc_magic_number': importlib.util.MAGIC_NUMBER,
    'implementation_name (sys)': sys.implementation.name,
    'implementation_version (sys)': sys.implementation.version,
    'platform (sys)': sys.platform,
    'prefix (sys)': sys.prefix,
    'exec_prefix (sys)': sys.exec_prefix,
    'base_prefix (sys)': sys.base_prefix,
    'base_exec_prefix (sys)': sys.base_exec_prefix,
    'stdlib_dir': os.path.dirname(os.__file__),
    'stdlib_dir (sys)': getattr(sys, '_stdlib_dir', None),
    'stdlib_dir (sysconfig)': sysconfig.get_path('stdlib'),
    'is_dev (sysconfig)': sysconfig.is_python_build(),
    'is_venv': sys.prefix != sys.base_prefix,
}
if IS_VENV:
    if CURRENT['base_executable'] == sys.executable:
        if CURRENT['base_executable (sys)'] == sys.executable:
            CURRENT['base_executable'] = None
        else:
            CURRENT['base_executable'] = CURRENT['base_executable (sys)']


class GetInfoTests(tests.Functional, unittest.TestCase):

    maxDiff = 80 * 100

    def test_no_args(self):
        expected = _pythoninfo._build_info(CURRENT)

        info = _pythoninfo.get_info()

        self.assertEqual(vars(info), vars(expected))

    def test_current(self):
        expected = _pythoninfo._build_info(CURRENT)

        info = _pythoninfo.get_info(sys.executable)

        self.assertEqual(vars(info), vars(expected))

    def test_venv(self):
        expected = _pythoninfo._build_info(CURRENT)
        if IS_VENV:
            python = sys.executable
        else:
            venv, python, cleanup = tests.create_venv()
            self.addCleanup(cleanup)
            expected.sys.executable = python
            realpath = os.path.realpath(os.path.normpath(sys.executable))
            if os.name == 'nt':
                # It isn't a symlink.
                expected.executable_realpath = os.path.realpath(python)
            expected.sys._base_executable = realpath
            expected.base_executable = realpath
            expected.sys.prefix = venv
            expected.sys.exec_prefix = venv
            expected.sys.version_info = tuple(expected.sys.version_info)
            (expected.sys.implementation.version
             ) = tuple(expected.sys.implementation.version)
            expected.is_venv = True

        info = _pythoninfo.get_info(python)

        # We have to work around a possible bug.
        if not info.base_executable:
            expected.base_executable = None
            expected.sys._base_executable = info.sys._base_executable
        self.assertEqual(vars(info), vars(expected))
