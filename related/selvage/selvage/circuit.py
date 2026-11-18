"""The reversible profile (IX.4), in part: certified clause rules lowered to X, CNOT and CCNOT.

What it lowers.  Every `Bit` of a rule's input is a wire.  Every word is layout: it is known when
the circuit is laid out, and the circuit holds for every input whose words have those values.  The
steps it lays out are updates of bits (`add x * y to z` is a CCNOT, `add x to z` a CNOT, `add 1 to z`
an X), calls of `ccnot` and of other rules it can lower (inlined), copies into fresh names (a fresh
wire and a CNOT), fresh arrays of bits (fresh wires at 0), swaps (wires relabelled), loops and
conditions on words, and uncomputes (the copy undone, and the wire given back, which must then be
0).  Index arithmetic on words is done at layout, with the interpreter's own arithmetic.

What it refuses, with a reason: a rule that is not certified; a word computed from a bit; a
condition, an index or a clause choice that reads a bit; a rule with no bit on a wire at all, which
computes on words only (word arithmetic would need adder circuits this profile does not lay out);
messages, decisions and any other step outside the list above.

A lowered circuit is checked by simulation: classical simulation is exact for X, CNOT and CCNOT,
which permute basis states.  Nothing here runs on reversible or quantum hardware.
"""
from collections import Counter

from .forms import Form, Word, Arr, Fault
from .interp import Interp


class NotLowerable(Exception):
    """The rule, or a step of it, is outside what this profile lays out."""


class Wire:
    __slots__ = ('n',)

    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return f'w{self.n}'


class Lowered:
    """A rule laid out as gates: wires, gates, where the input and output sit, and the ancillas."""

    def __init__(self, rule):
        self.rule = rule
        self.wires = 0
        self.gates = []            # ('X', t) | ('CNOT', c, t) | ('CCNOT', c1, c2, t), wire numbers
        self.ancillas = []         # wires that start at 0
        self.released = []         # (position in gates, wire): an ancilla given back, 0 there
        self.relabels = 0          # swaps, done by relabelling wires
        self.input = None          # the input with wires for bits and words as laid out
        self.output = None

    def wire(self):
        w = Wire(self.wires)
        self.wires += 1
        return w

    def ancilla(self):
        w = self.wire()
        self.ancillas.append(w.n)
        return w

    def counts(self):
        c = Counter(g[0] for g in self.gates)
        return {k: c.get(k, 0) for k in ('CCNOT', 'CNOT', 'X')}

    def input_wires(self):
        return [w.n for w in wires_of(self.input)]

    def output_wires(self):
        return [w.n for w in wires_of(self.output)]


def wires_of(v):
    """The wires of a laid-out value, in order."""
    if isinstance(v, Wire):
        return [v]
    if isinstance(v, tuple):
        return [w for x in v for w in wires_of(x)]
    if isinstance(v, Arr):
        return [w for x in v.data for w in wires_of(x)]
    if isinstance(v, Form):
        return [w for x in v.kids for w in wires_of(x)]
    return []


