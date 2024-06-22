"""
A simple pypdf benchmark.

Adapted from pypdf's own benchmarks:

   https://github.com/py-pdf/pypdf/blob/main/tests/bench.py
"""

import io
from pathlib import Path


from pypdf import PdfReader, PdfWriter, Transformation
import pyperf


DATA_DIR = Path(__file__).parent / "data"


def page_ops(stream, password):
    reader = PdfReader(stream)
    writer = PdfWriter()

    if password:
        reader.decrypt(password)

    page = reader.pages[0]
    writer.add_page(page)

    op = Transformation().rotate(90).scale(1.2)
    page.add_transformation(op)
    page.merge_page(page)

    op = Transformation().scale(1).translate(tx=1, ty=1)
    page.add_transformation(op)
    page.merge_page(page)

    op = Transformation().rotate(90).scale(1).translate(tx=1, ty=1)
    page.add_transformation(op)
    page.merge_page(page)

    page.add_transformation((1, 0, 0, 0, 0, 0))
    page.scale(2, 2)
    page.scale_by(0.5)
    page.scale_to(100, 100)

    page = writer.pages[0]
    page.compress_content_streams()
    page.extract_text()


def bench_page_ops(loops):
    """
    Apply various page operations.

    Rotation, scaling, translation, content stream compression, text extraction
    """
    content = (DATA_DIR / "libreoffice-writer-password.pdf").read_bytes()
    stream = io.BytesIO(content)

    t0 = pyperf.perf_counter()
    for _ in range(loops):
        page_ops(stream, "openpassword")
    return pyperf.perf_counter() - t0


BENCHMARKS = ("page_ops",)


def add_cmdline_args(cmd, args):
    if args.benchmark:
        cmd.append(args.benchmark)


if __name__ == "__main__":
    runner = pyperf.Runner(add_cmdline_args=add_cmdline_args)
    runner.metadata["description"] = "pypdf benchmark"
    runner.argparser.add_argument("benchmark", nargs="?", choices=BENCHMARKS)

    args = runner.parse_args()
    if args.benchmark:
        benchmarks = (args.benchmark,)
    else:
        benchmarks = BENCHMARKS

    for bench in benchmarks:
        name = f"pypdf_{bench}"
        func = globals()[f"bench_{bench}"]
        runner.bench_time_func(name, func)
