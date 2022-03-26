import os
import os.path
import sys
import types
import unittest

from pyperformance import tests
import pyperformance._venv


def new_venv_config(root, home=None, version=None, prompt=None,
                    system_site_packages=False,
                    executable=None, command=None, *,
                    old=sys.version_info < (3, 11),
                    ):
    if not home:
        home = os.path.dirname(sys.executable)
    if not version:
        version = '.'.join(str(v) for v in sys.version_info[:3])
    if not isinstance(system_site_packages, str):
        system_site_packages = 'true' if system_site_packages else 'false'
    system_site_packages = (system_site_packages == 'true')
    if not old:
        if executable is None:
            executable = sys.executable
        if command is None:
            command = f'{executable} -m venv {root}'
    return types.SimpleNamespace(
        home=home,
        version=version,
        system_site_packages=system_site_packages,
        prompt=prompt,
        executable=executable,
        command=command,
    )


def render_venv_config(cfg):
    lines = [
        f'home = {cfg.home}',
        f'version = {cfg.version}',
        f'include-system-site-packages = {cfg.system_site_packages}',
    ]
    if cfg.prompt is not None:
        lines.append(f'prompt = {cfg.prompt}')
    if cfg.executable is not None:
        lines.append(f'executable = {cfg.executable}')
    if cfg.command is not None:
        lines.append(f'command = {cfg.command}')
    return ''.join(l + os.linesep for l in lines)


class VenvConfigTests(tests.Functional, unittest.TestCase):

    # Note that we do not call self.ensure_venv().

    def generate_config(self, root, **kwargs):
        if not os.path.isabs(root):
            root = self.resolve_tmp(root)
        cfg = new_venv_config(root, **kwargs)
        text = render_venv_config(cfg)

        os.makedirs(root)
        filename = os.path.join(root, 'pyvenv.cfg')
        with open(filename, 'w', encoding='utf-8') as outfile:
            outfile.write(text)
        return cfg, filename, root

    def test_read(self):
        expected, _, root = self.generate_config('spam')

        cfg = pyperformance._venv.read_venv_config(root)

        self.assertEqual(vars(cfg), vars(expected))

    def test_parse(self):
        expected = new_venv_config('spam')
        text = render_venv_config(expected)

        cfg = pyperformance._venv.parse_venv_config(text)

        self.assertEqual(vars(cfg), vars(expected))
