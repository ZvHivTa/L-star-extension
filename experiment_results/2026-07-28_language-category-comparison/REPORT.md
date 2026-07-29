# `post_check` 与 `promote_to_p` 按语言类别性能对比

实验日期：2026-07-28
代码版本：`43f7591 + working tree changes`
运行环境：Windows，Python 3.14.3

# 中文报告

## 1. 实验目标

本轮不再按规模分组，而是比较两种策略在三类语言上的行为：

- 12 个Commutative：包含性 ($\Sigma^* a \Sigma^*$)、阈值计数 ($|w_a|> k$)、模计数 ($|w_a| \text{ mod } k = 0$) 以及交换计数器直积 ($|w_a| \text{ mod } k_1 = 0 \and |w_b| \text{ mod } k_2 = 0$) 。
- 12 个 star-free 语言：前后缀(prefix and suffix)、子串(substring)、子序列 ($\Sigma^* a \Sigma^*b \Sigma^*$)、有限计数 ($|w_a|> k$) 和模式规避 (not contain some substrings)。
- 20 个三字母语言：字母表固定为 `{a,b,c}`，并加入少量较困难的群与变换幺半群案例。

Runner 会直接审计交换语言的 syntactic monoid 是否交换，并审计 star-free组的 syntactic monoid 是否 aperiodic。

## 2. 方法

- 交换语言和 star-free 语言各预热 1 次、正式运行 15 次；
  三字母语言预热 1 次、正式运行 7 次。
- 每次重复交替策略顺序，报告正式运行的中位数。
- 每次运行验证最终语言等价、学习状态数等于目标 syntactic monoid 大小，
  并断言 `promote_to_p` 的 Monoid Consistency Check 次数为 0。
- 基础三组共执行 1,088 次 learner run，全部通过校验。

原始数据：[commutative.json](benchmark_data/commutative.json)、[star_free.json](benchmark_data/star_free.json)、[alphabet_3.json](benchmark_data/alphabet_3.json)。

复现实验脚本：[compare_language_categories.py](../../tests/compare_language_categories.py)。

## 3. 总体结果

组耗时是组内各用例中位耗时之和；差异在 5% 以内记为接近。

| 组别 | 用例数 | Post | Promote | Promote/Post | Post 胜 | Promote 胜 | 接近 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 交换语言 | 12 | 6.105 ms | 5.018 ms | 0.82x | 1 | 7 | 4 |
| Star-free 语言 | 12 | 7.263 ms | 7.203 ms | 0.99x | 2 | 5 | 5 |
| 三字母语言 | 20 | 2,199.091 ms | 22,763.389 ms | 10.35x | 11 | 3 | 6 |
| 合计 | 44 | 2,212.460 ms | 22,775.610 ms | 10.29x | 14 | 15 | 15 |

## 4. 各组详细数据

所有成对指标均按 `Post/Promote` 排列；比率为 Promote/Post。

### 4.1 Commutative

| 用例 | DFA | Monoid | Post ms | Promote ms | 比率 | MQ Post/Promote | EQ Post/Promote | Cells Post/Promote | P 大小 Post/Promote | I 大小 Post/Promote | S 大小 Post/Promote |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `contains_a` | 2 | 2 | 0.233 | 0.238 | 1.02x | 7/7 | 1/1 | 5/10 | 1/2 | 2/2 | 1/1 |
| `contains_a_and_b` | 4 | 4 | 0.607 | 0.543 | 0.90x | 51/51 | 3/2 | 27/108 | 1/4 | 4/4 | 3/3 |
| `even_a` | 2 | 2 | 0.233 | 0.230 | 0.99x | 7/7 | 1/1 | 5/10 | 1/2 | 2/2 | 1/1 |
| `odd_a` | 2 | 2 | 0.247 | 0.234 | 0.95x | 7/7 | 1/1 | 5/10 | 1/2 | 2/2 | 1/1 |
| `even_b` | 2 | 2 | 0.240 | 0.231 | 0.96x | 7/7 | 1/1 | 5/10 | 1/2 | 2/2 | 1/1 |
| `a_mod_3_zero` | 3 | 3 | 0.419 | 0.319 | 0.76x | 17/17 | 2/1 | 14/42 | 1/3 | 3/3 | 2/2 |
| `b_mod_4_zero` | 4 | 4 | 0.618 | 0.555 | 0.90x | 31/31 | 3/2 | 27/108 | 1/4 | 4/4 | 3/3 |
| `same_parity_a_b` | 2 | 2 | 0.240 | 0.236 | 0.98x | 7/7 | 1/1 | 5/10 | 1/2 | 2/2 | 1/1 |
| `both_counts_even` | 4 | 4 | 0.703 | 0.464 | 0.66x | 51/51 | 3/1 | 27/108 | 1/4 | 4/4 | 3/3 |
| `at_least_two_a` | 3 | 3 | 0.392 | 0.412 | 1.05x | 17/17 | 2/2 | 14/42 | 1/3 | 3/3 | 2/2 |
| `at_most_two_b` | 4 | 4 | 0.582 | 0.545 | 0.94x | 31/31 | 3/2 | 27/108 | 1/4 | 4/4 | 3/3 |
| `a_mod_3_b_mod_2_zero` | 6 | 6 | 1.592 | 1.012 | 0.64x | 155/155 | 5/1 | 65/390 | 1/6 | 6/6 | 5/5 |

