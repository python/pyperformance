"""
Benchmark graph creation and algorithms from NetworkX.
"""

import pyperf

import networkx as nx


G = nx.erdos_renyi_graph(200, 0.02)


def bench_sparse_graph_creation():
    _ = nx.erdos_renyi_graph(100, 0.02)


def bench_dense_graph_creation():
    _ = nx.erdos_renyi_graph(100, 0.9)


def bench_betweenness():
    _ = nx.betweenness_centrality(G)


def bench_modularity():
    _ = nx.community.greedy_modularity_communities(G)


BENCHMARKS = (
    "sparse_graph_creation",
    "dense_graph_creation",
    "betweenness",
    "modularity",
)


def bench_networkx(loops, func):
    t0 = pyperf.perf_counter()
    for _ in range(loops):
        func()
    return pyperf.perf_counter() - t0


def add_cmdline_args(cmd, args):
    if args.benchmark:
        cmd.append(args.benchmark)


if __name__ == "__main__":
    runner = pyperf.Runner(add_cmdline_args=add_cmdline_args)
    runner.metadata["description"] = "NetworkX benchmark"
    runner.argparser.add_argument("benchmark", nargs="?", choices=sorted(BENCHMARKS))

    args = runner.parse_args()
    if args.benchmark:
        benchmarks = (args.benchmark,)
    else:
        benchmarks = sorted(BENCHMARKS)

    for bench in benchmarks:
        name = "networkx_%s" % bench
        func = globals()["bench_" + bench]
        runner.bench_time_func(name, bench_networkx, func)
