import unittest

from pyperformance.run import order_benchmarks


class OrderBenchmarksTests(unittest.TestCase):
    def setUp(self):
        self.benchmarks = ["b", "a", "c"]

    def test_default_is_sorted(self):
        ordered = order_benchmarks(self.benchmarks)
        self.assertEqual(ordered, ["a", "b", "c"])

    def test_shuffle_seed_implies_shuffle(self):
        ordered = order_benchmarks(self.benchmarks, shuffle_seed=123)
        self.assertEqual(ordered, ["c", "a", "b"])

    def test_shuffle_flag_without_seed_changes_order(self):
        sorted_expected = sorted(self.benchmarks)

        shuffled_orders = []
        for seed in range(10):
            ordered = order_benchmarks(self.benchmarks, shuffle=True, shuffle_seed=seed)
            self.assertCountEqual(ordered, self.benchmarks)
            shuffled_orders.append(tuple(ordered))

        self.assertTrue(
            any(order != tuple(sorted_expected) for order in shuffled_orders),
            "Shuffle should change order for at least one seed in range(10)",
        )


if __name__ == "__main__":
    unittest.main()
