
"""Test the performance of the Django template system.

This will have Django generate a 150x150-cell HTML table.
"""

from six.moves import xrange
import perf.text_runner

import django.conf
from django.template import Context, Template


# 2016-10-10: Python 3.6 takes 380 ms
DEFAULT_SIZE = 100


def bench_django_template(loops, size):
    template = Template("""<table>
{% for row in table %}
<tr>{% for col in row %}<td>{{ col|escape }}</td>{% endfor %}</tr>
{% endfor %}
</table>
    """)
    table = [xrange(size) for _ in xrange(size)]
    context = Context({"table": table})

    range_it = xrange(loops)
    t0 = perf.perf_counter()

    for _ in range_it:
        # ignore result
        template.render(context)

    return perf.perf_counter() - t0


def prepare_cmd(runner, cmd):
    cmd.append("--size=%s" % runner.args.size)


if __name__ == "__main__":
    django.conf.settings.configure(TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
    }])
    django.setup()

    runner = perf.text_runner.TextRunner(name='django_template')
    cmd = runner.argparser
    cmd.add_argument("--size",
                     type=int, default=DEFAULT_SIZE,
                     help="Table size, height and width (default: %s)"
                          % DEFAULT_SIZE)

    args = runner.parse_args()
    runner.metadata['description'] = "Django template"
    runner.metadata['django_version'] = django.__version__
    runner.metadata['django_table_size'] = args.size

    runner.bench_sample_func(bench_django_template, args.size)
