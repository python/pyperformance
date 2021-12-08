from collections import namedtuple
import hashlib
import sys
import time
import traceback
try:
    import multiprocessing
except ImportError:
    multiprocessing = None

import pyperformance
from . import _utils, _pythoninfo
from . import venv as _venv


class BenchmarkException(Exception):
    pass


class RunID(namedtuple('RunID', 'python compat bench timestamp')):

    def __new__(cls, python, compat, bench, timestamp):
        self = super().__new__(
            cls,
            python,
            compat,
            bench or None,
            int(timestamp) if timestamp else None,
        )
        return self

    def __str__(self):
        if not self.timestamp:
            return self.name
        return f'{self.name}-{self.timestamp}'

    @property
    def name(self):
        try:
            return self._name
        except AttributeError:
            name = f'{self.python}-compat-{self.compat}'
            if self.bench:
                name = f'{name}-bm-{self.bench.name}'
            self._name = name
            return self._name


def get_run_id(python, bench=None):
    py_id = _pythoninfo.get_python_id(python, prefix=True)
    compat_id = get_compatibility_id(bench)
    ts = time.time()
    return RunID(py_id, compat_id, bench, ts)


def run_benchmarks(should_run, python, options):
    to_run = sorted(should_run)

    runid = get_run_id(python)

    benchmarks = {}
    venvs = set()
    if options.venv:
        venv = _venv.VirtualEnvironment(
            options.python,
            options.venv,
            inherit_environ=options.inherit_environ,
        )
        venv.ensure(refresh=False)
        venvs.add(venv.get_path())
    for i, bench in enumerate(to_run):
        bench_runid = runid._replace(bench=bench)
        assert bench_runid.name, (bench, bench_runid)
        venv = _venv.VirtualEnvironment(
            options.python,
            options.venv,
            inherit_environ=options.inherit_environ,
            name=bench_runid.name,
            usebase=True,
        )
        print(f'({i+1:>2}/{len(to_run)}) creating venv for benchmark ({bench.name})')
        venv_path = venv.get_path()
        alreadyseen = venv_path in venvs
        venv.ensure(refresh=not alreadyseen)
        try:
            # XXX Do not override when there is a requirements collision.
            venv.install_reqs(bench)
        except _venv.RequirementsInstallationFailedError:
            print('(benchmark will be skipped)')
            print()
            venv = None
        venvs.add(venv_path)
        benchmarks[bench] = (venv, bench_runid)

    suite = None
    run_count = str(len(to_run))
    errors = []

    pyperf_opts = get_pyperf_opts(options)

    import pyperf
    for index, bench in enumerate(to_run):
        name = bench.name
        print("[%s/%s] %s..." %
              (str(index + 1).rjust(len(run_count)), run_count, name))
        sys.stdout.flush()

        def add_bench(dest_suite, obj):
            if isinstance(obj, pyperf.BenchmarkSuite):
                results = obj
            else:
                results = (obj,)

            version = pyperformance.__version__
            for res in results:
                res.update_metadata({'performance_version': version})

                if dest_suite is not None:
                    dest_suite.add_benchmark(res)
                else:
                    dest_suite = pyperf.BenchmarkSuite([res])

            return dest_suite

        bench_venv, bench_runid = benchmarks.get(bench)
        if bench_venv is None:
            print("ERROR: Benchmark %s failed: could not install requirements" % name)
            errors.append(name)
            continue
        try:
            result = bench.run(
                python,
                bench_runid,
                pyperf_opts,
                venv=bench_venv,
                verbose=options.verbose,
            )
        except Exception as exc:
            print("ERROR: Benchmark %s failed: %s" % (name, exc))
            traceback.print_exc()
            errors.append(name)
        else:
            suite = add_bench(suite, result)

    print()

    return (suite, errors)


# Utility functions

def get_compatibility_id(bench=None):
    # XXX Do not include the pyperformance reqs if a benchmark was provided?
    reqs = sorted(_utils.iter_clean_lines(_venv.REQUIREMENTS_FILE))
    if bench:
        lockfile = bench.requirements_lockfile
        if lockfile and os.path.exists(lockfile):
            reqs += sorted(_utils.iter_clean_lines(lockfile))

    data = [
        # XXX Favor pyperf.__version__ instead?
        pyperformance.__version__,
        '\n'.join(reqs),
    ]

    h = hashlib.sha256()
    for value in data:
        h.update(value.encode('utf-8'))
    compat_id = h.hexdigest()
    # XXX Return the whole string?
    compat_id = compat_id[:12]

    return compat_id


def get_pyperf_opts(options):
    opts = []

    if options.debug_single_value:
        opts.append('--debug-single-value')
    elif options.rigorous:
        opts.append('--rigorous')
    elif options.fast:
        opts.append('--fast')

    if options.verbose:
        opts.append('--verbose')

    if options.affinity:
        opts.append('--affinity=%s' % options.affinity)
    if options.track_memory:
        opts.append('--track-memory')
    if options.inherit_environ:
        opts.append('--inherit-environ=%s' % ','.join(options.inherit_environ))

    return opts
