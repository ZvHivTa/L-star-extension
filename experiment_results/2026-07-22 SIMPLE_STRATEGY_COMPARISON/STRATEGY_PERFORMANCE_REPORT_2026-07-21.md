# `post_check` 与 `promote_to_p` 性能对比报告

测试日期：2026-07-21

## 1. 测试目的

本次测试比较一体化学习器的两种 Syntactic Monoid 学习策略：

- `post_check`：EQ 成功后执行 Monoid Consistency Check，发现不一致时继续细化观察表。
- `promote_to_p`：将 `I` 中的代表元提升到 `P`，通过 Right Consistency 细化观察表，不执行 Monoid Consistency Check。

重点比较总耗时、MQ、EQ、Monoid Check 开销，以及 `P` 的扩张情况。

## 2. 测试方法

- 字母表固定为 `{a, b}`。
- 使用与 `benchmark.py` 相同的学习器配置：`max_p_length=1`。
- 关闭 verbose 和 debug 文件输出，避免调试 I/O 干扰计时。
- 每个用例、每种策略先预热 1 次，再正式运行 25 次。
- 两种策略交替运行，尽量降低运行顺序带来的系统误差。
- 总耗时使用 25 次运行的中位数。
- 每次运行都检查学习结果的状态数是否等于目标 syntactic monoid 的状态数。
- 额外断言 `promote_to_p` 的 Monoid Consistency Check 次数必须为 0。

复现命令：

```powershell
python -m experiments.compare_strategies
```

## 3. 测试结果

### 3.1 总耗时

| 用例                                           | Minimal DFA | Monoid |  `post_check` | `promote_to_p` | 较快策略                 |
| ---------------------------------------------- | ----------: | -----: | ------------: | -------------: | ------------------------ |
| `(ab)*`                                        |           2 |      6 |      0.664 ms |   **0.559 ms** | `promote_to_p`，约快 16% |
| `(a|b)*aab`                                    |           4 |      8 |  **1.156 ms** |       1.264 ms | `post_check`，约快 9%    |
| `b*(ab*ab*)*`                                  |           2 |      2 |      0.237 ms |   **0.233 ms** | 基本持平                 |
| `(aa|bbb)*`                                    |           4 |     23 |  **6.864 ms** |      10.527 ms | `post_check`，约快 35%   |
| ()\|(a\|b)\|(a\|b)(a\|b)\|(a\|b)(a\|b)(a\|b)b* |           4 |     11 |  **2.441 ms** |       2.839 ms | `post_check`，约快 14%   |
| `(a|bb)*ab(a|b)*baa`                           |           7 |     32 | **23.889 ms** |      51.798 ms | `post_check`，约快 54%   |
| cyclic group 12                                |          12 |     12 |  **6.624 ms** |       8.691 ms | `post_check`，约快 24%   |

7 个用例的中位耗时相加：

- `post_check`：约 41.88 ms。
- `promote_to_p`：约 75.91 ms。
- 在本组用例中，`post_check` 赢得 5 项，`promote_to_p` 赢得 2 项，其中一项基本持平。

### 3.2 查询与细化统计

| 用例 | 策略 | MQ | EQ | 跳过 EQ | Monoid Check 次数 | Monoid Check 耗时 | Right Consistency 细化 | 最终 `|P|` |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `(ab)*` | `post_check` | 69 | 2 | 1 | 2 | 0.116 ms | 0 | 2 |
|  | `promote_to_p` | 71 | 1 | 0 | 0 | 0 | 1 | 6 |
| `(a|b)*aab` | `post_check` | 163 | 3 | 2 | 3 | 0.294 ms | 0 | 3 |
|  | `promote_to_p` | 163 | 3 | 0 | 0 | 0 | 0 | 8 |
| `b*(ab*ab*)*` | `post_check` | 7 | 1 | 0 | 1 | 0.013 ms | 0 | 1 |
|  | `promote_to_p` | 7 | 1 | 0 | 0 | 0 | 0 | 2 |
| `(aa|bbb)*` | `post_check` | 1419 | 4 | 3 | 4 | 3.942 ms | 0 | 4 |
|  | `promote_to_p` | 1419 | 1 | 0 | 0 | 0 | 3 | 23 |
| ()\|(a\|b)\|(a\|b)(a\|b)\|(a\|b)(a\|b)(a\|b)b* | `post_check` | 374 | 4 | 3 | 4 | 0.862 ms | 0 | 4 |
|  | `promote_to_p` | 379 | 3 | 0 | 0 | 0 | 1 | 11 |
| `(a|bb)*ab(a|b)*baa` | `post_check` | 5015 | 7 | 3 | 4 | 18.705 ms | 0 | 4 |
|  | `promote_to_p` | 5015 | 5 | 0 | 0 | 0 | 2 | 32 |
| cyclic group 12 | `post_check` | 287 | 11 | 0 | 1 | 2.426 ms | 0 | 1 |
|  | `promote_to_p` | 288 | 4 | 0 | 0 | 0 | 7 | 12 |

## 4. 结果分析

`promote_to_p` 的设计目标已经实现：所有测试中 Monoid Consistency Check 的次数和耗时均为 0。它还经常减少实际 EQ 次数，例如：

- `(aa|bbb)*`：EQ 从 4 次降到 1 次。
- cyclic group 12：EQ 从 11 次降到 4 次。
- 当前复杂用例：EQ 从 7 次降到 5 次。

但是，减少 EQ 和取消 Monoid Check 没有直接转化为更低的总耗时。主要原因是 `promote_to_p` 会把 `I` 中的代表元加入 `P`，使 `P` 最终接近或等于整个 monoid：

- `(aa|bbb)*`：`|P|` 从 4 增加到 23。
- 当前复杂用例：`|P|` 从 4 增加到 32。
- cyclic group 12：`|P|` 从 1 增加到 12。

更大的 `P` 会增加闭合性检查、观察表维护、行比较和 Right Consistency 检查的工作量。在复杂用例 `(a|bb)*ab(a|b)*baa` 中，`post_check` 虽然有 18.705 ms 用于 Monoid Check，总耗时仍只有 23.889 ms；`promote_to_p` 不执行 Monoid Check，但总耗时达到 51.798 ms。这说明 `P` 扩张造成的额外维护成本已经超过被省略的检查成本。

MQ 数量在多数用例中相同或非常接近，说明当前性能差异主要不是由新的 membership query 数量造成，而是由观察表规模及其内部操作造成。

## 5. 结论

在当前实现和本组测试用例下，`post_check` 的总体效率更高，适合作为默认策略。

`promote_to_p` 的逻辑是正确且独立的实验路线，其优势是完全不依赖 Monoid Consistency Check，并能减少部分 EQ；但随着 syntactic monoid 增大，将整个 `I` 提升到 `P` 的代价会快速显现。目前更适合将其保留为实验策略，用于继续研究是否能通过选择性提升代表元、增量 Right Consistency 或缩小检查范围来降低维护成本。

需要注意：本报告反映的是当前 Python 实现和所选测试集合的结果，不代表两种算法在理论渐近复杂度上的最终比较。
