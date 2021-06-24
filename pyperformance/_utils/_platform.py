import logging
import subprocess
import sys


MS_WINDOWS = (sys.platform == 'win32')


def run_command(command, hide_stderr=True):
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
