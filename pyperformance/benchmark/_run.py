import pyperf

from .. import _utils


def run_perf_script(python, runscript, *,
                    extra_opts=None,
                    pyperf_opts=None,
                    verbose=False,
                    ):
    if not runscript:
        raise ValueError('missing runscript')
    if not isinstance(runscript, str):
        raise TypeError(f'runscript must be a string, got {runscript!r}')
    if isinstance(python, str):
        python = [python]
    cmd = [
        *python, '-u', runscript,
        *(extra_opts or ()),
        *(pyperf_opts or ()),
    ]

    with _utils.temporary_file() as tmp:
        cmd.extend(('--output', tmp))
        _utils.run_command(cmd, hide_stderr=not verbose)
        return pyperf.BenchmarkSuite.load(tmp)
