"""How far a certified rule reaches (V.2).

`<->` certifies that a rule is one-to-one: no two inputs share an output, and its derived inverse
is defined exactly on its image (XI.3).  That says nothing yet about whether the rule takes every
value of its input type, or gives every value of its output type.  This module settles those two
questions, each on its own, and never claims what it has not established:

  permutation       defined on every input, and onto its output type
  embedding         defined on every input; its image is only part of its output type
  partial inverse   onto its output type, but defined on only part of its input type: the
                    inverse of an embedding
  partial           neither
  one-to-one        certified, with one or both questions not established

An answer's rule for one request is a clause rule like any other: it takes the request's fields
with the state and gives the reply with the state, and its extent is settled the same ways.

How each is established is reported with it:

  by running it     the input type has few values, and the rule was run on every one
  by its steps      no step of the rule can refuse, and none of its inverse's can: an inverse
                    defined everywhere means an image that is everything (XI.3, Part 3)
  by counting       the input type has fewer values than the output type, or a value of the
                    output type matches no right side
"""
from .forms import Form, Word, Arr, Inst, Fault, MAYBE, INT_TYPES, encode
from .checker import CONVERSIONS, WIDENINGS, settle

LIMIT = 4096           # the most runs spent on one rule

SAFE_OPS = {'Add', 'Subtract', 'Multiply', 'Negate', 'And', 'Or', 'Not', 'Tuple',
            'Equal', 'NotEqual', 'Less', 'LessEqual', 'Greater', 'GreaterEqual'}
SAFE_CALLS = set(CONVERSIONS) | set(WIDENINGS) | {'length', 'bitand', 'bitor', 'bitxor', 'shift_left', 'shift_right'}


def cardinality(m, t, inside=()):
    """How many values a type has, or None where that is unbounded or not counted."""
    t = settle(t)
    if t in ('Bit', 'Bool'):
        return 2
    if t == 'Trit':
        return 3
    if t == 'Unit':
        return 1
    if t in INT_TYPES:
        return 2 ** INT_TYPES[t][0]
    if isinstance(t, tuple):
        if t[0] == 'Tuple':
            n = 1
            for x in t[1]:
                c = cardinality(m, x, inside)
                if c is None:
                    return None
                n *= c
            return n
        if t[0] == 'Data' and t[1] in m.types and t[1] != 'Code' and t[1] not in inside:
            n = 0
            for fields in m.types[t[1]].ctors.values():
                k = 1
                for _, ft in fields:
                    c = cardinality(m, ft, inside + (t[1],))
                    if c is None:
                        return None
                    k *= c
                n += k
            return n
    return None            # F64, Text, arrays, code, instances, `Any`, and types that hold themselves


def values(m, t):
    """Every value of a type with few values."""
    t = settle(t)
    if t == 'Bit':
        return [Word(0, 'Bit'), Word(1, 'Bit')]
    if t == 'Bool':
        return [True, False]
    if t == 'Trit':
        return [True, False, MAYBE]
    if t == 'Unit':
        return [()]
    if t in INT_TYPES:
        bits, signed = INT_TYPES[t]
        lo = -(2 ** (bits - 1)) if signed else 0
        return [Word(v, t) for v in range(lo, lo + 2 ** bits)]
    if t[0] == 'Tuple':
        out = [()]
        for x in t[1]:
            vs = values(m, x)
            out = [a + (v,) for a in out for v in vs]
        return out
    out = []
    for ctor, fields in m.types[t[1]].ctors.items():
        combos = [()]
        for _, ft in fields:
            vs = values(m, ft)
            combos = [a + (v,) for a in combos for v in vs]
        out += [Form(ctor, c) for c in combos]
    return out


def closed(m, t, inside=()):
    """Whether a type is spelled out to the end: no `Any` and no code in it."""
    t = settle(t)
    if t == 'Any':
        return False
    if isinstance(t, tuple):
        if t[0] == 'Tuple':
            return all(closed(m, x, inside) for x in t[1])
        if t[0] == 'Array':
            return closed(m, t[1], inside)
        if t[0] == 'Data':
            if t[1] == 'Code' or t[1] not in m.types:
                return False
            return t[1] in inside or all(closed(m, ft, inside + (t[1],))
                                         for fs in m.types[t[1]].ctors.values() for _, ft in fs)
    return True


def copy(v):
    if isinstance(v, tuple):
        return tuple(copy(x) for x in v)
    if isinstance(v, Arr):
        return Arr(v.ty, [copy(x) for x in v.data])
    return v


def sides(m, r):
    """The types a certified rule takes and gives.  An answer's rule for one request takes the
    request's fields with the state and gives the reply with the state; read backward, the
    other way round."""
    if not r.is_answer:
        return r.takes, r.returns
    pts, ret = m.requests[m.ops[r.op]][r.op]
    request = ('Tuple', tuple(pt for _, pt in pts))
    asked, replied = ('Tuple', (request, r.takes)), ('Tuple', (ret, r.takes))
    return (replied, asked) if r.backward else (asked, replied)


def as_input(r, x):
    """A value of the type `sides` gives, as the rule is run on it: an answer's rule takes its
    request as the request form the interpreter sends."""
    if r.is_answer and not r.backward:
        fields, state = x
        return Form(r.op, tuple(fields)), state
    return x


def by_running(m, r):
    """Run the rule on every input: (defined on all, size of image, inputs), or None."""
    from .interp import Interp
    takes, _ = sides(m, r)
    dom = cardinality(m, takes)
    pars = cardinality(m, ('Tuple', tuple(t for _, t in r.params)))
    if dom is None or pars is None or dom * pars > LIMIT:
        return None
    total, least = True, None
    for p in values(m, ('Tuple', tuple(t for _, t in r.params))):
        image = set()
        for x in values(m, takes):
            try:
                image.add(encode(Interp(m).run_rule(r, copy(p), as_input(r, copy(x)))))
            except Fault:
                total = False
        least = len(image) if least is None else min(least, len(image))
    return total, least, dom


