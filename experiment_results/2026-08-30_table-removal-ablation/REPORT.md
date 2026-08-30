# 物化观察表删除消融实验 / Materialized Observation Table Removal Ablation

## 中文报告

### 1. 目的

本实验只研究一个实现变化：删除主 `Learner` 中以 `(i,p,s)` 为键的物化三维 `table`，改由全局 `query_cache` 按需生成虚拟观察表。算法、两种策略、Oracle、反例处理和理论 Cells 定义均保持不变。

实验回答两个问题：删除后是否保持完全相同的学习轨迹，以及本地时间和峰值内存是否发生变化。它不是 Post 与 Promote 的新一轮胜负实验。

### 2. 版本与方法

- 旧实现：Git 标签 `experiment-2026-08-25-v1` 中的原始 `learner.py`，运行时直接由 Git 载入。
- 新实现：基于 `bf0de65` 的当前工作树，`learner.py` SHA-256 为 `feb304ba304a6af086794d3e4c77da68b434d6f4207d0275b07aa410e228bee9`。
- 正式用例：24 个；计时重复 25 次；峰值内存重复 5 次；每种实现另有 1 次预热。
- 新旧实现逐次交错并轮换先后顺序；Oracle 构造在计时外完成。
- 本地时间定义为总学习时间减去学习器记录的理想 EQ 时间。峰值内存通过独立 `tracemalloc` 运行测量，因此不会污染正式计时样本。
- 每次运行均验证最终语言、monoid 状态数、MQ、EQ、`P/I/S`、跳过 EQ、Monoid Check、right consistency 次数和完整 `query_cache`。任一差异都会中止实验。

### 3. 分层选择

对 Commutative 与 Star-free 两组、字母表大小 1–4，按 8.25 历史数据中的 Promote Cells 排序，各取最小值、下中位数和最大值，避免主观挑选有利用例。

| 组别 | 字母表大小 | Low | Mid | High |
|---|---:|---|---|---|
| commutative | 1 | `comm_at_least_a_a_1` | `comm_at_least_a_a_4` | `comm_mod_a_a_9` |
| commutative | 2 | `comm_at_least_ab_a_1` | `comm_exact_ab_b_3` | `comm_mod_ab_b_9` |
| commutative | 3 | `comm_at_least_abc_a_1` | `comm_exact_abc_c_3` | `comm_mod_abc_c_9` |
| commutative | 4 | `comm_at_least_abcd_a_1` | `comm_exact_abcd_d_3` | `comm_contains_all_abcd` |
| star_free | 1 | `sf_at_least_a_a_1` | `sf_exact_a_a_2` | `sf_at_least_a_a_6` |
| star_free | 2 | `sf_at_least_ab_a_1` | `sf_at_most_ab_a_3` | `sf_contains_ab_aba` |
| star_free | 3 | `sf_at_least_abc_a_1` | `sf_at_least_abc_a_4` | `sf_at_least_abc_c_6` |
| star_free | 4 | `sf_at_least_abcd_a_1` | `sf_contains_abcd_bb` | `sf_ordered_abcd_acdb` |

### 4. 汇总结果

| 组别 | 策略 | 用例 | Σ本地中位时间 旧/新 ms | 聚合变化 | 逐例变化中位数 | 峰值内存中位数 旧/新 KiB | 内存变化中位数 |
|---|---|---:|---:|---:|---:|---:|---:|
| 合计 | Post | 24 | 70.175/63.198 | -9.9% | -13.3% | 54.4/47.4 | -11.9% |
| 合计 | Promote | 24 | 77.634/65.522 | -15.6% | -16.6% | 64.5/34.5 | -44.5% |
| 交换语言 | Post | 12 | 53.928/49.054 | -9.0% | -12.4% | 58.6/51.0 | -11.5% |
| 交换语言 | Promote | 12 | 59.289/50.615 | -14.6% | -15.6% | 64.8/35.2 | -45.6% |
| Star-free | Post | 12 | 16.247/14.144 | -12.9% | -13.7% | 47.5/40.4 | -12.6% |
| Star-free | Promote | 12 | 18.345/14.907 | -18.7% | -19.7% | 64.5/34.5 | -44.2% |

