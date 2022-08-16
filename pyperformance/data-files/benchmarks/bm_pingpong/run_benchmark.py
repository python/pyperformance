"""
Benchmark for inter-process communication.
"""
import pyperf
from multiprocessing import Process, Pipe


def ping(in_p, out_p, n):
    out_p.send(n)
    while True:
        got = in_p.recv()
        got -= 1
        out_p.send(got)
        if got < 0:
            break
    in_p.close()
    out_p.close()


def pong(in_p, out_p):
    while True:
        got = in_p.recv()
        if got < 0:
            break
        out_p.send(got)
    in_p.close()
    out_p.close()


def pingpong(n):
    t0 = pyperf.perf_counter()
    in_p0, out_p0 = Pipe()
    in_p1, out_p1 = Pipe()
    p0 = Process(target=ping, args=(in_p1, out_p0, n))
    p1 = Process(target=pong, args=(in_p0, out_p1))
    p0.start()
    p1.start()
    p0.join()
    p1.join()
    return pyperf.perf_counter() - t0


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata["description"] = "pingpong benchmark"
    count = 1000
    runner.bench_func("pingpong", pingpong, count)
