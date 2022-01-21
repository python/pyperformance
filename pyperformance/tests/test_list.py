import unittest

from pyperformance import tests


class FunctionalTests(tests.Functional, unittest.TestCase):

    def test_list(self):
        self.run_pyperformance('list')

    def test_list_groups(self):
        self.run_pyperformance('list_groups')


if __name__ == "__main__":
    unittest.main()
