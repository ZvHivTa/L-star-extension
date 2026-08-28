"""Regression tests for benchmark timing summaries."""

import unittest

from experiments.compare_language_categories import summarize_strategy
from experiments.reports.generate_main_decision_report import strategy_at_cost


class BenchmarkStatisticsTests(unittest.TestCase):
    def test_local_median_is_computed_from_paired_run_samples(self):
        totals = [10.0, 20.0, 100.0]
        eq_times = [0.0, 15.0, 90.0]
        local_times = [10.0, 5.0, 10.0]
        metrics = [
            {
                "mq": 7,
                "eq": 2,
                "eq_ms": eq_ms,
                "local_ms": local_ms,
                "monoid_check_ms": 0.0,
            }
            for eq_ms, local_ms in zip(eq_times, local_times)
        ]

        result = summarize_strategy(totals, metrics)

        self.assertEqual(result["median_ms"], 20.0)
        self.assertEqual(result["eq_ms"], 15.0)
        self.assertEqual(result["median_local_ms"], 10.0)
        self.assertNotEqual(
            result["median_local_ms"],
            result["median_ms"] - result["eq_ms"],
        )
        self.assertEqual(result["samples"]["local_ms"], local_times)

    def test_decision_uses_the_bootstrap_interval(self):
        row = {
            "saved_eq": 2,
            "delta_local_ci_low_ms": 18.0,
            "delta_local_ci_high_ms": 19.0,
        }
        self.assertEqual(strategy_at_cost(row, 10), "promote")

        row["delta_local_ci_low_ms"] = 21.0
        row["delta_local_ci_high_ms"] = 22.0
        self.assertEqual(strategy_at_cost(row, 10), "post")

        row["delta_local_ci_low_ms"] = 19.0
        row["delta_local_ci_high_ms"] = 21.0
        self.assertEqual(strategy_at_cost(row, 10), "inconclusive")


if __name__ == "__main__":
    unittest.main()
