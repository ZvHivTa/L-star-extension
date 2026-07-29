# `post_check` 与 `promote_to_p` 三组性能对比报告

测试日期：2026-07-22  
代码基线：`002dfb0` 加当前未提交策略修改  
运行环境：Windows，Python 3.14，字母表 `{a,b}`

---

# 中文报告

## 1. 测试目的

本轮测试比较一体化学习器的两种策略：

- `post_check`：语言 EQ 成功后执行 Monoid Consistency Check，只在发现 witness 时扩充 `P`。
- `promote_to_p`：每个新 `I` 代表元立即加入 `P`，执行 Right Consistency，但不执行 Monoid Consistency Check。

重点观察：

- 总耗时、MQ、EQ 和理想 EQ 耗时；
- Monoid Check 与 Right Consistency 的工作转移；
- `P` 的规模和观察表单元数；
- 当 EQ 是理想的内存 DFA 比较时，两种策略如何随问题规模变化；
- 如果未来换成昂贵的真实/PAC EQ，`promote_to_p` 在什么成本下可能反超。

## 2. 测试方法

- 三组各 12 个用例，共 36 个目标语言。
- 普通组每种策略预热 1 次，正式运行 25 次。
- 中等组每种策略预热 1 次，正式运行 15 次。
- 压力组每种策略预热 1 次，正式运行 7 次。
- 两种策略交替运行，报告正式运行的中位耗时。
- `debug_mode=False`、`verbose=False`、`max_p_length=1`。
- 每次运行后额外验证：最终 hypothesis 与目标语言等价，且状态数等于目标 syntactic monoid 大小。
- 每次运行还断言 `promote_to_p.monoid_check_count == 0`。
- 正式测试共执行 1,200 次 learner run；36 个用例全部通过校验。

cyclic family 记为：

```text
C_k = (b*a 重复 k 次)*b*
```

完整正则和原始指标保存在：

- [ordinary JSON](benchmark_data/strategy_comparison_2026-07-22_ordinary.json)
- [medium JSON](benchmark_data/strategy_comparison_2026-07-22_medium.json)
- [stress JSON](benchmark_data/strategy_comparison_2026-07-22_stress.json)

复现脚本：[compare_strategy_groups.py](../tests/compare_strategy_groups.py)

## 3. 总体结果

下面的组耗时是“该组各用例中位耗时之和”，用于整体比较，不代表一次同时运行全部用例的墙钟时间。胜负采用 5% 实用阈值：差异不超过 5% 记为接近。

| 组别 | 用例数 | `post_check` | `promote_to_p` | Promote/Post | Post 胜 | Promote 胜 | 接近 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 普通 | 12 | 5.687 ms | 5.494 ms | 0.97x | 2 | 4 | 6 |
| 中等 | 12 | 109.188 ms | 178.694 ms | 1.64x | 10 | 0 | 2 |
| 压力 | 12 | 3,764.268 ms | 26,405.117 ms | 7.02x | 12 | 0 | 0 |
| 合计 | 36 | 3,879.143 ms | 26,589.305 ms | 6.85x | 24 | 4 | 8 |

普通组中两种策略基本接近；中等组开始明显偏向 `post_check`；压力组中 `post_check` 全胜，并且规模越大差距越明显。

## 4. 各组详细耗时

`比率` 为 `promote_to_p / post_check`；大于 1 表示 `promote_to_p` 更慢。

### 4.1 普通组

