TODO
====

* bm_nqueens: Remove the "Pure-Python implementation of
  itertools.permutations()"?
* Decide of sqlalchemy benchmarks should only benchmark SELECT ALL
  or INSERT+SELECT?
* Run pep8 on Travis
* python3 -m performance list: list Python 2 benchmarks, but mention that
  they are incompatible with Python 3?
* Port bm_pyflate to Python 3?
* Add benchmarks from the Pyston benchmark suite:
  https://github.com/dropbox/pyston-perf
  and convince Pyston to use performance :-)
* pybench: don't use private perf submodules/functions
* Remove deprecated threading tests? bench.py -b threading doesn't run anything
* pybench: calibrate once in the main process, then pass the number of loops
  to workers? Or rewrite pybench as N subenchmarks?
* html5lib: 1 warmup, 3 runs: run 2 is always 10% slower!?


Port PyPy benchmarks
====================

Repository: https://bitbucket.org/pypy/benchmarks/

Different from performance?

* json_bench

Todo:

* mdp: https://github.com/python/performance/pull/14
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

* ai (called bm_nqueens in performance)
* bm_chameleon
* bm_mako
* chaos
* crypto_pyaes
* deltablue
* django (called django_template in performance)
* dulwich_log
* fannkuch
* float
* genshi_text
* genshi_xml
* go
* hexiom2
* html5lib
* meteor-contest
* nbody_modified (called nbody in performance)
* nqueens
* pidigits
* pyflate-fast (called pyflate in performance)
* raytrace-simple (called raytrace in performance)
* richards
* scimark_fft
* scimark_lu
* scimark_montecarlo
* scimark_sor
* scimark_sparsematmult
* spambayes
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

TODO:

- django_lexing
- django_migrate
- django_template2
- django_template3_10x
- django_template3
- django_template
- fasta
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
- raytrace, raytrace_small
- richards
- sqlalchemy_imperative, sqlalchemy_imperative2, sqlalchemy_imperative2_10x
- sre_compile_ubench: performance has a much more complete benchmark


pybench
=======

* pybench.TryExcept: some runs are 153% slower
* pybench: 1/20 run of TryExcept is 2x slower depending on the ASLR (not on the hash seed)

    $ for run in $(seq 1 40); do echo -n "run $run:"; PYTHONHASHSEED=1 python3 pybench.py -b TryExcept -l 32768 --worker --stdout 2>/dev/null|python3 -m perf show -; done
    ...
    run 29:Median +- std dev: 13.4 ns +- 0.0 ns
    run 30:Median +- std dev: 34.0 ns +- 0.1 ns  # 2x slower
    run 31:Median +- std dev: 13.5 ns +- 0.0 ns
    ...

* pybench.CompareStrings: a few runs are 50% faster (54.2 ns => 28.1 ns)
  XXX one worker uses a different number of loops?

* pybench.CompareStrings: ERROR: the benchmark is very unstable, the standard deviation is very high (stdev/median: 22%)!
  pybench.CompareStrings: Try to rerun the benchmark with more runs, samples and/or loops

* pybench.SimpleLongArithmetic: WARNING: the benchmark seems unstable, the standard deviation is high (stdev/median: 13%)
  pybench.SimpleLongArithmetic: Try to rerun the benchmark with more runs, samples and/or loops

