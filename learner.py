# 文件名: learner.py
import os
import shutil
import time

from automata.fa.dfa import DFA


class Learner:
    """一体化 L* learner；debug_mode=True 时保存观察表和假设 DFA 快照。"""

    def __init__(
        self,
        teacher,
        alphabet,
        max_p_length=0,
        ce_strategy="breakpoint",
        debug_mode=False,
        debug_dir="debug_snapshots",
        verbose=True,
    ):
        self.teacher = teacher
        self.alphabet = sorted(list(alphabet))
        self.ce_strategy = ce_strategy
        self.debug_mode = debug_mode
        self.debug_dir = debug_dir
        self.verbose = verbose
        self.max_p_length = max_p_length

        self.query_cache = {}
        self.mq_count = 0

        self.reset_learning_state()

    def log(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    # ------------------------------------------------------------------
    # 初始化与通用工具
    # ------------------------------------------------------------------
    def reset_learning_state(self):
        """重置观测表、增量填表标记和性能统计。"""
        self.P = {""}
        self.S = {""}
        self.I = {""}
        self.table = {}
        self.state_to_rep = {}

        self.filled_rows = set()
        self.processed_P = set()
        self.processed_S = set()
        self.row_cache = {}
        self.sorted_p_cache = None
        self.sorted_s_cache = None
        self.sorted_i_cache = None
        self.right_extensions_cache = None

        self.total_start_time = 0.0
        self.total_end_time = 0.0
        self.lstar_pure_time = 0.0
        self.monoid_probe_time = 0.0
        self.eq_time = 0.0
        self.eq_count = 0
        self.language_confirmed = False
        self.skipped_eq_count = 0

    def prepare_debug_dir(self):
        """清空并重新创建 debug 快照目录。"""
        if os.path.exists(self.debug_dir):
            shutil.rmtree(self.debug_dir)

        os.makedirs(self.debug_dir)
        self.log(f"[Debug] 已创建快照目录: {self.debug_dir}")

    def sort_key(self, value):
        """字符串集合的统一排序规则：先长度，再字典序。"""
        return len(value), value

    def invalidate_context_cache(self, rows=False, i=False):
        """Clear cached orderings and row vectors after P/S/I changes."""
        if rows:
            self.row_cache.clear()
            self.sorted_p_cache = None
            self.sorted_s_cache = None
        if i:
            self.sorted_i_cache = None
            self.right_extensions_cache = None

    def sorted_p(self):
        if self.sorted_p_cache is None:
            self.sorted_p_cache = tuple(sorted(self.P))
        return self.sorted_p_cache

    def sorted_s(self):
        if self.sorted_s_cache is None:
            self.sorted_s_cache = tuple(sorted(self.S))
        return self.sorted_s_cache

    def sorted_i(self):
        if self.sorted_i_cache is None:
            self.sorted_i_cache = tuple(sorted(self.I, key=self.sort_key))
        return self.sorted_i_cache

    def right_extensions(self):
        """生成当前主区 I 的右扩展 I·Σ。"""
        if self.right_extensions_cache is None:
            self.right_extensions_cache = {i + a for i in self.I for a in self.alphabet}
        return self.right_extensions_cache

    def needed_rows(self):
        """当前观测表需要维护的所有行：主区 I 加右扩展。"""
        return self.I | self.right_extensions()

    # ------------------------------------------------------------------
    # 查询与观测表
    # ------------------------------------------------------------------
    def _ask_teacher(self, string):
        """带缓存地向 teacher 发起 membership query。"""
        if string in self.query_cache:
            return self.query_cache[string]

        value = self.teacher.membership_query(string)
        self.query_cache[string] = value
        self.mq_count += 1
        return value

    def _fill_cell(self, i, p, s):
        """填充 3D 观测表中的一个单元格 T[i, p, s]。"""
        if (i, p, s) not in self.table:
            self.table[(i, p, s)] = self._ask_teacher(p + i + s)

    def get_row(self, i):
        """读取行 i 在所有 (p, s) 语境下的布尔特征向量。"""
        cached = self.row_cache.get(i)
        if cached is not None:
            return cached

        row_values = []
        for p in self.sorted_p():
            for s in self.sorted_s():
                if (i, p, s) not in self.table:
                    self._fill_cell(i, p, s)
                row_values.append(self.table[(i, p, s)])

        row = tuple(row_values)
        self.row_cache[i] = row
        return row

    def fill_table(self):
        """增量填表：只补新行、新 P 列或新 S 列造成的缺口。"""
        all_rows = self.needed_rows()
        new_rows = all_rows - self.filled_rows
        new_P = self.P - self.processed_P
        new_S = self.S - self.processed_S

        for i in new_rows:
            self.fill_row(i)

        for p in new_P:
            self.fill_prefix_column(p, all_rows)

        for s in new_S:
            self.fill_suffix_column(s, all_rows)

        self.filled_rows.update(all_rows)
        self.processed_P = self.P.copy()
        self.processed_S = self.S.copy()

    def fill_row(self, i):
        """为新出现的行 i 补齐当前全部 P×S 单元格。"""
        for p in self.P:
            for s in self.S:
                self._fill_cell(i, p, s)

    def fill_prefix_column(self, p, rows):
        """新左语境 p 加入后，为所有当前行补齐这一组单元格。"""
        for i in rows:
            for s in self.S:
                self._fill_cell(i, p, s)

    def fill_suffix_column(self, s, rows):
        """新右语境 s 加入后，为所有当前行补齐这一组单元格。"""
        for i in rows:
            for p in self.P:
                self._fill_cell(i, p, s)

    # ------------------------------------------------------------------
    # L* 主逻辑
    # ------------------------------------------------------------------
    def is_closed_and_separable(self):
        """检查右闭合性：每个 I·Σ 行都必须能在 I 中找到等价代表元。"""
        rows_in_I = {self.get_row(i) for i in self.I}
        extensions = sorted(self.right_extensions(), key=self.sort_key)

        for ext in extensions:
            if ext in self.I:
                continue

            if self.get_row(ext) not in rows_in_I:
                self.log(f"  [闭合拦截] 发现新状态: '{ext}'，将其提拔进主区 I")
                self.I.add(ext)
                self.invalidate_context_cache(i=True)
                return False

        return True

    def build_hypothesis(self):
        """根据当前观测表的唯一行向量构造假设 DFA。"""
        row_to_state, row_to_rep = self.build_state_maps()
        states = set(row_to_state.values())
        initial_state = row_to_state[self.get_row("")]
        final_states = self.build_final_states(row_to_rep, row_to_state)
        transitions = self.build_transitions(row_to_rep, row_to_state, states)

        return DFA(
            states=states,
            input_symbols=set(self.alphabet),
            transitions=transitions,
            initial_state=initial_state,
            final_states=final_states,
        )

    def build_state_maps(self):
        """建立“行向量 -> 状态名”和“行向量 -> 代表元”的映射。"""
        row_to_state = {}
        row_to_rep = self.row_representatives()
        for row, representative in sorted(row_to_rep.items()):
            state_name = "q0" if representative == "" else representative

            row_to_state[row] = state_name
            self.state_to_rep[state_name] = representative

        return row_to_state, row_to_rep

    def representative_for_row(self, row):
        """为一个行向量选择 I 中最短、最稳定的代表字符串。"""
        candidates = self.sorted_i()
        return next(i for i in candidates if self.get_row(i) == row)

    def build_final_states(self, row_to_rep, row_to_state):
        """接受状态由代表元自身是否属于目标语言决定。"""
        final_states = set()
        for row, representative in row_to_rep.items():
            if self._ask_teacher(representative):
                final_states.add(row_to_state[row])
        return final_states

    def build_transitions(self, row_to_rep, row_to_state, states):
        """按照代表元右接一个字母后的行向量生成 DFA 转移。"""
        transitions = {state: {} for state in states}

        for row, representative in row_to_rep.items():
            current_state = row_to_state[row]
            for char in self.alphabet:
                next_row = self.get_row(representative + char)
                transitions[current_state][char] = row_to_state.get(next_row, current_state)

        return transitions

    def ensure_monoid_consistency(self):
        """内部左一致性自检：防止 DFA 合并破坏 syntactic monoid 的左语境行为。"""
        row_to_rep = self.row_representatives()
        context_cache = {}

        for u in self.sorted_i():
            for char in self.alphabet:
                boundary = u + char
                representative = row_to_rep.get(self.get_row(boundary))

                if representative is None or boundary == representative:
                    continue

                if not self.check_boundary_consistency(boundary, representative, context_cache):
                    return False

        return True

    def lookup_context_membership(self, left, middle, suffix, context_cache):
        """Read MQ(left + middle + suffix), reusing existing table cells when possible."""
        key = (left, middle, suffix)
        if key in context_cache:
            return context_cache[key]

        if left in self.P and suffix in self.S:
            cell = self.table.get((middle, left, suffix))
            if cell is not None:
                context_cache[key] = cell
                return cell

        shifted_middle = left + middle
        if suffix in self.S:
            cell = self.table.get((shifted_middle, "", suffix))
            if cell is not None:
                context_cache[key] = cell
                return cell

        value = self._ask_teacher(left + middle + suffix)
        context_cache[key] = value
        return value

    def row_representatives(self):
        """为当前 I 中每个行向量建立一个代表元。"""
        row_to_rep = {}
        for i in self.sorted_i():
            row_to_rep.setdefault(self.get_row(i), i)
        return row_to_rep

    def check_boundary_consistency(self, boundary, representative, context_cache):
        """检查一个边界串和其代表元在所有已知左/右语境中是否一致。"""
        for left in self.sorted_i():
            if left in self.P:
                continue

            for suffix in self.sorted_s():
                q_boundary = self.lookup_context_membership(left, boundary, suffix, context_cache)
                q_rep = self.lookup_context_membership(left, representative, suffix, context_cache)

                if q_boundary != q_rep:
                    self.log(
                        f"  🚨 [代数拦截] 左前缀 '{left}' 在后缀 '{suffix}' 下，"
                        f"拆散了边界 '{boundary}' 和代表元 '{representative}'"
                    )
                    self.log(f"               >> 行动: 将 '{left}' 加入 P 集合！")
                    self.P.add(left)
                    self.invalidate_context_cache(rows=True)
                    return False

        return True

    # ------------------------------------------------------------------
    # 反例处理
    # ------------------------------------------------------------------
    def handle_counterexample(self, counterexample, hypothesis):
        """根据配置处理 Oracle 返回的反例。"""
        if self.ce_strategy == "expand":
            self.expand_with_counterexample(counterexample)
            return

        self.handle_breakpoint_counterexample(counterexample, hypothesis)

    def expand_with_counterexample(self, counterexample):
        """朴素扩张策略：加入反例的全部后缀和前缀。"""
        for k in range(len(counterexample) + 1):
            self.S.add(counterexample[k:])

        prefix = ""
        for char in counterexample:
            prefix += char
            self.P.add(prefix)
        self.invalidate_context_cache(rows=True)

    def handle_breakpoint_counterexample(self, counterexample, hypothesis):
        """Rivest-Schapire 二分断点策略，只加入关键区分后缀。"""
        reps = self.trace_hypothesis_representatives(counterexample, hypothesis)
        low, high = self.find_breakpoint(counterexample, reps)

        if low is None:
            self.S.add(counterexample)
            self.P.add(counterexample)
            self.invalidate_context_cache(rows=True)
            return

        distinguishing_suffix = counterexample[high:]
        prefix_to_add = reps[low]

        self.log(
            f"  ⚔️ [反例拦截] 收反例 '{counterexample}'! "
            f"二分断点定位: '{prefix_to_add}' | '{distinguishing_suffix}'"
        )
        self.log(f"               >> 行动: 将后缀 '{distinguishing_suffix}' 加入 S")
        self.S.add(distinguishing_suffix)
        self.invalidate_context_cache(rows=True)

    def trace_hypothesis_representatives(self, word, hypothesis):
        """沿假设 DFA 读取反例，记录每一步状态对应的代表元。"""
        reps = []
        current = hypothesis.initial_state
        reps.append(self.state_to_rep[current])

        for char in word:
            current = hypothesis.transitions[current][char]
            reps.append(self.state_to_rep[current])

        return reps

    def find_breakpoint(self, word, reps):
        """在反例轨迹上二分查找 teacher 判定发生翻转的位置。"""
        low, high = 0, len(word)
        q_low = self._ask_teacher(reps[low] + word[low:])
        q_high = self._ask_teacher(reps[high] + word[high:])

        if q_low == q_high:
            return None, None

        while low + 1 < high:
            mid = (low + high) // 2
            q_mid = self._ask_teacher(reps[mid] + word[mid:])
            if q_mid == q_low:
                low = mid
            else:
                high = mid

        return low, high

    # ------------------------------------------------------------------
    # Debug 输出
    # ------------------------------------------------------------------
    def save_table_snapshot(self, step):
        """把当前观测表保存为 debug_snapshots/table_step_xxx.txt。"""
        filename = os.path.join(self.debug_dir, f"table_step_{step:03d}.txt")
        self.display_observation_table(filename)
        self.log(f"\n▶️ [Step {step:03d}] 表格已更新，快照已保存")

    def save_hypothesis_snapshot(self, hypothesis, step):
        """把当前假设 DFA 保存成 Graphviz DOT 文本。"""
        filename = os.path.join(self.debug_dir, f"hypothesis_step_{step:03d}")
        self.print_acceptor(hypothesis, filename=filename)

    def print_acceptor(self, dfa_obj, filename="hypothesis"):
        """将假设 DFA 导出为 Graphviz DOT 文本文件。"""
        filepath = f"{filename}.dot"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("digraph G {\n")
            f.write("  rankdir=LR;\n")

            if dfa_obj.final_states:
                finals = " ".join(f'"{state}"' for state in dfa_obj.final_states)
                f.write(f"  node [shape = doublecircle]; {finals};\n")

            f.write("  node [shape = circle];\n")
            f.write(f'  start [shape=point]; start -> "{dfa_obj.initial_state}";\n')

            for state, transitions in dfa_obj.transitions.items():
                for char, next_state in transitions.items():
                    f.write(f'  "{state}" -> "{next_state}" [label="{char}"];\n')

            f.write("}\n")

        self.log(f"  [DOT] Hypothesis automaton saved to: {filepath}")

    def display_observation_table(self, filename="observation_table.txt"):
        """把当前 3D 观测表导出成便于阅读的文本表格。"""
        sorted_p, sorted_s, sorted_i, sorted_lower = self.table_sections()
        col_width, row_header_width = self.table_widths(sorted_p, sorted_s, sorted_i, sorted_lower)

        with open(filename, "w", encoding="utf-8") as f:
            self.write_table_summary(f, sorted_p, sorted_s, sorted_i, sorted_lower)
            self.write_table_body(f, sorted_p, sorted_s, sorted_i, sorted_lower, col_width, row_header_width)

    def table_sections(self):
        """准备表格输出所需的 P、S、I 和 lower rows。"""
        sorted_p = sorted(self.P, key=self.sort_key)
        sorted_s = sorted(self.S, key=self.sort_key)
        sorted_i = sorted(self.I, key=self.sort_key)
        sorted_lower = sorted(self.right_extensions() - self.I, key=self.sort_key)
        return sorted_p, sorted_s, sorted_i, sorted_lower

    def table_widths(self, sorted_p, sorted_s, sorted_i, sorted_lower):
        """根据当前字符串长度动态计算输出表格宽度。"""
        col_width = max(8, max([len(p) + len(s) + 3 for p in sorted_p for s in sorted_s] + [5]))
        row_header_width = max(12, max([len(r) for r in sorted_i + sorted_lower] + [10])) + 2
        return col_width, row_header_width

    def write_table_summary(self, file_obj, sorted_p, sorted_s, sorted_i, sorted_lower):
        """写入观察表顶部的行列统计信息。"""
        total_rows = len(sorted_i) + len(sorted_lower)
        n_cols = len(sorted_p) * len(sorted_s)

        file_obj.write("=" * 120 + "\n")
        file_obj.write("          OBSERVATION TABLE REPORT\n")
        file_obj.write(f"          Rows: {total_rows} (Upper I: {len(sorted_i)} | Lower Ext: {len(sorted_lower)})\n")
        file_obj.write(f"          Cols: {n_cols} (P: {len(sorted_p)} * S: {len(sorted_s)})\n")
        file_obj.write("=" * 120 + "\n")

    def write_table_body(self, file_obj, sorted_p, sorted_s, sorted_i, sorted_lower, col_width, row_header_width):
        """写入观察表表头、主区 I 和扩展区 lower rows。"""
        header = self.table_header(sorted_p, sorted_s, col_width, row_header_width)
        sep_line = "-" * len(header)
        double_sep = "=" * len(header)

        file_obj.write(header + "\n")
        file_obj.write(double_sep + "\n")
        self.write_table_rows(file_obj, sorted_i, sorted_p, sorted_s, col_width, row_header_width)
        file_obj.write(sep_line + "\n")
        self.write_table_rows(file_obj, sorted_lower, sorted_p, sorted_s, col_width, row_header_width)
        file_obj.write(double_sep + "\n")

    def table_header(self, sorted_p, sorted_s, col_width, row_header_width):
        """生成观察表的列标题。"""
        header = f"{'Row':<{row_header_width}} |"
        for p in sorted_p:
            for s in sorted_s:
                col_label = f"({self.format_string(p, 1).strip()},{self.format_string(s, 1).strip()})"
                header += f" {col_label:^{col_width}} |"
        return header

    def write_table_rows(self, file_obj, rows, sorted_p, sorted_s, col_width, row_header_width):
        """写入一组观察表行。"""
        for row in rows:
            line = f"{self.format_string(row, row_header_width):<{row_header_width}} |"
            for p in sorted_p:
                for s in sorted_s:
                    line += f" {self.format_cell(self.table.get((row, p, s))):^{col_width}} |"
            file_obj.write(line + "\n")

    def format_cell(self, value):
        """把 membership query 的布尔值格式化为 1/0/?。"""
        return "1" if value else "0" if value is not None else "?"

    def format_string(self, value, width=8):
        """输出表格时把空串显示为 epsilon。"""
        label = "ε" if value == "" else value
        return f"{label:^{width}}"

    # ------------------------------------------------------------------
    # 主循环
    # ------------------------------------------------------------------
    def learn(self, *args, **kwargs):
        """运行学习循环，debug 模式下记录每一步快照。"""
        self.reset_learning_state()
        if self.debug_mode:
            self.prepare_debug_dir()

        self.total_start_time = time.perf_counter()

        step = 1
        if self.debug_mode:
            self.log("\n🚀 [Learner] 启动学习引擎 (快照模式)...")

        while True:
            hypothesis = self.run_table_phase(step)
            step += 1

            if hypothesis is None:
                continue

            if self.debug_mode:
                self.save_hypothesis_snapshot(hypothesis, step - 1)

            if not self.language_confirmed:
                if self.run_equivalence_phase(hypothesis):
                    continue
            else:
                self.skipped_eq_count += 1
                self.log("  [交卷] 语言等价性已确认，跳过本轮 EQ，直接进入代数自检...")

            if self.run_monoid_phase():
                self.total_end_time = time.perf_counter()
                self.log("\n🎉 [完结] 句法幺半群代数结构完美收敛！")
                return hypothesis

    def run_table_phase(self, step):
        """填表、可选保存表格快照、检查闭合性；闭合时返回假设 DFA。"""
        start = time.perf_counter()
        self.fill_table()

        if self.debug_mode:
            self.save_table_snapshot(step)

        if not self.is_closed_and_separable():
            self.lstar_pure_time += time.perf_counter() - start
            return None

        hypothesis = self.build_hypothesis()
        self.lstar_pure_time += time.perf_counter() - start
        return hypothesis

    def run_equivalence_phase(self, hypothesis):
        """向 teacher 发起 EQ；若收到反例则处理并返回 True。"""
        self.log("  [交卷] 闭合检查通过，向 Oracle 发起 EQ...")
        start = time.perf_counter()
        counterexample = self.teacher.equivalence_query(hypothesis)
        self.eq_time += time.perf_counter() - start
        self.eq_count += 1

        if counterexample is None:
            self.language_confirmed = True
            return False

        start = time.perf_counter()
        self.language_confirmed = False
        self.handle_counterexample(counterexample, hypothesis)
        self.lstar_pure_time += time.perf_counter() - start
        return True

    def run_monoid_phase(self):
        """EQ 通过后执行内部 monoid 左一致性自检。"""
        self.log("  [自检] EQ 及格！启动内部左一致性自检...")
        start = time.perf_counter()
        consistent = self.ensure_monoid_consistency()
        self.monoid_probe_time += time.perf_counter() - start
        return consistent
