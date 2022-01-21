import contextlib
import errno
import os
import os.path
import tempfile


TESTS_ROOT = os.path.realpath(os.path.dirname(__file__))
DATA_DIR = os.path.join(TESTS_ROOT, 'data')


@contextlib.contextmanager
def temporary_file(**kwargs):
    tmp_filename = tempfile.mktemp(**kwargs)
    try:
        yield tmp_filename
    finally:
        try:
            os.unlink(tmp_filename)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise
