"""Tiny S-expression reader and writer for KiCad files. Standard library only.

A parsed tree is nested Python lists; atoms are str (bare symbols), QStr (quoted strings),
int or float. QStr keeps quoted strings distinct from bare symbols when writing back.
"""


class QStr(str):
    """A string that was quoted in the file and must be quoted when written."""
    __slots__ = ()


def parse(text):
    """Parse one or more top-level S-expressions; returns a list of trees."""
    i, n = 0, len(text)
    stack = [[]]
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
        elif c == '(':
            stack.append([]); i += 1
        elif c == ')':
            node = stack.pop(); stack[-1].append(node); i += 1
        elif c == '"':
            j = i + 1; out = []
            while j < n:
                ch = text[j]
                if ch == '\\' and j + 1 < n:
                    out.append(text[j:j + 2]); j += 2; continue
                if ch == '"':
                    break
                out.append(ch); j += 1
            stack[-1].append(QStr(''.join(out))); i = j + 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()':
                j += 1
            tok = text[i:j]
            try:
                if tok.lstrip('-').isdigit():
                    stack[-1].append(int(tok))
                else:
                    stack[-1].append(float(tok))
            except ValueError:
                stack[-1].append(tok)
            i = j
    return stack[0]


def _atom(a):
    if isinstance(a, QStr):
        return '"' + a + '"'
    if isinstance(a, bool):
        return 'yes' if a else 'no'
    if isinstance(a, float):
        s = ('%.6f' % a).rstrip('0').rstrip('.')
        return s if s not in ('', '-0') else '0'
    return str(a)


def write(node, indent=0):
    """Serialise a tree in KiCad's style (one child per line for lists of lists)."""
    if not isinstance(node, list):
        return _atom(node)
    pad = '\t' * indent
    head = []
    rest = []
    for x in node:
        (rest if isinstance(x, list) else head).append(x)
    if not rest:
        return '(' + ' '.join(_atom(x) for x in node) + ')'
    # keep leading atoms on the first line, then nested lists each on their own line
    first = []
    k = 0
    for x in node:
        if isinstance(x, list):
            break
        first.append(_atom(x)); k += 1
    lines = ['(' + ' '.join(first)]
    for x in node[k:]:
        if isinstance(x, list):
            lines.append(pad + '\t' + write(x, indent + 1))
        else:
            lines.append(pad + '\t' + _atom(x))
    lines.append(pad + ')')
    return '\n'.join(lines)


def find(node, key):
    """First child list whose head is `key`."""
    for x in node:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return None


def find_all(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]
