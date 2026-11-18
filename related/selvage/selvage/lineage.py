"""Lineage: what a rule's reversibility rests on, link by link, down to ccnot.

  prototype    an answer that delegates: its own request rules, and those of the
               component of its state it delegates to, each with its own certificate
  user root    Object: it holds a Root and delegates every request to it
  system root  Root: `keep`, a bijection on the journal, and `history`
  actor        an answer instance's request rules; a message is taken back by
               running the rule's derived inverse (concurrency is not part of it)
  function     a clause rule over words and data; each step is realized below.
               An expression rule is a function (empty row) or a procedure
  logic        rules over bits built from ccnot alone
  base         ccnot: four clauses, certified by the clause test alone

Every link carries its own certificate, of one of four kinds:

  checked      the checker certified this rule using the target's certificate
  delegated    at run time the request goes to the target; its certificate holds there
  realized     a step is realized by a gate-level rule; `verify` runs both and compares
  theorem      Bennett's construction over Toffoli-universal gates (not run)

The links come from the code that runs (elaborated), not from annotations.
"""
import random

from .checker import Checker, CMP_TAGS, CONVERSIONS, WIDENINGS, settle
from .forms import Word, Arr, Form, INT_TYPES, MAYBE

ROOTS = {'Root': 'system root', 'Object': 'user root'}


def bit_only(t):
    if t == 'Bit':
        return True
    if isinstance(t, tuple) and t[0] == 'Tuple':
        return all(bit_only(x) for x in t[1])
    if isinstance(t, tuple) and t[0] == 'Array':
        return bit_only(t[1])
    return False


def rule(m, node):
    if node in m.rules:
        return m.rules[node]
    owner, op = node.split('.', 1)
    return m.answers[owner].ops[op]


def structural(x, layout):
    """Whether an expression is circuit layout: built only from literals, the rule's
    parameters, loop counters and array lengths.  One that reads the rule's data is not."""
    if not isinstance(x, Form):
        return True
    if x.tag == 'Name':
        return x.kids[0] in layout
    if x.tag == 'Call':
        f = x.kids[0]
        if f.tag == 'Name' and f.kids[0] == 'length':
            return True
        return False
    if x.tag in ('Send', 'Ask', 'Decide', 'Instance', 'With', 'Undo', 'Quote', 'Index', 'Field'):
        return False
    return all(structural(k, layout) for k in x.kids)


def operators(m, x, add, wiring=None, skip=()):
    """A link for each operator class an expression uses, so nothing a rule rests on is
    unlabelled.  Word addition is realized by ripple_add and run by `verify`; the other
    classes reduce to the gates by Bennett's construction over Toffoli's gate, and are
    cited.  (A gate-level multiply, verified like ripple_add, is not built.)"""
    if not isinstance(x, Form) or x.tag == 'Quote':
        return
    tag = x.tag
    t = settle(m.etypes.get(id(x), 'Any'))
    word = isinstance(t, str) and t in INT_TYPES and t != 'Bit'
    if id(x) in skip:
        pass   # the step that holds this operator already carries its link
    elif tag in ('Add', 'Subtract', 'Multiply', 'Divide', 'Mod', 'Negate'):
        if t == 'F64':
            add('F64 arithmetic', 'ripple_add', 'theorem')
        elif t == 'Bit':
            if tag == 'Multiply':
                add('product on Bit', 'ccnot', 'realized', ('bit-and-xor',))
            else:
                add('sum on Bit', 'cnot', 'realized', ('bit-xor',))
        elif tag in ('Add', 'Subtract', 'Negate'):
            add(f'word addition on {t}' if word else 'word addition', 'ripple_add',
                'realized' if word else 'theorem', ('add', t) if word else None)
        elif tag == 'Multiply':
            add('multiplication', 'ripple_add', 'theorem')
        else:
            add('division and remainder', 'ripple_add', 'theorem')
    elif tag in CMP_TAGS:
        add('comparison', 'ripple_add', 'theorem')
    elif tag in ('And', 'Or', 'Not'):
        if m.etypes.get(id(x)) == 'Trit':
            add('Kleene logic on Trit', 'trit_and', 'realized', ('kleene',))
        else:
            # Bool is a sub-shape of Trit (R1): on known values the Kleene circuits are Boolean logic
            add('Boolean logic', 'trit_and', 'realized', ('boolean',))
    elif tag == 'Call' and x.kids[0].tag == 'Name':
        n = x.kids[0].kids[0]
        if n in ('bitand', 'bitor', 'bitxor', 'shift_left', 'shift_right'):
            add('bitwise operations and shifts', 'ccnot', 'theorem')
        elif n in CONVERSIONS or n in WIDENINGS:
            add('conversion', 'fanout', 'theorem')
        elif n in ('sqrt', 'floor'):
            add('F64 arithmetic', 'ripple_add', 'theorem')
        elif n in m.rules and m.rules[n].kind == 'block':
            add(f'computes with {n}', n, 'checked')
    kids = x.kids
    if wiring is not None and tag == 'Index' and structural(x.kids[1], wiring):
        kids = kids[:1]     # layout: which wire, fixed when the rule is unrolled
    for kid in kids:
        operators(m, kid, add, wiring, skip)


