import time

from automata.fa.dfa import DFA


class ClassicLearner:
    """Classic RS-style L* learner with an I x S observation table."""

    def __init__(self, oracle, alphabet):
        self.oracle = oracle
        self.alphabet = sorted(list(alphabet))

        # Classic observation table:
        # I: candidate state representatives / row prefixes
        # S: distinguishing suffixes / experiments
        self.I = {""}
        self.S = {""}
        self.table = {}
        self.state_to_rep = {}
        self.row_cache = {}
        self.sorted_i_cache = None
        self.sorted_s_cache = None

    def sort_key(self, value):
        return len(value), value

    def invalidate_cache(self, rows=False, i=False, s=False):
        if rows:
            self.row_cache.clear()
        if i:
            self.sorted_i_cache = None
        if s:
            self.sorted_s_cache = None

    def sorted_i(self):
        if self.sorted_i_cache is None:
            self.sorted_i_cache = tuple(sorted(self.I, key=self.sort_key))
        return self.sorted_i_cache

    def sorted_s(self):
        if self.sorted_s_cache is None:
            self.sorted_s_cache = tuple(sorted(self.S, key=self.sort_key))
        return self.sorted_s_cache

    def _ask(self, i, suffix):
        """Return T[i, suffix] = MQ(i + suffix), with cell caching."""
        if (i, suffix) not in self.table:
            self.table[(i, suffix)] = self.oracle.membership_query(i + suffix)
        return self.table[(i, suffix)]

    def _get_row(self, i):
        """Return the row vector of i over all current suffixes S."""
        cached = self.row_cache.get(i)
        if cached is not None:
            return cached

        row = tuple(self._ask(i, suffix) for suffix in self.sorted_s())
        self.row_cache[i] = row
        return row

    def _is_closed(self):
        """Every row in I.Sigma must already be represented by some row in I."""
        rows_in_i = {self._get_row(i) for i in self.I}

        for i in self.sorted_i():
            for char in self.alphabet:
                extension = i + char
                if self._get_row(extension) not in rows_in_i:
                    self.I.add(extension)
                    self.invalidate_cache(i=True)
                    return False
        return True

    def _is_consistent(self):
        """Classic table consistency check, kept for reference."""
        sorted_i = self.sorted_i()

        for left_idx in range(len(sorted_i)):
            for right_idx in range(left_idx + 1, len(sorted_i)):
                first, second = sorted_i[left_idx], sorted_i[right_idx]

                if self._get_row(first) == self._get_row(second):
                    for char in self.alphabet:
                        first_ext_row = self._get_row(first + char)
                        second_ext_row = self._get_row(second + char)

                        if first_ext_row != second_ext_row:
                            for idx, suffix in enumerate(self.sorted_s()):
                                if first_ext_row[idx] != second_ext_row[idx]:
                                    self.S.add(char + suffix)
                                    self.invalidate_cache(rows=True, s=True)
                                    return False
        return True

    def _build_hypothesis(self):
        """Build the current hypothesis DFA from the I x S table."""
        states = set()
        row_to_state = {}
        self.state_to_rep = {}

        unique_rows = sorted(list({self._get_row(i) for i in self.I}))
        sorted_i = self.sorted_i()
        for idx, row in enumerate(unique_rows):
            state_name = f"q{idx}"
            states.add(state_name)
            row_to_state[row] = state_name

            representative = next(i for i in sorted_i if self._get_row(i) == row)
            self.state_to_rep[state_name] = representative

        initial_state = row_to_state[self._get_row("")]
        final_states = set()
        transitions = {state: {} for state in states}

        for i in self.I:
            current_row = self._get_row(i)
            current_state = row_to_state[current_row]

            if self._ask(i, ""):
                final_states.add(current_state)

            for char in self.alphabet:
                next_row = self._get_row(i + char)
                transitions[current_state][char] = row_to_state[next_row]

        return DFA(
            states=states,
            input_symbols=set(self.alphabet),
            transitions=transitions,
            initial_state=initial_state,
            final_states=final_states,
        )

    def learn(self):
        """Run the RS-style L* loop using binary-search counterexample handling."""
        start_time = time.perf_counter()
        self.eq_time = 0.0
        self.eq_count = 0

        while True:
            if not self._is_closed():
                continue

            hypothesis = self._build_hypothesis()
            eq_start = time.perf_counter()
            counterexample = self.oracle.equivalence_query(hypothesis)
            self.eq_time += time.perf_counter() - eq_start
            self.eq_count += 1

            if counterexample is None:
                self.learn_time = time.perf_counter() - start_time
                return hypothesis

            word = counterexample
            word_length = len(word)

            reps = []
            current = hypothesis.initial_state
            reps.append(self.state_to_rep[current])
            for char in word:
                current = hypothesis.transitions[current][char]
                reps.append(self.state_to_rep[current])

            low = 0
            high = word_length

            q_low = self.oracle.membership_query(reps[low] + word[low:])
            q_high = self.oracle.membership_query(reps[high] + word[high:])

            if q_low != q_high:
                while low + 1 < high:
                    mid = (low + high) // 2
                    q_mid = self.oracle.membership_query(reps[mid] + word[mid:])

                    if q_mid == q_low:
                        low = mid
                    else:
                        high = mid

                distinguishing_suffix = word[high:]
                self.S.add(distinguishing_suffix)
                self.invalidate_cache(rows=True, s=True)
            else:
                for length in range(1, word_length + 1):
                    self.S.add(word[-length:])
                self.invalidate_cache(rows=True, s=True)
