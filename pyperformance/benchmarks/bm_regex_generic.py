
"""Benchmarks for Python's regex engine.

Benchmarks for checking begining and end of strings. Should have reasonable times after https://bugs.python.org/issue42885 is fixed.

Real life use case is e.g. comparing 500.000 filenames and paths each with thousands of regex of known malicous files, https://github.com/Neo23x0/signature-base/blob/master/iocs/filename-iocs.txt
(^ and $ mostly not yet included because it wouldn't give a speed advantage in https://github.com/Neo23x0/Loki)

Adopted from bm_regex_effbot.py by Arnim Rupp

Feel free to add other generic regex.

"""

# Python imports
import re

# Local imports
import pyperf

# These are the regular expressions to be tested. 

def gen_regex_table():
    return [
        re.compile('^c:'), # very slow if false
        re.compile('\Ac:'), # very slow if false
        re.compile('evil\.exe$'),
        re.compile('evil\.exe\Z'),
        re.compile('\Ad:'),
        re.compile('evil\.dll$'), # very slow if true
        re.compile('evil\.dll\Z'), # very slow if true
        ]


def gen_string_table(n):
    """Generates the list of strings that will be used in the benchmarks.

    """
    strings = []

    strings.append('d:' + ('A' * ( 10 ** n )) + 'evil.dll')
    return strings


def init_benchmarks(n_values=None):
    """Initialize the strings we'll run the regexes against.

    The generated list of strings is cached in the string_tables
    variable, which is indexed by n.

    Returns:
    A list of string + lengths.
    """

    if n_values is None:
        n_values = (3,5,7)

    string_tables = {n: gen_string_table(n) for n in n_values}
    #print(string_tables)
    regexs = gen_regex_table()

    data = []
    for n in n_values:
        for id in range(len(regexs)):
            regex = regexs[id]
            string = string_tables[n]
            data.append((regex, string))
    return data


def bench_regex_generic(loops):
    if bench_regex_generic.data is None:
        bench_regex_generic.data = init_benchmarks()
    data = bench_regex_generic.data

    range_it = range(loops)
    search = re.search
    t0 = pyperf.perf_counter()

    for _ in range_it:
        # Runs all of the benchmarks for a given value of n.
        for regex, string in data:
            # search 10 times
            search(regex, string[0])
            search(regex, string[0])
            search(regex, string[0])
            search(regex, string[0])
            search(regex, string[0])
            search(regex, string[0])
            search(regex, string[0])
            search(regex, string[0])
            search(regex, string[0])
            search(regex, string[0])

    return pyperf.perf_counter() - t0


# cached data, generated at the first call
bench_regex_generic.data = None


def add_cmdline_args(cmd, args):
    pass
    #if args.force_bytes:
        #cmd.append("--force_bytes")


if __name__ == '__main__':
    runner = pyperf.Runner(add_cmdline_args=add_cmdline_args)
    runner.metadata['description'] = ("Test the performance of regexps "
                                      "with long strings.")
    options = runner.parse_args()

    runner.bench_time_func('regex_generic', bench_regex_generic, inner_loops=10)
