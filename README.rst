The Grand Unified Python Benchmark Suite
########################################

This project is intended to be an authoritative source of benchmarks for all
Python implementations. The focus is on real-world benchmarks, rather than
synthetic benchmarks, using whole applications when possible.


Docstring
---------

Tool for comparing the performance of two Python implementations.

Typical usage looks like

./bench.py run_compare -b 2to3,django control/python experiment/python

This will run the 2to3 and Django template benchmarks, using `control/python`
as the baseline and `experiment/python` as the experiment. The --fast and
--rigorous options can be used to vary the duration/accuracy of the run. Run
--help to get a full list of options that can be passed to -b.

bench.py will run Student's two-tailed T test on the benchmark results at the 95%
confidence level to indicate whether the observed difference is statistically
significant.

Omitting the -b option will result in the default group of benchmarks being run
This currently consists of: 2to3, django, nbody, slowpickle,
slowunpickle, spambayes. Omitting -b is the same as specifying `-b default`.

To run every benchmark bench.py knows about, use `-b all`. To see a full list of
all available benchmarks, use `--help`.

Negative benchmarks specifications are also supported: `-b -2to3` will run every
benchmark in the default group except for 2to3 (this is the same as
`-b default,-2to3`). `-b all,-django` will run all benchmarks except the Django
templates benchmark. Negative groups (e.g., `-b -default`) are not supported.
Positive benchmarks are parsed before the negative benchmarks are subtracted.

If --track_memory is passed, bench.py will continuously sample the benchmark's
memory usage, then give you the maximum usage and a link to a Google Chart of
the benchmark's memory usage over time. This currently only works on Linux
2.6.16 and higher or Windows with PyWin32. Because --track_memory introduces
performance jitter while collecting memory measurements, only memory usage is
reported in the final report.

If --args is passed, it specifies extra arguments to pass to the test
python binaries. For example,
  bench.py run_compare --args="-A -B,-C -D" base_python changed_python
will run benchmarks like
  base_python -A -B the_benchmark.py
  changed_python -C -D the_benchmark.py
while
  bench.py run_compare --args="-A -B" base_python changed_python
will pass the same arguments to both pythons:
  base_python -A -B the_benchmark.py
  changed_python -A -B the_benchmark.py


Quickstart Guide
----------------

Not all benchmarks are created equal: some of the benchmarks listed below are
more useful than others. If you're interested in overall system performance,
the best guide is this:

    $ python bench.py run_compare -r -b default /control/python /test/python

That will run the benchmarks we consider the most important headline indicators
of performance. There's an additional collection of whole-app benchmarks that
are important, but take longer to run:

    $ python bench.py run_compare -r -b apps /control/python /test/python


Notable Benchmark groups
------------------------

Like individual benchmarks (see "Available benchmarks" below), benchmarks
group are allowed after the `-b` option.

- 2n3 - benchmarks compatible with both Python 2 and Python 3
- apps - "high-level" applicative benchmarks
- serialize - various serialization libraries
- template - various third-party template engines


Available Benchmarks
--------------------

- 2to3 - have the 2to3 tool translate itself.
- calls - collection of function and method call microbenchmarks:
    - call_simple - positional arguments-only function calls.
    - call_method - positional arguments-only method calls.
    - call_method_slots - method calls on classes that use __slots__.
    - call_method_unknown - method calls where the receiver cannot be predicted.
- django - use the Django template system to build a 150x150-cell HTML table.
- fastpickle - use the cPickle module to pickle a variety of datasets.
- fastunnpickle - use the cPickle module to unnpickle a variety of datasets.
- float - artificial, floating point-heavy benchmark originally used by Factor.
- html5lib - parse the HTML 5 spec using html5lib.
- html5lib_warmup - like html5lib, but gives the JIT a chance to warm up by
                    doing the iterations in the same process.
- mako - use the Mako template system to build a 150x150-cell HTML table.
- nbody - the N-body Shootout benchmark. Microbenchmark for floating point
          operations.
- nqueens - small solver for the N-Queens problem.
- pickle - use the cPickle and pure-Python pickle modules to pickle and unpickle
           a variety of datasets.
- pickle_dict - microbenchmark; use the cPickle module to pickle a lot of dicts.
- pickle_list - microbenchmark; use the cPickle module to pickle a lot of lists.
- pybench - run the standard Python PyBench benchmark suite. This is considered
            an unreliable, unrepresentative benchmark; do not base decisions
            off it. It is included only for completeness.
- regex - collection of regex benchmarks:
    - regex_compile - stress the performance of Python's regex compiler, rather
                      than the regex execution speed.
    - regex_effbot - some of the original benchmarks used to tune mainline
                     Python's current regex engine.
    - regex_v8 - Python port of V8's regex benchmark.
- richards - the classic Richards benchmark.
- slowpickle - use the pure-Python pickle module to pickle a variety of
               datasets.
- slowunpickle - use the pure-Python pickle module to unpickle a variety of
                 datasets.
- spambayes - run a canned mailbox through a SpamBayes ham/spam classifier.
- startup - collection of microbenchmarks focused on Python interpreter
            start-up time:
    - hg_startup - get Mercurial's help screen.
    - normal_startup - start Python, then exit immediately.
    - startup_nosite - start Python with the -S option, then exit immediately.
- threading - collection of microbenchmarks for Python's threading support.
              These benchmarks come in pairs: an iterative version
              (iterative_foo), and a multithreaded version (threaded_foo).
    - threaded_count, iterative_count - spin in a while loop, counting down from a large number.
- unpack_sequence - microbenchmark for unpacking lists and tuples.
- unpickle - use the cPickle module to unpickle a variety of datasets.


Benchmarks
----------

performance/ directory contains both macro- and micro-benchmarks for Python
implementations.

Macro(ish)benchmarks:
    - bm_django.py: assess Django template performance.
    - bm_pickle.py: test picking/unpickling performance.
    - bm_spitfire.py: assess Spitfire template performance.
    - gcbench.py: GC benchmark (allocate and deallocate lots of objects).
      Copied from PyPy's pypy/translator/goal/gcbench.py, r60845.


Microbenchmarks:
    - bm_ai.py: solvers for alphametics and N-Queens problems. These are
      classified as "micro" because they're dominated by a single function.
    - tuple_gc_hell.py: stress the GC by allocating lots of tuples.


Crap benchmarks used for historical comparisons:
    - pybench/: PyBench 2.0 benchmark suite.
    - pystone.py: standard PyStone benchmark.
    - richards.py: standard Richards benchmark.
      Copied from PyPy's pypy/translator/goal/richards.py, r60845.


Changelog
---------

Projected moved to https://github.com/python/benchmarks in August 2016. Files
reorganized, benchmarks patched to use the perf module to run benchmark in
multiple processes.

Projected moved to https://hg.python.org/benchmarks and developed there between
Dec 2008 and Feb 2016.

Project started by Collin Winter and Jeffrey Yasskin for the Unladen Swallow
project.