def layer(m, node):
    if node == 'ccnot':
        return 'base'
    if node in m.answers:
        return ROOTS.get(node) or ('prototype' if m.answers[node].delegates else 'actor')
    r = rule(m, node)
    if r.is_answer:
        return ROOTS.get(r.owner, 'actor') + ' rule'
    if r.kind == 'block':
        return r.cls
    return 'logic' if bit_only(r.takes) and bit_only(r.returns) else 'function'


def links(m, node):
    """[(what, target, kind, key)] for one node; key names a realization `verify` can run."""
    out = []

    def add(what, target, kind, key=None):
        if not any(o[:2] == (what, target) for o in out):
            out.append((what, target, kind, key))
    if node in m.answers:
        a = m.answers[node]
        for op, r in a.ops.items():
            add(op, r.name, 'checked')
        for op, (_, part) in a.delegates.items():
            # the request goes to the component, whose rule runs on its own state
            add(f'{op} (to its {part})', m.op_rule(node, op).name if m.op_rule(node, op) else part, 'delegated')
        if node not in ROOTS:
            add('what it does not answer continues outward', 'Object', 'delegated')
        return out
    r = rule(m, node)

    ch = Checker(m)
    if r.kind == 'block':
        def reach(x):
            # what an expression rule reaches: the clause rules it runs and the answers it messages
            if not isinstance(x, Form) or x.tag == 'Quote':
                return
            if x.tag in ('Call', 'Undo'):
                cc = ch.clause_callee(x.kids[0] if x.tag == 'Undo' else x)
                if cc is not None:
                    add('calls' if x.tag == 'Call' else 'undoes', cc[0].name, 'checked')
            if x.tag == 'Send':
                it = m.etypes.get(id(x.kids[0]))
                o = m.op_rule(it[1], x.kids[1].kids[0]) if isinstance(it, tuple) and it[0] == 'Inst' else None
                if o is not None:
                    add('sends ' + x.kids[1].kids[0], o.name, 'checked')
            if x.tag == 'With':
                it = m.etypes.get(id(x.kids[1]))
                if isinstance(it, tuple) and it[0] == 'Inst':
                    add('installs', it[1], 'checked')
            for kid in x.kids:
                reach(kid)
        reach(r.block)
        operators(m, r.block, add)
        if r.cls == 'function':
            add('recomputed whole from its parameters', 'fanout', 'theorem')
        else:
            add('recomputed from its parameters and the replies it kept', 'Object', 'delegated')
        return out
    # In a rule over bits, index and count expressions lay out the circuit: they are fixed
    # when the rule is unrolled at a width, and are not gates.
    # The exemption is for layout alone.  An index or count that reads the rule's data is
    # an operation on that data, and carries its link like any other.
    wiring = bit_only(r.takes) and bit_only(r.returns)
    params = {pn for pn, _ in r.params}

    def word_key(kind, t):
        return (kind, t) if isinstance(t, str) and t in INT_TYPES and t != 'Bit' else None

    def step(s, types, layout):
        tag, k = s.tag, s.kids
        skip = set()
        if tag in ('Let', 'Was'):
            pat, rhs = k
            inner = rhs.kids[0] if rhs.tag == 'Undo' else rhs
            cc = ch.clause_callee(inner) if inner.tag == 'Call' else None
            if cc is not None:
                add('calls' if (tag == 'Let') == (rhs.tag != 'Undo') else 'takes back', cc[0].name, 'checked')
            elif rhs.tag == 'Send':
                it = types.get(rhs.kids[0].kids[0])
                op = rhs.kids[1].kids[0]
                o = m.op_rule(it[1], op) if isinstance(it, tuple) and it[0] == 'Inst' else None
                if o is not None:
                    add(('sends ' if tag == 'Let' else 'takes back ') + op, o.name, 'checked')
            elif rhs.tag == 'Ask':
                op = rhs.kids[0].kids[0]
                for a in m.answers.values():
                    if op in a.ops:
                        add(f'asks {op}', a.ops[op].name, 'delegated')
            elif rhs.tag == 'Decide':
                add('keeps', 'Object', 'delegated')
            elif rhs.tag == 'Instance':
                add('moves', 'exchange', 'realized', ('move',))
            elif rhs.tag == 'Name':
                t = m.etypes.get(id(rhs))
                key = word_key('copy', t) or (('bit-xor',) if t == 'Bit' else None)
                add('copies and uncopies', 'cnot' if t == 'Bit' else 'fanout', 'realized' if key else 'theorem', key)
            elif m.etypes.get(id(rhs)) == 'Bit':
                # on Bit, a product is a ccnot into an empty cell and a sum a cnot
                add('computes and uncomputes on Bit', 'ccnot', 'realized', ('bit-and-xor',))
                skip.add(id(rhs))
            else:
                add('computes and uncomputes', 'fanout', 'theorem')
        elif tag in ('AddTo', 'SubtractFrom'):
            t = m.etypes.get(id(k[1]), 'Any')
            verb = 'add' if tag == 'AddTo' else 'subtract'
            if t == 'Bit':   # on Bit, add and subtract are both xor
                if k[0].tag == 'Multiply':
                    add(f'{verb} a * b on Bit', 'ccnot', 'realized', ('bit-and-xor',))
                    skip.add(id(k[0]))
                else:
                    add(f'{verb} on Bit', 'cnot', 'realized', ('bit-xor',))
            else:
                key = word_key('add', t)
                add(f'{verb} on {t if isinstance(t, str) else "words"}', 'ripple_add',
                    'realized' if key else 'theorem', key)
        elif tag == 'Swap':
            key = word_key('swap', m.etypes.get(id(k[0])))
            add('swap', 'exchange', 'realized' if key else 'theorem', key or ('move',))
        elif tag == 'Discard':
            add('keeps', 'Object', 'delegated')
        elif tag == 'Restore':
            add('takes back what it kept', 'Object', 'delegated')
        inner = layout | {k[0]} if tag in ('RepeatWith', 'RepeatDown') else layout
        for kid in k:
            if isinstance(kid, Form) and kid.tag == 'Block':
                for x in kid.kids:
                    step(x, types, inner)
            elif wiring and tag in ('RepeatWith', 'RepeatDown') and structural(kid, layout):
                pass    # layout: how many gates, fixed when the rule is unrolled
            else:
                operators(m, kid, add, layout if wiring else None, skip)
    for c in r.clauses:
        types = r.var_types.get(id(c), {})
        for s in c.kids[2].kids:
            step(s, types, params)
    if r.journal_choice:
        add('keeps its clause choice', 'Object', 'delegated')
    if not [o for o in out if o[1] != node] and node != 'ccnot':
        # nothing but its own clauses (and calls of itself): what it does is move values
        # between the shapes of its two sides
        add('moves', 'exchange', 'realized', ('move',))
    return out


