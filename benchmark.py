import argparse
import sys
import time
from collections import deque
from dataclasses import dataclass

from automata.fa.dfa import DFA

from classic_lstar_learner import ClassicLearner
from classic_lstar_oracle import ClassicOracle
from learner import Learner
from oracle import Oracle
from regex_converter import regex_to_minimal_dfa


DEFAULT_ALPHABET = {"a", "b"}
OBSERVATION_TABLE_FILE = "observation_table.txt"
DEFAULT_REGEX = None

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


@dataclass
class BaselineResult:
    """保存经典二步法的产物和计时结果。"""

    learner: ClassicLearner
    oracle: ClassicOracle
    monoid_size: int
    monoid_dfa: DFA
    lstar_time: float
    monoid_time: float
    monoid_dfa_build_time: float

    @property
    def total_time(self):
        """经典 L* 学习时间加上 DFA 转 monoid 时间。"""
        return self.lstar_time + self.monoid_time + self.monoid_dfa_build_time


@dataclass
class IntegratedResult:
    """保存一体化 learner 的实例和整体运行时间。"""

    name: str
    strategy: str
    learner: object
    total_time: float
    table_file: str


def benchmark(regex_str, debug_mode=False, alphabet=None, integrated_strategy="both"):
    """运行一次完整实验：构造目标 DFA、跑两种算法、输出对比报告。"""
    alphabet = DEFAULT_ALPHABET if alphabet is None else set(alphabet)
    strategies = normalize_integrated_strategies(integrated_strategy)

    print_header(regex_str)
    target_dfa = regex_to_minimal_dfa(regex_str, alphabet)

    baseline = run_classic_baseline(target_dfa, alphabet)
    integrated_results = [
        run_integrated_learner(target_dfa, alphabet, debug_mode, strategy)
        for strategy in strategies
    ]

    for result in integrated_results:
        result.learner.display_observation_table(result.table_file)

    print_report(regex_str, target_dfa, baseline, integrated_results)


def normalize_integrated_strategies(integrated_strategy):
    """Return the integrated learner strategies requested by the benchmark caller."""
    if integrated_strategy == "both":
        return ("post_check", "promote_to_p_monoid_check")
    if isinstance(integrated_strategy, str):
        strategies = (integrated_strategy,)
    else:
        strategies = tuple(integrated_strategy)

    valid = {"post_check", "promote_to_p_monoid_check"}
    unknown = set(strategies) - valid
    if unknown:
        raise ValueError(f"Unknown integrated strategy: {sorted(unknown)}")
    return strategies


def run_classic_baseline(target_dfa, alphabet):
    """执行经典 baseline：先用 L* 学 DFA，再把学到的 DFA 转成 transition monoid。"""
    print("\n>> 开始执行: 过程 A [经典二步法: Classic L* -> Monoid]")

    classic_oracle = ClassicOracle(target_dfa)
    classic_learner = ClassicLearner(classic_oracle, alphabet)

    start_lstar = time.perf_counter()
    learned_dfa = classic_learner.learn()
    lstar_time = time.perf_counter() - start_lstar

    start_monoid = time.perf_counter()
    monoid_elements, base_trans, initial_index, final_indices = compute_transition_monoid_data(learned_dfa, alphabet)
    monoid_time = time.perf_counter() - start_monoid

    start_monoid_dfa = time.perf_counter()
    monoid_dfa = build_monoid_dfa(monoid_elements, base_trans, initial_index, final_indices, alphabet)
    monoid_dfa_build_time = time.perf_counter() - start_monoid_dfa

    return BaselineResult(
        learner=classic_learner,
        oracle=classic_oracle,
        monoid_size=len(monoid_elements),
        monoid_dfa=monoid_dfa,
        lstar_time=lstar_time,
        monoid_time=monoid_time,
        monoid_dfa_build_time=monoid_dfa_build_time,
    )


