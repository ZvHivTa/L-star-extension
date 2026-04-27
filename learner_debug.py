# 文件名: learner_debug.py
import time
import os
from automata.fa.dfa import DFA
from graphviz import Digraph
import shutil

class LearnerDebug:
    def __init__(self, teacher, alphabet, max_p_length=0, ce_strategy='breakpoint', debug_dir="debug_snapshots"):
        self.teacher = teacher
        self.alphabet = sorted(list(alphabet))
        self.query_cache = {}
        self.mq_count = 0
        self.ce_strategy = ce_strategy

        # --- Debug 专属配置 ---
        self.debug_dir = debug_dir
        if os.path.exists(self.debug_dir):
            shutil.rmtree(self.debug_dir)

        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)
            print(f"[Debug] 已创建快照目录: {self.debug_dir}")

        # --- 增量填表需要的快照 ---
        self.filled_rows = set()
        self.processed_P = set()
        self.processed_S = set()

        self.P = {''}
        self.S = {''}
        self.I = {''}
        self.table = {}
        self.state_to_rep = {}

    def _ask_teacher(self, string):
        if string in self.query_cache:
            return self.query_cache[string]
        val = self.teacher.membership_query(string)
        self.mq_count += 1
        self.query_cache[string] = val
        return val

    def _fill_cell(self, i, p, s):
        if (i, p, s) not in self.table:
            self.table[(i, p, s)] = self._ask_teacher(p + i + s)

    def get_row(self, i):
        sorted_P = sorted(list(self.P))
        sorted_S = sorted(list(self.S))
        row_values = []
        for p in sorted_P:
            for s in sorted_S:
                val = self.table.get((i, p, s))
                if val is None:
                    val = self._ask_teacher(p + i + s)
                    self.table[(i, p, s)] = val
                row_values.append(val)
        return tuple(row_values)

    # ==========================================
    # 核心重构 1: 纯正的单边右扩展填表
    # ==========================================
    def fill_table(self):
        # 彻底去除了 left_ext (Σ·I)，极大降低算力消耗
        right_ext = {i + a for i in self.I for a in self.alphabet}
        all_needed_rows = self.I | right_ext

        new_rows = all_needed_rows - self.filled_rows
        new_P = self.P - self.processed_P
        new_S = self.S - self.processed_S

        if new_rows:
            for i in new_rows:
                for p in self.P:
                    for s in self.S:
                        self._fill_cell(i, p, s)

        if new_P:
            for p in new_P:
                for i in all_needed_rows:
                    for s in self.S:
                        self._fill_cell(i, p, s)

        if new_S:
            for s in new_S:
                for i in all_needed_rows:
                    for p in self.P:
                        self._fill_cell(i, p, s)

        self.filled_rows.update(all_needed_rows)
        self.processed_P = self.P.copy()
        self.processed_S = self.S.copy()

    # ==========================================
    # 核心重构 2: 纯正的右闭合检查
    # ==========================================
    def is_closed_and_separable(self):
        rows_in_I = {self.get_row(i) for i in self.I}

        right_ext = {i + a for i in self.I for a in self.alphabet}
        all_extensions = sorted(list(right_ext), key=lambda x: (len(x), x))

        for ext in all_extensions:
            if ext in self.I:
                continue

            ext_row = self.get_row(ext)

            if ext_row not in rows_in_I:
                print(f"  [闭合拦截] 发现新状态: '{ext}'，将其提拔进主区 I")
                self.I.add(ext)
                return False

        return True

    def build_hypothesis(self):
        states = set()
        row_to_state = {}
        unique_rows = sorted(list({self.get_row(i) for i in self.I}))

        # ====== 核心改动点 ======
        for r in unique_rows:
            # 直接在这里把代表元找出来
            representative_i = next(i for i in self.I if self.get_row(i) == r)

            # 如果是空串，就叫 'ε'，否则就用原本的字符串 (比如 'a', 'ab')
            state_name = "q0" if representative_i == "" else representative_i

            states.add(state_name)
            row_to_state[r] = state_name
        # =========================

        initial_state = row_to_state[self.get_row('')]
        final_states = set()
        transitions = {s: {} for s in states}

        for r in unique_rows:
            # 因为在上面已经找过一次了，这里其实不需要重复找了，但我保留你的原逻辑结构
            representative_i = next(i for i in self.I if self.get_row(i) == r)
            curr_state = row_to_state[r]

            # 这行其实留不留都行了，因为 curr_state 本身就是 representative_i
            self.state_to_rep[curr_state] = representative_i

            if self._ask_teacher(representative_i):
                final_states.add(curr_state)

            for a in self.alphabet:
                next_i = representative_i + a
                next_row = self.get_row(next_i)
                if next_row in row_to_state:
                    transitions[curr_state][a] = row_to_state[next_row]
                else:
                    transitions[curr_state][a] = curr_state

        return DFA(
            states=states, input_symbols=set(self.alphabet),
            transitions=transitions, initial_state=initial_state, final_states=final_states
        )

    # ==========================================
    # 核心重构 3: O(M^3) 的精准左一致性自检
    # ==========================================
    def ensure_monoid_consistency(self):
        # 1. 建立 DFA 状态的行向量到代表元的映射
        row_to_rep = {}
        for i in sorted(list(self.I), key=lambda x: (len(x), x)):
            r = self.get_row(i)
            if r not in row_to_rep:
                row_to_rep[r] = i

        # 2. 精准打击：只拷问转移边界
        for u in self.I:
            for a in self.alphabet:
                t = u + a
                t_row = self.get_row(t)
                v = row_to_rep.get(t_row)

                if v is None or t == v:
                    continue

                # 3. 拿出 I 作为替身使者进行左一致性逼问
                for i in self.I:
                    for s in self.S:
                        q_t = self._ask_teacher(i + t + s)
                        q_v = self._ask_teacher(i + v + s)

                        if q_t != q_v:
                            print(
                                f"  🚨 [代数拦截] 伪装被撕裂！左前缀 '{i}' 在后缀 '{s}' 的照射下，拆散了边界 '{t}' 和代表元 '{v}'")
                            print(f"               >> 行动: 将 '{i}' 加入 P 集合！")
                            if i not in self.P:
                                self.P.add(i)
                            return False
        return True

    def print_acceptor(self, dfa_obj, filename="hypothesis"):
        """
        将生成的假设自动机画成状态图并保存。
        """
        # 强制加个 .txt 后缀
        filepath = f"{filename}.txt"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("digraph G {\n")
            f.write("  rankdir=LR;\n")

            # 1. 过滤并写入最终状态 (双圈)
            if dfa_obj.final_states:
                # 把状态名用双引号包裹，防止出现空格或特殊字符导致解析报错
                finals = ' '.join(f'"{s}"' for s in dfa_obj.final_states)
                f.write(f"  node [shape = doublecircle]; {finals};\n")

            f.write("  node [shape = circle];\n")

            # 2. 写入初始状态
            init_state = str(dfa_obj.initial_state)
            f.write(f'  start [shape=point]; start -> "{init_state}";\n')

            # 3. 写入所有转移关系
            for state, transitions in dfa_obj.transitions.items():
                for char, next_state in transitions.items():
                    f.write(f'  "{state}" -> "{next_state}" [label="{char}"];\n')

            f.write("}\n")

        print(f"  📝 [纯文本出图] DOT 源码已保存至: {filepath}")
        print(f"               >> 请将文件内容复制到 https://edotor.net/ 查看")

    # ==========================================
    # 核心控制流: 带有快照打卡机的主循环
    # ==========================================
    def learn(self):
        self.P, self.S, self.I = {''}, {''}, {''}
        self.total_start_time = time.perf_counter()
        self.lstar_pure_time, self.monoid_probe_time, self.eq_time, self.eq_count = 0.0, 0.0, 0.0, 0

        step = 1  # 快照计数器

        print("\n🚀 [LearnerDebug] 启动学习引擎 (快照模式)...")
        while True:
            t0 = time.perf_counter()
            self.fill_table()

            # --- 📸 记录快照 ---
            snapshot_filename = os.path.join(self.debug_dir, f"table_step_{step:03d}.txt")
            self.display_observation_table(snapshot_filename)
            print(f"\n▶️ [Step {step:03d}] 表格已更新，快照已保存")
            step += 1

            if not self.is_closed_and_separable():
                self.lstar_pure_time += (time.perf_counter() - t0)
                continue

            hypothesis = self.build_hypothesis()
            self.lstar_pure_time += (time.perf_counter() - t0)

            txt_filename = os.path.join(self.debug_dir, f"hypothesis_step_{step - 1:03d}")
            self.print_acceptor(hypothesis, filename=txt_filename)

            # print_acceptor(hypothesis)
            print(f"  [交卷] 闭合检查通过，向 Oracle 发起 EQ...")
            t1 = time.perf_counter()
            counterexample = self.teacher.equivalence_query(hypothesis)
            self.eq_time += (time.perf_counter() - t1)
            self.eq_count += 1

            if counterexample is not None:
                t2 = time.perf_counter()
                w = counterexample
                m = len(w)
                reps = []
                curr = hypothesis.initial_state
                reps.append(self.state_to_rep[curr])

                for char in w:
                    curr = hypothesis.transitions[curr][char]
                    reps.append(self.state_to_rep[curr])

                low, high = 0, m
                Q_low = self._ask_teacher(reps[low] + w[low:])
                Q_high = self._ask_teacher(reps[high] + w[high:])

                if Q_low != Q_high:
                    while low + 1 < high:
                        mid = (low + high) // 2
                        Q_mid = self._ask_teacher(reps[mid] + w[mid:])
                        if Q_mid == Q_low:
                            low = mid
                        else:
                            high = mid

                    distinguishing_suffix = w[high:]
                    prefix_to_add = reps[low]

                    print(f"  ⚔️ [反例拦截] 收反例 '{w}'! 二分断点定位: '{prefix_to_add}' | '{distinguishing_suffix}'")
                    print(
                        f"               >> 行动: 将后缀 '{distinguishing_suffix}' 加入 S，前缀 '{prefix_to_add}' 加入 P")
                    self.S.add(distinguishing_suffix)
                    # self.P.add(prefix_to_add)
                else:
                    self.S.add(w)
                    self.P.add(w)

                self.lstar_pure_time += (time.perf_counter() - t2)
                continue

            print(f"  [自检] EQ 及格！启动内部左一致性自检...")
            t3 = time.perf_counter()
            consistent = self.ensure_monoid_consistency()
            self.monoid_probe_time += (time.perf_counter() - t3)

            if not consistent:
                continue

            print(f"\n🎉 [完结] 句法幺半群代数结构完美收敛！")
            self.total_end_time = time.perf_counter()
            return hypothesis

    def display_observation_table(self, filename):
        sort_key = lambda x: (len(x), x)
        sorted_p = sorted(list(self.P), key=sort_key)
        sorted_s = sorted(list(self.S), key=sort_key)
        sorted_i = sorted(list(self.I), key=sort_key)

        existing_I = set(self.I)
        right_ext = {i + a for i in self.I for a in self.alphabet}
        lower_rows_set = right_ext - existing_I  # 移除了 left_ext
        sorted_lower = sorted(list(lower_rows_set), key=sort_key)

        def fmt_cell(val):
            return "1" if val else "0" if val is not None else "?"

        def fmt_str(s, width=8):
            label = 'ε' if s == '' else s
            return f"{label:^{width}}"

        with open(filename, "w", encoding="utf-8") as f:
            total_rows = len(sorted_i) + len(sorted_lower)
            n_cols = len(sorted_p) * len(sorted_s)

            f.write("=" * 120 + "\n")
            f.write(f"          OBSERVATION TABLE REPORT\n")
            f.write(f"          Rows: {total_rows} (Upper I: {len(sorted_i)} | Lower Ext: {len(sorted_lower)})\n")
            f.write(f"          Cols: {n_cols} (P: {len(sorted_p)} * S: {len(sorted_s)})\n")
            f.write("=" * 120 + "\n")

            col_width = max(8, max([len(p) + len(s) + 3 for p in sorted_p for s in sorted_s] + [5]))
            row_header_width = max(12, max([len(r) for r in sorted_i + sorted_lower] + [10])) + 2

            header = f"{'Row':<{row_header_width}} |"
            for p in sorted_p:
                for s in sorted_s:
                    col_label = f"({fmt_str(p, 1).strip()},{fmt_str(s, 1).strip()})"
                    header += f" {col_label:^{col_width}} |"

            sep_line = "-" * len(header)
            double_sep = "=" * len(header)

            f.write(header + "\n")
            f.write(double_sep + "\n")

            def write_rows(rows):
                for r in rows:
                    line = f"{fmt_str(r, row_header_width):<{row_header_width}} |"
                    for p in sorted_p:
                        for s in sorted_s:
                            val = self.table.get((r, p, s))
                            line += f" {fmt_cell(val):^{col_width}} |"
                    f.write(line + "\n")

            write_rows(sorted_i)
            f.write(sep_line + "\n")
            write_rows(sorted_lower)
            f.write(double_sep + "\n")


