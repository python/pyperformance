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


def _iter_requirements(*reqs):
    for item in reqs:
        if item is None:
            continue
        if isinstance(item, os.PathLike):
            yield os.fspath(item)
            continue
        if isinstance(item, bytes):
            yield item.decode()
            continue
        if isinstance(item, str):
            yield item
            continue
        specs = getattr(item, "specs", None)
        if specs is not None:
            yield from _iter_requirements(*specs)
            continue
        if isinstance(item, (list, tuple, set)):
            yield from _iter_requirements(*item)
            continue
        try:
            iterator = iter(item)
        except TypeError:
            yield str(item)
        else:
            yield from _iter_requirements(*iterator)


def install_requirements(
    *reqs,
    python,
    upgrade=True,
    env=None,
    verbose=True,
):
    requirements = list(_iter_requirements(*reqs))
    if not requirements:
        return 0, None, None

    args = [
        "pip",
        "install",
        "--python",
        python,
    ]
    if upgrade:
        args.append("--upgrade")

    for spec in requirements:
        if os.path.isfile(spec) and spec.endswith(".txt"):
            args.extend(["-r", spec])
        else:
            args.append(spec)

    ec, stdout, stderr = run_uv(*args, env=env, verbose=verbose)
    if ec == 127:
        first, *rest = requirements
        return _pip.install_requirements(
            first,
            *rest,
            python=python,
            env=env,
            upgrade=upgrade,
        )
    return ec, stdout, stderr
