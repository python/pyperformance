#-*- coding: UTF-8 -*-

""" Telco Benchmark for measuring the performance of Fraction calculations

http://speleotrove.com/decimal/telco.html
http://speleotrove.com/decimal/telcoSpec.html

A call type indicator, c, is set from the bottom (least significant) bit of the duration (hence c is 0 or 1).
A r, r, is determined from the call type. Those calls with c=0 have a low r: 0.0013; the remainder (‘distance calls’) have a ‘premium’ r: 0.00894. (The rates are, very roughly, in Euros or dollarates per second.)
A price, p, for the call is then calculated (p=r*n).
A basic tax, b, is calculated: b=p*0.0675 (6.75%), and the total basic tax variable is then incremented (sumB=sumB+b).
For distance calls: a distance tax, d, is calculated: d=p*0.0341 (3.41%), and then the total distance tax variable is incremented (sumD=sumD+d).
The total price, t, is calculated (t=p+b, and, if a distance call, t=t+d).
The total prices variable is incremented (sumT=sumT+t).
The total price, t, is converted to a string, s.

"""

from __future__ import absolute_import

from struct import unpack
import os.path

import perf
from six.moves import xrange


def rel_path(*path):
    return os.path.join(os.path.dirname(__file__), *path)

filename = rel_path("data", "telco-bench.b")


def run(cls, loops=1):
    rates = list(map(cls, ('0.0013', '0.00894')))
    basictax = cls("0.0675")
    disttax = cls("0.0341")

    values = []
    with open(filename, "rb") as infil:
        for _ in xrange(20000):
            datum = infil.read(8)
            if datum == '': break
            n, =  unpack('>Q', datum)
            values.append(n)

    start = perf.perf_counter()
    results = set()
    for _ in xrange(loops):
        sumT = cls()   # sum of total prices
        sumB = cls()   # sum of basic tax
        sumD = cls()   # sum of 'distance' tax

        for n in values:
            calltype = n & 1
            r = rates[calltype]

            p = r * n
            b = p * basictax
            sumB += b
            t = p + b

            if calltype:
                d = p * disttax
                sumD += d
                t += d

            sumT += t

        results.add(str(sumT))

    time = perf.perf_counter() - start

    assert len(results) == 1
    return time


def run_bench(loops, backend_class):
    return run(backend_class, loops)


def find_benchmark_class(impl_name):
    if impl_name == 'fractions':
        from fractions import Fraction as backend_class
    elif impl_name == 'quicktions':
        from quicktions import Fraction as backend_class
    elif impl_name == 'decimal':
        from decimal import Decimal as backend_class
    else:
        raise ValueError("Invalid class name: '%s'" % impl_name)
    return backend_class


def prepare_subprocess_args(runner, args):
    args.append(runner.args.backend)


if __name__ == "__main__":
    import perf.text_runner
    runner = perf.text_runner.TextRunner(name='telco')
    runner.metadata['description'] = "Telco fractions benchmark"
    runner.prepare_subprocess_args = prepare_subprocess_args

    parser = runner.argparser
    backends = ["decimal", "fractions", "quicktions"]
    parser.add_argument("backend", choices=backends, nargs='?', default="fractions")

    options = runner.parse_args()
    runner.name += "/%s" % options.backend
    backend_class = find_benchmark_class(options.backend)

    runner.bench_sample_func(run_bench, backend_class)
