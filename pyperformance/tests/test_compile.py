import os
import pathlib
import tempfile
import textwrap
import types
import unittest
from unittest import mock

from pyperformance import compile as compile_mod


class ParseConfigTests(unittest.TestCase):
    def test_parse_config_reads_tail_call_interp(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            config_path = root / "benchmark.conf"
            config_path.write_text(
                textwrap.dedent(
                    f"""\
                    [config]
                    json_dir = {root / "json"}

                    [scm]
                    repo_dir = {root / "cpython"}

                    [compile]
                    bench_dir = {root / "bench"}
                    tail_call_interp = true

                    [run_benchmark]
                    """
                ),
                encoding="utf-8",
            )

            conf = compile_mod.parse_config(str(config_path), "compile")

            self.assertTrue(conf.tail_call_interp)


class CompileCommandTests(unittest.TestCase):
    def test_compile_adds_tail_call_interp_flag(self):
        conf = types.SimpleNamespace(
            build_dir="/tmp/build",
            repo_dir="/tmp/cpython",
            prefix="",
            debug=False,
            lto=False,
            pgo=True,
            jit="",
            tail_call_interp=True,
            pkg_only=[],
            jobs=0,
        )
        app = types.SimpleNamespace(
            branch="main",
            logger=None,
            safe_makedirs=mock.Mock(),
            run=mock.Mock(),
        )

        compile_mod.Python(app, conf).compile()

        configure_call = app.run.call_args_list[0]
        self.assertEqual(
            configure_call.args,
            (os.path.join(conf.repo_dir, "configure"), "--with-tail-call-interp"),
        )
        self.assertEqual(configure_call.kwargs, {"cwd": "/tmp/build"})


if __name__ == "__main__":
    unittest.main()
