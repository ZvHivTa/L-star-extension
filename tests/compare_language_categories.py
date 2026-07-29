"""Compare learner strategies on language-category benchmark suites."""

from __future__ import annotations

import argparse
import gc
import json
import statistics
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Hashable

from automata.fa.dfa import DFA
from automata.fa.gnfa import GNFA
from automata.fa.nfa import NFA

from learner import Learner
from oracle import Oracle


STRATEGIES = ("post_check", "promote_to_p")
DEFAULT_REPEATS = {
    "commutative": 15,
    "star_free": 15,
    "alphabet_3": 7,
    "complex_commutative": 5,
}


@dataclass(frozen=True)
class LanguageCase:
    """Describe one reproducible target language."""

    name: str
    description: str
    alphabet: frozenset[str]
    build: Callable[[], DFA]
    regex: str | None = None


def state_dfa(
    alphabet: set[str],
    initial: Hashable,
    transition: Callable[[Hashable, str], Hashable],
    accepting: Callable[[Hashable], bool],
) -> DFA:
    """Build and minimize the reachable complete DFA induced by callbacks."""
    states = {initial}
    queue = deque([initial])
    transitions = {}
    while queue:
        state = queue.popleft()
        transitions[state] = {}
        for symbol in sorted(alphabet):
            next_state = transition(state, symbol)
            transitions[state][symbol] = next_state
            if next_state not in states:
                states.add(next_state)
                queue.append(next_state)

    return DFA(
        states=states,
        input_symbols=alphabet,
        transitions=transitions,
        initial_state=initial,
        final_states={state for state in states if accepting(state)},
    ).minify()


def counter_mod(
    alphabet: set[str],
    moduli: dict[str, int],
    accepting: Callable[[tuple[int, ...]], bool],
) -> DFA:
    """Build a DFA whose state records selected letter counts modulo integers."""
    symbols = tuple(sorted(moduli))
    initial = tuple(0 for _ in symbols)

    def transition(state, char):
        return tuple(
            (value + (char == symbol)) % moduli[symbol]
            for value, symbol in zip(state, symbols)
        )

    return state_dfa(alphabet, initial, transition, accepting)


def threshold_counter(
    alphabet: set[str],
    limits: dict[str, int],
    accepting: Callable[[tuple[int, ...]], bool],
) -> DFA:
    """Build a DFA that tracks capped occurrence counts."""
    symbols = tuple(sorted(limits))
    initial = tuple(0 for _ in symbols)

    def transition(state, char):
        return tuple(
            min(value + (char == symbol), limits[symbol])
            for value, symbol in zip(state, symbols)
        )

    return state_dfa(alphabet, initial, transition, accepting)


def substring_dfa(alphabet: set[str], pattern: str, accept_when_seen=True) -> DFA:
    """Build a KMP-style DFA for containing or ending with a fixed pattern."""
    def next_prefix(length, char):
        candidate = pattern[:length] + char
        return max(
            size
            for size in range(len(pattern) + 1)
            if candidate.endswith(pattern[:size])
        )

    if accept_when_seen:
        seen = len(pattern)

        def transition(state, char):
            return seen if state == seen else next_prefix(state, char)

        accepting = lambda state: state == seen
    else:
        transition = next_prefix
        accepting = lambda state: state == len(pattern)

    return state_dfa(alphabet, 0, transition, accepting)


def exact_word_dfa(alphabet: set[str], word: str) -> DFA:
    """Build a DFA accepting exactly one word."""
    dead = len(word) + 1

    def transition(state, char):
        if state == dead:
            return dead
        if state < len(word) and char == word[state]:
            return state + 1
        return dead

    return state_dfa(alphabet, 0, transition, lambda state: state == len(word))


def contains_all(alphabet: set[str]) -> DFA:
    """Build a DFA accepting words that contain every alphabet symbol."""
    return state_dfa(
        alphabet,
        frozenset(),
        lambda state, char: state | {char},
        lambda state: state == alphabet,
    )


def begins_with(alphabet: set[str], symbol: str) -> DFA:
    """Build a DFA testing the first symbol."""
    return state_dfa(
        alphabet,
        "start",
        lambda state, char: ("yes" if char == symbol else "no")
        if state == "start"
        else state,
        lambda state: state == "yes",
    )


