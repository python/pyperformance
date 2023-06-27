"""
Benchmarks ported from Numpy's own "app" benchmarks.

https://github.com/numpy/numpy/blob/main/benchmarks/benchmarks/bench_app.py
"""

import pyperf

import numpy as np
from threadpoolctl import threadpool_limits


N = 150
Niter = 1000
dx = 0.1
dy = 0.1
dx2 = dx * dx
dy2 = dy * dy


def num_update(u, dx2, dy2):
    u[1:(-1), 1:(-1)] = (
        ((u[2:, 1:(-1)] + u[:(-2), 1:(-1)]) * dy2)
        + ((u[1:(-1), 2:] + u[1:(-1), :(-2)]) * dx2)
    ) / (2 * (dx2 + dy2))


def num_inplace(u, dx2, dy2):
    tmp = u[:(-2), 1:(-1)].copy()
    np.add(tmp, u[2:, 1:(-1)], out=tmp)
    np.multiply(tmp, dy2, out=tmp)
    tmp2 = u[1:(-1), 2:].copy()
    np.add(tmp2, u[1:(-1), :(-2)], out=tmp2)
    np.multiply(tmp2, dx2, out=tmp2)
    np.add(tmp, tmp2, out=tmp)
    np.multiply(tmp, (1.0 / (2.0 * (dx2 + dy2))), out=u[1:(-1), 1:(-1)])


def laplace(N, Niter, func, args):
    u = np.zeros([N, N], order="C")
    u[0] = 1
    for i in range(Niter):
        func(u, *args)
    return u


def bench_laplace_inplace():
    laplace(N, Niter, num_inplace, args=(dx2, dy2))


def bench_laplace_normal():
    laplace(N, Niter, num_update, args=(dx2, dy2))


np.random.seed(1)
nsubj = 5
nfeat = 1000
ntime = 2000
maxes_of_dots_arrays = [np.random.normal(size=(ntime, nfeat)) for i in range(nsubj)]


def bench_maxes_of_dots(arrays):
    """
    A magical feature score for each feature in each dataset
    :ref:`Haxby et al., Neuron (2011) <HGC+11>`.
    If arrays are column-wise zscore-d before computation it
    results in characterizing each column in each array with
    sum of maximal correlations of that column with columns
    in other arrays.

    Arrays must agree only on the first dimension.

    Numpy uses this as a simultaneous benchmark of 1) dot products
    and 2) max(<array>, axis=<int>).
    """
    # Use a single thread -- multi-threaded is too non-deterministic in timings
    with threadpool_limits(limits=1, user_api='blas'):
        feature_scores = [0] * len(arrays)
        for i, sd in enumerate(arrays):
            for j, sd2 in enumerate(arrays[(i + 1) :]):
                corr_temp = np.dot(sd.T, sd2)
                feature_scores[i] += np.max(corr_temp, axis=1)
                feature_scores[((j + i) + 1)] += np.max(corr_temp, axis=0)
    return feature_scores


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata["description"] = "Benchmark coverage"
    runner.bench_func("numpy_laplace_inplace", bench_laplace_inplace)
    runner.bench_func("numpy_laplace_normal", bench_laplace_normal)
    runner.bench_func("numpy_maxes_of_dots", bench_maxes_of_dots, maxes_of_dots_arrays)
