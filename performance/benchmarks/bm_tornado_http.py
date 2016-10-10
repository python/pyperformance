
"""Test the performance of simple HTTP serving and client using the Tornado
framework.

A trivial "application" is generated which generates a number of chunks of
data as a HTTP response's body.
"""

import socket

from six.moves import xrange
import perf.text_runner

from tornado.httpclient import AsyncHTTPClient
from tornado.httpserver import HTTPServer
from tornado.gen import coroutine, Task
from tornado.ioloop import IOLoop
from tornado.netutil import bind_sockets
from tornado.web import RequestHandler, Application


HOST = "127.0.0.1"
FAMILY = socket.AF_INET

CHUNK = b"Hello world\n" * 1000
NCHUNKS = 5

CONCURRENCY = 150


class MainHandler(RequestHandler):

    @coroutine
    def get(self):
        for i in range(NCHUNKS):
            self.write(CHUNK)
            yield Task(self.flush)

    def compute_etag(self):
        # Overriden to avoid stressing hashlib in this benchmark
        return None


def make_application():
    return Application([
        (r"/", MainHandler),
    ])


def make_http_server(loop, request_handler):
    server = HTTPServer(request_handler, io_loop=loop)
    sockets = bind_sockets(0, HOST, family=FAMILY)
    assert len(sockets) == 1
    server.add_sockets(sockets)
    return sockets[0].getsockname()


def bench_tornado(loops):
    loop = IOLoop.instance()
    host, port = make_http_server(loop, make_application())
    url = "http://%s:%s/" % (host, port)
    namespace = {}

    @coroutine
    def run_client():
        client = AsyncHTTPClient()
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:
            futures = [client.fetch(url) for j in xrange(CONCURRENCY)]
            for fut in futures:
                resp = yield fut
                buf = resp.buffer
                buf.seek(0, 2)
                assert buf.tell() == len(CHUNK) * NCHUNKS

        namespace['dt'] = perf.perf_counter() - t0

    loop.run_sync(run_client)
    return namespace['dt']


if __name__ == "__main__":
    kw = {}
    if perf.python_has_jit():
        # PyPy needs more samples to warmup its JIT
        kw['warmups'] = 30
    runner = perf.text_runner.TextRunner(name='tornado_http', **kw)
    runner.metadata['description'] = ("Test the performance of HTTP requests "
                                      "with Tornado.")
    runner.bench_sample_func(bench_tornado)
