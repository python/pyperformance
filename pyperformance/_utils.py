
__all__ = [
    # filesystem
    'temporary_file',
    'check_file',
    'check_dir',
    # platform
    'MS_WINDOWS',
    'run_command',
    # misc
    'check_name',
    'parse_name_pattern',
    'parse_tag_pattern',
    'parse_selections',
    'iter_clean_lines',
]


#######################################
# filesystem utils

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


def resolve_file(filename, relroot=None):
    resolved = os.path.normpath(filename)
    resolved = os.path.expanduser(resolved)
    #resolved = os.path.expandvars(filename)
    if not os.path.isabs(resolved):
        if not relroot:
            relroot = os.getcwd()
        elif not os.path.isabs(relroot):
            raise NotImplementedError(relroot)
        resolved = os.path.join(relroot, resolved)
    return resolved


#######################################
# platform utils

import logging
import subprocess
import sys


MS_WINDOWS = (sys.platform == 'win32')


def run_command(command, env=None, *, hide_stderr=True):
    if hide_stderr:
        kw = {'stderr': subprocess.PIPE}
    else:
        kw = {}

    logging.info("Running `%s`",
                 " ".join(list(map(str, command))))

    # Explicitly flush standard streams, required if streams are buffered
    # (not TTY) to write lines in the expected order
    sys.stdout.flush()
    sys.stderr.flush()

    proc = subprocess.Popen(command,
                            universal_newlines=True,
                            env=env,
                            **kw)
    try:
        stderr = proc.communicate()[1]
    except:   # noqa
        if proc.stderr:
            proc.stderr.close()
        try:
            proc.kill()
        except OSError:
            # process already exited
            pass
        proc.wait()
        raise

    if proc.returncode != 0:
        if hide_stderr:
            sys.stderr.flush()
            sys.stderr.write(stderr)
            sys.stderr.flush()
        raise RuntimeError("Benchmark died")


#######################################
# misc utils

def check_name(name, *, loose=False, allownumeric=False):
    if not name or not isinstance(name, str):
        raise ValueError(f'bad name {name!r}')
    if allownumeric:
        name = f'_{name}'
    if not loose:
        if name.startswith('-'):
            raise ValueError(name)
        if not name.replace('-', '_').isidentifier():
            raise ValueError(name)


def parse_name_pattern(text, *, fail=True):
    name = text
    # XXX Support globs and/or regexes?  (return a callable)
    try:
        check_name('_' + name)
    except Exception:
        if fail:
            raise  # re-raise
        return None
    return name


def parse_tag_pattern(text):
    if not text.startswith('<'):
        return None
    if not text.endswith('>'):
        return None
    tag = text[1:-1]
    # XXX Support globs and/or regexes?  (return a callable)
    check_name(tag)
    return tag


def parse_selections(selections, parse_entry=None):
    if isinstance(selections, str):
        selections = selections.split(',')
    if parse_entry is None:
        parse_entry = (lambda o, e: (o, e, None, e))

    for entry in selections:
        entry = entry.strip()
        if not entry:
            continue

        op = '+'
        if entry.startswith('-'):
            op = '-'
            entry = entry[1:]

        yield parse_entry(op, entry)


def iter_clean_lines(filename):
    with open(filename) as reqsfile:
        for line in reqsfile:
            # strip comment
            line = line.partition('#')[0]
            line = line.rstrip()
            if not line:
                continue
            yield line
