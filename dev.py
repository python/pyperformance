# A script for running pyperformance out of the repo in dev-mode.

import os.path
import sys


REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
VENV = os.path.join(REPO_ROOT, '.venvs', 'dev')


def main(venvroot=None):
    if sys.prefix != sys.base_prefix:  # already in a venv
        assert os.path.exists(os.path.join(sys.prefix, 'pyvenv.cfg'))
        # Make sure the venv has pyperformance installed.
        ready = os.path.join(sys.prefix, 'READY')
        if not os.path.exists(ready):
            import subprocess
            relroot = os.path.relpath(sys.prefix)
            print(f'venv {relroot} not ready, installing dependencies...')
            proc = subprocess.run(
                [sys.executable, '-m', 'pip', 'install',
                 '--upgrade',
                 '--editable', REPO_ROOT],
            )
            if proc.returncode != 0:
                sys.exit('ERROR: install failed')
            with open(ready, 'w'):
                pass
            print('...venv {relroot} ready!')
        # Now run pyperformance.
        import pyperformance.cli
        pyperformance.cli.main()
    else:
        import venv
        if not venvroot:
            import sysconfig
            if sysconfig.is_python_build():
                sys.exit('please install your built Python first (or pass it using --python)')
            # XXX Handle other implementations too?
            major, minor = sys.version_info[:2]
            pyloc = ((os.path.abspath(sys.executable)
                      ).partition(os.path.sep)[2].lstrip(os.path.sep)
                     ).replace(os.path.sep, '-')
            venvroot = f'{VENV}-{major}.{minor}-{pyloc}'
        # Make sure the venv exists.
        ready = os.path.join(venvroot, 'READY')
        if not os.path.exists(ready):
            relroot = os.path.relpath(venvroot)
            if not os.path.exists(venvroot):
                print(f'creating venv at {relroot}...')
            else:
                print(f'venv {relroot} not ready, re-creating...')
            venv.create(venvroot, with_pip=True, clear=True)
        # Now re-run dev.py using the venv.
        binname = 'Scripts' if os.name == 'nt' else 'bin'
        exename = os.path.basename(sys.executable)
        python = os.path.join(venvroot, binname, exename)
        os.execv(python, [python, *sys.argv])


if __name__ == '__main__':
    main()
