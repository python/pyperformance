import os.path


VERSION = (1, 0, 3)
__version__ = '.'.join(map(str, VERSION))


PKG_ROOT = os.path.dirname(__file__)
DATA_DIR = os.path.join(PKG_ROOT, 'data-files')


def is_installed():
    parent = os.path.dirname(PKG_ROOT)
    return os.path.exists(os.path.join(parent, 'setup.py'))
