# Experiment Tools

This package keeps reproducible experiment code separate from the regression
test suite.

```text
experiments/
├── compare_language_categories.py  # current grouped benchmark
├── compare_strategies.py          # original small comparison
├── compare_strategy_groups.py     # ordinary/medium/stress comparison
└── reports/
    ├── generate_language_category_report.py
    └── generate_main_decision_report.py
```

Run these files as modules from the repository root. For example:

```powershell
python -m experiments.compare_language_categories --group commutative --output result.json
python -m experiments.reports.generate_main_decision_report --input-dir benchmark_data --output-dir experiment_output
```

Experiment runners write machine-readable benchmark data. Files under
`reports/` consume saved data and generate Markdown reports or figures; they do
not rerun the learners.
