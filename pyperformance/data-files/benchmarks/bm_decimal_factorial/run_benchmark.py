"""
Calculate `factorial` using the decimal module.

- 2024-06-14: Michael Droettboom copied this from
  Modules/_decimal/tests/bench.py in the CPython source and adapted to use
  pyperf.
- 2026-02-22: Sergey B Kirpichev adapted context settings and tested
  values to support also pure-Python decimal module, copy
  increase_int_max_str_digits() decorator.
"""

# Original copyright notice in CPython source:

#
# Copyright (C) 2001-2012 Python Software Foundation. All Rights Reserved.
# Modified and extended by Stefan Krah.
#

import decimal
try:
    import _decimal
except ImportError:
    _decimal = None
import sys
from functools import wraps

import pyperf


def factorial(n, m):
    if n > m:
        return factorial(m, n)
    elif m == 0:
        return 1
    elif n == m:
        return n
    else:
        return factorial(n, (n + m) // 2) * factorial((n + m) // 2 + 1, m)


def increase_int_max_str_digits(maxdigits):
    def _increase_int_max_str_digits(func, maxdigits=maxdigits):
        @wraps(func)
        def wrapper(*args, **kwargs):
            previous_int_limit = sys.get_int_max_str_digits()
            sys.set_int_max_str_digits(maxdigits)
            ans = func(*args, **kwargs)
            sys.set_int_max_str_digits(previous_int_limit)
            return ans
        return wrapper
    return _increase_int_max_str_digits


@increase_int_max_str_digits(maxdigits=10000000)
def bench_decimal_factorial():
    c = decimal.getcontext()
    if _decimal:
        c.prec = decimal.MAX_PREC
        c.Emax = decimal.MAX_EMAX
        c.Emin = decimal.MIN_EMIN
        data = [10000, 100000]
    else:
        c.prec = 20000  # Should be enough to hold largest factorial exactly.
        data = [1000, 5000]

    for n in data:
        _ = factorial(decimal.Decimal(n), 0)


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata["description"] = "decimal_factorial benchmark"

    args = runner.parse_args()
    runner.bench_func("decimal_factorial", bench_decimal_factorial)
