import os
import sys
import subprocess
import tempfile

import pyperf

if __name__ == "__main__":
    runner = pyperf.Runner(values=10)

    runner.metadata['description'] = "Performance of importing standard library modules"
    args = runner.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        main = os.path.join(tmp, "main.py")
        with open(main, "w") as f:
            f.write("""
import importlib
import sys
for m in sys.stdlib_module_names:
    if m in {"antigravity", "this"}:
        continue
    try:
        importlib.import_module(m)
    except ImportError:
        pass
""")
        command = [sys.executable, main]
        runner.bench_command('stdlib_startup', command)
