from ..benchmark import parse_benchmark


def parse_benchmarks(raw, *, expand=None, known=None):
    included = set()
    excluded = set()
    for op, _, parsed in iter_parsed(raw, expand=expand, known=known):
        if op == 'add':
            included.add(parsed)
        elif op == 'remove':
            excluded.add(parsed)
        else:
            raise NotImplementedError(op)
    return included, excluded


def iter_parsed(raw, *, expand=None, known=None):
    if expand is None:
        def expand(parsed, _op):
            yield parsed
    check_known = _resolve_check_known(known)

    if isinstance(raw, str):
        raw = raw.split(',')
    entries = (e.strip() for e in raw)

    for entry in entries:
        if not entry:
            continue

        op = 'add'
        if entry.startswith('-'):
            op = 'remove'
            entry = entry[1:]

        parsed = parse_benchmark(entry)
        for expanded in expand(parsed, op):
            if check_known(expanded, entry):
                yield op, entry, expanded


def _resolve_check_known(known):
    if callable(known):
        return known
    elif not known:
        return (lambda p: True)
    else:
        known = set(known)
        def check_known(parsed, raw):
            if parsed not in known:
                raise ValueError(f'unknown benchmark {parsed!r} ({raw})')
            return True
        return check_known
