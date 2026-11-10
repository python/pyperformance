import io
import os.path
import unittest
from contextlib import redirect_stderr, redirect_stdout
from types import SimpleNamespace

from pyperformance import commands


def _missing(name):
    return os.path.join("definitely", "missing-%s.json" % name)


class MissingResultFilesTests(unittest.TestCase):
    """`show` and `compare` must report missing files cleanly, not crash."""

    def test_show_missing_file(self):
        missing = _missing("show")
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as cm:
                commands.cmd_show(SimpleNamespace(filename=missing))
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("ERROR", stdout.getvalue())
        # NOTE: compare basenames: str(OSError) escapes path separators
        # on some platforms (e.g. backslashes are doubled on Windows).
        self.assertIn(os.path.basename(missing), stdout.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_compare_missing_file(self):
        missing = _missing("compare")
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as cm:
                commands.cmd_compare(SimpleNamespace(
                    baseline_filename=missing,
                    changed_filename=_missing("other"),
                    csv=None,
                ))
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("ERROR", stdout.getvalue())
        # NOTE: compare basenames: str(OSError) escapes path separators
        # on some platforms (e.g. backslashes are doubled on Windows).
        self.assertIn(os.path.basename(missing), stdout.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
