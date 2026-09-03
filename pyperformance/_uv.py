"""Utilities for invoking the ``uv`` CLI."""

import os
import os.path
import shutil

from . import _pip, _utils


def run_uv(*args, env=None, capture=None, verbose=True):
    uv = shutil.which("uv")
    if not uv:
        if verbose:
            print(
                "ERROR: uv executable not found. Install uv from https://astral.sh/uv."
            )
        return 127, None, None
    return _utils.run_cmd([uv, *args], env=env, capture=capture, verbose=verbose)


def install_requirements(reqs, *extra, python, upgrade=True, env=None, verbose=True):
    args = [
        "pip",
        "install",
        "--python",
        python,
    ]
    if upgrade:
        args.append("--upgrade")

    for spec in (reqs, *extra):
        if spec is None:
            continue
        if isinstance(spec, os.PathLike):
            spec = os.fspath(spec)
        if os.path.isfile(spec) and spec.endswith(".txt"):
            args.extend(["-r", spec])
        else:
            args.append(spec)

    ec, stdout, stderr = run_uv(*args, env=env, verbose=verbose)
    if ec == 127:
        return _pip.install_requirements(
            reqs, *extra, python=python, env=env, upgrade=upgrade
        )
    return ec, stdout, stderr
