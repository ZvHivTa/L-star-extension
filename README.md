# L-star Extension

This project is an experimental Python implementation of an L*-style active learning algorithm for regular languages and syntactic monoid-aware DFA learning.

The main idea is to compare two routes:

```text
Classic route:
  Learn a DFA with classic L*
  -> convert the learned DFA to a transition monoid
  -> build a monoid-induced DFA

Integrated route:
  Use an extended L*-style observation table
  -> learn a DFA while refining syntactic monoid consistency during learning
```

The project is mainly intended for algorithm experiments, performance comparison, and debugging the evolution of observation tables and hypothesis automata.

## Core Idea

Classic L* learns a DFA for a target regular language by maintaining an observation table over prefixes and suffixes. This project extends that idea with a three-dimensional observation table:

```text
T[i, p, s] = MQ(p + i + s)
```

where:

- `I` is the current set of main representatives, interpreted as candidate states or candidate monoid elements.
- `P` is a set of left contexts.
- `S` is a set of right contexts.

This table is designed to approximate syntactic congruence:

```text
u ≡ v iff for all x, y: xuy ∈ L ⇔ xvy ∈ L
```

Instead of only checking whether two prefixes have the same right language, the integrated learner also checks whether candidate representatives remain consistent under known left and right contexts.

## Algorithm Flow

The integrated learner has four main refinement mechanisms.

### Closure Refinement

The learner checks whether every right extension:

```text
I · alphabet
```

is represented by an existing row pattern in `I`.

If a new pattern is found, it is promoted into `I`.

### Right Consistency Refinement

Before building a hypothesis, the learner checks that equal suffix rows remain
equal after right multiplication by each alphabet symbol. If `i` and `j` have
the same suffix row but `ia` and `ja` differ on suffix `s`, the learner adds
`a + s` to `S`.

### Counterexample Refinement

When the current hypothesis DFA is not language-equivalent to the target, the oracle returns a counterexample. The learner uses a Rivest-Schapire style breakpoint strategy to extract a distinguishing suffix and adds it to `S`.

### Algebraic Consistency Refinement

After language equivalence succeeds, the learner performs an internal monoid consistency check. If a boundary word and its representative are distinguishable by a known left/right context, the distinguishing left context is added to `P`.

In short:

```text
I grows when new representatives are needed.
S grows when right consistency fails or the language acceptor is wrong.
P grows when syntactic monoid consistency is violated.
```

## Repository Structure

```text
.
├── benchmark.py
├── learner.py
├── oracle.py
├── classic_lstar_learner.py
├── classic_lstar_oracle.py
├── regex_converter.py
├── experiments/
│   └── reports/
├── experiment_results/
├── tests/
└── docs/
```

Important files:

- `learner.py`: integrated L*-style learner with `P × I × S` observation table and monoid consistency refinement.
- `oracle.py`: oracle for membership queries, equivalence queries, and transition monoid verification.
- `classic_lstar_learner.py`: classic L* baseline.
- `classic_lstar_oracle.py`: oracle used by the classic baseline.
- `benchmark.py`: compares the classic route and the integrated route.
- `regex_converter.py`: converts a regular expression into a minimal DFA using `automata-lib`.
- `experiments/`: reproducible benchmark runners; report and figure generators live in `experiments/reports/`.
- `experiment_results/`: dated reports, raw benchmark JSON, and generated figures.
- `tests/`: focused regression tests for learner behavior and experiment statistics.
- `docs/`: project notes and work logs.

## Requirements

The code uses Python and `automata-lib`.

Install the main dependency with:

```bash
pip install automata-lib
```

If you are using the local virtual environment in this repository, activate it first.

## Running a Benchmark

Edit the target regular expression near the bottom of `benchmark.py`, then run:

```bash
python benchmark.py
```

For performance measurements, use:

```python
benchmark(regex, debug_mode=False)
```

For debugging the learning process, use:

```python
benchmark(regex, debug_mode=True)
```

Debug mode writes step-by-step files under `debug_snapshots/`.

Select a benchmark method with:

```bash
python benchmark.py --method baseline
python benchmark.py --method post_check
python benchmark.py --method promote_to_p
python benchmark.py --method all
```

`post_check` adds a left context to `P` only after a Monoid Consistency
failure. `promote_to_p` adds every new `I` representative to `P` immediately;
because `I` is already covered by `P`, it stops after a successful EQ and does
not execute Monoid Consistency Check.

## Benchmark Output

The benchmark compares:

### Process A: Classic Baseline

```text
Classic L*
-> learned DFA
-> transition monoid
-> monoid-induced DFA
```

Reported metrics include:

- L* learning time
- EQ time
- DFA-to-monoid time
- monoid DFA construction time
- total time
- MQ count
- EQ count

### Process B: Integrated Learner

```text
Extended observation table
-> hypothesis DFA
-> language EQ when needed
-> monoid consistency refinement
```

Reported metrics include:

- total time
- EQ time
- MQ count
- EQ count
- skipped EQ count

The integrated learner can skip repeated EQ calls after language equivalence has already been confirmed and only `P` has changed due to algebraic refinement.

## Debug Snapshots

When `debug_mode=True`, the learner saves:

```text
debug_snapshots/table_step_XXX.txt
debug_snapshots/hypothesis_step_XXX.dot
```

The `.dot` files are Graphviz DOT files. They can be previewed directly in VS Code with a Graphviz/DOT preview extension.

The table files show the current `P × I × S` observation table.

## Notes on Timing

For fair timing:

- Use `debug_mode=False`.
- Avoid counting debug file output.
- The final `observation_table.txt` export happens after integrated learner timing.
- Classic baseline total time includes monoid DFA construction.

Very small examples can have noisy timings because they run in fractions of a millisecond. For serious experiments, repeated runs and median/min reporting are recommended.

## Current Optimization Highlights

The integrated learner includes several implementation-level optimizations:

- cached row vectors for `get_row(i)`
- cached sorted `P`, `S`, and `I`
- cached right extensions
- reused observation table cells during monoid consistency checks
- local context cache inside each monoid consistency pass
- skipped EQ calls after language equivalence is already confirmed

The oracles use `deque` for BFS shortest-counterexample search.

## Example Regular Expressions

Some useful test targets:

```python
regex = "(a|b)*aab"
regex = "(aa|bbb)*"
regex = "(ab)*"
regex = "b*(ab*ab*)*"
regex = "()|(a|b)|(a|b)(a|b)|(a|b)(a|b)(a|b)b*"
regex = generate_cyclic_group_regex(50)
```

## Generated Files

These files and folders are generated during runs:

```text
observation_table.txt
debug_snapshots/
__pycache__/
```

They are not core source files.

## Project Status

The current focus is efficiency comparison between the classic two-step method and the integrated syntactic monoid-aware learner. Correctness has been tested on several regular expression examples, and ongoing work is focused on reducing implementation overhead and improving benchmark reporting.
