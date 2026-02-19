# 文件名: classic_learner.py
import time
from automata.fa.dfa import DFA


class ClassicLearner:
    def __init__(self, oracle, alphabet):
        self.oracle = oracle
        self.alphabet = sorted(list(alphabet))

        # 经典 L* 的两大核心集合: S (行前缀/状态代表), E (列后缀/区分实验)
        self.S = {''}
        self.E = {''}
        self.table = {}  # 单元格缓存，避免重复查询
        self.state_to_rep = {}  # 记录 DFA 状态对应的最短代表前缀 (RS算法需要)

    def _ask(self, s, e):
        """带有单元格缓存的查询"""
        if (s, e) not in self.table:
            self.table[(s, e)] = self.oracle.membership_query(s + e)
        return self.table[(s, e)]

    def _get_row(self, s):
        """获取行向量 (使用最朴素的 Tuple)"""
        sorted_E = sorted(list(self.E), key=lambda x: (len(x), x))
        return tuple(self._ask(s, e) for e in sorted_E)

    def _is_closed(self):
        """封闭性检查: S·Sigma 中的行必须都在 S 中见过"""
        rows_in_S = {self._get_row(s) for s in self.S}

        for s in sorted(list(self.S), key=lambda x: (len(x), x)):
            for a in self.alphabet:
                sa = s + a
                if self._get_row(sa) not in rows_in_S:
                    self.S.add(sa)
                    return False
        return True

    def _is_consistent(self):
        """一致性检查: 行为相同的两行，接上同一个字母后，行为依然要相同"""
        S_list = sorted(list(self.S), key=lambda x: (len(x), x))

        for i in range(len(S_list)):
            for j in range(i + 1, len(S_list)):
                s1, s2 = S_list[i], S_list[j]

                if self._get_row(s1) == self._get_row(s2):
                    for a in self.alphabet:
                        row_s1a = self._get_row(s1 + a)
                        row_s2a = self._get_row(s2 + a)

                        if row_s1a != row_s2a:
                            # 找出是哪一个已有的后缀 e 区分了它们
                            sorted_E = sorted(list(self.E), key=lambda x: (len(x), x))
                            for idx, e in enumerate(sorted_E):
                                if row_s1a[idx] != row_s2a[idx]:
                                    # 将 a+e 作为全新的精确后缀加入 E
                                    self.E.add(a + e)
                                    return False
        return True

    def _build_hypothesis(self):
        """构建假设 DFA"""
        states = set()
        row_to_state = {}
        self.state_to_rep = {}

        unique_rows = sorted(list({self._get_row(s) for s in self.S}))
        for idx, r in enumerate(unique_rows):
            state_name = f"q{idx}"
            states.add(state_name)
            row_to_state[r] = state_name

            # 找到对应这个行的最短前缀，作为状态的代表 (Representative)
            rep = next(s for s in sorted(list(self.S), key=lambda x: (len(x), x)) if self._get_row(s) == r)
            self.state_to_rep[state_name] = rep

        initial_state = row_to_state[self._get_row('')]
        final_states = set()
        transitions = {st: {} for st in states}

        for s in self.S:
            row_s = self._get_row(s)
            curr_state = row_to_state[row_s]

            if self._ask(s, ''):
                final_states.add(curr_state)

            for a in self.alphabet:
                row_sa = self._get_row(s + a)
                transitions[curr_state][a] = row_to_state[row_sa]

        return DFA(
            states=states,
            input_symbols=set(self.alphabet),
            transitions=transitions,
            initial_state=initial_state,
            final_states=final_states
        )

    def learn(self):
        """带有 Rivest & Schapire (RS) 二分查找优化的 L* 循环"""
        start_time = time.perf_counter()
        self.eq_time = 0.0  # <--- 【新增】初始化 EQ 耗时统计
        self.eq_count = 0  # <--- 【新增】顺便统计一下 EQ 调用次数

        while True:
            if not self._is_closed():
                continue

            hypothesis = self._build_hypothesis()
            eq_start = time.perf_counter()
            counterexample = self.oracle.equivalence_query(hypothesis)
            self.eq_time += (time.perf_counter() - eq_start)
            self.eq_count += 1

            if counterexample is None:
                self.learn_time = time.perf_counter() - start_time
                return hypothesis

            # ==============================================================
            # 【核心】Rivest & Schapire (RS) 精准后缀查找算法 (二分法)
            # ==============================================================
            w = counterexample
            m = len(w)

            # 1. 在当前的假设 DFA 中，描绘出吃掉这个反例的状态轨迹
            reps = []
            curr = hypothesis.initial_state
            reps.append(self.state_to_rep[curr])
            for char in w:
                curr = hypothesis.transitions[curr][char]
                reps.append(self.state_to_rep[curr])

            # reps[i] 代表在假设中，读取了 w 的前 i 个字符后，到达的状态的代表字符串。
            # Q_i 的定义: Oracle 对 ( reps[i] + w[i:] ) 的判定结果。

            low = 0
            high = m

            # 对于合法的反例，Q_0 一定不等于 Q_m。
            Q_low = self.oracle.membership_query(reps[low] + w[low:])
            Q_high = self.oracle.membership_query(reps[high] + w[high:])

            # 2. 二分查找断点 (Breakpoint)
            if Q_low != Q_high:
                while low + 1 < high:
                    mid = (low + high) // 2
                    Q_mid = self.oracle.membership_query(reps[mid] + w[mid:])

                    if Q_mid == Q_low:
                        low = mid
                    else:
                        high = mid

                # 3. 提取出引发分歧的后缀
                # 断点发生在 low 到 high 之间。此时的剩余后缀 w[high:] 即为精准后缀！
                distinguishing_suffix = w[high:]
                self.E.add(distinguishing_suffix)
            else:
                # 理论上不会发生，除非 Oracle 不一致，作为 Fallback 全加进去
                for i in range(1, m + 1):
                    self.E.add(w[-i:])