| 用例 | DFA | Monoid | Post | Promote | 比率 | MQ Post/Promote | EQ Post/Promote | Cells Post/Promote |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all_words | 1 | 1 | 0.216 | 0.216 | 1.00x | 3 / 3 | 1 / 1 | 3 / 3 |
| empty_only | 1 | 2 | 0.268 | 0.257 | 0.96x | 7 / 7 | 1 / 1 | 5 / 10 |
| a_star | 1 | 2 | 0.273 | 0.274 | 1.00x | 7 / 7 | 1 / 1 | 5 / 10 |
| b_star | 1 | 2 | 0.260 | 0.260 | 1.00x | 7 / 7 | 1 / 1 | 5 / 10 |
| even_a_only | 2 | 3 | 0.455 | 0.350 | 0.77x | 23 / 23 | 2 / 1 | 14 / 42 |
| ab_cycle | 2 | 6 | 0.731 | 0.638 | 0.87x | 69 / 71 | 2 / 1 | 52 / 156 |
| ba_cycle | 2 | 6 | 0.731 | 0.773 | 1.06x | 71 / 71 | 2 / 2 | 52 / 156 |
| ends_a | 2 | 3 | 0.340 | 0.297 | 0.87x | 15 / 15 | 1 / 1 | 14 / 21 |
| ends_b | 2 | 3 | 0.332 | 0.297 | 0.89x | 15 / 15 | 1 / 1 | 14 / 21 |
| a_then_b | 2 | 5 | 0.628 | 0.620 | 0.99x | 53 / 53 | 2 / 2 | 44 / 110 |
| b_then_a | 2 | 5 | 0.633 | 0.616 | 0.97x | 53 / 53 | 2 / 2 | 44 / 110 |
| a_or_bb_blocks | 2 | 7 | 0.819 | 0.896 | 1.09x | 95 / 95 | 2 / 2 | 60 / 210 |

### 4.2 中等组

| 用例 | DFA | Monoid | Post | Promote | 比率 | MQ Post/Promote | EQ Post/Promote | Cells Post/Promote |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| suffix_aab | 4 | 8 | 1.326 | 1.410 | 1.06x | 163 / 163 | 3 / 3 | 153 / 408 |
| suffix_abba | 5 | 11 | 2.604 | 3.219 | 1.24x | 352 / 359 | 4 / 4 | 368 / 1,012 |
| suffix_abab | 5 | 11 | 2.311 | 2.943 | 1.27x | 369 / 369 | 4 / 4 | 276 / 1,012 |
| alternating_blocks | 3 | 15 | 2.916 | 3.464 | 1.19x | 503 / 503 | 3 / 1 | 279 / 1,395 |
| mixed_blocks_2_3 | 4 | 23 | 8.006 | 12.654 | 1.58x | 1,419 / 1,419 | 4 / 1 | 752 / 4,324 |
| finite_b_tail | 4 | 11 | 3.291 | 3.265 | 0.99x | 374 / 379 | 4 / 3 | 368 / 1,012 |
| mixed_suffix | 7 | 32 | 25.265 | 52.734 | 2.09x | 5,015 / 5,015 | 7 / 5 | 1,820 / 14,560 |
| exact_a6b | 8 | 15 | 10.443 | 11.171 | 1.07x | 1,123 / 1,151 | 8 / 7 | 1,736 / 3,720 |
| cyclic_8 | 8 | 8 | 2.549 | 2.482 | 0.97x | 127 / 128 | 7 / 3 | 119 / 952 |
| cyclic_12 | 12 | 12 | 6.791 | 8.725 | 1.28x | 287 / 288 | 11 / 4 | 275 / 3,300 |
| cyclic_16 | 16 | 16 | 14.967 | 22.297 | 1.49x | 511 / 512 | 15 / 5 | 495 / 7,920 |
| cyclic_20 | 20 | 20 | 28.720 | 54.331 | 1.89x | 799 / 800 | 19 / 6 | 779 / 15,580 |

### 4.3 压力组

