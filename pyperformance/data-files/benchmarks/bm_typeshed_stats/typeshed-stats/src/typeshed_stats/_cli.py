"""Command-line interface."""

from __future__ import annotations

import argparse
import logging
import pprint
import sys
from collections.abc import Sequence
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias, get_args

from typeshed_stats.gather import gather_stats_on_multiple_packages, tmpdir_typeshed

__all__ = ["main"]


_LoggingLevels: TypeAlias = Literal[
    "NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
]


def _get_argument_parser() -> argparse.ArgumentParser:
    """Parse arguments and do basic argument validation.

    *Don't* do any querying of whether paths actually exist, etc.
    Leave that to _validate_options().
    """
    parser = argparse.ArgumentParser(
        prog="typeshed-stats", description="Tool to gather stats on typeshed"
    )
    parser.add_argument(
        "packages",
        type=str,
        nargs="*",
        action="extend",
        help=(
            "Packages to gather stats on"
            " (defaults to all third-party packages, plus the stdlib)"
        ),
    )
    parser.add_argument(
        "--log",
        choices=get_args(_LoggingLevels),
        default="INFO",
        help="Specify the level of logging (defaults to logging.INFO)",
        dest="logging_level",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Whether to pprint results or not (defaults to False)",
    )

    typeshed_options = parser.add_argument_group(title="Typeshed options")
    typeshed_options_group = typeshed_options.add_mutually_exclusive_group(
        required=True
    )
    typeshed_options_group.add_argument(
        "-t",
        "--typeshed-dir",
        type=Path,
        help="Path to a local clone of typeshed, to be used as the basis for analysis",
    )
    typeshed_options_group.add_argument(
        "-d",
        "--download-typeshed",
        action="store_true",
        help=(
            "Download a fresh copy of typeshed into a temporary directory,"
            " and use that as the basis for analysis"
        ),
    )

    return parser


@dataclass(init=False)
class _CmdArgs:
    logging_level: _LoggingLevels
    packages: list[str]
    typeshed_dir: Path | None
    download_typeshed: bool
    overwrite: bool
    writefile: Path | None
    pretty: bool


def _validate_packages(
    package_names: list[str], typeshed_dir: Path, *, parser: argparse.ArgumentParser
) -> None:
    stubs_dir = typeshed_dir / "stubs"
    for package_name in package_names:
        if package_name != "stdlib":
            package_dir = stubs_dir / package_name
            if not (package_dir.exists() and package_dir.is_dir()):
                parser.error(f"{package_name!r} does not have stubs in typeshed!")


def _validate_typeshed_dir(
    typeshed_dir: Path, *, parser: argparse.ArgumentParser
) -> None:
    for folder in typeshed_dir, (typeshed_dir / "stdlib"), (typeshed_dir / "stubs"):
        if not (folder.exists() and folder.is_dir()):
            parser.error(f'"{typeshed_dir}" is not a valid typeshed directory')


def _setup_logger(str_level: _LoggingLevels) -> logging.Logger:
    assert str_level in get_args(_LoggingLevels)
    logger = logging.getLogger("typeshed_stats")
    level = getattr(logging, str_level)
    assert isinstance(level, int)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    logger.addHandler(handler)
    return logger


def _run(argv: Sequence[str] | None = None) -> None:
    parser = _get_argument_parser()
    args: _CmdArgs = parser.parse_args(argv, namespace=_CmdArgs())
    logger = _setup_logger(args.logging_level)

    with ExitStack() as stack:
        if args.download_typeshed:
            logger.info("Cloning typeshed into a temporary directory...")
            typeshed_dir = stack.enter_context(tmpdir_typeshed())
        else:
            assert args.typeshed_dir is not None
            typeshed_dir = args.typeshed_dir
            _validate_typeshed_dir(typeshed_dir, parser=parser)

        packages: list[str] | None = args.packages or None
        if packages:
            _validate_packages(packages, typeshed_dir, parser=parser)

        logger.info("Gathering stats...")
        stats = gather_stats_on_multiple_packages(packages, typeshed_dir=typeshed_dir)

    pprint.pprint({info_bundle.package_name: info_bundle for info_bundle in stats})


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point."""
    try:
        _run(argv)
    except KeyboardInterrupt:
        sys.stderr.write("Interrupted!")
        code = 2
    else:
        code = 0
    raise SystemExit(code)
