+++++
Usage
+++++

Installation
============

Command to install pyperformance::

    python3 -m pip install pyperformance

The command installs a new ``pyperformance`` program.

If needed, ``pyperf`` and ``six`` dependencies are installed automatically.

pyperformance works on Python 3.6 and newer, but it may work on Python 3.4 and
3.5.

Mercurial might need Python developement headers to build its C extensions. For
example, on Fedora, use::

    sudo dnf install pypy3-devel

At runtime, Python development files (header files) may be needed to install
some dependencies like ``dulwich_log`` or ``psutil``, to build their C
extension. Commands on Fedora to install dependencies:

* Python 3: ``sudo dnf install python3-devel``
* PyPy: ``sudo dnf install pypy-devel``


Run benchmarks
==============

Commands to compare Python 3.6 and Python 3.7 performances::

    pyperformance run --python=python3.6 -o py36.json
    pyperformance run --python=python3.7 -o py38.json
    pyperformance compare py36.json py38.json

Note: ``python3 -m pyperformance ...`` syntax works as well (ex: ``python3 -m
pyperformance run -o py38.json``), but requires to install pyperformance on each
tested Python version.

JSON files are produced by the pyperf module and so can be analyzed using pyperf
commands::

    python3 -m pyperf show py36.json
    python3 -m pyperf check py36.json
    python3 -m pyperf metadata py36.json
    python3 -m pyperf stats py36.json
    python3 -m pyperf hist py36.json
    python3 -m pyperf dump py36.json
    (...)

It's also possible to use pyperf to compare results of two JSON files::

    python3 -m pyperf compare_to py36.json py38.json --table

pyperformance actions::

    run                 Run benchmarks on the running python
    show                Display a benchmark file
    compare             Compare two benchmark files
    list                List benchmarks which run command would run
    list_groups         List all benchmark groups
    venv                Actions on the virtual environment

Common options
--------------

Options available to all commands::

  -p PYTHON, --python PYTHON
                        Python executable (default: use running Python)
  --venv VENV           Path to the virtual environment
  --inherit-environ VAR_LIST
                        Comma-separated list of environment variable names
                        that are inherited from the parent environment when
                        running benchmarking subprocesses.

run
---

Options of the ``run`` command::

  -r, --rigorous        Spend longer running tests to get more accurate
                        results
  -f, --fast            Get rough answers quickly
  -m, --track-memory    Track memory usage. This only works on Linux.
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

show
----

Usage::

    show FILENAME


compare
-------

Options of the ``compare`` command::

  -v, --verbose         Print more output
  -O STYLE, --output_style STYLE
                        What style the benchmark output should take. Valid
                        options are 'normal' and 'table'. Default is normal.

list
----

Options of the ``list`` command::

  -b BM_LIST, --benchmarks BM_LIST
                        Comma-separated list of benchmarks to run. Can contain
                        both positive and negative arguments:
                        --benchmarks=run_this,also_this,-not_this. If there
                        are no positive arguments, we'll run all benchmarks
                        except the negative arguments. Otherwise we run only
                        the positive arguments.

Use ``python3 -m pyperformance list -b all`` to list all benchmarks.


venv
----

Options of the ``venv`` command::

  -p PYTHON, --python PYTHON
                        Python executable (default: use running Python)
  --venv VENV           Path to the virtual environment

Actions of the ``venv`` command::

  show      Display the path to the virtual environment and it's status (created or not)
  create    Create the virtual environment
  recreate  Force the recreation of the the virtual environment
  remove    Remove the virtual environment


Compile Python to run benchmarks
================================

pyperformance actions::

    compile        Compile, install and benchmark CPython
    compile_all    Compile, install and benchmark multiple branches and revisions of CPython
    upload         Upload JSON file

All these commands require a configuration file.

Simple configuration usable for ``compile`` (but not for ``compile_all`` nor
``upload``), ``doc/benchmark.conf``:

.. literalinclude:: benchmark.conf
   :language: ini

Configuration file sample with comments, ``doc/benchmark.conf.sample``:

.. literalinclude:: benchmark.conf.sample
   :language: ini


.. _cmd-compile:

compile
-------

Usage::

    pyperformance compile CONFIG_FILE REVISION [BRANCH]
        [--patch=PATCH_FILE]
        [-U/--no-update]
        [-T/--no-tune]

Compile Python, install Python and run benchmarks on the installed Python.

Options:

* ``--no-update``: Don't update the Git repository.
* ``--no-tune``: Don't run ``pyperf system tune`` to tune the system for
  benchmarks.

If the ``branch`` argument is not specified:

* If ``REVISION`` is a branch name: use it as a the branch, and get the
  latest revision of this branch
* Otherwise, use ``master`` branch by default

Notes:

