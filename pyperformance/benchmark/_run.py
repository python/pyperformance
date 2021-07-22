import argparse
import os

import pyperf

from .. import _utils


def run_perf_script(python, runscript, runid, *,
                    extra_opts=None,
                    pyperf_opts=None,
                    verbose=False,
                    ):
    if not runscript:
        raise ValueError('missing runscript')
    if not isinstance(runscript, str):
        raise TypeError(f'runscript must be a string, got {runscript!r}')

    with _utils.temporary_file() as tmp:
        opts = [
            *(extra_opts or ()),
            *(pyperf_opts or ()),
            '--output', tmp,
        ]
        prepargs = [python, runscript, opts, runid]
        if pyperf_opts and '--copy-env' in pyperf_opts:
            argv, env = _prep_basic(*prepargs)
        else:
            argv, env = _prep_restricted(*prepargs)

        _utils.run_command(argv, env=env, hide_stderr=not verbose)
        return pyperf.BenchmarkSuite.load(tmp)


def run_other_script(python, script, runid, *,
                     extra_opts=None,
                     verbose=False
                     ):
    argv, env = _prep_basic(python, script, extra_opts, runid)
    _utils.run_command(argv, env=env, hide_stderr=not verbose)


def _prep_restricted(python, script, opts_orig, runid):
    # Deal with --inherit-environ.
    FLAG = '--inherit-environ'
    opts = []
    idx = None
    for i, opt in enumerate(opts_orig):
        if opt.startswith(FLAG + '='):
            idx = i + 1
            opts.append(FLAG)
            opts.append(opt.partition('=')[-2])
            opts.extend(opts_orig[idx:])
            break
        elif opt == FLAG:
            idx = i + 1
            opts.append(FLAG)
            opts.append(opts_orig[idx])
            opts.extend(opts_orig[idx + 1:])
            break
        else:
            opts.append(opt)
    else:
        opts.extend(['--inherit-environ', ''])
        idx = len(opts) - 1
    inherited = set(opts[idx].replace(',', ' ').split())
    def inherit_env_var(name):
        inherited.add(name)
        opts[idx] = ','.join(inherited)

    # Track the environment variables.
    inherit_env_var('PYPERFORMANCE_RUNID')

    return _prep_basic(python, script, opts, runid)


def _prep_basic(python, script, opts, runid):
    # Build argv.
    argv = [
        python, '-u', script,
        *(opts or ()),
    ]

    # Populate the environment variables.
    env = dict(os.environ)
    env['PYPERFORMANCE_RUNID'] = str(runid)

    return argv, env


def _insert_on_PYTHONPATH(entry, env):
    PYTHONPATH = env.get('PYTHONPATH', '').split(os.pathsep)
    PYTHONPATH.insert(0, entry)
    env['PYTHONPATH'] = os.pathsep.join(PYTHONPATH)
