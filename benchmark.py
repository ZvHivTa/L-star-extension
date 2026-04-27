import time
from regex_converter import regex_to_minimal_dfa
from oracle import Oracle
from learner import Learner
from classic_lstar_learner import ClassicLearner
from classic_lstar_oracle import ClassicOracle
from learner_debug import LearnerDebug

def benchmark(regex_str,debug_mode=False,alphabet = {'a','b'}):
    # alphabet = {'a', 'b','c'}
    print("\n" + "*" * 65)
    print(f"🎯 正在测试正则: {regex_str}")
    print("*" * 65)

    target_dfa = regex_to_minimal_dfa(regex_str, alphabet)

    # ==========================================
    # 过程 A: 经典朴素二步法 (Naive Baseline)
    # 阶段1: Classic L* 学习 DFA (黑盒)
    # 阶段2: DFA 暴力转 Monoid (白盒)
    # ==========================================
    print("\n>> 开始执行: 过程 A [经典二步法: Classic L* -> Monoid]")
    classic_oracle = ClassicOracle(target_dfa)
    classic_learner = ClassicLearner(classic_oracle, alphabet)

    # 阶段 1: 学习 DFA
    start_a1 = time.perf_counter()
    learned_dfa_classic = classic_learner.learn()
    end_a1 = time.perf_counter()
    time_lstar_classic = end_a1 - start_a1

    # 阶段 2: 将学到的 DFA 暴力转换为 Monoid
    # （这里我们借用旧版 oracle 里的工具函数来跑转换矩阵）
    tool_oracle = Oracle(target_dfa,max_ce_length=1000)
    start_a2 = time.perf_counter()
    m_size, _ = tool_oracle._compute_transition_monoid_for_test(learned_dfa_classic)
    end_a2 = time.perf_counter()
    time_conv_classic = end_a2 - start_a2

    total_time_classic = time_lstar_classic + time_conv_classic




    # ==========================================
    # 过程 B: 你的改进版一体化算法 (Integrated Learner)
    # ==========================================
    print("\n>> 开始执行: 过程 B [改进版一体化 L* (位图化 + 纵向扩张)]")
    oracle_integrated = Oracle(target_dfa)

    if debug_mode:
        print("   [开启 Debug] 将详细记录每次表格的代数分裂轨迹...")
        learner_integrated = LearnerDebug(oracle_integrated, alphabet)
    else:
        learner_integrated = Learner(oracle_integrated, alphabet, max_p_length=1)
    start_b = time.perf_counter()
    result_syntactic_monoid = learner_integrated.learn()
    end_b = time.perf_counter()
    total_time_integrated = end_b - start_b

    # 打印观测表到文件
    learner_integrated.display_observation_table("observation_table.txt")

    # ==========================================
    # 结果汇总与对比
    # ==========================================
    print("\n" + "=" * 65)
    print(f"📊 最终对比报告 - 正则: {regex_str}")
    print("=" * 65)

    print(f"【代数特征】")
    print(f"  - Minimal DFA 状态数 : {len(target_dfa.states)}")
    print(f"  - Monoid 规模        : {m_size}")

    print(f"\n【过程 A: 经典朴素二步法 (Baseline)】")
    print(f"  - 阶段1 (L* 学 DFA)  : {time_lstar_classic:.6f} s")
    print(
        f"      └─ 其中 EQ 耗时  : {classic_learner.eq_time:.6f} s (占比 {(classic_learner.eq_time / time_lstar_classic) * 100:.1f}%)")
    print(f"  - 阶段2 (转 Monoid)  : {time_conv_classic:.6f} s")
    print(f"  - 阶段1+2 总耗时     : {total_time_classic:.6f} s")
    print(f"  - MQ 查询总数        : {classic_oracle.mq_count} 次")
    print(f"  - EQ 查询总数        : {classic_learner.eq_count} 次")

    print(f"\n【过程 B: 你的改进版一体化 L*】")
    print(f"  - 总耗时             : {total_time_integrated:.6f} s")
    print(
        f"      └─ 其中 EQ 耗时  : {learner_integrated.eq_time:.6f} s (占比 {(learner_integrated.eq_time / total_time_integrated) * 100:.1f}%)")
    print(f"  - MQ 查询总数        : {learner_integrated.mq_count} 次")
    # 注意：这里的 EQ 次数需要你在 learner.py 里也加上 eq_count 统计，或者粗略看输出里有几次“收到反例”
    print("-" * 65)
    if total_time_integrated < total_time_classic:
        speedup = total_time_classic / total_time_integrated
        print(f"🏆 结论: 你的算法赢了！比朴素基线快了 {speedup:.2f} 倍！")
    else:
        print(f"💡 结论: 朴素基线依然领先，需要继续排查 Python 的循环开销。")
    print("=" * 65 + "\n")
    # result_syntactic_monoid.show_diagram(path='syntactic_monoid.png')


    # 打印 Graphviz DOT 源码
    # print_acceptor(result_syntactic_monoid)





# 循环群语言
def generate_cyclic_group_regex(k):
    """
    生成一个 'a' 的数量为 k 的整数倍的正则表达式。
    例如 k=3: (b*ab*ab*a)*b*
    """
    # 构造核心的 a 序列，并在中间和两端穿插 b*
    core = "b*a" * k
    # 加上克林闭包，并在最后补上 b* 以允许以 b 结尾
    regex = f"({core})*b*"
    return regex

if __name__ == "__main__":
    cyclic_regex = generate_cyclic_group_regex(50)
    # benchmark(cyclic_regex)
    # 热身测试：简单的结构
    # regex = "(a|b)*aab"
    # regular language
    regex = "()|(a|b)|(a|b)(a|b)|(a|b)(a|b)(a|b)b*"
    # regex = "aab"
    # regex = "(aa|bbb)*"
    # regex = "(ab)*"

    # regex = "(a|b)*a"
    # regex = "(a|b)*aab"
    # regex = "b*(ab*ab*)*"
    # regex = "(b*ab*ab*a)*b*"
    # regex = "a"*10 + "b"


    # alphabet = {'a', 'b', 'c'}
    # regex = "(a|b)*a"
    # regex = "(a|b|c)*bac(a|b|c)*caca(a|b|c)*cc"
    # regex = "(c|ab|aaca)*(a|c|aba)(aca|b|aa)*(aa|ca|ab)(c|ab|aaca)*|c*"
    # benchmark(regex,True,alphabet)
    benchmark(regex, True)