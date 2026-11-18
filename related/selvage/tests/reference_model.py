"""The model of SPEC.md XI.3, written out as a second evaluator, and tested against the toolchain.

The soundness proof is about a model: values, patterns, the meaning F of each step, and
`invert` as a table.  This file is that model and nothing else.  It reads a rule's elaborated
code (a form) and runs it by the definitions of XI.3, sharing no code with the interpreter:
its own values, its own arithmetic, its own pattern matching, its own table for `invert`.

For generated rules the checker certifies it then checks, on random inputs, that
  - the interpreter's forward run is the model's F, refusals included;
  - the toolchain's `invert` is the model's table, form for form;
  - the interpreter's `undo` is the model's F of the inverse;
  - a `was` the checker marked proved really holds whenever it is reached (obligation O5).
A disagreement is a finding.  Run: python3 tests/reference_model.py [programs] [seed]
"""
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tests'))

from selvage import load, CheckError                 # noqa: E402
from selvage.checker import definition_of            # noqa: E402
from selvage.forms import Form, Word, Arr, Inst, Fault   # noqa: E402
from selvage.interp import Interp, deep_copy         # noqa: E402
from selvage.invert import invert                    # noqa: E402


class Refuse(Exception):
    """The model's bottom: a step that is not defined on a state."""


# ---- values: canonical trees (no value is shared) ---------------------------------------
def wrap(n):
    """An integer of Z/2^64, read in two's complement."""
    return (n + 2 ** 63) % 2 ** 64 - 2 ** 63


def of_toolchain(v):
    """A value of the interpreter as a value of the model."""
    if isinstance(v, bool):
        return v
    if isinstance(v, Word):
        return wrap(v.v)
    if isinstance(v, Arr):
        return [of_toolchain(x) for x in v.data]
    if isinstance(v, tuple):
        return tuple(of_toolchain(x) for x in v)
    if isinstance(v, Inst):
        return ('instance', v.answer, of_toolchain(v.params), of_toolchain(v.state))
    if isinstance(v, Form):
        return ('form', v.tag, tuple(of_toolchain(x) for x in v.kids))
    raise TypeError(repr(v))


def copy(v):
    if isinstance(v, list):
        return [copy(x) for x in v]
    if isinstance(v, tuple):
        return tuple(copy(x) for x in v)
    return v


