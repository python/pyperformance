import sys
import types
import unittest

from pyperformance import tests, _python


class GetIDTests(unittest.TestCase):

    def _dummy_info(self):
        info = types.SimpleNamespace(
            sys=types.SimpleNamespace(
                executable='/a/b/c/bin/spam-python',
                version='3.8.10 (default, May  5 2021, 03:01:07) \n[GCC 7.5.0]',
                version_info=(3, 8, 10, 'final', 0),
                api_version=1013,
                implementation=types.SimpleNamespace(
                    name='cpython',
                    version=(3, 8, 10, 'final', 0),
                ),
            ),
            pyc_magic_number=b'U\r\r\n',
        )
        base_id = 'b14d92fd0e6f'
        return info, base_id

    def test_no_prefix(self):
        info, expected = self._dummy_info()

        pyid = _python.get_id(info)

        self.assertEqual(pyid, expected)

    def test_default_prefix(self):
        info, expected = self._dummy_info()
        expected = f'cpython3.8-{expected}'

        pyid = _python.get_id(info, prefix=True)

        self.assertEqual(pyid, expected)

    def test_given_prefix(self):
        info, expected = self._dummy_info()
        expected = f'spam-{expected}'

        pyid = _python.get_id(info, prefix='spam-')

        self.assertEqual(pyid, expected)