这里的峰值内存中位数是逐例运行峰值的中位数，不是把所有语言同时装入内存。`Σ本地中位时间` 是把各语言的中位时间相加，用于表示这一固定测试套件的聚合工作量。

### 5. 逐语言数据

| 语言 | 组别/层级 | 字母表大小 | DFA/Monoid | 策略 | Cells | 本地时间旧/新 ms | 时间变化 | 峰值内存旧/新 KiB | 内存变化 | MQ/EQ |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| `comm_at_least_a_a_1` | 交换/low | 1 | 2/2 | Post | 3 | 0.166/0.146 | -11.5% | 13.7/12.5 | -9.1% | 4/1 |
| `comm_at_least_a_a_1` | 交换/low | 1 | 2/2 | Promote | 6 | 0.177/0.152 | -14.1% | 14.2/12.6 | -10.9% | 4/1 |
| `comm_at_least_a_a_4` | 交换/mid | 1 | 5/5 | Post | 24 | 0.433/0.406 | -6.3% | 27.0/23.8 | -12.1% | 13/4 |
| `comm_at_least_a_a_4` | 交换/mid | 1 | 5/5 | Promote | 120 | 0.559/0.443 | -20.7% | 40.2/26.3 | -34.6% | 13/3 |
| `comm_mod_a_a_9` | 交换/high | 1 | 9/9 | Post | 80 | 1.228/1.177 | -4.2% | 86.5/79.2 | -8.4% | 25/8 |
| `comm_mod_a_a_9` | 交换/high | 1 | 9/9 | Promote | 720 | 2.135/1.966 | -7.9% | 134.0/45.1 | -66.3% | 26/3 |
| `comm_at_least_ab_a_1` | 交换/low | 2 | 2/2 | Post | 5 | 0.197/0.167 | -15.3% | 14.7/13.0 | -11.2% | 7/1 |
| `comm_at_least_ab_a_1` | 交换/low | 2 | 2/2 | Promote | 10 | 0.181/0.154 | -15.0% | 15.4/13.4 | -13.2% | 7/1 |
| `comm_exact_ab_b_3` | 交换/mid | 2 | 5/5 | Post | 44 | 0.792/0.655 | -17.3% | 55.0/48.0 | -12.7% | 49/4 |
| `comm_exact_ab_b_3` | 交换/mid | 2 | 5/5 | Promote | 220 | 0.827/0.691 | -16.6% | 58.4/32.3 | -44.6% | 49/2 |
| `comm_mod_ab_b_9` | 交换/high | 2 | 9/9 | Post | 152 | 2.863/2.378 | -16.9% | 198.2/180.1 | -9.1% | 161/8 |
| `comm_mod_ab_b_9` | 交换/high | 2 | 9/9 | Promote | 1,368 | 4.394/3.448 | -21.5% | 250.7/65.1 | -74.1% | 162/3 |
| `comm_at_least_abc_a_1` | 交换/low | 3 | 2/2 | Post | 7 | 0.201/0.172 | -14.4% | 16.2/14.3 | -11.8% | 10/1 |
| `comm_at_least_abc_a_1` | 交换/low | 3 | 2/2 | Promote | 14 | 0.207/0.173 | -16.3% | 17.1/14.6 | -14.9% | 10/1 |
| `comm_exact_abc_c_3` | 交换/mid | 3 | 5/5 | Post | 64 | 1.038/0.888 | -14.5% | 62.3/53.9 | -13.5% | 85/4 |
| `comm_exact_abc_c_3` | 交换/mid | 3 | 5/5 | Promote | 320 | 1.126/0.883 | -21.6% | 71.3/38.1 | -46.6% | 85/2 |
| `comm_mod_abc_c_9` | 交换/high | 3 | 9/9 | Post | 224 | 3.913/3.395 | -13.2% | 304.9/275.5 | -9.6% | 297/8 |
| `comm_mod_abc_c_9` | 交换/high | 3 | 9/9 | Promote | 2,016 | 6.097/5.451 | -10.6% | 307.2/87.9 | -71.4% | 298/3 |
| `comm_at_least_abcd_a_1` | 交换/low | 4 | 2/2 | Post | 9 | 0.216/0.210 | -2.7% | 16.9/14.8 | -12.1% | 13/1 |
| `comm_at_least_abcd_a_1` | 交换/low | 4 | 2/2 | Promote | 18 | 0.213/0.199 | -6.3% | 18.2/15.4 | -15.3% | 13/1 |
| `comm_exact_abcd_d_3` | 交换/mid | 4 | 5/5 | Post | 84 | 1.298/1.170 | -9.9% | 76.6/65.8 | -14.1% | 121/4 |
| `comm_exact_abcd_d_3` | 交换/mid | 4 | 5/5 | Promote | 420 | 1.405/1.055 | -24.9% | 97.8/47.5 | -51.4% | 121/2 |
| `comm_contains_all_abcd` | 交换/high | 4 | 16/16 | Post | 975 | 41.585/38.292 | -7.9% | 2529.4/2406.5 | -4.9% | 10,319/15 |
| `comm_contains_all_abcd` | 交换/high | 4 | 16/16 | Promote | 10,400 | 41.968/35.999 | -14.2% | 1725.6/686.8 | -60.2% | 6,954/4 |
| `sf_at_least_a_a_1` | Star-free/low | 1 | 2/2 | Post | 3 | 0.162/0.161 | -0.0% | 13.7/12.5 | -9.1% | 4/1 |
| `sf_at_least_a_a_1` | Star-free/low | 1 | 2/2 | Promote | 6 | 0.174/0.151 | -13.3% | 14.2/12.6 | -10.9% | 4/1 |
| `sf_exact_a_a_2` | Star-free/mid | 1 | 4/4 | Post | 15 | 0.401/0.357 | -11.0% | 23.0/21.3 | -7.5% | 10/3 |
| `sf_exact_a_a_2` | Star-free/mid | 1 | 4/4 | Promote | 60 | 0.374/0.312 | -16.6% | 25.3/17.8 | -29.6% | 10/2 |
| `sf_at_least_a_a_6` | Star-free/high | 1 | 7/7 | Post | 48 | 0.717/0.718 | +0.2% | 41.2/34.2 | -17.1% | 19/6 |
| `sf_at_least_a_a_6` | Star-free/high | 1 | 7/7 | Promote | 336 | 1.139/0.892 | -21.7% | 70.1/36.3 | -48.2% | 19/4 |
| `sf_at_least_ab_a_1` | Star-free/low | 2 | 2/2 | Post | 5 | 0.196/0.161 | -18.1% | 14.7/13.0 | -11.2% | 7/1 |
| `sf_at_least_ab_a_1` | Star-free/low | 2 | 2/2 | Promote | 10 | 0.196/0.161 | -17.7% | 15.4/13.4 | -13.2% | 7/1 |
| `sf_at_most_ab_a_3` | Star-free/mid | 2 | 5/5 | Post | 44 | 0.762/0.577 | -24.3% | 53.8/46.7 | -13.1% | 49/4 |
| `sf_at_most_ab_a_3` | Star-free/mid | 2 | 5/5 | Promote | 220 | 0.835/0.575 | -31.1% | 58.9/32.7 | -44.5% | 49/3 |
| `sf_contains_ab_aba` | Star-free/high | 2 | 4/12 | Post | 225 | 2.218/1.907 | -14.1% | 136.7/108.4 | -20.7% | 307/3 |
| `sf_contains_ab_aba` | Star-free/high | 2 | 4/12 | Promote | 900 | 2.733/2.385 | -12.7% | 173.5/68.4 | -60.6% | 319/2 |
| `sf_at_least_abc_a_1` | Star-free/low | 3 | 2/2 | Post | 7 | 0.224/0.194 | -13.4% | 16.2/14.3 | -11.8% | 10/1 |
| `sf_at_least_abc_a_1` | Star-free/low | 3 | 2/2 | Promote | 14 | 0.208/0.200 | -3.7% | 17.1/14.6 | -14.9% | 10/1 |
| `sf_at_least_abc_a_4` | Star-free/mid | 3 | 5/5 | Post | 64 | 0.922/0.746 | -19.1% | 60.0/51.5 | -14.2% | 85/4 |
| `sf_at_least_abc_a_4` | Star-free/mid | 3 | 5/5 | Promote | 320 | 1.253/0.851 | -32.1% | 71.3/37.8 | -47.0% | 85/3 |
| `sf_at_least_abc_c_6` | Star-free/high | 3 | 7/7 | Post | 132 | 2.009/1.998 | -0.5% | 162.7/145.6 | -10.5% | 175/6 |
| `sf_at_least_abc_c_6` | Star-free/high | 3 | 7/7 | Promote | 924 | 2.690/2.104 | -21.8% | 170.2/65.3 | -61.6% | 175/4 |
| `sf_at_least_abcd_a_1` | Star-free/low | 4 | 2/2 | Post | 9 | 0.211/0.203 | -4.1% | 16.9/14.8 | -12.1% | 13/1 |
| `sf_at_least_abcd_a_1` | Star-free/low | 4 | 2/2 | Promote | 18 | 0.256/0.176 | -31.1% | 18.2/15.4 | -15.3% | 13/1 |
| `sf_contains_abcd_bb` | Star-free/mid | 4 | 3/6 | Post | 100 | 1.127/0.928 | -17.7% | 70.4/55.7 | -20.9% | 163/2 |
| `sf_contains_abcd_bb` | Star-free/mid | 4 | 3/6 | Promote | 300 | 1.168/0.891 | -23.7% | 78.0/43.7 | -43.9% | 163/2 |
| `sf_ordered_abcd_acdb` | Star-free/high | 4 | 5/12 | Post | 784 | 7.298/6.195 | -15.1% | 472.7/373.2 | -21.0% | 1,512/4 |
| `sf_ordered_abcd_acdb` | Star-free/high | 4 | 5/12 | Promote | 2,352 | 7.318/6.209 | -15.2% | 439.6/190.8 | -56.6% | 1,512/2 |