class Model:
    def __init__(self, m):
        self.m = m
        self.proved_reached = 0

    # ---- code --------------------------------------------------------------------------
    def rule_code(self, name):
        return definition_of(self.m, self.m.rules[name])

    def is_ctor(self, name):
        return name in self.m.ctors

    def clause_call(self, e):
        """g(k)(x) or g(x), for a clause rule g: (name, parameter expressions, input expression)."""
        if e.tag != 'Call':
            return None
        f, args = e.kids
        rules = self.m.rules
        if f.tag == 'Call' and f.kids[0].tag == 'Name' and rules.get(f.kids[0].kids[0]) is not None \
                and rules[f.kids[0].kids[0]].kind == 'clauses':
            return f.kids[0].kids[0], list(f.kids[1].kids), args.kids[0]
        if f.tag == 'Name' and f.kids[0] in rules and rules[f.kids[0]].kind == 'clauses' and not rules[f.kids[0]].params:
            return f.kids[0], [], args.kids[0]
        return None

    # ---- expressions: a value that depends only on the names read ----------------------
    def value(self, e, env):
        t, k = e.tag, e.kids
        if t == 'Literal':
            lit = k[0]
            return lit if isinstance(lit, bool) else wrap(lit.v)
        if t == 'Name':
            if self.is_ctor(k[0]):
                return ('form', k[0], ())
            if k[0] not in env:
                raise Refuse(f'{k[0]} is not live')
            return env[k[0]]
        if t in ('Add', 'Subtract', 'Multiply'):
            a, b = self.value(k[0], env), self.value(k[1], env)
            return wrap(a + b if t == 'Add' else a - b if t == 'Subtract' else a * b)
        if t == 'Negate':
            return wrap(-self.value(k[0], env))
        if t in ('Equal', 'NotEqual', 'Less', 'Greater', 'LessEqual', 'GreaterEqual'):
            a, b = self.value(k[0], env), self.value(k[1], env)
            return {'Equal': a == b, 'NotEqual': a != b, 'Less': a < b, 'Greater': a > b,
                    'LessEqual': a <= b, 'GreaterEqual': a >= b}[t]
        if t == 'Tuple':
            return tuple(self.value(x, env) for x in k)
        if t == 'Index':
            arr, i = self.value(k[0], env), self.value(k[1], env)
            if not 0 <= i < len(arr):
                raise Refuse('index out of range')
            return arr[i]
        if t == 'Call' and k[0].tag == 'Name' and k[0].kids[0] == 'length':
            return len(self.value(k[1].kids[0], env))
        if t == 'Call' and k[0].tag == 'Name' and self.is_ctor(k[0].kids[0]):
            return ('form', k[0].kids[0], tuple(self.value(x, env) for x in k[1].kids))
        raise NotImplementedError(f'expression {t}')

    # ---- patterns: linear, and (M) match and build undo each other ---------------------
    def match(self, p, v):
        """The bindings under which p reads v, or Refuse."""
        t, k = p.tag, p.kids
        if t == 'Name':
            if self.is_ctor(k[0]):
                if v != ('form', k[0], ()):
                    raise Refuse('shape')
                return {}
            return {k[0]: v}
        if t == 'Literal':
            lit = k[0] if isinstance(k[0], bool) else wrap(k[0].v)
            if type(lit) is not type(v) or lit != v:
                raise Refuse('literal')
            return {}
        if t == 'Tuple':
            if not isinstance(v, tuple) or len(v) != len(k) or (v and v[0] in ('form', 'instance')):
                raise Refuse('shape')
            out = {}
            for q, x in zip(k, v):
                out.update(self.match(q, x))
            return out
        if t == 'Call':
            c, args = k[0].kids[0], k[1].kids
            if not (isinstance(v, tuple) and v[:2] == ('form', c) and len(v[2]) == len(args)):
                raise Refuse('shape')
            out = {}
            for q, x in zip(args, v[2]):
                out.update(self.match(q, x))
            return out
        raise NotImplementedError(f'pattern {t}')

    def build(self, p, env):
        """The value p reads; its names are consumed."""
        t, k = p.tag, p.kids
        if t == 'Name':
            if self.is_ctor(k[0]):
                return ('form', k[0], ())
            if k[0] not in env:
                raise Refuse(f'{k[0]} is not live')
            return env.pop(k[0])
        if t == 'Literal':
            return k[0] if isinstance(k[0], bool) else wrap(k[0].v)
        if t == 'Tuple':
            return tuple(self.build(q, env) for q in k)
        if t == 'Call':
            return ('form', k[0].kids[0], tuple(self.build(q, env) for q in k[1].kids))
        raise NotImplementedError(f'pattern {t}')

    def bind(self, p, v, env):
        new = self.match(p, v)
        if set(new) & set(env):
            raise Refuse('a name bound twice')
        env.update(new)

    # ---- targets: a name or an element -------------------------------------------------
    def cell(self, t, env):
        if t.tag == 'Name':
            return env, t.kids[0]
        if t.tag == 'Index':
            arr, i = self.value(t.kids[0], env), self.value(t.kids[1], env)
            if not 0 <= i < len(arr):
                raise Refuse('index out of range')
            return arr, i
        raise NotImplementedError(f'target {t.tag}')

    def reads_cell(self, e, root, index, env):
        """Whether e reads the element `index` of the array named `root` (O3, settled when the step runs)."""
        if not isinstance(e, Form):
            return False
        if e.tag == 'Index' and e.kids[0].tag == 'Name' and e.kids[0].kids[0] == root:
            if self.value(e.kids[1], env) == index:
                return True
        return any(self.reads_cell(x, root, index, env) for x in e.kids)

    # ---- F: the meaning of a step ------------------------------------------------------
    def step(self, s, env):
        t, k = s.tag, s.kids
        if t in ('Let', 'Was'):
            return self.is_or_was(s, env, t == 'Was')
        if t in ('AddTo', 'SubtractFrom'):
            e, target = k
            if target.tag == 'Index' and target.kids[0].tag == 'Name':
                root, index = target.kids[0].kids[0], self.value(target.kids[1], env)
                if self.reads_cell(e, root, index, env):
                    raise Refuse('the update reads its own target')
            amount = self.value(e, env)
            box, key = self.cell(target, env)
            box[key] = wrap(box[key] + amount if t == 'AddTo' else box[key] - amount)
            return
        if t == 'Swap':
            (b1, k1), (b2, k2) = self.cell(k[0], env), self.cell(k[1], env)
            b1[k1], b2[k2] = b2[k2], b1[k1]
            return
        if t == 'If':
            c = self.value(k[0], env)
            return self.block(k[1] if c else k[2], env)
        if t in ('RepeatWith', 'RepeatDown'):
            var, first, last, body = k
            a, b = self.value(first, env), self.value(last, env)
            for i in (range(a, b + 1) if t == 'RepeatWith' else range(a, b - 1, -1)):
                env[var] = i
                self.block(body, env)
                del env[var]
            return
        raise NotImplementedError(f'step {t}')

    def is_or_was(self, s, env, back):
        pat, rhs = s.kids
        inner = rhs.kids[0] if rhs.tag == 'Undo' else rhs
        call = self.clause_call(inner)
        if call is not None:
            # p is g(k)(x): x is consumed, g runs, p is bound.  p was g(k)(x): the other way,
            # through invert(g).  `undo g` exchanges g and its inverse.
            name, ks, inp = call
            params = [self.value(x, env) for x in ks]
            src, dst = (pat, inp) if back else (inp, pat)
            code = self.rule_code(name)
            if back != (rhs.tag == 'Undo'):
                code = model_invert(code)
            return self.bind(dst, self.rule(code, params, self.build(src, env)), env)
        if rhs.tag == 'Send':
            t = rhs.kids[0].kids[0]
            op, args = rhs.kids[1].kids[0], rhs.kids[1].kids[1].kids
            argv = tuple(self.value(a, env) for a in args)
            _, answer, params, state = env[t]
            code = self.answer_code(answer, op)
            if not back:
                reply, new = self.rule(code, list(params), (('form', op, argv), state))
                env[t] = ('instance', answer, params, new)
                return self.bind(pat, reply, env)
            request, old = self.rule(model_invert(code), list(params), (self.build(pat, env), state))
            if request != ('form', op, argv):
                raise Refuse('the message does not match on the way back')
            env[t] = ('instance', answer, params, old)
            return
        if rhs.tag == 'Instance':
            ae = rhs.kids[0]
            answer = ae.kids[0] if ae.tag == 'Name' else ae.kids[0].kids[0]
            params = () if ae.tag == 'Name' else tuple(self.value(a, env) for a in ae.kids[1].kids)
            if not back:
                return self.bind(pat, ('instance', answer, params, self.build(rhs.kids[1], env)), env)
            inst = self.build(pat, env)
            if not (isinstance(inst, tuple) and inst[:3] == ('instance', answer, params)):
                raise Refuse('not an instance this step packs')
            return self.bind(rhs.kids[1], inst[3], env)
        e = rhs.kids[0] if rhs.tag == 'Decide' else rhs       # a decision about a Bool is its value
        if not back:
            return self.bind(pat, copy(self.value(e, env)), env)
        held = self.build(pat, env)
        if id(s) in self.m.proved:
            self.proved_reached += 1      # the toolchain omits this comparison; the model makes it
        if held != self.value(e, env):
            raise Refuse('proved' if id(s) in self.m.proved else 'not what it was computed from')

    def block(self, b, env):
        before = set(env)
        for s in b.kids:
            self.step(s, env)
        if set(env) != before:
            raise Refuse('a block must leave the names it found')      # O2

    def steps(self, b, env):
        for s in b.kids:
            self.step(s, env)

    # ---- clauses and rules ---------------------------------------------------------------
    def rule(self, code, params, x):
        names = [p.kids[0] for p in code.kids[1].kids]
        for clause in code.kids[-1].kids:
            left, right, steps = clause.kids
            try:
                env = self.match(left, x)
            except Refuse:
                continue
            given = dict(zip(names, params))
            scope = {**given, **env}
            self.steps(steps, scope)
            out = self.build(right, scope)
            if set(scope) != set(given):
                raise Refuse('a name is neither returned nor consumed')    # O2
            return out
        raise Refuse('no clause matches')

    def answer_code(self, answer, op):
        """The rule that answers op: the answer's clauses for it, as a rule over (request, state)."""
        a = self.m.answers[answer]
        if op not in a.ops:      # delegation is not used by the generators that reach here
            raise NotImplementedError('delegation')
        return Form('RuleDecl', (f'{answer}.{op}', a.decl.kids[1], None, None, None,
                                 Form('Clauses', tuple(a.ops[op].clauses))))