### 4.2 Star-free

| 用例 | DFA | Monoid | Post ms | Promote ms | 比率 | MQ Post/Promote | EQ Post/Promote | Cells Post/Promote | P 大小 Post/Promote | I 大小 Post/Promote | S 大小 Post/Promote |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `contains_a` | 2 | 2 | 0.255 | 0.238 | 0.93x | 7/7 | 1/1 | 5/10 | 1/2 | 2/2 | 1/1 |
| `contains_a_and_b` | 4 | 4 | 0.624 | 0.574 | 0.92x | 51/51 | 3/2 | 27/108 | 1/4 | 4/4 | 3/3 |
| `starts_with_a` | 3 | 3 | 0.431 | 0.420 | 0.98x | 23/23 | 2/2 | 14/42 | 1/3 | 3/3 | 2/2 |
| `ends_with_b` | 2 | 3 | 0.316 | 0.281 | 0.89x | 15/15 | 1/1 | 14/21 | 2/3 | 3/3 | 1/1 |
| `contains_ab` | 3 | 5 | 0.571 | 0.550 | 0.96x | 53/53 | 2/2 | 44/110 | 2/5 | 5/5 | 2/2 |
| `avoids_aa` | 3 | 6 | 0.652 | 0.629 | 0.97x | 71/71 | 2/2 | 52/156 | 2/6 | 6/6 | 2/2 |
| `exactly_one_a` | 3 | 3 | 0.413 | 0.326 | 0.79x | 17/17 | 2/1 | 14/42 | 1/3 | 3/3 | 2/2 |
| `at_least_two_a` | 3 | 3 | 0.399 | 0.398 | 1.00x | 17/17 | 2/2 | 14/42 | 1/3 | 3/3 | 2/2 |
| `at_most_two_b` | 4 | 4 | 0.624 | 0.555 | 0.89x | 31/31 | 3/2 | 27/108 | 1/4 | 4/4 | 3/3 |
| `a_before_b` | 3 | 5 | 0.614 | 0.694 | 1.13x | 53/53 | 2/2 | 44/110 | 2/5 | 5/5 | 2/2 |
| `ends_with_aba` | 4 | 8 | 1.201 | 1.253 | 1.04x | 159/159 | 3/3 | 153/408 | 3/8 | 8/8 | 3/3 |
| `length_at_most_4` | 6 | 6 | 1.163 | 1.285 | 1.10x | 71/71 | 5/3 | 65/390 | 1/6 | 6/6 | 5/5 |

### 4.3 3-alphabet

