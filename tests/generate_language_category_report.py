"""Generate a bilingual Markdown report from category benchmark JSON files."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
from pathlib import Path


GROUPS = ("commutative", "star_free", "alphabet_3")
EXTRA_GROUP = "complex_commutative"
GROUP_ZH = {
    "commutative": "交换语言",
    "star_free": "Star-free 语言",
    "alphabet_3": "三字母语言",
}
GROUP_EN = {
    "commutative": "Commutative",
    "star_free": "Star-free",
    "alphabet_3": "Three-letter alphabet",
}


def fmt(value: float) -> str:
    return f"{value:,.3f}"


def sums(rows: list[dict], strategy: str, key: str) -> float:
    return sum(row[strategy][key] for row in rows)


def wins(rows: list[dict]) -> tuple[int, int, int]:
    post = promote = close = 0
    for row in rows:
        ratio = row["promote_to_p"]["median_ms"] / row["post_check"]["median_ms"]
        if 0.95 <= ratio <= 1.05:
            close += 1
        elif ratio > 1:
            post += 1
        else:
            promote += 1
    return post, promote, close


def break_even(rows: list[dict]) -> float | None:
    """Return added average EQ cost needed for Promote to catch Post."""
    post_non_eq = sums(rows, "post_check", "median_ms") - sums(rows, "post_check", "eq_ms")
    promote_non_eq = (
        sums(rows, "promote_to_p", "median_ms")
        - sums(rows, "promote_to_p", "eq_ms")
    )
    saved_eq = sums(rows, "post_check", "eq") - sums(rows, "promote_to_p", "eq")
    if saved_eq <= 0:
        return None
    return max(0.0, (promote_non_eq - post_non_eq) / saved_eq)


def aggregate_table(data: dict[str, list[dict]], chinese: bool) -> list[str]:
    header = (
        "| 组别 | 用例数 | Post | Promote | Promote/Post | Post 胜 | Promote 胜 | 接近 |"
        if chinese
        else "| Group | Cases | Post | Promote | Promote/Post | Post wins | Promote wins | Close |"
    )
    lines = [header, "|---|---:|---:|---:|---:|---:|---:|---:|"]
    all_rows = []
    for group in GROUPS:
        rows = data[group]
        all_rows.extend(rows)
        post_time = sums(rows, "post_check", "median_ms")
        promote_time = sums(rows, "promote_to_p", "median_ms")
        post_wins, promote_wins, close = wins(rows)
        label = GROUP_ZH[group] if chinese else GROUP_EN[group]
        lines.append(
            f"| {label} | {len(rows)} | {fmt(post_time)} ms | "
            f"{fmt(promote_time)} ms | {promote_time / post_time:.2f}x | "
            f"{post_wins} | {promote_wins} | {close} |"
        )
    post_time = sums(all_rows, "post_check", "median_ms")
    promote_time = sums(all_rows, "promote_to_p", "median_ms")
    post_wins, promote_wins, close = wins(all_rows)
    total_label = "合计" if chinese else "Total"
    lines.append(
        f"| {total_label} | {len(all_rows)} | {fmt(post_time)} ms | "
        f"{fmt(promote_time)} ms | {promote_time / post_time:.2f}x | "
        f"{post_wins} | {promote_wins} | {close} |"
    )
    return lines


def detail_table(rows: list[dict], chinese: bool) -> list[str]:
    if chinese:
        header = (
            "| 用例 | DFA | Monoid | Post ms | Promote ms | 比率 | "
            "MQ Post/Promote | EQ Post/Promote | Cells Post/Promote | "
            "P 大小 Post/Promote | I 大小 Post/Promote | S 大小 Post/Promote |"
        )
    else:
        header = (
            "| Case | DFA | Monoid | Post ms | Promote ms | Ratio | "
            "MQ Post/Promote | EQ Post/Promote | Cells Post/Promote | "
            "P size Post/Promote | I size Post/Promote | S size Post/Promote |"
        )
    lines = [header, "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        post = row["post_check"]
        promote = row["promote_to_p"]
        ratio = promote["median_ms"] / post["median_ms"]
        lines.append(
            f"| `{row['case']}` | {row['dfa_states']} | {row['monoid_states']} | "
            f"{fmt(post['median_ms'])} | {fmt(promote['median_ms'])} | {ratio:.2f}x | "
            f"{post['mq']:,}/{promote['mq']:,} | {post['eq']}/{promote['eq']} | "
            f"{post['table_cells']:,}/{promote['table_cells']:,} | "
            f"{post['p_size']}/{promote['p_size']} | "
            f"{post['i_size']}/{promote['i_size']} | "
            f"{post['s_size']}/{promote['s_size']} |"
        )
    return lines


def structure_table(data: dict[str, list[dict]], chinese: bool) -> list[str]:
    if chinese:
        header = (
            "| 组别 | MQ Post/Promote | EQ Post/Promote | EQ 耗时 Post/Promote | "
            "Post Monoid Check | Cells Post/Promote | Cells 比率 | "
            "P 大小之和 Post/Promote | I 大小之和 Post/Promote | "
            "S 大小之和 Post/Promote |"
        )
    else:
        header = (
            "| Group | MQ Post/Promote | EQ Post/Promote | EQ time Post/Promote | "
            "Post Monoid Check | Cells Post/Promote | Cell ratio | "
            "Sum of P sizes Post/Promote | Sum of I sizes Post/Promote | "
            "Sum of S sizes Post/Promote |"
        )
    lines = [header, "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    scopes = [(GROUP_ZH[g] if chinese else GROUP_EN[g], data[g]) for g in GROUPS]
    scopes.append(("合计" if chinese else "Total", sum((data[g] for g in GROUPS), [])))
    for label, rows in scopes:
        post_cells = sums(rows, "post_check", "table_cells")
        promote_cells = sums(rows, "promote_to_p", "table_cells")
        lines.append(
            f"| {label} | {sums(rows, 'post_check', 'mq'):,.0f}/"
            f"{sums(rows, 'promote_to_p', 'mq'):,.0f} | "
            f"{sums(rows, 'post_check', 'eq'):,.0f}/"
            f"{sums(rows, 'promote_to_p', 'eq'):,.0f} | "
            f"{fmt(sums(rows, 'post_check', 'eq_ms'))}/"
            f"{fmt(sums(rows, 'promote_to_p', 'eq_ms'))} ms | "
            f"{fmt(sums(rows, 'post_check', 'monoid_check_ms'))} ms | "
            f"{post_cells:,.0f}/{promote_cells:,.0f} | "
            f"{promote_cells / post_cells:.2f}x | "
            f"{sums(rows, 'post_check', 'p_size'):,.0f}/"
            f"{sums(rows, 'promote_to_p', 'p_size'):,.0f} | "
            f"{sums(rows, 'post_check', 'i_size'):,.0f}/"
            f"{sums(rows, 'promote_to_p', 'i_size'):,.0f} | "
            f"{sums(rows, 'post_check', 's_size'):,.0f}/"
            f"{sums(rows, 'promote_to_p', 's_size'):,.0f} |"
        )
    return lines


def break_even_table(data: dict[str, list[dict]], chinese: bool) -> list[str]:
    header = (
        "| 范围 | Promote 追平所需平均 EQ 成本 |"
        if chinese
        else "| Scope | Average EQ cost required for Promote to break even |"
    )
    lines = [header, "|---|---:|"]
    scopes = [(GROUP_ZH[g] if chinese else GROUP_EN[g], data[g]) for g in GROUPS]
    scopes.append(("全部 44 例" if chinese else "All 44 cases",
                   sum((data[g] for g in GROUPS), [])))
    for label, rows in scopes:
        threshold = break_even(rows)
        rendered = "无有限阈值" if chinese else "no finite threshold"
        if threshold is not None:
            rendered = f"{fmt(threshold)} ms / EQ"
        lines.append(f"| {label} | {rendered} |")
    return lines


def load_data(input_dir: Path) -> tuple[dict[str, list[dict]], dict[str, int]]:
    data = {}
    repeats = {}
    for group in (*GROUPS, EXTRA_GROUP):
        payload = json.loads((input_dir / f"{group}.json").read_text(encoding="utf-8"))
        if payload["mode"] != "benchmark":
            raise ValueError(f"{group}.json is not a formal benchmark")
        data[group] = payload["results"]
        repeats[group] = payload["repeats"]
    return data, repeats


def git_revision() -> str:
    try:
        revision = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        return f"{revision} + working tree changes" if dirty else revision
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def render_report(data: dict[str, list[dict]], repeats: dict[str, int]) -> str:
    total_runs = sum(len(data[group]) * 2 * (repeats[group] + 1) for group in GROUPS)
    all_rows = sum((data[group] for group in GROUPS), [])
    mq_delta = sums(all_rows, "promote_to_p", "mq") - sums(all_rows, "post_check", "mq")
    eq_saved = sums(all_rows, "post_check", "eq") - sums(all_rows, "promote_to_p", "eq")
    cells_ratio = (
        sums(all_rows, "promote_to_p", "table_cells")
        / sums(all_rows, "post_check", "table_cells")
    )
    commutative = data["commutative"]
    star_free = data["star_free"]
    alphabet_3 = data["alphabet_3"]
    alphabet_3_without_t4 = [
        row for row in alphabet_3 if row["case"] != "full_transformation_monoid_4"
    ]
    comm_time_ratio = (
        sums(commutative, "promote_to_p", "median_ms")
        / sums(commutative, "post_check", "median_ms")
    )
    star_time_ratio = (
        sums(star_free, "promote_to_p", "median_ms")
        / sums(star_free, "post_check", "median_ms")
    )
    alphabet_without_t4_ratio = (
        sums(alphabet_3_without_t4, "promote_to_p", "median_ms")
        / sums(alphabet_3_without_t4, "post_check", "median_ms")
    )
    alphabet_without_t4_cells = (
        sums(alphabet_3_without_t4, "promote_to_p", "table_cells")
        / sums(alphabet_3_without_t4, "post_check", "table_cells")
    )
    t4 = next(row for row in alphabet_3 if row["case"] == "full_transformation_monoid_4")
    t4_time_ratio = t4["promote_to_p"]["median_ms"] / t4["post_check"]["median_ms"]
    t4_cell_ratio = t4["promote_to_p"]["table_cells"] / t4["post_check"]["table_cells"]
    complex_commutative = data[EXTRA_GROUP]
    complex_runs = len(complex_commutative) * 2 * (repeats[EXTRA_GROUP] + 1)
    complex_post_time = sums(complex_commutative, "post_check", "median_ms")
    complex_promote_time = sums(complex_commutative, "promote_to_p", "median_ms")
    complex_ratio = complex_promote_time / complex_post_time
    complex_post_cells = sums(complex_commutative, "post_check", "table_cells")
    complex_promote_cells = sums(complex_commutative, "promote_to_p", "table_cells")
    complex_cell_ratio = complex_promote_cells / complex_post_cells
    complex_mq_delta = (
        sums(complex_commutative, "promote_to_p", "mq")
        - sums(complex_commutative, "post_check", "mq")
    )
    complex_eq_saved = (
        sums(complex_commutative, "post_check", "eq")
        - sums(complex_commutative, "promote_to_p", "eq")
    )
    complex_break_even = break_even(complex_commutative)
    lines = [
        "# `post_check` 与 `promote_to_p` 按语言类别性能对比",
        "",
        "实验日期：2026-07-28",
        f"代码版本：`{git_revision()}`",
        f"运行环境：{platform.system()}，Python {platform.python_version()}",
        "",
        "# 中文报告",
        "",
        "## 1. 实验目标",
        "",
        "本轮不再按规模分组，而是比较两种策略在三类语言上的行为：",
        "",
        "- 12 个交换语言：包含性、阈值计数、模计数以及交换计数器直积。",
        "- 12 个 star-free 语言：前后缀、子串、子序列、有限计数和模式规避。",
        "- 20 个三字母语言：字母表固定为 `{a,b,c}`，并加入少量较困难的群与变换幺半群案例。",
        "",
        "Runner 会直接审计交换语言的 syntactic monoid 是否交换，并审计 star-free",
        "组的 syntactic monoid 是否 aperiodic。",
        "",
        "## 2. 方法",
        "",
        f"- 交换语言和 star-free 语言各预热 1 次、正式运行 {repeats['commutative']} 次；",
        f"  三字母语言预热 1 次、正式运行 {repeats['alphabet_3']} 次。",
        "- 每次重复交替策略顺序，报告正式运行的中位数。",
        "- 每次运行验证最终语言等价、学习状态数等于目标 syntactic monoid 大小，",
        "  并断言 `promote_to_p` 的 Monoid Consistency Check 次数为 0。",
        f"- 基础三组共执行 {total_runs:,} 次 learner run，全部通过校验。",
        "",
        "原始数据：[commutative.json](benchmark_data/commutative.json)、"
        "[star_free.json](benchmark_data/star_free.json)、"
        "[alphabet_3.json](benchmark_data/alphabet_3.json)。",
        "每个用例都包含经语言等价验证的 `regex` 字段；表达式只使用连接、"
        "`|`、`*` 和括号，可选项与固定次数均已显式展开。",
        "复现实验脚本：[compare_language_categories.py](../../tests/compare_language_categories.py)。",
        "",
        "## 3. 总体结果",
        "",
        "组耗时是组内各用例中位耗时之和；差异在 5% 以内记为接近。",
        "",
        *aggregate_table(data, True),
        "",
        "## 4. 各组详细数据",
        "",
        "所有成对指标均按 `Post/Promote` 排列；比率为 Promote/Post。",
        "",
    ]
    for index, group in enumerate(GROUPS, 1):
        lines.extend([f"### 4.{index} {GROUP_ZH[group]}", "", *detail_table(data[group], True), ""])
    lines.extend([
        "## 5. 查询、表格与集合规模",
        "",
        *structure_table(data, True),
        "",
        f"全部用例中 Promote 相对 Post 的 MQ 差值为 {mq_delta:+,.0f}，"
        f"节省 EQ {eq_saved:,.0f} 次；最终表格单元总数为 Post 的 {cells_ratio:.2f} 倍。",
        "详细表中的 `|P|、|I|、|S|` 可以进一步区分表格膨胀来自左上下文、",
        "代表元还是后缀实验集合。",
        "",
        "## 6. 理想 EQ 与真实/PAC EQ",
        "",
        "当前 Oracle 持有完整目标 DFA，通过 symmetric difference 执行精确 EQ。",
        "这类 EQ 是理想的内存操作，不能代表黑盒一致性测试或 PAC 抽样的真实成本。",
        "",
        "采用成本模型：",
        "",
        "```text",
        "Adjusted time = measured non-EQ time + EQ count × C",
        "```",
        "",
        "其中 `C` 是一次真实 EQ 的平均成本。本轮数据给出的盈亏平衡点为：",
        "",
        *break_even_table(data, True),
        "",
        "阈值为 0 表示 Promote 的非 EQ 成本已经不高于 Post；“无有限阈值”表示",
        "Promote 没有减少 EQ，因此提高 EQ 成本也无法靠该项追平。",
        "",
        "## 7. 结论",
        "",
        f"1. **交换语言最有利于 Promote。** 组耗时是 Post 的 {comm_time_ratio:.2f} 倍，"
        f"即低约 {(1 - comm_time_ratio) * 100:.1f}%；MQ 完全相同，EQ 从 "
        f"{sums(commutative, 'post_check', 'eq'):.0f} 次降到 "
        f"{sums(commutative, 'promote_to_p', 'eq'):.0f} 次。代价是表格扩大到 "
        f"{sums(commutative, 'promote_to_p', 'table_cells') / sums(commutative, 'post_check', 'table_cells'):.2f} 倍。"
        "这支持了最初的观察：当 DFA 和 syntactic monoid 同步增长且结构交换时，"
        "提前把代表元放入 `P` 能较便宜地替代若干 EQ。",
        "",
        f"2. **Star-free 组总体持平。** Promote/Post 耗时比为 {star_time_ratio:.2f}，"
        f"EQ 只减少 {sums(star_free, 'post_check', 'eq') - sums(star_free, 'promote_to_p', 'eq'):.0f} 次，"
        f"而表格为 Post 的 "
        f"{sums(star_free, 'promote_to_p', 'table_cells') / sums(star_free, 'post_check', 'table_cells'):.2f} 倍。"
        "这组没有显示出稳定的单边优势。",
        "",
        f"3. **三字母组的总耗时被 256 元 full transformation monoid 明显主导。** "
        f"该例中 Promote 慢 {t4_time_ratio:.2f} 倍，表格正好扩大 {t4_cell_ratio:.0f} 倍，"
        "因为 `|P|` 从 4 增至 256。即使剔除该例，三字母组 Promote 仍慢 "
        f"{alphabet_without_t4_ratio:.2f} 倍，表格为 {alphabet_without_t4_cells:.2f} 倍，"
        "说明较大字母表与非交换结构会放大维护完整 `P` 的本地成本。",
        "",
        f"4. **大表不等于更多 MQ。** 本轮 Promote 总 MQ 反而少 {-mq_delta:,.0f} 次。"
        "差值来自部分三字母案例中更小的 `S`；全局字符串缓存又把大量不同表格坐标"
        "折叠到同一个 MQ。这说明需要把表格单元、唯一 MQ 和 `P/I/S` 分开报告。",
        "",
        f"5. **真实 EQ 成本可能改变总排名，但门槛取决于语言类别。** "
        f"全体用例的估算门槛是 {fmt(break_even(all_rows) or 0)} ms/EQ；"
        f"交换语言为 {fmt(break_even(commutative) or 0)} ms/EQ，"
        f"三字母组则为 {fmt(break_even(alphabet_3) or 0)} ms/EQ。"
        "因此下一轮 PAC 实验不应只报告平均值，还应按语言结构分别估计 teacher 成本。",
        "",
        "---",
        "",
        "# English Report",
        "",
        "## 1. Objective",
        "",
        "This benchmark compares the strategies by language category: 12 commutative",
        "languages, 12 star-free languages, and 20 languages over `{a,b,c}`.",
        "The runner validates commutativity and aperiodicity for the first two suites.",
        "",
        "## 2. Methodology",
        "",
        f"- Commutative and star-free cases use one warm-up plus {repeats['commutative']} measured runs.",
        f"- Three-letter cases use one warm-up plus {repeats['alphabet_3']} measured runs.",
        "- Strategy order alternates, and reported runtime is the median.",
        f"- {total_runs:,} learner runs in the three base groups passed validation.",
        "- Every JSON case includes a target-verified `regex` using concatenation, `|`, `*`, "
        "and parentheses only; optional and fixed-count syntax is explicitly expanded.",
        "",
        "## 3. Aggregate Results",
        "",
        *aggregate_table(data, False),
        "",
        "## 4. Detailed Results",
        "",
        "All paired metrics are ordered as `Post/Promote`; Ratio is Promote/Post.",
        "",
    ])
    for index, group in enumerate(GROUPS, 1):
        lines.extend([f"### 4.{index} {GROUP_EN[group]}", "", *detail_table(data[group], False), ""])
    lines.extend([
        "## 5. Query and Structure Summary",
        "",
        *structure_table(data, False),
        "",
        "## 6. Ideal EQ Versus Real/PAC EQ",
        "",
        "The current Oracle performs exact in-memory EQ by DFA symmetric difference.",
        "Using `Adjusted time = measured non-EQ time + EQ count × C`, the estimated",
        "break-even costs are:",
        "",
        *break_even_table(data, False),
        "",
        "## 7. Conclusion",
        "",
        f"1. Commutative languages favor Promote: aggregate runtime is {comm_time_ratio:.2f}x "
        "Post with identical MQ counts and fewer EQs, despite a larger table.",
        f"2. Star-free languages are effectively tied at {star_time_ratio:.2f}x, so neither "
        "strategy has a stable overall advantage in this suite.",
        f"3. The 256-element full transformation monoid dominates the three-letter total: "
        f"Promote is {t4_time_ratio:.2f}x slower and its table is {t4_cell_ratio:.0f}x larger. "
        f"Without that case, Promote is still {alphabet_without_t4_ratio:.2f}x slower.",
        f"4. Promote uses {-mq_delta:,.0f} fewer MQs overall because some runs finish with a "
        "smaller suffix set. Table cells, unique MQs, and `P/I/S` sizes must remain separate metrics.",
        f"5. The modeled all-case break-even cost is {fmt(break_even(all_rows) or 0)} ms per EQ. "
        "A PAC-teacher benchmark should measure this cost separately by language category.",
        "",
        "---",
        "",
        "# 补充实验：复杂交换语言",
        "",
        f"本组在同一实验目录中追加 12 个更大规模的交换语言，每种策略预热 1 次、"
        f"正式运行 {repeats[EXTRA_GROUP]} 次，共 {complex_runs} 次 learner run。"
        "所有目标均通过正则等价验证和 syntactic monoid 交换性审计。",
        "",
        "所有成对指标均按 `Post/Promote` 排列；比率为 Promote/Post。",
        "",
        *detail_table(complex_commutative, True),
        "",
        "## 补充组汇总",
        "",
        "| Post 总耗时 | Promote 总耗时 | Promote/Post | MQ Post/Promote | "
        "EQ Post/Promote | Cells Post/Promote | Cells 比率 | EQ 盈亏平衡点 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
        f"| {fmt(complex_post_time)} ms | {fmt(complex_promote_time)} ms | "
        f"{complex_ratio:.2f}x | "
        f"{sums(complex_commutative, 'post_check', 'mq'):,.0f}/"
        f"{sums(complex_commutative, 'promote_to_p', 'mq'):,.0f} | "
        f"{sums(complex_commutative, 'post_check', 'eq'):,.0f}/"
        f"{sums(complex_commutative, 'promote_to_p', 'eq'):,.0f} | "
        f"{complex_post_cells:,.0f}/{complex_promote_cells:,.0f} | "
        f"{complex_cell_ratio:.2f}x | {fmt(complex_break_even or 0)} ms/EQ |",
        "",
        f"这一补充组中 Promote 节省了 {complex_eq_saved:,.0f} 次 EQ，MQ 差值为 "
        f"{complex_mq_delta:+,.0f}，但最终表格扩大到 {complex_cell_ratio:.2f} 倍，"
        f"组总耗时达到 Post 的 {complex_ratio:.2f} 倍。"
        "这表明 `DFA = syntactic monoid` 只能消除一种风险来源，并不能保证 "
        "Promote 在大规模交换语言上持续占优；当 `|P|` 从 1 扩张到整个 monoid 时，"
        "乘法式表格成本仍会随状态数迅速增长。",
        "",
        "# Additional Experiment: Complex Commutative Languages",
        "",
        f"This supplemental suite adds 12 larger commutative languages with one warm-up "
        f"and {repeats[EXTRA_GROUP]} measured runs per strategy ({complex_runs} learner runs).",
        "",
        "All paired metrics are ordered as `Post/Promote`; Ratio is Promote/Post.",
        "",
        *detail_table(complex_commutative, False),
        "",
        "## Supplemental Summary",
        "",
        "| Post total | Promote total | Promote/Post | MQ Post/Promote | "
        "EQ Post/Promote | Cells Post/Promote | Cell ratio | EQ break-even |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
        f"| {fmt(complex_post_time)} ms | {fmt(complex_promote_time)} ms | "
        f"{complex_ratio:.2f}x | "
        f"{sums(complex_commutative, 'post_check', 'mq'):,.0f}/"
        f"{sums(complex_commutative, 'promote_to_p', 'mq'):,.0f} | "
        f"{sums(complex_commutative, 'post_check', 'eq'):,.0f}/"
        f"{sums(complex_commutative, 'promote_to_p', 'eq'):,.0f} | "
        f"{complex_post_cells:,.0f}/{complex_promote_cells:,.0f} | "
        f"{complex_cell_ratio:.2f}x | {fmt(complex_break_even or 0)} ms/EQ |",
        "",
        f"Promote saves {complex_eq_saved:,.0f} EQs, but its table is "
        f"{complex_cell_ratio:.2f}x larger and aggregate runtime is {complex_ratio:.2f}x Post. "
        "Equality between DFA and monoid size removes one risk factor, but does not prevent "
        "full promotion from becoming expensive as the commutative monoid grows.",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data, repeats = load_data(args.input_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_report(data, repeats), encoding="utf-8")


if __name__ == "__main__":
    main()
