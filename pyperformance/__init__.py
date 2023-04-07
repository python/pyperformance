import os.path
import sys


VERSION = (1, 0, 6)
__version__ = '.'.join(map(str, VERSION))


PKG_ROOT = os.path.dirname(__file__)
DATA_DIR = os.path.join(PKG_ROOT, 'data-files')


def is_installed():
    if not is_dev():
        return True
    if _is_venv():
        return True
    return _is_devel_install()


def is_dev():
    parent = os.path.dirname(PKG_ROOT)
    return os.path.exists(os.path.join(parent, 'setup.py'))


def _is_venv():
    if sys.base_prefix == sys.prefix:
        return False
    return True


def _is_devel_install():
    # pip install -e <path-to-git-checkout> will do a "devel" install.
    # This means it creates a link back to the checkout instead
    # of copying the files.
    try:
        import toml
    except ModuleNotFoundError:
        return False
    sitepackages = os.path.dirname(os.path.dirname(toml.__file__))
    if os.path.isdir(os.path.join(sitepackages, 'pyperformance')):
        return False
    if not os.path.exists(os.path.join(sitepackages, 'pyperformance.egg-link')):
        # XXX Check the contents?
        return False
    return True