def ends_with(alphabet: set[str], symbol: str) -> DFA:
    """Build a DFA testing the last symbol."""
    return state_dfa(
        alphabet,
        False,
        lambda _state, char: char == symbol,
        bool,
    )


def avoids_double_letter(alphabet: set[str]) -> DFA:
    """Build a DFA rejecting any adjacent equal symbols."""
    dead = "#dead"

    def transition(state, char):
        if state == dead or state == char:
            return dead
        return char

    return state_dfa(alphabet, "", transition, lambda state: state != dead)


def ordered_blocks(alphabet: set[str], order: str) -> DFA:
    """Build the language a*b*c*... for the supplied symbol order."""
    positions = {symbol: index for index, symbol in enumerate(order)}
    dead = len(order)

    def transition(state, char):
        if state == dead or positions[char] < state:
            return dead
        return positions[char]

    return state_dfa(alphabet, 0, transition, lambda state: state != dead)


def permutation_dfa(alphabet: set[str], transformations: dict[str, tuple[int, ...]]) -> DFA:
    """Build a pointed transformation action with final state zero."""
    return state_dfa(
        alphabet,
        0,
        lambda state, char: transformations[char][state],
        lambda state: state == 0,
    )


def other_symbols_star(alphabet: set[str], symbol: str) -> str:
    """Return a basic regex for any word not containing the selected symbol."""
    others = sorted(alphabet - {symbol})
    atom = others[0] if len(others) == 1 else f"({'|'.join(others)})"
    return atom + "*"


def count_mod_zero_regex(alphabet: set[str], symbol: str, modulus: int) -> str:
    """Write a zero-residue counter with every repetition explicitly expanded."""
    gap = other_symbols_star(alphabet, symbol)
    cycle = (symbol + gap) * modulus
    return f"{gap}({cycle})*"


def at_least_regex(alphabet: set[str], symbol: str, threshold: int) -> str:
    """Write an at-least threshold language without counted repetition syntax."""
    gap = other_symbols_star(alphabet, symbol)
    tail = f"({'|'.join(sorted(alphabet))})*"
    return gap + (symbol + gap) * threshold + tail


def regex_union(*expressions: str) -> str:
    """Join complete language expressions using explicit alternation."""
    return "|".join(f"({expression})" for expression in expressions)


def threshold_or_mod_dfa(
    alphabet: set[str],
    threshold_symbol: str,
    threshold: int,
    mod_symbol: str,
    modulus: int,
) -> DFA:
    """Accept after a threshold or on a selected modular residue."""
    initial = (0, 0)

    def transition(state, char):
        capped, residue = state
        return (
            min(capped + (char == threshold_symbol), threshold),
            (residue + (char == mod_symbol)) % modulus,
        )

    return state_dfa(
        alphabet,
        initial,
        transition,
        lambda state: state[0] == threshold or state[1] == 0,
    )


AB = {"a", "b"}
ABC = {"a", "b", "c"}


COMMUTATIVE_CASES = (
    LanguageCase("contains_a", "contains at least one a", frozenset(AB),
                 lambda: threshold_counter(AB, {"a": 1}, lambda q: q[0] == 1)),
    LanguageCase("contains_a_and_b", "contains both a and b", frozenset(AB),
                 lambda: threshold_counter(AB, {"a": 1, "b": 1}, lambda q: q == (1, 1))),
    LanguageCase("even_a", "the number of a is even", frozenset(AB),
                 lambda: counter_mod(AB, {"a": 2}, lambda q: q[0] == 0)),
    LanguageCase("odd_a", "the number of a is odd", frozenset(AB),
                 lambda: counter_mod(AB, {"a": 2}, lambda q: q[0] == 1)),
    LanguageCase("even_b", "the number of b is even", frozenset(AB),
                 lambda: counter_mod(AB, {"b": 2}, lambda q: q[0] == 0)),
    LanguageCase("a_mod_3_zero", "#a is 0 modulo 3", frozenset(AB),
                 lambda: counter_mod(AB, {"a": 3}, lambda q: q[0] == 0)),
    LanguageCase("b_mod_4_zero", "#b is 0 modulo 4", frozenset(AB),
                 lambda: counter_mod(AB, {"b": 4}, lambda q: q[0] == 0)),
    LanguageCase("same_parity_a_b", "#a and #b have the same parity", frozenset(AB),
                 lambda: counter_mod(AB, {"a": 2, "b": 2}, lambda q: q[0] == q[1])),
    LanguageCase("both_counts_even", "both #a and #b are even", frozenset(AB),
                 lambda: counter_mod(AB, {"a": 2, "b": 2}, lambda q: q == (0, 0)),
                 "(aa|bb|(ab|ba)(aa|bb)*(ab|ba))*"),
    LanguageCase("at_least_two_a", "contains at least two a symbols", frozenset(AB),
                 lambda: threshold_counter(AB, {"a": 2}, lambda q: q[0] == 2)),
    LanguageCase("at_most_two_b", "contains at most two b symbols", frozenset(AB),
                 lambda: threshold_counter(AB, {"b": 3}, lambda q: q[0] < 3),
                 "a*|a*ba*|a*ba*ba*"),
    LanguageCase("a_mod_3_b_mod_2_zero", "#a mod 3 = 0 and #b mod 2 = 0", frozenset(AB),
                 lambda: counter_mod(AB, {"a": 3, "b": 2}, lambda q: q == (0, 0))),
)


