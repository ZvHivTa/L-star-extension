"""Regression tests for the query-cache-backed virtual observation table."""

import tempfile
import unittest
from pathlib import Path

from learner import Learner
from oracle import Oracle
from regex_converter import regex_to_minimal_dfa


class VirtualObservationTableTests(unittest.TestCase):
    def test_learning_keeps_all_virtual_cells_in_the_mq_cache(self):
        alphabet = {"a", "b"}
        target = regex_to_minimal_dfa("(aa|bbb)*", alphabet)

        for strategy in ("post_check", "promote_to_p"):
            with self.subTest(strategy=strategy):
                learner = Learner(
                    Oracle(target),
                    alphabet,
                    monoid_strategy=strategy,
                    verbose=False,
                )
                hypothesis = learner.learn()

                self.assertFalse(hasattr(learner, "table"))
                language_difference = target.symmetric_difference(hypothesis)
                self.assertTrue(language_difference.isempty())

                rows = learner.needed_rows()
                expected_words = {
                    p + row + suffix
                    for row in rows
                    for p in learner.P
                    for suffix in learner.S
                }
                self.assertLessEqual(expected_words, set(learner.query_cache))
                self.assertEqual(
                    learner.observation_cell_count(),
                    len(rows) * len(learner.P) * len(learner.S),
                )

    def test_exporting_the_final_virtual_table_does_not_add_mqs(self):
        alphabet = {"a", "b"}
        target = regex_to_minimal_dfa("(ab|ba)*", alphabet)
        learner = Learner(
            Oracle(target),
            alphabet,
            monoid_strategy="post_check",
            verbose=False,
        )
        learner.learn()
        mq_before = learner.mq_count
        cache_before = learner.query_cache.copy()

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "observation_table.txt"
            learner.display_observation_table(output)
            rendered = output.read_text(encoding="utf-8")

        self.assertEqual(learner.mq_count, mq_before)
        self.assertEqual(learner.query_cache, cache_before)
        self.assertNotIn("?", rendered)


if __name__ == "__main__":
    unittest.main()
