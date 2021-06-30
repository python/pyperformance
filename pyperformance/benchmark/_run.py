import sys

import pyperf

from .. import _utils


def run_perf_script(python, runscript, *,
                    venv=None,
                    extra_opts=None,
                    pyperf_opts=None,
                    verbose=False,
                    ):
    if not runscript:
        raise ValueError('missing runscript')
    if not isinstance(runscript, str):
        raise TypeError(f'runscript must be a string, got {runscript!r}')
    if venv and python == sys.executable:
        python = venv.get_python_program()
    cmd = [
        python, '-u', runscript,
        *(extra_opts or ()),
        *(pyperf_opts or ()),
    ]

    with _utils.temporary_file() as tmp:
        cmd.extend(('--output', tmp))
        _utils.run_command(cmd, hide_stderr=not verbose)
        return pyperf.BenchmarkSuite.load(tmp)