def star_free_cases() -> tuple[LanguageCase, ...]:
    """Return twelve aperiodic target languages over two letters."""
    return (
        LanguageCase("contains_a", "contains at least one a", frozenset(AB),
                     lambda: threshold_counter(AB, {"a": 1}, lambda q: q[0] == 1)),
        LanguageCase("contains_a_and_b", "contains both a and b", frozenset(AB),
                     lambda: threshold_counter(AB, {"a": 1, "b": 1}, lambda q: q == (1, 1))),
        LanguageCase("starts_with_a", "starts with a", frozenset(AB),
                     lambda: begins_with(AB, "a")),
        LanguageCase("ends_with_b", "ends with b", frozenset(AB),
                     lambda: ends_with(AB, "b")),
        LanguageCase("contains_ab", "contains ab as a substring", frozenset(AB),
                     lambda: substring_dfa(AB, "ab")),
        LanguageCase("avoids_aa", "does not contain aa", frozenset(AB),
                     lambda: state_dfa(
                         AB, 0,
                         lambda q, c: 2 if q == 2 or (q == 1 and c == "a") else int(c == "a"),
                         lambda q: q != 2,
                     ),
                     "(b|ab)*(a|())"),
        LanguageCase("exactly_one_a", "contains exactly one a", frozenset(AB),
                     lambda: threshold_counter(AB, {"a": 2}, lambda q: q[0] == 1)),
        LanguageCase("at_least_two_a", "contains at least two a symbols", frozenset(AB),
                     lambda: threshold_counter(AB, {"a": 2}, lambda q: q[0] == 2)),
        LanguageCase("at_most_two_b", "contains at most two b symbols", frozenset(AB),
                     lambda: threshold_counter(AB, {"b": 3}, lambda q: q[0] < 3),
                     "a*|a*ba*|a*ba*ba*"),
        LanguageCase("a_before_b", "contains a before a later b", frozenset(AB),
                     lambda: state_dfa(
                         AB, 0,
                         lambda q, c: 2 if q == 2 or (q == 1 and c == "b")
                         else max(q, int(c == "a")),
                         lambda q: q == 2,
                     )),
        LanguageCase("ends_with_aba", "ends with aba", frozenset(AB),
                     lambda: substring_dfa(AB, "aba", accept_when_seen=False)),
        LanguageCase("length_at_most_4", "has length at most four", frozenset(AB),
                     lambda: threshold_counter(AB, {"a": 5, "b": 5},
                                               lambda q: sum(q) <= 4),
                     "()|(a|b)|(a|b)(a|b)|(a|b)(a|b)(a|b)|"
                     "(a|b)(a|b)(a|b)(a|b)"),
    )


