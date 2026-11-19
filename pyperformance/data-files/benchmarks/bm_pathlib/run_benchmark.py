"""
Test the performance of pathlib operations.

This benchmark stresses the creation of small objects, globbing, and system
calls.
"""

# Python imports
import os
import pathlib
import shutil
import tempfile
from typing import Sequence

import pyperf


NUM_FILES = 2000


def generate_filenames(tmp_path, num_files):
    i = 0
    while num_files:
        for ext in [".py", ".txt", ".tar.gz", ""]:
            i += 1
            yield os.path.join(tmp_path, str(i) + ext)
            num_files -= 1


def setup(num_files):
    tmp_path = tempfile.mkdtemp()
    for fn in generate_filenames(tmp_path, num_files):
        with open(fn, "wb") as f:
            f.write(b'benchmark')

    return tmp_path


def warm_up_cache(base_path):
    # Warm up the filesystem cache and keep some objects in memory.
    path_objects = list(base_path.iterdir())
    # FIXME: does this code really cache anything?
    for p in path_objects:
        p.stat()
    assert len(path_objects) == NUM_FILES, len(path_objects)


def setup_single_benchmark(loops, tmp_path):
    base_path = pathlib.Path(tmp_path)
    warm_up_cache(base_path)
    range_it = range(loops)
    
    return base_path, range_it


def bench_pathlib_callable(loops, tmp_path, callable_):
    base_path, range_it = setup_single_benchmark(loops, tmp_path)

    t0 = pyperf.perf_counter()

    for _ in range_it:
        callable_(base_path)

    return pyperf.perf_counter() - t0

def bench_pure_pathlib_callable(loops, paths, callable_):
    range_it = range(loops)
    
    t0 = pyperf.perf_counter()

    for _ in range_it:
        callable_(paths)

    return pyperf.perf_counter() - t0


def do_simple_operations(base_path: pathlib.Path):
    # Do something simple with each path.
    for p in base_path.iterdir():
        p.stat()
    for p in base_path.glob("*.py"):
        p.stat()
    for p in base_path.iterdir():
        p.stat()
    for p in base_path.glob("*.py"):
        p.stat()


def do_parent(paths: Sequence[pathlib.PurePath]):
    for p in paths:
        p.parent


def do_parents(paths: Sequence[pathlib.PurePath]):
    # FIXME: this is not a good benchmark, because it creates a new list. However, otherwise it would be too slow
    for p in paths[:300]:
        list(p.parents)


def do_name(paths: Sequence[pathlib.PurePath]):
    for p in paths:
        p.name


def do_suffix(paths: Sequence[pathlib.PurePath]):
    for p in paths:
        p.suffix


def do_suffixes(paths: Sequence[pathlib.PurePath]):
    for p in paths:
        list(p.suffixes)


def do_stem(paths: Sequence[pathlib.PurePath]):
    for p in paths:
        p.stem


def do_parts(paths: Sequence[pathlib.PurePath]):
    for p in paths:
        list(p.parts)


def do_joinpath(paths: Sequence[pathlib.PurePath]):
    for p in paths:
        p.joinpath("foo")


def do_div(paths: Sequence[pathlib.PurePath]):
    for p in paths:
        p / "foo"


def do_with_name(paths: Sequence[pathlib.PurePath]):
    for p in paths:
        p.with_name("foo")


def do_with_suffix(paths: Sequence[pathlib.PurePath]):
    for p in paths:
        p.with_suffix(".py")


def do_relative_to(paths: Sequence[pathlib.PurePath]):
    for p in paths:
        p.relative_to("..")


def do_is_absolute(paths: Sequence[pathlib.PurePath]):
    for p in paths:
        p.is_absolute()


def do_is_reserved(paths: Sequence[pathlib.PurePath]):
    for p in paths:
        p.is_reserved()


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = ("Test the performance of "
                                      "pathlib operations.")

    modname = pathlib.__name__
    runner.metadata['pathlib_module'] = modname

    tmp_path = setup(NUM_FILES)
    paths = tuple(pathlib.PurePath(*([f"foo{i}"] * i)) for i in range(NUM_FILES))

    try:
        runner.bench_time_func('pathlib', bench_pathlib_callable, tmp_path, do_simple_operations)
        runner.bench_time_func('pathlib_purepath_parent', bench_pure_pathlib_callable, paths, do_parent)
        runner.bench_time_func('pathlib_purepath_parents', bench_pure_pathlib_callable, paths, do_parents)
        runner.bench_time_func('pathlib_purepath_name', bench_pure_pathlib_callable, paths, do_name)
        runner.bench_time_func('pathlib_purepath_suffix', bench_pure_pathlib_callable, paths, do_suffix)
        runner.bench_time_func('pathlib_purepath_suffixes', bench_pure_pathlib_callable, paths, do_suffixes)
        runner.bench_time_func('pathlib_purepath_stem', bench_pure_pathlib_callable, paths, do_stem)
        runner.bench_time_func('pathlib_purepath_parts', bench_pure_pathlib_callable, paths, do_parts)
        runner.bench_time_func('pathlib_purepath_joinpath', bench_pure_pathlib_callable, paths, do_joinpath)
        runner.bench_time_func('pathlib_purepath_div', bench_pure_pathlib_callable, paths, do_div)
        runner.bench_time_func('pathlib_purepath_with_name', bench_pure_pathlib_callable, paths, do_with_name)
        runner.bench_time_func('pathlib_purepath_with_suffix', bench_pure_pathlib_callable, paths, do_with_suffix)
        runner.bench_time_func('pathlib_purepath_relative_to', bench_pure_pathlib_callable, paths, do_relative_to)
        runner.bench_time_func('pathlib_purepath_is_absolute', bench_pure_pathlib_callable, paths, do_is_absolute)
        runner.bench_time_func('pathlib_purepath_is_reserved', bench_pure_pathlib_callable, paths, do_is_reserved)
        
    finally:
        shutil.rmtree(tmp_path)
