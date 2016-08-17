#!/usr/bin/python

"""Wrapper script for testing the performance of the Django template system.

This is intended to support Unladen Swallow's perf.py

This will have Django generate a 100x100 table as many times as you
specify (via the -n flag). The raw times to generate the template will be
dumped to stdout. This is more convenient for Unladen Swallow's uses: it
allows us to keep all our stats in perf.py.
"""

from six.moves import xrange
import perf.text_runner

import django.conf
from django.template import Context, Template


def test_django(loops):
    template = Template("""<table>
{% for row in table %}
<tr>{% for col in row %}<td>{{ col|escape }}</td>{% endfor %}</tr>
{% endfor %}
</table>
    """)
    table = [xrange(150) for _ in xrange(150)]
    context = Context({"table": table})

    range_it = xrange(loops)
    t0 = perf.perf_counter()

    for _ in range_it:
        # ignore result
        template.render(context)

    return perf.perf_counter() - t0


if __name__ == "__main__":
    django.conf.settings.configure()
    django.setup()

    runner = perf.text_runner.TextRunner(name='django')
    runner.metadata['description'] = "Django template"
    runner.metadata['django_version'] = django.__version__
    runner.bench_sample_func(test_django)