| 用例 | DFA | Monoid | Post | Promote | 比率 | MQ Post/Promote | EQ Post/Promote | Cells Post/Promote |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| cyclic_24 | 24 | 24 | 42.995 | 113.659 | 2.64x | 1,151 / 1,152 | 23 / 7 | 1,127 / 27,048 |
| cyclic_32 | 32 | 32 | 111.139 | 366.655 | 3.30x | 2,047 / 2,048 | 31 / 9 | 2,015 / 64,480 |
| cyclic_40 | 40 | 40 | 222.397 | 1,054.405 | 4.74x | 3,199 / 3,200 | 39 / 11 | 3,159 / 126,360 |
| cyclic_48 | 48 | 48 | 395.594 | 2,146.208 | 5.43x | 4,607 / 4,608 | 47 / 13 | 4,559 / 218,832 |
| cyclic_56 | 56 | 56 | 609.816 | 4,318.329 | 7.08x | 6,271 / 6,272 | 55 / 15 | 6,215 / 348,040 |
| cyclic_64 | 64 | 64 | 919.943 | 7,416.687 | 8.06x | 8,191 / 8,192 | 63 / 17 | 8,127 / 520,128 |
| cyclic_70 | 70 | 70 | 1,113.747 | 10,555.258 | 9.48x | 9,799 / 9,800 | 69 / 18 | 9,729 / 681,030 |
| exact_a8b | 10 | 19 | 21.540 | 23.301 | 1.08x | 2,145 / 2,199 | 10 / 9 | 3,510 / 7,410 |
| exact_a12b | 14 | 27 | 70.672 | 79.352 | 1.12x | 5,749 / 5,879 | 14 / 13 | 10,010 / 20,790 |
| exact_a16b | 18 | 35 | 225.164 | 277.809 | 1.23x | 12,073 / 12,311 | 18 / 17 | 21,726 / 44,730 |
| suffix_a6b | 8 | 20 | 14.846 | 20.658 | 1.39x | 1,651 / 1,703 | 7 / 7 | 2,009 / 5,740 |
| suffix_abababab | 9 | 23 | 16.415 | 32.797 | 2.00x | 2,583 / 2,645 | 8 / 7 | 1,128 / 8,648 |

## 5. 查询、结构和阶段统计

这些值是各组用例的结构计数之和；表格单元数是各次最终表大小之和，不表示同时占用的峰值内存。

| 组别 | MQ Post/Promote | EQ Post/Promote | EQ 耗时 Post/Promote | Post Monoid Check 耗时 | Cells Post/Promote | Cells 比率 | `Σ|P|` Post/Promote |
|---|---:|---:|---:|---:|---:|---:|---:|
| 普通 | 418 / 420 | 18 / 16 | 1.816 / 1.691 ms | 0.808 ms | 312 / 859 | 2.75x | 19 / 45 |
| 中等 | 11,042 / 11,086 | 89 / 46 | 23.363 / 8.159 ms | 52.071 ms | 7,420 / 55,195 | 7.44x | 36 / 182 |
| 压力 | 59,466 / 60,009 | 384 / 143 | 1,113.019 / 69.586 ms | 1,971.978 ms | 73,314 / 2,073,236 | 28.28x | 56 / 458 |
| 合计 | 70,926 / 71,515 | 491 / 205 | 1,138.198 / 79.436 ms | 2,024.857 ms | 81,046 / 2,129,290 | 26.27x | 111 / 685 |

主要观察：

1. `promote_to_p` 的 MQ 只比 `post_check` 多 589 次，即 0.83%。缓存把很多不同表格单元折叠到了相同字符串 MQ 上。
2. 但是最终表格单元累计达到 `post_check` 的 26.27 倍。即使 MQ 命中缓存，填表循环、行向量、字典单元和一致性维护仍然存在。
3. `promote_to_p` 共减少 286 次 EQ，恰好等于它在 36 个用例中的 286 次 Right Consistency refinement。这说明它把一部分由 EQ 反例完成的后缀细化前移到了表内 Right Consistency。
4. `post_check` 的 Monoid Check 在压力组花费约 1.972 秒，但仍远小于 `promote_to_p` 因表格扩张增加的约 22.6 秒总成本。
5. cyclic family 中 `post_check` 始终保持 `|P|=1`，而 `promote_to_p` 强制 `|P|=|I|=k`。因此表格单元比率从 cyclic-24 的 24 倍增长到 cyclic-70 的 70 倍，耗时比率也从 2.64 倍扩大到 9.48 倍。

## 6. 理想 EQ 与真实/PAC EQ

当前 Oracle 已知完整目标 DFA，通过 symmetric difference 精确执行 EQ。因此本报告中的 EQ 是理想、快速、内存内的 EQ，不能直接代表黑盒系统或 PAC 测试成本。