class Lowerer:
    def __init__(self, m):
        self.m = m
        self.it = Interp(m)
        self.c = None
        self.depth = 0

    # ---- the entry -------------------------------------------------------------------------
    def lower(self, rule, params, sample):
        if rule.kind != 'clauses':
            raise NotLowerable(f'{rule.name} is an expression rule; the profile lowers clause rules')
        if rule.cls not in ('bijection', 'partial'):
            raise NotLowerable(f'{rule.name} is {rule.cls}, not certified')
        self.c = Lowered(rule)
        self.c.input = self.lay_input(sample)
        if not wires_of(self.c.input):
            raise NotLowerable(f'{rule.name} has no bit on a wire: it computes on words, which this '
                               f'profile does not lay out as gates')
        out = self.call(rule, tuple(params), self.c.input)
        self.c.output = out
        outs = [w.n for w in wires_of(out)]
        if len(set(outs)) != len(outs):
            raise NotLowerable('an output wire appears twice')
        released = {w for _, w in self.c.released}
        left = set(range(self.c.wires)) - set(outs) - released
        if left:
            raise NotLowerable(f'wires {sorted(left)} are neither output nor given back')
        return self.c

    def lay_input(self, v):
        if isinstance(v, Word):
            return self.c.wire() if v.ty == 'Bit' else v
        if isinstance(v, tuple):
            return tuple(self.lay_input(x) for x in v)
        if isinstance(v, Arr):
            return Arr(v.ty, [self.lay_input(x) for x in v.data])
        if isinstance(v, Form):
            return Form(v.tag, tuple(self.lay_input(x) for x in v.kids))
        raise NotLowerable(f'an input of {type(v).__name__} is not laid out by this profile')

    # ---- gates -----------------------------------------------------------------------------
    def gate(self, *g):
        self.c.gates.append(g)

    def materialize(self, v):
        """A bit as a wire: a constant becomes a fresh ancilla, flipped if it is 1."""
        if isinstance(v, Wire):
            return v
        if isinstance(v, Word):
            w = self.c.ancilla()
            if v.v & 1:
                self.gate('X', w.n)
            return w
        raise NotLowerable('a value that is not a bit is used as one')

    def apply_terms(self, terms, target):
        """XOR a sum of products of at most two bits onto the target wire."""
        for term in terms:
            if any(w.n == target.n for w in term):
                raise Fault('R4: the update reads its own target')
            if len(term) == 0:
                self.gate('X', target.n)
            elif len(term) == 1:
                self.gate('CNOT', term[0].n, target.n)
            elif len(term) == 2:
                self.gate('CCNOT', term[0].n, term[1].n, target.n)
            else:
                raise NotLowerable('a product of more than two bits')

    def release(self, w):
        self.c.released.append((len(self.c.gates), w.n))

    # ---- expressions -----------------------------------------------------------------------
    def static(self, v, what):
        if isinstance(v, Wire) or (isinstance(v, (tuple, Arr, Form)) and wires_of(v)):
            raise NotLowerable(f'{what} reads a bit; the profile lays out only what words decide')
        return v

    def terms(self, e, env):
        """A bit expression as a sum of products (lists of wires); constants fold."""
        tag, k = e.tag, e.kids
        if tag in ('Add', 'Subtract'):
            return self.xor(self.terms(k[0], env), self.terms(k[1], env))
        if tag == 'Multiply':
            out = []
            for x in self.terms(k[0], env):
                for y in self.terms(k[1], env):
                    ws = sorted({w.n: w for w in x + y}.values(), key=lambda w: w.n)
                    out = self.xor(out, [ws])
            return out
        v = self.ev(e, env)
        if isinstance(v, Wire):
            return [[v]]
        if isinstance(v, Word):
            return [[]] if v.v & 1 else []
        raise NotLowerable('an update by a value that is not a bit')

    @staticmethod
    def xor(a, b):
        out = list(a)
        for t in b:
            key = sorted(w.n for w in t)
            hit = next((i for i, u in enumerate(out) if sorted(w.n for w in u) == key), None)
            if hit is None:
                out.append(t)
            else:
                del out[hit]
        return out

    def ev(self, e, env):
        tag, k = e.tag, e.kids
        if tag == 'Literal':
            return k[0]
        if tag == 'Name':
            n = k[0]
            if n in env:
                return env[n]
            if n in self.m.ctors and not self.m.ctors[n][1]:
                return Form(n, ())
            raise NotLowerable(f'unknown name {n}')
        if tag == 'Tuple':
            return tuple(self.ev(x, env) for x in k)
        if tag == 'Index':
            a = self.ev(k[0], env)
            i = self.static(self.ev(k[1], env), 'an index')
            if not isinstance(a, Arr):
                raise NotLowerable('an index into a value that is not an array')
            if not 0 <= i.v < len(a.data):
                raise Fault(f'index {i.v} is outside 0 to {len(a.data) - 1}')
            return a.data[i.v]
        if tag == 'Field':
            r = self.ev(k[0], env)
            fields = self.m.ctors[r.tag][1]
            return r.kids[[f for f, _ in fields].index(k[1])]
        if tag in ('Add', 'Subtract', 'Multiply', 'Divide', 'Mod'):
            a = self.static(self.ev(k[0], env), 'a word')
            b = self.static(self.ev(k[1], env), 'a word')
            return self.it.arith(tag, a, b)
        if tag in ('Equal', 'NotEqual', 'Less', 'Greater', 'LessEqual', 'GreaterEqual'):
            a = self.static(self.ev(k[0], env), 'a condition')
            b = self.static(self.ev(k[1], env), 'a condition')
            return self.it.compare(tag, a, b)
        if tag in ('And', 'Or', 'Not'):
            vals = [self.static(self.ev(x, env), 'a condition') for x in k]
            return (not vals[0]) if tag == 'Not' else (all(vals) if tag == 'And' else any(vals))
        if tag == 'Call':
            return self.ev_call(e, env)
        if tag == 'Undo':
            rule, params, arg = self.callee(k[0], env)
            return self.call(rule.inverse, params, arg)
        raise NotLowerable(f'{tag} is not laid out by this profile')

    def callee(self, e, env):
        head, args = e.kids[0], list(e.kids[1].kids)
        params = ()
        if head.tag == 'Call':
            params = tuple(self.static(self.ev(p, env), 'a parameter') for p in head.kids[1].kids)
            head = head.kids[0]
        name = head.kids[0]
        if name not in self.m.rules:
            raise NotLowerable(f'{name} is not a rule')
        if len(args) != 1:
            raise NotLowerable(f'{name} takes one input')
        return self.m.rules[name], params, self.take(args[0], env)

    def take(self, e, env):
        """A rule's input: evaluated, and the names it names consumed, as the call moves them."""
        v = self.ev(e, env)
        for n in moved_names(e):
            env.pop(n, None)
        return v

    def ev_call(self, e, env):
        head, args = e.kids[0], e.kids[1].kids
        if head.tag == 'Name':
            n = head.kids[0]
            if n == 'length':
                a = self.ev(args[0], env)
                return Word(len(a.data), 'I64')
            if n == 'array':
                ty, size = args[0].kids[0], self.static(self.ev(args[1], env), 'a length')
                zero = Word(0, ty) if ty != 'F64' else 0.0
                return Arr(ty, [zero] * size.v)
            if n in self.m.ctors:
                return Form(n, tuple(self.ev(x, env) for x in args))
            if n == 'Bit' and n not in self.m.rules:
                v = self.ev(args[0], env)
                return v if isinstance(v, Wire) else Word(v.v & 1, 'Bit')
            if n == 'ccnot':
                x, y, z = self.ev(args[0], env)
                for p in moved_names(args[0]):
                    env.pop(p, None)
                return self.ccnot(x, y, z)
            if n not in self.m.rules:
                v = self.ev(args[0], env) if args else None
                if len(args) == 1 and n in ('I64', 'U64', 'I32', 'U32', 'I16', 'U16', 'I8', 'U8'):
                    if wires_of(v):
                        raise NotLowerable(f'{n}(…) would compute a word from a bit; words are layout, bits are wires')
                    return self.it.convert(n, v, e.line)
                raise NotLowerable(f'{n}(…) is not laid out by this profile')
        rule, params, arg = self.callee(e, env)
        return self.call(rule, params, arg)

    def ccnot(self, x, y, z):
        """The base: z flips when x and y are both 1.  A constant control folds."""
        controls = [c for c in (x, y) if not (isinstance(c, Word) and c.v & 1)]
        if any(isinstance(c, Word) for c in controls):        # a control that is 0
            return (x, y, z)
        z = self.materialize(z)
        self.apply_terms([controls], z)
        return (x, y, z)

    # ---- rules and steps -------------------------------------------------------------------
    def call(self, rule, params, arg):
        base = self.m.rules.get('ccnot')
        if base is not None and (rule is base or rule is base.inverse):
            # the base, and its derived inverse, which is the same gate: CCNOT is its own inverse
            return self.ccnot(*arg)
        if rule.kind != 'clauses' or rule.cls not in ('bijection', 'partial'):
            raise NotLowerable(f'{rule.name} is not a certified clause rule')
        self.depth += 1
        if self.depth > 200:
            raise NotLowerable('calls nest too deep to lay out')
        try:
            for c in rule.clauses:
                env = {pn: pv for (pn, _), pv in zip(rule.params, params)}
                if self.match(c.kids[0], arg, env):
                    self.block(c.kids[2], env)
                    return self.build(c.kids[1], env)
            raise Fault(f'{rule.name}: no clause takes this input')
        finally:
            self.depth -= 1

    def match(self, p, v, env):
        tag, k = p.tag, p.kids
        if tag == 'Name':
            if k[0] in self.m.ctors:
                return isinstance(v, Form) and v.tag == k[0]
            env[k[0]] = v
            return True
        if tag == 'Literal':
            if isinstance(v, Wire):
                raise NotLowerable('a clause is chosen by a bit')
            return isinstance(v, Word) and v.v == k[0].v or v == k[0]
        if tag == 'Tuple':
            return isinstance(v, tuple) and len(v) == len(k) and all(self.match(a, b, env) for a, b in zip(k, v))
        if tag == 'Call' and k[0].tag == 'Name' and k[0].kids[0] in self.m.ctors:
            if not isinstance(v, Form) or v.tag != k[0].kids[0]:
                return False
            return all(self.match(a, b, env) for a, b in zip(k[1].kids, v.kids))
        raise NotLowerable(f'a pattern {tag} is not laid out by this profile')

    def build(self, p, env):
        tag, k = p.tag, p.kids
        if tag == 'Name':
            if k[0] in env:
                return env.pop(k[0])
            return self.ev(p, env)
        if tag == 'Literal':
            return k[0]
        if tag == 'Tuple':
            return tuple(self.build(x, env) for x in k)
        if tag == 'Call':
            return Form(k[0].kids[0], tuple(self.build(x, env) for x in k[1].kids))
        raise NotLowerable(f'a pattern {tag} is not laid out by this profile')

    def copy(self, v, live):
        """Values are owned: a bit that another live name still holds is copied onto a fresh wire."""
        if isinstance(v, Wire):
            if v.n in live:
                w = self.c.ancilla()
                self.gate('CNOT', v.n, w.n)
                return w
            return v
        if isinstance(v, tuple):
            return tuple(self.copy(x, live) for x in v)
        if isinstance(v, Arr):
            return Arr(v.ty, [self.copy(x, live) for x in v.data])
        if isinstance(v, Form):
            return Form(v.tag, tuple(self.copy(x, live) for x in v.kids))
        return v

    def block(self, b, env):
        for s in b.kids:
            self.step(s, env)

    def step(self, s, env):
        tag, k = s.tag, s.kids
        if tag == 'Let':
            pat, rhs = k
            if rhs.tag in ('Call', 'Undo') and self.is_rule_call(rhs):
                v = self.ev(rhs, env)
            else:
                v = self.ev(rhs, env)
                live = {w.n for x in env.values() for w in wires_of(x)}
                v = self.copy(v, live)
            if not self.match(pat, v, env):
                raise Fault('a value does not match the pattern it is bound to')
            return
        if tag == 'Was':
            pat, rhs = k
            if self.is_rule_call(rhs):
                # p was g(x): g's inverse takes p back to x
                inner = rhs.kids[0] if rhs.tag == 'Undo' else rhs
                rule, params, _ = self.callee_shape(inner, env)
                if rhs.tag == 'Undo':
                    rule = rule.inverse
                held = self.build(pat, env)
                back = self.call(rule.inverse, params, held)
                if not self.match(self.input_pattern(inner), back, env):
                    raise Fault('a value does not match the pattern it is given back to')
                return
            held = self.build(pat, env)
            want = self.ev(rhs, env)
            self.give_back(held, want)
            return
        if tag in ('AddTo', 'SubtractFrom'):
            e, target = k
            box, key = self.cell(target, env)
            cur = box[key]
            if isinstance(cur, Word) and cur.ty != 'Bit' and not cur.flex:
                rhs = self.static(self.ev(e, env), 'an update of a word')
                box[key] = self.it.arith('Add' if tag == 'AddTo' else 'Subtract', cur, rhs)
                return
            terms = self.terms(e, env)
            if isinstance(cur, Word) and not terms:
                return
            if isinstance(cur, Word) and all(len(t) == 0 for t in terms):
                box[key] = Word((cur.v + len(terms)) & 1, 'Bit')
                return
            w = self.materialize(cur)
            box[key] = w
            self.apply_terms(terms, w)
            return
        if tag == 'Swap':
            b1, k1 = self.cell(k[0], env)
            b2, k2 = self.cell(k[1], env)
            b1[k1], b2[k2] = b2[k2], b1[k1]
            self.c.relabels += 1
            return
        if tag == 'If':
            cond = self.static(self.ev(k[0], env), 'a condition')
            self.block(k[1] if cond else k[2], env)
            return
        if tag in ('RepeatWith', 'RepeatDown'):
            var, first, last, body = k
            a = self.static(self.ev(first, env), 'a loop bound')
            b = self.static(self.ev(last, env), 'a loop bound')
            seq = range(a.v, b.v + 1) if tag == 'RepeatWith' else range(a.v, b.v - 1, -1)
            for i in seq:
                env[var] = Word(i, a.ty if not a.flex else 'I64')
                self.block(body, env)
            env.pop(var, None)
            return
        raise NotLowerable(f'a step {tag} is not laid out by this profile')

    def is_rule_call(self, e):
        if e.tag == 'Undo':
            return True
        if e.tag != 'Call':
            return False
        head = e.kids[0]
        if head.tag == 'Call':
            head = head.kids[0]
        return head.tag == 'Name' and (head.kids[0] in self.m.rules)

    def callee_shape(self, e, env):
        head = e.kids[0]
        params = ()
        if head.tag == 'Call':
            params = tuple(self.static(self.ev(p, env), 'a parameter') for p in head.kids[1].kids)
            head = head.kids[0]
        return self.m.rules[head.kids[0]], params, None

    @staticmethod
    def input_pattern(call):
        return call.kids[1].kids[0]

    def give_back(self, held, want):
        """An uncompute: what a name holds must be what its expression gives; a wire is undone
        onto 0 and given back."""
        if isinstance(held, tuple) and isinstance(want, tuple) and len(held) == len(want):
            for h, x in zip(held, want):
                self.give_back(h, x)
            return
        if isinstance(held, Arr) and isinstance(want, Arr) and len(held.data) == len(want.data):
            for h, x in zip(held.data, want.data):
                self.give_back(h, x)
            return
        if isinstance(held, Form) and isinstance(want, Form) and held.tag == want.tag:
            for h, x in zip(held.kids, want.kids):
                self.give_back(h, x)
            return
        if isinstance(held, Wire):
            if isinstance(want, Wire):
                if want.n != held.n:
                    self.gate('CNOT', want.n, held.n)
            elif isinstance(want, Word):
                if want.v & 1:
                    self.gate('X', held.n)
            else:
                raise NotLowerable('a bit given back against a value that is not a bit')
            self.release(held)
            return
        if isinstance(want, Wire):
            raise NotLowerable('a word given back against a bit')
        if held != want and not (isinstance(held, Word) and isinstance(want, Word) and held.v == want.v):
            raise Fault(f'{held} is not what it was computed from')

    def cell(self, target, env):
        if target.tag == 'Name':
            return env, target.kids[0]
        if target.tag == 'Index':
            a = self.ev(target.kids[0], env)
            i = self.static(self.ev(target.kids[1], env), 'an index')
            if not isinstance(a, Arr):
                raise NotLowerable('an update of a value that is not an array cell')
            if not 0 <= i.v < len(a.data):
                raise Fault(f'index {i.v} is outside 0 to {len(a.data) - 1}')
            return a.data, i.v
        raise NotLowerable(f'an update of a {target.tag} is not laid out by this profile')


