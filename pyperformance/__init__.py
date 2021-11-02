import os.path


VERSION = (1, 0, 3)
__version__ = '.'.join(map(str, VERSION))


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data-files')
