"""Canonical printer: forms -> text.

The printer fixes all layout, so layout is never part of a program: printing a
parsed program and parsing the result returns the same forms, and every form
has exactly one printed sentence.  The conformance suite checks both laws.
"""
from .forms import Word, Form, MAYBE

PREC = {
    'With': 1, 'Instance': 2, 'Or': 3, 'And': 4, 'Not': 5,
    'Equal': 6, 'NotEqual': 6, 'Less': 6, 'Greater': 6, 'LessEqual': 6, 'GreaterEqual': 6,
    'Add': 7, 'Subtract': 7, 'Multiply': 8, 'Divide': 8, 'Mod': 8, 'Negate': 9,
}
SYM = {'Equal': '=', 'NotEqual': 'not=', 'Less': '<', 'Greater': '>', 'LessEqual': '<=',
       'GreaterEqual': '>=', 'Add': '+', 'Subtract': '-', 'Multiply': '*', 'Divide': '/',
       'Mod': 'mod', 'And': 'and', 'Or': 'or'}
CMP = {'Equal', 'NotEqual', 'Less', 'Greater', 'LessEqual', 'GreaterEqual'}
CODE_TAGS = set(PREC) | {'Literal', 'Name', 'Tuple', 'Call', 'Field', 'Index', 'Send',
                         'Request', 'Ask', 'Undo', 'Quote', 'Decide'}
IND = '    '


STEP_TAGS = {'Let', 'Was', 'AddTo', 'SubtractFrom', 'Set', 'Swap', 'Discard', 'Restore', 'Output', 'Commit',
             'If', 'RepeatWith', 'RepeatDown', 'RepeatWhile', 'Do'}


def is_code_form(v):
    return isinstance(v, Form) and v.tag in CODE_TAGS and v.tag != 'Tuple'


def code_text(v):
    """Any piece of code as source text: an expression, a step, a block, a clause or a declaration."""
    if v.tag in STEP_TAGS:
        return '\n'.join(stmt_lines(v, 0))
    if v.tag == 'Block':
        return '\n'.join(block_lines(v, 0))
    if v.tag in ('Clause', 'LossyClause'):
        return '\n'.join(clause_lines(v, 0))
    if v.tag in ('RuleDecl', 'AnswerDecl', 'TypeDecl', 'RequestDecl'):
        return '\n'.join(decl_lines(v))
    return expr_text(v)


def lit_text(v):
    if v is MAYBE:
        return 'maybe'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, Word):
        return str(v.v)
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, str):
        return '"' + v.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    raise TypeError(v)


def prec_of(e):
    if e.tag == 'Literal':
        v = e.kids[0]
        if (isinstance(v, Word) and v.v < 0) or (isinstance(v, float) and str(v).startswith('-')):
            return 9
        return 11
    return PREC.get(e.tag, 11)


def wrap(e, need):
    s = expr_text(e)
    return '(' + s + ')' if prec_of(e) < need else s


def expr_text(e):
    t, k = e.tag, e.kids
    if t == 'Literal':
        return lit_text(k[0])
    if t == 'Name':
        return k[0]
    if t == 'Tuple':
        if len(k) == 1:
            return '(' + expr_text(k[0]) + ',)'
        return '(' + ', '.join(expr_text(x) for x in k) + ')'
    if t in SYM:
        p = PREC[t]
        if t in CMP:
            return f'{wrap(k[0], p + 1)} {SYM[t]} {wrap(k[1], p + 1)}'
        return f'{wrap(k[0], p)} {SYM[t]} {wrap(k[1], p + 1)}'
    if t == 'Not':
        return 'not ' + wrap(k[0], 5)
    if t == 'Negate':
        return '-' + wrap(k[0], 9)
    if t == 'Call':
        return wrap(k[0], 10) + '(' + ', '.join(expr_text(x) for x in k[1].kids) + ')'
    if t == 'Field':
        return wrap(k[0], 10) + '.' + k[1]
    if t == 'Index':
        return wrap(k[0], 10) + '[' + expr_text(k[1]) + ']'
    if t == 'Send':
        return wrap(k[0], 10) + ' -> ' + request_text(k[1])
    if t == 'Ask':
        return 'ask ' + request_text(k[0])
    if t == 'Undo':
        return 'undo ' + wrap(k[0], 10)
    if t == 'Quote':
        return 'quote ' + wrap(k[0], 3)
    if t == 'Decide':
        return 'decide ' + wrap(k[0], 3)
    if t == 'Instance':
        return f'{wrap(k[0], 3)} from {wrap(k[1], 3)}'
    if t == 'With':
        return f'{wrap(k[0], 2)} with {wrap(k[1], 2)}'
    raise TypeError(f'not an expression form: {t}')


def request_text(r):
    op, args = r.kids
    if not args.kids:
        return op
    return op + '(' + ', '.join(expr_text(x) for x in args.kids) + ')'


def type_text(t):
    if t.tag == 'TypeName':
        return t.kids[0]
    if t.tag == 'TypeApp':
        return t.kids[0] + '(' + ', '.join(type_text(x) for x in t.kids[1:]) + ')'
    if t.tag == 'TupleType':
        return '(' + ', '.join(type_text(x) for x in t.kids) + ')'
    raise TypeError(t)


