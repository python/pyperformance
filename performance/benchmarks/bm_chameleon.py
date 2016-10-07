from chameleon import PageTemplate

import six
import perf.text_runner

BIGTABLE_ZPT = """\
<table xmlns="http://www.w3.org/1999/xhtml"
xmlns:tal="http://xml.zope.org/namespaces/tal">
<tr tal:repeat="row python: options['table']">
<td tal:repeat="c python: row.values()">
<span tal:define="d python: c + 1"
tal:attributes="class python: 'column-' + %s(d)"
tal:content="python: d" />
</td>
</tr>
</table>""" % six.text_type.__name__


def main(loops):
    tmpl = PageTemplate(BIGTABLE_ZPT)
    table = [dict(a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8, i=9, j=10)
             for x in range(500)]
    options = {'table': table}
    range_it = six.moves.xrange(loops)
    start = perf.perf_counter()

    for _ in range_it:
        tmpl(options=options)

    return perf.perf_counter() - start


if __name__ == '__main__':
    runner = perf.text_runner.TextRunner(name='chameleon')
    runner.metadata['description'] = "Chameleon template"
    runner.bench_sample_func(main)