def alphabet_three_cases() -> tuple[LanguageCase, ...]:
    """Return twenty varied targets over exactly three symbols."""
    return (
        LanguageCase("all_words", "all words over {a,b,c}", frozenset(ABC),
                     lambda: state_dfa(ABC, 0, lambda q, c: q, lambda q: True)),
        LanguageCase("contains_all_symbols", "contains a, b, and c", frozenset(ABC),
                     lambda: contains_all(ABC)),
        LanguageCase("exactly_one_each", "contains exactly one of each symbol", frozenset(ABC),
                     lambda: threshold_counter(ABC, {"a": 2, "b": 2, "c": 2},
                                               lambda q: q == (1, 1, 1))),
        LanguageCase("even_a", "#a is even", frozenset(ABC),
                     lambda: counter_mod(ABC, {"a": 2}, lambda q: q[0] == 0)),
        LanguageCase("a_mod_3_zero", "#a is 0 modulo 3", frozenset(ABC),
                     lambda: counter_mod(ABC, {"a": 3}, lambda q: q[0] == 0)),
        LanguageCase("all_counts_even", "#a, #b, and #c are even", frozenset(ABC),
                     lambda: counter_mod(ABC, {"a": 2, "b": 2, "c": 2},
                                         lambda q: q == (0, 0, 0))),
        LanguageCase("mixed_mod_3_2_2", "#a mod 3, #b mod 2, #c mod 2 are zero",
                     frozenset(ABC),
                     lambda: counter_mod(ABC, {"a": 3, "b": 2, "c": 2},
                                         lambda q: q == (0, 0, 0))),
        LanguageCase("length_mod_8", "word length is 0 modulo 8", frozenset(ABC),
                     lambda: state_dfa(ABC, 0, lambda q, c: (q + 1) % 8,
                                       lambda q: q == 0)),
        LanguageCase("a_mod_4_b_mod_3", "#a mod 4 = 0 and #b mod 3 = 0", frozenset(ABC),
                     lambda: counter_mod(ABC, {"a": 4, "b": 3}, lambda q: q == (0, 0))),
        LanguageCase("ends_with_abc", "ends with abc", frozenset(ABC),
                     lambda: substring_dfa(ABC, "abc", accept_when_seen=False)),
        LanguageCase("ends_with_abca", "ends with abca", frozenset(ABC),
                     lambda: substring_dfa(ABC, "abca", accept_when_seen=False)),
        LanguageCase("contains_abc", "contains abc as a substring", frozenset(ABC),
                     lambda: substring_dfa(ABC, "abc")),
        LanguageCase("contains_abca", "contains abca as a substring", frozenset(ABC),
                     lambda: substring_dfa(ABC, "abca")),
        LanguageCase("avoids_equal_neighbors", "has no equal adjacent symbols", frozenset(ABC),
                     lambda: avoids_double_letter(ABC)),
        LanguageCase("ordered_blocks", "belongs to a*b*c*", frozenset(ABC),
                     lambda: ordered_blocks(ABC, "abc"),
                     "a*b*c*"),
        LanguageCase("exact_abcabc", "is exactly abcabc", frozenset(ABC),
                     lambda: exact_word_dfa(ABC, "abcabc")),
        LanguageCase("at_least_two_each", "contains at least two of every symbol",
                     frozenset(ABC),
                     lambda: threshold_counter(ABC, {"a": 2, "b": 2, "c": 2},
                                               lambda q: q == (2, 2, 2))),
        LanguageCase("s4_permutation_action", "S4 action generated by three permutations",
                     frozenset(ABC),
                     lambda: permutation_dfa(
                         ABC,
                         {"a": (1, 2, 3, 0), "b": (1, 0, 2, 3), "c": (0, 2, 1, 3)},
                     )),
        LanguageCase("dihedral_action_12", "12-state dihedral group action",
                     frozenset(ABC),
                     lambda: permutation_dfa(
                         ABC,
                         {
                             "a": tuple((i + 1) % 12 for i in range(12)),
                             "b": tuple((-i) % 12 for i in range(12)),
                             "c": tuple((i + 3) % 12 for i in range(12)),
                         },
                     )),
        LanguageCase("full_transformation_monoid_4",
                     "four-state action generating the full transformation monoid",
                     frozenset(ABC),
                     lambda: permutation_dfa(
                         ABC,
                         {"a": (1, 2, 3, 0), "b": (1, 0, 2, 3), "c": (0, 1, 2, 2)},
                     )),
    )


