"""Reproducible performance comparison for the two integrated strategies."""

from __future__ import annotations

import gc
import io
import json
import statistics
import time
from contextlib import redirect_stdout

from learner import Learner
from oracle import Oracle
from regex_converter import regex_to_minimal_dfa


ALPHABET = {"a", "b"}
STRATEGIES = ("post_check", "promote_to_p")
REPEATS = 25

CASES = (
    ("tiny_cycle", "(ab)*"),
    ("suffix_aab", "(a|b)*aab"),
    ("even_a", "b*(ab*ab*)*"),
    ("mixed_blocks", "(aa|bbb)*"),
    ("finite_tail", "()|(a|b)|(a|b)(a|b)|(a|b)(a|b)(a|b)b*"),
    ("mixed_suffix", "(a|bb)*ab(a|b)*baa"),
    ("cyclic_12", "(" + "b*a" * 12 + ")*b*"),
)


def build_target(regex: str):
    """Convert a regex while suppressing converter diagnostics."""
    with redirect_stdout(io.StringIO()):
        return regex_to_minimal_dfa(regex, ALPHABET)


def run_once(target, strategy: str) -> tuple[float, dict[str, int | float]]:
    """Run one learner instance and collect its existing counters."""
    oracle = Oracle(target)
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
    elapsed = time.perf_counter() - started

    if len(hypothesis.states) != oracle.target_monoid_size:
        raise AssertionError(
            f"{strategy} learned {len(hypothesis.states)} states; "
            f"expected {oracle.target_monoid_size}"
        )
    if strategy == "promote_to_p" and learner.monoid_check_count != 0:
        raise AssertionError("promote_to_p unexpectedly ran Monoid Consistency Check")

    metrics = {
        "mq": learner.mq_count,
        "eq": learner.eq_count,
        "skipped_eq": learner.skipped_eq_count,
        "monoid_checks": learner.monoid_check_count,
        "monoid_check_ms": learner.monoid_probe_time * 1000,
        "right_refinements": learner.right_consistency_refinements,
        "promoted": learner.promoted_i_to_p_count,
        "p_size": len(learner.P),
        "i_size": len(learner.I),
        "s_size": len(learner.S),
    }
    return elapsed, metrics


def compare_case(name: str, regex: str) -> dict:
    """Warm up and compare both strategies with alternating run order."""
    target = build_target(regex)
    oracle = Oracle(target)
    samples = {strategy: [] for strategy in STRATEGIES}
    metric_samples = {strategy: [] for strategy in STRATEGIES}

    for strategy in STRATEGIES:
        run_once(target, strategy)

    for repetition in range(REPEATS):
        order = STRATEGIES if repetition % 2 == 0 else tuple(reversed(STRATEGIES))
        for strategy in order:
            elapsed, metrics = run_once(target, strategy)
            samples[strategy].append(elapsed * 1000)
            metric_samples[strategy].append(metrics)

    result = {
        "case": name,
        "regex": regex,
        "dfa_states": len(target.states),
        "monoid_states": oracle.target_monoid_size,
    }
    for strategy in STRATEGIES:
        representative = metric_samples[strategy][0]
        stable_keys = set(representative) - {"monoid_check_ms"}
        if any(
            any(metrics[key] != representative[key] for key in stable_keys)
            for metrics in metric_samples[strategy][1:]
        ):
            raise AssertionError(f"non-deterministic counters for {name}/{strategy}")

        result[strategy] = {
            "median_ms": statistics.median(samples[strategy]),
            "min_ms": min(samples[strategy]),
            "max_ms": max(samples[strategy]),
            **representative,
            "monoid_check_ms": statistics.median(
                metrics["monoid_check_ms"] for metrics in metric_samples[strategy]
            ),
        }
    return result


def main() -> None:
    """Print machine-readable comparison results for the report."""
    print(json.dumps([compare_case(*case) for case in CASES], indent=2))


if __name__ == "__main__":
    main()
