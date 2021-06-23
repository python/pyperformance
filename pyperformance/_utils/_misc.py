
def check_name(name, *, loose=False):
    if not name or not isinstance(name, str):
        raise ValueError(f'bad name {name!r}')
    if not loose:
        if name.startswith('-'):
            raise ValueError(name)
        if not name.replace('-', '_').isidentifier():
            raise ValueError(name)


def parse_name_pattern(text, *, fail=True):
    name = text
    # XXX Support globs and/or regexes?  (return a callable)
    try:
        check_name('_' + name)
    except Exception:
        if fail:
            raise  # re-raise
        return None
    return name


def parse_tag_pattern(text):
    if not text.startswith('<'):
        return None
    if not text.endswith('>'):
        return None
    tag = text[1:-1]
    # XXX Support globs and/or regexes?  (return a callable)
    check_name(tag)
    return tag


def parse_selections(selections, parse_entry=None):
    if isinstance(selections, str):
        selections = selections.split(',')
    if parse_entry is None:
        parse_entry = (lambda o, e: (o, e, None, e))

    for entry in selections:
        entry = entry.strip()
        if not entry:
            continue

        op = '+'
        if entry.startswith('-'):
            op = '-'
            entry = entry[1:]

        yield parse_entry(op, entry)