令真实环境中每次 EQ 的平均成本为 `C`，用下面的模型替换当前理想 EQ：

```text
Adjusted time = measured non-EQ time + EQ count × C
```

由本轮数据估算：

| 范围 | `promote_to_p` 追平所需平均 EQ 成本 |
|---|---:|
| 中等组 | 约 1.97 ms / EQ |
| 压力组 | 约 98.28 ms / EQ |
| 全部 36 例 | 约 83.11 ms / EQ |

普通组中 `promote_to_p` 的内部总耗时已经略低，不需要额外 EQ 成本即可接近或追平。

这个估算说明：

- 在便宜的精确 DFA EQ 下，`post_check` 明显更适合中大型目标。
- 在昂贵的真实系统/PAC EQ 下，`promote_to_p` 减少 EQ 的价值可能抵消表格扩张。
- 压力越大，`promote_to_p` 的追平门槛也会上升；不能只看到 EQ 次数下降，还必须同时计入 `P×S` 表维护成本。
- PAC EQ 经常在找到反例后提前停止，因此真正结论需要实现 PAC teacher，记录每轮实际样本数和目标系统调用成本。

## 7. 结论

在当前精确、理想 EQ 的测试模型下：

- 普通规模：两种策略总体接近，`promote_to_p` 在部分小例子中略快。
- 中等规模：`post_check` 开始稳定领先，组总耗时约低 38.9%。
- 压力规模：`post_check` 全部胜出，`promote_to_p` 组总耗时约为其 7.02 倍。

当前最合理的工程选择仍是：

```text
默认策略：post_check
实验策略：promote_to_p
```

但 `promote_to_p` 不应被简单判定为无效。它稳定减少 EQ，并把外部 teacher 工作转化为本地 Right Consistency 工作。如果未来目标是黑盒程序、远程服务或 PAC teacher，一次 EQ 的真实成本达到几十到上百毫秒后，策略胜负可能改变。下一轮真正有判别力的实验应当使用随机/PAC EQ，并把 EQ 样本数、外部调用时间和最终泛化误差纳入报告。

## 8. 未来的工作

1. Commutative Language：

​	Cyclic-n:  $\Sigma^* a \Sigma^*$, $\Sigma^* a \Sigma^* \cap \Sigma^* b \Sigma^*$ , Even number of $a$

2. Star-freeness decision

3. Blackbox case: Non-regular language. (EQ, MQ limitation?) 

   If EQ is not passed for 1 time, then increase the resource limitation: Ex. the number of example in EQ, total time, the accuracy of hypothesis model.

   Watch the size of $P$. 

   The correctness of EQ?  Random example	

4. Advantages of promote_to_P

   Direct construction (Without bypassing DFA)

   EQ cost 

   Accuracy

   Disadvantage: Table size is too large.



---

# Report

## 1. Objective

This benchmark compares two integrated learning strategies:

- `post_check`: run Monoid Consistency Check after language equivalence and add a left context to `P` only when a witness is found.
- `promote_to_p`: immediately promote every new `I` representative into `P`, rely on Right Consistency, and never run Monoid Consistency Check.

The benchmark measures runtime, MQ/EQ counts, ideal EQ time, table size, `P` size, Monoid Check cost, and Right Consistency refinements across ordinary, medium, and stress workloads.

## 2. Methodology

- 12 cases per group, 36 target languages in total.
- Ordinary: 1 warm-up plus 25 measured runs per strategy and case.
- Medium: 1 warm-up plus 15 measured runs per strategy and case.
- Stress: 1 warm-up plus 7 measured runs per strategy and case.
- Strategy order alternated between repetitions; reported runtime is the median.
- Debug and verbose output were disabled; `max_p_length=1`.
- Every run verified final language equivalence and equality between learned state count and target syntactic monoid size.
- Every `promote_to_p` run asserted zero Monoid Consistency Checks.
- The formal benchmark executed 1,200 learner runs, all of which passed validation.

The detailed case-level values are listed in the Chinese tables above; the tables use language-independent case identifiers. Raw JSON data and the reproducible runner are linked in Section 2 of the Chinese report.

