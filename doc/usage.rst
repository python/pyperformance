+++++
Usage
+++++

Installation
============

Command to install performance::

    python3 -m pip install performance

The command installs a new ``pyperformance`` program.

If needed, ``perf`` and ``six`` dependencies are installed automatically.

performance works on Python 2.7, 3.4 and newer.

On Python 2, the ``virtualenv`` program (or the Python module) is required
to create virtual environments. On Python 3, the ``venv`` module of the
standard library is used.

At runtime, Python development files (header files) may be needed to install
some dependencies like ``dulwich_log`` or ``psutil``, to build their C
extension. Commands on Fedora to install dependencies:

* Python 2: ``sudo dnf install python-devel``
* Python 3: ``sudo dnf install python3-devel``
* PyPy: ``sudo dnf install pypy-devel``

In some cases, performance fails to create a virtual environment. In this case,
upgrading virtualenv on the system can fix the issue. Example::

    sudo python2 -m pip install -U virtualenv


Run benchmarks
==============

Commands to compare Python 2 and Python 3 performances::

    pyperformance run --python=python2 -o py2.json
    pyperformance run --python=python3 -o py3.json
    pyperformance compare py2.json py3.json

Note: ``python3 -m performance ...`` syntax works as well (ex: ``python3 -m
performance run -o py3.json``), but requires to install performance on each
tested Python version.

JSON files are produced by the perf module and so can be analyzed using perf
commands::

    python3 -m perf show py2.json
    python3 -m perf check py2.json
    python3 -m perf metadata py2.json
    python3 -m perf stats py2.json
    python3 -m perf hist py2.json
    python3 -m perf dump py2.json
    (...)

It's also possible to use perf to compare results of two JSON files::

    python3 -m perf compare_to py2.json py3.json --table

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

Use ``python3 -m performance list -b all`` to list all benchmarks.


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
* ``--no-tune``: Don't run ``perf system tune`` to tune the system for
  benchmarks.

If the branch is not set:

* If ``REVISION`` is a branch name: use it as a the branch, and get the
  latest revision of this branch
* Otherwise, use ``master`` branch by default


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

See also perf documentation: `How to get reproductible benchmark results
<http://perf.readthedocs.io/en/latest/run_benchmark.html#how-to-get-reproductible-benchmark-results>`_.

Advices helping to get make stable benchmarks:

* Run ``python3 -m perf system tune`` command
* See also advices in the perf documentation: `Stable and reliable benchmarks
  <http://perf.readthedocs.io/en/latest/perf.html#stable-and-reliable-benchmarks>`_
* Compile Python using LTO (Link Time Optimization) and PGO (profile guided
  optimizations)::

    ./configure --with-lto
    make profile-opt

  You should get the ``-flto`` option on GCC for example.

* Use the ``--rigorous`` option of the ``run`` command

Notes:

* Development versions of Python 2.7, 3.6 and 3.7 have a --enable-optimizations
  configure option
* --enable-optimizations doesn't enable LTO because of compiler bugs:
  http://bugs.python.org/issue28032
  (see also: http://bugs.python.org/issue28605)
* PGO is broken on Ubuntu 14.04 LTS with GCC 4.8.4-2ubuntu1~14.04:
  ``Modules/socketmodule.c:7743:1: internal compiler error: in edge_badness,
  at ipa-inline.c:895``
* If the ``nohz_full`` kernel option is used, the CPU frequency must be fixed,
  otherwise the CPU frequency will be instable. See `Bug 1378529: intel_pstate
  driver doesn't support NOHZ_FULL
  <https://bugzilla.redhat.com/show_bug.cgi?id=1378529>`_.
* ASLR must *not* be disabled manually! (it's enabled by default on Linux)


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
