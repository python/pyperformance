import os
import sys

import pyperf

from .. import _utils


def run_perf_script(python, runscript, *,
                    venv=None,
                    extra_opts=None,
                    pyperf_opts=None,
                    libsdir=None,
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
    env = dict(os.environ)
    if libsdir:
        PYTHONPATH = os.environ.get('PYTHONPATH', '').split(os.pathsep)
        PYTHONPATH.insert(0, libsdir)
        env['PYTHONPATH'] = os.pathsep.join(PYTHONPATH)

    with _utils.temporary_file() as tmp:
        cmd.extend(('--output', tmp))
        _utils.run_command(cmd, env=env, hide_stderr=not verbose)
        return pyperf.BenchmarkSuite.load(tmp)
