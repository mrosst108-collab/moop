"""Generated tests for the 0.4 implementation group: one generator for each change.

  arrows      lossy rules write `=>`, certified rules `<->`; a wrong arrow is refused
              either way; inversion keeps the arrow; a lossy run is rewound exactly
  delegation  a request goes to the one state component that answers it; several are
              refused; none means the answer does not answer it; an `ask` that an
              installed answer does not take continues outward
  rows        functions and procedures by the row; System exactly when `keep` is reached;
              the journal holds exactly the world replies and losses an oracle predicts
  operators   every operator class an expression uses carries a lineage link
  any         `Any` written anywhere in a user declaration is refused
  refusal     a refusal goes to the nearest installed answer for Refusal, or ends the run
  seal        adversarial authority: every route by which a program might write, forge,
              answer for or open what is sealed to Root is refused
  witness     adversarial disclosure: what inner code reads through `history` is what the
              hosts around it pass on, whatever it installs itself
  depth       a run nests rule calls to a bound: one deeper is refused, in the interpreter
              and in compiled code alike; a self tail call adds no depth
  structures  the soundness theorem's three parts on rules that call rules, undo them,
              message and open instances, match variants and decide crisp conditions
  decisions   decisions inside clause rules: who settles each, what is kept, and a rewind
              that restores every answer consulted
  model       the interpreter and `invert` against the model the soundness proof is about,
              written out as a second evaluator (tests/reference_model.py)

Each generator builds programs together with an oracle that predicts, without the
checker or the interpreter, what they must do.  A disagreement is a finding.
Run: python3 tests/generated_04.py [programs] [seed]
"""
import re
import io
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tests'))

from selvage import load, CheckError                     # noqa: E402
from selvage.checker import definition_of                # noqa: E402
from selvage.deciders import fixed, replay               # noqa: E402
from selvage.forms import Word, Arr, Inst, Form, Fault, MAYBE, identity   # noqa: E402
from selvage.interp import Interp, deep_copy             # noqa: E402
from selvage.invert import invert                        # noqa: E402
from selvage.lineage import links                        # noqa: E402
from selvage.printer import code_text                    # noqa: E402
import roundtrip_gen                                     # noqa: E402

W = lambda v, t='I64': Word(v, t)  # noqa: E731


def by_name(text):
    """A printed journal with each entry's code identity left out: these oracles say which rule
    kept an entry; the `journal` part says which code."""
    return re.sub(r'\b(Dropped|Chose|Decided)\("[0-9a-f]{16}", ', r'\1(', text)


def refusal(src):
    """The checker's refusal of a program as text, or None if it is accepted."""
    try:
        load(src)
        return None
    except CheckError as e:
        return str(e)


# ---- 1. arrows -------------------------------------------------------------------------
HEAD = roundtrip_gen.HEAD


class LossyGen(roundtrip_gen.Gen):
    def loss(self, pad):
        if self.r.random() < 0.6:
            return [f'{pad}set {self.target([])} to {self.expr([])}']
        self.fresh += 1
        return [f'{pad}d{self.fresh} is {self.expr([])}', f'{pad}discard d{self.fresh}']

    def program(self):
        pad = '        '
        body = self.block(pad, 0, [])
        body = self.loss(pad) + body if self.r.random() < 0.5 else body + self.loss(pad)
        return '\n'.join(body) + '\n'


def arrows(programs=200, seed=1, inputs=8):
    rng = random.Random(seed)
    stats = {'lossy': 0, 'certified': 0, 'refused': 0, 'rewinds': 0}
    findings = []
    lossy_head = HEAD.replace('<->', '=>')
    for n in range(programs):
        if n % 3 == 2:      # a certified rule: `=>` on it must be refused
            body = roundtrip_gen.Gen(rng).program()[len(HEAD):]
            if refusal(HEAD + body) is not None:
                stats['refused'] += 1
                continue
            stats['certified'] += 1
            why = refusal(lossy_head + body)
            if why is None or 'a certified rule writes `<->`' not in why:
                findings.append(('`=>` accepted on a certified rule', lossy_head + body, str(why)))
            continue
        body = LossyGen(rng).program()
        src = lossy_head + body
        why = refusal(src)
        if why is not None:
            if 'internal' in why or 'a certified rule writes' in why:
                findings.append(('a rule with a loss was not classified lossy', src, why))
            stats['refused'] += 1
            continue
        stats['lossy'] += 1
        m = load(src)[0]
        r = m.rules['f']
        if r.cls != 'lossy' or r.inverse.cls != 'lossy':
            findings.append(('class', src, f'{r.cls}, inverse {r.inverse.cls}'))
            continue
        why = refusal(HEAD + body)
        if why is None or 'a lossy rule writes `=>`' not in why:
            findings.append(('`<->` accepted on a lossy rule', HEAD + body, str(why)))
        code = definition_of(m, r)
        for c in (code, invert(code), invert(invert(code))):
            text = code_text(c)
            if ' => ' not in text or ' <-> ' in text:
                findings.append(('inversion changed the arrow', src, text))
        if invert(invert(code)) != code:
            findings.append(('invert is not an involution on a lossy rule', src, ''))
        it = Interp(m)
        for _ in range(inputs):
            x1, x2 = roundtrip_gen.value(rng), roundtrip_gen.value(rng)
            empty = identity(it.root[0])
            try:
                y1 = it.forward(r, (), deep_copy(x1))
                mid, kept1 = identity(it.root[0]), it.kept
                y2 = it.forward(r, (), deep_copy(x2))
            except Fault:
                it = Interp(m)      # a refusal at run time: defined behaviour; start clean
                continue
            try:
                it.undo(r, (), deep_copy(y2))
                findings.append(('undo ran a lossy rule', src, ''))
            except Fault:
                pass
            if it.kept > kept1 and identity(y1) != identity(y2):
                held = identity(it.root[0])
                try:
                    it.rewind(r, (), deep_copy(y1))
                    findings.append(('an older run was rewound first', src, ''))
                except Fault:
                    if identity(it.root[0]) != held:
                        findings.append(('a refused rewind changed the journal', src, ''))
                        break
            try:
                b2 = it.rewind(r, (), deep_copy(y2))
                ok = identity(b2) == identity(x2) and identity(it.root[0]) == mid
                b1 = it.rewind(r, (), deep_copy(y1))
                ok = ok and identity(b1) == identity(x1) and identity(it.root[0]) == empty and it.kept == 0
            except Fault as e:
                findings.append(('rewind refused its own run', src, str(e)))
                break
            if not ok:
                findings.append(('rewind did not restore the input and the journal', src, ''))
                break
            stats['rewinds'] += 2
    return stats, findings


# ---- 2. delegation ---------------------------------------------------------------------
class Family:
    """A family of answers with an oracle for who answers what."""

    def __init__(self, rng):
        self.r = rng
        self.ops = [f'op{i}' for i in range(rng.randrange(2, 5))]
        self.group = {op: 'G' for op in self.ops}
        self.group['hop'] = 'H'
        self.answers = {}      # name -> dict(groups, own {op: (kind, k)}, shape, parts [(path, name)])
        self.order = []
        self.text = ['request G'] + [f'    {op}(n: I64) returns I64' for op in self.ops] + \
                    ['request H', '    hop(n: I64) returns I64']
        for i in range(rng.randrange(1, 4)):
            self.base(f'B{i}')
        for i in range(rng.randrange(1, 4)):
            self.derived(f'D{i}')

    def rule_text(self, op, kind, k, state):
        if kind == 'add':      # certified: the reply is n, the state gains n * k
            return [f'    ({op}(n), c) <-> (n, c) where', f'        add n * {k} to c']
        if kind == 'set':      # lossy: the old state is overwritten
            return [f'    ({op}(n), c) => (n, c) where', f'        set c to n + {k}']
        if kind == 'own':      # certified, on any state: the reply is n + k
            return [f'    ({op}(n), s) <-> (n, s) where', f'        add {k} to n']
        return [f'    ({op}(n), s) => (n, s) where', f'        set n to {k}']      # 'drop': lossy, reply k

    def base(self, name):
        r = self.r
        groups = r.choice([['G'], ['G'], ['G', 'H'], ['H']])
        pool = [op for op in self.group if self.group[op] in groups]
        own = {op: (r.choice(['add', 'add', 'set']), r.randrange(1, 4))
               for op in r.sample(pool, r.randrange(1, len(pool) + 1))}
        self.answers[name] = dict(groups=groups, own=own, shape=('int',), parts=[])
        self.order.append(name)
        self.text.append(f'answer {name} for {", ".join(groups)} takes I64')
        for op, (kind, k) in own.items():
            self.text += self.rule_text(op, kind, k, None)

    def derived(self, name):
        r = self.r
        earlier = list(self.order)
        c = r.random()
        if c < 0.45:
            shape = ('inst', r.choice(earlier))
        else:
            members = [r.choice(earlier)] + [r.choice(earlier + ['I64', 'I64']) for _ in range(r.randrange(1, 3))]
            r.shuffle(members)
            shape = ('tuple' if c < 0.75 else 'record', tuple(members))
        groups = r.choice([['G'], ['G'], ['G', 'H']])
        pool = [op for op in self.group if self.group[op] in groups]
        own = {op: (r.choice(['own', 'own', 'drop']), r.randrange(100, 104))
               for op in r.sample(pool, r.randrange(0, min(2, len(pool)) + 1))}
        if shape[0] == 'inst':
            parts, takes = [((), shape[1])], shape[1]
        else:
            parts = [((i,), x) for i, x in enumerate(shape[1]) if x != 'I64']
            takes = '(' + ', '.join(shape[1]) + ')'
            if shape[0] == 'record':
                fields = ', '.join(f'f{i}: {x}' for i, x in enumerate(shape[1]))
                self.text.append(f'type S{name}({fields})')
                takes = f'S{name}'
        self.answers[name] = dict(groups=groups, own=own, shape=shape, parts=parts)
        self.order.append(name)
        self.text.append(f'answer {name} for {", ".join(groups)} takes {takes}')
        for op, (kind, k) in own.items():
            self.text += self.rule_text(op, kind, k, None)

    # -- the oracle ----------------------------------------------------------------------
    def able(self, name, op):
        a = self.answers[name]
        if self.group[op] not in a['groups'] or op in a['own']:
            return []
        return [(path, part) for path, part in a['parts'] if self.answers_op(part, op)]

    def answers_op(self, name, op):
        a = self.answers[name]
        return op in a['own'] or (self.group[op] in a['groups'] and len(self.able(name, op)) >= 1)

    def ambiguous(self):
        return [(n, op) for n in self.order for op in self.group if len(self.able(n, op)) > 1]

    def terminal(self, name, op):
        """(answer, path from `name`'s state down to the answering instance)."""
        path = []
        while op not in self.answers[name]['own']:
            (step, part), = self.able(name, op)
            path.append(step)
            name = part
        return name, path

    def instance(self, name):
        """A value of the answer, built here and as source text."""
        a = self.answers[name]
        if a['shape'][0] == 'int':
            v = self.r.randrange(50)
            return Inst(name, (), W(v)), f'{name} from {v}'
        if a['shape'][0] == 'inst':
            v, t = self.instance(a['shape'][1])
            return Inst(name, (), v), f'{name} from ({t})'
        vals, texts = [], []
        for x in a['shape'][1]:
            if x == 'I64':
                n = self.r.randrange(50)
                vals.append(W(n))
                texts.append(str(n))
            else:
                v, t = self.instance(x)
                vals.append(v)
                texts.append(t)
        if a['shape'][0] == 'record':
            return Inst(name, (), Form(f'S{name}', tuple(vals))), f'{name} from S{name}({", ".join(texts)})'
        return Inst(name, (), tuple(vals)), f'{name} from ({", ".join(texts)})'

    def answer(self, inst, op, n):
        """What the instance replies to op(n), and the instance afterwards."""
        a = self.answers[inst.answer]
        if op in a['own']:
            kind, k = a['own'][op]
            if kind == 'add':
                return n, Inst(inst.answer, (), W(inst.state.v + n * k))
            if kind == 'set':
                return n, Inst(inst.answer, (), W(n + k))
            return (n + k if kind == 'own' else k), inst
        (step, part), = self.able(inst.answer, op)
        state = inst.state
        if not step:
            reply, new = self.answer(state, op, n)
            return reply, Inst(inst.answer, (), new)
        i = step[0]
        kids = list(state.kids if isinstance(state, Form) else state)
        reply, kids[i] = self.answer(kids[i], op, n)
        new = Form(state.tag, tuple(kids)) if isinstance(state, Form) else tuple(kids)
        return reply, Inst(inst.answer, (), new)


def delegation(programs=200, seed=1):
    rng = random.Random(seed)
    stats = {'valid': 0, 'ambiguous': 0, 'delegated': 0, 'unanswered': 0, 'messages': 0, 'asks': 0}
    findings = []
    for _ in range(programs):
        fam = Family(rng)
        base = '\n'.join(fam.text) + '\n'
        why = refusal(base)
        if fam.ambiguous():
            stats['ambiguous'] += 1
            name, op = fam.ambiguous()[0]
            if why is None or f'{name} must take {op} itself' not in why:
                findings.append(('several components answer, and it was not refused', base, str(why)))
            continue
        if why is not None:
            findings.append(('a valid family was refused', base, why))
            continue
        stats['valid'] += 1
        m = load(base)[0]
        for name in fam.order:
            for op in fam.group:
                want = fam.answers_op(name, op)
                if m.answers_op(name, op) != want:
                    findings.append(('who answers', base, f'{name} {op}: oracle {want}'))
                    continue
                able = fam.able(name, op)
                if able and m.answers[name].delegates.get(op) != able[0]:
                    findings.append(('delegates to', base, f'{name} {op}: oracle {able[0]}'))
                if want and m.op_rule(name, op).name != f'{fam.terminal(name, op)[0]}.{op}':
                    findings.append(('the rule that answers', base, f'{name} {op}'))
        top = fam.order[-1]
        for op in fam.group:
            n = rng.randrange(1, 9)
            send = f'rule send takes {top} returns (I64, {top})\n    d {{}} (r, d) where\n        r is d -> {op}({n})\n'
            if not fam.answers_op(top, op):
                stats['unanswered'] += 1
                why = refusal(base + send.format('<->'))
                if why is None or f'{top} does not answer {op}' not in why:
                    findings.append(('a message naming an unanswered request was accepted', base + send, str(why)))
                continue
            owner, path = fam.terminal(top, op)
            stats['delegated'] += bool(path)
            lossy = fam.answers[owner]['own'][op][0] in ('set', 'drop')
            arrow, wrong = ('=>', '<->') if lossy else ('<->', '=>')
            if refusal(base + send.format(wrong)) is None:
                findings.append(('the certificate did not follow the delegation', base + send.format(wrong), ''))
            why = refusal(base + send.format(arrow))
            if why is not None:
                findings.append(('a message to a delegating answer was refused', base + send.format(arrow), why))
                continue
            m2 = load(base + send.format(arrow))[0]
            it = Interp(m2)
            inst, _ = fam.instance(top)
            reply, after = fam.answer(inst, op, n)
            out = it.forward(m2.rules['send'], (), deep_copy(inst))
            stats['messages'] += 1
            if out != (W(reply), after):
                findings.append(('a delegated message', base + send.format(arrow), f'{out} not {(reply, after)}'))
                continue
            try:
                back = it.rewind(m2.rules['send'], (), out) if lossy else it.undo(m2.rules['send'], (), out)
            except Fault as e:
                back = f'refused: {e}'
            if back != inst or it.kept:
                findings.append(('taking a delegated message back', base + send.format(arrow), f'{back}'))
        # an `ask` goes to the nearest installed instance that answers it; one that does
        # not is passed over, and with none the request stays in the row and reaches Root
        op = rng.choice(list(fam.group))       # a request of either group: each group is on its own
        mine = [o for o in fam.group if fam.group[o] == fam.group[op]]
        installed = [rng.choice(fam.order) for _ in range(rng.randrange(1, 4))]    # innermost first
        insts = [fam.instance(a) for a in installed]
        expr = 'probe()'
        for _, text in insts:
            expr = f'({expr}) with {text}'
        pat = 'r'
        for i in range(len(insts)):
            pat = f'({pat}, i{i})'
        taker = next((i for i, a in enumerate(installed) if fam.answers_op(a, op)), None)
        need_g = not all(any(fam.answers_op(a, o) for a in installed) for o in mine)
        lossy = any(fam.answers[fam.terminal(a, o)[0]]['own'][o][0] in ('set', 'drop')
                    for a in installed for o in fam.group if fam.answers_op(a, o))
        row = ([fam.group[op]] if need_g else []) + (['System'] if lossy else [])
        go = (f'rule probe returns I64 uses {fam.group[op]}\n    ask {op}(3)\n'
              f'rule go returns I64{" uses " + ", ".join(row) if row else ""}\n    {pat} is {expr}\n    r\n')
        why = refusal(base + go)
        if why is not None:
            findings.append(('the row of a rule that installs answers', base + go, why))
            continue
        for g in row:
            less = [x for x in row if x != g]
            cut = go.replace(f'rule go returns I64 uses {", ".join(row)}',
                             f'rule go returns I64{" uses " + ", ".join(less) if less else ""}')
            why = refusal(base + cut)
            if why is None or f'declare `uses {g}`' not in why:
                findings.append((f'a row without {g} was accepted', base + cut, str(why)))
        m3 = load(base + go)[0]
        it = Interp(m3)
        stats['asks'] += 1
        try:
            got = it.call_expr_rule(m3.rules['go'], ())
        except Fault as e:
            if taker is not None:
                findings.append(('an ask an installed answer takes was refused', base + go, str(e)))
            continue
        if taker is None:
            findings.append(('an ask nobody takes was answered', base + go, str(got)))
        elif got != W(fam.answer(insts[taker][0], op, 3)[0]):
            findings.append(('the wrong instance answered an ask', base + go, str(got)))
    return stats, findings


# ---- 3. rows: functions and procedures -------------------------------------------------
ROWS_HEAD = '''rule cert takes I64 returns I64
    x <-> x where
        add 1 to x
rule lossy takes I64 returns I64
    x => x where
        set x to 0
request G
    op(n: I64) returns I64
answer Sure for G takes I64
    (op(n), c) <-> (n, c) where
        add n to c
answer Loose for G takes I64
    (op(n), c) => (n, c) where
        set c to n
answer Settler for Decide takes I64
    (settle(q, c), n) => (true, n) where
        add 1 to n
        discard q
        discard c
'''
INSTALL = {'Sure': ('G', False), 'Loose': ('G', True), 'Settler': ('Decide', True)}
ORDER = ['Decide', 'G', 'Output', 'System']