### 6. 结论

- 最大时间改善出现在 `sf_at_least_abc_a_4` / `Promote`：-32.1%；最弱结果为 `sf_at_least_a_a_6` / `Post`：+0.2%。
- 最大峰值内存改善出现在 `comm_mod_ab_b_9` / `Promote`：-74.1%；最弱结果为 `comm_contains_all_abcd` / `Post`：-4.9%。
- 所有结构与查询轨迹断言均通过，因此此次变化是实现层消融，不改变算法产生的 MQ/EQ、最终集合或语言。
- 历史 8.25 JSON 中的 MQ、EQ、`P/I/S` 和 Cells 仍可继续使用；其本地时间对应旧物化实现，不能直接代表当前代码。

### 7. 边界

结果只反映当前机器、Python 版本和所选 24 个分层语言。微秒到毫秒级时间仍会受系统负载影响；本报告保留全部原始样本和四分位数，正式结论以方向、量级和跨用例一致性为主。下一阶段加入 MQ 计时后还需单独校准统计仪器开销。

---

## English Report

### 1. Objective

This ablation isolates one implementation change: removing the materialized `(i,p,s)` dictionary from the integrated learner and deriving the virtual observation table from the global MQ cache. The algorithms, strategies, oracle, counterexample handling, and theoretical Cells definition are unchanged.

