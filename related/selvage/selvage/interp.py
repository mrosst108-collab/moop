"""The reversible interpreter: one engine, forward only.

A clause rule runs forward.  Its inverse is another clause rule, derived by
`invert` and checked by the checker, and it runs forward on the same engine:

  undo    user-facing: a certified rule's inverse; nothing kept is touched
  rewind  system-facing: any rule's inverse; what the rule kept comes back

Every loss is a `keep` message to the nearest keeper: the Object every run starts
in, which holds a Root and delegates to it.  The journal is that Root's state, a
Selvage value.  An expression rule's internal overwrites are recomputable (Bennett)
and are not journaled; a procedure keeps the replies the world gives it.  A refusal
is a request: the nearest installed answer for Refusal takes it, or the run ends.
"""
import math
import os
import sys

from .forms import Form, Word, Arr, Inst, Fault, INT_TYPES, MAYBE, show, weight, identity, equal, encode
from .checker import CONVERSIONS, WIDENINGS, pattern_vars, is_ctor_name, free_names, definition_of
from .invert import invert, invert_clause, NotInvertible, as_sequence, as_block
from .codeid import code_form, SharedIdentity
from .account import dropped_bits, entry_bits, decision_bits
from .declared import declared, undeclared, is_declared


def deep_copy(v):
    """A copy that shares nothing a later update could change.  Arrays are updated in place,
    and an instance's state holds arrays, so an instance is copied with its state; its
    parameters are only ever read, so they stay shared."""
    if isinstance(v, Arr):
        if v.data and isinstance(v.data[0], (Arr, tuple, Form, Inst)):
            return Arr(v.ty, [deep_copy(x) for x in v.data])
        return Arr(v.ty, list(v.data))
    if isinstance(v, tuple):
        return tuple(deep_copy(x) for x in v)
    if isinstance(v, Inst):
        return Inst(v.answer, v.params, deep_copy(v.state))
    if isinstance(v, Form) and v.kids and any(isinstance(k, (Arr, tuple, Form, Inst)) for k in v.kids):
        return Form(v.tag, tuple(deep_copy(k) for k in v.kids), v.line)
    return v


def unflex(v):
    if isinstance(v, Word) and v.flex:
        return Word(v.v, 'I64')
    return v


def comp_get(state, path):
    """The component of a state at a delegation path: the state itself, a tuple member, a field."""
    for i in path:
        state = state[i] if isinstance(state, tuple) else state.kids[i]
    return state


def comp_set(state, path, v):
    if not path:
        return v
    i = path[0]
    if isinstance(state, tuple):
        return state[:i] + (comp_set(state[i], path[1:], v),) + state[i + 1:]
    return Form(state.tag, state.kids[:i] + (comp_set(state.kids[i], path[1:], v),) + state.kids[i + 1:])


DEPTH = 10000    # the default depth bound: rule invocations in progress (the C runtime has the same)


def depth_bound():
    spec = os.environ.get('SELVAGE_DEPTH')
    if spec is None:
        return DEPTH
    if not spec.isdigit() or int(spec) < 1:
        raise Fault('SELVAGE_DEPTH must be a positive whole number')
    return int(spec)


class TailCall:
    """A rule's call of itself in tail position: the invocation goes round again."""
    def __init__(self, args):
        self.args = args


def trunc_div(x, y):
    q = abs(x) // abs(y)
    return q if (x >= 0) == (y >= 0) else -q