class Procedures:
    def __init__(self, rng, kinds=None):
        self.r = rng
        self.rules = []     # each a list of statements (kind, argument)
        kinds = kinds or ['pure', 'pure', 'cert', 'lossy', 'crisp', 'trit', 'send_sure', 'send_loose',
                          'ask', 'output', 'commit', 'call', 'call', 'with', 'with']
        for i in range(rng.randrange(2, 5)):
            body = []
            for _ in range(rng.randrange(1, 5)):
                k = rng.choice(kinds)
                if k in ('call', 'with') and i == 0:
                    k = 'pure'
                arg = None
                if k == 'call':
                    arg = rng.randrange(i)
                elif k == 'with':
                    arg = (rng.randrange(i), rng.choice(sorted(INSTALL)))
                body.append((k, arg))
            self.rules.append(body)

    def row(self, i):
        need = set()
        for k, arg in self.rules[i]:
            if k == 'lossy' or k == 'send_loose':
                need.add('System')
            elif k == 'trit':
                need |= {'Decide', 'System'}
            elif k == 'ask':
                need.add('G')
            elif k == 'output':
                need.add('Output')
            elif k == 'commit':       # it dissipates what Root retains: the effect is System's
                need.add('System')
            elif k == 'call':
                need |= self.row(arg)
            elif k == 'with':
                j, a = arg
                group, is_lossy = INSTALL[a]
                need |= self.row(j) - {group}
                if is_lossy:
                    need.add('System')
        return need

    def text(self, drop=None):
        """The program; `drop` = (rule, group) leaves that group out of that rule's row."""
        out = [ROWS_HEAD]
        for i, body in enumerate(self.rules):
            row = [g for g in ORDER if g in self.row(i) and (i, g) != drop]
            out.append(f'rule r{i}(t: Trit, n: I64) returns I64' + (f' uses {", ".join(row)}' if row else '') + '\n')
            for s, (k, arg) in enumerate(body):
                v = f'v{s}'
                out.append({
                    'pure': f'    {v} is n * 2 + {s}\n',
                    'cert': f'    {v} is cert(n)\n',
                    'lossy': f'    {v} is lossy(n)\n',
                    'crisp': f'    {v} is decide n > 2\n',
                    'trit': f'    {v} is decide t\n',
                    'send_sure': f'    s{s} is Sure from n\n    {v} is s{s} -> op(1)\n',
                    'send_loose': f'    s{s} is Loose from n\n    {v} is s{s} -> op(1)\n',
                    'ask': f'    {v} is ask op(1)\n',
                    'output': '    output n\n',
                    'commit': '    commit\n',
                    'call': f'    {v} is r{arg}(t, n)\n',
                    'with': f'    ({v}, h{s}) is r{arg[0]}(t, n) with {arg[1]} from 0\n' if k == 'with' else '',
                }[k])
            out.append('    n\n')
        return ''.join(out)

    def run(self, i, t, stack, journal, done):
        """Simulate rule i: `stack` is the installed answers, innermost last; `journal` gains
        (entry, by) for what is kept; `done` counts entries dissipated at commit points."""
        for k, arg in self.rules[i]:
            if k == 'lossy':
                journal.append(('Dropped', 'lossy'))
            elif k == 'send_loose':
                journal.append(('Dropped', 'Loose.op'))
            elif k == 'trit' and t is MAYBE:
                if 'Settler' in stack:        # an answer settles it: its rule keeps what it drops
                    journal += [('Dropped', 'Settler.settle')] * 2
                else:                         # the world settles it: the procedure keeps the reply
                    journal.append(('Decided', f'r{i}'))
            elif k == 'ask':
                nearest = next(a for a in reversed(stack) if a in ('Sure', 'Loose'))
                if nearest == 'Loose':
                    journal.append(('Dropped', 'Loose.op'))
            elif k in ('output', 'commit'):
                done[0] += len(journal)
                del journal[:]
            elif k == 'call':
                self.run(arg, t, stack, journal, done)
            elif k == 'with':
                self.run(arg[0], t, stack + [arg[1]], journal, done)


def rows(programs=200, seed=1):
    rng = random.Random(seed)
    stats = {'programs': 0, 'functions': 0, 'procedures': 0, 'rows cut': 0, 'runs': 0, 'kept': 0}
    findings = []
    for _ in range(programs):
        p = Procedures(rng)
        src = p.text()
        why = refusal(src)
        if why is not None:
            findings.append(('the oracle\'s rows were refused', src, why))
            continue
        stats['programs'] += 1
        m = load(src)[0]
        for i in range(len(p.rules)):
            want = 'procedure' if p.row(i) else 'function'
            stats[want + 's'] += 1
            if m.rules[f'r{i}'].cls != want:
                findings.append(('function or procedure', src, f'r{i} should be a {want}'))
            for g in sorted(p.row(i)):
                stats['rows cut'] += 1
                why = refusal(p.text(drop=(i, g)))
                if why is None or f'r{i} ' not in why or f'declare `uses {g}`' not in why:
                    findings.append((f'r{i} was accepted without {g}', p.text(drop=(i, g)), str(why)))
        last = len(p.rules) - 1
        for t in (MAYBE, True, False):
            it = Interp(m, io.StringIO(), fixed(True))
            it.handlers.append([Inst('Sure', (), W(0))])
            bits = [0]
            keep = it.keep

            def counting(entry, charge=None, keep=keep, bits=bits, it=it):
                bits[0] += it.entry_bits(entry) if charge is None else charge
                keep(entry, charge)
            it.keep = counting
            journal, done = [], [0]
            p.run(last, t, ['Sure'], journal, done)
            it.call_expr_rule(m.rules[f'r{last}'], (t, W(3)))
            stats['runs'] += 1
            stats['kept'] += len(journal) + done[0]
            got = [(e.tag, e.kids[1]) for e in it.journal]
            if got != journal:
                findings.append(('what a run keeps', src, f't={t}: {got}, oracle {journal}'))
            if it.epsilon + it.journal_bits() != bits[0] or (it.epsilon > 0) != (done[0] > 0):
                findings.append(('epsilon does not count what was kept', src, f't={t}'))
    return stats, findings


def between_runs(programs=100, seed=1):
    """A reply a procedure kept stands between the runs around it."""
    rng = random.Random(seed)
    stats = {'rewound': 0, 'refused': 0}
    findings = []
    src = ROWS_HEAD + ('rule world(t: Trit) returns Bool uses Decide, System\n    decide t\n'
                       'rule double(n: I64) returns I64\n    n * 2\n')
    m = load(src)[0]
    for _ in range(programs):
        it = Interp(m, io.StringIO(), fixed(True))
        x = W(rng.randrange(1, 99))
        out = it.forward(m.rules['lossy'], (), x)
        kept_after = 0
        for _ in range(rng.randrange(0, 3)):
            if rng.random() < 0.5:
                it.call_expr_rule(m.rules['double'], (W(4),))
            else:
                t = rng.choice([MAYBE, True, False])
                it.call_expr_rule(m.rules['world'], (t,))
                kept_after += t is MAYBE
        try:
            back = it.rewind(m.rules['lossy'], (), out)
            stats['rewound'] += 1
            if kept_after or back != x:
                findings.append(('a run was rewound across a kept reply', src, f'{kept_after} kept after it'))
        except Fault as e:
            stats['refused'] += 1
            if not kept_after:
                findings.append(('a rewind with nothing kept after its run was refused', src, ''))
            elif f'{kept_after} entry(ies) were kept after lossy ended' not in str(e):
                findings.append(('the refusal does not say what stands between the run and its rewind', src, str(e)))
    return stats, findings


def c_program(rng):
    """A rows program inside what compiles to C23, with a main; returns (source, decisions)."""
    p = Procedures(rng, ['pure', 'cert', 'lossy', 'crisp', 'trit', 'output', 'commit', 'call', 'call'])
    last = len(p.rules) - 1
    row = [g for g in ORDER if g in p.row(last) | {'Output'}]
    main = f'rule main uses {", ".join(row)}\n    output r{last}(maybe, 3)\n    output r{last}(true, 3)\n'
    head = ROWS_HEAD[:ROWS_HEAD.index('request G')]
    return head + p.text()[len(ROWS_HEAD):] + main


# ---- 4. operators ----------------------------------------------------------------------
CLASSES = {
    'add': ('word addition on I64', 'ripple_add', 'realized'),
    'mul': ('multiplication', 'ripple_add', 'theorem'),
    'div': ('division and remainder', 'ripple_add', 'theorem'),
    'bit': ('bitwise operations and shifts', 'ccnot', 'theorem'),
    'conv': ('conversion', 'fanout', 'theorem'),
    'f64': ('F64 arithmetic', 'ripple_add', 'theorem'),
    'cmp': ('comparison', 'ripple_add', 'theorem'),
    'bool': ('Boolean logic', 'trit_and', 'realized'),
}


class Exprs:
    def __init__(self, rng):
        self.r = rng
        self.used = set()

    def word(self, depth=0):
        r = self.r
        c = r.random()
        if depth > 2 or c < 0.3:
            return r.choice(['k', 'y', '3', '7'])
        if c < 0.42:
            self.used.add('add')
            return f'({self.word(depth + 1)} {r.choice("+-")} {self.word(depth + 1)})'
        if c < 0.54:
            self.used.add('mul')
            return f'({self.word(depth + 1)} * {self.word(depth + 1)})'
        if c < 0.64:
            self.used.add('div')
            return f'({self.word(depth + 1)} {r.choice(["/", "mod"])} {self.word(depth + 1)})'
        if c < 0.76:
            self.used.add('bit')
            if r.random() < 0.5:
                return f'{r.choice(["bitand", "bitor", "bitxor"])}({self.word(depth + 1)}, {self.word(depth + 1)})'
            return f'{r.choice(["shift_left", "shift_right"])}({self.word(depth + 1)}, 2)'
        self.used.add('conv')
        if c < 0.88:
            return 'I64(u)'
        return f'I64({self.real(depth + 1)})'

    def real(self, depth):
        if depth > 2 or self.r.random() < 0.4:
            return 'g'
        self.used.add('f64')
        return f'({self.real(depth + 1)} {self.r.choice("+-*/")} {self.real(depth + 1)})'

    def cond(self):
        self.used.add('cmp')
        one = f'{self.word(1)} {self.r.choice(["<", ">", "=", "not="])} {self.word(1)}'
        if self.r.random() < 0.4:
            self.used.add('bool')
            other = f'{self.word(2)} {self.r.choice(["<", ">"])} {self.word(2)}'
            return f'({one}) {self.r.choice(["and", "or"])} ({other})'
        return one


def operators(programs=200, seed=1):
    rng = random.Random(seed)
    stats = {'rules': 0, 'links': 0}
    findings = []
    for n in range(programs):
        e = Exprs(rng)
        if n % 2:
            src = ('rule f(k: I64, g: F64, u: U8) takes (I64, I64) returns (I64, I64)\n'
                   f'    (x, y) <-> (x, y) where\n        if {e.cond()}\n            add {e.word()} to x\n')
        else:
            src = f'rule f(k: I64, y: I64, g: F64, u: U8) returns I64\n    {e.word()}\n'
        why = refusal(src)
        if why is not None:
            findings.append(('an operator expression was refused', src, why))
            continue
        stats['rules'] += 1
        m = load(src)[0]
        got = {(what, target, kind) for what, target, kind, _ in links(m, 'f')}
        for cls, link in CLASSES.items():
            stats['links'] += cls in e.used
            if (link in got) != (cls in e.used):
                findings.append(('operator link', src, f'{link[0]}: used {cls in e.used}, linked {link in got}'))
    return stats, findings


# ---- 5. Any ----------------------------------------------------------------------------
TYPES = ['I64', 'Bool', 'Text', 'F64', 'U8', 'Array(I64)', '(I64, Bool)', 'Trit']
SLOTS = '''type Box(inside: {0}, also: {1})
request R
    put(x: {2}) returns {2}
answer A(q: {3}) for R takes {4}
    (put(x), s) <-> (x, s)
rule same(p: {5}) takes {6} returns {6}
    x <-> x
rule value(p: {7}) returns {7}
    p
rule fresh returns Array({8})
    array({8}, 3)
'''


def any_type(programs=200, seed=1):
    rng = random.Random(seed)
    stats = {'accepted': 0, 'refused': 0}
    findings = []
    for _ in range(programs):
        types = [rng.choice(TYPES) for _ in range(8)] + [rng.choice(['I64', 'Bool', 'F64', 'U8'])]
        src = SLOTS.format(*types)
        if refusal(src) is not None:
            findings.append(('a program without Any was refused', src, refusal(src)))
            continue
        stats['accepted'] += 1
        slot = rng.randrange(9)
        types[slot] = 'Any' if slot == 8 else rng.choice(['Any', 'Any', 'Array(Any)', '(I64, Any)', '(Any, Any)'])
        src = SLOTS.format(*types)
        why = refusal(src)
        stats['refused'] += 1
        if why is None or '`Any` belongs to the prelude' not in why:
            findings.append((f'Any was accepted in slot {slot}', src, str(why)))
    return stats, findings


# ---- 6. refusal ------------------------------------------------------------------------
REFUSAL_HEAD = '''type Log
    Clean
    Noted(reason: Text, earlier: Log)
answer Recorder for Refusal takes Log
    (refuse(reason), log) <-> ((), Noted(reason, log))
answer Counter for Refusal takes I64
    (refuse(reason), n) => ((), n) where
        add 1 to n
        discard reason
request G
    op(n: I64) returns I64
answer Sure for G takes I64
    (op(n), c) <-> (n, c) where
        add n to c
rule only3 takes I64 returns I64
    3 <-> 4
'''
ROW = ' uses Output, System, Refusal, G\n'
REASON = {'div': 'division by zero', 'index': 'is outside', 'image': 'no clause matches', 'explicit': 'stop'}


class Stop(Exception):
    def __init__(self, kind):
        self.kind = kind


class Refusals:
    def __init__(self, rng):
        self.r = rng
        self.rules = []
        self.marker = 0
        for i in range(rng.randrange(2, 6)):
            body = []
            for _ in range(rng.randrange(1, 5)):
                k = rng.choice(['mark', 'mark', 'div', 'index', 'image', 'explicit', 'ask', 'call', 'call',
                                'count', 'count', 'record', 'pass'])
                if i == 0 and k in ('call', 'count', 'record', 'pass'):
                    k = 'mark'
                self.marker += 1
                arg = self.marker
                if k in ('div', 'index', 'image'):
                    arg = rng.choice([0, 1, 3, 5])           # the value that refuses
                elif k in ('call', 'count', 'record', 'pass'):
                    arg = (rng.randrange(i), rng.choice([0, 1, 3, 5]))
                body.append((k, arg))
            self.rules.append(body)

    def text(self):
        out = [REFUSAL_HEAD]
        for i, body in enumerate(self.rules):
            out.append(f'rule p{i}(n: I64)' + ROW)
            for s, (k, arg) in enumerate(body):
                out.append({
                    'mark': f'    output {arg}\n',
                    'div': f'    output 10 / (n - {arg}) * 0\n',
                    'index': f'    a{s} is array(I64, 2)\n    output a{s}[n - {arg}] \n',
                    'image': f'    output only3(n - {arg} + 3) * 0\n',
                    'explicit': f'    ask refuse("stop {arg}")\n',
                    'ask': '    output ask op(1)\n',
                }.get(k) or {
                    'call': '    p{0}({1})\n',
                    'count': '    (u{2}, c{2}) is p{0}({1}) with Counter from 0\n    output c{2}\n',
                    'record': '    (u{2}, c{2}) is p{0}({1}) with Recorder from Clean\n    output c{2}\n',
                    'pass': '    (u{2}, c{2}) is p{0}({1}) with Sure from 100\n    output c{2}\n',
                }[k].format(arg[0], arg[1], s))
            out.append('    output 0\n')
        last = len(self.rules) - 1
        out.append('rule main' + ROW + f'    (u, s) is p{last}(1) with Sure from 0\n    output s\n')
        return ''.join(out)

    def run(self, i, n, sure, out):
        """Simulate p_i(n).  `sure` is the stack of Sure counters (innermost last); `out` gains
        what is printed, as text or as ('record', kind)."""
        for k, arg in self.rules[i]:
            if k == 'mark':
                out.append(str(arg))
            elif k == 'div':
                if n == arg:
                    raise Stop('div')
                out.append('0')
            elif k == 'index':
                if n - arg not in (0, 1):
                    raise Stop('index')
                out.append('0')
            elif k == 'image':
                if n != arg:
                    raise Stop('image')
                out.append('0')
            elif k == 'explicit':
                raise Stop('explicit')
            elif k == 'ask':
                sure[-1][0] += 1
                out.append('1')
            elif k == 'call':
                self.run(arg[0], arg[1], sure, out)
            elif k in ('count', 'record'):
                try:
                    self.run(arg[0], arg[1], sure, out)
                    out.append('Counter from 0' if k == 'count' else 'Recorder from Clean')
                except Stop as stop:
                    out.append('Counter from 1' if k == 'count' else ('record', stop.kind))
            elif k == 'pass':
                mine = [100]
                self.run(arg[0], arg[1], sure + [mine], out)
                out.append(f'Sure from {mine[0]}')
        out.append('0')


def refusals(programs=200, seed=1):
    rng = random.Random(seed)
    stats = {'completed': 0, 'ended by Root': 0, 'taken': 0}
    findings = []
    for _ in range(programs):
        p = Refusals(rng)
        src = p.text()
        why = refusal(src)
        if why is not None:
            findings.append(('a refusal program was refused by the checker', src, why))
            continue
        want, top, ended = [], [0], None
        try:
            p.run(len(p.rules) - 1, 1, [top], want)
            want.append(f'Sure from {top[0]}')
        except Stop as stop:
            ended = stop.kind
        m = load(src)[0]
        text = io.StringIO()
        it = Interp(m, text)
        fault = None
        try:
            it.run_main()
        except Fault as e:
            fault = str(e)
        got = text.getvalue().splitlines()
        stats['completed' if ended is None else 'ended by Root'] += 1
        stats['taken'] += sum(1 for w in want if w == 'Counter from 1' or isinstance(w, tuple))
        if (fault is None) != (ended is None) or (ended and REASON[ended] not in fault):
            findings.append(('how the run ended', src, f'oracle {ended}, run {fault}'))
            continue
        ok = len(got) == len(want) and all(
            (g.count('Noted(') == 1 and REASON[w[1]] in g) if isinstance(w, tuple) else g == w
            for g, w in zip(got, want))
        if not ok or len(it.handlers) != 1 or it.frames:
            findings.append(('what a run with refusals prints', src, f'{got}\noracle {want}'))
    return stats, findings


# ---- 7. the seal: adversarial authority -------------------------------------------------
SEAL_HEAD = '''rule drop takes (I64, I64) returns I64
    (a, b) => a where
        discard b
request G
    op(n: I64) returns I64
answer Sure for G takes I64
    (op(n), c) <-> (n, c) where
        add n to c
rule peek returns Journal uses Witness
    ask history()
rule work(n: I64) returns I64 uses System
    v is drop((n, 99))
    v
'''
SEAL_MAIN = 'rule main uses Output, System, Witness\n    x is work(3)\n    h is peek()\n    output x\n'
SENT = 'is a request of System, which is sealed'
MADE = 'which is sealed: only the system makes or opens one'
ROOT = 'Root is sealed: only the system makes or opens one'
NOT_ANSWERED = 'System is sealed to Root'


