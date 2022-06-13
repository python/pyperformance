"""
Convert Docutils' documentation from reStructuredText to <format>.
"""

from pathlib import Path
import shutil

import docutils
from docutils import core
import pyperf

try:
    from docutils.utils.math.math2html import Trace
except ImportError:
    pass
else:
    Trace.show = lambda message, channel: ...  # don't print to console


def build_html(doc_root, out_root):
    for file in doc_root.rglob("*.txt"):
        try:
            dest = out_root / file.relative_to(doc_root).with_suffix(".html")
            dest.parent.mkdir(parents=True, exist_ok=True)
            core.publish_file(source_path=str(file),
                              destination_path=str(dest),
                              reader_name="standalone",
                              parser_name="restructuredtext",
                              writer_name="html5",
                              settings_overrides={
                                  "input_encoding": "utf-8",
                                  "report_level": 5,
                              })
        except docutils.ApplicationError:
            ...


def bench_docutils(loops, doc_root, out_root):
    runs = []

    for _ in range(loops):
        t0 = pyperf.perf_counter()
        build_html(doc_root, out_root)
        runs.append(pyperf.perf_counter() - t0)

        shutil.rmtree(out_root, ignore_errors=True)

    return sum(runs)


if __name__ == "__main__":
    runner = pyperf.Runner()

    runner.metadata['description'] = "Render documentation with Docutils"
    args = runner.parse_args()

    DOC_ROOT = Path("data/docs").resolve()
    OUT_ROOT = Path("data/out").resolve()

    runner.bench_time_func("docutils", bench_docutils, DOC_ROOT, OUT_ROOT)
