# A script for running pyperformance out of the repo in dev-mode.

import os.path
import shutil
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
VENVS = os.path.join(REPO_ROOT, ".venvs")


def resolve_venv_root(kind="dev", venvsdir=VENVS):
    import sysconfig

    if sysconfig.is_python_build():
        sys.exit("please install your built Python first (or pass it using --python)")
    # XXX Handle other implementations too?
    base = os.path.join(venvsdir, kind or "dev")
    major, minor = sys.version_info[:2]
    pyloc = (
        (os.path.abspath(sys.executable)).partition(os.path.sep)[2].lstrip(os.path.sep)
    ).replace(os.path.sep, "-")
    return f"{base}-{major}.{minor}-{pyloc}"


def ensure_venv_ready(venvroot=None, kind="dev", venvsdir=VENVS):
    if sys.prefix != sys.base_prefix:
        assert os.path.exists(os.path.join(sys.prefix, "pyvenv.cfg"))
        venvroot = sys.prefix
        python = sys.executable
        readyfile = os.path.join(sys.prefix, "READY")
        isready = os.path.exists(readyfile)
    else:
        if not venvroot:
            venvroot = resolve_venv_root(kind, venvsdir)
        # Make sure the venv exists.
        readyfile = os.path.join(venvroot, "READY")
        isready = os.path.exists(readyfile)
        if not isready:
            relroot = os.path.relpath(venvroot)
            uv = shutil.which("uv")
            if not uv:
                sys.exit(
                    "ERROR: uv executable not found. "
                    "Install uv from https://astral.sh/uv and retry."
                )
            if os.path.exists(venvroot):
                print(f"uv env {relroot} not ready, re-creating...")
                shutil.rmtree(venvroot)
            else:
                print(f"creating uv env at {relroot}...")
            result = subprocess.run(
                [
                    uv,
                    "venv",
                    "--python",
                    sys.executable,
                    venvroot,
                ]
            )
            if result.returncode != 0:
                sys.exit("ERROR: uv venv creation failed")
        else:
            assert os.path.exists(os.path.join(venvroot, "pyvenv.cfg"))
        # Return the venv's Python executable.
        binname = "Scripts" if os.name == "nt" else "bin"
        exename = os.path.basename(sys.executable)
        python = os.path.join(venvroot, binname, exename)

    # Now make sure the venv has pyperformance installed.
    if not isready:
        relroot = os.path.relpath(venvroot)
        print(f"uv env {relroot} not ready, installing dependencies...")
        uv = shutil.which("uv")
        if not uv:
            sys.exit(
                "ERROR: uv executable not found. "
                "Install uv from https://astral.sh/uv and retry."
            )
        proc = subprocess.run(
            [
                uv,
                "pip",
                "install",
                "--python",
                python,
                "--upgrade",
                "--editable",
                f"{REPO_ROOT}[dev]",
            ],
        )
        if proc.returncode != 0:
            sys.exit("ERROR: uv pip install failed")
        with open(readyfile, "w"):
            pass
        print(f"...uv env {relroot} ready!")

    return venvroot, python


def main(venvroot=None):
    _, python = ensure_venv_ready(venvroot)
    if python != sys.executable:
        # Now re-run using the venv.
        os.execv(python, [python, *sys.argv])
        # <unreachable>

    # Now run pyperformance.
    import pyperformance.cli

    pyperformance.cli.main()


if __name__ == "__main__":
    main()
