"""
Measures the time it takes to import all the modules (excluding those with
import side effects) in the stdlib.

This benchmark is expected to change as the stdlib changes, so it is not
suitable for measuring compilation time.
"""

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
        modules_to_import = sorted(sys.stdlib_module_names - {'antigravity', 'this'})
        with open(main, 'w', encoding='utf-8') as f:
            for module in modules_to_import:
                f.write(f"""
try:
    import {module}
except ImportError:
    pass
""")
        command = [sys.executable, main]
        runner.bench_command('stdlib_startup', command)