| 用例 | DFA | Monoid | Post ms | Promote ms | 比率 | MQ Post/Promote | EQ Post/Promote | Cells Post/Promote | P 大小 Post/Promote | I 大小 Post/Promote | S 大小 Post/Promote |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `all_words` | 1 | 1 | 0.220 | 0.214 | 0.97x | 4/4 | 1/1 | 4/4 | 1/1 | 1/1 | 1/1 |
| `contains_all_symbols` | 8 | 8 | 3.556 | 3.625 | 1.02x | 787/682 | 7/3 | 175/1,200 | 1/8 | 8/8 | 7/6 |
| `exactly_one_each` | 9 | 9 | 5.657 | 6.668 | 1.18x | 1,079/1,079 | 8/2 | 224/2,016 | 1/9 | 9/9 | 8/8 |
| `even_a` | 2 | 2 | 0.284 | 0.271 | 0.95x | 10/10 | 1/1 | 7/14 | 1/2 | 2/2 | 1/1 |
| `a_mod_3_zero` | 3 | 3 | 0.496 | 0.386 | 0.78x | 27/27 | 2/1 | 20/60 | 1/3 | 3/3 | 2/2 |
| `all_counts_even` | 8 | 8 | 5.960 | 3.502 | 0.59x | 787/787 | 7/1 | 175/1,400 | 1/8 | 8/8 | 7/7 |
| `mixed_mod_3_2_2` | 12 | 12 | 16.635 | 16.059 | 0.97x | 2,679/2,679 | 11/1 | 407/4,884 | 1/12 | 12/12 | 11/11 |
| `length_mod_8` | 8 | 8 | 3.847 | 3.157 | 0.82x | 232/233 | 7/3 | 175/1,400 | 1/8 | 8/8 | 7/7 |
| `a_mod_4_b_mod_3` | 12 | 12 | 14.093 | 15.769 | 1.12x | 2,334/2,334 | 11/3 | 407/4,884 | 1/12 | 12/12 | 11/11 |
| `ends_with_abc` | 4 | 8 | 1.791 | 1.773 | 0.99x | 362/367 | 3/3 | 225/600 | 3/8 | 8/8 | 3/3 |
| `ends_with_abca` | 5 | 12 | 4.023 | 4.827 | 1.20x | 892/904 | 4/4 | 592/1,776 | 4/12 | 12/12 | 4/4 |
| `contains_abc` | 4 | 12 | 2.697 | 3.972 | 1.47x | 711/731 | 3/3 | 333/1,332 | 3/12 | 12/12 | 3/3 |
| `contains_abca` | 5 | 21 | 10.070 | 16.968 | 1.68x | 2,699/2,803 | 4/4 | 1,024/5,376 | 4/21 | 21/21 | 4/4 |
| `avoids_equal_neighbors` | 5 | 11 | 3.207 | 3.398 | 1.06x | 787/787 | 4/2 | 408/1,496 | 3/11 | 11/11 | 4/4 |
| `ordered_blocks` | 4 | 8 | 1.753 | 1.829 | 1.04x | 346/346 | 3/3 | 225/600 | 3/8 | 8/8 | 3/3 |
| `exact_abcabc` | 8 | 17 | 13.627 | 23.354 | 1.71x | 3,016/3,082 | 7/6 | 1,092/6,188 | 3/17 | 17/17 | 7/7 |
| `at_least_two_each` | 27 | 27 | 144.237 | 203.858 | 1.41x | 32,939/22,995 | 26/6 | 2,132/39,852 | 1/27 | 27/27 | 26/18 |
| `s4_permutation_action` | 4 | 24 | 9.793 | 15.219 | 1.55x | 2,929/2,929 | 3/3 | 657/5,256 | 3/24 | 24/24 | 3/3 |
| `dihedral_action_12` | 12 | 24 | 45.895 | 71.594 | 1.56x | 10,154/10,154 | 11/2 | 1,606/19,272 | 2/24 | 24/24 | 11/11 |
| `full_transformation_monoid_4` | 4 | 256 | 1,911.251 | 22,366.947 | 11.70x | 259,360/259,360 | 3/2 | 9,228/590,592 | 4/256 | 256/256 | 3/3 |

## 5. 查询、表格与集合规模

| 组别 | MQ Post/Promote | EQ Post/Promote | EQ 耗时 Post/Promote | Post Monoid Check | Cells Post/Promote | Cells 比率 | P 大小之和 Post/Promote | I 大小之和 Post/Promote | S 大小之和 Post/Promote |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 交换语言 | 388/388 | 26/16 | 2.628/1.570 ms | 0.835 ms | 226/956 | 4.23x | 12/38 | 38/38 | 26/26 |
| Star-free 语言 | 568/568 | 28/23 | 2.597/2.256 ms | 1.117 ms | 473/1,547 | 3.27x | 18/52 | 52/52 | 28/28 |
| 三字母语言 | 322,134/312,293 | 126/54 | 42.191/11.546 ms | 2,003.986 ms | 19,116/688,202 | 36.00x | 42/483 | 483/483 | 126/117 |
| 合计 | 323,090/313,249 | 180/93 | 47.416/15.372 ms | 2,005.938 ms | 19,815/690,705 | 34.86x | 72/573 | 573/573 | 180/171 |

全部用例中 Promote 相对 Post 的 MQ 差值为 -9,841，节省 EQ 87 次；最终表格单元总数为 Post 的 34.86 倍。
详细表中的 `|P|、|I|、|S|` 可以进一步区分表格膨胀来自左上下文、
代表元还是后缀实验集合。

## 6. 理想 EQ 与真实/PAC EQ

当前 Oracle 持有完整目标 DFA，通过 symmetric difference 执行精确 EQ。
这类 EQ 是理想的内存操作，不能代表黑盒一致性测试或 PAC 抽样的真实成本。

采用成本模型：

```text
Adjusted time = measured non-EQ time + EQ count × C
```

