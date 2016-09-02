from __future__ import division, with_statement, print_function, absolute_import

import csv
import os.path

import perf
import statistics


def _FormatPerfDataForTable(base_label, changed_label, results):
    """Prepare performance data for tabular output.

    Args:
        base_label: label for the control binary.
        changed_label: label for the experimental binary.
        results: iterable of (bench_name, result) 2-tuples where bench_name is
            the name of the benchmark being reported; and result is a
            BenchmarkResult object.

    Returns:
        A list of 6-tuples, where each tuple corresponds to a row in the output
        table, and each item in the tuples corresponds to a cell in the output
        table.
    """
    table = [("Benchmark", base_label, changed_label, "Change", "Significance")]

    for (bench_name, result) in results:
        # FIXME: use bench.format_sample(), not str()
        table.append((bench_name,
                      # Limit the precision for conciseness in the table.
                      str(round(result.avg_base, 2)),
                      str(round(result.avg_changed, 2)),
                      result.delta_avg,
                      result.t_msg.strip()))

    return table


def FormatOutputAsTable(base_label, changed_label, results):
    """Format a benchmark result in a PEP-fiendly ASCII-art table.

    Args:
        base_label: label to use for the baseline binary.
        changed_label: label to use for the experimental binary.
        results: list of (bench_name, result) 2-tuples, where bench_name is the
            name of the just-run benchmark; and result is a BenchmarkResult
            object.

    Returns:
        A string holding the desired ASCII-art table.
    """
    if isinstance(results[0][1], BenchmarkResult):
        table = _FormatPerfDataForTable(base_label, changed_label, results)
    else:
        raise TypeError("Unknown result type: %r" % type(results[0][1]))

    # Columns with None values are skipped
    skipped_cols = set()
    col_widths = [0] * len(table[0])
    for row in table:
        for col, val in enumerate(row):
            if val is None:
                skipped_cols.add(col)
                continue
            col_widths[col] = max(col_widths[col], len(val))

    outside_line = "+"
    header_sep_line = "+"
    for col, width in enumerate(col_widths):
        if col in skipped_cols:
            continue
        width += 2  # Compensate for the left and right padding spaces.
        outside_line += "-" * width + "+"
        header_sep_line += "=" * width + "+"

    output = [outside_line]
    for row_i, row in enumerate(table):
        output_row = []
        for col_i, val in enumerate(row):
            if col_i in skipped_cols:
                continue
            output_row.append("| " + val.ljust(col_widths[col_i]) + " ")
        output.append("".join(output_row) + "|")
        if row_i > 0:
            output.append(outside_line)

    output.insert(2, "".join(header_sep_line))
    return "\n".join(output)


class RawData(object):
    """Raw data from a benchmark run.

    Attributes:
        runtimes: list of floats, one per iteration.
        mem_usage: list of ints, memory usage in kilobytes.
        inst_output: output from Unladen's --with-instrumentation build. This is
            the empty string if there was no instrumentation output.
    """

    def __init__(self, runtimes, mem_usage, inst_output=""):
        self.runtimes = runtimes
        self.mem_usage = mem_usage
        self.inst_output = inst_output


class BaseBenchmarkResult(object):
    always_display = True

    def __str__(self):
        raise NotImplementedError

    def as_csv(self):
        raise NotImplementedError


class SimpleBenchmarkResult(BaseBenchmarkResult):
    """Object representing result data from a successful benchmark run."""

    def __init__(self, base_time, changed_time, time_delta):
        self.base_time    = base_time
        self.changed_time = changed_time
        self.time_delta   = time_delta

    def __str__(self):
        return ("%(base_time)f -> %(changed_time)f: %(time_delta)s"
                % self.__dict__)

    def as_csv(self):
        # Base, changed
        return ["%f" % self.base_time, "%f" % self.changed_time]


# FIXME: use perf module, remove this class
class BenchmarkResult(BaseBenchmarkResult):
    """An object representing data from a succesful benchmark run."""

    def __init__(self, min_base, min_changed, delta_min, avg_base,
                 avg_changed, delta_avg, t_msg, std_base, std_changed,
                 delta_std, is_significant):
        self.min_base      = min_base
        self.min_changed   = min_changed
        self.delta_min     = delta_min
        # FIXME: rename avg to median
        self.avg_base      = avg_base
        self.avg_changed   = avg_changed
        self.delta_avg     = delta_avg
        self.t_msg         = t_msg
        self.std_base      = std_base
        self.std_changed   = std_changed
        self.delta_std     = delta_std
        self.always_display = is_significant

    def __str__(self):
        values = (self.avg_base, self.std_base,
                  self.avg_changed, self.std_changed)
        # FIXME: don't use perf private function
        # FIXME: reuse perf.Benchmark.format()
        text = "%s +- %s -> %s +- %s" % perf._format_timedeltas(values)
        return ("Median +- Std dev: %s: %s\n%s"
                 % (text, self.delta_avg, self.t_msg))

    def as_csv(self):
        # Min base, min changed
        return ["%f" % self.min_base, "%f" % self.min_changed]


def TimeDelta(old, new):
    if old == 0 or new == 0:
        return "incomparable (one result was zero)"
    if new > old:
        return "%.2fx slower" % (new / old)
    elif new < old:
        return "%.2fx faster" % (old / new)
    else:
        return "no change"


