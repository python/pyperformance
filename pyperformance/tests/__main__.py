import unittest

from pyperformance import tests


def load_tests(loader, standard_tests, pattern):
    pkgtests = loader.discover(
        start_dir=tests.TESTS_ROOT,
        top_level_dir=tests.TESTS_ROOT,
        pattern=pattern or 'test*',
    )
    standard_tests.addTests(pkgtests)
    return standard_tests


if __name__ == "__main__":
    unittest.main()
