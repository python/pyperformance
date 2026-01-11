import pathlib
import tempfile
import unittest

from pyperformance import _pyproject_toml


class TestPyProjectToml(unittest.TestCase):
    def test_parse_project_with_readme_string(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = pathlib.Path(tmpdir)
            toml_content = """
            [project]
            name = "my-test-bench"
            version = "1.0"
            readme = "README.md"
            """
            (tmp_path / "README.md").touch()

            data = _pyproject_toml.parse_pyproject_toml(
                toml_content, rootdir=str(tmp_path), requirefiles=True
            )
            self.assertEqual(data["project"]["readme"]["file"], "README.md")

    def test_parse_full_valid_project_section(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            toml_content = """
            [project]
            name = "my-full-bench"
            version = "2.1.3"
            dependencies = [
                "pyperf",
                "six",
            ]
            requires-python = ">=3.12"
            """
            data = _pyproject_toml.parse_pyproject_toml(
                toml_content, rootdir=str(tmpdir)
            )
            project = data["project"]
            self.assertEqual(project["name"], "my-full-bench")
            self.assertEqual(project["version"], "2.1.3")
            self.assertEqual(project["dependencies"], ["pyperf", "six"])
            self.assertEqual(project["requires-python"], ">=3.12")

    def test_parse_fails_on_missing_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            toml_content = """
            [project]
            version = "1.0"
            """

            with self.assertRaisesRegex(ValueError, r'missing required "name" field'):
                _pyproject_toml.parse_pyproject_toml(toml_content, rootdir=str(tmpdir))

    def test_parse_fails_on_unsupported_section(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            toml_content = """
            [project]
            name = "my-test-bench"
            version = "1.0"

            [foobar]
            key = "value"
            """

            with self.assertRaisesRegex(ValueError, "unsupported sections"):
                _pyproject_toml.parse_pyproject_toml(toml_content, rootdir=str(tmpdir))

    def test_parse_readme_file_missing_with_requirefiles_true(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            toml_content = """
            [project]
            name = "my-test-bench"
            version = "1.0"
            readme = "MISSING_README.md"
            """

            with self.assertRaisesRegex(ValueError, "does not exist"):
                _pyproject_toml.parse_pyproject_toml(
                    toml_content, rootdir=str(tmpdir), requirefiles=True
                )

    def test_parse_readme_file_missing_with_requirefiles_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            toml_content = """
            [project]
            name = "my-test-bench"
            version = "1.0"
            readme = "MISSING_README.md"
            """
            data = _pyproject_toml.parse_pyproject_toml(
                toml_content, rootdir=str(tmpdir), requirefiles=False
            )
            self.assertEqual(data["project"]["readme"]["file"], "MISSING_README.md")


if __name__ == "__main__":
    unittest.main()
