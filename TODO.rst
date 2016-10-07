* Run pep8 on Travis
* Port bm_pyflate to Python 3?
* Fix installation dulwich on PyPy to be able to upgrade it
* venv.py: open text files in script creating the hash, read also setup.py
  content?
* Fix confusion on benchmark names between the list command,
  benchmarks/__init__.py names and benchmark resulting names
* Add benchmarks from the PyPy benchmark suite:
  https://bitbucket.org/pypy/benchmarks
  and convince PyPy to use performance :-)
* Add benchmarks from the Pyston benchmark suite:
  https://github.com/dropbox/pyston-perf
  and convince Pyston to use performance :-)
* Don't use PYTHONPATH by default when creating the venv: add --inherit-environ
  to be more explicit and avoid surprises
* pybench: don't use private perf submodules/functions
* Remove deprecated threading tests? bench.py -b threading doesn't run anything
* Remove json_dump and rename json_dump to json_dump_v2?
* pybench: calibrate once in the main process, then pass the number of loops
  to workers? Or rewrite pybench as N subenchmarks?
* Warning or error if two performance results were produced with two different
  performance major versions (ex: 0.3.x vs 0.2.x). Note: performance 0.1.x
  didn't store its version in results :-/
* fastpickle: use accelerator by default, as bm_elementtree
* html5lib: 1 warmup, 3 runs: run 2 is always 10% slower!?


Port PyPy benchmarks
====================

Repository: https://bitbucket.org/pypy/benchmarks/

Different from performance?

* json_bench
* nbody_modified
* raytrace-simple

Todo:

* mdp: https://github.com/python/performance/pull/14
* genshi_text
* genshi_xml
* pypy_interp
* pyxl_bench
* sphinx
* sqlalchemy_declarative
* sqlalchemy_imperative
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
* go
* hexiom2
* html5lib
* meteor-contest
* nqueens
* pidigits
* pyflate-fast (called pyflate in performance)
* richards
* scimark_fft
* scimark_lu
* scimark_montecarlo
* scimark_sor
* scimark_sparsematmult
* spambayes
* spectral-norm
* sqlitesynth
* sympy_expand
* sympy_integrate
* sympy_str
* sympy_sum
* telco


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

