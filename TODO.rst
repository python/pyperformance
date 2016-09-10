* pybench: don't use private perf submodules/functions
* performance.compare: don't use private perf submodules/functions
* Remove deprecated threading tests?
* Remove json_dump and rename json_dump to json_dump_v2?
* pybench: calibrate once in the main process, then pass the number of loops
  to workers? Or rewrite pybench as N subenchmarks?
* Warning or error if two performance results were produced with two different
  performance major versions (ex: 0.3.x vs 0.2.x). Note: performance 0.1.x
  didn't store its version in results :-/
* bench.py -b threading doesn't run anything
* fastpickle: use accelerator by default, as bm_elementtree