其中 `C` 是一次真实 EQ 的平均成本。本轮数据给出的盈亏平衡点为：

| 范围 | Promote 追平所需平均 EQ 成本 |
|---|---:|
| 交换语言 | 0.000 ms / EQ |
| Star-free 语言 | 0.056 ms / EQ |
| 三字母语言 | 286.041 ms / EQ |
| 全部 44 例 | 236.726 ms / EQ |

阈值为 0 表示 Promote 的非 EQ 成本已经不高于 Post；“无有限阈值”表示
Promote 没有减少 EQ，因此提高 EQ 成本也无法靠该项追平。

## 7. 结论

1. **交换语言最有利于 Promote。** 组耗时是 Post 的 0.82 倍，即低约 17.8%；MQ 完全相同，EQ 从 26 次降到 16 次。代价是表格扩大到 4.23 倍。这支持了最初的观察：当 DFA 和 syntactic monoid 同步增长且结构交换时，提前把代表元放入 `P` 能较便宜地替代若干 EQ。

2. **Star-free 组总体持平。** Promote/Post 耗时比为 0.99，EQ 只减少 5 次，而表格为 Post 的 3.27 倍。这组没有显示出稳定的单边优势。

3. **三字母组的总耗时被 256 元 full transformation monoid 明显主导。** 该例中 Promote 慢 11.70 倍，表格正好扩大 64 倍，因为 `|P|` 从 4 增至 256。即使剔除该例，三字母组 Promote 仍慢 1.38 倍，表格为 9.87 倍，说明较大字母表与非交换结构会放大维护完整 `P` 的本地成本。

4. **大表不等于更多 MQ。** 本轮 Promote 总 MQ 反而少 9,841 次。差值来自部分三字母案例中更小的 `S`；全局字符串缓存又把大量不同表格坐标折叠到同一个 MQ。这说明需要把表格单元、唯一 MQ 和 `P/I/S` 分开报告。

5. **真实 EQ 成本可能改变总排名，但门槛取决于语言类别。** 全体用例的估算门槛是 236.726 ms/EQ；交换语言为 0.000 ms/EQ，三字母组则为 286.041 ms/EQ。因此下一轮 PAC 实验不应只报告平均值，还应按语言结构分别估计 teacher 成本。

---

# English Report

## 1. Objective

This benchmark compares the strategies by language category: 12 commutative
languages, 12 star-free languages, and 20 languages over `{a,b,c}`.
The runner validates commutativity and aperiodicity for the first two suites.

## 2. Methodology

- Commutative and star-free cases use one warm-up plus 15 measured runs.
- Three-letter cases use one warm-up plus 7 measured runs.
- Strategy order alternates, and reported runtime is the median.
- 1,088 learner runs in the three base groups passed validation.
- Every JSON case includes a target-verified `regex` using concatenation, `|`, `*`, and parentheses only; optional and fixed-count syntax is explicitly expanded.

## 3. Aggregate Results

| Group | Cases | Post | Promote | Promote/Post | Post wins | Promote wins | Close |
|---|---:|---:|---:|---:|---:|---:|---:|
| Commutative | 12 | 6.105 ms | 5.018 ms | 0.82x | 1 | 7 | 4 |
| Star-free | 12 | 7.263 ms | 7.203 ms | 0.99x | 2 | 5 | 5 |
| Three-letter alphabet | 20 | 2,199.091 ms | 22,763.389 ms | 10.35x | 11 | 3 | 6 |
| Total | 44 | 2,212.460 ms | 22,775.610 ms | 10.29x | 14 | 15 | 15 |

## 4. Detailed Results

All paired metrics are ordered as `Post/Promote`; Ratio is Promote/Post.

### 4.1 Commutative