def QuantityDelta(old, new):
    if old == 0 or new == 0:
        return "incomparable (one result was zero)"
    if new > old:
        return "%.4fx larger" % (new / old)
    elif new < old:
        return "%.4fx smaller" % (old / new)
    else:
        return "no change"


def CompareMultipleRuns(base_times, changed_times, options):
    """Compare multiple control vs experiment runs of the same benchmark.

    Args:
        base_times: iterable of float times (control).
        changed_times: iterable of float times (experiment).
        options: optparse.Values instance.

    Returns:
        A BenchmarkResult object, summarizing the difference between the two
        runs; or a SimpleBenchmarkResult object, if there was only one data
        point per run.
    """
    assert len(base_times) == len(changed_times)
    if len(base_times) == 1:
        # With only one data point, we can't do any of the interesting stats
        # below.
        base_time, changed_time = base_times[0], changed_times[0]
        time_delta = TimeDelta(base_time, changed_time)
        return SimpleBenchmarkResult(base_time, changed_time, time_delta)

    base_times = sorted(base_times)
    changed_times = sorted(changed_times)

    min_base, min_changed = base_times[0], changed_times[0]
    avg_base = statistics.median(base_times)
    avg_changed = statistics.median(changed_times)
    std_base = statistics.stdev(base_times, avg_base)
    std_changed = statistics.stdev(changed_times, avg_changed)
    delta_min = TimeDelta(min_base, min_changed)
    delta_avg = TimeDelta(avg_base, avg_changed)
    delta_std = QuantityDelta(std_base, std_changed)

    t_msg = "Not significant\n"
    significant = False
    # Due to inherent measurement imprecisions, variations of less than 1%
    # are automatically considered insignificant. This helps present
    # a clear picture to the user.
    if abs(avg_base - avg_changed) > (avg_base + avg_changed) * 0.01:
        significant, t_score = perf.is_significant(base_times, changed_times)
        if significant:
            t_msg = "Significant (t=%.2f)\n" % t_score

    return BenchmarkResult(min_base, min_changed, delta_min, avg_base,
                           avg_changed, delta_avg, t_msg, std_base,
                           std_changed, delta_std, significant)


# FIXME: remove this function?
def CompareBenchmarkData(base_data, exp_data, options):
    """Compare performance and memory usage.

    Args:
        base_data: RawData instance for the control binary.
        exp_data: RawData instance for the experimental binary.
        options: optparse.Values instance.

    Returns:
        Something that implements a __str__() method:

        - BenchmarkResult: summarizes the difference between the two runs.
        - SimpleBenchmarkResult: if there was only one data point per run.
        - BenchmarkError: if something went wrong.
    """
    return CompareMultipleRuns(base_data.runtimes, exp_data.runtimes, options)


# FIXME: remove this function
def bench_to_data(bench1, bench2):
    name = bench1.get_name()
    name2 = bench2.get_name()
    if name2 != name:
        raise ValueError("not the same benchmark: %s != %s"
                         % (name, name2))

    class Namespace:
        pass
    ns = Namespace()
    ns.benchmark_name = name

    bench1 = RawData(bench1.get_samples(), [], inst_output=None)
    bench2 = RawData(bench2.get_samples(), [], inst_output=None)
    result = CompareBenchmarkData(bench1, bench2, ns)
    return (name, result)


def compare_results(options):
    base_label = os.path.basename(options.baseline_filename)
    changed_label = os.path.basename(options.changed_filename)
    base_suite = perf.BenchmarkSuite.load(options.baseline_filename)
    changed_suite = perf.BenchmarkSuite.load(options.changed_filename)

    # FIXME: work on suites, not results
    results = []
    common = set(base_suite.get_benchmark_names()) & set(changed_suite.get_benchmark_names())
    for name in sorted(common):
        base_bench = base_suite.get_benchmark(name)
        changed_bench = changed_suite.get_benchmark(name)
        name, result = bench_to_data(base_bench, changed_bench)
        results.append((name, result))

    hidden = []
    if not options.verbose:
        shown = []
        for name, result in results:
            if result.always_display:
                shown.append((name, result))
            else:
                hidden.append((name, result))
    else:
        shown = results

    if options.output_style == "normal":
        for name, result in shown:
            print()
            print("###", name, "###")
            print(result)
    elif options.output_style == "table":
        if shown:
            print(FormatOutputAsTable(base_label,
                                      changed_label,
                                      shown))
    else:
        raise ValueError("Invalid output_style: %r" % options.output_style)

    if hidden:
        print()
        print("The following not significant results are hidden, "
              "use -v to show them:")
        print(", ".join(name for (name, result) in hidden) + ".")

    only_base = set(base_suite.get_benchmark_names()) - common
    if only_base:
        print()
        print("Skipped benchmarks only in %s (%s): %s"
              % (len(only_base), base_suite.filename, ', '.join(sorted(only_base))))

    only_changed = set(changed_suite.get_benchmark_names()) - common
    if only_changed:
        print()
        print("Skipped benchmarks only in %s (%s): %s"
              % (len(only_changed), changed_suite.filename, ', '.join(sorted(only_changed))))

    return results


def cmd_compare(options):
    results = compare_results(options)

    if options.csv:
        with open(options.csv, "w") as f:
            writer = csv.writer(f)
            writer.writerow(['Benchmark', 'Base', 'Changed'])
            for name, result in results:
                writer.writerow([name] + result.as_csv())
