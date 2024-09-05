import sys

try:
    import pyperformance
except ModuleNotFoundError:
    sys.exit(0)
else:
    print(pyperformance.PKG_ROOT)

# Make sure pyperformance.PKG_ROOT matches expectations.
import os.path
datadir = os.path.dirname(os.path.abspath(__file__))
testsroot = os.path.dirname(datadir)
pkgroot = os.path.dirname(testsroot)
reporoot = os.path.realpath(os.path.dirname(pkgroot))
marker = os.path.join(reporoot, 'pyproject.toml')
if not os.path.exists(marker):
    sys.exit(f'ERROR: pyperformance is not an editable install ({reporoot})')
actual = os.path.realpath(os.path.abspath(pyperformance.PKG_ROOT))
if actual != os.path.join(reporoot, 'pyperformance'):
    print('ERROR: mismatch on pyperformance repo root:')
    print(f'  actual:   {actual}')
    print(f'  expected: {reporoot}')
    sys.exit(1)
