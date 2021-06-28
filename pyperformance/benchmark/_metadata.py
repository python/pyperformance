import os.path

from .. import _utils
from ._spec import BenchmarkSpec


METADATA = 'pyproject.toml'
DEPENDENCIES = 'requirements.in'
REQUIREMENTS = 'requirements.txt'
DATA = 'data'
PREP = 'prep_benchmark.py'
RUN = 'run_benchmark.py'

PEP_621_FIELDS = {
    'name': None,
    'version': None,
    'requires-python': 'python',
    'dependencies': None,
    #'optional-dependencies': '',
    #'urls': '',
}
TOOL_FIELDS = {
    #'metabase': None,
    'metafile': None,
    'name': None,
    'tags': None,
    'datadir': None,
    'prescript': None,
    'runscript': None,
    'extra_opts': None,
}


#class BenchmarkMetadata:
#    spec
#    base
#    metafile
#    tags
#    python
#    dependencies  # (from requirements.in)
#    requirements  # (from lock file or requirements.txt)
#    datadir
#    prescript
#    runscript
#    extra_opts


def load_metadata(metafile, defaults=None):
    if isinstance(metafile, str):
        name, rootdir = _name_from_filename(metafile)
        data, filename = _utils.load_pyproject_toml(metafile,
                                                    name=name or None,
                                                    requirefiles=False,
                                                    )
    else:
        text = metafile.read()
        filename = metafile.name
        name, rootdir = _name_from_filename(filename)
        data = _utils.parse_pyproject_toml(text, rootdir, name,
                                           requirefiles=False)
    project = data.get('project')
    tool = data.get('tool', {}).get('pyperformance', {})

    defaults = _ensure_defaults(defaults, rootdir)
    base, basefile = _resolve_base(
            tool,
            project,
            filename,
            project.get('version') or defaults.get('version'),
    )
    top = _resolve(project or {}, tool, filename)
    merged = _merge_metadata(top, base, defaults)

    if not merged.get('name'):
        raise ValueError('missing benchmark name')
    if not merged.get('version'):
        raise ValueError('missing benchmark version')

    metafile = merged.pop('metafile')
    merged['spec'] = BenchmarkSpec(
        merged.pop('name'),
        merged.pop('version'),
        # XXX Should we leave this (origin) blank?
        metafile,
    )
    if basefile:
        merged['base'] = basefile

    return merged, filename


def _name_from_filename(metafile):
    rootdir, basename = os.path.split(metafile)
    if basename == 'pyproject.toml':
        dirname = os.path.dirname(rootdir)
        name = dirname[3:] if dirname.startswith('bm_') else None
    elif basename.startswith('bm_') and basename.endswith('.toml'):
        name = basename[3:-5]
    else:
        name = None
    return name, rootdir


def _ensure_defaults(defaults, rootdir):
    if not defaults:
        defaults = {}

    if not defaults.get('datadir'):
        datadir = os.path.join(rootdir, DATA)
        if os.path.isdir(datadir):
            defaults['datadir'] = datadir

    if not defaults.get('prescript'):
        prescript = os.path.join(rootdir, PREP)
        if os.path.isfile(prescript):
            defaults['prescript'] = prescript

    if not defaults.get('runscript'):
        runscript = os.path.join(rootdir, RUN)
        if os.path.isfile(runscript):
            defaults['runscript'] = runscript

    return defaults


def _resolve_base(tool, project, filename, version):
    rootdir, basename = os.path.split(filename)

    metabase = tool.get('metabase')
    if not metabase:
        if basename == 'pyproject.toml':
            return None, None
        elif not (basename.startswith('bm_') and basename.endswith('.toml')):
            return None, None
        elif not os.path.basename(rootdir).startswith('bm_'):
            return None, None
        else:
            metabase = os.path.join(rootdir, 'pyproject.toml')
            if not os.path.isfile(metabase):
                return None, None

    if project is not None:
        unexpected = set(project) - {'name', 'dynamic'}
        if unexpected:
            raise ValueError(f'[project] should be minimal if "metabase" is provided, got extra {sorted(unexpected)}')

    if metabase == '..':
        metabase = os.path.join(
            os.path.dirname(rootdir),
            'base.toml',
        )
    if metabase == filename:
        raise Exception('circular')

    if not os.path.isabs(metabase):
        metabase = os.path.join(rootdir, metabase)
        if metabase == filename:
            raise Exception('circular')
    return load_metadata(metabase,
                         {'version': version, 'name': '_base_'})


def _resolve(project, tool, filename):
    resolved = {
        'metafile': filename,
    }

    rootdir = os.path.dirname(filename)
    for field, target in TOOL_FIELDS.items():
        if target is None:
            target = field
        if not resolved.get(target):
            value = tool.get(field)
            if value is not None:
                resolved[target] = _resolve_value(field, value, rootdir)

    for field, target in PEP_621_FIELDS.items():
        if target is None:
            target = field
        if field == 'url':
            repo = project.get('urls', {}).get('repository')
            raise NotImplementedError
        elif not resolved.get(target):
            value = project.get(field)
            if value is not None:
                resolved[target] = value

    return resolved


def _resolve_value(field, value, rootdir):
    if field == 'name':
        _utils.check_name(value)
    elif field == 'metafile':
        assert False, 'unreachable'
    elif field == 'tags':
        if isinstance(value, str):
            value = value.replace(',', ' ').split()
        for tag in value:
            _utils.check_name(tag)
    elif field == 'datadir':
        if not os.path.isabs(value):
            value = os.path.join(rootdir, value)
        _utils.check_dir(value)
    elif field == 'prescript':
        if not os.path.isabs(value):
            value = os.path.join(rootdir, value)
        _utils.check_file(value)
    elif field == 'runscript':
        if not os.path.isabs(value):
            value = os.path.join(rootdir, value)
        _utils.check_file(value)
    elif field == 'extra_opts':
        if isinstance(value, str):
            raise TypeError(f'extra_opts should be a list of strings, got {value!r}')
        for opt in value:
            if not opt or not isinstance(opt, str):
                raise TypeError(f'extra_opts should be a list of strings, got {value!r}')
    else:
        raise NotImplementedError(field)
    return value


def _merge_metadata(*tiers):
    merged = {}
    for data in tiers:
        if not data:
            continue
        for field, value in data.items():
            if merged.get(field):
                # XXX Merge containers?
                continue
            if value:
                merged[field] = value
    return merged
