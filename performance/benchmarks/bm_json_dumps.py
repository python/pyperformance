import json

import perf.text_runner
import six
from six.moves import xrange


EMPTY = ({}, 2000)
SIMPLE_DATA = {'key1': 0, 'key2': True, 'key3': 'value', 'key4': 'foo',
               'key5': 'string'}
SIMPLE = (SIMPLE_DATA, 1000)
NESTED_DATA = {'key1': 0, 'key2': SIMPLE[0], 'key3': 'value', 'key4': SIMPLE[0],
               'key5': SIMPLE[0], six.u('key'): six.u('\u0105\u0107\u017c')}
NESTED = (NESTED_DATA, 1000)
HUGE = ([NESTED[0]] * 1000, 1)

cases = ['EMPTY', 'SIMPLE', 'NESTED', 'HUGE']


def bench_json_dumps(loops):
    data = []
    for case in cases:
        obj, count = globals()[case]
        data.append((obj, xrange(count)))

    range_it = xrange(loops)
    t0 = perf.perf_counter()

    for _ in range_it:
        for obj, count_it in data:
            for _ in count_it:
                json.dumps(obj)

    return perf.perf_counter() - t0


if __name__ == '__main__':
    runner = perf.text_runner.TextRunner(name='json_dumps')
    runner.metadata['description'] = "Benchmark json.dumps()"
    runner.bench_sample_func(bench_json_dumps)