def steps_never_refuse(m, r, visiting=()):
    """Whether no run of the rule can be refused, as far as its code shows.  It is cautious:
    anything it does not know to be safe counts as able to refuse."""
    if r is None or r.kind != 'clauses' or not r.left_exhaustive or r.name in visiting:
        return False
    visiting = visiting + (r.name,)

    def callee(e):
        # f(x), f(p)(x) and their `undo`: the rule that runs
        back = e.tag == 'Undo'
        if back:
            e = e.kids[0]
        if e.tag != 'Call':
            return None
        head = e.kids[0]
        args = list(e.kids[1].kids)
        if head.tag == 'Call':
            args += list(head.kids[1].kids)
            head = head.kids[0]
        if head.tag != 'Name' or head.kids[0] not in m.rules or head.kids[0] in m.ctors:
            return None
        g = m.rules[head.kids[0]]
        if g.kind != 'clauses' or g.cls == 'lossy':
            return None
        return (g.inverse if back else g), args

    def expr(e):
        if not isinstance(e, Form):
            return True
        if e.tag in ('Literal', 'Name'):
            return True
        if e.tag in SAFE_OPS:
            return all(expr(k) for k in e.kids)
        if e.tag in ('Divide', 'Mod'):
            d = e.kids[1]
            return expr(e.kids[0]) and d.tag == 'Literal' and isinstance(d.kids[0], Word) and d.kids[0].v != 0
        if e.tag == 'Call' and e.kids[0].tag == 'Name' and e.kids[0].kids[0] in SAFE_CALLS \
                and e.kids[0].kids[0] not in m.rules:
            return all(expr(k) for k in e.kids[1].kids)
        return False

    def plain(p):
        # a pattern every value of its type matches
        if p.tag == 'Name':
            return p.kids[0] not in m.ctors
        return p.tag == 'Tuple' and all(plain(k) for k in p.kids)

    def target(t):
        return t.tag == 'Name'

    def step(s):
        k = s.kids
        if s.tag in ('AddTo', 'SubtractFrom'):
            return expr(k[0]) and target(k[1])
        if s.tag == 'Swap':
            return target(k[0]) and target(k[1])
        if s.tag == 'Let':
            got = callee(k[1])
            if got is not None:
                g, args = got
                return plain(k[0]) and all(expr(a) for a in args) and steps_never_refuse(m, g, visiting)
            return plain(k[0]) and expr(k[1])
        if s.tag == 'Was':
            got = callee(k[1])
            if got is not None:
                # giving back what a call gave runs that rule the other way
                g, args = got
                return plain(k[0]) and all(expr(a) for a in args) and steps_never_refuse(m, g.inverse, visiting)
            return id(s) in m.proved
        if s.tag == 'If':
            return expr(k[0]) and block(k[1]) and block(k[2])
        if s.tag in ('RepeatWith', 'RepeatDown'):
            return expr(k[1]) and expr(k[2]) and block(k[3])
        return False

    def block(b):
        return all(step(s) for s in b.kids)
    return all(block(c.kids[2]) for c in r.clauses)


def extent(m, r):
    """(kind, how) for a certified clause rule, an answer's rule for one request among them;
    (None, None) for any other."""
    if r.kind != 'clauses' or r.cls == 'lossy' or r.inverse is None:
        return None, None
    if r.is_answer and r.op not in m.ops:
        return None, None
    got = getattr(r, '_extent', None)
    if got is not None:
        return got
    takes, returns = sides(m, r)
    dom, cod = cardinality(m, takes), cardinality(m, returns)
    ran = by_running(m, r)
    if ran is not None:
        total, image, inputs = ran
        onto = cod is not None and image == cod
        whole = 'unbounded' if cod is None else str(cod)
        how = (f'run on all {inputs} inputs: ' + ('defined on every one' if total else 'some refused') +
               f'; it gives {image} of {whole} outputs')
    else:
        fwd, bwd = steps_never_refuse(m, r), steps_never_refuse(m, r.inverse)
        # one-to-one, so: fewer inputs than outputs cannot reach every output, and fewer
        # outputs than inputs cannot take every input.  And a value no side matches is a
        # value the rule does not take, or does not give
        fewer = dom is not None and cod is not None and dom < cod
        more = dom is not None and cod is not None and cod < dom
        gap_in = not r.left_exhaustive and closed(m, takes)
        gap_out = not r.inverse.left_exhaustive and closed(m, returns)
        total = True if fwd else (False if more or gap_in else None)
        onto = True if bwd else (False if fewer or gap_out else None)
        said = []
        for known, yes, by_count, gap, counted, name in (
                (total, 'no step of it can refuse', 'fewer outputs than inputs', 'a value no left side matches', more,
                 'defined on every input'),
                (onto, 'no step of its inverse can refuse', 'fewer inputs than outputs', 'a value no right side matches',
                 fewer, 'onto')):
            if known is True:
                said.append(f'{name} ({yes})')
            elif known is False:
                said.append(f'not {name} ({by_count if counted else gap})')
            else:
                said.append(f'{name}: not established')
        how = '; '.join(said)
    kind = {(True, True): 'permutation', (True, False): 'embedding', (False, True): 'partial inverse',
            (False, False): 'partial'}.get((total, onto), 'partial' if total is False else 'one-to-one')
    r._extent = (kind, how)
    return r._extent