| Case | DFA | Monoid | Post ms | Promote ms | Ratio | MQ Post/Promote | EQ Post/Promote | Cells Post/Promote | P size Post/Promote | I size Post/Promote | S size Post/Promote |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `contains_a` | 2 | 2 | 0.233 | 0.238 | 1.02x | 7/7 | 1/1 | 5/10 | 1/2 | 2/2 | 1/1 |
| `contains_a_and_b` | 4 | 4 | 0.607 | 0.543 | 0.90x | 51/51 | 3/2 | 27/108 | 1/4 | 4/4 | 3/3 |
| `even_a` | 2 | 2 | 0.233 | 0.230 | 0.99x | 7/7 | 1/1 | 5/10 | 1/2 | 2/2 | 1/1 |
| `odd_a` | 2 | 2 | 0.247 | 0.234 | 0.95x | 7/7 | 1/1 | 5/10 | 1/2 | 2/2 | 1/1 |
| `even_b` | 2 | 2 | 0.240 | 0.231 | 0.96x | 7/7 | 1/1 | 5/10 | 1/2 | 2/2 | 1/1 |
| `a_mod_3_zero` | 3 | 3 | 0.419 | 0.319 | 0.76x | 17/17 | 2/1 | 14/42 | 1/3 | 3/3 | 2/2 |
| `b_mod_4_zero` | 4 | 4 | 0.618 | 0.555 | 0.90x | 31/31 | 3/2 | 27/108 | 1/4 | 4/4 | 3/3 |
| `same_parity_a_b` | 2 | 2 | 0.240 | 0.236 | 0.98x | 7/7 | 1/1 | 5/10 | 1/2 | 2/2 | 1/1 |
| `both_counts_even` | 4 | 4 | 0.703 | 0.464 | 0.66x | 51/51 | 3/1 | 27/108 | 1/4 | 4/4 | 3/3 |
| `at_least_two_a` | 3 | 3 | 0.392 | 0.412 | 1.05x | 17/17 | 2/2 | 14/42 | 1/3 | 3/3 | 2/2 |
| `at_most_two_b` | 4 | 4 | 0.582 | 0.545 | 0.94x | 31/31 | 3/2 | 27/108 | 1/4 | 4/4 | 3/3 |
| `a_mod_3_b_mod_2_zero` | 6 | 6 | 1.592 | 1.012 | 0.64x | 155/155 | 5/1 | 65/390 | 1/6 | 6/6 | 5/5 |

### 4.2 Star-free

| Case | DFA | Monoid | Post ms | Promote ms | Ratio | MQ Post/Promote | EQ Post/Promote | Cells Post/Promote | P size Post/Promote | I size Post/Promote | S size Post/Promote |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `contains_a` | 2 | 2 | 0.255 | 0.238 | 0.93x | 7/7 | 1/1 | 5/10 | 1/2 | 2/2 | 1/1 |
| `contains_a_and_b` | 4 | 4 | 0.624 | 0.574 | 0.92x | 51/51 | 3/2 | 27/108 | 1/4 | 4/4 | 3/3 |
| `starts_with_a` | 3 | 3 | 0.431 | 0.420 | 0.98x | 23/23 | 2/2 | 14/42 | 1/3 | 3/3 | 2/2 |
| `ends_with_b` | 2 | 3 | 0.316 | 0.281 | 0.89x | 15/15 | 1/1 | 14/21 | 2/3 | 3/3 | 1/1 |
| `contains_ab` | 3 | 5 | 0.571 | 0.550 | 0.96x | 53/53 | 2/2 | 44/110 | 2/5 | 5/5 | 2/2 |
| `avoids_aa` | 3 | 6 | 0.652 | 0.629 | 0.97x | 71/71 | 2/2 | 52/156 | 2/6 | 6/6 | 2/2 |
| `exactly_one_a` | 3 | 3 | 0.413 | 0.326 | 0.79x | 17/17 | 2/1 | 14/42 | 1/3 | 3/3 | 2/2 |
| `at_least_two_a` | 3 | 3 | 0.399 | 0.398 | 1.00x | 17/17 | 2/2 | 14/42 | 1/3 | 3/3 | 2/2 |
| `at_most_two_b` | 4 | 4 | 0.624 | 0.555 | 0.89x | 31/31 | 3/2 | 27/108 | 1/4 | 4/4 | 3/3 |
| `a_before_b` | 3 | 5 | 0.614 | 0.694 | 1.13x | 53/53 | 2/2 | 44/110 | 2/5 | 5/5 | 2/2 |
| `ends_with_aba` | 4 | 8 | 1.201 | 1.253 | 1.04x | 159/159 | 3/3 | 153/408 | 3/8 | 8/8 | 3/3 |
| `length_at_most_4` | 6 | 6 | 1.163 | 1.285 | 1.10x | 71/71 | 5/3 | 65/390 | 1/6 | 6/6 | 5/5 |

### 4.3 Three-letter alphabet

