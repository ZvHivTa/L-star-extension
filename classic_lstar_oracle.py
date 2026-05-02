# 文件名: classic_oracle.py
from collections import deque

from automata.fa.dfa import DFA


class ClassicOracle:
    def __init__(self, target_dfa):
        self.target_dfa = target_dfa.minify()
        self.alphabet = sorted(list(target_dfa.input_symbols))
        self.mq_count = 0
        self.cache = {}

    def membership_query(self, w):
        if w in self.cache:
            return self.cache[w]

        self.mq_count += 1
        val = self.target_dfa.accepts_input(w)
        self.cache[w] = val
        return val

    def equivalence_query(self, hypothesis_dfa):
        try:
            diff = self.target_dfa.symmetric_difference(hypothesis_dfa)
            if diff.isempty():
                return None
            return self._find_shortest_counterexample(diff)
        except Exception as e:
            print(f"[Classic Oracle Error] EQ check failed: {e}")
            return ""

    def _find_shortest_counterexample(self, diff_dfa):
        """
        [极速版] 基于 DFA 状态图的 BFS 寻路。
        复杂度从 O(|Sigma|^L) 降维到 O(|States|)。
        即便反例长度是 1000，也能在 0.001 秒内找到！
        """
        initial_state = diff_dfa.initial_state
        final_states = diff_dfa.final_states

        # 如果初始状态就是接受状态，反例是空串
        if initial_state in final_states:
            return ""

        # 队列里存的是：(当前状态, 走到这里的字符串路径)
        queue = deque([(initial_state, "")])
        visited = {initial_state}

        while queue:
            curr_state, path = queue.popleft()

            # 遍历当前状态能走的边
            transitions = diff_dfa.transitions.get(curr_state, {})
            for char in self.alphabet:
                if char in transitions:
                    next_state = transitions[char]

                    if next_state not in visited:
                        next_path = path + char

                        # 如果到达了终点（发现分歧点），立刻返回路径！
                        if next_state in final_states:
                            return next_path

                        visited.add(next_state)
                        queue.append((next_state, next_path))

        return None
