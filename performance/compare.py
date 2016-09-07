from __future__ import division, with_statement, print_function, absolute_import

import csv
import os.path

import statistics

import perf


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


class BaseBenchmarkResult(object):
    always_display = True

    def __str__(self):
        raise NotImplementedError

    def as_csv(self):
        raise NotImplementedError


class SimpleBenchmarkResult(BaseBenchmarkResult):
    def __init__(self, base, changed):
        self.base = base

        base_times = base.get_samples()
        changed_times = changed.get_samples()

        self.base_time = base_times[0]
        self.changed_time = changed_times[0]

    def __str__(self):
        # FIXME: don't use private function
        format_sample = self.base._format_sample
        time_delta = TimeDelta(self.base_time, self.changed_time)
        return ("%s -> %s: %s"
                % (format_sample(self.base_time),
                   format_sample(self.changed_time),
                   time_delta))

    def as_csv(self):
        # Base, changed
        return ["%f" % self.base_time, "%f" % self.changed_time]


# FIXME: use perf module, remove this class
class BenchmarkResult(BaseBenchmarkResult):
    """An object representing data from a succesful benchmark run."""

    def __init__(self, base, changed):
        # Why do we need to sort?
        base_times = sorted(base.get_samples())
        changed_times = sorted(changed.get_samples())

        self.base = base
        self.changed = changed
        self.min_base      = min(base_times)
        self.min_changed   = max(base_times)
        self.delta_min     = TimeDelta(self.min_base, self.min_changed)
        # FIXME: rename avg to median
        self.avg_base      = statistics.median(base_times)
        self.avg_changed   = statistics.median(changed_times)
        self.delta_avg     = TimeDelta(self.avg_base, self.avg_changed)
        self.std_base      = statistics.stdev(base_times, self.avg_base)
        self.std_changed   = statistics.stdev(changed_times, self.avg_changed)
        self.delta_std     = QuantityDelta(self.std_base, self.std_changed)

        t_msg = "Not significant\n"
        significant = False
        # Due to inherent measurement imprecisions, variations of less than 1%
        # are automatically considered insignificant. This helps present
        # a clear picture to the user.
        if abs(self.avg_base - self.avg_changed) > (self.avg_base + self.avg_changed) * 0.01:
            significant, t_score = perf.is_significant(base_times, changed_times)
            if significant:
                t_msg = "Significant (t=%.2f)\n" % t_score

        self.t_msg         = t_msg
        self.always_display = significant

    def __str__(self):
        base_stdev = statistics.stdev(self.base.get_samples())
        changed_stdev = statistics.stdev(self.changed.get_samples())
        values = (self.base.median(), base_stdev,
                  self.changed.median(), changed_stdev )
        # FIXME: don't use perf private method
        text = "%s +- %s -> %s +- %s" % self.base._format_samples(values)
        return ("Median +- Std dev: %s: %s\n%s"
                 % (text, self.delta_avg, self.t_msg))

    def as_csv(self):
        # Min base, min changed
        base = self.base.median()
        changed = self.changed.median()
        return ["%f" % base, "%f" % changed]


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


# FIXME: remove this function
def bench_to_data(base, changed):
    name = base.get_name()
    name2 = changed.get_name()
    if name2 != name:
        raise ValueError("not the same benchmark: %s != %s"
                         % (name, name2))

    if base.get_nsample() != changed.get_nsample():
        raise RuntimeError("base and changed don't have "
                           "the same number of samples")

    if base.get_nsample() == 1:
        result = SimpleBenchmarkResult(base, changed)
    else:
        result = BenchmarkResult(base, changed)

    return result


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
        result = bench_to_data(base_bench, changed_bench)
        results.append(result)

    hidden = []
    shown = []
    for result in results:
        name = result.base.get_name()
        if result.always_display or options.verbose:
            shown.append((name, result))
        else:
            hidden.append((name, result))

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
            for result in results:
                name = result.base.get_name()
                writer.writerow([name] + result.as_csv())