| Case | DFA | Monoid | Post ms | Promote ms | Ratio | MQ Post/Promote | EQ Post/Promote | Cells Post/Promote | P size Post/Promote | I size Post/Promote | S size Post/Promote |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `all_words` | 1 | 1 | 0.220 | 0.214 | 0.97x | 4/4 | 1/1 | 4/4 | 1/1 | 1/1 | 1/1 |
| `contains_all_symbols` | 8 | 8 | 3.556 | 3.625 | 1.02x | 787/682 | 7/3 | 175/1,200 | 1/8 | 8/8 | 7/6 |
| `exactly_one_each` | 9 | 9 | 5.657 | 6.668 | 1.18x | 1,079/1,079 | 8/2 | 224/2,016 | 1/9 | 9/9 | 8/8 |
| `even_a` | 2 | 2 | 0.284 | 0.271 | 0.95x | 10/10 | 1/1 | 7/14 | 1/2 | 2/2 | 1/1 |
| `a_mod_3_zero` | 3 | 3 | 0.496 | 0.386 | 0.78x | 27/27 | 2/1 | 20/60 | 1/3 | 3/3 | 2/2 |
| `all_counts_even` | 8 | 8 | 5.960 | 3.502 | 0.59x | 787/787 | 7/1 | 175/1,400 | 1/8 | 8/8 | 7/7 |
| `mixed_mod_3_2_2` | 12 | 12 | 16.635 | 16.059 | 0.97x | 2,679/2,679 | 11/1 | 407/4,884 | 1/12 | 12/12 | 11/11 |
| `length_mod_8` | 8 | 8 | 3.847 | 3.157 | 0.82x | 232/233 | 7/3 | 175/1,400 | 1/8 | 8/8 | 7/7 |
| `a_mod_4_b_mod_3` | 12 | 12 | 14.093 | 15.769 | 1.12x | 2,334/2,334 | 11/3 | 407/4,884 | 1/12 | 12/12 | 11/11 |
| `ends_with_abc` | 4 | 8 | 1.791 | 1.773 | 0.99x | 362/367 | 3/3 | 225/600 | 3/8 | 8/8 | 3/3 |
| `ends_with_abca` | 5 | 12 | 4.023 | 4.827 | 1.20x | 892/904 | 4/4 | 592/1,776 | 4/12 | 12/12 | 4/4 |
| `contains_abc` | 4 | 12 | 2.697 | 3.972 | 1.47x | 711/731 | 3/3 | 333/1,332 | 3/12 | 12/12 | 3/3 |
| `contains_abca` | 5 | 21 | 10.070 | 16.968 | 1.68x | 2,699/2,803 | 4/4 | 1,024/5,376 | 4/21 | 21/21 | 4/4 |
| `avoids_equal_neighbors` | 5 | 11 | 3.207 | 3.398 | 1.06x | 787/787 | 4/2 | 408/1,496 | 3/11 | 11/11 | 4/4 |
| `ordered_blocks` | 4 | 8 | 1.753 | 1.829 | 1.04x | 346/346 | 3/3 | 225/600 | 3/8 | 8/8 | 3/3 |
| `exact_abcabc` | 8 | 17 | 13.627 | 23.354 | 1.71x | 3,016/3,082 | 7/6 | 1,092/6,188 | 3/17 | 17/17 | 7/7 |
| `at_least_two_each` | 27 | 27 | 144.237 | 203.858 | 1.41x | 32,939/22,995 | 26/6 | 2,132/39,852 | 1/27 | 27/27 | 26/18 |
| `s4_permutation_action` | 4 | 24 | 9.793 | 15.219 | 1.55x | 2,929/2,929 | 3/3 | 657/5,256 | 3/24 | 24/24 | 3/3 |
| `dihedral_action_12` | 12 | 24 | 45.895 | 71.594 | 1.56x | 10,154/10,154 | 11/2 | 1,606/19,272 | 2/24 | 24/24 | 11/11 |
| `full_transformation_monoid_4` | 4 | 256 | 1,911.251 | 22,366.947 | 11.70x | 259,360/259,360 | 3/2 | 9,228/590,592 | 4/256 | 256/256 | 3/3 |

## 5. Query and Structure Summary

| Group | MQ Post/Promote | EQ Post/Promote | EQ time Post/Promote | Post Monoid Check | Cells Post/Promote | Cell ratio | Sum of P sizes Post/Promote | Sum of I sizes Post/Promote | Sum of S sizes Post/Promote |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Commutative | 388/388 | 26/16 | 2.628/1.570 ms | 0.835 ms | 226/956 | 4.23x | 12/38 | 38/38 | 26/26 |
| Star-free | 568/568 | 28/23 | 2.597/2.256 ms | 1.117 ms | 473/1,547 | 3.27x | 18/52 | 52/52 | 28/28 |
| Three-letter alphabet | 322,134/312,293 | 126/54 | 42.191/11.546 ms | 2,003.986 ms | 19,116/688,202 | 36.00x | 42/483 | 483/483 | 126/117 |
| Total | 323,090/313,249 | 180/93 | 47.416/15.372 ms | 2,005.938 ms | 19,815/690,705 | 34.86x | 72/573 | 573/573 | 180/171 |

