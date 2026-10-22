import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from pyperformance import (
    _benchmark,
    _benchmark_metadata,
    _manifest,
    _pythoninfo,
    _venv,
    cli,
    commands,
)


def target_info(name, version, implementation_version=None):
    """Return minimal interpreter information for selection tests.

    name: Value reported by sys.implementation.name.
    version: Python language version.
    implementation_version: Implementation version, defaulting to the language version.
    Return: Interpreter information containing the fields used by selection.
    """
    implementation = SimpleNamespace(
        name=name, version=implementation_version or version
    )
    return SimpleNamespace(
        sys=SimpleNamespace(version_info=version, implementation=implementation)
    )


class BenchmarkCompatibilityTests(unittest.TestCase):
    """Exercise compatibility metadata and selection for the target interpreter."""

    def setUp(self):
        """Provide an isolated directory for benchmark metadata."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.cpython = target_info("cpython", (3, 12, 0))
        self.pypy = target_info("pypy", (3, 11, 0), (7, 3, 23))

    def write_benchmark(self, name, tool_text="", requires_python=">=3.10"):
        """Write one benchmark's metadata in the isolated directory.

        name: Benchmark name used for its directory and metadata.
        tool_text: Additional TOML lines in the pyperformance tool section.
        requires_python: Python language-version requirement.
        Return: Path to the new metadata file.
        """
        directory = self.root / ("bm_" + name)
        directory.mkdir()
        path = directory / "pyproject.toml"
        path.write_text(
            f'[project]\nname = "pyperformance_bm_{name}"\nversion = "1.0"\n'
            f'requires-python = "{requires_python}"\n\n'
            f'[tool.pyperformance]\nname = "{name}"\n{tool_text}\n'
        )
        return path

    def make_manifest(self):
        """Create a catalog with portable, restricted, and version-gated cases.

        Return: The loaded manifest and its file path.
        """
        paths = {
            "portable": self.write_benchmark("portable"),
            "cpython_only": self.write_benchmark(
                "cpython_only", 'python_implementations = ["cpython"]'
            ),
            "new_python": self.write_benchmark("new_python", requires_python=">=3.12"),
        }
        path = self.root / "MANIFEST"
        text = "[benchmarks]\n\nname\tmetafile\n"
        text += "".join(f"{name}\t{metafile}\n" for name, metafile in paths.items())
        text += "\n[group default]\nportable\ncpython_only\nnew_python\n"
        text += "\n[group gc]\nportable\ncpython_only\n"
        path.write_text(text)
        return _manifest.load_manifest(str(path)), path

    def select(self, selection, manifest, info):
        """Resolve one selection while retaining its user-facing notices.

        selection: Command-line benchmark selection.
        manifest: Catalog containing the test benchmarks.
        info: Target interpreter information.
        Return: Sorted selected names and captured stderr.
        """
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            selected = cli._select_benchmarks(selection, manifest, info)
        return sorted(benchmark.name for benchmark in selected), stderr.getvalue()

    def test_omitted_metadata_allows_every_implementation(self):
        """An unrestricted benchmark should expose no implementation filter."""
        path = self.write_benchmark("portable")
        metadata, _ = _benchmark_metadata.load_metadata(str(path))
        self.assertNotIn("python_implementations", metadata)
        benchmark = _benchmark.Benchmark(
            _benchmark.BenchmarkSpec("portable", "1.0"), str(path)
        )
        self.assertFalse(benchmark.python_implementations)

    def test_metadata_normalizes_names(self):
        """Names should be case-insensitive without requiring a central registry."""
        path = self.write_benchmark(
            "restricted", 'python_implementations = ["CPython", "PyPy", "New_Python"]'
        )
        metadata, _ = _benchmark_metadata.load_metadata(str(path))
        self.assertEqual(
            metadata["python_implementations"], ["cpython", "pypy", "new_python"]
        )

    def test_metadata_inherits_and_replaces_restrictions(self):
        """Variants should inherit a restriction unless they supply another list."""
        base = self.write_benchmark("base", 'python_implementations = ["cpython"]')
        inherited = base.parent / "bm_inherited.toml"
        inherited.write_text('[tool.pyperformance]\nname = "inherited"\n')
        overridden = base.parent / "bm_overridden.toml"
        overridden.write_text(
            '[tool.pyperformance]\nname = "overridden"\npython_implementations = ["PyPy"]\n'
        )

        metadata, _ = _benchmark_metadata.load_metadata(str(inherited))
        self.assertEqual(metadata["python_implementations"], ["cpython"])
        metadata, _ = _benchmark_metadata.load_metadata(str(overridden))
        self.assertEqual(metadata["python_implementations"], ["pypy"])

    def test_invalid_implementation_metadata(self):
        """Malformed restrictions should fail while metadata is loaded."""
        cases = (
            ('"cpython"', TypeError),
            ("[]", ValueError),
            ("[1]", TypeError),
            ('[""]', ValueError),
            ('["bad name"]', ValueError),
        )
        for index, (value, error) in enumerate(cases):
            with self.subTest(value=value):
                path = self.write_benchmark(
                    f"invalid_{index}", "python_implementations = " + value
                )
                with self.assertRaises(error):
                    _benchmark_metadata.load_metadata(str(path))

    def test_selection_uses_target_compatibility(self):
        """Names and groups should use the target language and implementation."""
        manifest, _ = self.make_manifest()
        cases = (
            ("default", ["cpython_only", "new_python", "portable"], ["portable"], True),
            ("all", ["cpython_only", "new_python", "portable"], ["portable"], True),
            ("gc", ["cpython_only", "portable"], ["portable"], True),
            ("portable", ["portable"], ["portable"], False),
            ("cpython_only", ["cpython_only"], [], True),
            ("portable,cpython_only", ["cpython_only", "portable"], ["portable"], True),
            ("all,-cpython_only", ["new_python", "portable"], ["portable"], False),
        )
        notice = "Skipping cpython_only: target implementation pypy is not supported (supported: cpython)\n"
        for selection, cpython_names, pypy_names, skipped in cases:
            with self.subTest(selection=selection, implementation="cpython"):
                self.assertEqual(
                    self.select(selection, manifest, self.cpython), (cpython_names, "")
                )
            with self.subTest(selection=selection, implementation="pypy"):
                self.assertEqual(
                    self.select(selection, manifest, self.pypy),
                    (pypy_names, notice if skipped else ""),
                )

    def test_implementation_notice_when_version_is_also_unsupported(self):
        """An implementation restriction should remain visible when both checks fail."""
        metadata = self.write_benchmark(
            "cpython_new",
            'python_implementations = ["cpython"]',
            requires_python=">=3.12",
        )
        path = self.root / "MANIFEST"
        path.write_text(f"[benchmarks]\n\nname\tmetafile\ncpython_new\t{metadata}\n")
        manifest = _manifest.load_manifest(str(path))
        names, stderr = self.select("cpython_new", manifest, self.pypy)
        self.assertEqual(names, [])
        self.assertEqual(
            stderr,
            "Skipping cpython_new: target implementation pypy is not supported (supported: cpython)\n",
        )

    def test_empty_run_stops_before_benchmark_preparation(self):
        """An empty selection should fail before preparing benchmark environments."""
        options = SimpleNamespace(output=None, python=sys.executable)
        stdout = io.StringIO()
        with (
            mock.patch("pyperformance.run.run_benchmarks") as run_benchmarks,
            contextlib.redirect_stdout(stdout),
        ):
            with self.assertRaises(SystemExit) as error:
                commands.cmd_run(options, [])
        self.assertEqual(error.exception.code, 1)
        self.assertIn("ERROR: No benchmark was run", stdout.getvalue())
        run_benchmarks.assert_not_called()

    def test_registered_gc_benchmarks_use_supported_implementations(self):
        """Normal and all selections should retain portable GC coverage on PyPy."""
        manifest = _manifest.load_manifest(None)
        portable = {"gc_collect_large", "gc_collect_self_lists", "gc_tuple_survivors"}
        restricted = {
            "btree_gc_only_frozen",
            "gc_weakref_recheck",
            "gc_resurrection_partial",
            "gc_resurrection_full",
        }
        for selection in ("default", "all"):
            with self.subTest(selection=selection, implementation="cpython"):
                names, _ = self.select(selection, manifest, self.cpython)
                self.assertTrue(portable | restricted <= set(names))
            with self.subTest(selection=selection, implementation="pypy"):
                names, stderr = self.select(selection, manifest, self.pypy)
                self.assertTrue(portable <= set(names))
                self.assertTrue(restricted.isdisjoint(names))
                for name in restricted:
                    self.assertIn(
                        f"Skipping {name}: target implementation pypy is not supported",
                        stderr,
                    )

    def test_dispatch_selects_for_the_effective_interpreter(self):
        """Commands should select for the interpreter they pass to execution."""
        _, manifest_path = self.make_manifest()

        def get_info(executable=sys.executable):
            """Return the synthetic interpreter named by the command."""
            if executable == "/target-pypy":
                return self.pypy
            if executable == sys.executable:
                return self.cpython
            raise AssertionError(f"unexpected interpreter: {executable}")

        cases = (
            ("run", None, False, ["portable"]),
            ("list", None, False, ["portable"]),
            ("venv", "create", False, ["portable"]),
            ("venv", "recreate", False, ["portable"]),
            ("venv", "create", True, ["cpython_only", "new_python", "portable"]),
            ("venv", "recreate", True, ["cpython_only", "new_python", "portable"]),
        )
        for action, venv_action, explicit_venv, expected in cases:
            with self.subTest(
                action=action, venv_action=venv_action, explicit_venv=explicit_venv
            ):
                options = SimpleNamespace(
                    action=action,
                    python="/target-pypy",
                    benchmarks="all",
                    manifest=str(manifest_path),
                    venv="/explicit-venv" if explicit_venv else None,
                    venv_action=venv_action,
                )
                command_name = (
                    "cmd_venv_" + venv_action if action == "venv" else "cmd_" + action
                )
                with contextlib.ExitStack() as stack:
                    stack.enter_context(
                        mock.patch.object(cli, "is_installed", return_value=True)
                    )
                    stack.enter_context(
                        mock.patch.object(
                            cli, "parse_args", return_value=(mock.Mock(), options)
                        )
                    )
                    stack.enter_context(
                        mock.patch.object(_pythoninfo, "get_info", side_effect=get_info)
                    )
                    stack.enter_context(
                        mock.patch.object(
                            _venv, "get_venv_root", return_value="/generated-venv"
                        )
                    )
                    command = stack.enter_context(mock.patch.object(cli, command_name))
                    stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
                    cli._main()
                command.assert_called_once()
                selected = command.call_args.args[-1]
                self.assertEqual(
                    sorted(benchmark.name for benchmark in selected), expected
                )
                if action == "venv":
                    self.assertIs(
                        command.call_args.args[-2], None if explicit_venv else self.pypy
                    )


if __name__ == "__main__":
    unittest.main()
