"""Generate the bilingual Markdown report for the table-removal ablation."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path


DEFAULT_INPUT = Path(
    "experiment_results/2026-08-30_table-removal-ablation/benchmark_data/results.json"
)
DEFAULT_OUTPUT = Path(
    "experiment_results/2026-08-30_table-removal-ablation/REPORT.md"
)
STRATEGIES = ("post_check", "promote_to_p")
STRATEGY_NAMES = {"post_check": "Post", "promote_to_p": "Promote"}


def load_data(path: Path) -> dict:
    with path.open(encoding="utf-8") as file_obj:
        return json.load(file_obj)


def percent(value: float) -> str:
    return f"{value:+.1f}%"


def implementation_values(row: dict, strategy: str) -> tuple[dict, dict]:
    result = row["strategies"][strategy]
    return result["materialized"], result["virtual"]


def grouped_summary(rows: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for row in rows:
        for strategy in STRATEGIES:
            groups[(row["group"], strategy)].append((row, row["strategies"][strategy]))
            groups[("all", strategy)].append((row, row["strategies"][strategy]))

    summaries = []
    for (group, strategy), selected in groups.items():
        old_local = sum(
            result["materialized"]["local_ms"]["median"] for _, result in selected
        )
        new_local = sum(
            result["virtual"]["local_ms"]["median"] for _, result in selected
        )
        old_peak = [
            result["materialized"]["peak_kib"]["median"] for _, result in selected
        ]
        new_peak = [result["virtual"]["peak_kib"]["median"] for _, result in selected]
        relative_local = [result["local_change_percent"] for _, result in selected]
        relative_peak = [result["peak_change_percent"] for _, result in selected]
        summaries.append(
            {
                "group": group,
                "strategy": strategy,
                "cases": len(selected),
                "old_local": old_local,
                "new_local": new_local,
                "aggregate_local_change": (new_local / old_local - 1) * 100,
                "median_case_local_change": statistics.median(relative_local),
                "median_old_peak": statistics.median(old_peak),
                "median_new_peak": statistics.median(new_peak),
                "median_peak_change": statistics.median(relative_peak),
            }
        )
    return sorted(summaries, key=lambda item: (item["group"] != "all", item["group"], item["strategy"]))


def summary_table(rows: list[dict], chinese: bool) -> list[str]:
    if chinese:
        lines = [
            "| 组别 | 策略 | 用例 | Σ本地中位时间 旧/新 ms | 聚合变化 | 逐例变化中位数 | 峰值内存中位数 旧/新 KiB | 内存变化中位数 |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
        group_names = {"all": "合计", "commutative": "交换语言", "star_free": "Star-free"}
    else:
        lines = [
            "| Group | Strategy | Cases | Sum median local old/new ms | Aggregate change | Median per-case change | Median peak old/new KiB | Median memory change |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
        group_names = {"all": "Total", "commutative": "Commutative", "star_free": "Star-free"}

    for item in grouped_summary(rows):
        lines.append(
            f"| {group_names[item['group']]} | {STRATEGY_NAMES[item['strategy']]} | {item['cases']} | "
            f"{item['old_local']:.3f}/{item['new_local']:.3f} | "
            f"{percent(item['aggregate_local_change'])} | "
            f"{percent(item['median_case_local_change'])} | "
            f"{item['median_old_peak']:.1f}/{item['median_new_peak']:.1f} | "
            f"{percent(item['median_peak_change'])} |"
        )
    return lines


def detail_table(rows: list[dict], chinese: bool) -> list[str]:
    if chinese:
        lines = [
            "| 语言 | 组别/层级 | 字母表大小 | DFA/Monoid | 策略 | Cells | 本地时间旧/新 ms | 时间变化 | 峰值内存旧/新 KiB | 内存变化 | MQ/EQ |",
            "|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|",
        ]
        group_names = {"commutative": "交换", "star_free": "Star-free"}
    else:
        lines = [
            "| Language | Group/tier | Alphabet size | DFA/Monoid | Strategy | Cells | Local old/new ms | Time change | Peak old/new KiB | Memory change | MQ/EQ |",
            "|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|",
        ]
        group_names = {"commutative": "Commutative", "star_free": "Star-free"}

    for row in rows:
        for strategy in STRATEGIES:
            result = row["strategies"][strategy]
            old, new = implementation_values(row, strategy)
            metrics = new["metrics"]
            lines.append(
                f"| `{row['case']}` | {group_names[row['group']]}/{row['selection_tier']} | "
                f"{row['alphabet_size']} | {row['dfa_states']}/{row['monoid_states']} | "
                f"{STRATEGY_NAMES[strategy]} | {metrics['table_cells']:,} | "
                f"{old['local_ms']['median']:.3f}/{new['local_ms']['median']:.3f} | "
                f"{percent(result['local_change_percent'])} | "
                f"{old['peak_kib']['median']:.1f}/{new['peak_kib']['median']:.1f} | "
                f"{percent(result['peak_change_percent'])} | "
                f"{metrics['mq']:,}/{metrics['eq']} |"
            )
    return lines


def selection_table(rows: list[dict], chinese: bool) -> list[str]:
    if chinese:
        lines = [
            "| 组别 | 字母表大小 | Low | Mid | High |",
            "|---|---:|---|---|---|",
        ]
    else:
        lines = [
            "| Group | Alphabet size | Low | Mid | High |",
            "|---|---:|---|---|---|",
        ]

    indexed = {(row["group"], row["alphabet_size"], row["selection_tier"]): row for row in rows}
    for group in ("commutative", "star_free"):
        for size in range(1, 5):
            selected = [indexed.get((group, size, tier)) for tier in ("low", "mid", "high")]
            if not any(selected):
                continue
            names = [f"`{row['case']}`" if row else "-" for row in selected]
            lines.append(
                f"| {group} | {size} | {names[0]} | {names[1]} | {names[2]} |"
            )
    return lines


def strongest_changes(rows: list[dict], key: str) -> tuple[dict, dict]:
    entries = []
    for row in rows:
        for strategy in STRATEGIES:
            entries.append(
                {
                    "case": row["case"],
                    "strategy": strategy,
                    "value": row["strategies"][strategy][key],
                }
            )
    return min(entries, key=lambda item: item["value"]), max(entries, key=lambda item: item["value"])


def generate_report(data: dict) -> str:
    rows = data["results"]
    best_time, worst_time = strongest_changes(rows, "local_change_percent")
    best_memory, worst_memory = strongest_changes(rows, "peak_change_percent")
    env = data["environment"]

    lines = [
        "# 物化观察表删除消融实验 / Materialized Observation Table Removal Ablation",
        "",
        "## 中文报告",
        "",
        "### 1. 目的",
        "",
        "本实验只研究一个实现变化：删除主 `Learner` 中以 `(i,p,s)` 为键的物化三维 `table`，改由全局 `query_cache` 按需生成虚拟观察表。算法、两种策略、Oracle、反例处理和理论 Cells 定义均保持不变。",
        "",
        "实验回答两个问题：删除后是否保持完全相同的学习轨迹，以及本地时间和峰值内存是否发生变化。它不是 Post 与 Promote 的新一轮胜负实验。",
        "",
        "### 2. 版本与方法",
        "",
        f"- 旧实现：Git 标签 `{data['old_revision']}` 中的原始 `learner.py`，运行时直接由 Git 载入。",
        f"- 新实现：基于 `{env['base_git_revision']}` 的当前工作树，`learner.py` SHA-256 为 `{env['virtual_learner_sha256']}`。",
        f"- 正式用例：{len(rows)} 个；计时重复 {data['timing_repeats']} 次；峰值内存重复 {data['memory_repeats']} 次；每种实现另有 1 次预热。",
        "- 新旧实现逐次交错并轮换先后顺序；Oracle 构造在计时外完成。",
        "- 本地时间定义为总学习时间减去学习器记录的理想 EQ 时间。峰值内存通过独立 `tracemalloc` 运行测量，因此不会污染正式计时样本。",
        "- 每次运行均验证最终语言、monoid 状态数、MQ、EQ、`P/I/S`、跳过 EQ、Monoid Check、right consistency 次数和完整 `query_cache`。任一差异都会中止实验。",
        "",
        "### 3. 分层选择",
        "",
        "对 Commutative 与 Star-free 两组、字母表大小 1–4，按 8.25 历史数据中的 Promote Cells 排序，各取最小值、下中位数和最大值，避免主观挑选有利用例。",
        "",
        *selection_table(rows, True),
        "",
        "### 4. 汇总结果",
        "",
        *summary_table(rows, True),
        "",
        "这里的峰值内存中位数是逐例运行峰值的中位数，不是把所有语言同时装入内存。`Σ本地中位时间` 是把各语言的中位时间相加，用于表示这一固定测试套件的聚合工作量。",
        "",
        "### 5. 逐语言数据",
        "",
        *detail_table(rows, True),
        "",
        "### 6. 结论",
        "",
        f"- 最大时间改善出现在 `{best_time['case']}` / `{STRATEGY_NAMES[best_time['strategy']]}`：{percent(best_time['value'])}；最弱结果为 `{worst_time['case']}` / `{STRATEGY_NAMES[worst_time['strategy']]}`：{percent(worst_time['value'])}。",
        f"- 最大峰值内存改善出现在 `{best_memory['case']}` / `{STRATEGY_NAMES[best_memory['strategy']]}`：{percent(best_memory['value'])}；最弱结果为 `{worst_memory['case']}` / `{STRATEGY_NAMES[worst_memory['strategy']]}`：{percent(worst_memory['value'])}。",
        "- 所有结构与查询轨迹断言均通过，因此此次变化是实现层消融，不改变算法产生的 MQ/EQ、最终集合或语言。",
        "- 历史 8.25 JSON 中的 MQ、EQ、`P/I/S` 和 Cells 仍可继续使用；其本地时间对应旧物化实现，不能直接代表当前代码。",
        "",
        "### 7. 边界",
        "",
        f"结果只反映当前机器、Python 版本和所选 {len(rows)} 个分层语言。微秒到毫秒级时间仍会受系统负载影响；本报告保留全部原始样本和四分位数，正式结论以方向、量级和跨用例一致性为主。下一阶段加入 MQ 计时后还需单独校准统计仪器开销。",
        "",
        "---",
        "",
        "## English Report",
        "",
        "### 1. Objective",
        "",
        "This ablation isolates one implementation change: removing the materialized `(i,p,s)` dictionary from the integrated learner and deriving the virtual observation table from the global MQ cache. The algorithms, strategies, oracle, counterexample handling, and theoretical Cells definition are unchanged.",
        "",
        "### 2. Method",
        "",
        f"The materialized implementation is loaded directly from Git tag `{data['old_revision']}`. The virtual implementation uses learner SHA-256 `{env['virtual_learner_sha256']}`. The suite contains {len(rows)} stratified languages, with {data['timing_repeats']} interleaved timing repetitions, {data['memory_repeats']} independent peak-memory repetitions, and one warmup per implementation.",
        "",
        "Every run requires identical language behavior, monoid state count, MQ/EQ counts, `P/I/S`, refinement counters, and complete MQ-cache contents. Timing and `tracemalloc` runs are separate.",
        "",
        "### 3. Stratified Cases",
        "",
        *selection_table(rows, False),
        "",
        "### 4. Aggregate Results",
        "",
        *summary_table(rows, False),
        "",
        "### 5. Per-language Results",
        "",
        *detail_table(rows, False),
        "",
        "### 6. Conclusions",
        "",
        f"The strongest local-time improvement is `{best_time['case']}` / `{STRATEGY_NAMES[best_time['strategy']]}` at {percent(best_time['value'])}; the weakest result is `{worst_time['case']}` / `{STRATEGY_NAMES[worst_time['strategy']]}` at {percent(worst_time['value'])}.",
        "",
        "All trajectory assertions passed. Historical query counts and structural measurements remain valid, while historical local timings describe the old materialized implementation. The next MQ-instrumented experiment must separately calibrate measurement overhead.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = load_data(args.input)
    report = generate_report(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Saved report to {args.output}")


if __name__ == "__main__":
    main()
