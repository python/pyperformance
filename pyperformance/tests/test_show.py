import os.path
import unittest

from pyperformance import tests


class FunctionalTests(tests.Functional, unittest.TestCase):

    def test_show(self):
        for filename in (
            os.path.join(tests.DATA_DIR, 'py36.json'),
            os.path.join(tests.DATA_DIR, 'mem1.json'),
        ):
            with self.subTest(filename):
                self.run_pyperformance('show', filename)


if __name__ == "__main__":
    unittest.main()
