"""Regression tests for EQ scheduling and endpoint-free RS search."""

import math
import unittest
from unittest.mock import patch

from automata.fa.dfa import DFA
from automata.fa.nfa import NFA

from classic_lstar_learner import ClassicLearner
from classic_lstar_oracle import ClassicOracle
from learner import Learner


def target_for(regex):
    return DFA.from_nfa(NFA.from_regex(regex, input_symbols={"a", "b"})).minify()


class RecordingOracle(ClassicOracle):
    def __init__(self, target):
        super().__init__(target)
        self.pending_rs = None
        self.rs_records = []
        self.hypotheses = []

    def equivalence_query(self, hypothesis):
        self.hypotheses.append(hypothesis)
        word = super().equivalence_query(hypothesis)
        if word is not None:
            self.pending_rs = {
                "word": word,
                "model_label": hypothesis.accepts_input(word),
                "calls": [],
                "mq_before": self.mq_count,
            }
        return word

    def membership_query(self, word):
        if self.pending_rs is not None:
            self.pending_rs["calls"].append(word)
        return super().membership_query(word)

    def finish_rs(self):
        if self.pending_rs is not None:
            self.pending_rs["new_mqs"] = self.mq_count - self.pending_rs["mq_before"]
            self.rs_records.append(self.pending_rs)
            self.pending_rs = None


class TracedLearner(Learner):
    def __init__(self, *args, **kwargs):
        self.built_hypotheses = []
        self.monoid_results = []
        super().__init__(*args, **kwargs)

    def build_hypothesis(self):
        hypothesis = super().build_hypothesis()
        self.built_hypotheses.append(hypothesis)
        return hypothesis

    def handle_counterexample(self, word, hypothesis):
        try:
            return super().handle_counterexample(word, hypothesis)
        finally:
            self.teacher.finish_rs()

    def run_monoid_phase(self):
        result = super().run_monoid_phase()
        self.monoid_results.append(result)
        return result


class TracedClassicLearner(ClassicLearner):
    def invalidate_cache(self, rows=False, i=False, s=False):
        super().invalidate_cache(rows=rows, i=i, s=s)
        if s:
            self.oracle.finish_rs()


class EqSchedulingTests(unittest.TestCase):
    def test_p_refinement_submits_every_new_hypothesis_to_eq(self):
        target = target_for("(aa|bbb)*")
        oracle = RecordingOracle(target)
        learner = TracedLearner(oracle, {"a", "b"}, verbose=False)
        hypothesis = learner.learn()

        self.assertIn(False, learner.monoid_results)
        self.assertEqual(learner.skipped_eq_count, 0)
        self.assertEqual(learner.eq_count, len(learner.built_hypotheses))
        self.assertEqual(
            [id(h) for h in learner.built_hypotheses],
            [id(h) for h in oracle.hypotheses],
        )
        difference = target.symmetric_difference(hypothesis)
        self.assertTrue(difference.isempty())

    def test_counterexample_after_a_previous_eq_pass_is_processed(self):
        learner = Learner(None, {"a", "b"}, verbose=False)
        hypotheses = [object(), object(), object()]
        events = []

        def eq(hypothesis):
            index = hypotheses.index(hypothesis)
            events.append(("eq", index))
            return index == 1

        def monoid():
            events.append(("monoid",))
            return events.count(("monoid",)) == 2

        with patch.object(learner, "run_table_phase", side_effect=hypotheses), \
             patch.object(learner, "run_equivalence_phase", side_effect=eq), \
             patch.object(learner, "run_monoid_phase", side_effect=monoid):
            self.assertIs(learner.learn(), hypotheses[-1])

        self.assertEqual(events, [
            ("eq", 0), ("monoid",), ("eq", 1), ("eq", 2), ("monoid",),
        ])


class RsQueryTests(unittest.TestCase):
    def test_rs_queries_only_midpoints_and_respects_the_mq_bound(self):
        regexes = ["a" * length for length in (2, 3, 4, 7, 8, 9, 16, 17)]
        regexes += ["(aa|bbb)*", "(ab|ba)*", "(a|b)*aab"]
        model_labels = set()
        for regex in regexes:
            target = target_for(regex)
            for strategy in ("baseline", "post_check", "promote_to_p"):
                with self.subTest(regex=regex, strategy=strategy):
                    oracle = RecordingOracle(target)
                    if strategy == "baseline":
                        learner = TracedClassicLearner(oracle, {"a", "b"})
                    else:
                        learner = TracedLearner(
                            oracle, {"a", "b"}, monoid_strategy=strategy,
                            verbose=False,
                        )
                    hypothesis = learner.learn()
                    difference = target.symmetric_difference(hypothesis)
                    self.assertTrue(difference.isempty())
                    for record in oracle.rs_records:
                        word = record["word"]
                        model_labels.add(record["model_label"])
                        bound = math.ceil(math.log2(len(word)))
                        self.assertNotIn(word, record["calls"])
                        self.assertLessEqual(len(record["calls"]), bound)
                        self.assertLessEqual(record["new_mqs"], bound)
        self.assertEqual(model_labels, {False, True})

    def test_length_one_counterexample_needs_no_mq(self):
        target = target_for("a")
        oracle = RecordingOracle(target)
        learner = Learner(oracle, {"a", "b"}, verbose=False)
        hypothesis = DFA(
            states={"q0"}, input_symbols={"a", "b"},
            transitions={"q0": {"a": "q0", "b": "q0"}},
            initial_state="q0", final_states=set(),
        )
        learner.state_to_rep = {hypothesis.initial_state: ""}
        for state in hypothesis.states - {hypothesis.initial_state}:
            learner.state_to_rep[state] = "b"
        reps = learner.trace_hypothesis_representatives("a", hypothesis)
        with patch.object(oracle, "membership_query", wraps=oracle.membership_query) as mq:
            self.assertEqual(learner.find_breakpoint("a", reps, hypothesis), (0, 1))
            mq.assert_not_called()


if __name__ == "__main__":
    unittest.main()
