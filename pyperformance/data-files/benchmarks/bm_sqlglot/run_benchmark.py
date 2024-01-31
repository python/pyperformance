import pyperf

from sqlglot import parse_one, transpile
from sqlglot.executor import execute
from sqlglot.optimizer import optimize, normalize


SQL = """
select
        supp_nation,
        cust_nation,
        l_year,
        sum(volume) as revenue
from
        (
                select
                        n1.n_name as supp_nation,
                        n2.n_name as cust_nation,
                        extract(year from l_shipdate) as l_year,
                        l_extendedprice * (1 - l_discount) as volume
                from
                        supplier,
                        lineitem,
                        orders,
                        customer,
                        nation n1,
                        nation n2
                where
                        s_suppkey = l_suppkey
                        and o_orderkey = l_orderkey
                        and c_custkey = o_custkey
                        and s_nationkey = n1.n_nationkey
                        and c_nationkey = n2.n_nationkey
                        and (
                                (n1.n_name = 'FRANCE' and n2.n_name = 'GERMANY')
                                or (n1.n_name = 'GERMANY' and n2.n_name = 'FRANCE')
                        )
                        and l_shipdate between date '1995-01-01' and date '1996-12-31'
        ) as shipping
group by
        supp_nation,
        cust_nation,
        l_year
order by
        supp_nation,
        cust_nation,
        l_year;
"""

TPCH_SCHEMA = {
    "lineitem": {
        "l_orderkey": "int",
        "l_partkey": "int",
        "l_suppkey": "int",
        "l_linenumber": "int",
        "l_quantity": "double",
        "l_extendedprice": "double",
        "l_discount": "double",
        "l_tax": "double",
        "l_returnflag": "string",
        "l_linestatus": "string",
        "l_shipdate": "date",
        "l_commitdate": "date",
        "l_receiptdate": "date",
        "l_shipinstruct": "string",
        "l_shipmode": "string",
        "l_comment": "string",
    },
    "orders": {
        "o_orderkey": "int",
        "o_custkey": "int",
        "o_orderstatus": "string",
        "o_totalprice": "double",
        "o_orderdate": "date",
        "o_orderpriority": "string",
        "o_clerk": "string",
        "o_shippriority": "int",
        "o_comment": "string",
    },
    "customer": {
        "c_custkey": "int",
        "c_name": "string",
        "c_address": "string",
        "c_nationkey": "int",
        "c_phone": "string",
        "c_acctbal": "double",
        "c_mktsegment": "string",
        "c_comment": "string",
    },
    "part": {
        "p_partkey": "int",
        "p_name": "string",
        "p_mfgr": "string",
        "p_brand": "string",
        "p_type": "string",
        "p_size": "int",
        "p_container": "string",
        "p_retailprice": "double",
        "p_comment": "string",
    },
    "supplier": {
        "s_suppkey": "int",
        "s_name": "string",
        "s_address": "string",
        "s_nationkey": "int",
        "s_phone": "string",
        "s_acctbal": "double",
        "s_comment": "string",
    },
    "partsupp": {
        "ps_partkey": "int",
        "ps_suppkey": "int",
        "ps_availqty": "int",
        "ps_supplycost": "double",
        "ps_comment": "string",
    },
    "nation": {
        "n_nationkey": "int",
        "n_name": "string",
        "n_regionkey": "int",
        "n_comment": "string",
    },
    "region": {
        "r_regionkey": "int",
        "r_name": "string",
        "r_comment": "string",
    },
}


def bench_parse(loops):
    elapsed = 0
    for _ in range(loops):
        t0 = pyperf.perf_counter()
        parse_one(SQL)
        elapsed += pyperf.perf_counter() - t0
    return elapsed


def bench_transpile(loops):
    elapsed = 0
    for _ in range(loops):
        t0 = pyperf.perf_counter()
        transpile(SQL, write="spark")
        elapsed += pyperf.perf_counter() - t0
    return elapsed


def bench_optimize(loops):
    elapsed = 0
    for _ in range(loops):
        t0 = pyperf.perf_counter()
        optimize(parse_one(SQL), TPCH_SCHEMA)
        elapsed += pyperf.perf_counter() - t0
    return elapsed


def bench_normalize(loops):
    elapsed = 0
    conjunction = parse_one("(A AND B) OR (C AND D) OR (E AND F) OR (G AND H)")
    for _ in range(loops):
        t0 = pyperf.perf_counter()
        normalize.normalize(conjunction)
        elapsed += pyperf.perf_counter() - t0
    return elapsed


def bench_execute(loops):
    tables = {
        "sushi": [],
        "order_items": [],
        "orders": [],
    }

    for i in range(10000):
        tables["sushi"].append({"id": i, "price": i})
        tables["order_items"].append({"sushi_id": i, "order_id": i})
        tables["orders"].append({"id": i, "user_id": i})

    elapsed = 0
    for _ in range(loops):
        t0 = pyperf.perf_counter()
        execute(
            """
            SELECT
              o.user_id,
              s.price / 2 AS half_price,
              AVG(s.price) AS avg_price,
              SUM(s.price) AS price
            FROM orders o
            JOIN order_items i
              ON o.id = i.order_id
            JOIN sushi s
              ON i.sushi_id = s.id
            GROUP BY o.user_id
            """,
            tables=tables,
        )
        elapsed += pyperf.perf_counter() - t0
    return elapsed


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "SQLGlot benchmark"
    runner.bench_time_func("sqlglot_parse", bench_parse)
    runner.bench_time_func("sqlglot_transpile", bench_transpile)
    runner.bench_time_func("sqlglot_optimize", bench_optimize)
    runner.bench_time_func("sqlglot_normalize", bench_normalize)
    runner.bench_time_func("sqlglot_execute", bench_execute)
