"""Compare the materialized and virtual observation-table implementations."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import platform
import statistics
import subprocess
import time
import tracemalloc
import types
from datetime import datetime, timezone
from pathlib import Path

from experiments.compare_language_categories import CASES
from learner import Learner as VirtualTableLearner
from oracle import Oracle


SOURCE_DIRECTORY = Path(
    "experiment_results/2026-08-25_commutative-star-free-decision-analysis/benchmark_data"
)
SOURCE_FILES = {
    "commutative": SOURCE_DIRECTORY / "commutative.json",
    "star_free": SOURCE_DIRECTORY / "star_free.json",
}
DEFAULT_OUTPUT = Path(
    "experiment_results/2026-08-30_table-removal-ablation/benchmark_data/results.json"
)
DEFAULT_OLD_REVISION = "experiment-2026-08-25-v1"
STRATEGIES = ("post_check", "promote_to_p")
TIERS = ("low", "mid", "high")


def percentile(values: list[float], probability: float) -> float:
    """Return a linearly interpolated percentile."""
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def summarize(values: list[float]) -> dict:
    """Preserve raw samples and their robust summary statistics."""
    return {
        "median": statistics.median(values),
        "q1": percentile(values, 0.25),
        "q3": percentile(values, 0.75),
        "min": min(values),
        "max": max(values),
        "samples": values,
    }


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file_obj:
        return json.load(file_obj)


def select_cases() -> list[dict]:
    """Select low/median/high Promote-Cells cases per group and alphabet size."""
    selected = []
    for group, path in SOURCE_FILES.items():
        document = load_json(path)
        for alphabet_size in range(1, 5):
            candidates = sorted(
                (
                    row
                    for row in document["results"]
                    if row["alphabet_size"] == alphabet_size
                ),
                key=lambda row: (row["promote_to_p"]["table_cells"], row["case"]),
            )
            if len(candidates) < 3:
                raise AssertionError(f"not enough {group} cases for alphabet {alphabet_size}")

            indices = (0, (len(candidates) - 1) // 2, len(candidates) - 1)
            for tier, index in zip(TIERS, indices):
                row = dict(candidates[index])
                row["selection_tier"] = tier
                row["source_group"] = group
                selected.append(row)

    return selected


def load_learner_from_revision(revision: str):
    """Load the exact historical Learner class without changing the worktree."""
    completed = subprocess.run(
        ["git", "show", f"{revision}:learner.py"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    module = types.ModuleType(f"learner_{revision.replace('-', '_')}")
    exec(compile(completed.stdout, f"{revision}:learner.py", "exec"), module.__dict__)
    return module.Learner


def git_revision() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        text=True,
    ).strip()


def learner_sha256() -> str:
    return hashlib.sha256(Path("learner.py").read_bytes()).hexdigest()


def environment_metadata() -> dict:
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "base_git_revision": git_revision(),
        "virtual_learner_sha256": learner_sha256(),
    }


def structural_metrics(learner) -> dict:
    rows = learner.needed_rows()
    cells = len(rows) * len(learner.P) * len(learner.S)
    if hasattr(learner, "table") and len(learner.table) != cells:
        raise AssertionError("historical materialized table is incomplete")

    return {
        "mq": learner.mq_count,
        "eq": learner.eq_count,
        "skipped_eq": learner.skipped_eq_count,
        "monoid_checks": learner.monoid_check_count,
        "right_refinements": learner.right_consistency_refinements,
        "promoted": learner.promoted_i_to_p_count,
        "p_size": len(learner.P),
        "i_size": len(learner.I),
        "s_size": len(learner.S),
        "table_cells": cells,
    }


def stable_signature(learner) -> tuple:
    metrics = structural_metrics(learner)
    return (
        tuple(sorted(metrics.items())),
        frozenset(learner.P),
        frozenset(learner.I),
        frozenset(learner.S),
        learner.query_cache,
    )


def make_learner(learner_class, target, alphabet: set[str], strategy: str):
    return learner_class(
        Oracle(target),
        alphabet,
        monoid_strategy=strategy,
        verbose=False,
    )


def assert_language(target, hypothesis, expected_monoid_states: int) -> None:
    difference = target.symmetric_difference(hypothesis)
    if not difference.isempty():
        raise AssertionError("learner returned a language-inequivalent hypothesis")
    if len(hypothesis.states) != expected_monoid_states:
        raise AssertionError(
            f"learned {len(hypothesis.states)} states; expected {expected_monoid_states}"
        )


def run_warmup(
    learner_classes: dict[str, type],
    target,
    alphabet: set[str],
    strategy: str,
    expected_monoid_states: int,
) -> tuple:
    reference = None
    for learner_class in learner_classes.values():
        learner = make_learner(learner_class, target, alphabet, strategy)
        hypothesis = learner.learn()
        assert_language(target, hypothesis, expected_monoid_states)
        signature = stable_signature(learner)
        if reference is None:
            reference = signature
        elif signature != reference:
            raise AssertionError("historical and virtual learners diverged during warmup")
    return reference


def run_timing_samples(
    learner_classes: dict[str, type],
    target,
    alphabet: set[str],
    strategy: str,
    repeats: int,
    reference: tuple,
) -> dict[str, dict[str, list[float]]]:
    samples = {
        name: {"total_ms": [], "eq_ms": [], "local_ms": []}
        for name in learner_classes
    }
    base_order = tuple(learner_classes.items())

    for repeat in range(repeats):
        order = base_order if repeat % 2 == 0 else tuple(reversed(base_order))
        for name, learner_class in order:
            learner = make_learner(learner_class, target, alphabet, strategy)
            gc.collect()
            started = time.perf_counter_ns()
            learner.learn()
            elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
            if stable_signature(learner) != reference:
                raise AssertionError(f"non-deterministic result for {name}")

            eq_ms = learner.eq_time * 1000
            samples[name]["total_ms"].append(elapsed_ms)
            samples[name]["eq_ms"].append(eq_ms)
            samples[name]["local_ms"].append(elapsed_ms - eq_ms)

    return samples


def run_memory_samples(
    learner_classes: dict[str, type],
    target,
    alphabet: set[str],
    strategy: str,
    repeats: int,
    reference: tuple,
) -> dict[str, list[float]]:
    samples = {name: [] for name in learner_classes}
    base_order = tuple(learner_classes.items())

    for repeat in range(repeats):
        order = base_order if repeat % 2 == 0 else tuple(reversed(base_order))
        for name, learner_class in order:
            learner = make_learner(learner_class, target, alphabet, strategy)
            gc.collect()
            tracemalloc.start()
            learner.learn()
            _, peak_bytes = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            if stable_signature(learner) != reference:
                raise AssertionError(f"memory run diverged for {name}")
            samples[name].append(peak_bytes / 1024)

    return samples


def summarize_implementation(timing: dict, memory: list[float], metrics: dict) -> dict:
    return {
        "metrics": metrics,
        "total_ms": summarize(timing["total_ms"]),
        "eq_ms": summarize(timing["eq_ms"]),
        "local_ms": summarize(timing["local_ms"]),
        "peak_kib": summarize(memory),
    }


def compare_case(
    case: dict,
    case_builders: dict[str, object],
    learner_classes: dict[str, type],
    timing_repeats: int,
    memory_repeats: int,
) -> dict:
    source_case = case_builders[case["case"]]
    alphabet = set(source_case.alphabet)
    if alphabet != set(case["alphabet"]):
        raise AssertionError(f"alphabet mismatch for {case['case']}")
    target = source_case.build()
    if len(target.states) != case["dfa_states"]:
        raise AssertionError(
            f"{case['case']} rebuilt DFA has {len(target.states)} states; "
            f"source data has {case['dfa_states']}"
        )

    result = {
        "group": case["source_group"],
        "selection_tier": case["selection_tier"],
        "case": case["case"],
        "description": case["description"],
        "regex": case["regex"],
        "alphabet": sorted(alphabet),
        "alphabet_size": len(alphabet),
        "dfa_states": case["dfa_states"],
        "monoid_states": case["monoid_states"],
        "source_table_cells": {
            strategy: case[strategy]["table_cells"] for strategy in STRATEGIES
        },
        "strategies": {},
    }

    for strategy in STRATEGIES:
        reference = run_warmup(
            learner_classes,
            target,
            alphabet,
            strategy,
            case["monoid_states"],
        )
        timing = run_timing_samples(
            learner_classes,
            target,
            alphabet,
            strategy,
            timing_repeats,
            reference,
        )
        memory = run_memory_samples(
            learner_classes,
            target,
            alphabet,
            strategy,
            memory_repeats,
            reference,
        )
        metrics = dict(reference[0])
        implementations = {
            name: summarize_implementation(timing[name], memory[name], metrics)
            for name in learner_classes
        }
        old_local = implementations["materialized"]["local_ms"]["median"]
        new_local = implementations["virtual"]["local_ms"]["median"]
        old_peak = implementations["materialized"]["peak_kib"]["median"]
        new_peak = implementations["virtual"]["peak_kib"]["median"]
        result["strategies"][strategy] = {
            **implementations,
            "local_change_percent": (new_local / old_local - 1) * 100,
            "peak_change_percent": (new_peak / old_peak - 1) * 100,
        }

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--old-revision", default=DEFAULT_OLD_REVISION)
    parser.add_argument("--timing-repeats", type=int, default=25)
    parser.add_argument("--memory-repeats", type=int, default=5)
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.timing_repeats < 1 or args.memory_repeats < 1:
        raise ValueError("repeat counts must be positive")

    cases = select_cases()
    if args.limit is not None:
        cases = cases[: args.limit]

    old_learner = load_learner_from_revision(args.old_revision)
    learner_classes = {
        "materialized": old_learner,
        "virtual": VirtualTableLearner,
    }
    case_builders = {
        case.name: case
        for group_cases in CASES.values()
        for case in group_cases
    }
    started = time.perf_counter()
    results = []
    for index, case in enumerate(cases, start=1):
        print(
            f"[{index:02d}/{len(cases):02d}] {case['source_group']} "
            f"alpha={case['alphabet_size']} {case['selection_tier']} {case['case']}"
        )
        results.append(
            compare_case(
                case,
                case_builders,
                learner_classes,
                args.timing_repeats,
                args.memory_repeats,
            )
        )

    document = {
        "experiment": "table-removal-ablation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "old_revision": args.old_revision,
        "new_implementation": "working-tree virtual observation table",
        "source_files": {key: str(value) for key, value in SOURCE_FILES.items()},
        "selection_rule": (
            "For each language group and alphabet size 1-4, sort by historical "
            "promote_to_p table_cells and select the minimum, lower median, and maximum."
        ),
        "timing_repeats": args.timing_repeats,
        "memory_repeats": args.memory_repeats,
        "warmups_per_implementation": 1,
        "elapsed_seconds": time.perf_counter() - started,
        "environment": environment_metadata(),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(document, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved {len(results)} cases to {args.output}")


if __name__ == "__main__":
    main()
