# Experiment Results

Each benchmark run is stored in its own directory:

```text
YYYY-MM-DD_experiment-topic/
├── REPORT.md
├── benchmark_data/
│   ├── group_1.json
│   └── group_2.json
└── figures/                 # optional generated charts
    └── figure_1.svg
```

The directory name records the experiment date and subject. `REPORT.md` contains
the human-readable analysis, while `benchmark_data/` preserves the raw,
machine-readable results needed to reproduce every table and calculation.
Generated visualizations belong in `figures/` when an experiment includes
charts.

Pilot runs and temporary diagnostics should not be kept in a completed
experiment directory.
