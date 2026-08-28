"""Generate the main strategy-decision report and dependency-free SVG plots."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import random
import statistics
from pathlib import Path


GROUPS = (
    "commutative",
    "star_free",
)
GROUP_LABELS = {
    "commutative": "Commutative",
    "star_free": "Star-free",
}
GROUP_LABELS_ZH = {
    "commutative": "交换语言",
    "star_free": "Star-free 语言",
}
GROUP_COLORS = {
    "commutative": "#16877A",
    "star_free": "#D18B19",
}
EQ_COST_LINES = (1, 10, 100, 300)


def fmt(value: float) -> str:
    """Format a millisecond value for report tables."""
    if abs(value) < 0.001:
        return f"{value:.6f}"
    if abs(value) < 10:
        return f"{value:.3f}"
    return f"{value:,.2f}"


def percentile(values: list[float], probability: float) -> float:
    """Return a linearly interpolated percentile."""
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def bootstrap_delta_ci(row: dict, iterations: int = 3000) -> tuple[float, float]:
    """Bootstrap an independent-sample CI for the difference of local medians."""
    post = row["post_check"]["samples"]["local_ms"]
    promote = row["promote_to_p"]["samples"]["local_ms"]
    seed = int.from_bytes(
        hashlib.sha256(f"{row['group']}:{row['case']}".encode()).digest()[:8],
        "big",
    )
    rng = random.Random(seed)
    deltas = []
    for _ in range(iterations):
        post_sample = rng.choices(post, k=len(post))
        promote_sample = rng.choices(promote, k=len(promote))
        deltas.append(statistics.median(promote_sample) - statistics.median(post_sample))
    return percentile(deltas, 0.025), percentile(deltas, 0.975)


def derive_metrics(row: dict) -> dict:
    """Derive the coordinates and decision threshold for one language."""
    post = row["post_check"]
    promote = row["promote_to_p"]
    saved_eq = post["eq"] - promote["eq"]
    extra_local = promote["median_local_ms"] - post["median_local_ms"]
    ci_low, ci_high = bootstrap_delta_ci(row)
    break_even = extra_local / saved_eq if saved_eq > 0 else None
    return {
        **row,
        "saved_eq": saved_eq,
        "extra_local_ms": extra_local,
        "delta_local_ci_low_ms": ci_low,
        "delta_local_ci_high_ms": ci_high,
        "break_even_eq_ms": break_even,
        "cell_ratio": promote["table_cells"] / post["table_cells"],
        "time_ratio": promote["median_ms"] / post["median_ms"],
    }


def load_experiment(input_dir: Path) -> tuple[dict[str, list[dict]], dict, list[dict]]:
    """Load and validate the benchmark groups and discarded-case manifest."""
    grouped = {}
    environments = []
    for group in GROUPS:
        payload = json.loads((input_dir / f"{group}.json").read_text(encoding="utf-8"))
        if payload["mode"] != "benchmark":
            raise ValueError(f"{group}.json is not a formal benchmark")
        if payload["group"] != group:
            raise ValueError(f"group mismatch in {group}.json")
        environments.append(payload.get("environment", {}))
        grouped[group] = [derive_metrics(row) for row in payload["results"]]

    environment = environments[0]
    if any(item != environment for item in environments[1:]):
        raise ValueError("benchmark groups were not recorded in the same environment")
    discarded_path = input_dir / "discarded_cases.json"
    discarded = []
    if discarded_path.exists():
        discarded = json.loads(discarded_path.read_text(encoding="utf-8")).get(
            "discarded", []
        )
    return grouped, environment, discarded


def svg_text(x: float, y: float, value: str, **attributes) -> str:
    """Return one escaped SVG text element."""
    rendered = " ".join(f'{key.replace("_", "-")}="{html.escape(str(val))}"' for key, val in attributes.items())
    return f'<text x="{x:.1f}" y="{y:.1f}" {rendered}>{html.escape(value)}</text>'


def symlog(value: float, linear_threshold: float = 0.1) -> float:
    """Map signed milliseconds to a compact symmetric logarithmic scale."""
    return math.copysign(math.log10(1 + abs(value) / linear_threshold), value)


def render_decision_svg(rows: list[dict], output: Path, zoom: bool = False) -> None:
    """Render the EQ-saving versus local-cost decision map as SVG."""
    width, height = 1500, 940
    left, right, top, bottom = 125, 370, 95, 110
    plot_width = width - left - right
    plot_height = height - top - bottom
    if zoom:
        absolute_values = [abs(row["extra_local_ms"]) for row in rows]
        zoom_limit = max(0.5, percentile(absolute_values, 0.90) * 1.25)
        visible = [row for row in rows if abs(row["extra_local_ms"]) <= zoom_limit]
        y_min, y_max = -zoom_limit, zoom_limit
        title = f"Main decision map: central low-cost region within {zoom_limit:.2f} ms"
    else:
        visible = rows
        values = [row["extra_local_ms"] for row in rows]
        ci_values = [row["delta_local_ci_low_ms"] for row in rows] + [
            row["delta_local_ci_high_ms"] for row in rows
        ]
        y_min = min(-0.2, min(values + ci_values))
        y_max = max(values + ci_values) * 1.12
        title = "Main decision map: EQ savings versus additional local time"

    x_values = [row["saved_eq"] for row in rows]
    x_min = min(-1.0, min(x_values) - 1)
    x_max = max(x_values) + 3
    sy_min, sy_max = symlog(y_min), symlog(y_max)

    def map_x(value: float) -> float:
        return left + (value - x_min) / (x_max - x_min) * plot_width

    def map_y(value: float) -> float:
        transformed = symlog(max(y_min, min(y_max, value)))
        return top + (sy_max - transformed) / (sy_max - sy_min) * plot_height

    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#FFFFFF"/>',
        svg_text(width / 2, 42, title, text_anchor="middle", font_family="sans-serif", font_size="25", font_weight="700", fill="#17202A"),
        svg_text(width / 2, 70, "Each point is one target language; error bars are bootstrap 95% CIs", text_anchor="middle", font_family="sans-serif", font_size="15", fill="#586069"),
    ]

    y_ticks = [-1, 0, 1, 10, 100, 1000, 10000, 30000]
    if zoom:
        y_ticks = [-10, -5, -2, -1, -0.5, 0, 0.5, 1, 2, 5, 10]
    for tick in y_ticks:
        if y_min <= tick <= y_max:
            y = map_y(tick)
            elements.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}" stroke="#E3E7EA" stroke-width="1"/>')
            elements.append(svg_text(left - 14, y + 5, f"{tick:g}", text_anchor="end", font_family="sans-serif", font_size="13", fill="#4B5563"))

    x_tick_step = 5 if x_max <= 45 else 10
    first_tick = math.ceil(max(0, x_min) / x_tick_step) * x_tick_step
    for tick in range(first_tick, math.floor(x_max) + 1, x_tick_step):
        x = map_x(tick)
        elements.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + plot_height}" stroke="#EEF1F3" stroke-width="1"/>')
        elements.append(svg_text(x, top + plot_height + 28, str(tick), text_anchor="middle", font_family="sans-serif", font_size="13", fill="#4B5563"))

    if x_min <= 0 <= x_max:
        x_zero = map_x(0)
        elements.append(f'<line x1="{x_zero:.1f}" y1="{top}" x2="{x_zero:.1f}" y2="{top + plot_height}" stroke="#7A8288" stroke-width="1.5"/>')
    if y_min <= 0 <= y_max:
        y_zero = map_y(0)
        elements.append(f'<line x1="{left}" y1="{y_zero:.1f}" x2="{left + plot_width}" y2="{y_zero:.1f}" stroke="#7A8288" stroke-width="1.5"/>')

    line_colors = ("#6B7280", "#7C5DB3", "#C17D11", "#B53A3A")
    for cost, color in zip(EQ_COST_LINES, line_colors):
        points = []
        samples = 160
        for index in range(samples + 1):
            x_value = max(0, x_min) + (x_max - max(0, x_min)) * index / samples
            y_value = cost * x_value
            if y_value <= y_max:
                points.append(f"{map_x(x_value):.1f},{map_y(y_value):.1f}")
        if len(points) > 1:
            elements.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2" stroke-dasharray="8 5" opacity="0.85"/>')

    largest_monoids = sorted(rows, key=lambda row: row["monoid_states"], reverse=True)[:4]
    largest_thresholds = sorted(
        (row for row in rows if row["break_even_eq_ms"] is not None),
        key=lambda row: row["break_even_eq_ms"],
        reverse=True,
    )[:3]
    label_cases = {row["case"] for row in largest_monoids + largest_thresholds}

    for row in visible:
        x = map_x(row["saved_eq"])
        y = map_y(row["extra_local_ms"])
        ci_low = map_y(row["delta_local_ci_low_ms"])
        ci_high = map_y(row["delta_local_ci_high_ms"])
        color = GROUP_COLORS[row["group"]]
        radius = 4.5 + 1.7 * math.log10(max(1, row["monoid_states"]))
        elements.append(f'<line x1="{x:.1f}" y1="{ci_low:.1f}" x2="{x:.1f}" y2="{ci_high:.1f}" stroke="{color}" stroke-width="1.4" opacity="0.5"/>')
        tooltip = (
            f"{row['case']} | saved EQ={row['saved_eq']} | extra local="
            f"{row['extra_local_ms']:.3f} ms | alphabet={row['alphabet_size']} | "
            f"monoid={row['monoid_states']}"
        )
        elements.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{color}" '
            f'stroke="#FFFFFF" stroke-width="1.6" opacity="0.88"><title>{html.escape(tooltip)}</title></circle>'
        )
        if row["case"] in label_cases:
            label_x = min(left + plot_width + 12, x + 10)
            label_y = max(top + 14, y - 9)
            elements.append(svg_text(label_x, label_y, row["case"], font_family="sans-serif", font_size="12", fill="#20262C"))

    elements.extend([
        f'<rect x="{left}" y="{top}" width="{plot_width}" height="{plot_height}" fill="none" stroke="#5C6570" stroke-width="1.2"/>',
        svg_text(left + plot_width / 2, height - 40, "EQs saved by Promote  (EQ Post - EQ Promote)", text_anchor="middle", font_family="sans-serif", font_size="18", font_weight="600", fill="#222B33"),
        f'<text x="31" y="{top + plot_height / 2:.1f}" transform="rotate(-90 31 {top + plot_height / 2:.1f})" text-anchor="middle" font-family="sans-serif" font-size="18" font-weight="600" fill="#222B33">Additional local time of Promote (ms, symlog)</text>',
    ])

    legend_x = left + plot_width + 45
    legend_y = top + 15
    elements.append(svg_text(legend_x, legend_y, "Language category", font_family="sans-serif", font_size="16", font_weight="700", fill="#222B33"))
    for index, group in enumerate(GROUPS):
        y = legend_y + 30 + index * 28
        elements.append(f'<circle cx="{legend_x + 7}" cy="{y - 5}" r="7" fill="{GROUP_COLORS[group]}"/>')
        elements.append(svg_text(legend_x + 23, y, GROUP_LABELS[group], font_family="sans-serif", font_size="14", fill="#303840"))

    line_legend_y = legend_y + 165
    elements.append(svg_text(legend_x, line_legend_y, "Decision lines", font_family="sans-serif", font_size="16", font_weight="700", fill="#222B33"))
    for index, (cost, color) in enumerate(zip(EQ_COST_LINES, line_colors)):
        y = line_legend_y + 27 + index * 27
        elements.append(f'<line x1="{legend_x}" y1="{y - 5}" x2="{legend_x + 35}" y2="{y - 5}" stroke="{color}" stroke-width="2" stroke-dasharray="8 5"/>')
        elements.append(svg_text(legend_x + 45, y, f"C = {cost} ms / EQ", font_family="sans-serif", font_size="14", fill="#303840"))

    note_y = line_legend_y + 155
    elements.append(svg_text(legend_x, note_y, "Below a C-line:", font_family="sans-serif", font_size="14", font_weight="700", fill="#16877A"))
    elements.append(svg_text(legend_x, note_y + 22, "Promote wins at that EQ cost", font_family="sans-serif", font_size="13", fill="#303840"))
    elements.append(svg_text(legend_x, note_y + 52, "Above a C-line:", font_family="sans-serif", font_size="14", font_weight="700", fill="#C84B4B"))
    elements.append(svg_text(legend_x, note_y + 74, "Post wins at that EQ cost", font_family="sans-serif", font_size="13", fill="#303840"))
    if zoom:
        elements.append(svg_text(legend_x, note_y + 118, f"Visible points: {len(visible)} / {len(rows)}", font_family="sans-serif", font_size="13", fill="#586069"))

    elements.append("</svg>")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(elements), encoding="utf-8")


def strategy_at_cost(row: dict, eq_cost: float) -> str:
    """Classify a strategy only when its bootstrap interval clears the line."""
    boundary = row["saved_eq"] * eq_cost
    if row["delta_local_ci_high_ms"] < boundary:
        return "promote"
    if row["delta_local_ci_low_ms"] > boundary:
        return "post"
    return "inconclusive"


def render_break_even(row: dict) -> str:
    """Render a language-level break-even threshold."""
    if row["saved_eq"] <= 0:
        return "Promote dominates" if row["extra_local_ms"] < 0 else "no finite threshold"
    if row["break_even_eq_ms"] <= 0:
        return "≤ 0"
    return fmt(row["break_even_eq_ms"])


def detailed_table(rows: list[dict]) -> list[str]:
    """Build a compact but complete per-language Markdown table."""
    lines = [
        "| Case | Alphabet | Alphabet size | DFA | Monoid | Total ms Post/Promote | Local ms Post/Promote | Local IQR Post/Promote | EQ Post/Promote | ΔEQ | ΔLocal ms | C* ms/EQ | MQ Post/Promote | Cells Post/Promote |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        post = row["post_check"]
        promote = row["promote_to_p"]
        post_iqr = f"[{fmt(post['q1_local_ms'])}, {fmt(post['q3_local_ms'])}]"
        promote_iqr = f"[{fmt(promote['q1_local_ms'])}, {fmt(promote['q3_local_ms'])}]"
        lines.append(
            f"| `{row['case']}` | `{''.join(row['alphabet'])}` | "
            f"{row['alphabet_size']} | {row['dfa_states']} | {row['monoid_states']} | "
            f"{fmt(post['median_ms'])}/{fmt(promote['median_ms'])} | "
            f"{fmt(post['median_local_ms'])}/{fmt(promote['median_local_ms'])} | "
            f"{post_iqr}/{promote_iqr} | {post['eq']}/{promote['eq']} | "
            f"{row['saved_eq']} | {fmt(row['extra_local_ms'])} | "
            f"{render_break_even(row)} | {post['mq']:,}/{promote['mq']:,} | "
            f"{post['table_cells']:,}/{promote['table_cells']:,} |"
        )
    return lines


def group_summary(grouped: dict[str, list[dict]]) -> list[str]:
    """Summarize the decision coordinates by language category."""
    lines = [
        "| Group | Cases | Alphabet sizes | Σ Local median ms Post/Promote | ΔLocal ms | EQ Post/Promote | ΔEQ | Group C* ms/EQ | Cells Post/Promote |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    all_rows = []
    for group in GROUPS:
        rows = grouped[group]
        all_rows.extend(rows)
        lines.append(group_summary_row(GROUP_LABELS_ZH[group], rows))
    lines.append(group_summary_row("合计", all_rows))
    return lines


def group_summary_row(label: str, rows: list[dict]) -> str:
    """Render one aggregate decision-summary row."""
    post_local = sum(row["post_check"]["median_local_ms"] for row in rows)
    promote_local = sum(row["promote_to_p"]["median_local_ms"] for row in rows)
    post_eq = sum(row["post_check"]["eq"] for row in rows)
    promote_eq = sum(row["promote_to_p"]["eq"] for row in rows)
    saved_eq = post_eq - promote_eq
    extra_local = promote_local - post_local
    threshold = extra_local / saved_eq if saved_eq > 0 else math.inf
    post_cells = sum(row["post_check"]["table_cells"] for row in rows)
    promote_cells = sum(row["promote_to_p"]["table_cells"] for row in rows)
    threshold_text = fmt(threshold) if math.isfinite(threshold) else "N/A"
    alphabet_sizes = ", ".join(str(size) for size in sorted({row["alphabet_size"] for row in rows}))
    return (
        f"| {label} | {len(rows)} | {alphabet_sizes} | "
        f"{fmt(post_local)}/{fmt(promote_local)} | "
        f"{fmt(extra_local)} | {post_eq}/{promote_eq} | {saved_eq} | "
        f"{threshold_text} | {post_cells:,}/{promote_cells:,} |"
    )


def alphabet_summary(rows: list[dict]) -> list[str]:
    """Summarize strategy coordinates after stratifying by alphabet size."""
    lines = [
        "| Group | Alphabet size | Cases | Σ Local median ms Post/Promote | ΔLocal ms | EQ Post/Promote | ΔEQ | Cells Post/Promote |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for size in sorted({row["alphabet_size"] for row in rows}):
        selections = [
            (GROUP_LABELS_ZH[group], [
                row for row in rows
                if row["alphabet_size"] == size and row["group"] == group
            ])
            for group in GROUPS
        ]
        selections.append(("合计", [row for row in rows if row["alphabet_size"] == size]))
        for label, selected in selections:
            post_local = sum(row["post_check"]["median_local_ms"] for row in selected)
            promote_local = sum(row["promote_to_p"]["median_local_ms"] for row in selected)
            post_eq = sum(row["post_check"]["eq"] for row in selected)
            promote_eq = sum(row["promote_to_p"]["eq"] for row in selected)
            post_cells = sum(row["post_check"]["table_cells"] for row in selected)
            promote_cells = sum(row["promote_to_p"]["table_cells"] for row in selected)
            lines.append(
                f"| {label} | {size} | {len(selected)} | "
                f"{fmt(post_local)}/{fmt(promote_local)} | "
                f"{fmt(promote_local - post_local)} | {post_eq}/{promote_eq} | "
                f"{post_eq - promote_eq} | {post_cells:,}/{promote_cells:,} |"
            )
    return lines


def decision_count_table(rows: list[dict]) -> list[str]:
    """Count strategy choices under several assumed real EQ costs."""
    lines = [
        "| Assumed real EQ cost | Promote languages | Post languages | Inconclusive |",
        "|---:|---:|---:|---:|",
    ]
    for cost in EQ_COST_LINES:
        choices = [strategy_at_cost(row, cost) for row in rows]
        lines.append(
            f"| {cost} ms/EQ | {choices.count('promote')} | "
            f"{choices.count('post')} | {choices.count('inconclusive')} |"
        )
    return lines


def render_report(
    grouped: dict[str, list[dict]],
    environment: dict,
    discarded: list[dict],
    experiment_date: str,
) -> str:
    """Render the Chinese experiment report."""
    rows = sum((grouped[group] for group in GROUPS), [])
    repeat_text = ", ".join(
        f"{GROUP_LABELS_ZH[group]} {grouped[group][0]['repeats']} 次"
        for group in GROUPS
    )
    lines = [
        "# Post 与 Promote 主决策图实验",
        "",
        f"实验日期：{experiment_date}",
        f"代码版本：`{environment.get('git_revision', 'unknown')} + 本次统计修改`",
        f"平台：`{environment.get('platform', 'unknown')}`",
        f"处理器：`{environment.get('processor', 'unknown')}`",
        f"Python：`{environment.get('python', 'unknown')}`",
        "",
        "## 1. 新图表的目的",
        "",
        "主决策图不再比较单纯的 EQ 比率和 Cells 比率，而是直接比较 Promote 的收益与代价。每个点代表一个目标语言。",
        "",
        "横轴定义为：",
        "",
        "$$",
        "\\Delta EQ = EQ_{Post}-EQ_{Promote}",
        "$$",
        "",
        "它表示 Promote 实际节省了多少次 EQ。点越靠右，Promote 的外部查询优势越大。",
        "",
        "纵轴定义为：",
        "",
        "$$",
        "\\Delta T_{local}=T_{Promote,local}-T_{Post,local}",
        "$$",
        "",
        "其中每次运行都直接计算：",
        "",
        "$$",
        "T_{local}^{(i)}=T_{total}^{(i)}-T_{EQ}^{(i)}",
        "$$",
        "",
        "然后对 local 样本自身取中位数。纵轴大于零表示 Promote 付出了更多本地计算，纵轴小于零表示 Promote 本地计算也更快。",
        "",
        "## 2. 决策线与判断规则",
        "",
        "假设真实环境中一次 EQ 的平均成本为 $C$ ms，则两种策略的边界是：",
        "",
        "$$",
        "\\Delta T_{local}=C\\,\\Delta EQ",
        "$$",
        "",
        "图中分别绘制 $C=1,10,100,300$ ms/EQ 的决策线。对于给定的 $C$：",
        "",
        "- 点在线下方：Promote 节省的 EQ 成本超过其额外本地成本，Promote 更优。",
        "- 点在线上方：额外本地成本尚未被 EQ 节省抵消，Post 更优。",
        "- 右下象限：Promote 同时减少 EQ 且降低本地时间，Promote 严格占优。",
        "- 左上象限：Promote 同时增加 EQ 和本地时间，Post 严格占优。",
        "",
        "单语言盈亏平衡成本定义为：",
        "",
        "$$",
        "C^*=\\frac{\\Delta T_{local}}{\\Delta EQ}",
        "$$",
        "",
        "当真实 EQ 成本高于 $C^*$ 时 Promote 更合适。$C^*$ 是平台相关的工程指标，不是语言固定不变的理论性质。",
        "",
        "## 3. 实验方法",
        "",
        f"- 两个性质分类共完成 {len(rows)} 个分类用例；其中 100 个语言同时属于 Commutative 和 Star-free，按最小 DFA 去重后共有 380 个不同语言。正式重复次数为：{repeat_text}。",
        f"- 每个分类生成 240 个候选语言；超过 600 秒或验证失败的用例共 {len(discarded)} 个，并记录在 `benchmark_data/discarded_cases.json`。",
        "- Commutative 套件覆盖单字母模计数、截断阈值、精确计数、长度模、包含性、模计数直积和阈值直积；每个目标均实际审计 syntactic monoid 的交换性。",
        "- Star-free 套件覆盖阈值/有限计数、首尾判定、固定子串、固定后缀、有限单词和有序块；每个目标均实际审计 syntactic monoid 的 aperiodicity。",
        "- 两个分类是语言性质而不是互斥分区，交集语言在各组中独立计时；组内不存在重复的最小 DFA。",
        "- 每个用例先各预热一次，并在正式测量中交替策略顺序。",
        "- `gc.collect()` 在计时开始前执行；目标 DFA、Oracle 构造和最终额外正确性验证不计入 learner 时间。",
        "- 每次运行保存 total、EQ、local 和 Monoid Check 原始时间样本。",
        "- 表格报告 local 中位数及四分位区间；图中误差棒为独立样本 bootstrap 的中位数差 95% 区间。",
        "- 给定 EQ 成本后，只有误差棒整体位于决策线下方/上方时才分别判为 Promote/Post；误差棒穿过决策线时记为 Inconclusive。",
        "- 所有运行验证最终语言等价、学习状态数等于目标 syntactic monoid 大小，且 Promote 不执行 Monoid Consistency Check。",
        "",
        "原始 JSON 位于 [`benchmark_data/`](benchmark_data/)，图位于 [`figures/`](figures/)。",
        "",
        "## 4. 一些说明",
        "",
        "### 4.1 本轮为何暂不计算 MQ 的外部代价",
        "",
        "本轮主决策图只把 EQ 作为可变的外部查询成本，没有把 MQ 次数乘以某个假设的单次 MQ 价格。这样处理不是认为 MQ 永远免费，也不是认为两种策略在所有语言上的 MQ 必然相同，而是因为本轮选取的低到中等复杂度 Commutative 与 Star-free 用例中，两种策略的 MQ 次数在逐语言层面高度接近。",
        "",
        "480 个分类用例中，有 402 个用例的 MQ 完全相同，467 个用例的差距不超过 1 次，逐语言绝对差的中位数为 0。最大的异常项 `comm_contains_all_abcd` 为 Post/Promote 10,319/6,954；去掉这一项后，其余 479 个分类用例的 MQ 总数为 63,192/63,203，仅相差 11 次。因此，本轮先把 MQ 视为近似受控变量，集中观察 Promote 节省 EQ 所获得的收益，以及扩大 `P` 和 Cells 带来的本地时间与空间代价。MQ 原始计数仍完整保存在 JSON 和逐语言表格中，并未从实验数据中删除。",
        "",
        "这一近似只适用于本轮样本，不能推广为 Commutative 或 Star-free 语言的一般性质。此前的复杂 Commutative 实验包含规模 35 至 99 的计数器组合，单个语言的 MQ 差距曾达到 +30,671 或 -12,432；在那些旧样本中，显著分叉主要出现在多个模计数器或阈值计数器与模计数器的析取组合中。相比之下，本轮 Commutative 的最大 syntactic monoid 只有 16，Star-free 的最大值只有 12。因此，复杂 Commutative 语言中的 MQ 分叉、查询长度和真实 MQ 成本需要在后续实验中按 monoid 规模与构造类型进一步研究。本报告末尾保留了相应的 MQ 成本建模与仿真方案。",
        "",
        "### 4.2 本轮实现使用的缓存",
        "",
        "按当前代码中的具体容器计算，Learner 侧共有 9 个可复用结构：`query_cache`、`table`、`row_cache`、`suffix_row_cache`、`sorted_p_cache`、`sorted_s_cache`、`sorted_i_cache`、`right_extensions_cache`，以及 Post 在单次 Monoid Check 中创建的局部 `context_cache`。此外还有 3 个增量填表标记；Oracle 侧有 1 个目标 syntactic monoid 预计算缓存。下面按实际调用过程逐项说明。需要注意，`table` 更准确地说是观察表的物化存储；它是否应继续保留的问题单独记录在第 11 节。",
        "",
        "#### 4.2.1 `query_cache`：完整字符串的 MQ 总缓存",
        "",
        "键是提交给 Teacher 的完整字符串 `w`，值是 `MQ(w)` 的布尔答案。填表、构造接受状态、反例二分和 Monoid Check 的补充查询全部经过 `Learner._ask_teacher(w)`：命中时直接返回；未命中时才调用 `teacher.membership_query(w)`、保存答案并把 `mq_count` 加一。因此实验 JSON 中的 MQ 表示真正到达 Teacher 的唯一字符串数，不是内部读取次数。",
        "",
        "例如多个观察表坐标都拼出字符串 `ab` 时，`query_cache` 中仍只有 `query_cache['ab']` 一项。成员关系不会因为 `P`、`I`、`S` 扩张而改变，所以它无需按表结构失效。该字典在 `Learner.__init__()` 中创建，生命周期覆盖整个 Learner 实例；本实验每个计时样本都新建 Learner 且只调用一次 `learn()`，因此不同策略、预热和重复测量之间不共享 MQ 答案。",
        "",
        "#### 4.2.2 `table`：三维观察表的物化单元格",
        "",
        "键是 `(i,p,s)`，值是 $MQ(pis)$。`_fill_cell(i,p,s)` 只在该三元组尚不存在时调用 `_ask_teacher(p+i+s)`。它让代码能够按理论观察表的坐标构造行、输出 debug 快照、判断哪些行列已填充并用 `len(table)` 统计 Cells。",
        "",
        "`table` 和 `query_cache` 的去重层次不同：前者区分结构坐标，后者区分最终字符串。`(i='ab',p='',s='')` 与 `(i='b',p='a',s='')` 都查询 `ab`，所以 table 中有两个 Cells，而 `query_cache` 中只有一个 MQ。`P`、`I`、`S` 扩张时，旧单元格不会失效，table 只继续增长。本结构主要提供观察表物化和实现便利，并不进一步减少真实 MQ；第 11 节给出了删除它的静态分析和原型验证。",
        "",
        "#### 4.2.3 `row_cache`：当前 $P\\times S$ 下的完整状态行",
        "",
        "键是字符串 `i`，值是按稳定的 `P`、`S` 顺序组成的布尔元组：",
        "",
        "$$",
        "row(i)=\\big(MQ(pis)\\big)_{p\\in P,\\,s\\in S}.",
        "$$",
        "",
        "例如 `P={ε,a}`、`S={ε,b}` 时，`row_cache['a']` 保存由 $MQ(a)$、$MQ(ab)$、$MQ(aa)$、$MQ(aab)$ 组成的整行。它不减少 Teacher MQ，而是避免 closed 检查、代表元选择、状态映射、转移构造和 Monoid Check 准备阶段反复遍历 $P\\times S$、拼接字符串并重新组装同一个元组。",
        "",
        "只要 `P` 或 `S` 改变，行的坐标或维度就改变，`row_cache` 必须整体清空；`I` 增加只会带来新的行，不改变旧字符串的行，因此无需清空旧缓存。删除三维 table 后，`row_cache` 仍然有明确价值，并会成为 `query_cache` 之上的主要结构缓存。",
        "",
        "#### 4.2.4 `suffix_row_cache`：right consistency 使用的经典后缀行",
        "",
        "键同样是 `i`，值只包含空左语境下的经典 L-star 行：",
        "",
        "$$",
        "row_S(i)=\\big(MQ(is)\\big)_{s\\in S}.",
        "$$",
        "",
        "right consistency 先比较两个 `I` 元素的 `row_S`，再比较它们右接字母后的 `row_S`，因此同一行会在状态对和字母循环中被反复读取。该缓存避免重复组装这些后缀向量。它只依赖 `S`：新增 `S` 时整体清空；新增 `P` 不改变经典后缀行，所以不应清空；新增 `I` 也不影响已经存在的行。",
        "",
        "#### 4.2.5 `sorted_p_cache`：P 的稳定遍历顺序",
        "",
        "值是 `tuple(sorted(P))`。`P` 本身是集合，直接遍历没有适合行向量比较的稳定顺序；缓存后的元组既避免在多层循环里反复排序，也保证所有 `row(i)` 使用完全相同的坐标顺序。它在 `P` 改变时置为 `None`，下一次读取时重建。Promote 会频繁把 `I` 代表元加入 `P`，因此该缓存及完整 `row_cache` 在 Promote 中通常比 Post 更频繁失效。",
        "",
        "#### 4.2.6 `sorted_s_cache`：S 的稳定遍历顺序",
        "",
        "值是 `tuple(sorted(S))`，用于完整 row、经典后缀 row、right consistency 和 Monoid Check。它保证不同字符串的第 k 个行分量始终对应同一个后缀。只在 `S` 新增区分后缀时失效；`P` 或 `I` 的变化不会影响它。",
        "",
        "#### 4.2.7 `sorted_i_cache`：I 的稳定代表元顺序",
        "",
        "值是按“先字符串长度、后字典序”排列的 `I` 元组。它用于枚举 right consistency 的状态对、建立 row 到代表元的映射、枚举 Monoid Check 左语境，并使同一 row 优先选择较短且可复现的代表串。只在 `I` 增加新元素时失效；`P`、`S` 改变会改变 row 的内容，但不会改变 `I` 自身的排序。",
        "",
        "#### 4.2.8 `right_extensions_cache`：边界集合 $I\\cdot\\Sigma$",
        "",
        "值是集合 $\\{ia\\mid i\\in I,a\\in\\Sigma\\}$。它定义 observation table 的 lower rows，也是 closed 检查和 debug 表格边界部分的输入。构造这一集合需要遍历全部 `I` 和字母表，因此在多个阶段复用。它只依赖 `I` 和固定字母表：`I` 改变时失效，`P` 或 `S` 改变时保持有效。",
        "",
        "#### 4.2.9 `context_cache`：Post 单次 Monoid Check 的语境缓存",
        "",
        "每次 `ensure_monoid_consistency()` 都创建一个新的局部字典，键是 `(left,middle,suffix)`，值是 $MQ(left\\,middle\\,suffix)$。它在同一轮检查多个边界与代表元时复用已经计算的语境答案。读取顺序是：先查该局部字典，再尝试已有 table 单元格或移位后的 $p=\\varepsilon$ 单元格，最后才进入全局 `query_cache`/Teacher。",
        "",
        "如果检查找到不一致并把新的左语境加入 `P`，本轮立即结束；下一次 Monoid Check 会重建 `context_cache`，因为检查阶段和候选关系已经改变。不过真实 MQ 答案仍保留在全局 `query_cache` 中。Promote 不执行 Monoid Consistency Check，因此完全不创建这一局部缓存。",
        "",
        "#### 4.2.10 Oracle 的目标 monoid 预计算缓存",
        "",
        "Oracle 构造时从最小目标 DFA 计算一次 `target_monoid_size` 和 `target_monoid_elements`。本实验用它审计 Commutative 的交换性、Star-free 的 aperiodicity，并验证最终学习状态数。该计算发生在 learner 计时之外；同一语言的两种策略、预热和正式重复共用同一个 Oracle，所以不会重复生成目标 monoid。",
        "",
        "它不缓存 MQ 或 EQ 答案：`membership_query(w)` 仍由目标 DFA 判定；每次 EQ 仍重新计算目标与假设的对称差。",
        "",
        "#### 4.2.11 三个增量填表标记",
        "",
        "- `filled_rows` 记录已经按当时 $P\\times S$ 填过的 `I\\cup I\\Sigma` 行；新增 `I` 后只识别并填充新行。",
        "- `processed_P` 保存上次填表结束时的 `P`；下一轮通过 `P-processed_P` 找到新左语境，只补对应的新列。",
        "- `processed_S` 保存上次填表结束时的 `S`；下一轮通过 `S-processed_S` 找到新区分后缀，只补对应的新列。",
        "",
        "这三个集合不保存 MQ 答案，而是维护物化 table 的增量进度。如果第 11 节提出的 table 删除方案实施，它们和五个填表辅助方法也可以一起删除。",
        "",
        "#### 4.2.12 不属于结果缓存的结构",
        "",
        "`state_to_rep` 保存假设状态名到代表字符串的语义映射，供反例轨迹定位使用，不是性能缓存。EQ 也没有跨轮缓存：每次都重新构造对称差并用 BFS 找最短反例，BFS 的 `visited` 只在当前一次 EQ 内存在。Post 和 Promote 共同使用 `query_cache`、row/suffix row、排序视图和右扩展缓存；Promote 额外扩大物化 table，Post 则独有单轮 `context_cache`。因此缓存结构会影响本地时间和空间，但不会改变 Teacher 的语言答案。",
        "",
        "## 5. 分组汇总",
        "",
        *group_summary(grouped),
        "",
        "### 5.1 按字母表大小分层",
        "",
        "字母表大小不再作为独立语言组，而是作为所有语言共有的实验维度。",
        "",
        *alphabet_summary(rows),
        "",
        "## 6. 不同 EQ 成本下的策略选择",
        "",
        *decision_count_table(rows),
        "",
        "这一表格只代入 EQ 成本，暂时把 MQ 的外部成本视为相同或可忽略。若真实 MQ 也昂贵，应进一步加入 $\\Delta MQ\\cdot C_{MQ}$。Inconclusive 表示 bootstrap 95% 区间与决策线相交，并不表示两种策略已被证明等价。",
        "",
        "## 7. 各语言统计数据",
        "",
        "`Local IQR` 为 `[Q1, Q3]`；`ΔEQ` 为 Post 减 Promote；`ΔLocal` 为 Promote 减 Post。",
        "",
    ]
    for index, group in enumerate(GROUPS, 1):
        lines.extend([
            f"### 7.{index} {GROUP_LABELS_ZH[group]}",
            "",
            *detailed_table(grouped[group]),
            "",
        ])

    finite = [row for row in rows if row["break_even_eq_ms"] is not None]
    lowest = sorted(finite, key=lambda row: row["break_even_eq_ms"])[:5]
    highest = sorted(finite, key=lambda row: row["break_even_eq_ms"], reverse=True)[:5]
    post_local = sum(row["post_check"]["median_local_ms"] for row in rows)
    promote_local = sum(row["promote_to_p"]["median_local_ms"] for row in rows)
    post_eq = sum(row["post_check"]["eq"] for row in rows)
    promote_eq = sum(row["promote_to_p"]["eq"] for row in rows)
    post_cells = sum(row["post_check"]["table_cells"] for row in rows)
    promote_cells = sum(row["promote_to_p"]["table_cells"] for row in rows)
    saved_eq = post_eq - promote_eq
    zero_saved_eq = sum(row["saved_eq"] == 0 for row in rows)
    decisions_at_1 = [strategy_at_cost(row, 1) for row in rows]
    decisions_at_10 = [strategy_at_cost(row, 10) for row in rows]
    lines.extend([
        "## 8. 初步结论",
        "",
        f"- 480 个分类用例合计中，Promote 把 EQ 从 {post_eq:,} 次降到 {promote_eq:,} 次，节省 {saved_eq:,} 次（{saved_eq / post_eq:.1%}）；与此同时，local 中位时间之和从 {fmt(post_local)} ms 增至 {fmt(promote_local)} ms，增加 {((promote_local / post_local) - 1):.1%}。按聚合量计算，只要一次真实 EQ 的平均成本高于 {fmt((promote_local - post_local) / saved_eq)} ms，节省的 EQ 就足以抵消这部分本地时间。",
        f"- Promote 的最终 Cells 总量是 Post 的 {promote_cells / post_cells:.2f} 倍（{post_cells:,}/{promote_cells:,}），但 local 时间仅为 {promote_local / post_local:.2f} 倍。这说明本实验规模内的表膨胀没有按 Cells 比例等幅转化为运行时间，不过它仍是更大 monoid 或更长查询下的主要风险指标。",
        f"- 当真实 EQ 成本取 1 ms 时，bootstrap 95% 规则明确支持 Promote/Post 的用例分别为 {decisions_at_1.count('promote')}/{decisions_at_1.count('post')}，另有 {decisions_at_1.count('inconclusive')} 个无法区分；成本升至 10 ms 时分别为 {decisions_at_10.count('promote')}/{decisions_at_10.count('post')}/{decisions_at_10.count('inconclusive')}。因此 Promote 的优势主要来自 EQ 变昂贵，但并非所有语言都能据此判定。",
        f"- 有 {zero_saved_eq} 个分类用例的两种策略 EQ 数相同；对这些点，提高假设 EQ 成本不会改变决策。误差区间穿过决策线的语言也被保留为 Inconclusive，避免把本地计时噪声解释成策略优势。",
        "- 字母表大小分层表展示的是不同用例组合下的绝对总量，不是控制其他变量后的因果效应。由于各层样本数和语言族构成不同，不能仅凭总时间随字母表增大就断言字母表大小本身导致某种策略退化。",
        "",
        "最容易由 Promote 获益的五个语言（按 $C^*$ 从低到高）：",
        "",
        *[f"- `{row['case']}`：{render_break_even(row)} ms/EQ" for row in lowest],
        "",
        "最需要昂贵 EQ 才能由 Promote 获益的五个语言：",
        "",
        *[f"- `{row['case']}`：{render_break_even(row)} ms/EQ" for row in highest],
        "",
        "主图用于在给定 EQ 成本下做策略决策；低成本区域放大图用于观察被极端大 monoid 案例压缩的小型语言。由于纵轴是平台时间，更换机器后应重跑本实验，而横轴 ΔEQ 和结构计数通常更稳定。",
        "",
        "## 9. 主决策图",
        "",
        "![主决策图](figures/main_decision_map.svg)",
        "",
        "### 中心低成本区域放大",
        "",
        "![主决策图低成本区域](figures/main_decision_map_zoom.svg)",
        "",
        "## 10. 后续实验提案：MQ 成本建模与仿真",
        "",
        "### 10.1 当前结论的边界",
        "",
        "以下提案继承自上一轮实验，并按本轮目录结构保留在报告末尾。上一轮主决策图只展开了 EQ 成本，其简化成本模型为：",
        "",
        "$$",
        "T_{strategy}=T_{local}+C_{EQ}N_{EQ}",
        "$$",
        "",
        "这相当于假设 MQ 的外部成本可忽略，或两种策略的 MQ 差异足够小。上一轮 56 个语言中，Post/Promote 的 MQ 总数为 1,163,767/1,166,812，总量仅差约 0.26%，并有 38 个用例的 MQ 完全相同。然而，这个总量接近是不同语言的正负差异抵消后的结果：单个复杂语言中，Promote 可能多出 30,671 次 MQ，也可能减少 12,432 次 MQ。因此，“MQ 整体接近”是值得继续研究的实验现象，还不能当作一般性结论。",
        "",
        "上一轮的 1,168 次正式计时是对 56 个语言的重复测量；它们可以降低时间噪声，却不能替代更多独立语言样本。另外，当前精确 EQ 总是返回最短反例，虽然代码没有硬性限制 MQ 字符串长度，但这种理想反例机制会间接使 $I$、$P$、$S$ 和实际 MQ 偏短。当前 JSON 未记录 MQ 长度分布，因而尚无法分辨某个策略的 MQ 是“次数更多”还是“字符串更长”。",
        "",
        "### 10.2 下一轮需新增的原始统计",
        "",
        "应在 `Learner._ask_teacher()` 的缓存未命中分支上，围绕真正的 `teacher.membership_query()` 调用记录 MQ 时间和字符串长度。缓存命中不应计入外部 MQ 次数或 MQ 时间。每次运行至少保存：",
        "",
        "- `mq_count`：缓存未命中后真正调用 Teacher 的次数；",
        "- `mq_ms`：当前理想 Oracle 处理这些 MQ 的累计时间；",
        "- `mq_total_word_length`：所有真实 MQ 字符串长度之和；",
        "- `mq_max_word_length`：最长 MQ 字符串长度；",
        "- `mq_length_histogram`：按长度或长度区间统计的查询分布；",
        "- `mq_logical_requests` 和 `mq_cache_hits`：可选的补充指标，用于区分表读取次数与真正外部查询。",
        "",
        "计时应进一步拆分为：",
        "",
        "$$",
        "T_{internal}=T_{total}-T_{MQ,ideal}-T_{EQ,ideal}",
        "$$",
        "",
        "其中 $T_{internal}$ 只保留观察表维护、closed/right consistency/Monoid Check、反例处理和构造假设等学习器内部计算。对 `total_ms`、`mq_ms`、`eq_ms` 和 `internal_ms` 都应保留逐次原始样本、中位数和 IQR。当前 DFA Oracle 的 MQ 可能快到与 `perf_counter()` 调用开销同量级，因此实测 `mq_ms` 主要用于从本地时间中分离理想 MQ，不应直接视为真实环境的 MQ 成本。",
        "",
        "### 10.3 完整的查询成本模型",
        "",
        "对任意策略，真实成本应写为：",
        "",
        "$$",
        "T_{strategy}=T_{internal}+C_{MQ}N_{MQ}+C_{EQ}N_{EQ}",
        "$$",
        "",
        "定义 Promote 节省的查询数和其额外内部计算为：",
        "",
        "$$",
        "\\Delta MQ=MQ_{Post}-MQ_{Promote},\\qquad \\Delta EQ=EQ_{Post}-EQ_{Promote}",
        "$$",
        "",
        "$$",
        "\\Delta T_{internal}=T_{Promote,internal}-T_{Post,internal}",
        "$$",
        "",
        "则 Promote 更优的条件是：",
        "",
        "$$",
        "\\Delta T_{internal}<C_{MQ}\\Delta MQ+C_{EQ}\\Delta EQ",
        "$$",
        "",
        "固定 MQ 成本是最简单也有价值的基线。下一轮应至少代入 $C_{MQ}=0,0.01,0.1,1,10$ ms/MQ，对比每个语言的策略选择如何随 MQ 成本变化。这是敏感性分析，不是宣称真实 MQ 必然等于其中某一个固定值。",
        "",
        "### 10.4 考虑字符串长度和网络抖动的 MQ 仿真",
        "",
        "更真实的单次 MQ 成本可以建模为：",
        "",
        "$$",
        "C_{MQ}(w)=\\alpha+\\beta|w|+\\varepsilon",
        "$$",
        "",
        "其中 $\\alpha$ 是每次调用的固定网络/服务延迟，$\\beta$ 是每个字符的传输或处理成本，$\\varepsilon$ 是网络抖动。对一种策略：",
        "",
        "$$",
        "T_{MQ}=\\alpha N_{MQ}+\\beta\\sum_{w\\in MQ}|w|+\\sum_w\\varepsilon_w",
        "$$",
        "",
        "建议实现一个“虚拟成本仿真器”，Teacher 继续立即返回正确答案，仿真器只根据查询长度和随机种子累加虚拟 MQ 成本，不应通过 `time.sleep()` 真实等待。使用虚拟时间可以在不延长数百万次查询实验的前提下，可复现地测试大量参数组合。",
        "",
        "对当前同步学习器，MQ 延迟不会改变 Teacher 的答案，因而完成一次真实学习并保存 MQ 长度直方图后，大多数加性成本模型都可以离线重放，不必为每一组 $\\alpha$、$\\beta$、$C_{EQ}$ 重新运行 learner。只有当未来引入超时、总预算、并行/批量查询或基于时间的自适应决策时，查询顺序和延迟才会反过来改变学习轨迹。",
        "",
        "仿真场景可以先覆盖：",
        "",
        "| Scenario | $\\alpha$ | $\\beta$ | Interpretation |",
        "|---|---:|---:|---|",
        "| Local DFA | 0.001 ms | 0.0001 ms/char | 几乎无外部成本 |",
        "| Local service | 0.1 ms | 0.001 ms/char | 进程或本地服务调用 |",
        "| LAN teacher | 1 ms | 0.005 ms/char | 低延迟远程 Teacher |",
        "| WAN teacher | 30 ms | 0.01 ms/char | 网络往返占主导 |",
        "| Human/expensive teacher | 1,000 ms | approximately 0 | 每次询问本身昂贵 |",
        "",
        "这些数值只是覆盖不同量级的初始情景，应在报告中明确标记为假设参数。对带抖动的场景，可使用固定随机种子和长尾分布进行 Monte Carlo 重放，报告模拟总时间的中位数、95% 区间，以及 Promote/Post 的获胜概率。",
        "",
        "### 10.5 新的决策图与实验顺序",
        "",
        "固定某个 $C_{MQ}$ 后，可定义 MQ 修正后的纵轴：",
        "",
        "$$",
        "y_{adjusted}=\\Delta T_{internal}-C_{MQ}\\Delta MQ",
        "$$",
        "",
        "横轴仍为 $x=\\Delta EQ$，对给定 $C_{EQ}$ 的决策线仍为：",
        "",
        "$$",
        "y_{adjusted}=C_{EQ}x",
        "$$",
        "",
        "当 Promote 减少 MQ 时，$\\Delta MQ>0$，数据点会向下移动；当 Promote 增加 MQ 时，点会向上移动。建议分别为多个 $C_{MQ}$ 画分面图，并增加 $\\Delta EQ$-$\\Delta MQ$ 查询平衡散点图。每个语言的表格应同时列出 MQ Post/Promote、$\\Delta MQ$、MQ 总字符数、长度分位数、internal Post/Promote、$\\Delta T_{internal}$、EQ Post/Promote 和 $\\Delta EQ$。",
        "",
        "下一轮实验建议按以下顺序进行：",
        "",
        "1. 实现 MQ 时间、查询长度、逻辑请求和缓存命中统计；",
        "2. 先重跑相同 56 个语言，与本轮结果建立可比的新基线；",
        "3. 用固定 $C_{MQ}$ 完成第一轮敏感性分析；",
        "4. 实现 $\\alpha+\\beta|w|+\\varepsilon$ 虚拟成本重放，扫描 MQ/EQ 参数网格；",
        "5. 增加更多独立语言，按 DFA 大小、syntactic monoid 大小、字母表大小、最短反例/区分后缀长度分层取样；",
        "6. 引入随机/PAC EQ 后再测试非最短反例和预算限制；",
        "7. 最后使用小型 HTTP Teacher 进行少量真实网络实验，用于校准而非取代参数化仿真。",
        "",
        "这一设计将算法本身产生的 $T_{internal}$、MQ 次数/长度和 EQ 次数，与外部环境的 MQ/EQ 成本分开。因此不必假定存在一个唯一正确的“真实 MQ 时间”，而是可以给出 Promote 和 Post 在不同查询成本区域中的适用边界。",
        "",
        "## 11. 本地的缓存策略问题",
        "",
        "### 11.1 learner.py 中的三维 table",
        "",
        "第 4 节按当前代码中的具体容器把 **table** 列入了缓存清单。进一步审查后，更准确的定义是：table 是理论观察表的物化存储，而不是负责减少真实 MQ 的主缓存。真正按完整字符串去重 Teacher 调用的是 **query_cache**；table 以 (i,p,s) 为键再次保存同一个布尔答案，用于显式表示观察表坐标。",
        "",
        "当前实现始终满足：",
        "",
        "$$",
        "table[(i,p,s)] = query\\_cache[p+i+s]",
        "$$",
        "",
        "原因是 table 的所有写入都经过 **_fill_cell()** 和 **_ask_teacher()**，而 _ask_teacher() 会在返回前把答案写入 query_cache；在同一个 Learner 实例中，query_cache 的生命周期不短于 table。不同的 (i,p,s) 可能拼出同一个完整字符串，于是 table 保存多个坐标和多份相同布尔值，而 query_cache 只保留一个字符串答案。前者没有进一步减少 MQ，只提供观察表物化、增量填表、debug 输出和 Cells 统计方面的编程便利。",
        "",
        "### 11.2 无 table 原型验证",
        "",
        "本轮使用不修改项目文件的内存子类做了对照：取消 fill_table()，让 get_row()、get_suffix_row() 和 Monoid Check 直接通过 _ask_teacher() 读取 query_cache。四个代表语言、两种策略的结果如下；每一行还验证了最终语言、完整 query_cache 键值集合和最终 P/I/S 均一致。",
        "",
        "| Case | Strategy | MQ 原版/无 table | EQ 原版/无 table | Cells 原版/理论值 |",
        "|---|---|---:|---:|---:|",
        "| comm_mod_ab_a_5 | Post | 49/49 | 4/4 | 44/44 |",
        "| comm_mod_ab_a_5 | Promote | 50/50 | 2/2 | 220/220 |",
        "| comm_contains_all_abcd | Post | 10,319/10,319 | 15/15 | 975/975 |",
        "| comm_contains_all_abcd | Promote | 6,954/6,954 | 4/4 | 10,400/10,400 |",
        "| sf_contains_ab_aba | Post | 307/307 | 3/3 | 225/225 |",
        "| sf_contains_ab_aba | Promote | 319/319 | 2/2 | 900/900 |",
        "| at_least_6_a_or_b_mod_7 | Post | 24,105/24,105 | 16/16 | 1,392/1,392 |",
        "| at_least_6_a_or_b_mod_7 | Promote | 31,424/31,424 | 5/5 | 78,561/78,561 |",
        "",
        "这组对照覆盖普通模计数、本轮最大交换语言、Star-free 子串语言和 syntactic monoid 大小为 43 的旧复杂交换语言。静态数据流和原型结果都支持同一判断：主 Learner 的三维 table 可以删除而不改变语言、MQ、EQ 或学习轨迹。",
        "",
        "### 11.3 删除时需要同步调整的内容",
        "",
        "- get_row(i) 直接按当前 $P\\times S$ 顺序调用 _ask_teacher(p+i+s)，并继续由 row_cache 保存最终行向量。",
        "- get_suffix_row(i) 直接调用 _ask_teacher(i+s)，并继续由 suffix_row_cache 保存经典后缀行。",
        "- Monoid Check 删除两条 table.get(...) 捷径，统一通过 _ask_teacher(left+middle+suffix) 访问全局 MQ 缓存；局部 context_cache 可先保留，另行评估。",
        "- Debug 快照根据当前 P、I、S 动态生成逻辑观察表，不再读取物化字典。",
        "- filled_rows、processed_P、processed_S 及 _fill_cell()、fill_table()、fill_row()、fill_prefix_column()、fill_suffix_column() 可随物化表一起删除。",
        "- 实验中的 Cells 改为理论规模 $|I\\cup I\\Sigma|\\cdot|P|\\cdot|S|$。由于 I、P、S 只增不减，且当前终止时的物化表完整，原型中该公式与 len(table) 完全一致；历史 JSON 不需要回写。",
        "",
        "删除后的明确收益是降低内存占用和实现复杂度，尤其避免 Promote 为大量不同三元组分配重复布尔值和体积较大的 tuple/dict 项。本地时间不应在实现前预判：无 table 后会增加部分字符串拼接和 query_cache 查找，同时减少三元组构造、哈希和大字典维护，最终差异需要用同一批语言重新基准测试。",
        "",
        "这一结论只适用于主算法 learner.py。classic_lstar_learner.py 没有独立的全局 query_cache，其中二维 table 同时承担 MQ 去重职责，不能随主 Learner 的三维表直接删除。当前状态为“调查完成、尚未实施”，正式修改时应增加语言等价、MQ/EQ 轨迹、debug 快照和 Cells 口径的回归测试。",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    grouped, environment, discarded = load_experiment(args.input_dir)
    rows = sum((grouped[group] for group in GROUPS), [])
    figures = args.output_dir / "figures"
    render_decision_svg(rows, figures / "main_decision_map.svg")
    render_decision_svg(rows, figures / "main_decision_map_zoom.svg", zoom=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "REPORT.md").write_text(
        render_report(grouped, environment, discarded, args.output_dir.name[:10]),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