def stmt_lines(s, depth):
    pad = IND * depth
    t, k = s.tag, s.kids
    if t == 'Let':
        return [f'{pad}{expr_text(k[0])} is {expr_text(k[1])}']
    if t == 'Do':
        return [pad + expr_text(k[0])]
    if t == 'AddTo':
        return [f'{pad}add {expr_text(k[0])} to {expr_text(k[1])}']
    if t == 'SubtractFrom':
        return [f'{pad}subtract {expr_text(k[0])} from {expr_text(k[1])}']
    if t == 'Set':
        return [f'{pad}set {expr_text(k[0])} to {expr_text(k[1])}']
    if t == 'Swap':
        return [f'{pad}swap {expr_text(k[0])} and {expr_text(k[1])}']
    if t == 'Restore':
        return [f'{pad}{k[0]} was discarded']
    if t == 'Was':
        return [f'{pad}{expr_text(k[0])} was {expr_text(k[1])}']
    if t == 'Discard':
        return [f'{pad}discard {k[0]}']
    if t == 'Output':
        return [f'{pad}output {expr_text(k[0])}']
    if t == 'Commit':
        return [pad + 'commit']
    if t == 'If':
        out = [f'{pad}if {expr_text(k[0])}'] + block_lines(k[1], depth + 1)
        other = k[2]
        while other.kids:
            if len(other.kids) == 1 and other.kids[0].tag == 'If':
                inner = other.kids[0]
                out += [f'{pad}otherwise if {expr_text(inner.kids[0])}'] + block_lines(inner.kids[1], depth + 1)
                other = inner.kids[2]
            else:
                out += [pad + 'otherwise'] + block_lines(other, depth + 1)
                break
        return out
    if t == 'RepeatWith':
        return ([f'{pad}repeat with {k[0]} from {expr_text(k[1])} to {expr_text(k[2])}']
                + block_lines(k[3], depth + 1))
    if t == 'RepeatDown':
        return ([f'{pad}repeat with {k[0]} from {expr_text(k[1])} down to {expr_text(k[2])}']
                + block_lines(k[3], depth + 1))
    if t == 'RepeatWhile':
        return [f'{pad}repeat while {expr_text(k[0])}'] + block_lines(k[1], depth + 1)
    raise TypeError(f'not a statement form: {t}')


def block_lines(b, depth):
    out = []
    for s in b.kids:
        out += stmt_lines(s, depth)
    return out


def params_text(ps):
    if not ps.kids:
        return ''
    parts = []
    for p in ps.kids:
        name, ty = p.kids
        parts.append(name + (': ' + type_text(ty) if ty.kids[0:1] != ('',) else ''))
    return '(' + ', '.join(parts) + ')'


def clause_lines(c, depth):
    left, right, steps = c.kids
    head = IND * depth + f'{expr_text(left)} {"=>" if c.tag == "LossyClause" else "<->"} {expr_text(right)}'
    if steps.kids:
        return [head + ' where'] + block_lines(steps, depth + 1)
    return [head]


def fields_text(fs):
    return '(' + ', '.join(f'{f.kids[0]}: {type_text(f.kids[1])}' for f in fs.kids) + ')'


def decl_lines(d):
    t, k = d.tag, d.kids
    if t == 'RuleDecl':
        name, params, takes, returns, uses, body = k
        head = 'rule ' + name + params_text(params)
        if takes.kids[0:1] != ('',):
            head += ' takes ' + type_text(takes)
        if returns.kids[0:1] != ('',):
            head += ' returns ' + type_text(returns)
        if uses.kids:
            head += ' uses ' + ', '.join(uses.kids)
        if body.tag == 'Clauses':
            lines = []
            for c in body.kids:
                lines += clause_lines(c, 1)
        else:
            lines = block_lines(body, 1)
        return [head] + lines
    if t == 'TypeDecl':
        name, ctors, parent = k
        cs = ctors.kids
        if len(cs) == 1 and cs[0].kids[0] == name and (cs[0].kids[1].kids or parent):
            line = 'type ' + name + (fields_text(cs[0].kids[1]) if cs[0].kids[1].kids else '')
            if parent:
                line += ' <- ' + parent
            return [line]
        out = ['type ' + name]
        for c in cs:
            out.append(IND + c.kids[0] + (fields_text(c.kids[1]) if c.kids[1].kids else ''))
        return out
    if t == 'RequestDecl':
        ops = [x for x in k[1:] if x.tag == 'Op']
        out = ['request ' + k[0] + ''.join(' for ' + x.kids[0] for x in k[1:] if x.tag == 'SealedTo')]
        for op in ops:
            oname, ps, ret = op.kids
            line = IND + oname + params_text(ps)
            if ret.kids[0:1] != ('',):
                line += ' returns ' + type_text(ret)
            out.append(line)
        return out
    if t == 'AnswerDecl':
        name, params, groups, state, clauses = k
        head = f'answer {name}{params_text(params)} for {", ".join(groups.kids)}'
        if state.kids[0:1] != ('',):
            head += ' takes ' + type_text(state)
        out = [head]
        for c in clauses.kids:
            out += clause_lines(c, 1)
        return out
    raise TypeError(t)


def program_text(prog):
    chunks = ['\n'.join(decl_lines(d)) for d in prog.kids]
    return '\n\n'.join(chunks) + '\n'
