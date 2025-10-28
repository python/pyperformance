# Benchmarking Scripts Toolkit

Companion assets for running `pyperformance` benchmarks on hosts that provide isolated CPUs and for backfilling historical CPython revisions to [speed.python.org](https://speed.python.org/).

## Contents
- `run-pyperformance.sh` – shell wrapper that reserves an isolated CPU (175–191) via lockfiles, renders `benchmark.conf` from `benchmark.conf.in` with `m4`, sets up a virtual environment, and runs `pyperformance` with upload enabled.
- `benchmark.conf.in` – template consumed by the wrapper; placeholders `TMPDIR` and `CPUID` are filled in so each run has its own working tree, build directory, and CPU affinity.
- `backfill.py` – Python helper that reads revisions from `backfill_shas.txt` and launches multiple `run-pyperformance.sh` jobs in parallel, capturing stdout/stderr per revision under `output/`.
- `backfill_shas.txt` – example list of `sha=branch` pairs targeted by the backfill script.

## Typical Workflow
1. Ensure kernel CPU isolation (`isolcpus=175-191`) and the `lockfile` utility are available so the wrapper can pin workloads without contention.
2. Invoke `./run-pyperformance.sh -- compile benchmark.conf <sha> <branch>` for an ad-hoc run; the script installs `pyperformance==1.13.0`, clones CPython, and uploads results using the environment label configured in `benchmark.conf.in`.
3. Populate `backfill_shas.txt` with the revisions you want to replay and run `python backfill.py` to batch process them; individual logs land in `output/<branch>-<sha>.out|.err`.

Adjust `benchmark.conf.in` if you need to change build parameters (PGO/LTO, job count, upload target, etc.).

## Scheduled Runs
If you want a daily unattended run, drop an entry like this into `crontab -e` on the host:

```
0 0 * * * cd /home/user/pyperformance/examples/benchmarking-scripts && ./run-pyperformance.sh -- compile_all benchmark.conf > /home/pyperf/pyperformance/cron.log 2>&1
```
