##########################
The Python Benchmark Suite
##########################

This project is intended to be an authoritative source of benchmarks for all
Python implementations. The focus is on real-world benchmarks, rather than
synthetic benchmarks, using whole applications when possible.

* GitHub: https://github.com/python/benchmarks (source code, issues)
* PyPI: https://pypi.python.org/pypi/performance

Other Python Benchmarks:

* CPython: `speed.python.org <https://speed.python.org/>`_ uses the
  `old Python benchmarks (hg.python.org/benchmarks)
  <https://hg.python.org/benchmarks>`_
* PyPy: `speed.pypy.org <http://speed.pypy.org/>`_
  uses `PyPy benchmarks <https://bitbucket.org/pypy/benchmarks>`_
* Pyston: `pyston-perf <https://github.com/dropbox/pyston-perf>`_
* `Numba benchmarks <http://numba.pydata.org/numba-benchmark/>`_
* Cython: `Cython Demos/benchmarks
  <https://github.com/cython/cython/tree/master/Demos/benchmarks>`_


Run benchmarks
==============

Commands to compare Python 2 and Python 3 performances::

    python2 pybenchmarks run --rigorous -b all -o py2.json
    python3 pybenchmarks run --rigorous -b all -o py3.json

    python3 pybenchmarks compare py2.json py3.json

Actions::

    run                 Run benchmarks on the running python
    compare             Compare two benchmark files
    list                List benchmarks of the running Python
    list_groups         List benchmark groups of the running Python

Options of the ``run`` command::

  -r, --rigorous        Spend longer running tests to get more accurate
                        results
  -f, --fast            Get rough answers quickly
  -b BM_LIST, --benchmarks BM_LIST
                        Comma-separated list of benchmarks to run. Can contain
                        both positive and negative arguments:
                        --benchmarks=run_this,also_this,-not_this. If there
                        are no positive arguments, we'll run all benchmarks
                        except the negative arguments. Otherwise we run only
                        the positive arguments.
  --affinity CPU_LIST   Specify CPU affinity for benchmark runs. This way,
                        benchmarks can be forced to run on a given CPU to
                        minimize run to run variation. This uses the taskset
                        command.
  -o FILENAME, --output FILENAME
                        Run the benchmarks on only one interpreter and write
                        benchmark into FILENAME. Provide only baseline_python,
                        not changed_python.
  --append FILENAME     Add runs to an existing file, or create it if it
                        doesn't exist

Options of the ``compare`` command::

  -v, --verbose         Print more output
  -O STYLE, --output_style STYLE
                        What style the benchmark output should take. Valid
                        options are 'normal' and 'table'. Default is normal.


How to get stable benchmarks
============================

Advices helping to get make stable benchmarks:

* Use the ``--rigorous`` option to the ``run`` command
* On Linux with multiple CPU cores: use CPU isolation, see ``isolcpus`` kernel
  option
* On Linux, use nohz_full kernel option (especially on isolated CPUs)
* On a laptop: plug the power cable.
* For modern Intel CPUs: disable Turbo Boost

Note: ASRL must *not* be disabled!


Notes
=====

Tool for comparing the performance of two Python implementations.

pybenchmarks will run Student's two-tailed T test on the benchmark results at the 95%
confidence level to indicate whether the observed difference is statistically
significant.

Omitting the -b option will result in the default group of benchmarks being run
This currently consists of: 2to3, django, nbody, slowpickle,
slowunpickle, spambayes. Omitting -b is the same as specifying `-b default`.

To run every benchmark pybenchmarks knows about, use `-b all`. To see a full list of
all available benchmarks, use `--help`.

Negative benchmarks specifications are also supported: `-b -2to3` will run every
benchmark in the default group except for 2to3 (this is the same as
`-b default,-2to3`). `-b all,-django` will run all benchmarks except the Django
templates benchmark. Negative groups (e.g., `-b -default`) are not supported.
Positive benchmarks are parsed before the negative benchmarks are subtracted.

If --track_memory is passed, pybenchmarks will continuously sample the benchmark's
memory usage, then give you the maximum usage and a link to a Google Chart of
the benchmark's memory usage over time. This currently only works on Linux
2.6.16 and higher or Windows with PyWin32. Because --track_memory introduces
performance jitter while collecting memory measurements, only memory usage is
reported in the final report.

If --args is passed, it specifies extra arguments to pass to the test
python binaries. For example::

  pybenchmarks run_compare --args="-A -B,-C -D" base_python changed_python

will run benchmarks like::

  base_python -A -B the_benchmark.py
  changed_python -C -D the_benchmark.py

while::

  pybenchmarks run_compare --args="-A -B" base_python changed_python

will pass the same arguments to both pythons::

  base_python -A -B the_benchmark.py
  changed_python -A -B the_benchmark.py


Benchmarks
==========

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
- django_template - use the Django template system to build a 150x150-cell HTML table.
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


Changelog
=========

Version 0.1 (2016-08-24)
------------------------

- First release after the conversion to the perf module and move to GitHub


History
-------

Projected moved to https://github.com/python/benchmarks in August 2016. Files
reorganized, benchmarks patched to use the perf module to run benchmark in
multiple processes.

Project started in December 2008 by Collin Winter and Jeffrey Yasskin for the
Unladen Swallow project. The project was hosted at
https://hg.python.org/benchmarks until Feb 2016
