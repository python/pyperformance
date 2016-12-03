"""
Benchmark Python startup.
"""
import sys
import subprocess

import perf
from six.moves import xrange


# common stdlibs. Many applications imports them directly, or indirectly.
IMPORT_COMMON_STDLIBS = """\
import abc
import argparse
import collections
import copy
import ctypes
import datetime
#import enum  # Python >=3.4
import functools
import io
import json
import logging
import os
#import pathlib  # Python >=3.4
import re
import socket
import struct
import subprocess
import tempfile
import threading
import types
#import typing  # Python >=3.5
import urllib
"""


def bench_startup(loops, command):
    run = subprocess.check_call
    range_it = xrange(loops)
    t0 = perf.perf_counter()

    for _ in range_it:
        run(command)

    return perf.perf_counter() - t0


def add_cmdline_args(cmd, args):
    if args.no_site:
        cmd.append("--no-site")
    if args.stdlibs:
        cmd.append("--stdlibs")


if __name__ == "__main__":
    runner = perf.Runner(samples=10, add_cmdline_args=add_cmdline_args)
    runner.argparser.add_argument("--no-site", action="store_true")
    runner.argparser.add_argument("--stdlibs", action="store_true")

    runner.metadata['description'] = "Performance of the Python startup"
    args = runner.parse_args()
    name = 'python_startup'
    if args.no_site:
        name += "_no_site"
    if args.stdlibs:
        name += "_stdlibs"

    command = [sys.executable]
    if args.no_site:
        command.append("-S")
    if args.stdlibs:
        command.extend(("-c", IMPORT_COMMON_STDLIBS))
    else:
        command.extend(("-c", "pass"))

    runner.bench_sample_func(name, bench_startup, command)