def complex_commutative_cases() -> tuple[LanguageCase, ...]:
    """Return larger commutative targets with explicit basic regular expressions."""
    cases = []
    for a_modulus, b_modulus in ((5, 7), (6, 7), (7, 8), (8, 9), (9, 11)):
        cases.append(
            LanguageCase(
                f"a_mod_{a_modulus}_or_b_mod_{b_modulus}",
                f"#a is 0 mod {a_modulus} or #b is 0 mod {b_modulus}",
                frozenset(AB),
                lambda m=a_modulus, n=b_modulus: counter_mod(
                    AB,
                    {"a": m, "b": n},
                    lambda state: state[0] == 0 or state[1] == 0,
                ),
                regex_union(
                    count_mod_zero_regex(AB, "a", a_modulus),
                    count_mod_zero_regex(AB, "b", b_modulus),
                ),
            )
        )

    for threshold, modulus in ((6, 7), (8, 9)):
        cases.append(
            LanguageCase(
                f"at_least_{threshold}_a_or_b_mod_{modulus}",
                f"#a is at least {threshold} or #b is 0 mod {modulus}",
                frozenset(AB),
                lambda k=threshold, n=modulus: threshold_or_mod_dfa(
                    AB, "a", k, "b", n
                ),
                regex_union(
                    at_least_regex(AB, "a", threshold),
                    count_mod_zero_regex(AB, "b", modulus),
                ),
            )
        )

    for a_threshold, b_threshold in ((6, 7), (8, 9)):
        cases.append(
            LanguageCase(
                f"at_least_{a_threshold}_a_or_{b_threshold}_b",
                f"#a is at least {a_threshold} or #b is at least {b_threshold}",
                frozenset(AB),
                lambda m=a_threshold, n=b_threshold: threshold_counter(
                    AB,
                    {"a": m, "b": n},
                    lambda state: state[0] == m or state[1] == n,
                ),
                regex_union(
                    at_least_regex(AB, "a", a_threshold),
                    at_least_regex(AB, "b", b_threshold),
                ),
            )
        )

    cases.extend(
        (
            LanguageCase(
                "a_or_b_or_c_mod_3_4_5",
                "#a is 0 mod 3 or #b is 0 mod 4 or #c is 0 mod 5",
                frozenset(ABC),
                lambda: counter_mod(
                    ABC,
                    {"a": 3, "b": 4, "c": 5},
                    lambda state: 0 in state,
                ),
                regex_union(
                    count_mod_zero_regex(ABC, "a", 3),
                    count_mod_zero_regex(ABC, "b", 4),
                    count_mod_zero_regex(ABC, "c", 5),
                ),
            ),
            LanguageCase(
                "a_mod_31_zero",
                "#a is 0 modulo 31",
                frozenset(AB),
                lambda: counter_mod(AB, {"a": 31}, lambda state: state[0] == 0),
                count_mod_zero_regex(AB, "a", 31),
            ),
            LanguageCase(
                "length_mod_40",
                "word length is 0 modulo 40",
                frozenset(ABC),
                lambda: state_dfa(
                    ABC,
                    0,
                    lambda state, char: (state + 1) % 40,
                    lambda state: state == 0,
                ),
                f"({('(a|b|c)' * 40)})*",
            ),
        )
    )
    return tuple(cases)


CASES = {
    "commutative": COMMUTATIVE_CASES,
    "star_free": star_free_cases(),
    "alphabet_3": alphabet_three_cases(),
    "complex_commutative": complex_commutative_cases(),
}


