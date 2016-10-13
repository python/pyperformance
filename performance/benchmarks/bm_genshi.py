"""
Render a template using Genshi module.
"""

import perf
from six.moves import xrange

from genshi.template import MarkupTemplate, NewTextTemplate


BIGTABLE_XML = """\
<table xmlns:py="http://genshi.edgewall.org/">
<tr py:for="row in table">
<td py:for="c in row.values()" py:content="c"/>
</tr>
</table>
"""

BIGTABLE_TEXT = """\
<table>
{% for row in table %}<tr>
{% for c in row.values() %}<td>$c</td>{% end %}
</tr>{% end %}
</table>
"""


def bench_genshi(loops, tmpl_cls, tmpl_str):
    tmpl = tmpl_cls(tmpl_str)
    table = [dict(a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8, i=9, j=10)
             for _ in range(1000)]
    range_it = xrange(loops)
    t0 = perf.perf_counter()

    for _ in range_it:
        stream = tmpl.generate(table=table)
        stream.render()

    return perf.perf_counter() - t0


def prepare_cmd(runner, cmd):
    cmd.append(runner.args.benchmark)


BENCHMARKS = {
    'xml': (MarkupTemplate, BIGTABLE_XML),
    'text': (NewTextTemplate, BIGTABLE_TEXT),
}


if __name__ == "__main__":
    runner = perf.Runner(name='genshi')
    runner.metadata['description'] = "Render a template using Genshi module"
    runner.prepare_subprocess_args = prepare_cmd
    runner.argparser.add_argument("benchmark", choices=sorted(BENCHMARKS))

    args = runner.parse_args()
    bench = args.benchmark

    runner.name += "_%s" % bench
    tmpl_cls, tmpl_str = BENCHMARKS[bench]
    runner.bench_sample_func(bench_genshi, tmpl_cls, tmpl_str)
