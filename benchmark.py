import time
from learner import Learner
from oracle import Oracle  # 假设你把朴素转换算法放在了这里
from regex_converter import regex_to_minimal_dfa

def benchmark(regex_str):
    # alphabet = {'a'}
    alphabet = {'a','b'}
    # alphabet = {'a','b','c'}
    # --- 过程 A: 你的改进版 L* 算法 ---
    # 重新实例化，确保环境干净
    target_dfa = regex_to_minimal_dfa(regex_str, alphabet)
    oracle = Oracle(target_dfa)
    learner = Learner(oracle, alphabet, max_p_length=2)

    print(f">> 开始执行：改进版 L* 算法 (Integrated Learning)")
    start_a = time.perf_counter()
    learned_dfa = learner.learn(depth = 1)  # 内部已经包含了 Monoid 探测
    end_a = time.perf_counter()
    time_a = end_a - start_a
    learner.display_observation_table()
    # --- 过程 B: 朴素算法 (学 DFA -> 暴力转 Monoid) ---
    # 1. 模拟学最小 DFA 的时间 (这里可以直接用过程 A 中 L* 阶段的时间，或者重新跑一个纯 L*)
    # 为了简单，我们直接测“已知最小 DFA 转换到 Monoid”的时间
    target_dfa = regex_to_minimal_dfa(regex_str, alphabet)


    print(f">> 开始执行：朴素转换算法 (DFA to Monoid Conversion)")
    start_b = time.perf_counter()
    # 假设这个函数内部调用了第三方库或朴素 BFS 来求转换半群
    m_size, _ = oracle._compute_transition_monoid_for_test(target_dfa)
    end_b = time.perf_counter()
    time_b = end_b - start_b

    # --- 结果汇总 ---
    print("\n" + "=" * 50)
    print(f"对比报告 - 正则: {regex_str}")
    print("=" * 50)
    print(f"你的算法 (黑盒探测) 时间: {time_a:.10f} s")
    print(f"朴素算法 (白盒转换) 时间: {time_b:.10f} s")
    print(f"查询总数 (MQ): {learner.mq_count}")
    print(f"Monoid 规模: {m_size}")
    print("-" * 50)

    if time_a < time_b:
        print(f"结论: 你的算法比朴素转换快了 {((time_b - time_a) / time_b) * 100:.10f}%")
    else:
        print(f"结论: 朴素转换在已知模型下仍具有计算优势")
    print("=" * 50)



# benchmark("(c|ab|aaca)*(a|c|aba)(aca|b|aa)*(aa|ca|ab)(c|ab|aaca)*|c*")
# benchmark("()|(a|b)|(a|b)(a|b)|(a|b)(a|b)(a|b)b*")
# benchmark("a"*10 + "b"*10 + "c"*10)

benchmark("(ab)*")

