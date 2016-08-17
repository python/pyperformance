#!/usr/bin/env python
"""Wrapper script for testing the performance of the html5lib HTML 5 parser.

The input data is the spec document for HTML 5, written in HTML 5.
The spec was pulled from http://svn.whatwg.org/webapps/index.
"""
from __future__ import with_statement

__author__ = "collinwinter@google.com (Collin Winter)"

import StringIO
import io
import os.path

import html5lib
import perf.text_runner
from six.moves import xrange


def bench_html5lib(loops, html_file):
    t0 = perf.perf_counter()
    for _ in xrange(loops):
        html_file.seek(0)
        html5lib.parse(html_file)
    return perf.perf_counter() - t0


if __name__ == "__main__":
    runner = perf.text_runner.TextRunner(name='html5lib')
    runner.metadata['description'] = ("Test the performance of the html5lib parser.")
    runner.metadata['html5lib_version'] = html5lib.__version__

    # Get all our IO over with early.
    filename = os.path.join(os.path.dirname(__file__), "data", "w3_tr_html5.html")
    with io.open(filename, "rb") as fp:
        html_file = StringIO.StringIO(fp.read())

    runner.bench_sample_func(bench_html5lib, html_file)