def certificate(m, node):
    return m.answers[node].cls if node in m.answers else rule(m, node).cls


# ---- verifying realizations: run the gate-level rule against the step it realizes ------
def to_bits(v, w):
    return Arr('Bit', [Word((v >> i) & 1, 'Bit') for i in range(w)])


def from_bits(a):
    return sum(b.v << i for i, b in enumerate(a.data))


def verify(m, key, samples=256, seed=1):
    """Run one realization check.  Returns (cases, mismatches, how)."""
    from .interp import Interp
    it = Interp(m)
    bad = cases = 0
    B = lambda v: Word(v, 'Bit')  # noqa: E731
    if key == ('bit-xor',):
        for a in (0, 1):
            for c in (0, 1):
                cases += 1
                out = it.forward(m.rules['cnot'], (), (B(a), B(c)))
                bad += out != (B(a), it.arith('Add', B(c), B(a)))
        return cases, bad, 'exhaustive over Bit'
    if key == ('bit-and-xor',):
        for a in (0, 1):
            for b in (0, 1):
                for c in (0, 1):
                    cases += 1
                    out = it.forward(m.rules['ccnot'], (), (B(a), B(b), B(c)))
                    bad += out != (B(a), B(b), it.arith('Add', B(c), it.arith('Multiply', B(a), B(b))))
        return cases, bad, 'exhaustive over Bit'
    if key == ('kleene',):
        enc = {True: (1, 1), False: (1, 0), MAYBE: (0, 0)}
        vals = (True, False, MAYBE)
        for x in vals:
            for y in vals:
                for name, want in (('trit_and', it.ev(Form('And', (Form('Literal', (x,)), Form('Literal', (y,)))), {})),
                                   ('trit_or', it.ev(Form('Or', (Form('Literal', (x,)), Form('Literal', (y,)))), {}))):
                    cases += 1
                    out = it.forward(m.rules[name], (), tuple(B(b) for b in enc[x] + enc[y] + (0, 0)))
                    bad += (out[4].v, out[5].v) != enc[want] or tuple(b.v for b in out[:4]) != enc[x] + enc[y]
            cases += 1
            out = it.forward(m.rules['trit_not'], (), tuple(B(b) for b in enc[x] + (0, 0)))
            bad += (out[2].v, out[3].v) != enc[it.ev(Form('Not', (Form('Literal', (x,)),)), {})]
        return cases, bad, 'exhaustive over Trit, into empty targets'
    if key == ('boolean',):
        for x in (True, False):
            for y in (True, False):
                for name, want in (('trit_and', it.ev(Form('And', (Form('Literal', (x,)), Form('Literal', (y,)))), {})),
                                   ('trit_or', it.ev(Form('Or', (Form('Literal', (x,)), Form('Literal', (y,)))), {}))):
                    cases += 1
                    out = it.forward(m.rules[name], (), (B(1), B(int(x)), B(1), B(int(y)), B(0), B(0)))
                    bad += (out[4].v, out[5].v) != (1, int(want)) or tuple(b.v for b in out[:4]) != (1, int(x), 1, int(y))
            cases += 1
            out = it.forward(m.rules['trit_not'], (), (B(1), B(int(x)), B(0), B(0)))
            bad += (out[2].v, out[3].v) != (1, int(it.ev(Form('Not', (Form('Literal', (x,)),)), {})))
        return cases, bad, 'exhaustive over Bool, as known values of Trit, into empty targets'
    rng = random.Random(seed)
    if key == ('move',):
        w = 8
        pairs, small = [(x, 0) for x in range(256)], []
        how = 'exhaustive at 8 bits into empty cells'
    else:
        kind, t = key
        w = INT_TYPES[t][0]
        mask = (1 << w) - 1
        edge = [0, 1, mask, mask >> 1, (mask >> 1) + 1]
        small = [(x, y) for x in range(16) for y in range(16)]   # every pair at 4 bits
        pairs = [(x, y) for x in edge for y in edge] + \
                [(rng.getrandbits(w), rng.getrandbits(w)) for _ in range(samples)]
        how = f'every pair at 4 bits, and {len(pairs)} pairs at {w} bits (edges and random)'
    for width, ps in ((4, small), (w, pairs)):
        for x, y in ps:
            cases += 1
            if key == ('move',) or key[0] == 'swap':
                a, b = it.forward(m.rules['exchange'], (), (to_bits(x, width), to_bits(y, width)))
                bad += (from_bits(a), from_bits(b)) != (y, x)
            elif key[0] == 'copy':
                a, z = it.forward(m.rules['fanout'], (), (to_bits(x, width), to_bits(0, width)))
                bad += (from_bits(a), from_bits(z)) != (x, x)
                back = it.undo(m.rules['fanout'], (), (a, z))
                bad += from_bits(back[1]) != 0
            else:
                a, b, c = it.forward(m.rules['ripple_add'], (), (to_bits(x, width), to_bits(y, width), B(0)))
                bad += (from_bits(a), from_bits(b), c.v) != (x, (x + y) & ((1 << width) - 1), 0)
                a2, b2, c2 = it.undo(m.rules['ripple_add'], (), (a, b, c))
                bad += from_bits(b2) != y      # the derived inverse subtracts
    return cases, bad, how


