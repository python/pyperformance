import os.path
import sys

from ._spec import BenchmarkSpec
from ._metadata import load_metadata
from ._run import run_perf_script, run_other_script


class Benchmark:

    _metadata = None

    def __init__(self, spec, metafile):
        spec, _metafile = BenchmarkSpec.from_raw(spec)
        if not metafile:
            if not _metafile:
                raise ValueError(f'missing metafile for {spec!r}')
            metafile = _metafile

        self.spec = spec
        self.metafile = metafile

    def __repr__(self):
        return f'{type(self).__name__}(spec={self.spec}, metafile={self.metafile})'

    def __hash__(self):
        return hash(self.spec)

    def __eq__(self, other):
        try:
            other_spec = other.spec
        except AttributeError:
            return NotImplemented
        return self.spec == other_spec

    def __gt__(self, other):
        try:
            other_spec = other.spec
        except AttributeError:
            return NotImplemented
        return self.spec > other_spec

    # __getattr__() gets weird when AttributeError comes out of
    # properties so we spell out all the aliased attributes.

    @property
    def name(self):
        return self.spec.name

    @property
    def version(self):
        return self.spec.version

    @property
    def origin(self):
        return self.spec.origin

    def _get_rootdir(self):
        try:
            return self._rootdir
        except AttributeError:
            script = self.runscript
            self._rootdir = os.path.dirname(script) if script else None
            return self._rootdir

    def _init_metadata(self):
        if self._metadata is not None:
            raise NotImplementedError

    def _get_metadata_value(self, key, default):
        try:
            return self._metadata[key]
        except TypeError:
            if self._metadata is None:
                defaults = {
                    'name': self.name,
                    'version': self.version,
                }
                self._metadata, _ = load_metadata(self.metafile, defaults)
        except KeyError:
            pass
        return self._metadata.setdefault(key, default)

    @property
    def tags(self):
        return self._get_metadata_value('tags', ())

    @property
    def datadir(self):
        return self._get_metadata_value('datadir', None)

    @property
    def requirements_lockfile(self):
        try:
            return self._lockfile
        except AttributeError:
            lockfile = self._get_metadata_value('requirements_lockfile', None)
            if not lockfile:
                rootdir = self._get_rootdir()
                if rootdir:
                    lockfile = os.path.join(rootdir, 'requirements.txt')
            self._lockfile = lockfile
            return self._lockfile

    @property
    def runscript(self):
        return self._get_metadata_value('runscript', None)

    @property
    def extra_opts(self):
        return self._get_metadata_value('extra_opts', ())

    # Other metadata keys:
    # * base
    # * python
    # * dependencies
    # * requirements

    def run(self, python, runid=None, pyperf_opts=None, *,
            venv=None,
            verbose=False,
            ):
        if venv and python == sys.executable:
            python = venv.get_python_program()

        if not runid:
            from ..run import get_run_id
            runid = get_run_id(python, self)

        runscript = self.runscript
        bench = run_perf_script(
            python,
            runscript,
            runid,
            extra_opts=self.extra_opts,
            pyperf_opts=pyperf_opts,
            verbose=verbose,
        )

        return bench
