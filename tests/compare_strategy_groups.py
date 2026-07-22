"""Grouped benchmark for post_check and promote_to_p strategies."""

from __future__ import annotations

import argparse
import gc
import io
import json
import statistics
import time
from contextlib import redirect_stdout
from pathlib import Path

from learner import Learner
from oracle import Oracle
from regex_converter import regex_to_minimal_dfa


ALPHABET = {"a", "b"}
STRATEGIES = ("post_check", "promote_to_p")
DEFAULT_REPEATS = {"ordinary": 25, "medium": 15, "stress": 7}


def cyclic_regex(size: int) -> str:
    return "(" + "b*a" * size + ")*b*"


CASES = {
    "ordinary": (
        ("all_words", "(a|b)*"),
        ("empty_only", "()"),
        ("a_star", "a*"),
        ("b_star", "b*"),
        ("even_a_only", "(aa)*"),
        ("ab_cycle", "(ab)*"),
        ("ba_cycle", "(ba)*"),
        ("ends_a", "(a|b)*a"),
        ("ends_b", "(a|b)*b"),
        ("a_then_b", "a*b*"),
        ("b_then_a", "b*a*"),
        ("a_or_bb_blocks", "(a|bb)*"),
    ),
    "medium": (
        ("suffix_aab", "(a|b)*aab"),
        ("suffix_abba", "(a|b)*abba"),
        ("suffix_abab", "(a|b)*abab"),
        ("alternating_blocks", "(ab|ba)*"),
        ("mixed_blocks_2_3", "(aa|bbb)*"),
        ("finite_b_tail", "()|(a|b)|(a|b)(a|b)|(a|b)(a|b)(a|b)b*"),
        ("mixed_suffix", "(a|bb)*ab(a|b)*baa"),
        ("exact_a6b", "aaaaaab"),
        ("cyclic_8", cyclic_regex(8)),
        ("cyclic_12", cyclic_regex(12)),
        ("cyclic_16", cyclic_regex(16)),
        ("cyclic_20", cyclic_regex(20)),
    ),
    "stress": (
        ("cyclic_24", cyclic_regex(24)),
        ("cyclic_32", cyclic_regex(32)),
        ("cyclic_40", cyclic_regex(40)),
        ("cyclic_48", cyclic_regex(48)),
        ("cyclic_56", cyclic_regex(56)),
        ("cyclic_64", cyclic_regex(64)),
        ("cyclic_70", cyclic_regex(70)),
        ("exact_a8b", "a" * 8 + "b"),
        ("exact_a12b", "a" * 12 + "b"),
        ("exact_a16b", "a" * 16 + "b"),
        ("suffix_a6b", "(a|b)*" + "a" * 6 + "b"),
        ("suffix_abababab", "(a|b)*abababab"),
    ),
}


def build_target(regex: str):
    """Convert a regex while suppressing converter diagnostics."""
    with redirect_stdout(io.StringIO()):
        return regex_to_minimal_dfa(regex, ALPHABET)


def run_once(target, oracle: Oracle, strategy: str) -> tuple[float, dict]:
    """Run one learner and return elapsed time plus current counters."""
    learner = Learner(
        oracle,
        ALPHABET,
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
        raise AssertionError(f"{strategy} returned a language counterexample: {counterexample!r}")
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


def compare_case(group: str, name: str, regex: str, repeats: int) -> dict:
    """Warm up, alternate strategy order, and compare one target."""
    target = build_target(regex)
    oracle = Oracle(target)
    samples = {strategy: [] for strategy in STRATEGIES}
    metric_samples = {strategy: [] for strategy in STRATEGIES}

    for strategy in STRATEGIES:
        run_once(target, oracle, strategy)

    for repetition in range(repeats):
        order = STRATEGIES if repetition % 2 == 0 else tuple(reversed(STRATEGIES))
        for strategy in order:
            elapsed_ms, metrics = run_once(target, oracle, strategy)
            samples[strategy].append(elapsed_ms)
            metric_samples[strategy].append(metrics)

    return {
        "group": group,
        "case": name,
        "regex": regex,
        "repeats": repeats,
        "dfa_states": len(target.states),
        "monoid_states": oracle.target_monoid_size,
        **{
            strategy: summarize_strategy(samples[strategy], metric_samples[strategy])
            for strategy in STRATEGIES
        },
    }


def pilot_group(group: str) -> list[dict]:
    """Run each strategy once to validate a group's scale and correctness."""
    results = []
    for name, regex in CASES[group]:
        target = build_target(regex)
        oracle = Oracle(target)
        item = {
            "group": group,
            "case": name,
            "regex": regex,
            "dfa_states": len(target.states),
            "monoid_states": oracle.target_monoid_size,
        }
        for strategy in STRATEGIES:
            elapsed_ms, metrics = run_once(target, oracle, strategy)
            item[strategy] = {"elapsed_ms": elapsed_ms, **metrics}
        results.append(item)
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=tuple(CASES), required=True)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--repeats", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repeats = args.repeats or DEFAULT_REPEATS[args.group]
    if args.pilot:
        results = pilot_group(args.group)
    else:
        results = [
            compare_case(args.group, name, regex, repeats)
            for name, regex in CASES[args.group]
        ]

    payload = {
        "group": args.group,
        "mode": "pilot" if args.pilot else "benchmark",
        "repeats": 1 if args.pilot else repeats,
        "results": results,
    }
    rendered = json.dumps(payload, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    if not args.quiet:
        print(rendered)


if __name__ == "__main__":
    main()