def moved_names(e):
    """The names a call's input moves: the names it is built of directly."""
    if e.tag == 'Name':
        return [e.kids[0]]
    if e.tag == 'Tuple':
        return [n for x in e.kids for n in moved_names(x)]
    return []


def lower(m, rule, params, sample):
    """Lay out a certified rule for the words of `sample`: a Lowered circuit, or NotLowerable."""
    return Lowerer(m).lower(rule, params, sample)


# ---- simulation: exact for X, CNOT and CCNOT, which permute basis states ----------------------
def bits_of(v, template):
    """The bits a value gives the wires of a laid-out template, as {wire: bit}."""
    out = {}
    if isinstance(template, Wire):
        out[template.n] = v.v & 1
    elif isinstance(template, tuple):
        for x, t in zip(v, template):
            out.update(bits_of(x, t))
    elif isinstance(template, Arr):
        for x, t in zip(v.data, template.data):
            out.update(bits_of(x, t))
    elif isinstance(template, Form):
        for x, t in zip(v.kids, template.kids):
            out.update(bits_of(x, t))
    return out


def fill(template, bits):
    """The value a laid-out template holds, given its wires' bits."""
    if isinstance(template, Wire):
        return Word(bits[template.n], 'Bit')
    if isinstance(template, tuple):
        return tuple(fill(x, bits) for x in template)
    if isinstance(template, Arr):
        return Arr(template.ty, [fill(x, bits) for x in template.data])
    if isinstance(template, Form):
        return Form(template.tag, tuple(fill(x, bits) for x in template.kids))
    return template


