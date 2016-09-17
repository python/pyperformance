from __future__ import division, with_statement, print_function, absolute_import

import csv
import os.path

import statistics

import perf


def average(bench):
    return bench.median()


def stdev(bench):
    center = average(bench)
    samples = bench.get_samples()
    return statistics.stdev(samples, center)


def _FormatPerfDataForTable(base_label, changed_label, results):
    table = [("Benchmark", base_label, changed_label, "Change", "Significance")]

    for (bench_name, result) in results:
        format_sample = result.base.format_sample
        avg_base = average(result.base)
        avg_changed = average(result.changed)
        delta_avg = quantity_delta(result.base, result.changed)
        msg = t_msg(result.base, result.changed)[0]
        table.append((bench_name,
                      # Limit the precision for conciseness in the table.
                      format_sample(avg_base),
                      format_sample(avg_changed),
                      delta_avg,
                      msg))

    return table


def FormatOutputAsTable(base_label, changed_label, results):
    table = _FormatPerfDataForTable(base_label, changed_label, results)

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


def t_msg(base, changed):
    if base.get_nsample() < 2 or changed.get_nsample() < 2:
        return ("(benchmark only contains a single sample)", True)

    avg_base = average(base)
    avg_changed = average(changed)

    msg = "Not significant"
    significant = False

    # Due to inherent measurement imprecisions, variations of less than 1%
    # are automatically considered insignificant. This helps present
    # a clear picture to the user.
    if abs(avg_base - avg_changed) > (avg_base + avg_changed) * 0.01:
        base_times = base.get_samples()
        changed_times = changed.get_samples()

        significant, t_score = perf.is_significant(base_times, changed_times)
        if significant:
            msg = "Significant (t=%.2f)" % t_score

    return (msg, significant)


class BenchmarkResult(object):
    """An object representing data from a succesful benchmark run."""

    def __init__(self, base, changed):
        name = base.get_name()
        name2 = changed.get_name()
        if name2 != name:
            raise ValueError("not the same benchmark: %s != %s"
                             % (name, name2))

        if base.get_nsample() != changed.get_nsample():
            raise RuntimeError("base and changed don't have "
                               "the same number of samples")

        self.base = base
        self.changed = changed

    def __str__(self):
        if self.base.get_nsample() > 1:
            base_stdev = stdev(self.base)
            changed_stdev = stdev(self.changed)
            values = (average(self.base), base_stdev,
                      average(self.changed), changed_stdev)
            text = "%s +- %s -> %s +- %s" % self.base.format_samples(values)

            msg = t_msg(self.base, self.changed)[0]
            delta_avg = quantity_delta(self.base, self.changed)
            return ("Median +- Std dev: %s: %s\n%s"
                     % (text, delta_avg, msg))
        else:
            format_sample = self.base.format_sample
            base = average(self.base)
            changed = average(self.changed)
            delta_avg = quantity_delta(self.base, self.changed)
            return ("%s -> %s: %s"
                    % (format_sample(base),
                       format_sample(changed),
                       delta_avg))


def quantity_delta(base, changed):
    old = average(base)
    new = average(changed)
    is_time = (base.get_unit() == 'second')

    if old == 0 or new == 0:
        return "incomparable (one result was zero)"
    if new > old:
        if is_time:
            return "%.2fx slower" % (new / old)
        else:
            return "%.2fx larger" % (new / old)
    elif new < old:
        if is_time:
            return "%.2fx faster" % (old / new)
        else:
            return "%.2fx smaller" % (old / new)
    else:
        return "no change"


def display_suite_metadata(suite, title=None):
    metadata = suite.get_metadata()
    empty = True
    for key, fmt in (
        ('platform', "Report on %s"),
        ('cpu_count', "Number of logical CPUs: %s"),
        ('python_version', "Python version: %s"),
    ):
        if key not in metadata:
            continue

        empty = False
        if title:
            print(title)
            print("=" * len(title))
            print()
            title = None

        text = fmt % metadata[key]
        print(text)

    if not empty:
        print()


def display_benchmark_suite(suite):
    display_suite_metadata(suite)

    for bench in suite.get_benchmarks():
        print("### %s ###" % bench.get_name())
        print(bench)
        print()


def cmd_show(options):
    suite = perf.BenchmarkSuite.load(options.filename)
    display_benchmark_suite(suite)


def compare_results(options):
    base_label = os.path.basename(options.baseline_filename)
    changed_label = os.path.basename(options.changed_filename)

    base_suite = perf.BenchmarkSuite.load(options.baseline_filename)
    changed_suite = perf.BenchmarkSuite.load(options.changed_filename)

    results = []
    common = set(base_suite.get_benchmark_names()) & set(changed_suite.get_benchmark_names())
    for name in sorted(common):
        base_bench = base_suite.get_benchmark(name)
        changed_bench = changed_suite.get_benchmark(name)
        result = BenchmarkResult(base_bench, changed_bench)
        results.append(result)

    hidden = []
    shown = []
    for result in results:
        name = result.base.get_name()

        significant = t_msg(result.base, result.changed)[0]
        if significant or options.verbose:
            shown.append((name, result))
        else:
            hidden.append((name, result))

    display_suite_metadata(base_suite, title=base_label)
    display_suite_metadata(changed_suite, title=changed_label)

    if options.output_style == "normal":
        for name, result in shown:
            print("###", name, "###")
            print(result)
            print()

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


def format_csv(value):
    abs_value = abs(value)
    # keep at least 3 significant digits, but also try to avoid too many zeros
    if abs_value >= 1.0:
        return "%.2f" % value
    elif abs_value >= 1e-3:
        return "%.5f" % value
    elif abs_value >= 1e-6:
        return "%.8f" % value
    else:
        return "%.11f" % value


def write_csv(results, filename):
    with open(filename, "w") as f:
        writer = csv.writer(f)
        writer.writerow(['Benchmark', 'Base', 'Changed'])
        for result in results:
            name = result.base.get_name()
            base = average(result.base)
            changed = average(result.changed)
            row = [name, format_csv(base), format_csv(changed)]
            writer.writerow(row)


def cmd_compare(options):
    results = compare_results(options)

    if options.csv:
        write_csv(results, options.csv)