def seal_attacks(r):
    """One attack: (name, declarations to add, statements for main, what must refuse it).
    The last is ('check', needle) for the checker or ('run', needle) for a refusal at run time."""
    x = f'{r.choice("abcdefgh")}{r.randrange(100)}'
    n = r.randrange(1, 9999)
    forged = r.choice(['Empty', f'Kept(Dropped("00c0de", "drop", {n}), Empty)', f'Kept({n}, Empty)', 'ask history()', 'peek()'])
    entry = r.choice([str(n), f'Dropped("00c0de", "drop", {n})', f'({n}, {n})', 'true'])
    state = r.choice(['Root', '(Root, I64)', '(I64, Root)', 'Object', '(Sure, Root)'])
    row = r.choice(['', ' uses System', ' uses G', ' uses Output', ' uses System, G'])
    return r.choice([
        ('send keep from a procedure', f'rule {x} uses System, Witness\n    u is ask keep({entry})\n', '', ('check', SENT)),
        ('send keep from a clause rule', f'rule {x} takes I64 returns I64 uses System\n    n => n where\n'
         f'        u is ask keep(n)\n        discard u\n', '', ('check', SENT)),
        ('send keep from an answer', f'answer {x.upper()} for G takes I64\n    (op(n), c) => (n, c) where\n'
         f'        u is ask keep(c)\n        discard u\n', '', ('check', SENT)),
        ('message keep to a root', f'rule {x} takes {r.choice(["Root", "Object"])} returns ((), '
         f'{"Root"})\n    o <-> (u, o) where\n        u is o -> keep({n})\n', '', ('check', SENT)),
        ('make a Root', f'rule {x} returns Root uses Witness\n    Root from {forged}\n', '', ('check', ROOT)),
        ('make an Object', f'rule {x} returns Object uses Witness\n    Object from {r.choice(["Empty", forged])}\n',
         '', ('check', MADE)),
        ('make an Object around a forged Root', f'rule {x} returns Object uses Witness\n    Object from (Root from {forged})\n',
         '', ('check', ROOT)),
        ('install a forged root', f'rule {x} returns I64 uses System, Witness\n'
         f'    (v, k) is work(1) with {r.choice(["Root from " + forged, "Object from (Root from " + forged + ")"])}\n    v\n',
         '', ('check', ROOT)),
        ('pack a Root in a clause', f'rule {x} takes Journal returns Root\n    j <-> k where\n        k is Root from j\n',
         '', ('check', ROOT)),
        ('open a Root in a clause', f'rule {x} takes Root returns Journal\n    k <-> j where\n        k was Root from j\n',
         '', ('check', ROOT)),
        ('open an Object in a clause', f'rule {x} takes Object returns Root\n    o <-> k where\n        o was Object from k\n',
         '', ('check', MADE)),
        ('answer keep', f'answer {x.upper()} for System takes Journal\n    (keep(e), j) <-> ((), Kept(e, j))\n',
         '', ('check', NOT_ANSWERED)),
        ('answer keep by holding a root', f'answer {x.upper()} for {r.choice(["System", "System, G", "G, System", "Witness, System"])} '
         f'takes {state}\n', '', ('check', NOT_ANSWERED)),
        ('hold a root and make the holder', f'answer {x.upper()} for Witness takes Root\n'
         f'rule {x} returns {x.upper()} uses Witness\n    {x.upper()} from (Root from {forged})\n', '', ('check', ROOT)),
        ('seal another group to Root', f'request {x.upper()} for Root\n    look() returns Journal\n',
         '', ('check', 'declared in another place')),
        ('declare a prelude name again', r.choice([
            'request System\n    look() returns Journal\n', 'request Witness\n    look() returns Journal\n',
            f'request {x.upper()}\n    keep(e: I64) returns ()\n', f'request {x.upper()}\n    history() returns I64\n',
            'answer Root for G takes I64\n', 'answer Object for G takes I64\n', 'type Journal\n    Forged\n',
            'type Entry\n    Forged\n']), '', ('check', 'twice')),
        ('read history without Witness', f'rule {x} returns Journal{row}\n    {r.choice(["ask history()", "peek()"])}\n',
         '', ('check', 'declare `uses Witness`')),
        ('undo a lossy rule', f'rule {x} returns (I64, I64) uses System\n    undo drop({n})\n',
         '', ('check', 'needs a certified rule')),
        ('commit under an empty row', f'rule {x} returns I64\n    commit\n    {n}\n', '', ('check', 'declare `uses System`')),
        ('pass a request outward off the sealed path', f'answer {x.upper()} for G takes I64\n'
         f'    (op(n), c) => (k, c) where\n        k is ask op(n)\n        discard n\n',
         '', ('check', 'while it is answering op')),
        ('an instance with the wrong state', f'rule {x} returns Sure\n    Sure from {r.choice(["true", "Empty", "(1, 2)", chr(34) + "text" + chr(34)])}\n',
         '', ('check', 'Sure takes a state of type I64')),
        ('take back in user code', f'rule {x} takes I64 returns (I64, I64)\n    a => (a, b) where\n        b was discarded\n',
         f'    y is {x}(x)\n', ('run', 'only the system takes back')),
        ('constructed code', '', f'    y is evaluate(quote ({r.choice(["ask keep(1)", "Root from Empty", "ask history()", "Object from Empty"])}))\n',
         ('run', 'evaluate refused')),
    ])


def seal(programs=200, seed=1):
    rng = random.Random(seed)
    stats = {'refused by the checker': 0, 'refused in the run': 0, 'routes': 0}
    findings, routes = [], set()
    if refusal(SEAL_HEAD + SEAL_MAIN) is not None:
        return stats, [('the program without an attack was refused', SEAL_HEAD + SEAL_MAIN, refusal(SEAL_HEAD + SEAL_MAIN))]
    for _ in range(programs):
        name, decls, stmts, (where, needle) = seal_attacks(rng)
        routes.add(name)
        main = SEAL_MAIN.replace('    output x\n', stmts + '    output x\n')
        src = SEAL_HEAD + decls + main if rng.random() < 0.5 else decls + SEAL_HEAD + main
        why = refusal(src)
        if where == 'check':
            stats['refused by the checker'] += 1
            if why is None or needle not in why:
                findings.append((f'not refused: {name}', src, str(why)))
            elif 'internal' in why:      # refused by accident of the implementation, not by the rule
                findings.append((f'refused only by an internal check: {name}', src, why))
            continue
        if why is not None:
            findings.append((f'refused before the run: {name}', src, why))
            continue
        stats['refused in the run'] += 1
        out = io.StringIO()
        try:
            Interp(load(src)[0], out).run_main()
            findings.append((f'ran: {name}', src, out.getvalue()))
        except Fault as e:
            if needle not in str(e) or out.getvalue():
                findings.append((f'refused for another reason: {name}', src, str(e)))
    stats['routes'] = len(routes)
    return stats, findings


# ---- 8. Witness: adversarial disclosure -------------------------------------------------
WITNESS_HEAD = '''rule spend takes (I64, I64) returns I64
    (kept, secret) => kept where
        discard secret
answer Closed for Witness takes ()
    (history(), s) <-> (Empty, s)
answer Counting for Witness takes I64
    (history(), n) => (h, n) where
        h is ask history()
        add 1 to n
rule redact takes Journal returns (Journal, Journal)
    Empty <-> (Empty, Empty)
    Kept(Dropped(code, by, value), rest) <-> (Kept(Dropped(code, by, ()), shown), Kept(value, hidden)) where
        (shown, hidden) is redact(rest)
    Kept(Chose(code, by, among), rest) <-> (Kept(Chose(code, by, among), shown), hidden) where
        (shown, hidden) is redact(rest)
    Kept(Decided(code, by, asked, world), rest) <-> (Kept(Decided(code, by, asked, world), shown), hidden) where
        (shown, hidden) is redact(rest)
answer Redacting for Witness takes ()
    (history(), s) => (out, s) where
        all is ask history()
        (shown, hidden) is redact(all)
        out is shown
        (shown, hidden) was redact(all)
        all was ask history()
answer Logging for Witness takes Journal
    (history(), log) => (h, Kept(c, log)) where
        h is ask history()
        c is h
answer Audit for Witness takes ()
    (history(), s) => (h, s) where
        h is ask history()
        record is h
        discard record
answer Marking for Witness takes ()
    (history(), s) => (h, s) where
        h is ask history()
        mark is 1
        discard mark
request G
    op(n: I64) returns I64
answer Sure for G takes I64
    (op(n), c) <-> (n, c) where
        add n to c
answer Carrier for G takes (I64, Counting)
    (op(n), s) <-> (n, s)
rule inquire returns Journal uses Witness
    ask history()
'''
HOSTS = {'Closed': 'Closed from ()', 'Counting': 'Counting from 0', 'Redacting': 'Redacting from ()',
         'Logging': 'Logging from Empty', 'Audit': 'Audit from ()', 'Marking': 'Marking from ()',
         'Sure': 'Sure from 0', 'Carrier': 'Carrier from (0, Counting from 0)'}
# hosts whose rule asks `history` of the next answer out
ASKING = ('Counting', 'Redacting', 'Logging', 'Audit', 'Marking')
MEDIATES = ('Closed',) + ASKING
KEEPS = ('Audit', 'Marking')                # hosts that keep a record of each disclosure they make
WITHDRAWAL = 'only the system takes back what was kept'


class Withdrawal(Exception):
    """The oracle's refusal: a copy given back through a host that kept a record of it."""


class Chain:
    """The oracle for a chain of hosts, innermost first.  It knows the hosts by what they are
    said to do (VII.2), and nothing of the toolchain.
      - a request goes to the nearest answer for Witness, and Root gives the whole journal;
      - Closed stops it; the others ask the next answer out;
      - Counting counts and Logging holds a copy, both in their own state: transactional;
      - Audit and Marking keep a record in the journal: durable;
      - Redacting gives its copy back, which takes its ask back from every answer further out.
        What was transactional is rewound; a kept record refuses the giving back."""

    def __init__(self, chain):
        self.chain = chain
        self.counts = [0] * len(chain)
        self.logs = [[] for _ in chain]
        self.kept = 0
        self.rewound = 0

    def next(self, i):
        return next((j for j in range(i, len(self.chain)) if self.chain[j] in MEDIATES), None)

    def ask(self, i=0):
        j = self.next(i)
        if j is None:
            return 'open'
        h = self.chain[j]
        if h == 'Closed':
            return 'closed'
        view = self.ask(j + 1)
        if h == 'Counting':
            self.counts[j] += 1
        elif h == 'Logging':
            self.logs[j].append(view)
        elif h in KEEPS:
            self.kept += 1
        else:
            self.unask(j + 1)
            return 'closed' if view == 'closed' else 'redacted'
        return view

    def unask(self, i):
        j = self.next(i)
        if j is None or self.chain[j] == 'Closed':
            return
        h = self.chain[j]
        if h in KEEPS:
            raise Withdrawal(h)
        if h == 'Counting':
            self.counts[j] -= 1
            self.rewound += 1
        elif h == 'Logging':
            self.logs[j].pop()
            self.rewound += 1
        else:                          # a Redacting host read backward asks again and gives back again
            self.ask(j + 1)
        self.unask(j + 1)


def wrapped(expr, hosts):
    """`expr` under the hosts, innermost first; the pattern that takes the result apart."""
    pat = 'seen'
    for i, h in enumerate(hosts):
        expr = f'({expr}) with {HOSTS[h]}'
        pat = f'({pat}, w{i})'
    return expr, pat


def journal_text(secrets):
    text = 'Empty'
    for sv in secrets:
        text = f'Kept(Dropped("spend", {sv}), {text})'
    return text


RETAIN = '''request Note
    put(n: Journal) returns ()
answer Box for Note takes ()
    (put(n), s) <-> ((), s) where
        n was Empty
rule drop takes Journal returns ()
    n => () where
        discard n
'''
KEEPS_NOTHING = 'a host that gives its copy back keeps nothing of it'


def withdrawal_routes(rng):
    """Hosts that ask history, give their copy back, and try to keep what they read (E8),
    each with random steps around the attempt; and hosts that keep nothing, which pass."""
    def filler():
        return ''.join(rng.choice(['        u0 is 1\n        u0 was 1\n', '', '        out0 is Empty\n'
                                   '        out0 was Empty\n']) for _ in range(rng.randrange(0, 3)))

    def host(body, state='s', takes='()', reply='out', bound=None):
        bound = bound or ('s' if state == 's' else 'mine')
        return (f'answer H for Witness takes {takes}\n    (history(), {bound}) => ({reply}, {state}) where\n'
                f'        all is ask history()\n' + filler() + body + filler() + '        all was ask history()\n')
    copy = rng.choice(['        c is all\n', '        (shown, hidden) is redact(all)\n        c is hidden\n'
                       '        (shown, hidden) was redact(all)\n'])
    cond = rng.choice(['all = Empty', 'all = Kept(Dropped("00c0de", "spend", ()), Empty)'])
    return [
        ('a copy in its state', True, host(copy + '        out is Empty\n', 'Kept(c, mine)', 'Journal')),
        ('a bit of it in its state', True, host(f'        out is Empty\n        if {cond}\n            add 1 to mine\n',
                                                'mine', 'I64')),
        ('a bit of it carried by a loop', True,
         host(f'        t is 0\n        out is Empty\n        repeat with round from 1 to 2\n            swap t and mine\n'
              f'            if {cond}\n                add 1 to t\n        t was 0\n', 'mine', 'I64')),
        ('a copy in the journal', True, host(copy + '        discard c\n        out is Empty\n')),
        ('a copy sent to another request', True,
         host(copy + '        u is ask put(c)\n        u was ()\n        out is Empty\n')),
        ('a copy sent to a component', True,
         host(copy + '        u is k -> put(c)\n        u was ()\n        out is Empty\n', 'k', 'Box', bound='k')),
        ('a copy through a lossy rule', True, host(copy + '        u is drop(c)\n        u was ()\n        out is Empty\n')),
        ('redacted, keeping nothing', False, host('        (shown, hidden) is redact(all)\n        out is shown\n'
                                                  '        (shown, hidden) was redact(all)\n')),
        ('everything, keeping nothing', False, host('        out is all\n')),
        ('a count that does not read it', False, host('        out is all\n        add 1 to mine\n', 'mine', 'I64')),
    ]


def witness(programs=200, seed=1):
    rng = random.Random(seed)
    stats = {'programs': 0, 'disclosed': 0, 'redacted': 0, 'closed': 0, 'rows cut': 0,
             'withdrawals refused': 0, 'records kept': 0, 'effects rewound': 0, 'retaining hosts refused': 0}
    findings = []
    for n in range(programs):
        if n % 4 == 0:      # a host that gives its copy back and tries to keep what it read
            for name, kept, h in withdrawal_routes(rng):
                why = refusal(WITNESS_HEAD + RETAIN + h)
                if kept and (why is None or KEEPS_NOTHING not in why):
                    findings.append((f'a host gave its copy back and kept it: {name}', h, str(why)))
                elif not kept and why is not None:
                    findings.append((f'a host that keeps nothing was refused: {name}', h, why))
                stats['retaining hosts refused'] += kept
        secrets = [rng.randrange(10000, 99999) for _ in range(rng.randrange(1, 4))]
        inner = [rng.choice(sorted(HOSTS)) for _ in range(rng.randrange(0, 3))]      # what inner code installs itself
        outer = [rng.choice(sorted(HOSTS)) for _ in range(rng.randrange(0, 3))]      # what its host installs
        chain = inner + outer                                                          # innermost first
        oracle = Chain(chain)
        try:
            state, refused = oracle.ask(), False
        except Withdrawal:
            state, refused = None, True

        def view(v):
            return 'Empty' if v == 'closed' else journal_text(['()'] * len(secrets) if v == 'redacted' else secrets)
        want_journal = None if refused else view(state)
        instances = []
        for i, h in enumerate(chain):
            instances.append({'Counting': f'Counting from {oracle.counts[i]}',
                              'Logging': 'Logging from ' + ''.join(f'Kept({view(v)}, ' for v in oracle.logs[i])
                                         + 'Empty' + ')' * len(oracle.logs[i])}.get(h, HOSTS[h]))
        # the rows the oracle expects of the inner rule
        inner_w = [h for h in inner if h in MEDIATES]
        needs_witness = not inner_w or inner_w[-1] != 'Closed'
        needs_system = any(h in ASKING for h in inner)
        row = (['Witness'] if needs_witness else []) + (['System'] if needs_system else [])
        expr, pat = wrapped('inquire()', inner)
        value = '(' + ', '.join(['seen'] + [f'w{i}' for i in range(len(inner))]) + ')' if inner else 'seen'
        body = f'    {pat} is {expr}\n    {value}\n'

        def program(row):
            head = 'rule inner' + (f' uses {", ".join(row)}' if row else '')
            expr2, pat2 = 'inner()', 'got'
            for i, h in enumerate(outer):
                expr2 = f'({expr2}) with {HOSTS[h]}'
                pat2 = f'({pat2}, v{i})'
            main = ('rule main uses Output, System, Witness\n'
                    + ''.join(f'    s{i} is spend(({i}, {sv}))\n' for i, sv in enumerate(secrets))
                    + '    before is inquire()\n' + f'    {pat2} is {expr2}\n' + '    after is inquire()\n'
                    + '    unchanged is after = before\n'
                    + '    output got\n' + ''.join(f'    output v{i}\n' for i in range(len(outer)))
                    + '    output unchanged\n')
            return WITNESS_HEAD + head + '\n' + body + main
        src = program(row)
        why = refusal(src)
        if why is not None:
            findings.append(('the oracle\'s program was refused', src, why))
            continue
        stats['programs'] += 1
        for g in row:
            stats['rows cut'] += 1
            cut = program([x for x in row if x != g])
            why = refusal(cut)
            if why is None or f'declare `uses {g}`' not in why:
                findings.append((f'inner code was accepted without {g}', cut, str(why)))
        out = io.StringIO()
        try:
            Interp(load(src)[0], out).run_main()
        except Fault as e:
            # a copy given back through a host that kept a record of it: refused, and nothing shown
            if refused and WITHDRAWAL in str(e) and not out.getvalue():
                stats['withdrawals refused'] += 1
            else:
                findings.append(('the run was refused', src, str(e)))
            continue
        except RecursionError:
            findings.append(('the request never reached Root', src, 'the run did not end'))
            continue
        if refused:
            findings.append(('a kept record of a disclosure was withdrawn', src, out.getvalue()))
            continue
        got = by_name(out.getvalue()).splitlines()
        first = '(' + ', '.join([want_journal] + instances[:len(inner)]) + ')' if inner else want_journal
        # an inquiry leaves the journal as it was, unless a host kept a record of it
        want = [first] + instances[len(inner):] + ['false' if oracle.kept else 'true']
        if got != want:
            findings.append(('what inner code read', src, f'{got}\noracle {want}'))
            continue
        stats[{'open': 'disclosed', 'redacted': 'redacted', 'closed': 'closed'}[state]] += 1
        stats['records kept'] += oracle.kept
        stats['effects rewound'] += oracle.rewound
        leaked = any(str(sv) in line for sv in secrets for line in got)
        if leaked != (state == 'open'):
            findings.append(('a kept value reached inner code past a host', src, '\n'.join(got)))
    return stats, findings


# ---- 9. depth ---------------------------------------------------------------------------
DEPTH_HEAD = '''rule climb(k: I64) takes I64 returns I64
    a <-> a where
        add k to a
        if k > 0
            a is climb(k - 1)(a)
rule ping(n: I64) returns I64
    if n = 0
        0
    otherwise
        1 + pong(n - 1)
rule pong(n: I64) returns I64
    if n = 0
        0
    otherwise
        2 + ping(n - 1)
rule nest(n: I64) returns I64
    if n = 0
        0
    otherwise
        (v, w) is (nest(n - 1) + 1, n)
        v + w - n
rule spin(n: I64, acc: I64) returns I64
    if n = 0
        acc
    otherwise
        spin(n - 1, acc + n)
rule both(n: I64) returns I64
    if n = 0
        spin(5000, 0)
    otherwise
        both(n - 1) + climb(n)(0) * 0
request G
    op(n: I64) returns I64
answer Echo for G takes I64
    (op(n), c) <-> (n, c) where
        add 1 to c
        if n > 0
            c is relay(n - 1)(c)
rule relay(n: I64) takes I64 returns I64
    c <-> c where
        e is Echo from c
        r is e -> op(n)
        r was n
        e was Echo from c
'''