def layout_text(v):
    """A laid-out value for reading: wires as ~, words as they are."""
    from .forms import show
    if isinstance(v, Wire):
        return '~'
    if isinstance(v, tuple):
        return '(' + ', '.join(layout_text(x) for x in v) + ')'
    if isinstance(v, Arr):
        if v.data and all(isinstance(x, Wire) for x in v.data):
            return f'[{len(v.data)} wires]'
        return '[' + ', '.join(layout_text(x) for x in v.data) + ']'
    if isinstance(v, Form):
        return v.tag + ('(' + ', '.join(layout_text(x) for x in v.kids) + ')' if v.kids else '')
    return show(v)


class Dirty(Exception):
    """An ancilla given back is not 0, or a run backward ends with a wire that is not."""


def simulate(c, value):
    """Run the circuit forward on an input with the laid-out words: the output value."""
    state = [0] * c.wires
    for n, b in bits_of(value, c.input).items():
        state[n] = b
    releases = {}
    for pos, w in c.released:
        releases.setdefault(pos, []).append(w)
    for pos, g in enumerate(c.gates):
        for w in releases.get(pos, ()):
            if state[w]:
                raise Dirty(f'wire {w} is given back as 1 before gate {pos}')
        apply(state, g)
    for w in releases.get(len(c.gates), ()):
        if state[w]:
            raise Dirty(f'wire {w} is given back as 1 at the end')
    return fill(c.output, dict(enumerate(state)))


def simulate_back(c, value):
    """Run the gates in reverse from an output: the input, or Dirty where a wire that started at
    0 does not end there, which is an output the circuit does not give."""
    state = [0] * c.wires
    for n, b in bits_of(value, c.output).items():
        state[n] = b
    for g in reversed(c.gates):
        apply(state, g)
    inputs = set(c.input_wires())
    for n in range(c.wires):
        if n not in inputs and state[n]:
            raise Dirty(f'wire {n} ends as 1: not an output this circuit gives')
    return fill(c.input, dict(enumerate(state)))


def apply(state, g):
    if g[0] == 'X':
        state[g[1]] ^= 1
    elif g[0] == 'CNOT':
        state[g[2]] ^= state[g[1]]
    else:
        state[g[3]] ^= state[g[1]] & state[g[2]]