def compute_transition_monoid_data(dfa, alphabet):
    """Return transition monoid elements and the metadata needed to build its DFA."""
    alphabet = sorted(alphabet)
    states = sorted(list(dfa.states))
    state_to_idx = {state: idx for idx, state in enumerate(states)}
    needs_dead_state = any(len(dfa.transitions.get(state, {})) < len(alphabet) for state in states)

    dead_state_idx = len(states) if needs_dead_state else -1
    vector_len = len(states) + 1 if needs_dead_state else len(states)
    base_trans = {}

    for char in alphabet:
        trans_vec = []
        for state in states:
            if char in dfa.transitions.get(state, {}):
                next_state = dfa.transitions[state][char]
                trans_vec.append(state_to_idx[next_state])
            else:
                trans_vec.append(dead_state_idx)

        if needs_dead_state:
            trans_vec.append(dead_state_idx)

        base_trans[char] = tuple(trans_vec)

    identity = tuple(range(vector_len))
    monoid_elements = {identity}
    queue = deque([identity])

    while queue:
        current_vec = queue.popleft()
        for char in alphabet:
            base_vec = base_trans[char]
            new_vec = tuple(base_vec[index] for index in current_vec)
            if new_vec not in monoid_elements:
                monoid_elements.add(new_vec)
                queue.append(new_vec)

    initial_index = state_to_idx[dfa.initial_state]
    final_indices = {state_to_idx[state] for state in dfa.final_states}
    return monoid_elements, base_trans, initial_index, final_indices


def build_monoid_dfa(monoid_elements, base_trans, initial_index, final_indices, alphabet):
    """Build the Cayley-style DFA whose states are transition monoid elements."""
    alphabet = sorted(alphabet)
    sorted_elements = sorted(monoid_elements)
    element_to_state = {element: f"m{idx}" for idx, element in enumerate(sorted_elements)}
    transitions = {state: {} for state in element_to_state.values()}

    for element in sorted_elements:
        current_state = element_to_state[element]
        for char in alphabet:
            base_vec = base_trans[char]
            next_element = tuple(base_vec[index] for index in element)
            transitions[current_state][char] = element_to_state[next_element]

    identity = tuple(range(len(sorted_elements[0])))
    final_states = {
        element_to_state[element]
        for element in sorted_elements
        if element[initial_index] in final_indices
    }

    return DFA(
        states=set(element_to_state.values()),
        input_symbols=set(alphabet),
        transitions=transitions,
        initial_state=element_to_state[identity],
        final_states=final_states,
    )


def run_integrated_learner(target_dfa, alphabet, debug_mode, strategy):
    name = integrated_strategy_name(strategy)
    print(f"\n>> Start Process B [{name}]")

    oracle = Oracle(target_dfa)
    learner = build_integrated_learner(oracle, alphabet, debug_mode, strategy)

    start = time.perf_counter()
    learner.learn()
    total_time = time.perf_counter() - start

    table_file = (
        OBSERVATION_TABLE_FILE
        if strategy == "post_check"
        else f"observation_table_{strategy}.txt"
    )
    return IntegratedResult(
        name=name,
        strategy=strategy,
        learner=learner,
        total_time=total_time,
        table_file=table_file,
    )

def integrated_strategy_name(strategy):
    """Human-readable label for an integrated learner strategy."""
    names = {
        "post_check": "Integrated L* + Monoid Consistency Check",
        "promote_to_p_monoid_check": "Integrated L* + Promote I to P + Monoid Check",
    }
    return names[strategy]


def build_integrated_learner(oracle, alphabet, debug_mode, strategy):
    """构造一体化 learner；debug_mode 控制是否输出快照文件。"""
    if debug_mode:
        print("   [开启 Debug] 将详细记录每次表格的代数分裂轨迹...")

    return Learner(
        oracle,
        alphabet,
        max_p_length=1,
        monoid_strategy=strategy,
        debug_mode=debug_mode,
        verbose=debug_mode,
    )


def print_header(regex_str):
    """打印单次 benchmark 的开场信息。"""
    print("\n" + "*" * 65)
    print(f"🎯 正在测试正则: {regex_str}")
    print("*" * 65)


def print_report(regex_str, target_dfa, baseline, integrated_results):
    """汇总目标自动机特征和两种算法的性能指标。"""
    print("\n" + "=" * 65)
    print(f"📊 最终对比报告 - 正则: {regex_str}")
    print("=" * 65)

    print("【代数特征】")
    print(f"  - Minimal DFA 状态数 : {len(target_dfa.states)}")
    print(f"  - Monoid 规模        : {baseline.monoid_size}")
    print(f"  - Monoid DFA 状态数  : {len(baseline.monoid_dfa.states)}")

    print_baseline_report(baseline)
    for integrated in integrated_results:
        print_integrated_report(integrated)
    print_conclusion(baseline.total_time, integrated_results)


