import itertools, time
from automata.fa.dfa import DFA


class Learner:
    def __init__(self, teacher, alphabet, max_p_length=1):
        self.teacher = teacher
        self.alphabet = sorted(list(alphabet))
        self.query_cache = {}
        self.mq_count = 0

        # --- 增量填表需要的快照 ---
        self.filled_rows = set()  # <--- [新增] 记录所有已填过表的行 (I ∪ IΣ ∪ ΣI)
        self.processed_P = set()
        self.processed_S = set()

        self.P = set()
        # 初始化 P (建议 max_p_length 设为 0 或 1，避免指数爆炸)
        for length in range(max_p_length + 1):
            for s in itertools.product(self.alphabet, repeat=length):
                self.P.add("".join(s))

        self.S = {''}
        self.I = {''}
        self.table = {}

    def _ask_teacher(self, string):
        if string in self.query_cache:
            return self.query_cache[string]
        val = self.teacher.membership_query(string)
        self.mq_count += 1
        self.query_cache[string] = val
        return val

    def _fill_cell(self, i, p, s):
        """底层单元格填充逻辑"""
        if (i, p, s) not in self.table:
            self.table[(i, p, s)] = self._ask_teacher(p + i + s)

    def fill_table(self):
        """
        [最终修正版] 增量填表逻辑。
        支持双向扩展 (I·Σ 和 Σ·I)，并使用 filled_rows 避免重复查询。
        """
        # 1. 构造所有需要存在的行：基(I) + 右扩展 + 左扩展
        right_ext = {i + a for i in self.I for a in self.alphabet}
        left_ext = {a + i for i in self.I for a in self.alphabet}

        # all_needed_rows 是当前观测表必须包含的所有行
        all_needed_rows = self.I | right_ext | left_ext

        # 2. 计算增量
        # 新出现的行 = 当前需要的行 - 历史填过的行
        new_rows = all_needed_rows - self.filled_rows

        # 新的前缀和后缀
        new_P = self.P - self.processed_P
        new_S = self.S - self.processed_S

        # --- 情况 1: 有新行出现 (i_new, P_all, S_all) ---
        if new_rows:
            for i in new_rows:
                for p in self.P:
                    for s in self.S:
                        self._fill_cell(i, p, s)

        # --- 情况 2: 有新前缀出现 (I_all, p_new, S_all) ---
        if new_P:
            # 注意：新 P 需要对所有行生效
            for p in new_P:
                for i in all_needed_rows:
                    for s in self.S:
                        self._fill_cell(i, p, s)

        # --- 情况 3: 有新后缀出现 (I_all, P_all, s_new) ---
        if new_S:
            # 注意：新 S 需要对所有行生效
            for s in new_S:
                for i in all_needed_rows:
                    for p in self.P:
                        self._fill_cell(i, p, s)

        # 3. 更新快照 (打卡记录)
        # 将本次涉及的所有行标记为“已填”
        self.filled_rows.update(all_needed_rows)
        self.processed_P = self.P.copy()
        self.processed_S = self.S.copy()

    def get_row(self, i):
        # 这里的 get_row 依然保持一致性，但依赖于 fill_table 已填完
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

    def is_closed_and_separable(self):
        """
        [双边封闭性检查]
        不仅检查右扩展 (i + a)，也检查左扩展 (a + i)。
        """
        # 1. 获取当前 I 中所有行的特征向量
        rows_in_I = {self.get_row(i) for i in self.I}

        # 2. 生成所有候选扩展项
        # 我们优先检查短的字符串，这样生成的 I 集合更紧凑
        right_ext = {i + a for i in self.I for a in self.alphabet}
        left_ext = {a + i for i in self.I for a in self.alphabet}

        # 合并并排序 (按长度 -> 字典序)
        all_extensions = sorted(list(right_ext | left_ext), key=lambda x: (len(x), x))

        for ext in all_extensions:
            if ext in self.I:
                continue  # 已经在基里的跳过

            # 获取扩展项的行向量
            ext_row = self.get_row(ext)

            # 如果发现这个扩展项的行为在 I 里找不到原型
            if ext_row not in rows_in_I:
                # print(f"发现新代数状态: '{ext}' (提拔入 I)")
                self.I.add(ext)
                return False  # 立即跳出，触发 fill_table 补全数据

        return True

    def build_hypothesis(self):
        """
        构建假设自动机 (DFA / Monoid Acceptor)
        """
        states = set()
        row_to_state = {}

        # 1. 确定状态 (唯一的行向量)
        unique_rows = sorted(list({self.get_row(i) for i in self.I}))
        for idx, r in enumerate(unique_rows):
            state_name = f"q{idx}"
            states.add(state_name)
            row_to_state[r] = state_name

        # 2. 初始状态
        start_row = self.get_row('')
        initial_state = row_to_state[start_row]

        final_states = set()
        transitions = {s: {} for s in states}

        # 3. 构建转移
        for r in unique_rows:
            representative_i = next(i for i in self.I if self.get_row(i) == r)
            curr_state = row_to_state[r]

            # 接受状态判断：看空语境 (p='', s='')
            if self._ask_teacher(representative_i):
                final_states.add(curr_state)

            for a in self.alphabet:
                next_i = representative_i + a
                next_row = self.get_row(next_i)

                if next_row in row_to_state:
                    transitions[curr_state][a] = row_to_state[next_row]
                else:
                    # 理论上不会发生 (如果 Closed)
                    transitions[curr_state][a] = curr_state

        return DFA(
            states=states,
            input_symbols=set(self.alphabet),
            transitions=transitions,
            initial_state=initial_state,
            final_states=final_states
        )

    def display_observation_table(self, filename="observation_table.txt"):
        """
        [优化版] 将 3D 观测表导出到文件。
        改进点：
        1. 包含双向扩展 (I·Σ 和 Σ·I) 到下半部分，确保不漏掉左扩展。
        2. 使用集合运算加速行生成。
        3. 格式对齐更美观。
        """
        import os

        # --- 1. 准备数据 ---
        # 排序辅助函数：按长度 -> 字典序
        sort_key = lambda x: (len(x), x)

        sorted_p = sorted(list(self.P), key=sort_key)
        sorted_s = sorted(list(self.S), key=sort_key)

        # 上半部分 (Upper): 基 I
        sorted_i = sorted(list(self.I), key=sort_key)

        # 下半部分 (Lower): 所有的扩展 (右扩展 + 左扩展) 减去已经在 I 里的
        existing_I = set(self.I)
        right_ext = {i + a for i in self.I for a in self.alphabet}
        left_ext = {a + i for i in self.I for a in self.alphabet}

        # 核心修正：双向扩展去重后，排除掉已经是基的行
        lower_rows_set = (right_ext | left_ext) - existing_I
        sorted_lower = sorted(list(lower_rows_set), key=sort_key)

        # --- 2. 格式化工具 ---
        def fmt_cell(val):
            # 1=接受, 0=拒绝, ?=未填(Bug)
            return "1" if val else "0" if val is not None else "?"

        def fmt_str(s, width=8):
            # 空串显示为 ε
            label = 'ε' if s == '' else s
            return f"{label:^{width}}"

        # --- 3. 写入文件 ---
        with open(filename, "w", encoding="utf-8") as f:
            # 统计头信息
            total_rows = len(sorted_i) + len(sorted_lower)
            n_cols = len(sorted_p) * len(sorted_s)

            f.write("=" * 120 + "\n")
            f.write(f"          OBSERVATION TABLE REPORT\n")
            f.write(f"          Rows: {total_rows} (Upper I: {len(sorted_i)} | Lower Ext: {len(sorted_lower)})\n")
            f.write(f"          Cols: {n_cols} (P: {len(sorted_p)} * S: {len(sorted_s)})\n")
            f.write("=" * 120 + "\n")

            # 动态计算列宽 (至少 8 格，防止 (p,s) 太长显示不下)
            col_width = max(8, max([len(p) + len(s) + 3 for p in sorted_p for s in sorted_s] + [5]))
            row_header_width = max(12, max([len(r) for r in sorted_i + sorted_lower] + [10])) + 2

            # --- 表头 ---
            header = f"{'Row':<{row_header_width}} |"
            for p in sorted_p:
                for s in sorted_s:
                    col_label = f"({fmt_str(p, 1).strip()},{fmt_str(s, 1).strip()})"
                    header += f" {col_label:^{col_width}} |"

            sep_line = "-" * len(header)
            double_sep = "=" * len(header)

            f.write(header + "\n")
            f.write(double_sep + "\n")

            # --- 辅助写入函数 ---
            def write_rows(rows):
                for r in rows:
                    # 行头
                    line = f"{fmt_str(r, row_header_width):<{row_header_width}} |"
                    # 数据格
                    for p in sorted_p:
                        for s in sorted_s:
                            val = self.table.get((r, p, s))
                            line += f" {fmt_cell(val):^{col_width}} |"
                    f.write(line + "\n")

            # --- 写入 Upper Part (I) ---
            write_rows(sorted_i)

            # 分隔线
            f.write(sep_line + "\n")

            # --- 写入 Lower Part (Extensions) ---
            write_rows(sorted_lower)

            # 结束线
            f.write(double_sep + "\n")

        print(f">> [Log] 观测表已导出至: {os.path.abspath(filename)}")

    def print_performance_report(self):
        total_raw_time = self.total_end_time - self.total_start_time
        # 算法的核心纯执行时间 = L*纯逻辑 + Monoid探测
        core_algo_time = self.lstar_pure_time + self.monoid_probe_time

        print("\n" + "=" * 50)
        print("          ALGORITHM PERFORMANCE REPORT")
        print("=" * 50)
        print(f"Total Wall Clock Time    : {total_raw_time:.4f} s")
        print(f"External EQ Time (Excl.) : {self.eq_time:.4f} s ({(self.eq_time / total_raw_time) * 100:.1f}%)")
        print("-" * 50)
        print(f"PURE ALGORITHM TIME      : {core_algo_time:.10f} s")
        print(f"  - Logic & Table Filling: {self.lstar_pure_time:.4f} s")
        print(f"  - Monoid Probing       : {self.monoid_probe_time:.4f} s")
        print("-" * 50)
        print(f"Total Membership Queries : {self.mq_count}")
        print(f"Core Algorithm QPS       : {self.mq_count / core_algo_time:.1f}")
        print("=" * 50 + "\n")

    def print_final_statistics(self):
        """打印最终统计数据"""
        print("\n" + "=" * 45)
        print("OBSERVATION TABLE STATISTICS")
        print("=" * 45)
        print(f"Total REAL Queries       : {self.mq_count}")
        print(f"Total Cached Hits        : {len(self.query_cache)}")

        n_rows_upper = len(self.I)
        n_rows_lower = len({i + a for i in self.I for a in self.alphabet} - self.I)
        n_cols = len(self.P) * len(self.S)

        print("-" * 45)
        print(f"Table Rows (Upper I)     : {n_rows_upper}")
        print(f"Table Rows (Lower Ext)   : {n_rows_lower}")
        print(f"Total Rows               : {n_rows_upper + n_rows_lower}")
        print("-" * 45)
        print(f"Table Cols (P x S)       : {n_cols} (P={len(self.P)}, S={len(self.S)})")
        print("=" * 45 + "\n")

    def ensure_monoid_consistency_doublesided(self, depth=1):
        """
        [优化] 批量探测。
        一次收集所有能发现的冲突，避免反复重填表。
        """
        import itertools
        found_any_conflict = False

        all_candidates = list(self.I)
        extensions = {i + a for i in self.I for a in self.alphabet}
        all_candidates.extend(list(extensions - self.I))
        all_candidates.sort(key=lambda x: (len(x), x))

        groups = {}
        for i in all_candidates:
            r = self.get_row(i)
            if r not in groups: groups[r] = []
            groups[r].append(i)

        for r, group in groups.items():
            if len(group) < 2: continue

            base = group[0]
            for other in group[1:]:
                # 探测逻辑
                is_split = False
                for length in range(depth + 1):
                    current_probes = ["".join(s) for s in itertools.product(self.alphabet, repeat=length)]
                    for x in current_probes:
                        for y in current_probes:
                            if self._ask_teacher(x + base + y) != self._ask_teacher(x + other + y):
                                # 发现冲突，记录并标记，但不立即 return
                                if x not in self.P: self.P.add(x)
                                if y not in self.S: self.S.add(y)
                                found_any_conflict = True
                                is_split = True
                                break  # 已经分开了这对 (base, other)，跳出探测
                        if is_split: break
                    if is_split: break

        if not found_any_conflict:
            # print(f">> [Pass] Depth={depth} 双边探测结束。")
            pass
        return not found_any_conflict

    # ... [性能报告和统计函数保持不变] ...

    def learn(self, depth):
        # 初始化所有计时器
        self.total_start_time = time.perf_counter()
        self.lstar_pure_time = 0.0  # Learner 内部逻辑（填表、建假设、处理反例）
        self.monoid_probe_time = 0.0  # 双边探测计算时间
        self.eq_time = 0.0  # 外部 Oracle (Teacher) 找反例的时间

        while True:
            # --- 阶段 1: Learner 内部计算 (填表、闭合检查) ---
            lstar_start = time.perf_counter()
            self.fill_table()

            if not self.is_closed_and_separable():
                self.lstar_pure_time += (time.perf_counter() - lstar_start)
                continue

            hypothesis = self.build_hypothesis()
            self.lstar_pure_time += (time.perf_counter() - lstar_start)

            # --- 阶段 2: 外部 EQ 查询 (单独计时，不计入学生时间) ---
            eq_start = time.perf_counter()
            counterexample = self.teacher.equivalence_query(hypothesis)
            self.eq_time += (time.perf_counter() - eq_start)

            # --- 阶段 3: 处理反例 (回到 Learner 内部计算) ---
            if counterexample is not None:
                lstar_start = time.perf_counter()  # 重新开始记 Lstar 的账
                print(f"收到反例: '{counterexample}'，正在处理...")
                for i in range(len(counterexample) + 1):
                    self.S.add(counterexample[i:])
                self.lstar_pure_time += (time.perf_counter() - lstar_start)
                continue

            # --- 阶段 4: Monoid 双边探测 ---
            monoid_start = time.perf_counter()
            consistency_passed = self.ensure_monoid_consistency_doublesided(depth)
            self.monoid_probe_time += (time.perf_counter() - monoid_start)

            if not consistency_passed:
                continue

            # 结束计时
            self.total_end_time = time.perf_counter()
            self.print_performance_report()
            self.print_final_statistics()
            return hypothesis