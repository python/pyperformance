import contextlib
import errno
import os
import os.path
import tempfile


@contextlib.contextmanager
def temporary_file():
    tmp_filename = tempfile.mktemp()
    try:
        yield tmp_filename
    finally:
        try:
            os.unlink(tmp_filename)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise


def check_file(filename):
    if not os.path.isabs(filename):
        raise ValueError(f'expected absolute path, got {filename!r}')
    if not os.path.isfile(filename):
        raise ValueError(f'file missing ({filename})')


def check_dir(dirname):
    if not os.path.isabs(dirname):
        raise ValueError(f'expected absolute path, got {dirname!r}')
    if not os.path.isdir(dirname):
        raise ValueError(f'directory missing ({dirname})')
