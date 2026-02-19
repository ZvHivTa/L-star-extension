# 文件名: regex_converter.py
from automata.fa.nfa import NFA
from automata.fa.dfa import DFA


def regex_to_minimal_dfa(regex_str, alphabet):
    """
    将正则表达式转换为最小化 DFA

    参数:
        regex_str: 正则表达式字符串 (例如: '(a|b)*aab')
        alphabet: 字母表集合 (例如: {'a', 'b'})

    返回:
        最小化的 DFA 对象
    """
    print(f"正在将正则 '{regex_str}' 转换为自动机...")

    # 1. Regex -> NFA
    # automata-lib 提供了从正则直接构建 NFA 的方法
    nfa = NFA.from_regex(regex_str, input_symbols=alphabet)

    # 2. NFA -> DFA (子集构造法)
    dfa = DFA.from_nfa(nfa)

    # 3. DFA -> Minimal DFA (最小化)
    # 这一步非常重要，因为 NFA 转过来的 DFA 通常包含冗余状态
    minimal_dfa = dfa.minify()

    print(f"转换成功！最终 DFA 状态数: {len(minimal_dfa.states)}")
    return minimal_dfa


# --- 测试代码 ---
if __name__ == "__main__":
    # 测试一下 aab
    target = regex_to_minimal_dfa('(a|b)*aab', {'a', 'b'})

    # 验证一下
    print(f"Accepts 'aab'? {target.accepts_input('aab')}")
    print(f"Accepts 'baab'? {target.accepts_input('baab')}")
    print(f"Accepts 'aabb'? {target.accepts_input('aabb')}")