def keys_of(m, nodes):
    return sorted({k for n in nodes for (_, _, kind, k) in links(m, n) if kind == 'realized' and k},
                  key=str)


def reachable(m, start):
    order, seen, queue = [], set(), list(start)
    while queue:
        n = queue.pop(0)
        if n in seen:
            continue
        seen.add(n)
        order.append(n)
        queue += [t for _, t, _, _ in links(m, n)]
    return order


def report(m, start, check=False):
    """Every node reachable from `start`, each once, nearest first; with `check`, every
    realization link is run against the gate-level rule that realizes it."""
    order = reachable(m, start)
    width = max(len(n) for n in order) + 2
    lines = []
    for n in order:
        ls = links(m, n)
        rest = '; '.join(f'{w} -> {t} [{kind}]' for w, t, kind, _ in ls) if ls \
            else 'its four clauses [the clause test alone]'
        lines.append(f'{n:<{width}}{layer(m, n):<18}{certificate(m, n):<11}{rest}')
    if check:
        lines.append('')
        lines.append('realizations, run now:')
        names = {'bit-xor': 'add on Bit = cnot', 'bit-and-xor': 'add a * b on Bit = ccnot',
                 'move': 'move = exchange', 'add': 'add on {} = ripple_add', 'swap': 'swap on {} = exchange',
                 'copy': 'copy of {} = fanout', 'kleene': 'Kleene logic = trit_and, trit_or, trit_not',
                 'boolean': 'Boolean logic = trit_and, trit_or, trit_not'}
        for key in keys_of(m, order):
            cases, bad, how = verify(m, key)
            label = names[key[0]].format(*key[1:])
            lines.append(f'  {label:<44}{cases:>5} cases, {bad} mismatches  ({how})')
    return '\n'.join(lines)
