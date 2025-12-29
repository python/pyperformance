"""Benchmark for the base64 module's primary public APIs.

Tests encoding and decoding performance across various variants
and data sizes.
"""

import base64
import random
import pyperf


# Generate test data with fixed seed for reproducibility
random.seed(12345)
DATA_TINY = bytes(random.randrange(256) for _ in range(20))
DATA_SMALL = bytes(random.randrange(256) for _ in range(127))  # odd on purpose
DATA_MEDIUM = bytes(random.randrange(256) for _ in range(3072))
DATA_LARGE = bytes(random.randrange(256) for _ in range(102400))

# Pre-encoded data for decode benchmarks
B64_TINY = base64.b64encode(DATA_TINY)
B64_SMALL = base64.b64encode(DATA_SMALL)
B64_MEDIUM = base64.b64encode(DATA_MEDIUM)
B64_LARGE = base64.b64encode(DATA_LARGE)

B64_URLSAFE_TINY = base64.urlsafe_b64encode(DATA_TINY)
B64_URLSAFE_SMALL = base64.urlsafe_b64encode(DATA_SMALL)
B64_URLSAFE_MEDIUM = base64.urlsafe_b64encode(DATA_MEDIUM)
# large intentionally excluded... c'mon people, they're URLs!

B32_TINY = base64.b32encode(DATA_TINY)
B32_SMALL = base64.b32encode(DATA_SMALL)
B32_MEDIUM = base64.b32encode(DATA_MEDIUM)
B32_LARGE = base64.b32encode(DATA_LARGE)

B16_TINY = base64.b16encode(DATA_TINY)
B16_SMALL = base64.b16encode(DATA_SMALL)
B16_MEDIUM = base64.b16encode(DATA_MEDIUM)
B16_LARGE = base64.b16encode(DATA_LARGE)

A85_TINY = base64.a85encode(DATA_TINY)
A85_SMALL = base64.a85encode(DATA_SMALL)
A85_MEDIUM = base64.a85encode(DATA_MEDIUM)
A85_LARGE = base64.a85encode(DATA_LARGE)

A85_WRAP_TINY = base64.a85encode(DATA_TINY, wrapcol=76)
A85_WRAP_SMALL = base64.a85encode(DATA_SMALL, wrapcol=76)
A85_WRAP_MEDIUM = base64.a85encode(DATA_MEDIUM, wrapcol=76)
A85_WRAP_LARGE = base64.a85encode(DATA_LARGE, wrapcol=76)

B85_TINY = base64.b85encode(DATA_TINY)
B85_SMALL = base64.b85encode(DATA_SMALL)
B85_MEDIUM = base64.b85encode(DATA_MEDIUM)
B85_LARGE = base64.b85encode(DATA_LARGE)


def bench_b64encode(loops):
    range_it = range(loops)
    t0 = pyperf.perf_counter()
    for _ in range_it:
        base64.b64encode(DATA_TINY)
        base64.b64encode(DATA_SMALL)
        base64.b64encode(DATA_MEDIUM)
        base64.b64encode(DATA_LARGE)
    return pyperf.perf_counter() - t0


def bench_b64decode(loops):
    range_it = range(loops)
    t0 = pyperf.perf_counter()
    for _ in range_it:
        base64.b64decode(B64_TINY)
        base64.b64decode(B64_SMALL)
        base64.b64decode(B64_MEDIUM)
        base64.b64decode(B64_LARGE)
    return pyperf.perf_counter() - t0


def bench_urlsafe_b64encode(loops):
    range_it = range(loops)
    t0 = pyperf.perf_counter()
    for _ in range_it:
        base64.urlsafe_b64encode(DATA_TINY)
        base64.urlsafe_b64encode(DATA_SMALL)
        base64.urlsafe_b64encode(DATA_MEDIUM)
    return pyperf.perf_counter() - t0


def bench_urlsafe_b64decode(loops):
    range_it = range(loops)
    t0 = pyperf.perf_counter()
    for _ in range_it:
        base64.urlsafe_b64decode(B64_URLSAFE_TINY)
        base64.urlsafe_b64decode(B64_URLSAFE_SMALL)
        base64.urlsafe_b64decode(B64_URLSAFE_MEDIUM)
    return pyperf.perf_counter() - t0


def bench_b32encode(loops):
    range_it = range(loops)
    t0 = pyperf.perf_counter()
    for _ in range_it:
        base64.b32encode(DATA_TINY)
        base64.b32encode(DATA_SMALL)
        base64.b32encode(DATA_MEDIUM)
        base64.b32encode(DATA_LARGE)
    return pyperf.perf_counter() - t0