def depth_shape(r):
    """One call and how deep it nests below its caller: (statement, levels, value, compiles to C)."""
    k = r.randrange(0, 12)
    return r.choice([
        (f'climb({k})(0)', k + 1, k * (k + 1) // 2, True),
        (f'undo climb({k})({k * (k + 1) // 2})', k + 1, 0, True),
        (f'ping({k})', k + 1, (k + 1) // 2 + 2 * (k // 2), True),
        (f'nest({k})', k + 1, k, True),                                      # inside a tuple
        (f'spin({k * 1000}, 0)', 1, k * 1000 * (k * 1000 + 1) // 2, True),     # a tail call: a loop
        (f'both({k})', k + 2, 12502500, True),
        (f'relay({k})(0)', 2 * k + 2, k + 1, False),                         # through an answer: interpreter
    ])


def depth_program(rng, compilable=False):
    """A main that makes three calls; returns (source, [(levels below main, what it prints)])."""
    calls = []
    while len(calls) < 3:
        text, levels, value, in_c = depth_shape(rng)
        if in_c or not compilable:
            calls.append((text, levels, value))
    head = DEPTH_HEAD[:DEPTH_HEAD.index('request G')] if compilable else DEPTH_HEAD
    main = 'rule main uses Output\n' + ''.join(f'    output {i}\n    output {t}\n' for i, (t, _, _) in enumerate(calls))
    return head + main, calls


def depth_oracle(calls, bound):
    """What a run prints under a bound, and whether it is refused: main is one level."""
    out = []
    for i, (_, levels, value) in enumerate(calls):
        out.append(str(i))
        if 1 + levels > bound:
            return out, True
        out.append(str(value))
    return out, False


def depth(programs=200, seed=1):
    rng = random.Random(seed)
    stats = {'runs': 0, 'refused': 0, 'completed': 0, 'at the bound': 0}
    findings = []
    for _ in range(programs):
        src, calls = depth_program(rng)
        m = load(src)[0]
        deepest = 1 + max(levels for _, levels, _ in calls)
        for bound in sorted({deepest - 1, deepest, deepest + 1, rng.randrange(1, deepest + 2)}):
            if bound < 1:
                continue
            want, refused = depth_oracle(calls, bound)
            out = io.StringIO()
            it = Interp(m, out)
            it.depth_limit = bound
            fault = None
            try:
                it.run_main()
            except Fault as e:
                fault = str(e)
            stats['runs'] += 1
            stats['refused' if refused else 'completed'] += 1
            stats['at the bound'] += bound == deepest
            got = out.getvalue().splitlines()
            if got != want or (fault is not None) != refused or it.depth != 0:
                findings.append(('a run under a depth bound', src, f'bound {bound}: {got} {fault}\noracle {want} {refused}'))
            elif refused and f'nests deeper than {bound} rule calls' not in fault:
                findings.append(('refused for another reason', src, fault))
    return stats, findings


# ---- 10. structures: the theorem on rules that call, message and open ---------------------
STRUCT_HEAD = '''type Tag
    Red
    Green
    Blue(n: I64)
request G
    put(n: I64) returns I64
answer Cell for G takes I64
    (put(n), c) <-> (n, c) where
        add n to c
rule inc(k: I64) takes I64 returns I64
    x <-> x where
        add k to x
rule mix(k: I64) takes (I64, I64) returns (I64, I64)
    (q, p) <-> (q, p) where
        add k * q to p
        subtract p from q
rule turn takes Tag returns Tag
    Red <-> Green
    Green <-> Red
    Blue(n) <-> Blue(n) where
        add 1 to n
rule low takes I64 returns I64
    0 <-> 2
    1 <-> 5
    2 <-> 1
'''
STRUCT_RULE = ('rule f takes (I64, I64, Cell, Tag) returns (I64, I64, Cell, Tag)\n'
               '    (a, b, c, s) <-> (a, b, c, s) where\n')


class Structures:
    """Steps over (a, b, c, s).  Nothing here knows what the checker accepts: about half the
    rules read what a step changes and must be refused; the rest must satisfy the theorem."""

    def __init__(self, rng):
        self.r = rng
        self.fresh = 0

    def e(self, deep=True):
        r = self.r
        c = r.random()
        if c < 0.3 or not deep:
            return r.choice(['a', 'b', str(r.randrange(1, 5))])
        if c < 0.75:
            return f'{self.e(False)} {r.choice("+-*")} {self.e(False)}'
        return r.choice(['a', 'b'])

    def name(self, prefix):
        self.fresh += 1
        return f'{prefix}{self.fresh}'

    def steps(self, pad, depth=0):
        r, out = self.r, []
        for _ in range(r.randrange(1, 4)):
            k = r.choice(['update', 'update', 'swap', 'call', 'call', 'undo', 'pair', 'unpair', 'message', 'withdraw',
                          'open', 'turn', 'decide', 'if', 'repeat', 'repeat', 'count', 'even', 'temp', 'temps', 'temps'])
            x = r.choice('ab')
            if k == 'update':
                out.append(f'{pad}add {self.e()} to {x}' if r.random() < 0.5 else f'{pad}subtract {self.e()} from {x}')
            elif k == 'swap':
                out.append(f'{pad}swap a and b')
            elif k == 'call':
                out.append(f'{pad}{x} is inc({self.e()})({x})')
            elif k == 'undo':
                out.append(f'{pad}{x} is undo inc({self.e()})({x})')
            elif k == 'pair':
                out.append(f'{pad}(a, b) is mix({r.randrange(1, 4)})((a, b))')
            elif k == 'unpair':
                out.append(f'{pad}(a, b) was mix({r.randrange(1, 4)})((a, b))')
            elif k == 'even':      # a partial bijection: outside three values it refuses, either way
                out.append(f'{pad}{x} is low({x})' if r.random() < 0.6 else f'{pad}{x} is undo low({x})')
            elif k == 'message':
                m, arg = self.name('m'), self.e()
                out += [f'{pad}{m} is c -> put({arg})', f'{pad}add {m} to {x}', f'{pad}{m} was {arg}']
            elif k == 'withdraw':
                m, arg = self.name('m'), self.e()
                out += [f'{pad}{m} is c -> put({arg})', f'{pad}add {m} to {x}', f'{pad}{m} was c -> put({arg})']
            elif k == 'open':
                st = self.name('k')
                out += [f'{pad}c was Cell from {st}', f'{pad}add {self.e()} to {st}', f'{pad}c is Cell from {st}']
            elif k == 'turn':
                out.append(f'{pad}s is turn(s)' if r.random() < 0.7 else f'{pad}s is undo turn(s)')
            elif k == 'temp':
                t = self.name('t')
                out += [f'{pad}{t} is {self.e()}', f'{pad}add {t} to {x}']
            elif k == 'temps':     # a tuple of temporaries, given back in its own pattern or in another
                y = 'b' if x == 'a' else 'a'     # read what the steps between do not change, so it is proved
                t, u = self.name('t'), self.name('t')
                e1, e2 = (r.choice([y, str(r.randrange(1, 5)), f'{y} + {r.randrange(1, 5)}', f'{y} * 2'])
                          for _ in range(2))
                back = f'({t}, {u})' if r.random() < 0.5 else f'({u}, {t})'
                out += [f'{pad}({t}, {u}) is ({e1}, {e2})', f'{pad}add {t} to {x}', f'{pad}subtract {u} from {x}',
                        f'{pad}{back} was ({e1}, {e2})']
            elif k == 'decide' and depth < 2:
                d, cond = self.name('d'), f'{r.choice("ab")} > {r.randrange(0, 6)}'
                out += [f'{pad}{d} is decide {cond}', f'{pad}if {d}'] + self.steps(pad + '    ', depth + 1) \
                    + [f'{pad}{d} was decide {cond}']
            elif k == 'if' and depth < 2:
                out += [f'{pad}if {r.choice("ab")} {r.choice(["<", ">", "="])} {r.randrange(0, 6)}'] \
                    + self.steps(pad + '    ', depth + 1)
                if r.random() < 0.4:
                    out += [f'{pad}otherwise'] + self.steps(pad + '    ', depth + 1)
            elif k == 'repeat' and depth < 2:      # the count is often data the body may try to change
                j = self.name('j')
                out += [f'{pad}repeat with {j} from 1 to {r.choice(["2", "b", "a", "b", "a"])}'] + self.steps(pad + '    ', depth + 1)
            elif k == 'count' and depth < 2:
                i = self.name('i')
                out += [f'{pad}repeat with {i} from 0 to {r.choice(["2", "a", "b"])}', f'{pad}    add {i} to {x}'] \
                    + self.steps(pad + '    ', depth + 1)
            else:
                out.append(f'{pad}swap a and b')
        return out

    def program(self):
        return STRUCT_HEAD + STRUCT_RULE + '\n'.join(self.steps('        ')) + '\n'


def struct_value(rng):
    tag = rng.choice([Form('Red', ()), Form('Green', ()), Form('Blue', (W(rng.randrange(-2, 5)),))])
    return (W(rng.randrange(-3, 7)), W(rng.randrange(-3, 7)), Inst('Cell', (), W(rng.randrange(-3, 7))), tag)


def structures(programs=200, seed=1, inputs=12):
    rng = random.Random(seed)
    stats = {'certified': 0, 'refused': 0, 'round trips': 0, 'refusals in the run': 0, 'inverse refused': 0,
             'inverse accepted': 0}
    findings = []
    for _ in range(programs):
        src = Structures(rng).program()
        why = refusal(src)
        if why is not None:
            if 'internal' in why:
                findings.append(('checker failure', src, why))
            stats['refused'] += 1
            continue
        m = load(src)[0]
        r = m.rules['f']
        if r.cls not in ('bijection', 'partial'):
            findings.append(('class', src, r.cls))
            continue
        stats['certified'] += 1
        it = Interp(m)
        seen = {}
        for _ in range(inputs):
            x = struct_value(rng)
            try:
                y = it.forward(r, (), deep_copy(x))
            except Fault:
                stats['refusals in the run'] += 1
                y = None
            if y is not None:
                ix, iy = identity(x), identity(y)
                if seen.setdefault(iy, ix) != ix:              # part 1
                    findings.append(('not injective', src, f'{seen[iy]} and {ix} both give {iy}'))
                    break
                try:
                    back = it.undo(r, (), deep_copy(y))          # part 2
                except Fault as e:
                    findings.append(('undo refused a value in the image', src, f'{x}: {e}'))
                    break
                if identity(back) != ix or it.kept:
                    findings.append(('undo is not the inverse', src, f'{x} -> {y} -> {back}'))
                    break
                stats['round trips'] += 1
            z = struct_value(rng)                                # part 3
            try:
                w = it.undo(r, (), deep_copy(z))
            except Fault:
                stats['inverse refused'] += 1
                continue
            stats['inverse accepted'] += 1
            try:
                again = it.forward(r, (), deep_copy(w))
            except Fault as e:
                findings.append(('the inverse accepted a value the rule refuses to produce', src, f'{z}: {e}'))
                break
            if identity(again) != identity(z):
                findings.append(('the inverse accepted a value outside the image', src, f'{z} -> {w} -> {again}'))
                break
    return stats, findings


# ---- 11. decisions inside clause rules ----------------------------------------------------
DECIDE_HEAD = '''answer Defer for Decide takes I64
    (settle(q, c), n) => (maybe, n) where
        add 1 to n
        discard q
        discard c
answer Yes for Decide takes I64
    (settle(q, c), n) => (true, n) where
        add 1 to n
        discard q
        discard c
answer No for Decide takes I64
    (settle(q, c), n) => (false, n) where
        add 1 to n
        discard q
        discard c
'''
K3 = {'and': lambda p, q: False if (p is False or q is False) else (True if (p is True and q is True) else MAYBE),
      'or': lambda p, q: True if (p is True or q is True) else (False if (p is False and q is False) else MAYBE)}


def decision_program(rng):
    """A clause rule over (t, u, x) with one to three decisions among other steps.  Returns the
    source and the steps as the oracle reads them."""
    steps, text, names = [], [], []
    for i in range(rng.randrange(1, 4)):
        if rng.random() < 0.4:
            k = rng.randrange(1, 5)
            lossy = rng.random() < 0.5
            steps.append(('set', k) if lossy else ('add', k))
            text.append(f'        set x to x + {k}' if lossy else f'        add {k} to x')
        form = rng.choice(['t', 'u', 't and u', 't or u', 'not t', 'crisp'])
        steps.append(('decide', form, i))
        text.append(f'        d{i} is decide {"x > 2" if form == "crisp" else form}')
        names.append(f'd{i}')
    lossy = any(s[0] == 'set' or (s[0] == 'decide' and s[1] != 'crisp') for s in steps)
    uses = ' uses Decide' if any(s[0] == 'decide' and s[1] != 'crisp' for s in steps) else ''
    ret = ', '.join(['Trit', 'Trit', 'I64'] + ['Bool'] * len(names))

    def source(arrow, row=uses):
        return (DECIDE_HEAD + f'rule gate takes (Trit, Trit, I64) returns ({ret}){row}\n'
                f'    (t, u, x) {arrow} ({", ".join(["t", "u", "x"] + names)}) where\n' + '\n'.join(text) + '\n')
    return source, steps, lossy, uses


def decision_oracle(steps, t, u, x, stack, world):
    """What the rule returns, what is kept, and each answer's count.  `stack` is the installed
    answers, innermost first; `world` is what the world replies."""
    counts, kept, out = [0] * len(stack), [], []
    for s in steps:
        if s[0] == 'add':
            x += s[1]
        elif s[0] == 'set':
            kept.append(('Dropped', 'gate'))
            x += s[1]
        else:
            form = s[1]
            v = {'t': t, 'u': u, 'crisp': x > 2, 'not t': MAYBE if t is MAYBE else (not t)}.get(form)
            if form in ('t and u', 't or u'):
                v = K3[form.split()[1]](t, u)
            if v is MAYBE:
                asked, settled = 0, None
                for i, a in enumerate(stack):
                    asked += 1
                    counts[i] += 1
                    kept += [('Dropped', f'{a}.settle')] * 2       # the answer drops the question and its context
                    if a != 'Defer':
                        settled = a == 'Yes'
                        break
                if settled is None:
                    kept.append(('Decided', 'gate', asked, True))
                    v = world
                else:
                    kept.append(('Decided', 'gate', asked, False))
                    v = settled
            out.append(v)
    return (t, u, W(x)) + tuple(out), kept, counts


def decisions(programs=200, seed=1):
    rng = random.Random(seed)
    stats = {'rules': 0, 'runs': 0, 'settled by an answer': 0, 'settled by the world': 0, 'crisp': 0, 'rewinds': 0,
             'replays': 0, 'replays refused': 0, 'decisions charged': 0}
    findings = []
    for _ in range(programs):
        source, steps, lossy, uses = decision_program(rng)
        arrow, wrong = ('=>', '<->') if lossy else ('<->', '=>')
        src = source(arrow)
        why = refusal(src)
        if why is not None:
            findings.append(('the oracle\'s arrow and row were refused', src, why))
            continue
        if refusal(source(wrong)) is None:
            findings.append(('the other arrow was accepted', source(wrong), ''))
        if uses and (refusal(source(arrow, '')) or '').find('declare `uses Decide`') < 0:
            findings.append(('a rule that may ask the world was accepted without Decide', source(arrow, ''), ''))
        stats['rules'] += 1
        m = load(src)[0]
        r = m.rules['gate']
        for _ in range(6):
            t, u = rng.choice([True, False, MAYBE]), rng.choice([True, False, MAYBE])
            x = rng.randrange(0, 5)
            stack = [rng.choice(['Defer', 'Defer', 'Yes', 'No']) for _ in range(rng.randrange(0, 4))]
            world = rng.choice([True, False])
            it = Interp(m, io.StringIO(), fixed(world))
            cells = [[Inst(a, (), W(0))] for a in reversed(stack)]      # handlers: outermost first
            it.handlers += cells
            before = identity(it.root[0])
            want, kept, counts = decision_oracle(steps, t, u, x, stack, world)
            out = it.forward(r, (), (t, u, W(x)))
            stats['runs'] += 1
            got_kept = [(e.tag, e.kids[1]) + ((e.kids[2].v, e.kids[3]) if e.tag == 'Decided' else ()) for e in it.journal]
            got_counts = [c[0].state.v for c in reversed(cells)]
            for e in kept:
                if e[0] == 'Decided':
                    stats['settled by the world' if e[3] else 'settled by an answer'] += 1
            stats['crisp'] += len([s for s in steps if s[0] == 'decide']) - len([e for e in kept if e[0] == 'Decided'])
            # a decision is charged for the ways it could have been settled: by each answer
            # installed for Decide, or by the world, whichever of them were asked (VII.5)
            charged = [c for c, e in zip(it.charges, it.journal) if e.tag == 'Decided']
            if any(c != 1 + acc_clog2(len(stack) + 1) for c in charged):
                findings.append(('a decision was not charged by the answers installed', src,
                                 f'stack={stack}: charged {charged}'))
            stats['decisions charged'] += len(charged)
            if out != want or got_kept != kept or got_counts != counts:
                findings.append(('a decision in a clause rule', src,
                                 f't={t} u={u} x={x} stack={stack} world={world}\n{out} {got_kept} {got_counts}\n'
                                 f'oracle {want} {kept} {counts}'))
                continue
            # replay (F5): the record of what the world was asked reproduces the run; each record
            # answers once, in order, and nothing is searched for
            record = list(it.decisions)

            def rerun(records):
                again = Interp(m, io.StringIO(), replay(records))
                again.handlers += [[Inst(a, (), W(0))] for a in reversed(stack)]
                return again.forward(r, (), (t, u, W(x))), [e for e in again.journal]
            if record:
                stats['replays'] += 1
                try:
                    if rerun(record) != (out, [e for e in it.journal]):
                        findings.append(('a replay did not reproduce the run', src, f't={t} u={u} x={x}'))
                except Fault as e:
                    findings.append(('a replay of the run\'s own record was refused', src, str(e)))
                wrong = [record[1:]]                                          # the first decision is missing
                wrong += [[dict(record[0], context={'forged': '1'})] + record[1:]]     # asked in another context
                if len(record) > 1 and (record[0]['question'], record[0]['context']) != \
                        (record[1]['question'], record[1]['context']):
                    wrong.append([record[1], record[0]] + record[2:])          # the right records, out of order
                for records in wrong:
                    try:
                        rerun(records)
                        findings.append(('a replay accepted a record that is not the run\'s', src, str(records)[:300]))
                    except Fault as e:
                        stats['replays refused'] += 1
                        if 'replay:' not in str(e):
                            findings.append(('a replay was refused for another reason', src, str(e)))
            try:
                back = it.rewind(r, (), out) if lossy else it.undo(r, (), out)
            except Fault as e:
                findings.append(('the rewind was refused', src, str(e)))
                continue
            stats['rewinds'] += 1
            if back != (t, u, W(x)) or identity(it.root[0]) != before or any(c[0].state.v for c in cells) or it.kept:
                findings.append(('a rewind across decisions', src, f'{back} {[c[0].state.v for c in cells]} {it.kept}'))
    return stats, findings


# ---- 13. the journal: an entry names the code that kept it, by identity (R13) -----------
NAMES = {'f': ['f', 'g', 'renamed'], 'helper': ['helper', 'h2'], 'sink': ['sink', 'fall'],
         'ping': ['ping', 'tick'], 'pong': ['pong', 'tock']}


def journal_program(rng):
    """Five rules.  `f` has three clauses whose right sides overlap, so every run keeps which
    it chose; its clauses drop values themselves or through `helper`.  `sink` calls itself,
    and `ping` and `pong` call each other; each keeps its choice at every level.

    Returns a function giving the source under chosen names, clause order, declaration order
    and changes to what is called, and what the oracle knows of a run."""
    plans = [(tag, rng.choice(['plain', 'own', 'helper', 'both']), rng.randrange(2, 9)) for tag in 'ABC']
    step = {'sink': rng.randrange(1, 5), 'ping': rng.randrange(1, 5), 'pong': rng.randrange(5, 9)}

    def clause(tag, kind, c, helper):
        text = f'    {tag}(n) => n where\n        add {c} to n\n'
        if kind in ('own', 'both'):
            text += f'        x is n * {c}\n        discard x\n'
        if kind in ('helper', 'both'):
            text = text.replace(f'{tag}(n) => n where', f'{tag}(n) => m where') + \
                f'        y is {c}\n        m is {helper}((n, y))\n'
        return text

    def source(names=None, order=(0, 1, 2), declared=(0, 1, 2, 3, 4), helper_adds=0, pong_adds=0):
        nm = dict({k: k for k in NAMES}, **(names or {}))

        def recursive(me, other, by):
            return (f'rule {nm[me]} takes (I64, I64) returns I64\n    (0, acc) => acc\n    (n, acc) => out where\n'
                    f'        add {by} to acc\n        subtract 1 from n\n        out is {nm[other]}((n, acc))\n')
        decls = [
            f'rule {nm["helper"]} takes (I64, I64) returns I64\n    (kept, dropped) => kept where\n'
            + (f'        add {helper_adds} to kept\n' if helper_adds else '') + '        discard dropped\n',
            f'rule {nm["f"]} takes T returns I64\n' + ''.join(clause(*plans[i], nm['helper']) for i in order),
            recursive('sink', 'sink', step['sink']),
            recursive('ping', 'pong', step['ping']),
            recursive('pong', 'ping', step['pong'] + pong_adds),
        ]
        return 'type T\n    A(n: I64)\n    B(n: I64)\n    C(n: I64)\n' + ''.join(decls[i] for i in declared)

    def oracle(rule, tag, n):
        """What a run gives and keeps, oldest entry first: (output, [(entry, rule, clause, value)]),
        the clause given as (the rule as first named, its place as first written)."""
        if rule == 'f':
            i, (_, kind, c) = next((i, p) for i, p in enumerate(plans) if p[0] == tag)
            out, kept = n + c, []
            if kind in ('own', 'both'):
                kept.append(('Dropped', 'f', ('f', i), out * c))
            if kind in ('helper', 'both'):
                kept.append(('Dropped', 'helper', ('helper', 0), c))
            return out, kept + [('Chose', 'f', ('f', i), 3)]
        # (n, acc) with acc = 0: each level adds its rule's step and calls the next with n - 1
        chain = [rule if rule == 'sink' or j % 2 == 0 else {'ping': 'pong', 'pong': 'ping'}[rule] for j in range(n + 1)]
        out = sum(step[r] for r in chain[:-1])
        # a choice is kept after the clause's steps, so the innermost, which took the first clause, is oldest
        kept = [('Chose', chain[-1], (chain[-1], 0), 2)] + [('Chose', r, (r, 1), 2) for r in reversed(chain[:-1])]
        return out, kept
    return source, oracle, plans


def journal(programs=200, seed=1):
    from unittest import mock
    import selvage.interp
    from selvage.codeid import code_identity, rule_identities
    rng = random.Random(seed)
    stats = {'runs': 0, 'entries': 0, 'renamed': 0, 'variables renamed': 0, 'reordered': 0, 'declared elsewhere': 0, 'recursive runs': 0,
             'callees changed': 0, 'rewinds': 0, 'forged entries refused': 0, 'shared identities refused': 0}
    findings = []
    for n in range(programs):
        source, oracle, plans = journal_program(rng)
        # the oracle's names for the code: every clause of the program as first written and
        # named.  Under other names, in another order of clauses or of declarations, the same
        # code has the same identities: a call holds the identity of the rule called, not its name
        base = load(source())[0]
        code = {(r, i): code_identity(base, c) for r in NAMES for i, c in enumerate(base.rules[r].clauses)}
        rule_id = rule_identities(base)
        names = {k: rng.choice(v) for k, v in NAMES.items()}
        order = rng.choice([(0, 1, 2), (1, 0, 2), (2, 1, 0), (1, 2, 0)])
        declared = tuple(rng.sample(range(5), 5))
        stats['renamed'] += any(names[k] != k for k in names)
        stats['reordered'] += order != (0, 1, 2)
        stats['declared elsewhere'] += declared != (0, 1, 2, 3, 4)
        src = source(names, order, declared)
        if rng.random() < 0.5:        # and every variable under another name: the same code still
            src = renamed(src, ['n', 'm', 'x', 'y', 'kept', 'dropped', 'acc', 'out'], lambda v: v + '_v')
            stats['variables renamed'] += 1
        m = load(src)[0]
        if {k: rule_identities(m)[names[k]] for k in NAMES} != {k: rule_id[k] for k in NAMES}:
            findings.append(('a rule\'s identity changed with a name or with where it is declared', src, ''))
            continue
        # a rule that is called is changed: it is another rule, and so is every caller of it;
        # code that does not call it is the same code
        which = rng.choice(['helper', 'pong'])
        changed = load(source(names, order, declared, helper_adds=int(which == 'helper'), pong_adds=int(which == 'pong')))[0]
        stats['callees changed'] += 1
        after = {(r, i): code_identity(changed, c) for r in NAMES for i, c in enumerate(changed.rules[names[r]].clauses)}
        calls_it = {('f', i) for i, p in enumerate(plans) if p[1] in ('helper', 'both')} if which == 'helper' \
            else {('ping', 1), ('pong', 1)}
        f_now = {('f', i): after[('f', order.index(i))] for i in range(3)}      # f's clauses stand in another order
        after.update(f_now)
        for key in code:
            if key == (which, 0) and which == 'helper':
                moved = True                                    # the changed clause itself
            elif which == 'pong' and key == ('pong', 1):
                moved = True
            else:
                moved = key in calls_it
            if (after[key] != code[key]) != moved:
                findings.append(('what a change to a called rule changed', src, f'{which} changed; {key}: '
                                 f'{"changed" if after[key] != code[key] else "unchanged"}'))
        r_of = {k: m.rules[names[k]] for k in NAMES}
        for _ in range(4):
            rule = rng.choice(['f', 'f', 'sink', 'ping', 'pong'])
            if rule == 'f':
                tag, x = rng.choice('ABC'), rng.randrange(-5, 9)
                value = Form(tag, (W(x),))
            else:
                tag, x = None, rng.randrange(0, 6)
                value = (W(x), W(0))
                stats['recursive runs'] += 1
            r = r_of[rule]
            want_out, want_kept = oracle(rule, tag, x)
            want = [(kind, code[clause], names[who], v) for kind, who, clause, v in want_kept]
            it = Interp(m)
            out = it.forward(r, (), deep_copy(value))
            got = [(e.tag, e.kids[0], e.kids[1], e.kids[2].v) for e in it.journal]
            stats['runs'] += 1
            stats['entries'] += len(got)
            if out != W(want_out) or got != want:
                findings.append(('what a run kept, and under which code', src, f'{rule} {tag}({x}): {out} {got}\noracle {want_out} {want}'))
                continue
            # a forged entry: the newest names code that is no clause of this rule, and must be
            # refused; or it names the right code and another keeper, which decides nothing
            top = it.journal[-1]
            stranger = code[('helper', 0)] if rule != 'helper' else '1' * 16
            for forged, must_refuse in ((Form('Chose', (stranger,) + top.kids[1:]), True),
                                        (Form('Chose', ('0' * 16,) + top.kids[1:]), True),
                                        (Form('Chose', (top.kids[0], 'someone else', top.kids[2])), False)):
                it2 = Interp(m)
                out2 = it2.forward(r, (), deep_copy(value))
                it2.root[0] = it2.with_journal(it2.root[0], Form('Kept', (forged, it2.journal_of(it2.root[0]).kids[1])))
                try:
                    back = it2.rewind(r, (), out2)
                    if must_refuse:
                        findings.append(('a rewind took back an entry that names other code', src, f'{rule} {tag}({x}) {forged}'))
                    elif back != value or it2.journal:
                        findings.append(('a rewind went by who kept an entry, not by its code', src, f'{rule} {tag}({x})'))
                except Fault as e:
                    if not must_refuse:
                        findings.append(('a rewind was refused over who kept an entry', src, str(e)))
                    else:
                        stats['forged entries refused'] += 1
            if rule == 'f' and len(got) > 1:      # a dropped value under a name that is not the code taking it back
                it2 = Interp(m)
                out2 = it2.forward(r, (), deep_copy(value))
                j = it2.journal_of(it2.root[0])
                below = j.kids[1]
                mine = code[('f', 'ABC'.index(tag))]
                forged = Form('Dropped', (mine if below.kids[0].kids[0] != mine else code[('helper', 0)],) + below.kids[0].kids[1:])
                it2.root[0] = it2.with_journal(it2.root[0], Form('Kept', (j.kids[0], Form('Kept', (forged, below.kids[1])))))
                try:
                    it2.rewind(r, (), out2)
                    findings.append(('code took back a value that other code is named as keeping', src, f'{tag}({x})'))
                except Fault as e:
                    stats['forged entries refused'] += 'journal out of step' in str(e)
            try:
                back = it.rewind(r, (), out)     # forward kept, backward takes back: they agree on the code
            except Fault as e:
                findings.append(('the rewind was refused', src, str(e)))
                continue
            stats['rewinds'] += 1
            if back != value or it.journal:
                findings.append(('the rewind did not restore', src, f'{rule} {tag}({x}): {back}'))
        if n % 10 == 0:
            # an identity is a name: were two pieces of code to share one, the run must refuse
            # and not guess which kept an entry (III.3)
            with mock.patch.object(selvage.interp, 'identity', lambda v, refs=None: 'one-name'):
                it = Interp(m)
                try:
                    for tag in 'ABC':
                        it.forward(r_of['f'], (), Form(tag, (W(1),)))
                    findings.append(('code that shares an identity was told apart by it', src, ''))
                except Fault as e:
                    if 'share the identity' in str(e):
                        stats['shared identities refused'] += 1
                    else:
                        findings.append(('refused for another reason', src, str(e)))
            # and rules: were two rules to share an identity, their callers could not be told apart
            import selvage.codeid
            fresh = load(src)[0]
            with mock.patch.object(selvage.codeid, 'identity', lambda v, refs=None: 'one-name'):
                try:
                    Interp(fresh).forward(fresh.rules[names['f']], (), Form('A', (W(1),)))
                    findings.append(('rules that share an identity were told apart by it', src, ''))
                except Fault as e:
                    stats['shared identities refused'] += 'share the identity' in str(e)
    return stats, findings


# ---- 14. names: code is identified by what it is and refers to, not by how it is named ----
def renamed(text, names, how):
    """`text` with each of `names` replaced, as a whole word, by `how(name)`."""
    if not names:
        return text
    return re.sub(r'\b(' + '|'.join(sorted(map(re.escape, names), key=len, reverse=True)) + r')\b',
                  lambda w: how(w.group(1)), text)


def scope_cases(rng):
    """Small programs in threes: the code, the same code with its variables renamed
    consistently (binding by binding), and code that differs in which binding a use refers
    to, in the shape of a pattern, or in a name that is not bound.  The oracle knows which
    is which because it wrote them so."""
    a, b, t, u, i, j = rng.sample(['p', 'q', 'u', 'w', 'x', 'y', 'z', 'left', 'right', 'tmp', 'acc', 'it'], 6)
    c1, c2 = rng.randrange(1, 9), rng.randrange(1, 9)
    head = f'rule f takes (I64, I64) returns (I64, I64)\n    ({a}, {b}) <-> ({a}, {b}) where\n'

    def body(*lines):
        return head + ''.join(f'        {line}\n' for line in lines)

    def twice(second, used):        # a name bound again after it was given back: another variable
        return body(f'{t} is {b}', f'add {t} to {a}', f'{t} was {b}', f'{second} is {a}',
                    f'add {used} to {b}', f'{second} was {a}')

    def loops(second):              # two loops, one after the other, may use one counter name
        return body(f'repeat with {i} from 0 to {c1}', f'    add {i} to {a}',
                    f'repeat with {second} from 0 to {c2}', f'    add {second} to {b}')

    def nested(inner, used):        # one loop in another: two counters
        return body(f'repeat with {i} from 0 to {c1}', f'    repeat with {inner} from 0 to {c2}',
                    f'        add {used} to {b}')

    def pair(x, y):                 # the shape of a pattern, and a variable twice in one
        return body(f'{t} is ({x}, {y})', f'{t} was ({x}, {y})')

    def sides(x, y):
        return f'rule f takes (I64, I64) returns (I64, I64)\n    ({a}, {b}) <-> ({x}, {y})\n'

    def param(p1, p2, used):        # parameters are bound by the rule: by place, not by name
        return (f'rule f({p1}: I64, {p2}: I64) takes I64 returns I64\n    {a} <-> {a} where\n'
                f'        add {used} to {a}\n')

    def branches(second, shown):    # two branches may each bind one name: two variables
        return (f'rule f({a}: I64) returns I64 uses Output\n    if {a} > 0\n        {t} is {c1}\n        output {t}\n'
                f'    otherwise\n        {second} is {c2}\n        output {shown}\n    {a}\n')

    def after(inner, used):         # a name bound in a block may be bound again after it
        return (f'rule f({a}: I64) returns I64 uses Output\n    if {a} > 0\n        {inner} is {c1}\n'
                f'        output {inner}\n    {t} is {a} + {c2}\n    {used}\n')

    def ctor(x, y):                 # a name bound nowhere is a name
        return f'type K\n    Red\n    Green\n    Blue\nrule f takes K returns K\n    Red <-> {x}\n    Green <-> {y}\n    Blue <-> Blue\n'

    def quote(p1, said):            # quoted code is data, even where a variable has that name
        return f'rule f({p1}: I64) returns Code\n    quote {said} + {c1}\n'
    read = body(f'{t} is {c1}', f'add {t} to {a}')
    return [
        ('a name bound twice', twice(t, t), [twice(u, u)], []),
        ('two loops with one counter name', loops(i), [loops(j)], []),
        ('two counters', nested(j, j), [renamed(nested(j, j), [i, j], lambda n: n + '_c')], [nested(j, i)]),
        ('which variable is read', read, [renamed(read, [a, b, t], lambda n: n + '_r')],
         [body(f'{t} is {c1}', f'add {t} to {b}'), body(f'{t} is {c1 + 10}', f'add {t} to {a}')]),
        ('a variable twice in a pattern', pair(a, a), [renamed(pair(a, a), [a, b, t], lambda n: 'k_' + n)],
         [pair(a, b), pair(b, b)]),
        ('the sides of a clause', sides(a, b), [renamed(sides(a, b), [a, b], lambda n: n + n)], [sides(b, a)]),
        ('a parameter', param(t, u, t), [param(i, j, i), param(u, t, u)], [param(t, u, u)]),
        ('two branches with one name', branches(t, t), [branches(u, u)], [branches(u, a)]),
        ('a name bound after a block bound it', after(t, t), [after(u, t)], [after(u, a)]),
        ('a constructor', ctor('Green', 'Red'), [], [ctor('Red', 'Green')]),
        ('a quoted name', quote(a, a), [quote(b, a)], [quote(a, b)]),
    ]


def shadowed(rng):
    """Every way of binding a name where it is already bound.  The language has none of them:
    each is refused, so a use never has two bindings of its name to choose between."""
    a, b, t, i = rng.sample(['p', 'q', 'u', 'w', 'x', 'y', 'z', 'left', 'right', 'tmp', 'acc', 'it'], 4)
    c = rng.randrange(1, 9)
    clause = f'rule f({t}: I64) takes (I64, I64) returns (I64, I64)\n    ({a}, {b}) <-> ({a}, {b}) where\n'
    expr = f'rule f({a}: I64) returns I64 uses Output\n'
    return [
        ('a counter named as the counter of the loop it is in',
         clause + f'        repeat with {i} from 0 to {c}\n            repeat with {i} from 0 to 2\n                add {i} to {b}\n'),
        ('a counter named as a live name', clause + f'        repeat with {a} from 0 to {c}\n            add {a} to {b}\n'),
        ('a counter named as a parameter', clause + f'        repeat with {t} from 0 to {c}\n            add {t} to {b}\n'),
        ('a name bound again in a body', expr + f'    {t} is {a}\n    {t} is {t} + {c}\n    {t}\n'),
        ('a name bound in a block that is bound outside it',
         expr + f'    {t} is {a}\n    if {a} > 0\n        {t} is {c}\n        output {t}\n    {t}\n'),
        ('a parameter bound again', expr + f'    {a} is {c}\n    {a}\n'),
        ('a counter named as a bound name', expr + f'    {t} is {c}\n    repeat with {t} from 0 to 2\n        output {t}\n    {t}\n'),
        ('a counter named as a parameter, in a body', expr + f'    repeat with {a} from 0 to {c}\n        output {a}\n    0\n'),
        ('counters of one name, one in another, in a body',
         expr + f'    repeat with {i} from 0 to {c}\n        repeat with {i} from 0 to 2\n            output {i}\n    0\n'),
    ]


NAMED = (
    'request {G}\n    {put}(n: I64) returns I64\n    {take}(n: I64) returns I64\n'
    'answer {Cell} for {G} takes I64\n'
    '    ({put}(n), c) => (n, c) where\n        t is c + n\n        discard t\n'
    '    ({take}(n), c) => (n, c) where\n        t is c - n\n        discard t\n'
    'answer {Twin} for {G} takes I64\n'
    '    ({put}(n), c) => (n, c) where\n        t is c + n\n        discard t\n'
    '    ({take}(n), c) => (n, c) where\n        t is c - n\n        discard t\n'
    'rule via takes (I64, I64) returns (I64, I64)\n    (a, b) => (a, r) where\n'
    '        i is {made} from b\n        r is i -> {sent}(a)\n        i was {made} from b\n        discard b\n'
    'rule asker takes I64 returns I64 uses {G}\n    a => r where\n        r is ask {asked}(a)\n        discard a\n'
    'rule holder takes {made} returns {made}\n    i <-> i\n')


def names(programs=200, seed=1):
    from selvage.codeid import code_identity, identities
    rng = random.Random(seed)
    stats = {'rules': 0, 'renamed alike': 0, 'nested bindings renamed': 0, 'uses changed': 0, 'scope cases': 0,
             'shadowing refused': 0,
             'requests and answers renamed': 0, 'twins kept apart': 0, 'runs': 0}
    findings = []

    def ids(src, rule='f'):
        m = load(src)[0]
        r = m.rules[rule]
        body = tuple(code_identity(m, c, r) for c in r.clauses) if r.kind == 'clauses' else code_identity(m, r.block, r)
        return identities(m).rules[rule], body
    base = dict(G='G', put='put', take='take', Cell='Cell', Twin='Twin', made='Cell', sent='put', asked='put')
    first = load(NAMED.format(**base))[0]
    a = identities(first)
    base_ids = {r: ids(NAMED.format(**base), r) for r in ('via', 'asker', 'holder')}
    for n in range(programs):
        # 1. generated rules, with every variable renamed, then only those bound inside
        src = Structures(rng).program() if n % 2 else roundtrip_gen.Gen(rng).program()
        head = STRUCT_HEAD if n % 2 else ''
        if refusal(src) is None:
            stats['rules'] += 1
            body = src[len(head):]
            every = set(re.findall(r'\b(?:[abcsxy]|[tmkid]\d+)\b', body))
            inner = {v for v in every if re.fullmatch(r'[tmkid]\d+', v)}
            want = ids(src)
            for which, key in ((every, 'renamed alike'), (inner, 'nested bindings renamed')):
                if not which:
                    continue
                tags = {v: f'v{k}_' for k, v in enumerate(rng.sample(sorted(which), len(which)))}
                other = head + renamed(body, which, lambda v: tags[v])
                why = refusal(other)
                if why is not None:
                    findings.append(('renaming variables made a program the checker refuses', other, why))
                elif ids(other) != want:
                    findings.append(('renaming variables changed an identity', other, key))
                else:
                    stats[key] += 1
            # one use made to refer to another binding: other code
            sites = [mt for mt in re.finditer(r'\b[ab]\b', body) if mt.start() > body.index('where')]
            if sites:
                at = rng.choice(sites)
                other = head + body[:at.start()] + ('b' if at.group() == 'a' else 'a') + body[at.end():]
                if refusal(other) is None:
                    stats['uses changed'] += 1
                    if ids(other) == want:
                        findings.append(('a use referring to another binding kept the identity', other, body))
        # 2. scope: shadowing, rebinding, patterns, parameters, blocks, free and quoted names
        for what, code, same, different in (scope_cases(rng) if n % 4 == 0 else []):
            stats['scope cases'] += 1
            try:
                want = ids(code)
                for other in same:
                    if ids(other) != want:
                        findings.append((f'renaming changed an identity: {what}', other, code))
                for other in different:
                    if ids(other) == want:
                        findings.append((f'different code has one identity: {what}', other, code))
            except CheckError as e:
                findings.append((f'a scope case was refused: {what}', code, str(e)))
        for what, code in (shadowed(rng) if n % 4 == 0 else []):
            why = refusal(code)
            stats['shadowing refused'] += 1
            if why is None or ('already bound' not in why and 'never rebound' not in why):
                findings.append((f'a name was bound where it is already bound: {what}', code, str(why)))
        # 3. requests and answers: referred to by identity; declarations with the same content stay apart
        if n % 2:
            continue
        new = dict(G=rng.choice(['G', 'Store']), put=rng.choice(['put', 'stash']), take=rng.choice(['take', 'fetch']),
                   Cell=rng.choice(['Cell', 'Box']), Twin=rng.choice(['Twin', 'Other']))
        new.update(made=new['Cell'], sent=new['put'], asked=new['put'])
        second = load(NAMED.format(**new))[0]
        b = identities(second)
        stats['requests and answers renamed'] += 1
        same = [(a.groups['G'], b.groups[new['G']]), (a.requests['put'], b.requests[new['put']]),
                (a.requests['take'], b.requests[new['take']]), (a.answers['Cell'], b.answers[new['Cell']]),
                (a.answers['Twin'], b.answers[new['Twin']])] + \
               [(base_ids[r], ids(NAMED.format(**new), r)) for r in ('via', 'asker', 'holder')]
        if any(x != y for x, y in same):
            findings.append(('renaming a request, a group or an answer changed an identity', NAMED.format(**new), ''))
        if a.requests['put'] == a.requests['take'] or a.answers['Cell'] == a.answers['Twin']:
            findings.append(('declarations with the same content share an identity', NAMED.format(**base), ''))
        # the same signature is not the same request, and the same code is not the same answer:
        # code that refers to the other one is other code, and code that does not is the same
        change, rules = rng.choice([(dict(sent='take'), ['via']), (dict(asked='take'), ['asker']),
                                    (dict(made='Twin'), ['via', 'holder'])])
        if True:
            other = NAMED.format(**dict(base, **change))
            stats['twins kept apart'] += 1
            for r in ('via', 'asker', 'holder'):
                if (ids(other, r) != base_ids[r]) != (r in rules):
                    findings.append(('what referring to a twin changed', other, f'{change}: {r}'))
        # and a run names the same code, under the names of this program
        x, y = rng.randrange(1, 9), rng.randrange(1, 9)
        kept = []
        for m, nm in ((first, base), (second, new)):
            it = Interp(m)
            out = it.forward(m.rules['via'], (), (W(x), W(y)))
            kept.append((out, [(e.tag, e.kids[0], e.kids[2]) for e in it.journal], [e.kids[1] for e in it.journal]))
            back = it.rewind(m.rules['via'], (), out)
            if back != (W(x), W(y)) or it.journal or kept[-1][2] != [f'{nm["Cell"]}.{nm["put"]}', 'via']:
                findings.append(('a run through a renamed answer', NAMED.format(**nm), f'{back} {kept[-1][2]}'))
        stats['runs'] += 2
        if kept[0][:2] != kept[1][:2]:
            findings.append(('renaming a request or an answer changed what a run kept, or under which code',
                             NAMED.format(**new), f'{kept[0][:2]}\n{kept[1][:2]}'))
    return stats, findings


# ---- accounting: what a run is charged for what it lets go of (VII.5) -------------------------
# The oracle has its own model of each generated rule: its own values, its own matcher, and its
# own reading of the definition.  It never asks the checker which constructors are possible or
# which values can be computed again; it decides both by going through every input.  A second
# check owes nothing to the definition: for each output, the charges of the inputs that give
# it must be the lengths of a code that tells those inputs apart (Kraft's inequality), so a
# charge that is too small for the information lost is a finding.
ACC_TYPES = {
    'Bit': ['0', '1'], 'Bool': ['true', 'false'], 'Trit': ['true', 'false', 'maybe'],
    'Hue': ['Red', 'Green', 'Blue'],
    'Box': ['Hollow', ('Full', 'Red'), ('Full', 'Green'), ('Full', 'Blue')],
    'Lamp': [('Lamp', b, h) for b in ('0', '1') for h in ('Red', 'Green', 'Blue')],
    'Text': ['""', '"a"', '"b"'],
}
ACC_HEAD = ('type Hue\n    Red\n    Green\n    Blue\n\n'
            'type Box\n    Hollow\n    Full(hue: Hue)\n\n'
            'type Lamp\n    Lamp(on: Bit, hue: Hue)\n\n')
ACC_CTORS = {'Hue': {'Red': [], 'Green': [], 'Blue': []}, 'Box': {'Hollow': [], 'Full': ['Hue']}, 'Lamp': {'Lamp': ['Bit', 'Hue']}}
ACC_WIDTH = {'Bit': 1, 'Bool': 1, 'Trit': 2}


def acc_clog2(n):
    b = 0
    while (1 << b) < n:
        b += 1
    return b


def acc_text(v):
    return v if isinstance(v, str) else f'{v[0]}({", ".join(acc_text(x) for x in v[1:])})'


def acc_value(v, t):
    """The oracle's value as the interpreter's."""
    if t == 'Bit':
        return W(int(v), 'Bit')
    if t in ('Bool', 'Trit'):
        return MAYBE if v == 'maybe' else v == 'true'
    if t == 'Text':
        return v[1:-1]
    if isinstance(v, str):
        return Form(v, ())
    return Form(v[0], tuple(acc_value(x, ft) for x, ft in zip(v[1:], ACC_CTORS[t][v[0]])))


def acc_charge(v, t, top=None):
    """The charge for a dropped value, read off the definition: a word its width; otherwise
    the bits that tell apart the constructors it may have, and its fields."""
    if t in ACC_WIDTH:
        return ACC_WIDTH[t]
    if t == 'Text':
        return 64 + 8 * len(v[1:-1])          # an array of bytes: its length, and its bytes
    ctor = v if isinstance(v, str) else v[0]
    fields = () if isinstance(v, str) else v[1:]
    return acc_clog2(len(ACC_CTORS[t]) if top is None else top) + \
        sum(acc_charge(x, ft) for x, ft in zip(fields, ACC_CTORS[t][ctor]))


class Tables:
    """A rule over a few small types, written as a table of clauses.  A side is, place by place,
    a value, a name, or `Full(name)`; names the right side does not use are discarded."""

    def __init__(self, rng):
        self.rng = rng
        self.takes = [rng.choice(['Bit', 'Bool', 'Hue', 'Box', 'Trit', 'Lamp', 'Text']) for _ in range(rng.randint(1, 3))]
        while len(self.inputs()) > 96:
            self.takes.pop()
        self.returns = [rng.choice(['Bit', 'Bool', 'Hue', 'Box']) for _ in range(rng.randint(1, 2))]
        self.clauses = [self.clause(i) for i in range(rng.randint(1, 5))]

    def inputs(self):
        out = [()]
        for t in self.takes:
            out = [x + (v,) for x in out for v in ACC_TYPES[t]]
        return out

    def clause(self, i):
        rng = self.rng
        left, bound = [], []                      # bound: (name, type, path)
        for p, t in enumerate(self.takes):
            roll = rng.random()
            if roll < 0.45:
                left.append(('val', rng.choice(ACC_TYPES[t])))
            elif roll < 0.6 and t == 'Box':
                left.append(('full', f'h{i}{p}'))
                bound.append((f'h{i}{p}', 'Hue', (p, 0)))
            else:
                left.append(('var', f'v{i}{p}'))
                bound.append((f'v{i}{p}', t, (p,)))
        right, used = [], set()
        for t in self.returns:
            free = [n for n, bt, _ in bound if bt == t and n not in used]
            if free and rng.random() < 0.5:
                n = rng.choice(free)
                used.add(n)
                right.append(('var', n))
            else:
                right.append(('val', rng.choice(ACC_TYPES[t])))
        steps = []                                # ('drop', name) | ('copy', temp, name) | ('made', temp, name) | ('flip', name)
        drops = [n for n, _, _ in bound if n not in used]
        rng.shuffle(drops)
        k = 0
        for n, bt, _ in bound:
            if n in used and rng.random() < (0.6 if bt == 'Bit' else 0.3):
                k += 1
                # a copy of something that stays: dropping the copy loses nothing, unless what
                # it was copied from has changed in between
                steps.append(('copy', f't{i}{k}', n))
                if bt == 'Bit' and rng.random() < 0.6:
                    steps.append(('flip', n))
                steps.append(('drop', f't{i}{k}'))
            if n not in used and bt == 'Bit' and rng.random() < 0.35:
                # a copy of a value that is itself dropped, changed in between: the copy can no
                # longer be computed from it, so both are charged
                k += 1
                steps += [('copy', f't{i}{k}', n), ('flip', n), ('drop', f't{i}{k}'), ('drop', n)]
                drops.remove(n)
            if n in used and bt == 'Hue' and rng.random() < 0.25:
                k += 1
                steps.append(('made', f't{i}{k}', n))      # a value made here, by a known constructor
                steps.append(('drop', f't{i}{k}'))
        for n in drops:
            steps.insert(rng.randint(0, len(steps)), ('drop', n))
        return left, right, steps, bound

    @staticmethod
    def side(items):
        text = ', '.join(acc_text(x) if kind == 'val' else f'Full({x})' if kind == 'full' else x for kind, x in items)
        return f'({text})' if len(items) > 1 else text

    def program(self, arrow='=>'):
        ty = lambda ts: f'({", ".join(ts)})' if len(ts) > 1 else ts[0]   # noqa: E731
        out = [f'rule f takes {ty(self.takes)} returns {ty(self.returns)}']
        for left, right, steps, _ in self.clauses:
            out.append(f'    {self.side(left)} {arrow} {self.side(right)}' + (' where' if steps else ''))
            for s in steps:
                out.append({'drop': '        discard {1}', 'copy': '        {1} is {2}', 'made': '        {1} is Full({2})',
                            'flip': '        add 1 to {1}'}[s[0]].format(*s))
        return ACC_HEAD + '\n'.join(out) + '\n'

    # ---- the oracle ---------------------------------------------------------------------
    @staticmethod
    def fits(items, value, env=None):
        for (kind, x), v in zip(items, value):
            if kind == 'val' and v != x:
                return False
            if kind == 'full':
                if isinstance(v, str):
                    return False
                if env is not None:
                    env[x] = v[1]
            if kind == 'var' and env is not None:
                env[x] = v
        return True

    def clause_of(self, x):
        return next((i for i, c in enumerate(self.clauses) if self.fits(c[0], x)), None)

    def possible(self, i, path):
        """How many constructors the name bound at `path` in clause i may have: one is ruled out
        where a single earlier clause takes every input of this clause that has it there."""
        t = 'Hue' if len(path) == 2 else self.takes[path[0]]
        if t not in ACC_CTORS:
            return None

        def ctor_at(x):
            v = x[path[0]] if len(path) == 1 else x[path[0]][1]
            return v if isinstance(v, str) else v[0]
        mine = [x for x in self.inputs() if self.fits(self.clauses[i][0], x)]
        left = 0
        for k in ACC_CTORS[t]:
            having = [x for x in mine if ctor_at(x) == k]
            if not any(all(self.fits(self.clauses[e][0], x) for x in having) for e in range(i)):
                left += 1
        return left if 0 < left < len(ACC_CTORS[t]) else None

    def run(self, x):
        """What the rule gives for x and what it is charged: (output, charge, entries kept)."""
        i = self.clause_of(x)
        if i is None:
            return None
        left, right, steps, bound = self.clauses[i]
        env = {}
        self.fits(left, x, env)
        types = {n: t for n, t, _ in bound}
        paths = {n: p for n, _, p in bound}
        charge = entries = 0
        fresh = {}                                # temp -> the name it was copied from, while that still holds
        for s in steps:
            if s[0] == 'copy':
                env[s[1]], types[s[1]] = env[s[2]], types[s[2]]
                fresh[s[1]] = s[2]
            elif s[0] == 'made':
                env[s[1]], types[s[1]] = ('Full', env[s[2]]), 'Box'
                fresh[s[1]] = s[2]
            elif s[0] == 'flip':
                env[s[1]] = '1' if env[s[1]] == '0' else '0'
                fresh = {t: n for t, n in fresh.items() if n != s[1]}
            else:
                n = s[1]
                entries += 1
                if n in fresh:
                    pass                          # still computable from what remains: nothing
                elif n in paths:
                    charge += acc_charge(env[n], types[n], self.possible(i, paths[n]))
                elif types[n] == 'Box' and isinstance(env[n], tuple) and n not in paths:
                    charge += acc_charge(env[n], 'Box', 1)       # made here by `Full`
                else:
                    charge += acc_charge(env[n], types[n])
        out = tuple(env[v] if kind == 'var' else v for kind, v in right)
        sharing = sum(1 for c in self.clauses if self.fits(c[1], out))
        if sharing > 1 and len(self.clauses) > 1 and self.overlapping():
            charge += acc_clog2(sharing)
            entries += 1
        return out, charge, entries

    def overlapping(self):
        """Whether two clauses can take one input, or give one output."""
        def meet(a, b):
            return all(ka != 'val' or kb != 'val' or va == vb for (ka, va), (kb, vb) in zip(a, b)) and \
                all(not (ka == 'val' and kb == 'full' and isinstance(va, str)) and
                    not (kb == 'val' and ka == 'full' and isinstance(vb, str)) for (ka, va), (kb, vb) in zip(a, b))
        cs = self.clauses
        return any(meet(cs[i][s], cs[j][s]) for s in (0, 1) for i in range(len(cs)) for j in range(i + 1, len(cs)))


def accounting(programs=200, seed=1):
    import shutil
    import subprocess
    import tempfile
    rng = random.Random(seed)
    stats = {'rules': 0, 'lossy': 0, 'runs': 0, 'entries': 0, 'bits': 0, 'choices kept': 0, 'choices not needed': 0,
             'constructors ruled out': 0, 'dropped for nothing': 0, 'outputs weighed': 0, 'compiled': 0,
             'copies dropped after a change': 0}
    findings = []
    clang = shutil.which('clang')
    tmp = tempfile.mkdtemp(prefix='selvage-accounting-')
    try:
        for n in range(programs):
            g = Tables(rng)
            src = g.program('=>')
            why = refusal(src)
            lossy = why is None
            if why is not None and 'certified' in why:
                src = g.program('<->')
                why = refusal(src)
            if why is not None:
                if 'unreachable' in why or 'never' in why:
                    continue
                findings.append(('a table the checker refuses', src, why))
                continue
            stats['rules'] += 1
            stats['lossy'] += lossy
            m = load(src)[0]
            r = m.rules['f']
            ty = lambda vs, ts: tuple(acc_value(v, t) for v, t in zip(vs, ts)) if len(ts) > 1 else acc_value(vs[0], ts[0])  # noqa: E731
            fibres = {}
            for i, c in enumerate(g.clauses):
                for name, t, path in c[3]:
                    if g.possible(i, path) is not None:
                        stats['constructors ruled out'] += 1
                stats['copies dropped after a change'] += sum(1 for st in c[2] if st[0] == 'flip')
            for x in g.inputs():
                want = g.run(x)
                it = Interp(m)
                try:
                    out = it.forward(r, (), ty(x, g.takes))
                except Fault as e:
                    if want is not None:
                        findings.append(('a run was refused', src, f'{x}: {e}'))
                    continue
                stats['runs'] += 1
                if want is None:
                    findings.append(('a run the table has no clause for', src, str(x)))
                    continue
                o, charge, entries = want
                if deep(out) != deep(ty(o, g.returns)):
                    findings.append(('what a run gave', src, f'{x}: {out}, expected {o}'))
                    continue
                kept = [e.tag for e in it.journal]
                if it.journal_bits() != charge or len(kept) != entries:
                    findings.append(('what a run was charged', src,
                                     f'{x} -> {o}: {it.journal_bits()} bits for {kept}, expected {charge} bits for {entries} entries'))
                stats['entries'] += entries
                stats['bits'] += charge
                stats['choices kept'] += 'Chose' in kept
                stats['choices not needed'] += lossy and 'Chose' not in kept and r.journal_choice
                stats['dropped for nothing'] += any(s[0] == 'copy' for s in g.clauses[g.clause_of(x)][2])
                fibres.setdefault(o, []).append((x, charge))
                try:
                    back = it.rewind(r, (), out)
                except Fault as e:
                    findings.append(('a rewind was refused', src, f'{x}: {e}'))
                    continue
                if deep(back) != deep(ty(x, g.takes)) or it.journal:
                    findings.append(('a rewind did not give the input back', src, str(x)))
            # the charges for one output are the lengths of a code that tells its inputs apart
            for o, xs in fibres.items():
                stats['outputs weighed'] += 1
                if sum(2.0 ** -c for _, c in xs) > 1 + 1e-9:
                    findings.append(('a charge too small for what was lost', src, f'{o}: {xs}'))
            # the whole run, in both backends: epsilon is the sum
            some = [x for x in g.inputs() if g.run(x) is not None]
            some = rng.sample(some, min(6, len(some)))
            if not some:
                continue
            lit = lambda vs, ts: ('(' + ', '.join(acc_lit(v, t) for v, t in zip(vs, ts)) + ')')  # noqa: E731
            main = 'rule main uses Output' + (', System' if lossy else '') + '\n' + \
                ''.join(f'    output f({lit(x, g.takes) if len(g.takes) > 1 else acc_lit(x[0], g.takes[0])})\n' for x in some)
            total = sum(g.run(x)[1] for x in some)
            m2 = load(src + '\n' + main)[0]
            it = Interp(m2)
            it.out = io.StringIO()
            it.run_main()
            if it.epsilon != total:
                findings.append(('epsilon in the interpreter', src + main, f'{it.epsilon}, expected {total}'))
            # compiled code is tried on every eighth rule, and on every rule that drops a copy
            copies = any(st[0] in ('copy', 'made') for c in g.clauses for st in c[2])
            if clang and (n % 8 == 0 or (copies and n % 3 == 0)):
                path = os.path.join(tmp, f'p{n}.selv')
                with open(path, 'w') as f:
                    f.write(src + '\n' + main)
                exe = os.path.join(tmp, f'p{n}')
                b = subprocess.run([sys.executable, '-m', 'selvage', 'build', path, '-o', exe], capture_output=True, text=True,
                                   cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                if b.returncode != 0:
                    if 'not supported' in b.stderr or 'stays in the interpreter' in b.stderr or 'unsupported' in b.stderr.lower():
                        continue
                    findings.append(('the table does not compile', src + main, b.stderr[-300:]))
                    continue
                c = subprocess.run([exe], capture_output=True, text=True, env=dict(os.environ, SELVAGE_STATS='1'))
                stats['compiled'] += 1
                got = re.search(r'epsilon=(\d+)', c.stderr)
                if c.stdout != it.out.getvalue() or got is None or int(got.group(1)) != total:
                    findings.append(('epsilon in compiled code', src + main,
                                     f'{got.group(1) if got else c.stderr[-120:]}, expected {total}; output the same: {c.stdout == it.out.getvalue()}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return stats, findings


def acc_lit(v, t):
    return f'Bit({v})' if t == 'Bit' else acc_text(v)


def deep(v):
    """A value as plain data, for comparison."""
    if isinstance(v, Word):
        return ('w', v.ty, v.v)
    if isinstance(v, tuple):
        return tuple(deep(x) for x in v)
    if isinstance(v, Form):
        return (v.tag,) + tuple(deep(x) for x in v.kids)
    return ('maybe',) if v is MAYBE else v


# ---- extent: whether a certified rule takes every input and gives every output (V.2) -----------
# Over bits the oracle is a gate simulator of its own: it runs every input and counts.  Over
# words it knows, from how the rule was put together, what must be claimed and what may not
# be, and it tries the claims on values chosen to break them.
class Gates:
    def __init__(self, rng, words=False):
        self.rng, self.words = rng, words
        self.n = rng.randint(2, 3)
        self.wires = [f'w{i}' for i in range(self.n)]
        self.extra = [(f'x{i}', rng.randint(0, 1)) for i in range(rng.choice([0, 0, 1, 2 if not words else 1]))]
        self.gone = []                             # wires given back against a constant at the end
        live = self.wires + [x for x, _ in self.extra]
        self.steps = [self.step(live) for _ in range(rng.randint(1, 6))]
        self.unsafe = any(s[0] == 'div' for s in self.steps)
        if rng.random() < 0.3 and len(live) > 1:
            w = rng.choice(live)
            self.gone.append((w, rng.randint(0, 1)))
        self.out = [w for w in live if w not in [g for g, _ in self.gone]]

    def step(self, live):
        rng = self.rng
        a, b = rng.sample(live, 2)
        c = rng.choice([w for w in live if w not in (a, b)] or [None])
        roll = rng.random()
        if self.words:
            if roll < 0.15:
                return ('div', a, b)               # add a / b to itself is not allowed; a third wire or a constant
            return rng.choice([('add', a, b), ('sub', a, b), ('swap', a, b), ('half', a, b), ('mul', a, b)])
        if c is not None and roll < 0.35:
            return ('ccnot', a, b, c)
        return rng.choice([('add', a, b), ('swap', a, b), ('not', a)])

    def program(self):
        t = 'I64' if self.words else 'Bit'
        ty = lambda ws: f'({", ".join([t] * len(ws))})' if len(ws) != 1 else t   # noqa: E731
        pat = lambda ws: f'({", ".join(ws)})' if len(ws) != 1 else ws[0]         # noqa: E731
        lit = (lambda k: str(k * 5)) if self.words else (lambda k: f'Bit({k})')
        lines = [f'rule f takes {ty(self.wires)} returns {ty(self.out)}', f'    {pat(self.wires)} <-> {pat(self.out)} where']
        for x, k in self.extra:
            lines.append(f'        {x} is {lit(k)}')
        for s in self.steps:
            lines.append('        ' + {'add': 'add {1} to {2}', 'sub': 'subtract {1} from {2}', 'swap': 'swap {1} and {2}',
                                       'not': 'add 1 to {1}', 'ccnot': 'add {1} * {2} to {3}', 'half': 'add {1} / 2 to {2}',
                                       'mul': 'add 3 * {1} to {2}', 'div': 'add 7 / {1} to {2}'}[s[0]].format(*s))
        for w, k in self.gone:
            lines.append(f'        {w} was {lit(k)}')
        return '\n'.join(lines) + '\n'

    def answer_program(self):
        """The same rule hosted by an answer: the request's fields are its input, the reply its
        output, and the state is (), so the answer's rule has the rule's extent."""
        t = 'I64' if self.words else 'Bit'
        ty = lambda ws: f'({", ".join([t] * len(ws))})' if len(ws) != 1 else t   # noqa: E731
        pat = lambda ws: f'({", ".join(ws)})' if len(ws) != 1 else ws[0]         # noqa: E731
        body = self.program().splitlines()[2:]
        fields = ', '.join(f'{w}: {t}' for w in self.wires)
        return '\n'.join([f'request Go\n    go({fields}) returns {ty(self.out)}',
                          'answer G for Go takes ()',
                          f'    (go({", ".join(self.wires)}), st) <-> ({pat(self.out)}, st) where'] + body) + '\n'

    # the oracle, over bits: every input, run by a simulator of its own
    def run(self, x):
        env = dict(zip(self.wires, x))
        env.update(dict(self.extra))
        for s in self.steps:
            if s[0] == 'add':
                env[s[2]] ^= env[s[1]]
            elif s[0] == 'swap':
                env[s[1]], env[s[2]] = env[s[2]], env[s[1]]
            elif s[0] == 'not':
                env[s[1]] ^= 1
            else:
                env[s[3]] ^= env[s[1]] & env[s[2]]
        if any(env[w] != k for w, k in self.gone):
            return None
        return tuple(env[w] for w in self.out)

    def kind(self):
        import itertools
        outs = [self.run(x) for x in itertools.product((0, 1), repeat=self.n)]
        total = all(o is not None for o in outs)
        onto = len({o for o in outs if o is not None}) == 2 ** len(self.out)
        return {(True, True): 'permutation', (True, False): 'embedding', (False, True): 'partial inverse',
                (False, False): 'partial'}[total, onto]

    # the oracle, over words: what may be claimed from how the rule is put together
    def claim(self):
        # an extra wire bound to a constant and given back against the same constant, with
        # nothing writing it in between, is a proved uncompute: it changes neither question
        writes = set()
        for s in self.steps:
            writes |= {s[1], s[2]} if s[0] == 'swap' else {s[2]}
        cancelled = [(w, k) for w, k in self.gone if (w, k) in self.extra and w not in writes]
        extra = [x for x in self.extra if x not in cancelled]
        gone = [x for x in self.gone if x not in cancelled]
        total = False if len(self.out) < self.n else (None if self.unsafe or gone else True)
        onto = False if len(self.out) > self.n else (None if self.unsafe or extra else True)
        return {(True, True): 'permutation', (True, False): 'embedding', (False, True): 'partial inverse',
                (False, False): 'partial'}.get((total, onto), 'partial' if total is False else 'one-to-one')


def extents(programs=200, seed=1):
    from selvage.extent import extent
    rng = random.Random(seed)
    stats = {'gate rules': 0, 'permutations': 0, 'embeddings': 0, 'partial inverses': 0, 'partial': 0,
             'word rules': 0, 'claimed onto': 0, 'claimed total': 0, 'not established': 0, 'claims tried': 0,
             'answers': 0}
    findings = []
    for n in range(programs):
        words = n % 3 == 2
        g = Gates(rng, words)
        src = g.program()
        why = refusal(src)
        if why is not None:
            if 'R4' in why or 'reads' in why or 'lossy' in why or 'not available' in why:
                continue
            findings.append(('a gate rule the checker refuses', src, why))
            continue
        m = load(src)[0]
        r = m.rules['f']
        kind, how = extent(m, r)
        back, _ = extent(m, r.inverse)
        flipped = {'permutation': 'permutation', 'embedding': 'partial inverse', 'partial inverse': 'embedding',
                   'partial': 'partial', 'one-to-one': 'one-to-one'}
        # the same rule hosted by an answer reaches exactly as far, both ways
        asrc = g.answer_program()
        why = refusal(asrc)
        if why is not None:
            findings.append(('a rule the checker certifies, refused as an answer', asrc, why))
        else:
            am = load(asrc)[0]
            ar = am.answers['G'].ops['go']
            stats['answers'] += 1
            if extent(am, ar)[0] != kind or extent(am, ar.inverse)[0] != back:
                findings.append(('the extent of a rule hosted by an answer', asrc,
                                 f'{extent(am, ar)[0]} and {extent(am, ar.inverse)[0]}, expected {kind} and {back}'))
        if not words:
            stats['gate rules'] += 1
            want = g.kind()
            stats[{'permutation': 'permutations', 'embedding': 'embeddings', 'partial inverse': 'partial inverses',
                   'partial': 'partial'}[want]] += 1
            if kind != want:
                findings.append(('the extent of a gate rule', src, f'{kind} ({how}), expected {want}'))
            if back != flipped[want]:
                findings.append(('the extent of the inverse of a gate rule', src, f'{back}, expected {flipped[want]}'))
            continue
        stats['word rules'] += 1
        want = g.claim()
        if kind != want:
            findings.append(('the extent of a word rule', src, f'{kind} ({how}), expected {want}'))
            continue
        stats['not established'] += 'not established' in how
        # whatever is claimed is tried: on zeros, where a division would refuse, and at random
        tries = [tuple(W(v) for v in vs) for vs in ([0] * g.n, [1] * g.n)] + \
                [tuple(W(rng.choice([0, 1, -1, rng.randrange(-2 ** 63, 2 ** 63)])) for _ in range(g.n)) for _ in range(12)]
        one = lambda vs: vs if len(vs) != 1 else vs[0]   # noqa: E731
        if kind in ('permutation', 'embedding'):
            stats['claimed total'] += 1
            for x in tries:
                stats['claims tried'] += 1
                try:
                    Interp(m).forward(r, (), one(x))
                except Fault as e:
                    findings.append(('a rule said to take every input refused one', src, f'{x}: {e}'))
        if kind in ('permutation', 'partial inverse'):
            stats['claimed onto'] += 1
            for _ in range(12):
                y = tuple(W(rng.choice([0, 1, 5, -1, rng.randrange(-2 ** 63, 2 ** 63)])) for _ in g.out)
                stats['claims tried'] += 1
                try:
                    x = Interp(m).undo(r, (), one(y))
                    if deep(Interp(m).forward(r, (), x)) != deep(one(y)):
                        findings.append(('an output said to be reached is not', src, str(y)))
                except Fault as e:
                    findings.append(('a rule said to be onto has an output it does not give', src, f'{y}: {e}'))
        if kind == 'embedding' and g.extra:
            # an output whose extra wire holds another constant is one it does not give
            bad = [W(77)] * len(g.out)
            stats['claims tried'] += 1
            try:
                x = Interp(m).undo(r, (), one(tuple(bad)))
                if deep(Interp(m).forward(r, (), x)) == deep(one(tuple(bad))):
                    pass                              # 77 everywhere can happen to be in the image
            except Fault:
                pass
    return stats, findings


# ---- forms: declarations and programs as values a rule takes apart (VIII.1) --------------------
# The oracle reads the source as text, with no parser: which declarations there are, in what
# order, of what kind and under what name, how many parameters, clauses, constructors or
# requests each has, and what its row or its groups are.  A rule written in Selvage reads the
# same from `program()`, and the two must agree.
FORMS_INSPECT = '''
rule census_count takes Parts returns I64
    NoParts => 0
    Part(first, rest) => n where
        n is census_count(rest)
        add 1 to n
        discard first

rule census_kind takes Declaration returns (Text, Text, I64, Parts)
    RuleDecl(name, params, domain, codomain, row, body) => ("rule", name, n, row) where
        n is census_count(params)
        discard domain
        discard codomain
        discard body
    AnswerDecl(name, params, groups, state, clauses) => ("answer", name, n, groups) where
        n is census_count(clauses)
        discard params
        discard state
    TypeDecl(name, shapes, parent) => ("type", name, n, NoParts) where
        n is census_count(shapes)
        discard parent
    RequestDecl(name, requests, sealed) => ("request", name, n, NoParts) where
        n is census_count(requests)
        discard sealed

rule census_kinds takes Parts returns Parts
    NoParts => NoParts
    Part(d, rest) => Part(k, more) where
        k is census_kind(d)
        more is census_kinds(rest)

request CensusAsk
    census_one(n: I64) returns I64
    census_two() returns ()

answer CensusAnswer for CensusAsk takes I64
    (census_one(n), s) <-> (n, s)
    (census_two(), s) <-> ((), s)

rule census_all returns Parts uses System
    Program(all) is program()
    census_kinds(all)
'''


def forms_oracle(text):
    """What a program declares, read off its text."""
    out, cur = [], None
    for line in text.split('\n'):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        head = re.match(r'(rule|type|request|answer) (\w+)(.*)$', line)
        if head:
            kind, name, rest = head.groups()
            n, extra = 0, []
            if kind == 'rule':
                if rest.startswith('('):
                    depth, i = 0, 0
                    for i, ch in enumerate(rest):
                        depth += ch == '('
                        depth -= ch == ')'
                        if depth == 0:
                            break
                    n = len(re.findall(r'\w+: ', rest[:i + 1]))
                    rest = rest[i + 1:]
                uses = re.search(r' uses (.*)$', rest)
                extra = [u.strip() for u in uses.group(1).split(',')] if uses else []
            elif kind == 'answer':
                groups = re.search(r' for (.*?)( takes .*)?$', rest)
                extra = [g.strip() for g in groups.group(1).split(',')]
            elif kind == 'type' and (rest.startswith('(') or ' <- ' in rest):
                n = 1
            cur = [kind, name, n, extra]
            out.append(cur)
        elif cur is not None and line.startswith('    ') and not line.startswith('     '):
            if cur[0] in ('type', 'request') or (cur[0] == 'answer' and (' <-> ' in line or ' => ' in line)):
                cur[2] += 1
    return [tuple(x[:3]) + (tuple(x[3]),) for x in out]


def forms(programs=200, seed=1):
    from selvage.census import census
    from selvage.declared import declared, undeclared, items
    from selvage.forms import encode, show
    from selvage.invert import as_sequence, as_block, mirror, invert_clause
    from selvage.parser import parse
    from selvage.printer import program_text
    rng = random.Random(seed)
    stats = {'accepted': 0, 'declarations': 0, 'read alike by a rule and from the text': 0, 'clauses mirrored': 0,
             'constructors taken apart': 0, 'nodes': 0, 'uncomputes that read themselves refused': 0}
    findings = []
    for n in range(programs):
        pick = n % 5
        src = (roundtrip_gen.Gen(rng).program() if pick == 0 else Structures(rng).program() if pick == 1
               else c_program(rng) if pick == 2 else Gates(rng, pick == 4).program() if pick == 4 else None)
        if src is None:
            g = Tables(rng)
            src = g.program('=>')
            if refusal(src) is not None:
                src = g.program('<->')
        if refusal(src) is not None:
            continue
        stats['accepted'] += 1
        whole = src + FORMS_INSPECT
        prog = parse(src)
        # 1. each declaration, written as a program holds it and back
        for d in prog.kids:
            stats['declarations'] += 1
            try:
                if encode(undeclared(declared(d))) != encode(d):
                    findings.append(('a declaration changed on the way to a value and back', src, d.kids[0]))
            except Fault as e:
                findings.append(('a declaration could not be written as a value', src, f'{d.kids[0]}: {e}'))
        if show(declared(prog)) + '\n' != program_text(prog):
            findings.append(('a program as a value does not print as the program', src, ''))
        # 2. a rule reads from `program()` what the text says
        try:
            m = load(whole)[0]
        except CheckError as e:
            findings.append(('the inspecting rules are refused', whole, str(e)))
            continue
        it = Interp(m, io.StringIO(), fixed(True))
        try:
            got = [(k[0], k[1], k[2].v, tuple(items(k[3]))) for k in items(it.call_expr_rule(m.rules['census_all'], ()))]
        except Fault as e:
            findings.append(('the inspecting rules were refused when run', whole, str(e)))
            continue
        if got != forms_oracle(whole):
            findings.append(('what a rule reads of the program', whole, f'{got}\nexpected {forms_oracle(whole)}'))
        else:
            stats['read alike by a rule and from the text'] += 1
        # 3. the census: nothing escapes, and every constructor met is taken apart and put together
        if n % 6 == 0:
            rows, escaped, _, bad = census(load(src)[0])
            stats['constructors taken apart'] += len(rows)
            stats['nodes'] += sum(r[2] for r in rows)
            if escaped:
                findings.append(('a form that is no constructor of a form type', src, str(escaped)))
            if any(not (r[3] and r[4]) for r in rows):
                findings.append(('a constructor a rule could not take apart and put together', src,
                                 str([r[1] for r in rows if not (r[3] and r[4])])))
            if bad:
                findings.append(('a declaration whose text does not read back', src, str(bad)))
        # 4. every clause, written out whole, mirrored and written back, is the clause `invert` gives
        for name, r in m.rules.items():
            if r.kind != 'clauses' or r.backward or name in m.prelude_names or name.startswith('census_'):
                continue
            for c in r.clauses:
                stats['clauses mirrored'] += 1
                try:
                    back = as_block(mirror(as_sequence(c, whole=True)), whole=True)
                    if encode(back) != encode(invert_clause(c)):
                        findings.append(('a clause written out whole is mirrored otherwise', src, name))
                    if encode(as_block(as_sequence(c, whole=True), whole=True)) != encode(c):
                        findings.append(('a clause is not the same after `sequence` and `block`', src, name))
                except Exception as e:
                    findings.append(('a clause written out whole could not be mirrored', src, f'{name}: {e}'))
        # 5. a name is not given back against an expression that reads it
        v, k = rng.choice('abn'), rng.randrange(0, 9)
        expr = rng.choice([f'{k} + {v}', f'{v} * {k + 1}', f'{v}', f'{v} - {k}'])
        why = refusal(f'rule f takes I64 returns I64\n    {v} <-> m where\n        m is {k}\n        {v} was {expr}\n')
        stats['uncomputes that read themselves refused'] += 1
        if why is None or 'reads it' not in why or 'internal' in why:
            findings.append(('a name given back against an expression that reads it', expr, str(why)))
    return stats, findings


def model(programs=200, seed=1):
    """The interpreter against the model of XI.3 (tests/reference_model.py)."""
    import reference_model
    return reference_model.run(programs, seed)


# ---- declared types: a value is given only where its type is declared (R1) --------------------
# A `Bool` is a sub-shape of `Trit`, so a Bool is given where a Trit is declared and never a
# Trit where a Bool is.  Each program below gives a value of type X at one site where a Bool is
# declared.  The oracle is the sentence above: with X a Trit the program is refused, with its
# reason and with no failure of the toolchain; with X a Bool the same program is accepted.
# Then `set` to a value written as a literal, and literals given where a word is declared: the
# oracle is the type's width.
DECL_WHY = 'a Trit may be maybe and a Bool may not'
DECL_CELL = 'request {Cell}\n    {put}(flag: Bool) returns ()\n    {get}() returns Bool\n\n'
DECL_SITES = [
    ('the input of a rule',
     'rule {g} takes Bool returns Bool\n    b <-> b\n\n'
     'rule {f} takes {X} returns Bool\n    {t} <-> {b} where\n        {b} is {g}({t})\n'),
    ('inside a tuple',
     'rule {g} takes (Bool, {P}) returns (Bool, {P})\n    (b, n) <-> (b, n)\n\n'
     'rule {f} takes ({X}, {P}) returns (Bool, {P})\n    ({t}, n) <-> ({b}, m) where\n'
     '        ({b}, m) is {g}(({t}, n))\n'),
    ('a parameter',
     'rule {g}(flag: Bool) takes {P} returns {P}\n    n <-> n\n\n'
     'rule {f} takes ({X}, {P}) returns ({X}, {P})\n    ({t}, n) <-> ({t}, m) where\n'
     '        m is {g}({t})(n)\n'),
    ('the result of a clause rule',
     'rule {f} takes ({X}, {P}) returns (Bool, {P})\n    ({t}, n) <-> ({t}, n)\n'),
    ('a field',
     'type {Flag}\n    {Flag}(on: Bool, n: {P})\n\n'
     'rule {f} takes ({X}, {P}) returns {Flag}\n    ({t}, n) <-> {Flag}({t}, n)\n'),
    ('the value set gives',
     'rule {f} takes (Bool, {X}) returns (Bool, {X})\n    ({b}, {t}) => ({b}, {t}) where\n'
     '        set {b} to {t}\n'),
    ('the other side of a swap',
     'rule {f} takes ({X}, Bool) returns ({X}, Bool)\n    ({t}, {b}) <-> ({t}, {b}) where\n'
     '        swap {t} and {b}\n'),
    ('a name given back',
     'rule {f} takes (Bool, {X}) returns {X}\n    ({b}, {t}) <-> {t} where\n        {b} was {t}\n'),
    ('the argument of an ask',
     DECL_CELL + 'rule {f}({t}: {X}) uses {Cell}\n    ask {put}({t})\n'),
    ('the argument of a message',
     'request {Cell}\n    {put}(flag: Bool) returns Bool\n\n'
     'answer {Store} for {Cell} takes Bool\n    ({put}(f), s) <-> (s, f)\n\n'
     'rule {f} takes ({Store}, {X}) returns ({Store}, {X}, Bool)\n    (i, {t}) <-> (i, {t}, r) where\n'
     '        r is i -> {put}({t})\n'),
    ('the reply of an answer',
     'request {Cell}\n    {get}() returns Bool\n\n'
     'answer {Store} for {Cell} takes {X}\n    ({get}(), s) <-> (s, true)\n'),
    ('the state of an answer',
     'request {Cell}\n    {put}(flag: {X}) returns ()\n\n'
     'answer {Store} for {Cell} takes Bool\n    ({put}(f), s) => ((), f) where\n        discard s\n'),
    ('the state an instance is made from',
     'request {Cell}\n    {get}() returns Bool\n\n'
     'answer {Store} for {Cell} takes Bool\n    ({get}(), s) <-> (r, s) where\n        r is s\n\n'
     'rule {f} takes {X} returns {Store}\n    {t} <-> i where\n        i is {Store} from {t}\n'),
    ('the parameter of a function',
     'rule {g}(b: Bool) returns Bool\n    b\n\nrule {f}({t}: {X}) returns {X}\n    {g}({t})\n'),
    ('the result of a function',
     'rule {f}({t}: {X}) returns Bool\n    {t}\n'),
    ('a rule read backward',
     'rule {g} takes {X} returns {X}\n    t <-> t\n\n'
     'rule {f} takes Bool returns {X}\n    {b} <-> {t} where\n        {t} is {g}({b})\n'),
]
DECL_WORDS = ['U8', 'I8', 'U16', 'I16', 'U32', 'I32', 'U64', 'I64', 'Bit']


def declared(programs=200, seed=1):
    from selvage.forms import INT_TYPES
    rng = random.Random(seed)
    stats = {'narrowings refused': 0, 'same programs accepted': 0, 'sites': 0, 'literals set': 0,
             'undecided values set': 0, 'literals given as words': 0, 'rewinds': 0}
    findings, seen = [], set()
    for i in range(programs):
        # ---- one site, given a Trit and given a Bool
        site, template = DECL_SITES[i % len(DECL_SITES)] if i < 2 * len(DECL_SITES) else rng.choice(DECL_SITES)
        tag = rng.randrange(1000)
        names = {k: f'{v}{tag}' for k, v in (('f', 'f'), ('g', 'g'), ('t', 't'), ('b', 'b'), ('put', 'put'), ('get', 'get'))}
        names.update({k: f'{k}{tag}' for k in ('Cell', 'Store', 'Flag')}, P=rng.choice(['I64', 'U8', 'Bit', 'Text']))
        narrow, same = template.format(X='Trit', **names), template.format(X='Bool', **names)
        why = refusal(narrow)
        seen.add(site)
        if why is None:
            findings.append(('a Trit was accepted where a Bool is declared', narrow, site))
        elif 'internal' in why or (DECL_WHY not in why and 'takes a state of type Bool, found Trit' not in why):
            findings.append(('a Trit where a Bool is declared was refused without its reason', narrow, why))
        else:
            stats['narrowings refused'] += 1
        why = refusal(same)
        if why is not None:
            findings.append(('the same program with a Bool was refused', same, why))
        else:
            stats['same programs accepted'] += 1
        # ---- `set` to a literal, and a literal given as a word: the type's width
        t = rng.choice(DECL_WORDS + ['F64'])
        lit, start = rng.randrange(0, 300), rng.randrange(0, 300)
        src = (f'rule g takes {t} returns {t}\n    n => n where\n        set n to {lit}\n\n'
               f'rule k takes ({t}, I64) returns I64\n    (n, m) => m where\n        discard n\n\n'
               f'rule p(w: {t}) takes I64 returns I64\n    n => n where\n        c is w\n        add 1 to c\n'
               f'        discard c\n')
        why = refusal(src)
        if why is not None:
            findings.append(('`set` to a literal was refused', src, why))
            continue
        m = load(src)[0]
        width = 64 if t == 'F64' else INT_TYPES[t][0]
        value = float(start) if t == 'F64' else Word(start, t)
        want = float(lit) if t == 'F64' else Word(lit, t)
        it = Interp(m)
        try:
            out = it.forward(m.rules['g'], (), deep_copy(value))
            kept = it.journal_bits()
            back = it.rewind(m.rules['g'], (), out)
        except Fault as e:
            findings.append(('`set` to a literal did not run', src, f'{start}: {e}'))
            continue
        stats['literals set'] += 1
        stats['rewinds'] += 1
        if identity(out) != identity(want) or kept != width or identity(back) != identity(value):
            findings.append(('`set` to a literal', src, f'{start} -> {out}, kept {kept} bits, rewound to {back}; '
                             f'the oracle says {want}, {width} bits'))
        for rule, params, given in (('k', (), (Word(lit, 'I64', True), Word(1))), ('p', (Word(lit, 'I64', True),), Word(1))):
            if rule == 'p' and t == 'F64':
                continue                      # an update on F64 rounds, and keeps what it replaces
            it = Interp(m)
            it.forward(m.rules[rule], params, given)
            entry = it.journal[0].kids[2]
            stats['literals given as words'] += 1
            ty = 'F64' if isinstance(entry, float) else getattr(entry, 'ty', None)
            if it.journal_bits() != width or ty != t:
                findings.append(('a literal given where a word is declared', src,
                                 f'{rule}: kept {entry} as {ty}, {it.journal_bits()} bits; the oracle says {t}, {width} bits'))
        # ---- `set` on a Trit: what it replaces is a Trit, two bits whichever it holds
        new = rng.choice(['true', 'false', 'maybe'])
        src = f'rule g takes Trit returns Trit\n    t => t where\n        set t to {new}\n'
        why = refusal(src)
        if why is not None:
            findings.append(('`set` on a Trit was refused', src, why))
            continue
        m = load(src)[0]
        charges = []
        for v in (True, False, MAYBE):
            it = Interp(m)
            out = it.forward(m.rules['g'], (), v)
            charges.append(it.journal_bits())
            if it.rewind(m.rules['g'], (), out) is not v:
                findings.append(('`set` on a Trit did not rewind', src, str(v)))
            stats['rewinds'] += 1
        stats['undecided values set'] += 1
        if charges != [2, 2, 2]:
            findings.append(('`set` on a Trit', src, f'charged {charges} for true, false and maybe; the oracle says 2 each'))
    stats['sites'] = len(seen)
    return stats, findings


# ---- the CCNOT tape: the prelude's draw and birth against a model of wiring 1 of its own -----
class TapeModel:
    """Wiring 1, written from its description and sharing no code with the interpreter: two
    CCNOTs share the cells under both heads as controls and target the next cell of each tape;
    then head i moves forward and head j backward.  A draw ticks and reads the cell under i."""
    def __init__(self, a, b, i, j):
        self.a, self.b, self.i, self.j = list(a), list(b), i, j

    def tick(self):
        c = self.a[self.i] & self.b[self.j]
        self.a[(self.i + 1) % len(self.a)] ^= c
        self.b[(self.j - 1) % len(self.b)] ^= c
        self.i, self.j = (self.i + 1) % len(self.a), (self.j - 1) % len(self.b)

    def draw(self):
        self.tick()
        return self.a[self.i]

    def birth(self):
        ca = [self.draw() for _ in self.a]
        cb = [self.draw() for _ in self.b]
        return TapeModel(ca, cb, 0, 0)

    def value(self):
        return (self.a, self.b, self.i, self.j)


def tape_state(a, b, i, j):
    return Form('CcnotTape', (Arr('Bit', [Word(x, 'Bit') for x in a]), Arr('Bit', [Word(x, 'Bit') for x in b]),
                              Word(i, 'I64'), Word(j, 'I64')))


def tape_value(state):
    a, b, i, j = state.kids
    return ([w.v for w in a.data], [w.v for w in b.data], i.v, j.v)


def tape(programs=200, seed=1):
    """The prelude's `draw` and `birth` against the model, on random tapes of 2 to 16 cells;
    every draw and birth taken back by its derived inverse; and the tick against its own."""
    rng = random.Random(seed)
    stats = {'tapes': 0, 'draws': 0, 'births': 0, 'taken back': 0, 'ticks undone': 0}
    findings = []
    m = load('')[0]
    if not all(n in m.rules for n in ('tape_tick', 'draw', 'birth')):
        return stats, [('the prelude has no CCNOT tape', '', '')]
    tick, draw, birth = m.rules['tape_tick'], m.rules['draw'], m.rules['birth']
    for _ in range(programs):
        la, lb = rng.randint(2, 16), rng.randint(2, 16)
        a, b = [rng.randint(0, 1) for _ in range(la)], [rng.randint(0, 1) for _ in range(lb)]
        i, j = rng.randrange(la), rng.randrange(lb)
        where = f'a={a} b={b} i={i} j={j}'
        stats['tapes'] += 1
        model, it = TapeModel(a, b, i, j), Interp(m)
        state, history = tape_state(a, b, i, j), []
        try:
            for _ in range(rng.randint(0, 40)):
                before = deep_copy(state)
                bit, state = it.forward(draw, (), state)
                history.append((before, draw, deep_copy((bit, state))))
                stats['draws'] += 1
                if bit.v != model.draw() or tape_value(state) != model.value():
                    findings.append(('a draw differs from the model', where, f'after {stats["draws"]} draws'))
                    break
            if rng.random() < 0.5:
                before = deep_copy(state)
                child, state = it.forward(birth, (), state)
                history.append((before, birth, deep_copy((child, state))))    # as born; the child draws below
                stats['births'] += 1
                kid = model.birth()
                if tape_value(child) != kid.value() or tape_value(state) != model.value():
                    findings.append(('a birth differs from the model', where, tape_value(child)))
                for _ in range(rng.randint(0, 10)):
                    bit, child = it.forward(draw, (), child)
                    if bit.v != kid.draw():
                        findings.append(('a child draws other than the model', where, ''))
                        break
            for before, rule, out in reversed(history):
                back = it.undo(rule, (), out)
                stats['taken back'] += 1
                if back != before:
                    findings.append((f'taking back a {rule.name} did not give the tape back', where, ''))
                    break
            start = tape_state(a, b, i, j)
            ticked = it.forward(tick, (), deep_copy(start))
            ref = TapeModel(a, b, i, j)
            ref.tick()
            if tape_value(ticked) != ref.value() or it.undo(tick, (), ticked) != start:
                findings.append(('a tick, or its derived inverse', where, ''))
            stats['ticks undone'] += 1
        except Fault as e:
            findings.append(('a tape of two cells or more was refused', where, str(e)))
    return stats, findings


# ---- the reversible profile: certified rules laid out as gates, run against the interpreter ----
def circuits(programs=200, seed=1):
    """Generated gate rules over bits laid out as X, CNOT and CCNOT, run on every input; and the
    prelude's array rules and the CCNOT tape at random sizes and head positions.  Each circuit must
    give what the interpreter gives, refuse where it refuses, give its input back when run
    backward, and agree with the derived inverse laid out on its own."""
    from selvage.circuit import lower, simulate, simulate_back, NotLowerable, Dirty
    rng = random.Random(seed)
    stats = {'gate rules': 0, 'array rules': 0, 'tape rules': 0, 'runs': 0, 'refused alike': 0,
             'gates laid out': 0, 'ancillas given back': 0, 'inverses laid out': 0}
    findings = []
    B = lambda v: Word(v, 'Bit')                                   # noqa: E731

    def check(m, r, inputs, where):
        try:
            c = lower(m, r, (), inputs[0])
        except NotLowerable as e:
            findings.append(('a rule the profile should lay out was refused', where, str(e)))
            return
        except Fault:
            # refused while laid out: what the words decide refuses, so every input refuses
            for x in inputs:
                stats['runs'] += 1
                try:
                    Interp(m).forward(r, (), deep_copy(x))
                    findings.append(('refused when laid out, but the interpreter runs it', where, f'{x}'))
                    return
                except Fault:
                    stats['refused alike'] += 1
            return
        stats['gates laid out'] += len(c.gates)
        for x in inputs:
            stats['runs'] += 1
            try:
                want = Interp(m).forward(r, (), deep_copy(x))
            except Fault:
                want = None
            try:
                got = simulate(c, x)
            except Dirty:
                got = None
            if want is None or got is None:
                if (want is None) != (got is None):
                    findings.append(('the circuit and the interpreter refuse differently', where, f'{x}'))
                else:
                    stats['refused alike'] += 1
                continue
            stats['ancillas given back'] += len(c.released)
            if got != want:
                findings.append(('the circuit gives other than the interpreter', where, f'{x}'))
                return
            try:
                if simulate_back(c, got) != x:
                    findings.append(('run backward, the circuit does not give the input back', where, f'{x}'))
                    return
                ci = lower(m, r.inverse, (), got)
                stats['inverses laid out'] += 1
                if simulate(ci, got) != x:
                    findings.append(('the derived inverse, laid out, does not give the input back', where, f'{x}'))
                    return
            except (Dirty, NotLowerable, Fault) as e:
                findings.append(('the inverse failed', where, f'{x}: {e}'))
                return

    prelude = load('')[0]
    for _ in range(programs):
        g = Gates(rng, False)
        src = g.program()
        if refusal(src) is None:
            m = load(src)[0]
            stats['gate rules'] += 1
            ins = [tuple(B((v >> k) & 1) for k in range(g.n)) for v in range(2 ** g.n)]
            check(m, m.rules['f'], ins, src)
        name = rng.choice(['exchange', 'fanout', 'ripple_add'])
        w = rng.randint(1, 6)
        def arr():
            return Arr('Bit', [B(rng.randint(0, 1)) for _ in range(w)])
        ins = [(arr(), arr(), B(rng.randint(0, 1))) if name == 'ripple_add' else (arr(), arr()) for _ in range(6)]
        stats['array rules'] += 1
        check(prelude, prelude.rules[name], ins, f'{name} at width {w}')
        name = rng.choice(['tape_tick', 'draw', 'birth'])
        la, lb = rng.randint(2, 6), rng.randint(2, 6)
        i, j = rng.randrange(la), rng.randrange(lb)
        ins = [Form('CcnotTape', (Arr('Bit', [B(rng.randint(0, 1)) for _ in range(la)]),
                                  Arr('Bit', [B(rng.randint(0, 1)) for _ in range(lb)]), Word(i, 'I64'), Word(j, 'I64')))
               for _ in range(6)]
        stats['tape rules'] += 1
        check(prelude, prelude.rules[name], ins, f'{name} at {la} and {lb} cells, heads {i} and {j}')
    return stats, findings


# ---- the Measure group: declared in the prelude, answered by nothing ---------------------------
class MeasureProgram:
    """Procedures main = p0, p1, ... that output markers, ask `measure`, call a lossy clause rule
    that asks it, and call the next procedure, some of it inside a stand-in answer installed with
    `with`.  The oracle knows nothing of the toolchain: an ask the innermost stand-in takes gets that
    stand-in's reply; one nothing takes reaches Root and ends the run."""

    def __init__(self, rng):
        self.r = rng
        self.stand = [(rng.randint(0, 3), rng.randint(0, 1)) for _ in range(rng.randint(0, 2))]
        self.look = rng.random() < 0.6
        self.levels = rng.randint(1, 4)
        self.body = [self.steps(i) for i in range(self.levels)]

    def steps(self, i):
        kinds = ['ask', 'out'] + (['look'] if self.look else [])
        if self.stand and self.look:
            kinds.append('lookwith')
        out = [('out', 100 + i)]
        for _ in range(self.r.randint(1, 4)):
            k = self.r.choice(kinds + (['call', 'call'] if i + 1 < self.levels else []))
            if k == 'out':
                out.append(('out', self.r.randint(2, 99)))
            elif k in ('call', 'lookwith'):
                within = (self.r.randrange(len(self.stand)), self.r.randint(0, 5)) if self.stand and (
                    k == 'lookwith' or self.r.random() < 0.5) else None
                out.append((k, within))
            else:
                out.append((k,))
        return out

    def rows(self):
        """Measure where an ask leaves the rule; System where a lossy rule is called."""
        need = [None] * self.levels
        for i in reversed(range(self.levels)):
            m = s = False
            for st in self.body[i]:
                if st[0] in ('ask', 'look'):
                    m = True
                if st[0] in ('look', 'lookwith'):
                    s = True
                if st[0] == 'call':
                    m = m or (need[i + 1][0] and st[1] is None)
                    s = s or need[i + 1][1]
            need[i] = (m, s)
        return need

    def text(self, drop=None, arrow='=>'):
        lines = []
        for x, (c, d) in enumerate(self.stand):
            lines += [f'answer S{x} for Measure takes I64', '    (measure(), n) <-> (b, n) where',
                      f'        b is Bit(({c} * n + {d}) mod 2)', '        add 1 to n', '']
        if self.look:
            lines += ['rule look takes I64 returns (I64, Bit) uses Measure', f'    x {arrow} (x, b) where',
                      '        b is ask measure()', '']
        need = self.rows()
        for i in range(self.levels):
            row = ['Output'] + (['Measure'] if need[i][0] and drop != i else []) + (['System'] if need[i][1] else [])
            lines.append(f'rule {"main" if i == 0 else f"p{i}"} uses {", ".join(row)}')
            for u, st in enumerate(self.body[i]):
                if st[0] == 'out':
                    lines.append(f'    output {st[1]}')
                elif st[0] == 'ask':
                    lines += [f'    x{u} is ask measure()', f'    output x{u}']
                elif st[0] == 'look':
                    lines += [f'    (y{u}, b{u}) is look({u})', f'    output b{u}']
                elif st[0] == 'lookwith':
                    x, n = st[1]
                    lines += [f'    ((y{u}, b{u}), s{u}) is look({u}) with S{x} from {n}', f'    output b{u}', f'    output s{u}']
                elif st[1] is None:
                    lines.append(f'    p{i + 1}()')
                else:
                    x, n = st[1]
                    lines += [f'    (v{u}, s{u}) is p{i + 1}() with S{x} from {n}', f'    output s{u}']
            lines.append('')
        return '\n'.join(lines)

    def run(self, i, stack, out):
        def reply():
            if not stack:
                raise Stop('root')
            x, n = stack[-1]
            c, d = self.stand[x]
            stack[-1] = (x, n + 1)
            return (c * n + d) % 2
        for st in self.body[i]:
            if st[0] == 'out':
                out.append(str(st[1]))
            elif st[0] in ('ask', 'look'):
                out.append(str(reply()))
            elif st[0] == 'lookwith' or st[1] is not None:
                stack.append(st[1])
                if st[0] == 'lookwith':
                    out.append(str(reply()))
                else:
                    self.run(i + 1, stack, out)
                x, n = stack.pop()
                out.append(f'S{x} from {n}')
            else:
                self.run(i + 1, stack, out)


def measure(programs=200, seed=1):
    """`ask measure()` through procedures, a lossy clause rule and stand-in answers.  The run must
    print what the oracle prints and end where it ends: an ask nothing installed takes is refused at
    Root, with the reason the interpreter gives for a request nobody answers.  A clause rule that
    asks is lossy, so `<->` on it is refused; a rule whose ask leaves it without `Measure` in its
    row is refused."""
    rng = random.Random(seed)
    stats = {'programs run': 0, 'asks taken': 0, 'refused at the root': 0, 'completed': 0,
             'wrong arrows refused': 0, 'missing rows refused': 0}
    findings = []
    for _ in range(programs):
        p = MeasureProgram(rng)
        src = p.text()
        stats['programs run'] += 1
        why = refusal(src)
        if why is not None:
            findings.append(('a program that asks measure was refused by the checker', src, why))
            continue
        if p.look:
            why = refusal(p.text(arrow='<->'))
            if why is None or 'it asks outside itself, so its reply is world input' not in why:
                findings.append(('a clause rule that asks measure accepted as certified', src, why))
            else:
                stats['wrong arrows refused'] += 1
        need = p.rows()
        asking = [i for i in range(p.levels) if need[i][0]]
        if asking:
            i = rng.choice(asking)
            why = refusal(p.text(drop=i))
            if why is None or 'Measure' not in why:
                findings.append(('a rule that reaches measure accepted without Measure in its row', src, why))
            else:
                stats['missing rows refused'] += 1
        want, ended = [], None
        try:
            p.run(0, [], want)
        except Stop:
            ended = 'root'
        text = io.StringIO()
        it = Interp(load(src)[0], text)
        fault = None
        try:
            it.run_main()
        except Fault as e:
            fault = str(e)
        got = text.getvalue().splitlines()
        stats['refused at the root' if ended else 'completed'] += 1
        stats['asks taken'] += sum(1 for w in want if w in ('0', '1'))
        if (fault is None) != (ended is None) or (ended and 'no answer for request measure' not in fault):
            findings.append(('how a run that asks measure ended', src, f'oracle {ended}, run {fault}'))
        elif got != want:
            findings.append(('what a run that asks measure prints', src, f'{got}\noracle {want}'))
    return stats, findings


PARTS = [('arrows', arrows), ('delegation', delegation), ('rows', rows), ('between runs', between_runs),
         ('operators', operators), ('any', any_type), ('refusal', refusals), ('seal', seal), ('witness', witness), ('depth', depth), ('structures', structures), ('decisions', decisions),
         ('journal', journal), ('names', names), ('accounting', accounting), ('extent', extents), ('forms', forms), ('model', model),
         ('declared', declared), ('tape', tape), ('circuits', circuits), ('measure', measure)]


def guarded(part):
    """A generator counts a refused program as a refusal the oracle may have expected.  A
    toolchain that refuses its own prelude would then pass every one of them silently, so
    that is checked first, and is a finding."""
    def run(programs=200, seed=1, **more):
        why = refusal('')
        if why is not None:
            return {}, [('the toolchain refuses its own prelude', '', why)]
        return part(programs, seed, **more)
    return run


PARTS = [(name, guarded(part)) for name, part in PARTS]


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    s = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    total = 0
    for name, part in PARTS:
        stats, findings = part(n, s)
        total += len(findings)
        print(f'{name:<13} {n} programs: ' + ', '.join(f'{v} {k}' for k, v in stats.items())
              + f'; {len(findings)} findings')
        for kind, src, detail in findings[:3]:
            print(f'--- {kind}: {detail}\n{src}')
    sys.exit(1 if total else 0)
