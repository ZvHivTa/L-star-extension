
import time
from oracle import Oracle
from learner import Learner
from regex_converter import regex_to_minimal_dfa  # <--- 导入新工具


def run_experiment():
    # ==========================================
    # 实验设置：在这里修改正则表达式即可！
    # ==========================================


    # regex = "(a|b)*aab"
    # regex = "b*(ab*ab*)*"

    # regular language
    # regex = "()|(a|b)|(a|b)(a|b)|(a|b)(a|b)(a|b)b*"
    # regex = "aab"
    regex = "(aa|bbb)*"

    # regex = "(c|ab|aaca)*(a|c|aba)(aca|b|aa)*(aa|ca|ab)(c|ab|aaca)*|c*"
    # alphabet
    alphabet = {'a', 'b'}

    print(f"--- start: Target Regex = /{regex}/ ---")

    # 1. minimal DFA

    target_dfa = regex_to_minimal_dfa(regex, alphabet)
    # 2. Oracle
    oracle = Oracle(target_dfa)

    monoid_len,transition_time = oracle._compute_transition_monoid_for_test(target_dfa)

    # 3. Learner
    # max_p_length, the initialization of set P


    learner = Learner(oracle, alphabet, max_p_length=1)

    # 4. algorithm
    start_learn = time.perf_counter()
    learned_acceptor = learner.learn(depth = 1)
    end_learn = time.perf_counter()

    learn_time = end_learn - start_learn

    # 5. print observation table (OT)
    learner.display_observation_table()

    # 6. Verification
    oracle.verify_syntactic_monoid(learned_acceptor)

    print(f"Algorithm Execution Time : {learn_time:.10f} seconds")
    print(f"DFA to Monoid Conv Time  : {transition_time:.10f} seconds")

if __name__ == "__main__":
    run_experiment()