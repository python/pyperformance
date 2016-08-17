#!/usr/bin/env python

"""Script for testing the performance of logging simple messages.
"""

# Python imports
import io
import logging

# Third party imports
import six
from six.moves import xrange
import perf.text_runner

# A simple format for parametered logging
FORMAT = 'important: %s'
MESSAGE = 'some important information to be logged'


def bench_no_output(loops, logger):
    # micro-optimization: use fast local variables
    m = MESSAGE
    range_it = xrange(loops)
    t0 = perf.perf_counter()

    for _ in range_it:
        # repeat 10 times
        logger.debug(m)
        logger.debug(m)
        logger.debug(m)
        logger.debug(m)
        logger.debug(m)
        logger.debug(m)
        logger.debug(m)
        logger.debug(m)
        logger.debug(m)
        logger.debug(m)

    return perf.perf_counter() - t0


def bench_simple_output(loops, logger):
    # micro-optimization: use fast local variables
    m = MESSAGE
    range_it = xrange(loops)
    t0 = perf.perf_counter()

    for _ in range_it:
        # repeat 10 times
        logger.warn(m)
        logger.warn(m)
        logger.warn(m)
        logger.warn(m)
        logger.warn(m)
        logger.warn(m)
        logger.warn(m)
        logger.warn(m)
        logger.warn(m)
        logger.warn(m)

    return perf.perf_counter() - t0


def bench_formatted_output(loops, logger):
    # micro-optimization: use fast local variables
    f = FORMAT
    m = MESSAGE
    range_it = xrange(loops)
    t0 = perf.perf_counter()

    for _ in range_it:
        # repeat 10 times
        logger.warn(f, m)
        logger.warn(f, m)
        logger.warn(f, m)
        logger.warn(f, m)
        logger.warn(f, m)
        logger.warn(f, m)
        logger.warn(f, m)
        logger.warn(f, m)
        logger.warn(f, m)
        logger.warn(f, m)

    return perf.perf_counter() - t0


def prepare_subprocess_args(runner, args):
    args.append(runner.args.benchmark)


if __name__ == "__main__":
    runner = perf.text_runner.TextRunner(name='logging', inner_loops=10)
    runner.metadata['description'] = "Test the performance of logging."
    runner.prepare_subprocess_args = prepare_subprocess_args

    parser = runner.argparser
    benchmarks = ["no_output", "simple_output", "formatted_output"]
    parser.add_argument("benchmark", choices=benchmarks)

    options = runner.parse_args()
    benchmark = globals()["bench_" + options.benchmark]
    runner.name += "/%s" % options.benchmark

    # NOTE: StringIO performance will impact the results...
    if six.PY3:
        sio = io.StringIO()
    else:
        sio = io.BytesIO()

    handler = logging.StreamHandler(stream=sio)
    logger = logging.getLogger("benchlogger")
    logger.propagate = False
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)

    runner.bench_sample_func(benchmark, logger)

    if benchmark is not bench_no_output:
        assert len(sio.getvalue()) > 0
    else:
        assert len(sio.getvalue()) == 0