def bench_b32decode(loops):
    range_it = range(loops)
    t0 = pyperf.perf_counter()
    for _ in range_it:
        base64.b32decode(B32_TINY)
        base64.b32decode(B32_SMALL)
        base64.b32decode(B32_MEDIUM)
        base64.b32decode(B32_LARGE)
    return pyperf.perf_counter() - t0


def bench_b16encode(loops):
    range_it = range(loops)
    t0 = pyperf.perf_counter()
    for _ in range_it:
        base64.b16encode(DATA_TINY)
        base64.b16encode(DATA_SMALL)
        base64.b16encode(DATA_MEDIUM)
        base64.b16encode(DATA_LARGE)
    return pyperf.perf_counter() - t0


def bench_b16decode(loops):
    range_it = range(loops)
    t0 = pyperf.perf_counter()
    for _ in range_it:
        base64.b16decode(B16_TINY)
        base64.b16decode(B16_SMALL)
        base64.b16decode(B16_MEDIUM)
        base64.b16decode(B16_LARGE)
    return pyperf.perf_counter() - t0


def bench_a85encode(loops):
    range_it = range(loops)
    t0 = pyperf.perf_counter()
    for _ in range_it:
        base64.a85encode(DATA_TINY)
        base64.a85encode(DATA_SMALL)
        base64.a85encode(DATA_MEDIUM)
        base64.a85encode(DATA_LARGE)
    return pyperf.perf_counter() - t0


def bench_a85decode(loops):
    range_it = range(loops)
    t0 = pyperf.perf_counter()
    for _ in range_it:
        base64.a85decode(A85_TINY)
        base64.a85decode(A85_SMALL)
        base64.a85decode(A85_MEDIUM)
        base64.a85decode(A85_LARGE)
    return pyperf.perf_counter() - t0


def bench_b85encode(loops):
    range_it = range(loops)
    t0 = pyperf.perf_counter()
    for _ in range_it:
        base64.b85encode(DATA_TINY)
        base64.b85encode(DATA_SMALL)
        base64.b85encode(DATA_MEDIUM)
        base64.b85encode(DATA_LARGE)
    return pyperf.perf_counter() - t0


def bench_b85decode(loops):
    range_it = range(loops)
    t0 = pyperf.perf_counter()
    for _ in range_it:
        base64.b85decode(B85_TINY)
        base64.b85decode(B85_SMALL)
        base64.b85decode(B85_MEDIUM)
        base64.b85decode(B85_LARGE)
    return pyperf.perf_counter() - t0


def bench_a85encode_wrapcol(loops):
    range_it = range(loops)
    t0 = pyperf.perf_counter()
    for _ in range_it:
        base64.a85encode(DATA_TINY, wrapcol=76)
        base64.a85encode(DATA_SMALL, wrapcol=76)
        base64.a85encode(DATA_MEDIUM, wrapcol=76)
        base64.a85encode(DATA_LARGE, wrapcol=76)
    return pyperf.perf_counter() - t0


def bench_b64decode_validate(loops):
    range_it = range(loops)
    t0 = pyperf.perf_counter()
    for _ in range_it:
        base64.b64decode(B64_TINY, validate=True)
        base64.b64decode(B64_SMALL, validate=True)
        base64.b64decode(B64_MEDIUM, validate=True)
        base64.b64decode(B64_LARGE, validate=True)
    return pyperf.perf_counter() - t0


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Benchmark base64 module encoding/decoding"

    runner.bench_time_func('base64_encode', bench_b64encode)
    runner.bench_time_func('base64_decode', bench_b64decode)
    runner.bench_time_func('base64_decode_validate', bench_b64decode_validate)
    runner.bench_time_func('urlsafe_base64_encode', bench_urlsafe_b64encode)
    runner.bench_time_func('urlsafe_base64_decode', bench_urlsafe_b64decode)
    runner.bench_time_func('base32_encode', bench_b32encode)
    runner.bench_time_func('base32_decode', bench_b32decode)
    runner.bench_time_func('base16_encode', bench_b16encode)
    runner.bench_time_func('base16_decode', bench_b16decode)
    runner.bench_time_func('ascii85_encode', bench_a85encode)
    runner.bench_time_func('ascii85_decode', bench_a85decode)
    runner.bench_time_func('ascii85_encode_wrapcol', bench_a85encode_wrapcol)
    runner.bench_time_func('base85_encode', bench_b85encode)
    runner.bench_time_func('base85_decode', bench_b85decode)
