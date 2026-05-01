import time
from dataclasses import dataclass

from classic_lstar_learner import ClassicLearner
from classic_lstar_oracle import ClassicOracle
from learner import Learner
from oracle import Oracle
from regex_converter import regex_to_minimal_dfa


DEFAULT_ALPHABET = {"a", "b"}
OBSERVATION_TABLE_FILE = "observation_table.txt"


@dataclass
class BaselineResult:
    """保存经典二步法的产物和计时结果。"""

    learner: ClassicLearner
    oracle: ClassicOracle
    monoid_size: int
    lstar_time: float
    monoid_time: float

    @property
    def total_time(self):
        """经典 L* 学习时间加上 DFA 转 monoid 时间。"""
        return self.lstar_time + self.monoid_time


@dataclass
class IntegratedResult:
    """保存一体化 learner 的实例和整体运行时间。"""

    learner: object
    total_time: float


def benchmark(regex_str, debug_mode=False, alphabet=None):
    """运行一次完整实验：构造目标 DFA、跑两种算法、输出对比报告。"""
    alphabet = DEFAULT_ALPHABET if alphabet is None else set(alphabet)

    print_header(regex_str)
    target_dfa = regex_to_minimal_dfa(regex_str, alphabet)

    baseline = run_classic_baseline(target_dfa, alphabet)
    integrated = run_integrated_learner(target_dfa, alphabet, debug_mode)

    integrated.learner.display_observation_table(OBSERVATION_TABLE_FILE)
    print_report(regex_str, target_dfa, baseline, integrated)


def run_classic_baseline(target_dfa, alphabet):
    """执行经典 baseline：先用 L* 学 DFA，再把学到的 DFA 转成 transition monoid。"""
    print("\n>> 开始执行: 过程 A [经典二步法: Classic L* -> Monoid]")

    classic_oracle = ClassicOracle(target_dfa)
    classic_learner = ClassicLearner(classic_oracle, alphabet)

    start_lstar = time.perf_counter()
    learned_dfa = classic_learner.learn()
    lstar_time = time.perf_counter() - start_lstar

    tool_oracle = Oracle(target_dfa, max_ce_length=1000)
    start_monoid = time.perf_counter()
    monoid_size, _ = tool_oracle._compute_transition_monoid_for_test(learned_dfa)
    monoid_time = time.perf_counter() - start_monoid

    return BaselineResult(
        learner=classic_learner,
        oracle=classic_oracle,
        monoid_size=monoid_size,
        lstar_time=lstar_time,
        monoid_time=monoid_time,
    )


def run_integrated_learner(target_dfa, alphabet, debug_mode):
    """执行改进版一体化 learner，直接在学习循环中加入 monoid 相关检查。"""
    print("\n>> 开始执行: 过程 B [改进版一体化 L* (位图化 + 纵向扩张)]")

    oracle = Oracle(target_dfa)
    learner = build_integrated_learner(oracle, alphabet, debug_mode)

    start = time.perf_counter()
    learner.learn()
    total_time = time.perf_counter() - start

    return IntegratedResult(learner=learner, total_time=total_time)


def build_integrated_learner(oracle, alphabet, debug_mode):
    """构造一体化 learner；debug_mode 控制是否输出快照文件。"""
    if debug_mode:
        print("   [开启 Debug] 将详细记录每次表格的代数分裂轨迹...")

    return Learner(oracle, alphabet, max_p_length=1, debug_mode=debug_mode)


def print_header(regex_str):
    """打印单次 benchmark 的开场信息。"""
    print("\n" + "*" * 65)
    print(f"🎯 正在测试正则: {regex_str}")
    print("*" * 65)


def print_report(regex_str, target_dfa, baseline, integrated):
    """汇总目标自动机特征和两种算法的性能指标。"""
    print("\n" + "=" * 65)
    print(f"📊 最终对比报告 - 正则: {regex_str}")
    print("=" * 65)

    print("【代数特征】")
    print(f"  - Minimal DFA 状态数 : {len(target_dfa.states)}")
    print(f"  - Monoid 规模        : {baseline.monoid_size}")

    print_baseline_report(baseline)
    print_integrated_report(integrated)
    print_conclusion(baseline.total_time, integrated.total_time)


def print_baseline_report(result):
    """打印经典二步法的时间、查询次数和 EQ 占比。"""
    eq_percent = percent(result.learner.eq_time, result.lstar_time)

    print("\n【过程 A: 经典朴素二步法 (Baseline)】")
    print(f"  - 阶段1 (L* 学 DFA)  : {result.lstar_time:.6f} s")
    print(f"      └─ 其中 EQ 耗时  : {result.learner.eq_time:.6f} s (占比 {eq_percent:.1f}%)")
    print(f"  - 阶段2 (转 Monoid)  : {result.monoid_time:.6f} s")
    print(f"  - 阶段1+2 总耗时     : {result.total_time:.6f} s")
    print(f"  - MQ 查询总数        : {result.oracle.mq_count} 次")
    print(f"  - EQ 查询总数        : {result.learner.eq_count} 次")


def print_integrated_report(result):
    """打印一体化算法的时间、查询次数和 EQ 占比。"""
    learner = result.learner
    eq_percent = percent(learner.eq_time, result.total_time)
    eq_count = getattr(learner, "eq_count", "未统计")

    print("\n【过程 B: 改进版一体化 L*】")
    print(f"  - 总耗时             : {result.total_time:.6f} s")
    print(f"      └─ 其中 EQ 耗时  : {learner.eq_time:.6f} s (占比 {eq_percent:.1f}%)")
    print(f"  - MQ 查询总数        : {learner.mq_count} 次")
    print(f"  - EQ 查询总数        : {eq_count} 次")


def print_conclusion(baseline_time, integrated_time):
    """根据总耗时给出本次实验的简单胜负判断。"""
    print("-" * 65)
    if integrated_time < baseline_time:
        speedup = baseline_time / integrated_time
        print(f"🏆 结论: 你的算法赢了！比朴素基线快了 {speedup:.2f} 倍！")
    else:
        print("💡 结论: 朴素基线依然领先，需要继续排查 Python 的循环开销。")
    print("=" * 65 + "\n")


def percent(part, total):
    """安全计算百分比，避免耗时过小时除零。"""
    return 0.0 if total == 0 else part / total * 100


def generate_cyclic_group_regex(k):
    """生成一个 'a' 的数量为 k 的整数倍的正则表达式。"""
    core = "b*a" * k
    return f"({core})*b*"


if __name__ == "__main__":
    # regex = "()|(a|b)|(a|b)(a|b)|(a|b)(a|b)(a|b)b*"

    # 常用测试样例：
    # regex = generate_cyclic_group_regex(50)
    regex = "(a|b)*aab"
    # regex = "aab"
    # regex = "(aa|bbb)*"
    # regex = "(ab)*"
    # regex = "b*(ab*ab*)*"
    # regex = "(b*ab*ab*a)*b*"
    # regex = "a" * 10 + "b"

    benchmark(regex, debug_mode=True)