## 6. Ideal EQ Versus Real/PAC EQ

The current Oracle performs exact in-memory EQ by DFA symmetric difference.
Using `Adjusted time = measured non-EQ time + EQ count × C`, the estimated
break-even costs are:

| Scope | Average EQ cost required for Promote to break even |
|---|---:|
| Commutative | 0.000 ms / EQ |
| Star-free | 0.056 ms / EQ |
| Three-letter alphabet | 286.041 ms / EQ |
| All 44 cases | 236.726 ms / EQ |

## 7. Conclusion

1. Commutative languages favor Promote: aggregate runtime is 0.82x Post with identical MQ counts and fewer EQs, despite a larger table.
2. Star-free languages are effectively tied at 0.99x, so neither strategy has a stable overall advantage in this suite.
3. The 256-element full transformation monoid dominates the three-letter total: Promote is 11.70x slower and its table is 64x larger. Without that case, Promote is still 1.38x slower.
4. Promote uses 9,841 fewer MQs overall because some runs finish with a smaller suffix set. Table cells, unique MQs, and `P/I/S` sizes must remain separate metrics.
5. The modeled all-case break-even cost is 236.726 ms per EQ. A PAC-teacher benchmark should measure this cost separately by language category.

---

# 补充实验：复杂交换语言

本组在同一实验目录中追加 12 个更大规模的交换语言，每种策略预热 1 次、正式运行 5 次，共 144 次 learner run。所有目标均通过正则等价验证和 syntactic monoid 交换性审计。

所有成对指标均按 `Post/Promote` 排列；比率为 Promote/Post。

| 用例 | DFA | Monoid | Post ms | Promote ms | 比率 | MQ Post/Promote | EQ Post/Promote | Cells Post/Promote | P 大小 Post/Promote | I 大小 Post/Promote | S 大小 Post/Promote |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `a_mod_5_or_b_mod_7` | 35 | 35 | 154.523 | 194.708 | 1.26x | 16,132/15,201 | 16/4 | 1,136/34,790 | 1/35 | 35/35 | 16/14 |
| `a_mod_6_or_b_mod_7` | 42 | 42 | 234.470 | 369.655 | 1.58x | 26,352/25,113 | 18/4 | 1,530/57,120 | 1/42 | 42/42 | 18/16 |
| `a_mod_7_or_b_mod_8` | 56 | 56 | 583.897 | 1,102.726 | 1.89x | 57,982/56,052 | 22/4 | 2,486/126,560 | 1/56 | 56/56 | 22/20 |
| `a_mod_8_or_b_mod_9` | 72 | 72 | 1,201.063 | 3,077.407 | 2.56x | 114,722/111,420 | 26/5 | 3,770/250,560 | 1/72 | 72/72 | 26/24 |
| `a_mod_9_or_b_mod_11` | 99 | 99 | 3,317.740 | 9,916.342 | 2.99x | 271,292/266,020 | 32/6 | 6,368/591,030 | 1/99 | 99/99 | 32/30 |
| `at_least_6_a_or_b_mod_7` | 43 | 43 | 143.230 | 570.152 | 3.98x | 24,105/31,424 | 16/5 | 1,392/78,561 | 1/43 | 43/43 | 16/21 |
| `at_least_8_a_or_b_mod_9` | 73 | 73 | 673.059 | 3,739.194 | 5.56x | 99,037/129,708 | 22/7 | 3,234/311,199 | 1/73 | 73/73 | 22/29 |
| `at_least_6_a_or_7_b` | 43 | 43 | 91.834 | 261.857 | 2.85x | 18,433/18,433 | 12/7 | 1,044/44,892 | 1/43 | 43/43 | 12/12 |
| `at_least_8_a_or_9_b` | 73 | 73 | 439.939 | 1,837.285 | 4.18x | 73,201/73,201 | 16/9 | 2,352/171,696 | 1/73 | 73/73 | 16/16 |
| `a_or_b_or_c_mod_3_4_5` | 60 | 60 | 775.137 | 1,767.942 | 2.28x | 131,220/118,788 | 20/4 | 3,620/195,480 | 1/60 | 60/60 | 20/18 |
| `a_mod_31_zero` | 31 | 31 | 119.629 | 407.662 | 3.41x | 1,921/1,922 | 30/8 | 1,890/58,590 | 1/31 | 31/31 | 30/30 |
| `length_mod_40` | 40 | 40 | 374.122 | 1,971.240 | 5.27x | 6,280/6,281 | 39/11 | 4,719/188,760 | 1/40 | 40/40 | 39/39 |

