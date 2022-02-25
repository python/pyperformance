import os.path
import sys
import unittest

from pyperformance.tests import DATA_DIR, run_cmd

USER_DEFINED_MANIFEST = os.path.join(DATA_DIR, 'user_defined_bm', 'MANIFEST')


class TestBM(unittest.TestCase):
    def test_user_defined_bm(self):
        cmd = [sys.executable, '-m', 'pyperformance', 'run', f'--manifest={USER_DEFINED_MANIFEST}']

        run_cmd(cmd)


if __name__ == "__main__":
    unittest.main()
