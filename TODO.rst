TODO
====

* Remove genshi module? Last release in January 2014!
* upload:

  - add Q1 and Q3: keys 'q1' and 'q3'
  - "description"

* bm_python_startup: add again python metadata, to get back the Python version
  in benchmark suite metadata. Same for bm_hg_startup.
* Remove compare command or reimplement it using pyperf compare_to
* Add a --log option to create a log file. Use the logging module
  and replace print() with logger.error().
* Write a test to ensure that benchmarks listed in groups exist
* Decide if sqlalchemy benchmarks should only benchmark SELECT ALL
  or INSERT+SELECT?
* Run pep8 on Travis
* compile: add metadata on compiler option, especially LTO and PGO flags


Bugs on old CPython version
===========================

* Python 3.5.0beta2: SyntaxError in parse() of chameleon/astutil.py,
  on parsing "def func(target):". Failed commits:

  * CPython 8a8f453c5a6d

* Skip bm_django_template on Python 3 older than 3.4:
  Python 3.3.6 final: django_template: django/utils/module_loading.py:
  "from importlib.util import find_spec as importlib_find"
  ImportError: cannot import name find_spec
  CPython 75e3630c6071

* sympy uses deprecated inspect.getargspec(), function removed from 3.6a0 then
  reintroduced. TODO: fix sympy upstream?
  sympy: sympy/core/function.py
  "inspect.getargspec(cls.eval)"
  module 'inspect' has no attribute 'getargspec'
  CPython 0d30940dd256


numpy benchmarks?
=================

* https://morepypy.blogspot.fr/2016/11/vectorization-extended-powerpc-and-s390x.html
* https://bitbucket.org/plan_rich/numpy-benchmark
  fork of https://bitbucket.org/mikefc/numpy-benchmark/src to use pyperf


Port PyPy benchmarks
====================

Repository: https://bitbucket.org/pypy/benchmarks/

Different from pyperformance?

* json_bench

Todo:

* pypy_interp
* pyxl_bench

  PyPI version 1.0: https://pypi.python.org/pypi/pyxl (2012)
  Old repo: https://github.com/awable/pyxl (last commit: Feb 2013)
  Python2: https://github.com/dropbox/pyxl (latest commit: Aug 2016)
  Python3: https://github.com/gvanrossum/pyxl3 (latest commit: Apr 2016)

* sphinx

  benchmarks.py: invoke sphinx-build.py on lib/cpython-doc/
  cpython-doc/: 24 MB

* trans2_annotate
* trans2_backendopt
* trans2_database
* trans2_rtype
* trans2_source
* twisted_iteration
* twisted_names
* twisted_pb
* twisted_tcp

Deliberate choice to not add it:

* eparse: https://pypi.python.org/pypi/Monte 0.0.11 was released in 2013,
  no tarball on PyPI, only on SourceForge
* krakatau: https://github.com/Storyyeller/Krakatau is not on PyPI, but it
  seems actively developed
* slowspitfire, spitfire, spitfire_cstringio: not on PyPI
* rietveld: not on PyPy

Done:

* ai (called bm_nqueens in pyperformance)
* bm_chameleon
* bm_mako
* chaos
* crypto_pyaes
* deltablue
* django (called django_template in pyperformance)
* dulwich_log
* fannkuch
* float
* genshi_text
* genshi_xml
* go
* hexiom2
* html5lib
* mdp
* meteor-contest
* nbody_modified (called nbody in pyperformance)
* nqueens
* pidigits
* pyflate-fast (called pyflate in pyperformance)
* raytrace-simple (called raytrace in pyperformance)
* richards
* scimark_fft
* scimark_lu
* scimark_montecarlo
* scimark_sor
* scimark_sparsematmult
* spectral-norm
* sqlalchemy_declarative
* sqlalchemy_imperative
* sqlitesynth (called pyflate in sqlite_synth)
* sympy_expand
* sympy_integrate
* sympy_str
* sympy_sum
* telco


pyston benchmarks
=================

Add benchmarks from the Pyston benchmark suite:
https://github.com/dropbox/pyston-perf
and convince Pyston to use pyperformance :-)

TODO:

- django_lexing
- django_migrate
- django_template2
- django_template3_10x
- django_template3
- django_template
- fasta (it's different than pyperformance "regex_dna")
- interp2
- pyxl_bench_10x
- pyxl_bench2_10x
- pyxl_bench2
- pyxl_bench
- sre_parse_parse
- virtualenv_bench2
- virtualenv_bench

Done:

- chaos
- deltablue
- fannkuch, fannkuch_med
- nbody
- pidigits: pyston has a flat implementation, single function
- raytrace, raytrace_small: use "--width=80 --height=60" cmdline option to get
  raytrace_small profile
- richards
- sqlalchemy_imperative, sqlalchemy_imperative2, sqlalchemy_imperative2_10x:
  use --rows cmdline option to control the number of SQL rows
- sre_compile_ubench: pyperformance has a much more complete benchmark on regex