class Interp:
    def __init__(self, model, out=None, decider=None):
        self.m = model
        self.out = out if out is not None else sys.stdout
        from .deciders import refuse
        self.decider = decider or refuse   # the world's answer to settle
        self.decisions = []                 # what the world was asked, for --record
        self.epsilon = 0        # bits pruned from the journal at commits
        # The stack of installed answer instances, innermost last.  Every run starts
        # inside an Object (the user-facing root).  It holds a Root, the system-facing
        # root, whose state is the journal, and delegates every request to it.
        self.root = [Inst('Object', (), Inst('Root', (), Form('Empty', ())))]
        self.handlers = [self.root]
        self.frames = []         # the expression rules running, innermost last
        self.depth = 0           # rule invocations in progress
        self.depth_limit = depth_bound()
        self.answering = []      # installed instances answering now: (place in the stack, request)
        self.clauses = []        # the clauses running now, innermost last
        self.code_ids, self.mirror_ids, self.codes = {}, {}, {}
        self.authority = 'user'  # 'system' while rewinding: only then may kept entries come back
        self.kept = 0            # entries in the root's journal
        self.charges = []        # the charge for each of them, oldest first (VII.5)
        self.runs = []           # (rule, its output in canonical form, entries before, entries after), for runs that kept
        self.budget = 0          # entries the rewind in progress may take back: exactly its run's
        self.steps = 0

    # ---- the journal: Root's state, kept by messages ----------------------------------
    def keeper(self):
        for cell in reversed(self.handlers):
            if self.m.answers_op(cell[0].answer, 'keep'):
                return cell
        raise Fault('no answer keeps the journal')

    def journal_of(self, inst):
        """The journal an instance keeps: its own state (Root), or its component's (Object)."""
        a = self.m.answers[inst.answer]
        if 'keep' in a.ops:
            return inst.state
        return self.journal_of(comp_get(inst.state, a.delegates['keep'][0]))

    def with_journal(self, inst, j):
        a = self.m.answers[inst.answer]
        if 'keep' in a.ops:
            return Inst(inst.answer, inst.params, j)
        path = a.delegates['keep'][0]
        return Inst(inst.answer, inst.params,
                    comp_set(inst.state, path, self.with_journal(comp_get(inst.state, path), j)))

    def keep(self, entry, bits=None):
        """A loss: the entry goes to the nearest keeper as a `keep` message (Root's rule)."""
        cell = self.keeper()
        _, cell[0] = self.send(cell[0], 'keep', (entry,))
        self.kept += 1
        self.charges.append(entry_bits(entry) if bits is None else bits)

    def take_back(self, line=None):
        """The backward reading of `keep`: Root's derived inverse, run by the system only."""
        if self.authority != 'system':
            raise Fault(f'line {line}: only the system takes back what was kept (rewind); '
                        f'`undo` is for certified rules')
        if self.budget <= 0:
            raise Fault(f'line {line}: rewind out of order: this rewind may take back only what its own '
                        f'run kept, and the newest entries belong to another run')
        cell = self.keeper()
        if self.journal_of(cell[0]) == Form('Empty', ()):
            raise Fault('rewind reached a commit point: nothing is kept')
        req, cell[0] = self.unsend_any(cell[0], 'keep', (), line)
        self.budget -= 1
        self.kept -= 1
        if self.charges:
            self.charges.pop()
        return req.kids[0]

    def take_back_from(self, r, kind, line=None):
        """Take back the newest entry, which must be of this kind and kept by the rule this
        code is the inverse of: rewinds go newest first, and one out of step is refused."""
        e = self.take_back(line)
        owner = r.inverse.name if r.backward and r.inverse is not None else r.name
        if e.tag != kind or not self.clauses or e.kids[0] != self.mirrors(self.clauses[-1], r):
            raise Fault(f'line {line}: journal out of step: {owner} expected its {kind} entry, found {show(e)}')
        return e

    # An entry names the code that kept it by that code's identity (III.3), and code takes back
    # what its mirror kept: the clause running backward is `mirror` of the clause that ran.
    # An identity is a name, and does not by itself establish equality (III.3).  So the run
    # holds the canonical form behind every identity it uses, and refuses if two different
    # pieces of code share one: where two identities are compared, the forms are compared.
    def code_of(self, c, r):
        got = self.code_ids.get(id(c))
        if got is None:
            got = self.code_ids[id(c)] = (self.named(c, r), c)
        return got[0]

    def mirrors(self, c, r):
        got = self.mirror_ids.get(id(c))
        if got is None:
            got = self.mirror_ids[id(c)] = (self.named(invert_clause(c), r), c)
        return got[0]

    def named(self, code, r):
        """The identity of a piece of code that runs: its canonical form (variables by their
        binding, references by identity), hashed.  `r` is the rule it stands in."""
        try:
            form = code_form(self.m, code, r)
        except SharedIdentity as e:
            raise Fault(str(e))
        name = identity(form)
        if self.codes.setdefault(name, form) != form:
            raise Fault(f'two different pieces of code share the identity {name}; an entry cannot name which kept it')
        return name

    @property
    def journal(self):
        out, j = [], self.journal_of(self.root[0])
        while j.tag == 'Kept':
            out.append(j.kids[0])
            j = j.kids[1]
        return out[::-1]


    def commit(self):
        """A commit point: the journals are dissipated (epsilon counts the bits)."""
        self.epsilon += self.journal_bits()
        for cell in self.handlers:
            if self.m.answers_op(cell[0].answer, 'keep'):
                cell[0] = self.with_journal(cell[0], Form('Empty', ()))
        self.kept, self.runs, self.charges = 0, [], []

    @staticmethod
    def entry_bits(e):
        """The charge for an entry as its declaration leaves it open (account.py)."""
        return entry_bits(e)

    def journal_bits(self):
        """The charge for what the journal holds.  An entry the run did not keep itself (one
        put there from outside) is charged as its declaration leaves it open."""
        js = self.journal
        if len(js) != len(self.charges):
            return sum(entry_bits(e) for e in js)
        return sum(self.charges)

    # ---- arithmetic (R8: every case defined or refused) -------------------
    def arith(self, op, a, b, line=None):
        if isinstance(a, Word) and isinstance(b, Word):
            if not a.flex and not b.flex and a.ty != b.ty:
                raise Fault(f'line {line}: {a.ty} and {b.ty} do not mix; convert one')
            ty = a.ty if not a.flex else (b.ty if not b.flex else 'I64')
            x, y = Word(a.v, ty).v, Word(b.v, ty).v
            flex = a.flex and b.flex
            if op == 'Add':
                return Word(x + y, ty, flex)
            if op == 'Subtract':
                return Word(x - y, ty, flex)
            if op == 'Multiply':
                return Word(x * y, ty, flex)
            if y == 0:
                raise Fault(f'line {line}: division by zero')
            q = trunc_div(x, y)
            if op == 'Divide':
                return Word(q, ty, flex)
            return Word(x - y * q, ty, flex)
        if isinstance(a, str) and isinstance(b, str) and op == 'Add':
            return a + b
        if isinstance(a, (Word, float)) and isinstance(b, (Word, float)) and \
                not isinstance(a, bool) and not isinstance(b, bool):
            if (isinstance(a, Word) and not a.flex) or (isinstance(b, Word) and not b.flex):
                raise Fault(f'line {line}: integers and F64 do not mix; convert with F64(...)')
            x = float(a.v) if isinstance(a, Word) else a
            y = float(b.v) if isinstance(b, Word) else b
            if op == 'Add':
                return x + y
            if op == 'Subtract':
                return x - y
            if op == 'Multiply':
                return x * y
            if op == 'Divide':
                if y == 0.0:
                    if x == 0.0 or math.isnan(x):
                        return math.nan
                    return math.copysign(math.inf, x) * math.copysign(1.0, y)
                return x / y
            if y == 0.0:
                return math.nan
            return math.fmod(x, y)
        raise Fault(f'line {line}: cannot apply {op} to {show(a)} and {show(b)}')

    def compare(self, op, a, b, line=None):
        if isinstance(a, Word) and isinstance(b, Word):
            if not a.flex and not b.flex and a.ty != b.ty:
                raise Fault(f'line {line}: cannot compare {a.ty} with {b.ty}')
            ty = a.ty if not a.flex else (b.ty if not b.flex else 'I64')
            x, y = Word(a.v, ty).v, Word(b.v, ty).v
        elif isinstance(a, (Word, float)) and isinstance(b, (Word, float)) and \
                not isinstance(a, bool) and not isinstance(b, bool):
            x = float(a.v) if isinstance(a, Word) else a
            y = float(b.v) if isinstance(b, Word) else b
        else:
            x, y = a, b
            if op not in ('Equal', 'NotEqual'):
                raise Fault(f'line {line}: cannot order {show(a)} and {show(b)}')
        if op == 'Equal':
            return equal(x, y, same=False)
        if op == 'NotEqual':
            return not equal(x, y, same=False)
        if op == 'Less':
            return x < y
        if op == 'Greater':
            return x > y
        if op == 'LessEqual':
            return x <= y
        return x >= y

    @staticmethod
    def convert(ty, v, line=None):
        if ty == 'F64':
            if isinstance(v, Word):
                return float(v.v)
            if isinstance(v, float):
                return v
        elif ty in INT_TYPES:
            if isinstance(v, Word):
                return Word(v.v, ty)
            if isinstance(v, float):
                bits, signed = INT_TYPES[ty]
                if math.isnan(v):
                    return Word(0, ty)
                lo = -(1 << (bits - 1)) if signed else 0
                hi = (1 << (bits - 1)) - 1 if signed else (1 << bits) - 1
                return Word(max(lo, min(hi, int(v))), ty)  # saturating, defined
        raise Fault(f'line {line}: cannot convert {show(v)} to {ty}')

    # ---- expressions --------------------------------------------------------
    def ev(self, e, env):
        tag, k = e.tag, e.kids
        if tag == 'Literal':
            return k[0]
        if tag == 'Name':
            n = k[0]
            if n in env:
                return env[n]
            if n in self.m.ctors:
                return Form(n, ())
            raise Fault(f'line {e.line}: {n} is not available')
        if tag in ('Add', 'Subtract', 'Multiply', 'Divide', 'Mod'):
            return self.arith(tag, self.ev(k[0], env), self.ev(k[1], env), e.line)
        if tag in ('Equal', 'NotEqual', 'Less', 'Greater', 'LessEqual', 'GreaterEqual'):
            return self.compare(tag, self.ev(k[0], env), self.ev(k[1], env), e.line)
        if tag == 'And':           # Kleene: false wins, then maybe
            a = self.ev(k[0], env)
            if a is False:
                return False
            b = self.ev(k[1], env)
            if a is True:
                return b
            return False if b is False else MAYBE
        if tag == 'Or':            # Kleene: true wins, then maybe
            a = self.ev(k[0], env)
            if a is True:
                return True
            b = self.ev(k[1], env)
            if a is False:
                return b
            return True if b is True else MAYBE
        if tag == 'Not':
            a = self.ev(k[0], env)
            return MAYBE if a is MAYBE else (not a)
        if tag == 'Decide':
            # in an expression rule.  A reply from the world is kept: the procedure's result
            # is recomputable from its parameters together with the replies it kept.
            reply, consulted = self.decide(k[0], env, e.line, journal=None)
            if consulted and consulted[-1][0] is None:
                by = self.frames[-1] if self.frames else 'main'
                body = getattr(self.m.rules.get(by), 'block', None) or e       # the procedure's own code
                self.keep(Form('Decided', (self.code_of(body, self.m.rules.get(by)), by, Word(len(consulted) - 1, 'I64'), True)))
            return reply
        if tag == 'Negate':
            v = self.ev(k[0], env)
            if isinstance(v, Word):
                return Word(-v.v, v.ty, v.flex)
            if isinstance(v, float):
                return -v
            raise Fault(f'line {e.line}: cannot negate {show(v)}')
        if tag == 'Tuple':
            return tuple([self.ev(x, env) for x in k])
        if tag == 'Field':
            base = self.ev(k[0], env)
            return self.field(base, k[1], e.line)
        if tag == 'Index':
            arr = self.ev(k[0], env)
            i = self.index(arr, self.ev(k[1], env), e.line)
            return arr.data[i]
        if tag == 'Call':
            return self.call(e, env)
        if tag == 'Send':
            target = k[0]
            if target.tag != 'Name':
                raise Fault(f'line {e.line}: a message goes to a named instance')
            inst = env[target.kids[0]]
            op, args = k[1].kids
            argv = tuple([self.ev(a, env) for a in args.kids])
            reply, inst2 = self.send(inst, op, argv)
            env[target.kids[0]] = inst2
            return reply
        if tag == 'Ask':
            op, args = k[0].kids
            argv = tuple([self.ev(a, env) for a in args.kids])
            return self.ask(op, argv, line=e.line)
        if tag == 'Undo':
            rule, params, inp = self.callee(k[0], env)
            return self.undo(rule, params, deep_copy(self.ev(inp, env)))
        if tag == 'Quote':
            return k[0]
        if tag == 'Instance':
            ae = k[0]
            aname = ae.kids[0] if ae.tag == 'Name' else ae.kids[0].kids[0]
            ans = self.m.answers[aname]
            ps = () if ae.tag == 'Name' else tuple(unflex_to(self.ev(a, env), pt)
                                                   for a, (_, pt) in zip(ae.kids[1].kids, ans.params))
            return Inst(aname, ps, unflex_to(self.ev(k[1], env), ans.takes))
        if tag == 'With':
            inst = self.ev(k[1], env)
            if not isinstance(inst, Inst):
                raise Fault(f'line {e.line}: `with` needs an answer instance')
            cell = [inst]
            takes = 'refuse' in self.m.answered_ops(inst.answer) and 'refuse' not in self.m.answers[inst.answer].native
            self.handlers.append(cell)
            frames, answering = len(self.frames), len(self.answering)
            try:
                v = self.ev(k[0], env)
            except Fault as refusal:
                from .checker import CheckError
                if not takes or isinstance(refusal, CheckError):
                    raise
                # R8 as a request: this instance is the nearest answer for Refusal, so it
                # takes refuse(reason).  What ran inside it stops there; the run goes on.
                del self.frames[frames:]
                del self.answering[answering:]
                _, cell[0] = self.send(cell[0], 'refuse', (str(refusal),))
                v = ()
            finally:
                self.handlers.pop()
            return (v, cell[0])
        raise Fault(f'line {e.line}: cannot evaluate {tag}')

    def field(self, base, name, line):
        if isinstance(base, Form) and base.tag in self.m.ctors:
            fs = self.m.ctors[base.tag][1]
            for i, (fname, _) in enumerate(fs):
                if fname == name:
                    return base.kids[i]
        raise Fault(f'line {line}: {show(base)} has no field {name}')

    @staticmethod
    def index(arr, iv, line):
        if not isinstance(arr, Arr):
            raise Fault(f'line {line}: {show(arr)} is not an array')
        if not isinstance(iv, Word):
            raise Fault(f'line {line}: an index must be an integer')
        i = iv.v
        if i < 0 or i >= len(arr.data):
            raise Fault(f'line {line}: index {i} is outside 0 to {len(arr.data) - 1}')
        return i

    def callee(self, e, env):
        """Resolve a clause-rule call to (rule, param values, input expression)."""
        m = self.m
        f, args = e.kids
        if f.tag == 'Name' and f.kids[0] in m.rules and m.rules[f.kids[0]].kind == 'clauses':
            r = m.rules[f.kids[0]]
            if not r.params:
                return r, (), args.kids[0]
        if f.tag == 'Call' and f.kids[0].tag == 'Name' and f.kids[0].kids[0] in m.rules:
            r = m.rules[f.kids[0].kids[0]]
            return r, tuple([self.ev(a, env) for a in f.kids[1].kids]), args.kids[0]
        raise Fault(f'line {e.line}: not a call of a clause rule')

    def call(self, e, env):
        m = self.m
        f, args = e.kids
        if f.tag == 'Call' or (f.tag == 'Name' and f.kids[0] in m.rules and m.rules[f.kids[0]].kind == 'clauses'):
            rule, params, inp = self.callee(e, env)
            return self.forward(rule, params, deep_copy(self.ev(inp, env)))
        n = f.kids[0]
        a = args.kids
        if n in m.ctors:
            return Form(n, tuple([unflex_to(self.ev(x, env), ft) for x, (_, ft) in zip(a, m.ctors[n][1])]))
        if n in m.rules:
            return self.call_expr_rule(m.rules[n], tuple([self.ev(x, env) for x in a]))
        if n in CONVERSIONS:
            return self.convert(n, self.ev(a[0], env), e.line)
        if n in WIDENINGS:
            return self.ev(a[0], env)       # a Bool given as a Trit: the same value
        if n == 'array':
            ty = a[0].kids[0]
            length = self.ev(a[1], env)
            if not isinstance(length, Word) or length.v < 0:
                raise Fault(f'line {e.line}: an array length must be a non-negative integer')
            zero = 0.0 if ty == 'F64' else (False if ty == 'Bool' else Word(0, ty))
            return Arr(ty, [zero] * length.v)
        vals = [self.ev(x, env) for x in a]
        if n == 'length':
            return Word(len(vals[0].data), 'I64')
        if n in ('bitand', 'bitor', 'bitxor'):
            x, y = vals
            ty = x.ty if not x.flex else (y.ty if not y.flex else 'I64')
            xv, yv = Word(x.v, ty).v, Word(y.v, ty).v
            bits = INT_TYPES[ty][0]
            mask = (1 << bits) - 1
            xv, yv = xv & mask, yv & mask
            r = xv & yv if n == 'bitand' else (xv | yv if n == 'bitor' else xv ^ yv)
            return Word(r, ty)
        if n in ('shift_left', 'shift_right'):
            x, s = vals
            bits, signed = INT_TYPES[x.ty]
            amt = s.v & (bits - 1) if bits > 1 else 0
            if n == 'shift_left':
                return Word(x.v << amt, x.ty)
            return Word(x.v >> amt, x.ty)  # arithmetic for signed, logical for unsigned
        if n == 'sqrt':
            x = float(vals[0].v) if isinstance(vals[0], Word) else vals[0]
            return math.sqrt(x) if x >= 0 else math.nan
        if n == 'floor':
            return float(math.floor(vals[0])) if math.isfinite(vals[0]) else vals[0]
        if n == 'identity':
            return identity(vals[0])
        if n == 'show':
            return show(vals[0])
        if n == 'evaluate':
            code = vals[0]
            env2 = {}
            for i in range(1, len(vals) - 1, 2):
                nm = vals[i]
                env2[nm.kids[0] if isinstance(nm, Form) else nm] = vals[i + 1]
            self.admit(code, env2, e.line)
            return self.ev(code, env2)
        if n == 'definition':
            name = vals[0].kids[0] if isinstance(vals[0], Form) and vals[0].tag == 'Name' else vals[0]
            r = m.rules.get(name) or m.answers.get(name)
            if r is not None:
                return declared(definition_of(m, r))          # a rule or an answer, as it runs
            if name in m.decls:
                return declared(m.decls[name])                # a type or a request group, as written
            raise Fault(f'line {e.line}: nothing is declared under the name {name}')
        if n == 'program':
            return declared(Form('Program', tuple(m.program)))
        if n in ('sequence', 'block'):
            try:
                return (as_sequence if n == 'sequence' else as_block)(vals[0], e.line, whole=True)
            except NotInvertible as x:
                raise Fault(str(x))
        if n == 'inverse':
            try:
                if is_declared(vals[0]):
                    return declared(invert(undeclared(vals[0])))
                return invert(vals[0])
            except NotInvertible as x:
                raise Fault(str(x))
        raise Fault(f'line {e.line}: unknown rule {n}')

    def admit(self, code, env, line):
        """Admission for constructed code: representing code grants nothing, so `evaluate`
        runs a form only after the checker passes it, here and now, as a pure expression
        over the names it is given.  Nothing is remembered: each call is admitted afresh."""
        from .checker import Checker
        from .printer import is_code_form
        if not (is_code_form(code) or isinstance(code, Form) and code.tag == 'Tuple'):
            what = code.tag if isinstance(code, Form) else 'that value'
            raise Fault(f'line {line}: evaluate runs an expression, and {what} is not one')
        ch, saved = Checker(self.m), len(self.m.errors)
        ch.tyof(code, {n: value_type(v, self.m) for n, v in env.items()}, line)
        errs = self.m.errors[saved:]
        del self.m.errors[saved:]

        def effects(x):
            if not isinstance(x, Form) or x.tag == 'Quote':
                return []
            if x.tag in ('Ask', 'Send', 'Decide', 'With', 'Instance', 'Undo') or \
                    (x.tag == 'Call' and ch.clause_callee(x) is not None):
                return [x]
            return [y for k in x.kids for y in effects(k)]
        bad = effects(code)
        if errs or bad:
            why = errs[0] if errs else f'{p_text(bad[0])} is not a pure expression'
            raise Fault(f'line {line}: evaluate refused `{p_text(code)}`: {why}')

    # ---- requests: an instance answers with its own rule for the request, or delegates
    # it to the one component of its state that answers it.  The component's rule runs
    # on the component's state; the instance's other state is untouched. ----------------
    def send(self, inst, op, argv):
        a = self.m.answers[inst.answer]
        rule = a.ops.get(op)
        if rule is not None:
            reply, state = self.run_rule(rule, inst.params, (Form(op, argv), inst.state))
            return reply, Inst(inst.answer, inst.params, state)
        if op in a.delegates:
            path = a.delegates[op][0]
            reply, part = self.send(comp_get(inst.state, path), op, argv)
            return reply, Inst(inst.answer, inst.params, comp_set(inst.state, path, part))
        raise Fault(f'{inst.answer} does not answer {op}')

    def unsend_any(self, inst2, op, reply, line=None):
        """Take back a message: run the derived inverse of the rule that answered it."""
        a = self.m.answers[inst2.answer]
        if op not in a.ops and op in a.delegates:
            path = a.delegates[op][0]
            req, part = self.unsend_any(comp_get(inst2.state, path), op, reply, line)
            return req, Inst(inst2.answer, inst2.params, comp_set(inst2.state, path, part))
        if op not in a.ops:
            raise Fault(f'line {line}: {inst2.answer} does not answer {op}')
        req, state = self.run_rule(a.ops[op].inverse, inst2.params, (reply, inst2.state))
        if req.tag != op:
            raise Fault(f'line {line}: {inst2.answer}: the message does not match on the way back')
        return req, Inst(inst2.answer, inst2.params, state)

    def unsend(self, inst2, op, argv, reply, line=None):
        req, inst = self.unsend_any(inst2, op, reply, line)
        if not equal(req, Form(op, argv), same=True):
            raise Fault(f'line {line}: {inst2.answer}: message does not match on the way back')
        return inst

    def resolve(self, op):
        """Where an `ask` goes: the place in the stack of the nearest installed instance
        that answers `op`, by a rule of its own or by delegation.  An instance that does
        not answer it is passed over, and the request continues outward.

        One path starts further out.  An instance that is answering `op` and asks `op`
        again is passing its request on, so the search starts outside it: a host's answer
        for Witness reaches the next answer for Witness, in the end Root.  This holds only
        for requests a sealed answer finally answers; it is not a rule for requests in
        general."""
        top = len(self.handlers)
        if self.answering and self.answering[-1][1] == op and self.m.passes_outward(op):
            top = self.answering[-1][0]
        for i in range(top - 1, -1, -1):
            if self.m.answers_op(self.handlers[i][0].answer, op):
                return i
        return None

    def answerer(self, op):
        i = self.resolve(op)
        return None if i is None else self.handlers[i]

    def ask(self, op, argv, line=None):
        if op == 'refuse':
            # a refusal a program raises itself: the same request the system makes when an
            # operation refuses.  The nearest answer for Refusal takes it; Root ends the run.
            raise Fault(f'line {line}: {argv[0]}')
        i = self.resolve(op)
        if i is not None:
            cell = self.handlers[i]
            self.answering.append((i, op))
            try:
                reply, cell[0] = self.send(cell[0], op, argv)
            finally:
                self.answering.pop()
            return reply
        if op == 'output':
            self.write(argv[0])
            return ()
        raise Fault(f'line {line}: no answer for request {op}')

    def unask(self, op, argv, reply, line=None):
        """The backward reading of an `ask`: the message is taken back from the instance
        the request went to."""
        i = self.resolve(op)
        if i is None:
            raise Fault(f'line {line}: rewind reached the world: {op} cannot be taken back')
        cell = self.handlers[i]
        self.answering.append((i, op))
        try:
            cell[0] = self.unsend(cell[0], op, argv, reply, line)
        finally:
            self.answering.pop()

    # ---- decisions ------------------------------------------------------------
    def decide(self, e, env, line, journal):
        """Settle a condition.  true and false pass straight through; maybe goes out as
        settle(question, context) to the answers for Decide, innermost first.  An answer
        that replies maybe passes the question on; the world decides last."""
        v = self.ev(e, env)
        if isinstance(v, bool):
            return v, None
        if v is not MAYBE:
            raise Fault(f'line {line}: `decide` settles true, false or maybe, found {show(v)}')
        names = sorted(n for n in free_names(e) if n in env)
        context = Form('Bindings', tuple(Form('Bind', (n, env[n])) for n in names))
        argv = (e, context)
        consulted = []
        reply = MAYBE
        for cell in reversed(self.handlers):
            if not self.m.answers_op(cell[0].answer, 'settle'):
                continue
            r, inst2 = self.send(cell[0], 'settle', argv)
            cell[0] = inst2
            consulted.append((cell, r))
            if r is True or r is False:
                reply = r
                break
            if r is not MAYBE:
                raise Fault(f'{inst2.answer}: settle must reply true, false or maybe')
        if reply is MAYBE:
            record = self.question_record(e, names, env)
            reply = self.decider(record)
            record['reply'] = 'maybe' if reply is MAYBE else ('true' if reply else 'false')
            self.decisions.append(record)
            consulted.append((None, reply))
        if reply is MAYBE:
            raise Fault(f'line {line}: nobody decided `{p_text(e)}`; it is still maybe')
        if journal:   # which answers were asked, and whether the world settled it
            asked = sum(1 for c, _ in consulted if c is not None)
            # charged for the ways it could have been settled: by each answer installed for
            # `Decide`, or by the world, whichever of them were asked
            installed = sum(1 for cell in self.handlers if self.m.answers_op(cell[0].answer, 'settle'))
            self.keep(Form('Decided', journal + (Word(asked, 'I64'), consulted[-1][0] is None)),
                      decision_bits(installed))
        return reply, consulted

    def question_record(self, e, names, env):
        from .printer import expr_text, decl_lines
        called = []

        def walk(x):
            if isinstance(x, Form):
                if x.tag == 'Call' and x.kids[0].tag == 'Name' and x.kids[0].kids[0] in self.m.rules:
                    n = x.kids[0].kids[0]
                    if n not in called:
                        called.append(n)
                for kid in x.kids:
                    walk(kid)
        walk(e)
        context = {n: show(env[n]) for n in names}
        question = expr_text(e)
        key_text = question + '\n' + ''.join(f'{n}={context[n]}\n' for n in names)
        h = 14695981039346656037
        for byte in key_text.encode():
            h = ((h ^ byte) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return {
            'question': question,
            'context': context,
            'key': f'{h:016x}',
            'identity': identity(Form('settle', (e, Form('Bindings', tuple(
                Form('Bind', (n, env[n])) for n in names))))),
            'definitions': ['\n'.join(decl_lines(self.m.rules[n].decl)) for n in called],
        }

    def write(self, v):
        self.out.write((v if isinstance(v, str) else show(v)) + '\n')
        self.commit()   # output reaches the world: a commit point

    # ---- patterns --------------------------------------------------------------
    def match(self, p, v, env):
        tag = p.tag
        if tag == 'Name':
            n = p.kids[0]
            if is_ctor_name(n, self.m):
                return isinstance(v, Form) and v.tag == n and not v.kids
            env[n] = v
            return True
        if tag == 'Literal':
            lit = p.kids[0]
            if isinstance(lit, Word):
                if not isinstance(v, Word):
                    return False
                if v.flex:
                    return v.v == lit.v
                return Word(lit.v, v.ty).v == lit.v and lit.v == v.v
            if isinstance(lit, bool):
                return isinstance(v, bool) and v == lit
            return type(v) is type(lit) and equal(v, lit, same=True)
        if tag == 'Tuple':
            if not isinstance(v, tuple) or len(v) != len(p.kids):
                return False
            return all(self.match(a, b, env) for a, b in zip(p.kids, v))
        if tag == 'Call':
            c = p.kids[0].kids[0]
            args = p.kids[1].kids
            if not isinstance(v, Form) or v.tag != c or len(v.kids) != len(args):
                return False
            return all(self.match(a, b, env) for a, b in zip(args, v.kids))
        raise Fault(f'line {p.line}: {tag} is not a pattern')

    def build(self, p, env):
        """Build a value from a pattern, consuming its names (the other side of match)."""
        tag = p.tag
        if tag == 'Name':
            n = p.kids[0]
            if is_ctor_name(n, self.m):
                return Form(n, ())
            if n not in env:
                raise Fault(f'line {p.line}: {n} is not available')
            return env.pop(n)
        if tag == 'Literal':
            return p.kids[0]
        if tag == 'Tuple':
            return tuple(self.build(x, env) for x in p.kids)
        if tag == 'Call':
            n, args = p.kids[0].kids[0], p.kids[1].kids
            fields = self.m.ctors[n][1] if n in self.m.ctors else ()
            if len(fields) != len(args):
                return Form(n, tuple(self.build(x, env) for x in args))
            # a literal takes the type the field declares, as it does in an expression
            return Form(n, tuple(self.build(x, env) if ft == 'Any' else unflex_to(self.build(x, env), ft)
                                 for x, (_, ft) in zip(args, fields)))
        raise Fault(f'line {p.line}: {tag} is not a pattern')

    def bind(self, p, v, env, line):
        if not self.match(p, v, env):
            raise Fault(f'line {line}: {show(v)} does not match {p_text(p)}')

    # ---- depth (R8): a run nests rule calls to a bound, counted as the C runtime counts
    # them: one for each rule invocation in progress, none for a self tail call ----------
    def enter(self):
        self.depth += 1
        if self.depth > self.depth_limit:
            self.depth -= 1
            raise Fault(f'the run nests deeper than {self.depth_limit} rule calls')

    # ---- clause rules: one engine, for rules and for their derived inverses ------------
    def run_rule(self, r, params, value):
        self.enter()
        try:
            return self.run_rule_(r, params, value)
        finally:
            self.depth -= 1

    def run_rule_(self, r, params, value):
        # a literal takes the type it is given under: the rule's input and its parameters
        params = tuple(unflex_to(p, pt) for p, (_, pt) in zip(params, r.params)) + tuple(params[len(r.params):])
        if not r.is_answer:
            value = unflex_to(value, r.takes)
        env = dict(zip((pn for pn, _ in r.params), params))
        only = self.sharing(r, 0, value, params) if r.journal_choice and r.backward else []
        if len(only) == 1:
            # the value shows which clause ran: nothing was kept for the choice
            c = only[0]
            self.match(c.kids[0], value, env)
        elif r.journal_choice and r.backward:
            # the forward rule kept which clause it took; its inverse takes that back first
            e = self.take_back(None)
            ci = next((i for i, c in enumerate(r.clauses) if e.tag == 'Chose' and e.kids[0] == self.mirrors(c, r)), None)
            if ci is None:
                owner = r.inverse.name if r.inverse is not None else r.name
                raise Fault(f'journal out of step: {owner} expected the entry of a clause it chose, found {show(e)}')
            c = r.clauses[ci]
            if not self.match(c.kids[0], value, env):
                raise Fault(f'{r.name}: the journal and the value disagree')
        else:
            for ci, c in enumerate(r.clauses):
                trial = dict(env)
                if self.match(c.kids[0], value, trial):
                    env = trial
                    break
            else:
                raise Fault(f'{r.name}: no clause matches {show(value)}')
        self.clauses.append(c)
        try:
            self.exec_fwd(c.kids[2], env, r, journal=True)
        finally:
            self.clauses.pop()
        out = unflex_to(self.build(c.kids[1], env), r.returns)   # a literal takes the declared type
        if r.journal_choice and not r.backward:
            # the choice is lost only among the clauses whose right side this output matches
            among = len(self.sharing(r, 1, out, params))
            if among > 1:
                self.keep(Form('Chose', (self.code_of(c, r), r.name, Word(among, 'I64'))))
        return out

    def sharing(self, r, side, value, params):
        """The clauses of `r` whose left (0) or right (1) side matches the value."""
        env = dict(zip((pn for pn, _ in r.params), params))
        return [c for c in r.clauses if self.match(c.kids[side], value, dict(env))]

    def forward(self, r, params, value):
        """A run the system may later rewind.  If it keeps anything, the system remembers the
        run, so that a rewind names the newest such run and its exact output."""
        depth = self.kept
        out = self.run_rule(r, params, value)
        if self.kept > depth:
            # the output itself, in canonical form: a rewind is bound to it by equality, and
            # an identity (a hash) would only be a presumption of it
            self.runs.append((r.name, encode(out), depth, self.kept))
        return out

    def undo(self, r, params, value):
        """User-facing: run a certified rule's derived inverse."""
        if r.cls == 'lossy':
            raise Fault(f'`undo` needs a certified rule; {r.name} is lossy ({r.reasons[0]})')
        return self.run_rule(r.inverse, params, value)

    def rewind(self, r, params, value):
        """System-facing: run any rule's derived inverse, taking back what it kept."""
        mine = bool(self.runs) and self.runs[-1][:2] == (r.name, encode(value))
        if mine and self.kept != self.runs[-1][3]:
            raise Fault(f'rewind out of order: {self.kept - self.runs[-1][3]} entry(ies) were kept after '
                        f'{r.name} ended, and what was kept after a run stands between it and its rewind')
        depth = self.runs[-1][2] if mine else self.kept
        saved = self.authority, self.budget
        self.authority, self.budget = 'system', self.kept - depth
        try:
            back = self.run_rule(r.inverse, params, value)
        finally:
            self.authority, self.budget = saved
        if self.kept != depth:
            raise Fault(f'{r.name}: the rewind left {self.kept - depth} of its run\'s entries behind')
        if mine:
            self.runs.pop()
        return back

    def backward(self, r, params, value, mode):
        return self.undo(r, params, value) if mode == 'undo' else self.rewind(r, params, value)

    def exec_fwd(self, block, env, r, journal):
        for s in block.kids:
            self.step_fwd(s, env, r, journal)
        return env

    def alias_check(self, s, env):
        for ti, ri in self.m.alias_checks.get(id(s), ()):
            if self.ev(ti, env) == self.ev(ri, env):
                raise Fault(f'line {s.line}: R4: the update reads its own target at run time')

    def get_target(self, t, env):
        return self.ev(t, env)

    def set_target(self, t, env, val):
        if t.tag == 'Name':
            env[t.kids[0]] = val
        elif t.tag == 'Index':
            arr = self.ev(t.kids[0], env)
            arr.data[self.index(arr, self.ev(t.kids[1], env), t.line)] = val
        elif t.tag == 'Field':
            base = self.ev(t.kids[0], env)
            fs = self.m.ctors[base.tag][1]
            i = [f for f, _ in fs].index(t.kids[1])
            kids = list(base.kids)
            kids[i] = val
            self.set_target(t.kids[0], env, Form(base.tag, tuple(kids)))
        else:
            raise Fault(f'line {t.line}: cannot update {t.tag}')

    def step_fwd(self, s, env, r, journal):
        self.steps += 1
        tag, k, line = s.tag, s.kids, s.line
        m = self.m
        if tag in ('Let', 'Was'):
            self.is_step(s, env, r, tag == 'Was', journal)
            return
        if tag in ('AddTo', 'SubtractFrom'):
            e, t = k
            self.alias_check(s, env)
            d = self.ev(e, env)
            old = self.get_target(t, env)
            new = self.arith('Add' if tag == 'AddTo' else 'Subtract', old, d, line)
            if isinstance(old, Word) and old.flex is False and isinstance(new, Word):
                new = Word(new.v, old.ty)
            self.set_target(t, env, new)
            return
        if tag == 'Set':      # expression rules only: in a clause rule it is elaborated
            t, e = k
            v = unflex_to_val(self.ev(e, env), self.get_target(t, env))
            if e.tag != 'Call':
                v = deep_copy(v)
            self.set_target(t, env, v)
            return
        if tag == 'Swap':
            a, b = self.get_target(k[0], env), self.get_target(k[1], env)
            self.set_target(k[0], env, b)
            self.set_target(k[1], env, a)
            return
        if tag == 'Restore':
            e = self.take_back_from(r, 'Dropped', line)
            self.bind(Form('Name', (k[0],)), e.kids[2], env, line)
            return
        if tag == 'Discard':
            v = env.pop(k[0])
            if journal:
                t, top, again = self.m.drops.get(id(s), ('Any', None, False))
                self.keep(Form('Dropped', (self.code_of(self.clauses[-1], r), r.name, v)),
                          0 if again else dropped_bits(self.m, v, t, top))
            return
        if tag == 'Output':
            self.write(self.ev(k[0], env))
            return
        if tag == 'Commit':
            self.commit()
            return
        if tag == 'If':
            branch = k[1] if self.truth(self.ev(k[0], env), line) else k[2]
            self.run_scoped(branch, env, r, journal)
            return
        if tag in ('RepeatWith', 'RepeatDown'):
            var, first, last, body = k
            fv, lv = self.ev(first, env), self.ev(last, env)
            ty = self.loop_type(fv, lv)
            a, b = Word(fv.v, ty).v, Word(lv.v, ty).v
            for i in (range(a, b + 1) if tag == 'RepeatWith' else range(a, b - 1, -1)):
                env[var] = Word(i, ty)
                self.run_scoped(body, env, r, journal)
            env.pop(var, None)
            return
        if tag == 'RepeatWhile':
            while self.truth(self.ev(k[0], env), line):
                self.run_scoped(k[1], env, r, journal)
            return
        if tag == 'Do':
            env['$result'] = self.ev(k[0], env)
            return
        raise Fault(f'line {line}: unexpected step {tag}')

    @staticmethod
    def loop_type(lo, hi):
        if not lo.flex:
            return lo.ty
        if not hi.flex:
            return hi.ty
        return 'I64'

    def truth(self, v, line):
        if v is MAYBE:
            raise Fault(f'line {line}: the condition is maybe; say `decide` to settle it')
        if not isinstance(v, bool):
            raise Fault(f'line {line}: a condition must be true or false, found {show(v)}')
        return v

    def run_scoped(self, block, env, r, journal):
        before = set(env)
        self.exec_fwd(block, env, r, journal)
        for n in list(env):
            if n not in before:
                del env[n]

    def is_clause_call(self, e):
        f = e.kids[0]
        m = self.m
        if f.tag == 'Name' and f.kids[0] in m.rules and m.rules[f.kids[0]].kind == 'clauses':
            return True
        return f.tag == 'Call' and f.kids[0].tag == 'Name' and f.kids[0].kids[0] in m.rules \
            and m.rules[f.kids[0].kids[0]].kind == 'clauses'

    def is_pack(self, rhs, env):
        st = rhs.kids[1]
        from .checker import is_pattern
        return is_pattern(st, self.m) and any(n in env for n in pattern_vars(st, self.m)) and \
            all(n in env for n in pattern_vars(st, self.m))

    def is_step(self, s, env, r, back, journal):
        """`p is e`, and its backward reading `p was e`: release what p holds and give
        back what the step took."""
        (pat, rhs), line = s.kids, s.line
        clause = r.kind == 'clauses'
        inner = rhs.kids[0] if rhs.tag == 'Undo' else rhs
        if clause and inner.tag == 'Call' and self.is_clause_call(inner):
            rule, params, inp = self.callee(inner, env)
            src, dst = (pat, inp) if back else (inp, pat)
            rule = rule.inverse if back != (rhs.tag == 'Undo') else rule
            self.bind(dst, self.run_rule(rule, params, self.build(src, env)), env, line)
            return
        if clause and rhs.tag in ('Send', 'Ask'):
            op, args = (rhs.kids[1] if rhs.tag == 'Send' else rhs.kids[0]).kids
            argv = tuple([self.ev(a, env) for a in args.kids])
            if rhs.tag == 'Ask' and not back:
                self.bind(pat, self.ask(op, argv, line=line), env, line)
                return
            if rhs.tag == 'Ask':
                self.unask(op, argv, self.build(pat, env), line)
                return
            tname = rhs.kids[0].kids[0]
            cell = [env[tname]]
            if back:
                cell[0] = self.unsend(cell[0], op, argv, self.build(pat, env), line)
            else:
                reply, cell[0] = self.send(cell[0], op, argv)
                self.bind(pat, reply, env, line)
            if tname:
                env[tname] = cell[0]
            return
        if clause and rhs.tag == 'Decide' and not back:
            self.bind(pat, self.decide(rhs.kids[0], env, line, journal=(self.code_of(self.clauses[-1], r), r.name) if journal else None)[0], env, line)
            return
        if clause and rhs.tag == 'Decide':
            reply = self.build(pat, env)
            v = self.ev(rhs.kids[0], env)
            if isinstance(v, bool):
                if v != reply:
                    raise Fault(f'line {line}: the decision does not match on the way back')
                return
            e = self.take_back_from(r, 'Decided', line)
            asked, world = e.kids[2].v, e.kids[3]
            names = sorted(n for n in free_names(rhs.kids[0]) if n in env)
            argv = (rhs.kids[0], Form('Bindings', tuple(Form('Bind', (n, env[n])) for n in names)))
            cells = [c for c in reversed(self.handlers) if self.m.answers_op(c[0].answer, 'settle')][:asked]
            for i in range(len(cells) - 1, -1, -1):
                said = reply if (i == len(cells) - 1 and not world) else MAYBE
                cells[i][0] = self.unsend(cells[i][0], 'settle', argv, said, line)
            return
        if clause and rhs.tag == 'Instance' and (back or self.is_pack(rhs, env)):
            ae = rhs.kids[0]
            ps = () if ae.tag == 'Name' else tuple(self.ev(a, env) for a in ae.kids[1].kids)
            aname = ae.kids[0] if ae.tag == 'Name' else ae.kids[0].kids[0]
            if back:   # unpack: only an instance this step could have packed is in its image
                inst = self.build(pat, env)
                if not isinstance(inst, Inst) or inst.answer != aname or not equal(inst.params, ps, same=True):
                    raise Fault(f'line {line}: {show(inst)} is not an instance this step packs')
                self.bind(rhs.kids[1], inst.state, env, line)
                return
            self.bind(pat, Inst(aname, ps, self.build(rhs.kids[1], env)), env, line)
            return
        if not back:
            v = self.ev(rhs, env)
            if rhs.tag != 'Call':
                v = deep_copy(v)   # value semantics: never alias an owned array
            self.bind(pat, unflex(v), env, line)
            return
        value = self.build(pat, env)
        if id(s) in self.m.proved:
            return
        expected = unflex(self.ev(rhs, env))
        if not equal(value, expected, same=True):
            raise Fault(f'line {line}: {show(value)} is not what it was computed from '
                        f'(uncompute expected {show(expected)})')

    # ---- expression rules -------------------------------------------------------
    def call_expr_rule(self, r, args):
        if len(args) != len(r.params):
            raise Fault(f'{r.name} takes {len(r.params)} parameter(s)')
        self.enter()
        self.frames.append(r.name)
        depth = len(self.frames)
        try:
            while True:       # a self tail call is a loop: the same invocation, new parameters
                env = {}
                for (pn, pt), a in zip(r.params, args):
                    env[pn] = unflex_to(a, pt)
                v = self.exec_expr_block(r.block, env, r, tail=r.returns != 'Unit')
                if not isinstance(v, TailCall):
                    return v
                args = v.args
        finally:
            del self.frames[depth - 1:]
            self.depth -= 1

    def exec_expr_block(self, block, env, r, tail=False):
        result = ()
        n = len(block.kids)
        for i, s in enumerate(block.kids):
            if i == n - 1 and s.tag == 'Do':
                e = s.kids[0]
                if tail and e.tag == 'Call' and e.kids[0].tag == 'Name' and e.kids[0].kids[0] == r.name:
                    return TailCall(tuple([self.ev(x, env) for x in e.kids[1].kids]))
                v = self.ev(e, env)
                return deep_copy(v) if e.tag == 'Name' else v
            if i == n - 1 and s.tag == 'If' and s.kids[2].kids:
                branch = s.kids[1] if self.truth(self.ev(s.kids[0], env), s.line) else s.kids[2]
                before = set(env)
                v = self.exec_expr_block(branch, env, r, tail)
                for nm in list(env):
                    if nm not in before:
                        del env[nm]
                return v
            if s.tag == 'Do':
                self.ev(s.kids[0], env)
                continue
            self.step_fwd(s, env, r, journal=False)
            env.pop('$result', None)
        return result

    def run_main(self, name='main'):
        r = self.m.rules.get(name)
        if r is None:
            raise Fault(f'no rule {name}')
        if r.kind != 'block' or r.params:
            raise Fault(f'{name} must be a rule without parameters or clauses')
        return self.call_expr_rule(r, ())


def value_type(v, m):
    if isinstance(v, Word):
        return 'Lit' if v.flex else v.ty
    if isinstance(v, bool):
        return 'Bool'
    if v is MAYBE:
        return 'Trit'
    if isinstance(v, float):
        return 'F64'
    if isinstance(v, str):
        return 'Text'
    if isinstance(v, Form) and v.tag in m.ctors:
        return ('Data', m.ctors[v.tag][0])
    if isinstance(v, Arr):
        return ('Array', v.ty)
    if isinstance(v, tuple):
        return ('Tuple', tuple(value_type(x, m) for x in v)) if v else 'Unit'
    return 'Any'


def unflex_to(v, t):
    if isinstance(v, Word) and v.flex:
        if t in INT_TYPES:
            return Word(v.v, t)
        if t == 'F64':
            return float(v.v)
        return Word(v.v, 'I64')
    if isinstance(v, tuple) and isinstance(t, tuple) and t[0] == 'Tuple' and len(t[1]) == len(v):
        return tuple(unflex_to(x, tt) for x, tt in zip(v, t[1]))
    return v


def unflex_to_val(v, like):
    if isinstance(v, Word) and v.flex:
        if isinstance(like, Word):
            return Word(v.v, like.ty)
        if isinstance(like, float):
            return float(v.v)
    return v


def p_text(p):
    from .printer import expr_text
    return expr_text(p)