def print_baseline_report(result):
    """打印经典二步法的时间、查询次数和 EQ 占比。"""
    eq_percent = percent(result.learner.eq_time, result.lstar_time)

    print("\n【过程 A: 经典朴素二步法 (Baseline)】")
    print(f"  - 阶段1 (L* 学 DFA)  : {result.lstar_time:.6f} s")
    print(f"      └─ 其中 EQ 耗时  : {result.learner.eq_time:.6f} s (占比 {eq_percent:.1f}%)")
    print(f"  - 阶段2 (转 Monoid)  : {result.monoid_time:.6f} s")
    print(f"  - 阶段3 (Monoid DFA) : {result.monoid_dfa_build_time:.6f} s")
    print(f"  - 阶段1+2+3 总耗时   : {result.total_time:.6f} s")
    print(f"  - MQ 查询总数        : {result.oracle.mq_count} 次")
    print(f"  - EQ 查询总数        : {result.learner.eq_count} 次")


def print_integrated_report(result):
    """打印一体化算法的时间、查询次数和 EQ 占比。"""
    learner = result.learner
    eq_percent = percent(learner.eq_time, result.total_time)
    eq_count = getattr(learner, "eq_count", "未统计")

    print(f"\n[Process B: {result.name}]")
    print(f"  - Strategy              : {result.strategy}")
    print(f"  - 总耗时             : {result.total_time:.6f} s")
    print(f"      └─ 其中 EQ 耗时  : {learner.eq_time:.6f} s (占比 {eq_percent:.1f}%)")
    print(f"  - MQ 查询总数        : {learner.mq_count} 次")
    print(f"  - EQ 查询总数        : {eq_count} 次")
    print(f"  - 跳过 EQ 次数        : {learner.skipped_eq_count} 次")
    print(f"  - Monoid check time     : {learner.monoid_probe_time:.6f} s")
    print(f"  - I-promoted-to-P count : {learner.promoted_i_to_p_count}")
    print(f"  - Observation table     : {result.table_file}")


def print_conclusion(baseline_time, integrated_results):
    """根据总耗时给出本次实验的简单胜负判断。"""
    print("-" * 65)
    fastest = min(integrated_results, key=lambda result: result.total_time)
    if fastest.total_time < baseline_time:
        speedup = baseline_time / fastest.total_time
        print(f"Best integrated strategy: {fastest.strategy} ({speedup:.2f}x faster than baseline)")
    else:
        print(f"Baseline remains faster than the best integrated strategy ({fastest.strategy}).")
    print("=" * 65 + "\n")


def percent(part, total):
    """安全计算百分比，避免耗时过小时除零。"""
    return 0.0 if total == 0 else part / total * 100


def generate_cyclic_group_regex(k):
    """生成一个 'a' 的数量为 k 的整数倍的正则表达式。"""
    core = "b*a" * k
    return f"({core})*b*"


def default_regex():
    if DEFAULT_REGEX is not None:
        return DEFAULT_REGEX
    # 常用测试样例：
    regex = generate_cyclic_group_regex(70)
    # regex = "(a|b)*aab"
    # regex = "aab"
    # regex = "(aa|bbb)*"
    # regex = "(aaa|bbb)*"
    # regex = "(ab)*"
    # regex = "(ba)*"
    # regex = "b*(ab*ab*)*"
    # regex = "(b*ab*ab*a)*b*"
    # regex = "a" * 10 + "b"
    # regex = "a" * 20 + "b"
    # regex = "a" * 30 + "b"
    # regex = "(a|b)*abba"
    # regex = "a" * 5 + "b"
    regex = "(a|bb)*ab(a|b)*baa"
    # regex = "aab(a|b)*ba(a|bb)*"
    return regex


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strategy",
        choices=("post_check", "promote_to_p_monoid_check", "both"),
        default="both",
        help="Integrated learner variant to benchmark.",
    )
    parser.add_argument(
        "--regex",
        default=None,
        help="Regex target. Defaults to DEFAULT_REGEX or generate_cyclic_group_regex(50).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable learner debug snapshots and verbose logging.",
    )
    args = parser.parse_args()

    regex = default_regex()

    if args.regex is not None:
        regex = args.regex
    # --strategy   post_check | promote_to_p_monoid_check | both
    # --regex      指定测试用正则
    # --debug      打开 verbose 日志和 debug_snapshots
    benchmark(regex, debug_mode=args.debug, integrated_strategy=args.strategy)