# ---- invert: the table of V.6 ----------------------------------------------------------------
BACKWARD = {'Let': 'Was', 'Was': 'Let', 'AddTo': 'SubtractFrom', 'SubtractFrom': 'AddTo', 'Swap': 'Swap',
            'RepeatWith': 'RepeatDown', 'RepeatDown': 'RepeatWith'}


def model_invert(x):
    """Reverse each block and replace each step by its backward reading."""
    t, k = x.tag, x.kids
    if t == 'RuleDecl':
        return Form('RuleDecl', k[:-1] + (model_invert(k[-1]),))
    if t == 'Clauses':
        return Form('Clauses', tuple(model_invert(c) for c in k))
    if t in ('Clause', 'LossyClause'):
        return Form(t, (k[1], k[0], model_invert(k[2])))
    if t == 'Block':
        return Form('Block', tuple(model_invert(s) for s in reversed(k)))
    if t == 'If':
        return Form('If', (k[0], model_invert(k[1]), model_invert(k[2])))
    if t in ('RepeatWith', 'RepeatDown'):
        return Form(BACKWARD[t], (k[0], k[2], k[1], model_invert(k[3])))
    if t in BACKWARD:
        return Form(BACKWARD[t], k)
    if t in ('Discard', 'Restore'):               # a loss, and taking it back
        return Form('Restore' if t == 'Discard' else 'Discard', k)
    raise NotImplementedError(f'invert {t}')