### 2. Method

The materialized implementation is loaded directly from Git tag `experiment-2026-08-25-v1`. The virtual implementation uses learner SHA-256 `feb304ba304a6af086794d3e4c77da68b434d6f4207d0275b07aa410e228bee9`. The suite contains 24 stratified languages, with 25 interleaved timing repetitions, 5 independent peak-memory repetitions, and one warmup per implementation.

Every run requires identical language behavior, monoid state count, MQ/EQ counts, `P/I/S`, refinement counters, and complete MQ-cache contents. Timing and `tracemalloc` runs are separate.

### 3. Stratified Cases

| Group | Alphabet size | Low | Mid | High |
|---|---:|---|---|---|
| commutative | 1 | `comm_at_least_a_a_1` | `comm_at_least_a_a_4` | `comm_mod_a_a_9` |
| commutative | 2 | `comm_at_least_ab_a_1` | `comm_exact_ab_b_3` | `comm_mod_ab_b_9` |
| commutative | 3 | `comm_at_least_abc_a_1` | `comm_exact_abc_c_3` | `comm_mod_abc_c_9` |
| commutative | 4 | `comm_at_least_abcd_a_1` | `comm_exact_abcd_d_3` | `comm_contains_all_abcd` |
| star_free | 1 | `sf_at_least_a_a_1` | `sf_exact_a_a_2` | `sf_at_least_a_a_6` |
| star_free | 2 | `sf_at_least_ab_a_1` | `sf_at_most_ab_a_3` | `sf_contains_ab_aba` |
| star_free | 3 | `sf_at_least_abc_a_1` | `sf_at_least_abc_a_4` | `sf_at_least_abc_c_6` |
| star_free | 4 | `sf_at_least_abcd_a_1` | `sf_contains_abcd_bb` | `sf_ordered_abcd_acdb` |