* --enable-optimizations doesn't enable LTO because of compiler bugs:
  http://bugs.python.org/issue28032
  (see also: http://bugs.python.org/issue28605)
* PGO is broken on Ubuntu 14.04 LTS with GCC 4.8.4-2ubuntu1~14.04:
  ``Modules/socketmodule.c:7743:1: internal compiler error: in edge_badness,
  at ipa-inline.c:895``


compile_all
-----------

Usage::

    pyperformance compile_all CONFIG_FILE

Compile all branches and revisions of CONFIG_FILE.


upload
------

Usage::

    pyperformance upload CONFIG_FILE JSON_FILE

Upload results from a JSON file to a Codespeed website.




How to get stable benchmarks
============================

* Run ``python3 -m pyperf system tune`` command
* Compile Python using LTO (Link Time Optimization) and PGO (profile guided
  optimizations): use the :ref:`pyperformance compile <cmd-compile>` command with
  uses LTO and PGO by default
* See advices of the pyperf documentation:
  `How to get reproductible benchmark results
  <http://pyperf.readthedocs.io/en/latest/run_benchmark.html#how-to-get-reproductible-benchmark-results>`_.


pyperformance virtual environment
=================================

To run benchmarks, pyperformance first creates a virtual environment. It installs
requirements with fixed versions to get a reproductible environment. The system
Python has unknown module installed with unknown versions, and can have
``.pth`` files run at Python startup which can modify Python behaviour or at
least slow down Python startup.


What is the goal of pyperformance
=================================

A benchmark is always written for a specific purpose. Depending how the
benchmark is written and how the benchmark is run, the result can be different
and so have a different meaning.

The pyperformance benchmark suite has multiple goals:

* Help to detect performance regression in a Python implementation
* Validate that an optimization change makes Python faster and don't
  performance regressions, or only minor regressions
* Compare two implementations of Python, for example CPython and PyPy
* Showcase of Python performance which ideally would be representative
  of performances of applications running on production

Don't disable GC nor ASLR
-------------------------

The pyperf module and pyperformance benchmarks are designed to produce
reproductible results, but not at the price of running benchmarks in a special
mode which would not be used to run applications in production. For these
reasons, the Python garbage collector, Python randomized hash function and
system ASLR (Address Space Layout Randomization) are **not disabled**.
Benchmarks don't call ``gc.collect()`` neither since CPython implements it with
`stop-the-world
<https://en.wikipedia.org/wiki/Tracing_garbage_collection#Stop-the-world_vs._incremental_vs._concurrent>`_
and so applications don't call it to not kill performances.

Include outliers and spikes
---------------------------

Moreover, while the pyperf documentation explains how to reduce the random noise
of the system and other applications, some benchmarks use the system and so can
get different timing depending on the system workload, depending on I/O
performances, etc. Outliers and temporary spikes in results are **not
automatically removed**: values are summarized by computing the average
(arithmetic mean) and standard deviation which "contains" these spikes, instead
of using median and the median absolute deviation for example which to ignore
outliers. It is deliberate choice since applications running in production are
impacted by such temporary slowdown caused by various things like a garbage
collection or a JIT compilation.

Warmups and steady state
------------------------

A borderline issue are the benchmarks "warmups". The first values of each
worker process are always slower: 10% slower in the best case, it can be 1000%
slower or more on PyPy. Right now (2017-04-14), pyperformance ignore first values
considered as warmup until a benchmark reachs its "steady state". The "steady
state" can include temporary spikes every 5 values (ex: caused by the garbage
collector), and it can still imply further JIT compiler optimizations but with
a "low" impact on the average pyperformance.

To be clear "warmup" and "steady state" are a work-in-progress and a very
complex topic, especially on PyPy and its JIT compiler.


Notes
=====

Tool for comparing the performance of two Python implementations.

pyperformance will run Student's two-tailed T test on the benchmark results at the 95%
confidence level to indicate whether the observed difference is statistically
significant.

Omitting the ``-b`` option will result in the default group of benchmarks being
run Omitting ``-b`` is the same as specifying `-b default`.

To run every benchmark pyperformance knows about, use ``-b all``. To see a full
list of all available benchmarks, use `--help`.

Negative benchmarks specifications are also supported: `-b -2to3` will run every
benchmark in the default group except for 2to3 (this is the same as
`-b default,-2to3`). `-b all,-django` will run all benchmarks except the Django
templates benchmark. Negative groups (e.g., `-b -default`) are not supported.
Positive benchmarks are parsed before the negative benchmarks are subtracted.

If ``--track_memory`` is passed, pyperformance will continuously sample the
benchmark's memory usage. This currently only works on Linux 2.6.16 and higher
or Windows with PyWin32. Because ``--track_memory`` introduces performance
jitter while collecting memory measurements, only memory usage is reported in
the final report.
