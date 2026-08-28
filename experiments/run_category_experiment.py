"""Run one large language category with per-case timeouts and checkpoints."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import deque
from pathlib import Path

from experiments.compare_language_categories import (
    CASES,
    DEFAULT_REPEATS,
    environment_metadata,
)


def canonical_dfa_signature(dfa) -> tuple:
    """Return a state-name-independent signature for a reachable minimal DFA."""
    alphabet = tuple(sorted(dfa.input_symbols))
    order = []
    indexes = {dfa.initial_state: 0}
    queue = deque([dfa.initial_state])
    while queue:
        state = queue.popleft()
        order.append(state)
        for symbol in alphabet:
            target = dfa.transitions[state][symbol]
            if target not in indexes:
                indexes[target] = len(indexes)
                queue.append(target)
    transitions = tuple(
        tuple(indexes[dfa.transitions[state][symbol]] for symbol in alphabet)
        for state in order
    )
    accepting = tuple(state in dfa.final_states for state in order)
    return alphabet, accepting, transitions


def validate_suite(group: str) -> None:
    """Reject duplicate names or duplicate minimized languages before timing."""
    names = set()
    signatures = {}
    for case in CASES[group]:
        if case.name in names:
            raise ValueError(f"duplicate case name: {case.name}")
        names.add(case.name)
        signature = canonical_dfa_signature(case.build())
        previous = signatures.get(signature)
        if previous is not None:
            raise ValueError(f"duplicate languages: {previous} and {case.name}")
        signatures[signature] = case.name


def load_checkpoint(path: Path) -> dict | None:
    """Load one completed case checkpoint when it is valid."""
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    results = payload.get("results", [])
    return results[0] if len(results) == 1 else None


def update_discarded(
    path: Path,
    group: str,
    discarded: list[dict],
    timeout_seconds: int,
) -> None:
    """Replace one group's entries in the shared discarded-case manifest."""
    existing = []
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8")).get("discarded", [])
    retained = [item for item in existing if item.get("group") != group]
    payload = {
        "timeout_seconds": timeout_seconds,
        "discarded": retained + discarded,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_group(args: argparse.Namespace) -> dict:
    """Run or resume every case in one category."""
    validate_suite(args.group)
    cases = CASES[args.group]
    repeats = args.repeats or DEFAULT_REPEATS[args.group]
    checkpoint_dir = args.checkpoint_dir / args.group
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    results = []
    discarded = []
    environment = None
    started = time.perf_counter()

    for index, case in enumerate(cases, 1):
        checkpoint = checkpoint_dir / f"{case.name}.json"
        saved = load_checkpoint(checkpoint)
        if saved is not None:
            results.append(saved)
            print(f"[{args.group} {index}/{len(cases)}] resumed {case.name}", flush=True)
            continue

        command = [
            sys.executable,
            "-m",
            "experiments.compare_language_categories",
            "--group",
            args.group,
            "--case",
            case.name,
            "--repeats",
            str(repeats),
            "--output",
            str(checkpoint),
            "--quiet",
        ]
        case_started = time.perf_counter()
        try:
            completed = subprocess.run(
                command,
                cwd=Path(__file__).resolve().parent.parent,
                capture_output=True,
                text=True,
                timeout=args.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            discarded.append(
                {
                    "group": args.group,
                    "case": case.name,
                    "description": case.description,
                    "alphabet": sorted(case.alphabet),
                    "alphabet_size": len(case.alphabet),
                    "reason": "timeout",
                    "timeout_seconds": args.timeout_seconds,
                }
            )
            print(f"[{args.group} {index}/{len(cases)}] TIMEOUT {case.name}", flush=True)
            continue

        elapsed = time.perf_counter() - case_started
        if completed.returncode != 0:
            discarded.append(
                {
                    "group": args.group,
                    "case": case.name,
                    "description": case.description,
                    "alphabet": sorted(case.alphabet),
                    "alphabet_size": len(case.alphabet),
                    "reason": "validation_or_runtime_error",
                    "returncode": completed.returncode,
                    "stderr": completed.stderr[-4000:],
                }
            )
            print(f"[{args.group} {index}/{len(cases)}] ERROR {case.name}", flush=True)
            continue

        payload = json.loads(checkpoint.read_text(encoding="utf-8"))
        environment = environment or payload.get("environment")
        results.append(payload["results"][0])
        print(
            f"[{args.group} {index}/{len(cases)}] {case.name} ({elapsed:.2f}s)",
            flush=True,
        )

    payload = {
        "group": args.group,
        "mode": "benchmark",
        "generated_cases": len(cases),
        "completed_cases": len(results),
        "discarded_cases": len(discarded),
        "repeats": repeats,
        "timeout_seconds": args.timeout_seconds,
        "elapsed_seconds": time.perf_counter() - started,
        "environment": environment or environment_metadata(),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    update_discarded(
        args.discarded_output,
        args.group,
        discarded,
        args.timeout_seconds,
    )
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=tuple(CASES), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--discarded-output", type=Path, required=True)
    parser.add_argument("--checkpoint-dir", type=Path, required=True)
    parser.add_argument("--repeats", type=int)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = run_group(args)
    print(
        f"completed {payload['completed_cases']}/{payload['generated_cases']} "
        f"{args.group} cases; discarded {payload['discarded_cases']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
