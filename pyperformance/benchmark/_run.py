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
        if pyperf_opts and '--copy-env' in pyperf_opts:
            argv, env = _prep_cmd(python, runscript, opts, runid, NOOP)
        else:
            opts, inherit_envvar = _resolve_restricted_opts(opts)
            argv, env = _prep_cmd(python, runscript, opts, runid, inherit_envvar)
        _utils.run_command(argv, env=env, hide_stderr=not verbose)

        return pyperf.BenchmarkSuite.load(tmp)


def run_other_script(python, script, runid, *,
                     extra_opts=None,
                     verbose=False
                     ):
    argv, env = _prep_cmd(python, script, extra_opts, runid)
    _utils.run_command(argv, env=env, hide_stderr=not verbose)


def _prep_cmd(python, script, opts, runid, on_set_envvar=None):
    # Populate the environment variables.
    env = dict(os.environ)
    def set_envvar(name, value):
        env[name] = value
        if on_set_envvar is not None:
            on_set_envvar(name)
    # on_set_envvar() may update "opts" so all calls to set_envvar()
    # must happen before building argv.
    set_envvar('PYPERFORMANCE_RUNID', str(runid))

    # Build argv.
    argv = [
        python, '-u', script,
        *(opts or ()),
    ]

    return argv, env


def _resolve_restricted_opts(opts):
    # Deal with --inherit-environ.
    FLAG = '--inherit-environ'
    resolved = []
    idx = None
    for i, opt in enumerate(opts):
        if opt.startswith(FLAG + '='):
            idx = i + 1
            resolved.append(FLAG)
            resolved.append(opt.partition('=')[-2])
            resolved.extend(opts[idx:])
            break
        elif opt == FLAG:
            idx = i + 1
            resolved.append(FLAG)
            resolved.append(opts[idx])
            resolved.extend(opts[idx + 1:])
            break
        else:
            resolved.append(opt)
    else:
        resolved.extend(['--inherit-environ', ''])
        idx = len(resolved) - 1
    inherited = set(resolved[idx].replace(',', ' ').split())
    def inherit_env_var(name):
        inherited.add(name)
        resolved[idx] = ','.join(inherited)

    return resolved, inherit_env_var


def _insert_on_PYTHONPATH(entry, env):
    PYTHONPATH = env.get('PYTHONPATH', '').split(os.pathsep)
    PYTHONPATH.insert(0, entry)
    env['PYTHONPATH'] = os.pathsep.join(PYTHONPATH)