## 3. Aggregate Results

Group times are sums of per-case median runtimes. A difference within 5% is treated as practically close.

| Group | Cases | `post_check` | `promote_to_p` | Promote/Post | Post wins | Promote wins | Close |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ordinary | 12 | 5.687 ms | 5.494 ms | 0.97x | 2 | 4 | 6 |
| Medium | 12 | 109.188 ms | 178.694 ms | 1.64x | 10 | 0 | 2 |
| Stress | 12 | 3,764.268 ms | 26,405.117 ms | 7.02x | 12 | 0 | 0 |
| Total | 36 | 3,879.143 ms | 26,589.305 ms | 6.85x | 24 | 4 | 8 |

The strategies are effectively tied on ordinary cases. `post_check` becomes consistently faster in the medium group and wins every stress case.

## 4. Query and Structure Summary

| Group | MQ Post/Promote | EQ Post/Promote | EQ time Post/Promote | Post Monoid Check | Cells Post/Promote | Cell ratio | `Σ|P|` Post/Promote |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ordinary | 418 / 420 | 18 / 16 | 1.816 / 1.691 ms | 0.808 ms | 312 / 859 | 2.75x | 19 / 45 |
| Medium | 11,042 / 11,086 | 89 / 46 | 23.363 / 8.159 ms | 52.071 ms | 7,420 / 55,195 | 7.44x | 36 / 182 |
| Stress | 59,466 / 60,009 | 384 / 143 | 1,113.019 / 69.586 ms | 1,971.978 ms | 73,314 / 2,073,236 | 28.28x | 56 / 458 |
| Total | 70,926 / 71,515 | 491 / 205 | 1,138.198 / 79.436 ms | 2,024.857 ms | 81,046 / 2,129,290 | 26.27x | 111 / 685 |

Key findings:

1. `promote_to_p` issued only 589 more MQs, an increase of 0.83%, because the query cache collapses many table cells onto identical strings.
2. Its aggregate final table size was nevertheless 26.27 times larger. Cached MQs do not remove table construction, row-vector, dictionary, and consistency-maintenance costs.
3. `promote_to_p` avoided 286 EQs, exactly matching its 286 Right Consistency refinements. It shifts part of suffix refinement from EQ counterexamples into local consistency work.
4. On the cyclic family, `post_check` retained `|P|=1`, whereas `promote_to_p` forced `|P|=|I|=k`. The table-size ratio rose from 24x at cyclic-24 to 70x at cyclic-70, and the runtime ratio rose from 2.64x to 9.48x.

## 5. Ideal EQ Versus Real/PAC EQ

The current Oracle owns the complete target DFA and implements exact EQ through symmetric difference. These EQs are ideal in-memory operations and do not represent black-box conformance testing or PAC sampling costs.

Using the cost model:

```text
Adjusted time = measured non-EQ time + EQ count × C
```

where `C` is the average real-world cost of one EQ, the estimated break-even points for `promote_to_p` are:

| Scope | Average EQ cost required to break even |
|---|---:|
| Medium group | approximately 1.97 ms / EQ |
| Stress group | approximately 98.28 ms / EQ |
| All 36 cases | approximately 83.11 ms / EQ |

Therefore, `post_check` is clearly preferable when EQ is a cheap exact DFA operation. When EQ requires hundreds of black-box executions or PAC samples, the reduction in EQ count may compensate for the larger observation table. This must be measured with a real PAC teacher because failed EQ rounds may stop early after finding a counterexample.

## 6. Conclusion

Under the current exact and ideal EQ model:

- Ordinary workloads: the two strategies are effectively tied.
- Medium workloads: `post_check` is consistently faster.
- Stress workloads: `post_check` wins all cases, while `promote_to_p` takes 7.02 times the aggregate median runtime.

The recommended engineering default remains `post_check`, with `promote_to_p` retained as an experimental strategy for expensive-teacher settings. The next decisive benchmark should replace exact EQ with randomized/PAC EQ and report actual samples per EQ, external system time, and held-out language agreement.