def same_code(a, b):
    """Two forms, compared without their line numbers."""
    if isinstance(a, Form) and isinstance(b, Form):
        return a.tag == b.tag and len(a.kids) == len(b.kids) and all(same_code(x, y) for x, y in zip(a.kids, b.kids))
    return a == b and type(a) is type(b)


# ---- the comparison ---------------------------------------------------------------------------
def compare(src, values, findings, stats):
    """One program whose rule f is certified: the model against the toolchain on each value."""
    m = load(src)[0]
    r = m.rules['f']
    model = Model(m)
    code = definition_of(m, r)
    mine = model_invert(code)
    theirs = invert(code)
    if not same_code(mine.kids[-1], theirs.kids[-1]):
        findings.append(('`invert` is not the table of V.6', src, ''))
        return
    it = Interp(m)
    for x in values:
        def run(fn, *args):
            try:
                return fn(*args), None
            except (Fault, Refuse) as e:
                return None, str(e)
        y, refused = run(it.forward, r, (), deep_copy(x))
        want, model_refused = run(model.rule, code, [], copy(of_toolchain(x)))
        stats['forward runs'] += 1
        if model_refused == 'proved':
            findings.append(('a `was` the checker proved does not hold', src, str(x)))
            return
        if (refused is None) != (model_refused is None):
            findings.append(('the interpreter and the model disagree on a refusal', src,
                             f'{x}: interpreter {refused}, model {model_refused}'))
            return
        if refused is None and of_toolchain(y) != want:
            findings.append(('the interpreter is not the model', src, f'{x}: {of_toolchain(y)}, model {want}'))
            return
        z = y if refused is None else x          # also run the inverse on a value that may be outside the image
        back, refused = run(it.undo, r, (), deep_copy(z))
        want, model_refused = run(model.rule, mine, [], copy(of_toolchain(z)))
        stats['inverse runs'] += 1
        if (refused is None) != (model_refused is None) or (refused is None and of_toolchain(back) != want):
            findings.append(('the interpreter\'s undo is not the model\'s inverse', src,
                             f'{z}: {back} {refused}, model {want} {model_refused}'))
            return
    stats['proved uncomputes reached'] += model.proved_reached


def run(programs=300, seed=1, inputs=10):
    import generated_04
    import roundtrip_gen
    rng = random.Random(seed)
    stats = {'rules': 0, 'forward runs': 0, 'inverse runs': 0, 'proved uncomputes reached': 0}
    findings = []
    for n in range(programs):
        if n % 2:
            src, value = roundtrip_gen.Gen(rng).program(), roundtrip_gen.value
        else:
            src, value = generated_04.Structures(rng).program(), generated_04.struct_value
        try:
            load(src)
        except CheckError as e:
            if 'internal' in str(e):      # the checker could not check an inverse it derived itself
                findings.append(('checker failure', src, str(e)))
            continue
        stats['rules'] += 1
        compare(src, [value(rng) for _ in range(inputs)], findings, stats)
    return stats, findings


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    s = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    stats, findings = run(n, s)
    print(f'{n} programs: ' + ', '.join(f'{v} {k}' for k, v in stats.items()) + f'; {len(findings)} findings')
    for kind, src, detail in findings[:4]:
        print(f'--- {kind}: {detail}\n{src[-700:]}')
    sys.exit(1 if findings else 0)