## 补充组汇总

| Post 总耗时 | Promote 总耗时 | Promote/Post | MQ Post/Promote | EQ Post/Promote | Cells Post/Promote | Cells 比率 | EQ 盈亏平衡点 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 8,108.643 ms | 25,216.170 ms | 3.11x | 840,677/853,563 | 269/74 | 33,541/2,109,238 | 62.89x | 99.389 ms/EQ |

这一补充组中 Promote 节省了 195 次 EQ，MQ 差值为 +12,886，但最终表格扩大到 62.89 倍，组总耗时达到 Post 的 3.11 倍。这表明 `DFA = syntactic monoid` 只能消除一种风险来源，并不能保证 Promote 在大规模交换语言上持续占优；当 `|P|` 从 1 扩张到整个 monoid 时，乘法式表格成本仍会随状态数迅速增长。

# Additional Experiment: Complex Commutative Languages

This supplemental suite adds 12 larger commutative languages with one warm-up and 5 measured runs per strategy (144 learner runs).

All paired metrics are ordered as `Post/Promote`; Ratio is Promote/Post.

| Case | DFA | Monoid | Post ms | Promote ms | Ratio | MQ Post/Promote | EQ Post/Promote | Cells Post/Promote | P size Post/Promote | I size Post/Promote | S size Post/Promote |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `a_mod_5_or_b_mod_7` | 35 | 35 | 154.523 | 194.708 | 1.26x | 16,132/15,201 | 16/4 | 1,136/34,790 | 1/35 | 35/35 | 16/14 |
| `a_mod_6_or_b_mod_7` | 42 | 42 | 234.470 | 369.655 | 1.58x | 26,352/25,113 | 18/4 | 1,530/57,120 | 1/42 | 42/42 | 18/16 |
| `a_mod_7_or_b_mod_8` | 56 | 56 | 583.897 | 1,102.726 | 1.89x | 57,982/56,052 | 22/4 | 2,486/126,560 | 1/56 | 56/56 | 22/20 |
| `a_mod_8_or_b_mod_9` | 72 | 72 | 1,201.063 | 3,077.407 | 2.56x | 114,722/111,420 | 26/5 | 3,770/250,560 | 1/72 | 72/72 | 26/24 |
| `a_mod_9_or_b_mod_11` | 99 | 99 | 3,317.740 | 9,916.342 | 2.99x | 271,292/266,020 | 32/6 | 6,368/591,030 | 1/99 | 99/99 | 32/30 |
| `at_least_6_a_or_b_mod_7` | 43 | 43 | 143.230 | 570.152 | 3.98x | 24,105/31,424 | 16/5 | 1,392/78,561 | 1/43 | 43/43 | 16/21 |
| `at_least_8_a_or_b_mod_9` | 73 | 73 | 673.059 | 3,739.194 | 5.56x | 99,037/129,708 | 22/7 | 3,234/311,199 | 1/73 | 73/73 | 22/29 |
| `at_least_6_a_or_7_b` | 43 | 43 | 91.834 | 261.857 | 2.85x | 18,433/18,433 | 12/7 | 1,044/44,892 | 1/43 | 43/43 | 12/12 |
| `at_least_8_a_or_9_b` | 73 | 73 | 439.939 | 1,837.285 | 4.18x | 73,201/73,201 | 16/9 | 2,352/171,696 | 1/73 | 73/73 | 16/16 |
| `a_or_b_or_c_mod_3_4_5` | 60 | 60 | 775.137 | 1,767.942 | 2.28x | 131,220/118,788 | 20/4 | 3,620/195,480 | 1/60 | 60/60 | 20/18 |
| `a_mod_31_zero` | 31 | 31 | 119.629 | 407.662 | 3.41x | 1,921/1,922 | 30/8 | 1,890/58,590 | 1/31 | 31/31 | 30/30 |
| `length_mod_40` | 40 | 40 | 374.122 | 1,971.240 | 5.27x | 6,280/6,281 | 39/11 | 4,719/188,760 | 1/40 | 40/40 | 39/39 |

## Supplemental Summary

| Post total | Promote total | Promote/Post | MQ Post/Promote | EQ Post/Promote | Cells Post/Promote | Cell ratio | EQ break-even |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 8,108.643 ms | 25,216.170 ms | 3.11x | 840,677/853,563 | 269/74 | 33,541/2,109,238 | 62.89x | 99.389 ms/EQ |

Promote saves 195 EQs, but its table is 62.89x larger and aggregate runtime is 3.11x Post. Equality between DFA and monoid size removes one risk factor, but does not prevent full promotion from becoming expensive as the commutative monoid grows.
