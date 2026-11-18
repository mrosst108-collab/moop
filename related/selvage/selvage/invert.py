"""Inversion: code in, code out.

Inversion is defined in Selvage: the prelude's rule `mirror` (prelude.selv), a clause rule on
Code that the checker certifies and that is its own inverse.  This module holds no table of
its own.  It reads the clauses of `mirror` as data and runs them:

    invert(c)  =  block(mirror(sequence(c)))

`sequence` writes a block as Then(first, rest) ending in Done; `mirror` reads every step
backward and the sequence from its other end, After(before, last); `block` reads the result
in order.  Nothing is run and no model is needed, so the output is ordinary Selvage that
prints, parses, hashes and checks like any other rule.

`mirror` works on a rule's elaborated code.  `elaborate` (used by the checker) writes the
uncompute of every temporary as an explicit `was` step and spells `set` and rounding
updates as an exchange plus a discard, so every step has a clause in `mirror`.

What is left here is what `mirror` does not read: the header of a rule or an answer, which
is not Code.  Its name is flipped and the types it takes and returns are exchanged.
"""
import os

from .forms import Form


def F(tag, *kids, line=None):
    return Form(tag, kids, line)


class NotInvertible(Exception):
    pass


def flip_name(n):
    return n[len('undo '):] if n.startswith('undo ') else 'undo ' + n


# ---- a block as a sequence, read from either end -------------------------------------
BODIES = {'If': (1, 2), 'RepeatWith': (3,), 'RepeatDown': (3,), 'RepeatWhile': (1,),
          'Clause': (2,), 'LossyClause': (2,)}      # where a step or a clause holds a block
DONE = Form('Done', ())


OPAQUE = ('Quote', 'Literal')      # what they hold is data, and is left as it is


def as_sequence(c, line=None, whole=False):
    """Code with every block written as a sequence: Then(first, rest), ending in Done.  With
    `whole`, every part of the code is written so that a clause can take it apart: a tuple
    becomes Tupled(items), its members a list of parts."""
    if not isinstance(c, Form):
        return c
    if c.tag == 'Block':
        out = DONE
        for step in reversed(c.kids):
            out = Form('Then', (as_sequence(step, line, whole), out))
        return out
    if whole:
        if c.tag in OPAQUE:
            return c
        if c.tag == 'Tuple':
            out = Form('NoParts', ())
            for x in reversed(c.kids):
                out = Form('Part', (as_sequence(x, line, whole), out))
            return Form('Tupled', (out,), c.line)
        return Form(c.tag, tuple(as_sequence(k, line, whole) for k in c.kids), c.line)
    if c.tag in BODIES:
        return Form(c.tag, tuple(as_sequence(k) if i in BODIES[c.tag] else k for i, k in enumerate(c.kids)), c.line)
    return c


def as_block(c, line=None, whole=False):
    """The other way.  A sequence is read in order from either end: Then(first, rest) runs
    `first` and then the rest; After(before, last) runs what comes before and then `last`."""
    if not isinstance(c, Form):
        return c
    if c.tag in ('Done', 'Then', 'After'):
        first, last = [], []
        while c.tag != 'Done':
            if c.tag == 'Then':
                first.append(as_block(c.kids[0], line, whole))
                c = c.kids[1]
            elif c.tag == 'After':
                last.append(as_block(c.kids[1], line, whole))
                c = c.kids[0]
            else:
                raise NotInvertible(f'line {line}: a sequence ends in Done, found {c.tag}')
        return Form('Block', tuple(first + last[::-1]))
    if whole:
        if c.tag in OPAQUE:
            return c
        if c.tag == 'Tupled':
            members, p = [], c.kids[0]
            while isinstance(p, Form) and p.tag == 'Part':
                members.append(as_block(p.kids[0], line, whole))
                p = p.kids[1]
            if not (isinstance(p, Form) and p.tag == 'NoParts'):
                raise NotInvertible(f'line {line}: the members of a tuple end in NoParts')
            return Form('Tuple', tuple(members), c.line)
        return Form(c.tag, tuple(as_block(k, line, whole) for k in c.kids), c.line)
    if c.tag in BODIES:
        return Form(c.tag, tuple(as_block(k, line) if i in BODIES[c.tag] else k for i, k in enumerate(c.kids)), c.line)
    return c


# ---- the prelude's `mirror`, read as data and run ------------------------------------
_CLAUSES = None


