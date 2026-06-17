# Failure Case: `(aa|bbb)*`

This directory preserves a counterexample for the experimental
`promote_to_p_monoid_check` strategy.

## Reproduction

```powershell
python benchmark.py --method promote_to_p_monoid_check --regex "(aa|bbb)*" --debug
```

## Observed Failure

The generated hypothesis recognizes the target language and has five states,
but it is not the Right Cayley Graph of the syntactic monoid. The traditional
baseline computes a syntactic monoid with 23 elements for this language.

Promoting every new representative from `I` directly into `P` can produce a
closed observation table without ensuring that row equivalence is preserved
by right multiplication. This case therefore motivates an explicit Right
Consistency condition.

## Files

- `incorrect_observation_table.txt`: final incorrect observation table.
- `incorrect_hypothesis.dot`: final five-state hypothesis DFA.
- `snapshots/table_step_001.txt` through `table_step_005.txt`: complete table
  evolution from the debug run.