def compose(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    """Compose transformations using the Oracle's vector convention."""
    return tuple(right[index] for index in left)


def is_commutative_monoid(elements: set[tuple[int, ...]]) -> bool:
    """Check pairwise commutativity of a finite transformation monoid."""
    return all(
        compose(left, right) == compose(right, left)
        for left in elements
        for right in elements
    )


def is_aperiodic_monoid(elements: set[tuple[int, ...]]) -> bool:
    """Check that every element has an idempotent power."""
    identity = tuple(range(len(next(iter(elements)))))
    for element in elements:
        power = identity
        stabilized = False
        for _ in range(len(elements) + 1):
            next_power = compose(power, element)
            if next_power == power:
                stabilized = True
                break
            power = next_power
        if not stabilized:
            return False
    return True


def audit_case(group: str, case: LanguageCase, target: DFA, oracle: Oracle) -> None:
    """Assert the structural property advertised by the benchmark group."""
    if set(target.input_symbols) != set(case.alphabet):
        raise AssertionError(f"{case.name} does not use its declared alphabet")
    if group in {"commutative", "complex_commutative"} and not is_commutative_monoid(
        oracle.target_monoid_elements
    ):
        raise AssertionError(f"{case.name} does not have a commutative syntactic monoid")
    if group == "star_free" and not is_aperiodic_monoid(oracle.target_monoid_elements):
        raise AssertionError(f"{case.name} is not star-free")


def run_once(target: DFA, alphabet: set[str], oracle: Oracle, strategy: str) -> tuple[float, dict]:
    """Run one learner and return elapsed time plus current counters."""
    learner = Learner(
        oracle,
        alphabet,
        max_p_length=1,
        monoid_strategy=strategy,
        debug_mode=False,
        verbose=False,
    )

    gc.collect()
    started = time.perf_counter()
    hypothesis = learner.learn()
    elapsed_ms = (time.perf_counter() - started) * 1000

    counterexample = oracle.equivalence_query(hypothesis)
    if counterexample is not None:
        raise AssertionError(f"{strategy} returned a counterexample: {counterexample!r}")
    if len(hypothesis.states) != oracle.target_monoid_size:
        raise AssertionError(
            f"{strategy} learned {len(hypothesis.states)} states; "
            f"expected {oracle.target_monoid_size}"
        )
    if strategy == "promote_to_p" and learner.monoid_check_count != 0:
        raise AssertionError("promote_to_p unexpectedly ran Monoid Consistency Check")

    return elapsed_ms, {
        "mq": learner.mq_count,
        "eq": learner.eq_count,
        "eq_ms": learner.eq_time * 1000,
        "skipped_eq": learner.skipped_eq_count,
        "monoid_checks": learner.monoid_check_count,
        "monoid_check_ms": learner.monoid_probe_time * 1000,
        "right_refinements": learner.right_consistency_refinements,
        "promoted": learner.promoted_i_to_p_count,
        "p_size": len(learner.P),
        "i_size": len(learner.I),
        "s_size": len(learner.S),
        "table_cells": len(learner.table),
    }


def summarize_strategy(times: list[float], metrics: list[dict]) -> dict:
    """Summarize timings while requiring deterministic structural counters."""
    representative = metrics[0]
    timing_keys = {"eq_ms", "monoid_check_ms"}
    stable_keys = set(representative) - timing_keys
    for sample in metrics[1:]:
        if any(sample[key] != representative[key] for key in stable_keys):
            raise AssertionError("non-deterministic structural counters")

    result = {
        "median_ms": statistics.median(times),
        "min_ms": min(times),
        "max_ms": max(times),
        **representative,
    }
    for key in timing_keys:
        result[key] = statistics.median(sample[key] for sample in metrics)
    return result


def case_metadata(group: str, case: LanguageCase, target: DFA, oracle: Oracle) -> dict:
    """Return stable target metadata shared by pilot and formal runs."""
    return {
        "group": group,
        "case": case.name,
        "description": case.description,
        "regex": verified_regex(target, set(case.alphabet), case.regex),
        "alphabet": sorted(case.alphabet),
        "dfa_states": len(target.states),
        "monoid_states": oracle.target_monoid_size,
    }


def expand_optional_operators(regex: str) -> str:
    """Replace every postfix optional operator with an explicit epsilon union."""
    while "?" in regex:
        optional_index = regex.index("?")
        atom_end = optional_index
        atom_start = optional_index - 1

        if atom_start < 0:
            raise ValueError("optional operator has no preceding atom")
        if regex[atom_start] == "*":
            atom_start -= 1
        if regex[atom_start] == ")":
            depth = 1
            atom_start -= 1
            while atom_start >= 0 and depth:
                if regex[atom_start] == ")":
                    depth += 1
                elif regex[atom_start] == "(":
                    depth -= 1
                atom_start -= 1
            if depth:
                raise ValueError("unbalanced parentheses before optional operator")
            atom_start += 1

        atom = regex[atom_start:atom_end]
        regex = regex[:atom_start] + f"({atom}|())" + regex[optional_index + 1:]
    return regex


def verified_regex(
    target: DFA,
    alphabet: set[str],
    preferred_regex: str | None = None,
) -> str:
    """Choose a basic regex and verify that it reconstructs the target language."""
    regex = preferred_regex or GNFA.from_dfa(target).to_regex()
    regex = expand_optional_operators(regex)
    if "?" in regex:
        raise AssertionError("optional operators must be expanded in benchmark regexes")
    rebuilt = DFA.from_nfa(NFA.from_regex(regex, input_symbols=alphabet)).minify()
    difference = target.symmetric_difference(rebuilt)
    if not difference.isempty():
        raise AssertionError("DFA-derived regex does not reconstruct the target language")
    return regex


def enrich_existing_json(path: Path, group: str, cases: tuple[LanguageCase, ...]) -> None:
    """Add DFA-derived regular expressions without rerunning timed benchmarks."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("group") != group:
        raise ValueError(f"{path} contains group {payload.get('group')!r}, expected {group!r}")

    regex_by_case = {}
    for case in cases:
        target = case.build()
        regex_by_case[case.name] = verified_regex(
            target,
            set(case.alphabet),
            case.regex,
        )
    result_names = {result["case"] for result in payload["results"]}
    if result_names != set(regex_by_case):
        raise ValueError("benchmark cases do not match the current suite definition")

    for result in payload["results"]:
        result["regex"] = regex_by_case[result["case"]]
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def compare_case(group: str, case: LanguageCase, repeats: int) -> dict:
    """Warm up, alternate strategy order, and compare one target."""
    target = case.build()
    oracle = Oracle(target)
    audit_case(group, case, target, oracle)
    alphabet = set(case.alphabet)
    samples = {strategy: [] for strategy in STRATEGIES}
    metric_samples = {strategy: [] for strategy in STRATEGIES}

    for strategy in STRATEGIES:
        run_once(target, alphabet, oracle, strategy)

    for repetition in range(repeats):
        order = STRATEGIES if repetition % 2 == 0 else tuple(reversed(STRATEGIES))
        for strategy in order:
            elapsed_ms, metrics = run_once(target, alphabet, oracle, strategy)
            samples[strategy].append(elapsed_ms)
            metric_samples[strategy].append(metrics)

    return {
        **case_metadata(group, case, target, oracle),
        "repeats": repeats,
        **{
            strategy: summarize_strategy(samples[strategy], metric_samples[strategy])
            for strategy in STRATEGIES
        },
    }


def pilot_cases(
    group: str,
    cases: tuple[LanguageCase, ...],
    progress: bool = False,
) -> list[dict]:
    """Run each strategy once to validate selected cases."""
    results = []
    for case in cases:
        if progress:
            print(f"[pilot] {case.name}", file=sys.stderr, flush=True)
        target = case.build()
        oracle = Oracle(target)
        audit_case(group, case, target, oracle)
        item = case_metadata(group, case, target, oracle)
        for strategy in STRATEGIES:
            elapsed_ms, metrics = run_once(target, set(case.alphabet), oracle, strategy)
            item[strategy] = {"elapsed_ms": elapsed_ms, **metrics}
        results.append(item)
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=tuple(CASES), required=True)
    parser.add_argument("--case", help="run only the named case within the group")
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--repeats", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--enrich-existing",
        type=Path,
        help="add regex metadata to an existing benchmark JSON and exit",
    )
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repeats = args.repeats or DEFAULT_REPEATS[args.group]
    cases = CASES[args.group]
    if args.case:
        cases = tuple(case for case in cases if case.name == args.case)
        if not cases:
            raise ValueError(f"unknown case {args.case!r} in group {args.group!r}")
    if args.enrich_existing:
        enrich_existing_json(args.enrich_existing, args.group, cases)
        return
    results = (
        pilot_cases(args.group, cases, progress=args.progress)
        if args.pilot
        else [compare_case(args.group, case, repeats) for case in cases]
    )
    payload = {
        "group": args.group,
        "mode": "pilot" if args.pilot else "benchmark",
        "repeats": 1 if args.pilot else repeats,
        "results": results,
    }
    rendered = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    if not args.quiet:
        print(rendered)


if __name__ == "__main__":
    main()
