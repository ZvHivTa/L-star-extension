import os
import shutil
import time

from automata.fa.dfa import DFA


class TwoSidedLearner:
    """Two-sided L*-style learner with left and right generator actions."""

    def __init__(
        self,
        teacher,
        alphabet,
        debug_mode=False,
        debug_dir="debug_snapshots_two_sided",
        verbose=True,
        max_steps=10000,
    ):
        self.teacher = teacher
        self.alphabet = sorted(list(alphabet))
        self.debug_mode = debug_mode
        self.debug_dir = debug_dir
        self.verbose = verbose
        self.max_steps = max_steps

        self.query_cache = {}
        self.mq_count = 0

        self.reset_learning_state()

    def log(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def reset_learning_state(self):
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
        self.boundary_rows_cache = None

        self.total_start_time = 0.0
        self.total_end_time = 0.0
        self.table_time = 0.0
        self.eq_time = 0.0
        self.eq_count = 0
        self.right_refinements = 0
        self.left_refinements = 0

    def prepare_debug_dir(self):
        if os.path.exists(self.debug_dir):
            shutil.rmtree(self.debug_dir)
        os.makedirs(self.debug_dir)

    def sort_key(self, value):
        return len(value), value

    def invalidate_context_cache(self, rows=False, i=False):
        if rows:
            self.row_cache.clear()
            self.sorted_p_cache = None
            self.sorted_s_cache = None
        if i:
            self.sorted_i_cache = None
            self.boundary_rows_cache = None

    def sorted_p(self):
        if self.sorted_p_cache is None:
            self.sorted_p_cache = tuple(sorted(self.P, key=self.sort_key))
        return self.sorted_p_cache

    def sorted_s(self):
        if self.sorted_s_cache is None:
            self.sorted_s_cache = tuple(sorted(self.S, key=self.sort_key))
        return self.sorted_s_cache

    def sorted_i(self):
        if self.sorted_i_cache is None:
            self.sorted_i_cache = tuple(sorted(self.I, key=self.sort_key))
        return self.sorted_i_cache

    def left_extensions(self):
        return {char + i for i in self.I for char in self.alphabet}

    def right_extensions(self):
        return {i + char for i in self.I for char in self.alphabet}

    def boundary_rows(self):
        if self.boundary_rows_cache is None:
            self.boundary_rows_cache = self.left_extensions() | self.right_extensions()
        return self.boundary_rows_cache

    def needed_rows(self):
        return self.I | self.boundary_rows()

    def _ask_teacher(self, string):
        if string in self.query_cache:
            return self.query_cache[string]
        value = self.teacher.membership_query(string)
        self.query_cache[string] = value
        self.mq_count += 1
        return value

    def _fill_cell(self, middle, left, suffix):
        key = (middle, left, suffix)
        if key not in self.table:
            self.table[key] = self._ask_teacher(left + middle + suffix)

    def get_row(self, middle):
        cached = self.row_cache.get(middle)
        if cached is not None:
            return cached

        values = []
        for left in self.sorted_p():
            for suffix in self.sorted_s():
                self._fill_cell(middle, left, suffix)
                values.append(self.table[(middle, left, suffix)])

        row = tuple(values)
        self.row_cache[middle] = row
        return row

    def fill_table(self):
        rows = self.needed_rows()
        new_rows = rows - self.filled_rows
        new_P = self.P - self.processed_P
        new_S = self.S - self.processed_S

        for row in new_rows:
            self.fill_row(row)

        for left in new_P:
            self.fill_left_column(left, rows)

        for suffix in new_S:
            self.fill_suffix_column(suffix, rows)

        self.filled_rows.update(rows)
        self.processed_P = self.P.copy()
        self.processed_S = self.S.copy()

    def fill_row(self, row):
        for left in self.P:
            for suffix in self.S:
                self._fill_cell(row, left, suffix)

    def fill_left_column(self, left, rows):
        for row in rows:
            for suffix in self.S:
                self._fill_cell(row, left, suffix)

    def fill_suffix_column(self, suffix, rows):
        for row in rows:
            for left in self.P:
                self._fill_cell(row, left, suffix)

    def row_representatives(self):
        row_to_rep = {}
        for representative in self.sorted_i():
            row_to_rep.setdefault(self.get_row(representative), representative)
        return row_to_rep

    def representative_for_row(self, row):
        row_to_rep = self.row_representatives()
        return row_to_rep.get(row)

    def ensure_two_sided_closed(self):
        row_to_rep = self.row_representatives()
        boundaries = sorted(self.boundary_rows(), key=self.sort_key)

        for boundary in boundaries:
            if boundary in self.I:
                continue
            if self.get_row(boundary) not in row_to_rep:
                self.I.add(boundary)
                self.invalidate_context_cache(i=True)
                self.log(f"  [closed] promote boundary '{boundary}' into I")
                return False
        return True

    def build_state_maps(self):
        row_to_state = {}
        row_to_rep = self.row_representatives()
        self.state_to_rep = {}

        for row, representative in sorted(row_to_rep.items()):
            state_name = "q0" if representative == "" else representative
            row_to_state[row] = state_name
            self.state_to_rep[state_name] = representative

        return row_to_state, row_to_rep

    def build_right_acceptor(self):
        row_to_state, row_to_rep = self.build_state_maps()
        states = set(row_to_state.values())
        initial_state = row_to_state[self.get_row("")]
        final_states = {
            row_to_state[row]
            for row, representative in row_to_rep.items()
            if self._ask_teacher(representative)
        }

        transitions = {state: {} for state in states}
        for row, representative in row_to_rep.items():
            state = row_to_state[row]
            for char in self.alphabet:
                next_row = self.get_row(representative + char)
                transitions[state][char] = row_to_state[next_row]

        return DFA(
            states=states,
            input_symbols=set(self.alphabet),
            transitions=transitions,
            initial_state=initial_state,
            final_states=final_states,
        )

    def right_trace_representatives(self, word, hypothesis):
        reps = []
        current = hypothesis.initial_state
        reps.append(self.state_to_rep[current])

        for char in word:
            current = hypothesis.transitions[current][char]
            reps.append(self.state_to_rep[current])
        return reps

    def left_step_state(self, representative, char):
        row_to_rep = self.row_representatives()
        return row_to_rep[self.get_row(char + representative)]

    def left_trace_suffix_representatives(self, word):
        reps = [""] * (len(word) + 1)
        current = ""
        reps[len(word)] = current

        for idx in range(len(word) - 1, -1, -1):
            current = self.left_step_state(current, word[idx])
            reps[idx] = current

        return reps

    def find_right_breakpoint(self, word, reps):
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

    def find_left_breakpoint(self, word, suffix_reps):
        low, high = 0, len(word)
        q_low = self._ask_teacher(word[:low] + suffix_reps[low])
        q_high = self._ask_teacher(word[:high] + suffix_reps[high])

        if q_low == q_high:
            return None, None

        while low + 1 < high:
            mid = (low + high) // 2
            q_mid = self._ask_teacher(word[:mid] + suffix_reps[mid])
            if q_mid == q_low:
                low = mid
            else:
                high = mid
        return low, high

    def handle_counterexample(self, counterexample, hypothesis):
        right_reps = self.right_trace_representatives(counterexample, hypothesis)
        _, right_high = self.find_right_breakpoint(counterexample, right_reps)
        if right_high is None:
            self.S.add(counterexample)
        else:
            self.S.add(counterexample[right_high:])
        self.right_refinements += 1

        left_reps = self.left_trace_suffix_representatives(counterexample)
        _, left_high = self.find_left_breakpoint(counterexample, left_reps)
        if left_high is None:
            self.P.add(counterexample)
        else:
            self.P.add(counterexample[:left_high])
        self.left_refinements += 1

        self.invalidate_context_cache(rows=True)

    def run_table_phase(self, step):
        start = time.perf_counter()
        self.fill_table()

        if self.debug_mode:
            self.save_table_snapshot(step)

        if not self.ensure_two_sided_closed():
            self.table_time += time.perf_counter() - start
            return None

        hypothesis = self.build_right_acceptor()
        self.table_time += time.perf_counter() - start
        return hypothesis

    def run_equivalence_phase(self, hypothesis):
        start = time.perf_counter()
        counterexample = self.teacher.equivalence_query(hypothesis)
        self.eq_time += time.perf_counter() - start
        self.eq_count += 1

        if counterexample is None:
            return False

        start = time.perf_counter()
        self.handle_counterexample(counterexample, hypothesis)
        self.table_time += time.perf_counter() - start
        return True

    def learn(self):
        self.reset_learning_state()
        if self.debug_mode:
            self.prepare_debug_dir()

        self.total_start_time = time.perf_counter()
        step = 1

        while step <= self.max_steps:
            hypothesis = self.run_table_phase(step)
            step += 1

            if hypothesis is None:
                continue

            if self.debug_mode:
                self.save_hypothesis_snapshot(hypothesis, step - 1)
                self.save_two_sided_snapshot(step - 1)

            if self.run_equivalence_phase(hypothesis):
                continue

            self.total_end_time = time.perf_counter()
            return hypothesis

        raise RuntimeError(f"Two-sided learner exceeded max_steps={self.max_steps}")

    def table_sections(self):
        sorted_p = sorted(self.P, key=self.sort_key)
        sorted_s = sorted(self.S, key=self.sort_key)
        sorted_i = sorted(self.I, key=self.sort_key)
        sorted_lower = sorted(self.boundary_rows() - self.I, key=self.sort_key)
        return sorted_p, sorted_s, sorted_i, sorted_lower

    def display_observation_table(self, filename="observation_table_two_sided.txt"):
        sorted_p, sorted_s, sorted_i, sorted_lower = self.table_sections()
        col_width = max(8, max([len(p) + len(s) + 3 for p in sorted_p for s in sorted_s] + [5]))
        row_header_width = max(12, max([len(r) for r in sorted_i + sorted_lower] + [10])) + 2

        with open(filename, "w", encoding="utf-8") as file_obj:
            total_rows = len(sorted_i) + len(sorted_lower)
            file_obj.write("=" * 120 + "\n")
            file_obj.write("          TWO-SIDED OBSERVATION TABLE REPORT\n")
            file_obj.write(f"          Rows: {total_rows} (Upper I: {len(sorted_i)} | Boundary: {len(sorted_lower)})\n")
            file_obj.write(f"          Cols: {len(sorted_p) * len(sorted_s)} (P: {len(sorted_p)} * S: {len(sorted_s)})\n")
            file_obj.write("=" * 120 + "\n")

            header = f"{'Row':<{row_header_width}} |"
            for left in sorted_p:
                for suffix in sorted_s:
                    label = f"({self.format_string(left, 1).strip()},{self.format_string(suffix, 1).strip()})"
                    header += f" {label:^{col_width}} |"

            sep_line = "-" * len(header)
            double_sep = "=" * len(header)
            file_obj.write(header + "\n")
            file_obj.write(double_sep + "\n")
            self.write_table_rows(file_obj, sorted_i, sorted_p, sorted_s, col_width, row_header_width)
            file_obj.write(sep_line + "\n")
            self.write_table_rows(file_obj, sorted_lower, sorted_p, sorted_s, col_width, row_header_width)
            file_obj.write(double_sep + "\n")

    def write_table_rows(self, file_obj, rows, sorted_p, sorted_s, col_width, row_header_width):
        for row in rows:
            line = f"{self.format_string(row, row_header_width):<{row_header_width}} |"
            for left in sorted_p:
                for suffix in sorted_s:
                    value = self.table.get((row, left, suffix))
                    line += f" {self.format_cell(value):^{col_width}} |"
            file_obj.write(line + "\n")

    def save_table_snapshot(self, step):
        filename = os.path.join(self.debug_dir, f"table_step_{step:03d}.txt")
        self.display_observation_table(filename)

    def save_hypothesis_snapshot(self, hypothesis, step):
        filename = os.path.join(self.debug_dir, f"right_hypothesis_step_{step:03d}")
        self.print_acceptor(hypothesis, filename)

    def save_two_sided_snapshot(self, step):
        filename = os.path.join(self.debug_dir, f"two_sided_hypothesis_step_{step:03d}")
        self.print_two_sided_model(filename)

    def print_acceptor(self, dfa_obj, filename="right_hypothesis"):
        filepath = f"{filename}.dot"
        with open(filepath, "w", encoding="utf-8") as file_obj:
            file_obj.write("digraph G {\n")
            file_obj.write("  rankdir=LR;\n")

            if dfa_obj.final_states:
                finals = " ".join(f'"{state}"' for state in dfa_obj.final_states)
                file_obj.write(f"  node [shape = doublecircle]; {finals};\n")

            file_obj.write("  node [shape = circle];\n")
            file_obj.write(f'  start [shape=point]; start -> "{dfa_obj.initial_state}";\n')
            for state, transitions in dfa_obj.transitions.items():
                for char, next_state in transitions.items():
                    file_obj.write(f'  "{state}" -> "{next_state}" [label="{char}"];\n')
            file_obj.write("}\n")

    def print_two_sided_model(self, filename="two_sided_hypothesis"):
        filepath = f"{filename}.dot"
        row_to_state, row_to_rep = self.build_state_maps()
        states = set(row_to_state.values())
        final_states = {
            row_to_state[row]
            for row, representative in row_to_rep.items()
            if self._ask_teacher(representative)
        }

        with open(filepath, "w", encoding="utf-8") as file_obj:
            file_obj.write("digraph G {\n")
            file_obj.write("  rankdir=LR;\n")

            if final_states:
                finals = " ".join(f'"{state}"' for state in final_states)
                file_obj.write(f"  node [shape = doublecircle]; {finals};\n")

            file_obj.write("  node [shape = circle];\n")
            initial_state = row_to_state[self.get_row("")]
            file_obj.write(f'  start [shape=point]; start -> "{initial_state}";\n')

            for row, representative in row_to_rep.items():
                state = row_to_state[row]
                for char in self.alphabet:
                    right_state = row_to_state[self.get_row(representative + char)]
                    left_state = row_to_state[self.get_row(char + representative)]
                    file_obj.write(
                        f'  "{state}" -> "{right_state}" [label="R:{char}", color="black"];\n'
                    )
                    file_obj.write(
                        f'  "{state}" -> "{left_state}" [label="L:{char}", color="blue"];\n'
                    )
            file_obj.write("}\n")

    def format_cell(self, value):
        return "1" if value else "0" if value is not None else "?"

    def format_string(self, value, width=8):
        label = "ε" if value == "" else value
        return f"{label:^{width}}"
