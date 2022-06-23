"""
Convert Docutils' documentation from reStructuredText to <format>.
"""

import contextlib
from pathlib import Path
import time

import docutils
from docutils import core
import pyperf

try:
    from docutils.utils.math.math2html import Trace
except ImportError:
    pass
else:
    Trace.show = lambda message, channel: ...  # don't print to console

DOC_ROOT = (Path(__file__).parent / "data" / "docs").resolve()


def build_html(doc_root):
    elapsed = 0
    for file in doc_root.rglob("*.txt"):
        file_contents = file.read_text(encoding="utf-8")
        t0 = time.perf_counter_ns()
        with contextlib.suppress(docutils.ApplicationError):
            core.publish_string(source=file_contents,
                                reader_name="standalone",
                                parser_name="restructuredtext",
                                writer_name="html5",
                                settings_overrides={
                                    "input_encoding": "unicode",
                                    "output_encoding": "unicode",
                                    "report_level": 5,
                                })
        elapsed += time.perf_counter_ns() - t0
    return elapsed


def bench_docutils(loops, doc_root):
    runs_total_ns = 0

    for _ in range(loops):
        runs_total_ns += build_html(doc_root)

    return runs_total_ns / 10**9


if __name__ == "__main__":
    runner = pyperf.Runner()

    runner.metadata['description'] = "Render documentation with Docutils"
    args = runner.parse_args()

    runner.bench_time_func("docutils", bench_docutils, DOC_ROOT)
