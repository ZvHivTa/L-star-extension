import unittest

from benchmark import compute_transition_monoid_data
from learner import Learner
from oracle import Oracle
from regex_converter import regex_to_minimal_dfa


ALPHABET = {"a", "b"}


def extend_transformation(transformation, char, base_trans):
    char_transformation = base_trans[char]
    return tuple(char_transformation[index] for index in transformation)


def word_transformation(word, vector_length, base_trans):
    transformation = tuple(range(vector_length))
    for char in word:
        transformation = extend_transformation(transformation, char, base_trans)
    return transformation


class PromoteToPTests(unittest.TestCase):
    CASES = (
        "()",
        "(ab|ba)*",
        "b*(ab*ab*)*",
        "(aa|bbb)*",
        "()|(a|b)|(a|b)(a|b)|(a|b)(a|b)(a|b)b*",
        "(a|bb)*ab(a|b)*baa",
    )

    def test_promote_to_p_learns_right_cayley_graph_without_monoid_check(self):
        for regex in self.CASES:
            with self.subTest(regex=regex):
                target_dfa = regex_to_minimal_dfa(regex, ALPHABET)
                learner = Learner(
                    Oracle(target_dfa),
                    ALPHABET,
                    monoid_strategy="promote_to_p",
                    verbose=False,
                )
                hypothesis = learner.learn()

                monoid_elements, base_trans, _, _ = compute_transition_monoid_data(
                    target_dfa,
                    ALPHABET,
                )
                vector_length = len(next(iter(monoid_elements)))
                state_transformations = {
                    state: word_transformation(
                        learner.state_to_rep[state],
                        vector_length,
                        base_trans,
                    )
                    for state in hypothesis.states
                }

                language_difference = target_dfa.symmetric_difference(hypothesis)
                self.assertTrue(language_difference.isempty())
                self.assertEqual(set(state_transformations.values()), monoid_elements)
                self.assertEqual(len(state_transformations), len(monoid_elements))
                self.assertTrue(learner.I <= learner.P)
                self.assertEqual(learner.monoid_check_count, 0)
                self.assertEqual(learner.monoid_probe_time, 0.0)

                for state, transitions in hypothesis.transitions.items():
                    for char, next_state in transitions.items():
                        expected = extend_transformation(
                            state_transformations[state],
                            char,
                            base_trans,
                        )
                        self.assertEqual(state_transformations[next_state], expected)

                for state, representative in learner.state_to_rep.items():
                    self.assertEqual(
                        state in hypothesis.final_states,
                        target_dfa.accepts_input(representative),
                    )

    def test_known_failure_case_uses_right_consistency(self):
        target_dfa = regex_to_minimal_dfa("(aa|bbb)*", ALPHABET)
        learner = Learner(
            Oracle(target_dfa),
            ALPHABET,
            monoid_strategy="promote_to_p",
            verbose=False,
        )

        learner.learn()

        self.assertGreater(learner.right_consistency_refinements, 0)
        self.assertEqual(learner.monoid_check_count, 0)


if __name__ == "__main__":
    unittest.main()