def mirror_clauses():
    """The clauses of `mirror`, by the constructor each takes:
    constructor -> (its fields, the constructor it gives, that one's fields, the fields it mirrors).
    Every clause has the shape  C(fields) <-> C'(fields') where  x' is mirror(x) ..."""
    global _CLAUSES
    if _CLAUSES is None:
        from .parser import parse
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prelude.selv'), encoding='utf-8') as f:
            decl = next(d for d in parse(f.read()).kids if d.tag == 'RuleDecl' and d.kids[0] == 'mirror')

        def side(p):
            if p.tag == 'Name':
                return p.kids[0], ()
            assert p.tag == 'Call' and all(a.tag == 'Name' for a in p.kids[1].kids), p
            return p.kids[0].kids[0], tuple(a.kids[0] for a in p.kids[1].kids)
        table = {}
        for c in decl.kids[-1].kids:
            left, right, steps = c.kids
            assert c.tag == 'Clause', 'mirror is certified: every clause is `<->`'
            moves = []
            for st in steps.kids:
                pat, rhs = st.kids
                assert st.tag == 'Let' and pat.tag == 'Name' and rhs.tag == 'Call' and rhs.kids[0] == F('Name', 'mirror') \
                    and len(rhs.kids[1].kids) == 1 and rhs.kids[1].kids[0].tag == 'Name', st
                moves.append((pat.kids[0], rhs.kids[1].kids[0].kids[0]))
            (tag, fields), (tag2, fields2) = side(left), side(right)
            assert tag not in table, f'mirror has two clauses for {tag}'
            table[tag] = (fields, tag2, fields2, tuple(moves))
        _CLAUSES = table
    return _CLAUSES


def mirror(c):
    """`mirror` applied to code in its sequence reading, clause by clause as the prelude states it."""
    clause = mirror_clauses().get(c.tag) if isinstance(c, Form) else None
    if clause is None or len(clause[0]) != len(c.kids):
        what = c.tag if isinstance(c, Form) else repr(c)
        raise NotInvertible(f'line {getattr(c, "line", None)}: {what} has no backward reading; elaborate it first')
    fields, tag, fields2, moves = clause
    env = dict(zip(fields, c.kids))
    for target, source in moves:
        env[target] = mirror(env.pop(source))
    return Form(tag, tuple(env[f] for f in fields2), c.line)


def invert_clause(c):
    return as_block(mirror(as_sequence(c)))      # the arrow is kept: `=>` stays `=>`


def invert(code):
    """The inverse of a rule, an answer, a clause, a block or a step."""
    t, k = code.tag, code.kids
    if t == 'RuleDecl':
        name, params, takes, returns, uses, body = k
        if body.tag != 'Clauses':
            raise NotInvertible(f'{name} is an expression rule; it is recomputed, not inverted')
        return Form('RuleDecl', (flip_name(name), params, returns, takes, uses,
                                 Form('Clauses', tuple(invert_clause(c) for c in body.kids), body.line)),
                    code.line)
    if t == 'AnswerDecl':
        name, params, groups, state, clauses = k
        return Form('AnswerDecl', (flip_name(name), params, groups, state,
                                   Form('Clauses', tuple(invert_clause(c) for c in clauses.kids), clauses.line)),
                    code.line)
    return as_block(mirror(as_sequence(code)))


# ---- elaboration helpers ----------------------------------------------------------
def names_in(x, out=None):
    """Every identifier a piece of code mentions (for choosing fresh names)."""
    out = set() if out is None else out
    if isinstance(x, Form):
        if x.tag == 'Name':
            out.add(x.kids[0])
        elif x.tag in ('RepeatWith', 'RepeatDown', 'Discard', 'Restore'):
            out.add(x.kids[0])
        for kid in x.kids:
            names_in(kid, out)
    elif isinstance(x, tuple):
        for kid in x:
            names_in(kid, out)
    return out


def fresh(base, taken):
    n, i = base, 2
    while n in taken:
        n, i = f'{base}_{i}', i + 1
    taken.add(n)
    return n


def root_name(target):
    while target.tag in ('Index', 'Field'):
        target = target.kids[0]
    return target.kids[0] if target.tag == 'Name' else 'value'


def exchange_and_discard(target, new_value, taken, line):
    """`set t to e` and a rounding update, spelled with kernel steps:
    old is e; swap t and old; discard old."""
    old = fresh('old_' + root_name(target), taken)
    name = F('Name', old, line=line)
    return [F('Let', name, new_value, line=line),
            F('Swap', target, name, line=line),
            F('Discard', old, line=line)]