### 4. Aggregate Results

| Group | Strategy | Cases | Sum median local old/new ms | Aggregate change | Median per-case change | Median peak old/new KiB | Median memory change |
|---|---|---:|---:|---:|---:|---:|---:|
| Total | Post | 24 | 70.175/63.198 | -9.9% | -13.3% | 54.4/47.4 | -11.9% |
| Total | Promote | 24 | 77.634/65.522 | -15.6% | -16.6% | 64.5/34.5 | -44.5% |
| Commutative | Post | 12 | 53.928/49.054 | -9.0% | -12.4% | 58.6/51.0 | -11.5% |
| Commutative | Promote | 12 | 59.289/50.615 | -14.6% | -15.6% | 64.8/35.2 | -45.6% |
| Star-free | Post | 12 | 16.247/14.144 | -12.9% | -13.7% | 47.5/40.4 | -12.6% |
| Star-free | Promote | 12 | 18.345/14.907 | -18.7% | -19.7% | 64.5/34.5 | -44.2% |

### 5. Per-language Results

| Language | Group/tier | Alphabet size | DFA/Monoid | Strategy | Cells | Local old/new ms | Time change | Peak old/new KiB | Memory change | MQ/EQ |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| `comm_at_least_a_a_1` | Commutative/low | 1 | 2/2 | Post | 3 | 0.166/0.146 | -11.5% | 13.7/12.5 | -9.1% | 4/1 |
| `comm_at_least_a_a_1` | Commutative/low | 1 | 2/2 | Promote | 6 | 0.177/0.152 | -14.1% | 14.2/12.6 | -10.9% | 4/1 |
| `comm_at_least_a_a_4` | Commutative/mid | 1 | 5/5 | Post | 24 | 0.433/0.406 | -6.3% | 27.0/23.8 | -12.1% | 13/4 |
| `comm_at_least_a_a_4` | Commutative/mid | 1 | 5/5 | Promote | 120 | 0.559/0.443 | -20.7% | 40.2/26.3 | -34.6% | 13/3 |
| `comm_mod_a_a_9` | Commutative/high | 1 | 9/9 | Post | 80 | 1.228/1.177 | -4.2% | 86.5/79.2 | -8.4% | 25/8 |
| `comm_mod_a_a_9` | Commutative/high | 1 | 9/9 | Promote | 720 | 2.135/1.966 | -7.9% | 134.0/45.1 | -66.3% | 26/3 |
| `comm_at_least_ab_a_1` | Commutative/low | 2 | 2/2 | Post | 5 | 0.197/0.167 | -15.3% | 14.7/13.0 | -11.2% | 7/1 |
| `comm_at_least_ab_a_1` | Commutative/low | 2 | 2/2 | Promote | 10 | 0.181/0.154 | -15.0% | 15.4/13.4 | -13.2% | 7/1 |
| `comm_exact_ab_b_3` | Commutative/mid | 2 | 5/5 | Post | 44 | 0.792/0.655 | -17.3% | 55.0/48.0 | -12.7% | 49/4 |
| `comm_exact_ab_b_3` | Commutative/mid | 2 | 5/5 | Promote | 220 | 0.827/0.691 | -16.6% | 58.4/32.3 | -44.6% | 49/2 |
| `comm_mod_ab_b_9` | Commutative/high | 2 | 9/9 | Post | 152 | 2.863/2.378 | -16.9% | 198.2/180.1 | -9.1% | 161/8 |
| `comm_mod_ab_b_9` | Commutative/high | 2 | 9/9 | Promote | 1,368 | 4.394/3.448 | -21.5% | 250.7/65.1 | -74.1% | 162/3 |
| `comm_at_least_abc_a_1` | Commutative/low | 3 | 2/2 | Post | 7 | 0.201/0.172 | -14.4% | 16.2/14.3 | -11.8% | 10/1 |
| `comm_at_least_abc_a_1` | Commutative/low | 3 | 2/2 | Promote | 14 | 0.207/0.173 | -16.3% | 17.1/14.6 | -14.9% | 10/1 |
| `comm_exact_abc_c_3` | Commutative/mid | 3 | 5/5 | Post | 64 | 1.038/0.888 | -14.5% | 62.3/53.9 | -13.5% | 85/4 |
| `comm_exact_abc_c_3` | Commutative/mid | 3 | 5/5 | Promote | 320 | 1.126/0.883 | -21.6% | 71.3/38.1 | -46.6% | 85/2 |
| `comm_mod_abc_c_9` | Commutative/high | 3 | 9/9 | Post | 224 | 3.913/3.395 | -13.2% | 304.9/275.5 | -9.6% | 297/8 |
| `comm_mod_abc_c_9` | Commutative/high | 3 | 9/9 | Promote | 2,016 | 6.097/5.451 | -10.6% | 307.2/87.9 | -71.4% | 298/3 |
| `comm_at_least_abcd_a_1` | Commutative/low | 4 | 2/2 | Post | 9 | 0.216/0.210 | -2.7% | 16.9/14.8 | -12.1% | 13/1 |
| `comm_at_least_abcd_a_1` | Commutative/low | 4 | 2/2 | Promote | 18 | 0.213/0.199 | -6.3% | 18.2/15.4 | -15.3% | 13/1 |
| `comm_exact_abcd_d_3` | Commutative/mid | 4 | 5/5 | Post | 84 | 1.298/1.170 | -9.9% | 76.6/65.8 | -14.1% | 121/4 |
| `comm_exact_abcd_d_3` | Commutative/mid | 4 | 5/5 | Promote | 420 | 1.405/1.055 | -24.9% | 97.8/47.5 | -51.4% | 121/2 |
| `comm_contains_all_abcd` | Commutative/high | 4 | 16/16 | Post | 975 | 41.585/38.292 | -7.9% | 2529.4/2406.5 | -4.9% | 10,319/15 |
| `comm_contains_all_abcd` | Commutative/high | 4 | 16/16 | Promote | 10,400 | 41.968/35.999 | -14.2% | 1725.6/686.8 | -60.2% | 6,954/4 |
| `sf_at_least_a_a_1` | Star-free/low | 1 | 2/2 | Post | 3 | 0.162/0.161 | -0.0% | 13.7/12.5 | -9.1% | 4/1 |
| `sf_at_least_a_a_1` | Star-free/low | 1 | 2/2 | Promote | 6 | 0.174/0.151 | -13.3% | 14.2/12.6 | -10.9% | 4/1 |
| `sf_exact_a_a_2` | Star-free/mid | 1 | 4/4 | Post | 15 | 0.401/0.357 | -11.0% | 23.0/21.3 | -7.5% | 10/3 |
| `sf_exact_a_a_2` | Star-free/mid | 1 | 4/4 | Promote | 60 | 0.374/0.312 | -16.6% | 25.3/17.8 | -29.6% | 10/2 |
| `sf_at_least_a_a_6` | Star-free/high | 1 | 7/7 | Post | 48 | 0.717/0.718 | +0.2% | 41.2/34.2 | -17.1% | 19/6 |
| `sf_at_least_a_a_6` | Star-free/high | 1 | 7/7 | Promote | 336 | 1.139/0.892 | -21.7% | 70.1/36.3 | -48.2% | 19/4 |
| `sf_at_least_ab_a_1` | Star-free/low | 2 | 2/2 | Post | 5 | 0.196/0.161 | -18.1% | 14.7/13.0 | -11.2% | 7/1 |
| `sf_at_least_ab_a_1` | Star-free/low | 2 | 2/2 | Promote | 10 | 0.196/0.161 | -17.7% | 15.4/13.4 | -13.2% | 7/1 |
| `sf_at_most_ab_a_3` | Star-free/mid | 2 | 5/5 | Post | 44 | 0.762/0.577 | -24.3% | 53.8/46.7 | -13.1% | 49/4 |
| `sf_at_most_ab_a_3` | Star-free/mid | 2 | 5/5 | Promote | 220 | 0.835/0.575 | -31.1% | 58.9/32.7 | -44.5% | 49/3 |
| `sf_contains_ab_aba` | Star-free/high | 2 | 4/12 | Post | 225 | 2.218/1.907 | -14.1% | 136.7/108.4 | -20.7% | 307/3 |
| `sf_contains_ab_aba` | Star-free/high | 2 | 4/12 | Promote | 900 | 2.733/2.385 | -12.7% | 173.5/68.4 | -60.6% | 319/2 |
| `sf_at_least_abc_a_1` | Star-free/low | 3 | 2/2 | Post | 7 | 0.224/0.194 | -13.4% | 16.2/14.3 | -11.8% | 10/1 |
| `sf_at_least_abc_a_1` | Star-free/low | 3 | 2/2 | Promote | 14 | 0.208/0.200 | -3.7% | 17.1/14.6 | -14.9% | 10/1 |
| `sf_at_least_abc_a_4` | Star-free/mid | 3 | 5/5 | Post | 64 | 0.922/0.746 | -19.1% | 60.0/51.5 | -14.2% | 85/4 |
| `sf_at_least_abc_a_4` | Star-free/mid | 3 | 5/5 | Promote | 320 | 1.253/0.851 | -32.1% | 71.3/37.8 | -47.0% | 85/3 |
| `sf_at_least_abc_c_6` | Star-free/high | 3 | 7/7 | Post | 132 | 2.009/1.998 | -0.5% | 162.7/145.6 | -10.5% | 175/6 |
| `sf_at_least_abc_c_6` | Star-free/high | 3 | 7/7 | Promote | 924 | 2.690/2.104 | -21.8% | 170.2/65.3 | -61.6% | 175/4 |
| `sf_at_least_abcd_a_1` | Star-free/low | 4 | 2/2 | Post | 9 | 0.211/0.203 | -4.1% | 16.9/14.8 | -12.1% | 13/1 |
| `sf_at_least_abcd_a_1` | Star-free/low | 4 | 2/2 | Promote | 18 | 0.256/0.176 | -31.1% | 18.2/15.4 | -15.3% | 13/1 |
| `sf_contains_abcd_bb` | Star-free/mid | 4 | 3/6 | Post | 100 | 1.127/0.928 | -17.7% | 70.4/55.7 | -20.9% | 163/2 |
| `sf_contains_abcd_bb` | Star-free/mid | 4 | 3/6 | Promote | 300 | 1.168/0.891 | -23.7% | 78.0/43.7 | -43.9% | 163/2 |
| `sf_ordered_abcd_acdb` | Star-free/high | 4 | 5/12 | Post | 784 | 7.298/6.195 | -15.1% | 472.7/373.2 | -21.0% | 1,512/4 |
| `sf_ordered_abcd_acdb` | Star-free/high | 4 | 5/12 | Promote | 2,352 | 7.318/6.209 | -15.2% | 439.6/190.8 | -56.6% | 1,512/2 |

### 6. Conclusions

The strongest local-time improvement is `sf_at_least_abc_a_4` / `Promote` at -32.1%; the weakest result is `sf_at_least_a_a_6` / `Post` at +0.2%.

All trajectory assertions passed. Historical query counts and structural measurements remain valid, while historical local timings describe the old materialized implementation. The next MQ-instrumented experiment must separately calibrate measurement overhead.
