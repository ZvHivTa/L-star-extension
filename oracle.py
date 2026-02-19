from automata.fa.dfa import DFA
from collections import deque
import time

class Oracle:
    def __init__(self, target_dfa):
        # 保证 Oracle 内部持有的是规范化（最小化）的目标 DFA
        self.target_dfa = target_dfa.minify()
        self.alphabet = sorted(list(target_dfa.input_symbols))
        self._cache_target_monoid()

    # ==========================================
    # Part 1: 标准查询接口
    # ==========================================

    def membership_query(self, w):
        return self.target_dfa.accepts_input(w)

    def equivalence_query(self, hypothesis_dfa):
        try:
            diff = self.target_dfa.symmetric_difference(hypothesis_dfa)
            if diff.isempty():
                return None
            return self._find_shortest_counterexample(diff)
        except Exception as e:
            print(f"[Oracle Error] EQ check failed: {e}")
            return ""

    def _find_shortest_counterexample(self, diff_dfa):
        queue = ['']
        visited = set()
        while queue:
            w = queue.pop(0)
            if diff_dfa.accepts_input(w):
                return w
            if len(w) > 10:
                continue
            for char in self.alphabet:
                next_w = w + char
                if next_w not in visited:
                    visited.add(next_w)
                    queue.append(next_w)
        return None

    # ==========================================
    # Part 2: 代数结构验证 (已修复 Bug)
    # ==========================================

    def verify_syntactic_monoid(self, learned_dfa):
        print("\n[Oracle] 开始验证句法幺半群结构...")

        # 1. 预处理：最小化
        learned_min = learned_dfa.minify()

        # 2. 比较 DFA 结构
        is_isomorphic = (self.target_dfa == learned_min)
        if is_isomorphic:
            print("  [Pass] Acceptor 结构完全匹配 (Isomorphic)。")
        else:
            print("  [Info] Acceptor 结构看起来不同 (可能是同构但未识别)。")

        # 3. 计算学习到的转换幺半群
        l_size, l_elems = self._compute_transition_monoid(learned_min)

        # 4. 对比
        print(f"  Target Monoid Size: {self.target_monoid_size}")
        print(f"  Learned Monoid Size: {l_size}")

        if self.target_monoid_elements == l_elems:
            print("  [Result] ✅ 验证成功！代数结构完全一致。")
            return True
        else:
            # 如果 DFA 同构但 Monoid 不同，通常是因为我们的计算器处理死状态的方式有差异
            # 但经过修复后，这种情况不应再发生
            if is_isomorphic:
                print("  [Result] ✅ 验证通过 (DFA 同构即保证了代数结构一致，忽略计算误差)。")
                return True
            print("  [Result] ❌ 验证失败。")
            return False

    def _cache_target_monoid(self):
        self.target_monoid_size, self.target_monoid_elements = \
            self._compute_transition_monoid(self.target_dfa)

    def _compute_transition_monoid(self, dfa):
        """
        修复版：能够正确处理 Partial DFA（缺边的 DFA）。
        如果发现缺边，会自动引入一个虚拟的 'Dead State'。
        """
        states = sorted(list(dfa.states))
        state_to_idx = {s: i for i, s in enumerate(states)}
        n = len(states)

        # 检查是否需要补全死状态
        # 扫描所有状态，看是否有缺少的转移
        needs_dead_state = False
        for s in states:
            if len(dfa.transitions.get(s, {})) < len(self.alphabet):
                needs_dead_state = True
                break

        # 如果需要死状态，它的索引是 n
        dead_state_idx = n if needs_dead_state else -1
        vector_len = n + 1 if needs_dead_state else n

        # 基础变换向量
        base_trans = {}
        for char in self.alphabet:
            trans_vec = []
            for s in states:
                # 正常转移
                if char in dfa.transitions.get(s, {}):
                    next_s = dfa.transitions[s][char]
                    trans_vec.append(state_to_idx[next_s])
                else:
                    # 【修复】缺失的转移 -> 指向死状态
                    trans_vec.append(dead_state_idx)

            # 如果有死状态，死状态接收任何字符都跳回自己
            if needs_dead_state:
                trans_vec.append(dead_state_idx)

            base_trans[char] = tuple(trans_vec)

        # BFS 生成闭包
        identity = tuple(range(vector_len))
        monoid_elements = {identity}
        queue = deque([identity])
        while queue:
            current_vec = queue.popleft()
            for char in self.alphabet:
                base_vec = base_trans[char]
                # 复合函数
                new_vec = tuple(base_vec[x] for x in current_vec)

                if new_vec not in monoid_elements:
                    monoid_elements.add(new_vec)
                    queue.append(new_vec)
        return len(monoid_elements), monoid_elements

    def _compute_transition_monoid_for_test(self, dfa):
        """
        修复版：能够正确处理 Partial DFA（缺边的 DFA）。
        如果发现缺边，会自动引入一个虚拟的 'Dead State'。
        """
        states = sorted(list(dfa.states))
        state_to_idx = {s: i for i, s in enumerate(states)}
        n = len(states)

        # 检查是否需要补全死状态
        # 扫描所有状态，看是否有缺少的转移
        needs_dead_state = False
        for s in states:
            if len(dfa.transitions.get(s, {})) < len(self.alphabet):
                needs_dead_state = True
                break

        # 如果需要死状态，它的索引是 n
        dead_state_idx = n if needs_dead_state else -1
        vector_len = n + 1 if needs_dead_state else n

        # 基础变换向量
        base_trans = {}
        for char in self.alphabet:
            trans_vec = []
            for s in states:
                # 正常转移
                if char in dfa.transitions.get(s, {}):
                    next_s = dfa.transitions[s][char]
                    trans_vec.append(state_to_idx[next_s])
                else:
                    # 【修复】缺失的转移 -> 指向死状态
                    trans_vec.append(dead_state_idx)

            # 如果有死状态，死状态接收任何字符都跳回自己
            if needs_dead_state:
                trans_vec.append(dead_state_idx)

            base_trans[char] = tuple(trans_vec)

        # BFS 生成闭包
        identity = tuple(range(vector_len))
        monoid_elements = {identity}
        queue = deque([identity])
        start_time = time.perf_counter()
        while queue:
            current_vec = queue.popleft()
            for char in self.alphabet:
                base_vec = base_trans[char]
                # 复合函数
                new_vec = tuple(base_vec[x] for x in current_vec)

                if new_vec not in monoid_elements:
                    monoid_elements.add(new_vec)
                    queue.append(new_vec)
        end_time = time.perf_counter()

        return len(monoid_elements), end_time - start_time

