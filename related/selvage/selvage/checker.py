"""The checker: builds the program model, infers types and certifies rules.

R1 shapes are types        R5 roles by seal
R2 certification           R6 rows contain
R3 linearity               R7 two stores (prelude fixed for the run)
R4 exact updates           R8 no undefined behaviour

Every clause rule is classified as a bijection, a partial bijection or lossy, and
its arrow must say which: `<->` certified, `=>` lossy.  An expression rule with an
empty `uses` row is a function, recomputable as a whole from its parameters
(Bennett); with a row it is a procedure, which keeps the world's replies.
"""
from .forms import Form, Word, INT_TYPES, Fault, MAYBE
from .printer import expr_text, type_text
from .invert import invert_clause, flip_name, names_in, exchange_and_discard

INTS = set(INT_TYPES)
NUMERIC = INTS | {'F64'}
CONVERSIONS = INTS | {'F64'}
WIDENINGS = {'Trit'}       # `Trit(b)`: a Bool given as a Trit; the value is unchanged
BUILTINS = {'array', 'length', 'bitand', 'bitor', 'bitxor', 'shift_left', 'shift_right',
            'sqrt', 'floor', 'identity', 'show', 'evaluate', 'definition', 'inverse', 'sequence', 'block', 'program'}
CMP_TAGS = {'Equal', 'NotEqual', 'Less', 'Greater', 'LessEqual', 'GreaterEqual'}
ARITH_TAGS = {'Add', 'Subtract', 'Multiply', 'Divide', 'Mod'}
WILD = ('_',)


class CheckError(Fault):
    pass


def tstr(t):
    if isinstance(t, str):
        return t
    if t[0] == 'Tuple':
        return '(' + ', '.join(tstr(x) for x in t[1]) + ')'
    if t[0] == 'Array':
        return f'Array({tstr(t[1])})'
    if t[0] in ('Data', 'Inst', 'Rule'):
        return t[1]
    return str(t)


class TypeInfo:
    def __init__(self, name, ctors, parent, line):
        self.name, self.ctors, self.parent, self.line = name, ctors, parent, line  # ctors: {c: [(f, ty)]}


class RuleInfo:
    def __init__(self, name, decl):
        self.name, self.decl = name, decl
        self.line = decl.line
        self.params = []          # [(name, type)]
        self.takes = self.returns = 'Any'
        self.uses = set()
        self.kind = None          # 'clauses' | 'block'
        self.clauses = []
        self.block = None
        self.cls = None           # bijection | partial | lossy | function | procedure
        self.reasons = []
        self.journal_choice = False
        self.left_exhaustive = False
        self.var_types = {}       # id(clause or rule) -> {var: type}
        self.is_answer = False
        self.group = None
        self.groups = set()       # answers: the request groups it is declared for
        self.group_order = []
        self.backward = name.startswith('undo ')   # a derived inverse: it reads its choices back
        self.ops = {}             # answers: request -> the rule of its own that answers it
        self.delegates = {}       # answers: request -> (path into the state, the answer of the component there)
        self.native = set()       # Root: requests the system answers without a clause (refuse)
        self.place = 'program'    # where the declaration lives: the prelude, or the program
        self.asks = None          # an answer's request rule: the requests and groups it can reach by asking
        self.op = None            # an answer's per-request rule: its request
        self.owner = None         # ... and the answer that declared it
        self.inverse = None       # the RuleInfo checked from invert(this rule's code)
        self.source_clauses = None
        self.first_match_decides = False


class Model:
    def __init__(self):
        self.types = {}
        self.ctors = {}       # ctor -> (typename, [(field, type)])
        self.rules = {}
        self.answers = {}
        self.requests = {}    # group -> {op: (params, returns)}
        self.ops = {}         # op -> group
        self.auto = {}        # id(block) -> [(defstep, lastuse, names)]  (source only; elaborated away)
        self.rounding = set() # id(update stmt) whose target rounds (elaborated to exchange + discard)
        self.set_as = {}      # id(set stmt in a clause) -> the conversion its value is written under
        self.proved = set()   # id(was stmt) the checker proved: an uncompute whose check cannot fail
        # id(discard stmt) -> (type, constructors still possible or None, recomputable): what the
        # dropped value is charged for, alike in both backends (VII.5)
        self.drops = {}
        self.elaborated = {}  # id(source clause) -> the clause that runs
        self.alias_checks = {}  # id(update stmt) -> [(target_index_expr, read_index_expr)]
        self.etypes = {}      # id(expr) -> type
        self.errors = []
        self.decl_order = []
        self.answer_names = set()
        self.prelude_names = set()
        self.any_ok = True    # `Any` may be written: true only inside the prelude's declarations
        self.sealed = {}      # request group -> the answer it is sealed to (`request G for A`)
        self.sealed_answers = {}   # that answer -> the group
        self.group_place = {}      # request group -> the place that declares it

    def err(self, line, msg):
        self.errors.append(f'line {line}: {msg}' if line else msg)

    # ---- answers: a request is answered by a rule of the answer's own, or delegated to
    # the one component of its state that answers it ----------------------------------
    def answers_op(self, aname, op):
        a = self.answers.get(aname)
        return a is not None and (op in a.ops or op in a.delegates or op in a.native)

    def op_rule(self, aname, op):
        """The rule that finally answers `op` for an instance of `aname`: its own, or the
        rule of the component it delegates to.  None if nothing does, or the system does."""
        seen = set()
        while aname in self.answers and aname not in seen:
            seen.add(aname)
            a = self.answers[aname]
            if op in a.ops:
                return a.ops[op]
            if op not in a.delegates:
                return None
            aname = a.delegates[op][1]
        return None

    # ---- R5: a sealed declaration is used only by code in the place that declares it ---
    def holds_seal(self, place, group):
        return place == self.group_place.get(group, 'program')

    def sealed_by(self, aname, seen=()):
        """The sealed answer an answer is under: itself, or one that its state holds.  An
        answer that holds a sealed instance is sealed with it, since making or opening
        the holder would hand that instance over."""
        if aname in self.sealed_answers:
            return aname
        a = self.answers.get(aname)
        if a is None or aname in seen:
            return None
        for _, part in self.components(a.takes):
            inner = self.sealed_by(part, seen + (aname,))
            if inner:
                return inner
        return None

    def passes_outward(self, op):
        """An answer may pass the request it is answering outward only where a sealed answer
        gives the final reply: a host's answer for Witness asks `history` of the next answer
        out, in the end Root."""
        return any(self.answers_op(a, op) for a in self.sealed_answers)

    def reach(self, aname, op):
        """What the rule that answers `op` for `aname` can reach by asking: (requests, groups)."""
        r = self.op_rule(aname, op)
        return r.asks if r is not None and r.asks is not None else (frozenset(), frozenset())

    def answered_ops(self, aname):
        a = self.answers.get(aname)
        return [] if a is None else list(a.ops) + list(a.delegates) + sorted(a.native)

    def components(self, t):
        """The parts of a state that can hold an instance to delegate to: the state itself,
        the members of a tuple, the fields of a record.  Each is (path, answer name)."""
        inst = lambda x: isinstance(x, tuple) and x[0] == 'Inst'
        if inst(t):
            return [((), t[1])]
        if isinstance(t, tuple) and t[0] == 'Tuple':
            return [((i,), x[1]) for i, x in enumerate(t[1]) if inst(x)]
        if isinstance(t, tuple) and t[0] == 'Data' and t[1] in self.types and len(self.types[t[1]].ctors) == 1:
            fields = next(iter(self.types[t[1]].ctors.values()))
            return [((i,), ft[1]) for i, (_, ft) in enumerate(fields) if inst(ft)]
        return []

    # ---- type helpers ------------------------------------------------------
    def conv(self, tf, line=None):
        if tf is None:
            return 'Any'
        if tf.tag == 'TypeName':
            n = tf.kids[0]
            if n == '':
                return 'Any'
            if n == 'Any' and not self.any_ok:
                self.err(line, '`Any` belongs to the prelude, where it types the journal\'s entries and code; '
                               'a declaration names its types')
            if n in INTS or n in ('F64', 'Bool', 'Trit', 'Text', 'Any'):
                return n
            if n in self.types:
                return ('Data', n)
            if n in self.answer_names:
                return ('Inst', n)
            self.err(line, f'unknown type {n}')
            return 'Any'
        if tf.tag == 'TupleType':
            if not tf.kids:
                return 'Unit'
            return ('Tuple', tuple(self.conv(x, line) for x in tf.kids))
        if tf.tag == 'TypeApp':
            n = tf.kids[0]
            if n == 'Array' and len(tf.kids) == 2:
                return ('Array', self.conv(tf.kids[1], line))
            self.err(line, f'unknown type constructor {n}')
            return 'Any'
        return 'Any'

    def record_fields(self, t):
        if isinstance(t, tuple) and t[0] == 'Data':
            info = self.types[t[1]]
            if len(info.ctors) == 1:
                return dict(next(iter(info.ctors.values())))
        return None


def join(a, b, m=None, line=None, what='operands'):
    if a == b:
        return a
    if {a, b} == {'Bool', 'Trit'}:
        return 'Trit'   # Bool is a sub-shape of Trit
    if a == 'Any' or b == 'Any':
        return 'Any'
    if a == 'Lit' and (b in NUMERIC):
        return b
    if b == 'Lit' and (a in NUMERIC):
        return a
    if isinstance(a, tuple) and isinstance(b, tuple) and a[0] == b[0] == 'Tuple' and len(a[1]) == len(b[1]):
        return ('Tuple', tuple(join(x, y, m, line, what) for x, y in zip(a[1], b[1])))
    if m is not None:
        m.err(line, f'type mismatch in {what}: {tstr(a)} and {tstr(b)}')
    return 'Any'


def widens(want, found):
    """Whether `found` may hold `maybe` where `want` declares a `Bool`."""
    if want == 'Bool' and found == 'Trit':
        return True
    if isinstance(want, tuple) and isinstance(found, tuple) and want[0] == found[0] == 'Tuple' \
            and len(want[1]) == len(found[1]):
        return any(widens(w, f) for w, f in zip(want[1], found[1]))
    return False


UNDECIDED = 'a Trit may be maybe and a Bool may not; `decide` it first'


def expect(want, found, m=None, line=None, what='operands'):
    """A value of type `found` given where `want` is declared (R1).  `Bool` is a sub-shape of
    `Trit`, so a Bool is given where a Trit is declared and never the other way."""
    if widens(want, found):
        if m is not None:
            m.err(line, f'type mismatch in {what}: {tstr(want)} and {tstr(found)} ({UNDECIDED})')
        return want
    return join(want, found, m, line, what)


def alike(a, b, m=None, line=None, what='swap'):
    """Two cells that exchange their values hold the same type."""
    if widens(a, b) or widens(b, a):
        if m is not None:
            m.err(line, f'type mismatch in {what}: {tstr(a)} and {tstr(b)} ({UNDECIDED})')
        return a
    return join(a, b, m, line, what)


def fits(want, found):
    """Whether a value of type `found` is of the declared type `want`."""
    unit = ('Unit', ('Tuple', ()))
    if want == found or want == 'Any' or found == 'Any' or (want in unit and found in unit):
        return True
    if found == 'Lit':
        return want in NUMERIC
    if want == 'Trit' and found == 'Bool':
        return True
    if isinstance(want, tuple) and isinstance(found, tuple) and want[0] == found[0] == 'Tuple':
        return len(want[1]) == len(found[1]) and all(fits(w, f) for w, f in zip(want[1], found[1]))
    return False


def settle(t):
    """A literal that is bound to a name defaults to I64."""
    if t == 'Lit':
        return 'I64'
    if isinstance(t, tuple) and t[0] == 'Tuple':
        return ('Tuple', tuple(settle(x) for x in t[1]))
    return t


# ---- patterns --------------------------------------------------------------

def is_pattern(e, m):
    t = e.tag
    if t in ('Name', 'Literal'):
        return True
    if t == 'Tuple':
        return all(is_pattern(x, m) for x in e.kids)
    if t == 'Call' and e.kids[0].tag == 'Name' and (e.kids[0].kids[0] in m.ctors or e.kids[0].kids[0] in m.ops):
        return all(is_pattern(x, m) for x in e.kids[1].kids)
    return False


def is_ctor_name(n, m):
    return n in m.ctors or n in m.ops


def pattern_vars(e, m, out=None):
    out = [] if out is None else out
    t = e.tag
    if t == 'Name':
        if not is_ctor_name(e.kids[0], m):
            out.append(e.kids[0])
    elif t == 'Tuple':
        for x in e.kids:
            pattern_vars(x, m, out)
    elif t == 'Call':
        for x in e.kids[1].kids:
            pattern_vars(x, m, out)
    return out


def absp(e, m):
    t = e.tag
    if t == 'Name':
        n = e.kids[0]
        if is_ctor_name(n, m):
            return ('ctor', n, ())
        return WILD
    if t == 'Literal':
        v = e.kids[0]
        if isinstance(v, bool):
            return ('bool', v, ())
        if v is MAYBE:
            return ('maybe', None, ())
        if isinstance(v, Word):
            return ('int', v.v, ())
        return ('lit', v, ())
    if t == 'Tuple':
        return ('tuple', len(e.kids), tuple(absp(x, m) for x in e.kids))
    if t == 'Call':
        return ('ctor', e.kids[0].kids[0], tuple(absp(x, m) for x in e.kids[1].kids))
    return WILD


def overlap(p, q):
    if p == WILD or q == WILD:
        return True
    if p[0] != q[0] or p[1] != q[1] or len(p[2]) != len(q[2]):
        return False
    return all(overlap(a, b) for a, b in zip(p[2], q[2]))


def covers(p, q):
    """Whether the pattern p matches every value the pattern q matches."""
    if p == WILD:
        return True
    if q == WILD or p[0] != q[0] or p[1] != q[1] or len(p[2]) != len(q[2]):
        return False
    return all(covers(a, b) for a, b in zip(p[2], q[2]))


def path_to(e, name):
    """Where a pattern binds `name`: the indices leading to it, or None."""
    if e.tag == 'Name':
        return () if e.kids[0] == name else None
    kids = e.kids if e.tag == 'Tuple' else e.kids[1].kids if e.tag == 'Call' else ()
    for i, x in enumerate(kids):
        got = path_to(x, name)
        if got is not None:
            return (i,) + got
    return None


def put_at(p, path, q):
    """The abstract pattern p with q where `path` leads."""
    if not path:
        return q
    kids = list(p[2])
    kids[path[0]] = put_at(kids[path[0]], path[1:], q)
    return (p[0], p[1], tuple(kids))


class Exhaust:
    def __init__(self, m):
        self.m = m

    def col_type(self, t, col):
        if t != 'Any':
            return t
        for p in col:
            if p == WILD:
                continue
            if p[0] == 'ctor' and p[1] in self.m.ctors:
                return ('Data', self.m.ctors[p[1]][0])
            if p[0] == 'tuple':
                return ('Tuple', ('Any',) * p[1])
            if p[0] == 'maybe':
                return 'Trit'
        for p in col:
            if p != WILD and p[0] == 'bool':
                return 'Bool'
        return 'Any'

    def all_heads(self, t):
        if t == 'Bit':
            return [('int', 0, 0), ('int', 1, 0)]
        if t == 'Bool':
            return [('bool', False, 0), ('bool', True, 0)]
        if t == 'Trit':
            return [('bool', False, 0), ('bool', True, 0), ('maybe', None, 0)]
        if isinstance(t, tuple) and t[0] == 'Tuple':
            return [('tuple', len(t[1]), len(t[1]))]
        if isinstance(t, tuple) and t[0] == 'Data':
            info = self.m.types[t[1]]
            return [('ctor', c, len(fs)) for c, fs in info.ctors.items()]
        if t == 'Unit':
            return [('tuple', 0, 0)]
        return None

    def sub_types(self, t, head):
        kind, key, arity = head
        if kind == 'tuple':
            if isinstance(t, tuple) and t[0] == 'Tuple' and len(t[1]) == arity:
                return list(t[1])
            return ['Any'] * arity
        if kind == 'ctor' and key in self.m.ctors:
            return [ft for _, ft in self.m.ctors[key][1]]
        return ['Any'] * arity

    @staticmethod
    def head(p):
        return (p[0], p[1], len(p[2]))

    def spec(self, rows, head):
        out = []
        for r in rows:
            if r[0] == WILD:
                out.append([WILD] * head[2] + r[1:])
            elif self.head(r[0]) == head:
                out.append(list(r[0][2]) + r[1:])
        return out

    def useful(self, rows, q, tys):
        if not q:
            return not rows
        t = self.col_type(tys[0], [r[0] for r in rows] + [q[0]])
        if q[0] != WILD:
            h = self.head(q[0])
            return self.useful(self.spec(rows, h), list(q[0][2]) + q[1:], self.sub_types(t, h) + tys[1:])
        heads = {self.head(r[0]) for r in rows if r[0] != WILD}
        allh = self.all_heads(t)
        if allh is not None and set(allh) <= heads:
            return any(self.useful(self.spec(rows, h), [WILD] * h[2] + q[1:], self.sub_types(t, h) + tys[1:])
                       for h in allh)
        default = [r[1:] for r in rows if r[0] == WILD]
        return self.useful(default, q[1:], tys[1:])

    def exhaustive(self, pats, t):
        return not self.useful([[p] for p in pats], [WILD], [t])


# ---- variables in the linearity walk ----------------------------------------

class Var:
    __slots__ = ('kind', 'reads', 'defstep', 'modified', 'ty', 'block', 'rhs', 'pat')

    def __init__(self, kind, ty, reads=frozenset(), defstep=None, block=None):
        self.kind, self.ty, self.reads, self.defstep = kind, ty, reads, defstep
        self.modified = False
        self.block = block
        self.rhs = None
        self.pat = None        # the pattern of the `is` that bound it


def free_names(e, out=None):
    out = set() if out is None else out
    t = e.tag
    if t == 'Name':
        out.add(e.kids[0])
    elif t == 'Literal' or t == 'Quote':
        pass
    elif t == 'Field':
        free_names(e.kids[0], out)
    elif t in ('Send',):
        free_names(e.kids[0], out)
        for a in e.kids[1].kids[1].kids:
            free_names(a, out)
    elif t == 'Ask':
        for a in e.kids[0].kids[1].kids:
            free_names(a, out)
    else:
        for k in e.kids:
            if isinstance(k, Form):
                free_names(k, out)
    return out


def length_only_names(e):
    """Names an expression reads only through length(name)."""
    inside, outside = set(), set()

    def walk(x, in_len):
        if not isinstance(x, Form):
            return
        if x.tag == 'Name':
            (inside if in_len else outside).add(x.kids[0])
            return
        if x.tag == 'Call' and x.kids[0].tag == 'Name' and x.kids[0].kids[0] == 'length':
            for a in x.kids[1].kids:
                walk(a, True)
            return
        for k in x.kids:
            walk(k, in_len)
    walk(e, False)
    return inside - outside


def index_key(e):
    """Normalize an index expression to (base, offset) for disjointness."""
    if e.tag == 'Literal' and isinstance(e.kids[0], Word):
        return (None, e.kids[0].v)
    if e.tag in ('Add', 'Subtract'):
        b, o = index_key(e.kids[0])
        r = e.kids[1]
        if r.tag == 'Literal' and isinstance(r.kids[0], Word):
            return (b, o + (r.kids[0].v if e.tag == 'Add' else -r.kids[0].v))
        if e.tag == 'Add' and e.kids[0].tag == 'Literal' and isinstance(e.kids[0].kids[0], Word):
            b2, o2 = index_key(r)
            return (b2, o2 + e.kids[0].kids[0].v)
    return (e, 0)


def index_relation(a, b):
    ka, kb = index_key(a), index_key(b)
    if ka[0] == kb[0]:
        return 'same' if ka[1] == kb[1] else 'different'
    if ka[0] is None and kb[0] is None:
        return 'different'
    return 'unknown'


def path_of(e):
    """Access path of a target or a read: [name, ('.', f) | ('[]', idx), ...] or None."""
    if e.tag == 'Name':
        return [e.kids[0]]
    if e.tag == 'Field':
        p = path_of(e.kids[0])
        return None if p is None else p + [('.', e.kids[1])]
    if e.tag == 'Index':
        p = path_of(e.kids[0])
        return None if p is None else p + [('[]', e.kids[1])]
    return None


def read_paths(e, out=None):
    out = [] if out is None else out
    t = e.tag
    if t in ('Name', 'Field', 'Index'):
        p = path_of(e)
        if p is not None:
            out.append(p)
            if t == 'Index':
                read_paths(e.kids[1], out)
            return out
    if t == 'Call' and e.kids[0].tag == 'Name' and e.kids[0].kids[0] == 'length':
        return out  # length is invariant under element updates
    if t == 'Literal' or t == 'Quote':
        return out
    for k in e.kids:
        if isinstance(k, Form):
            read_paths(k, out)
    return out


class Checker:
    def __init__(self, m):
        self.m = m
        self.ex = Exhaust(m)
        self.place = 'program'    # the place of the code being checked (R5: who holds a seal)

    # ---- expression typing ----------------------------------------------
    def tyof(self, e, env, line=None):
        t = self._tyof(e, env, line or e.line)
        self.m.etypes[id(e)] = t
        return t

    def _tyof(self, e, env, line):
        m = self.m
        tag, k = e.tag, e.kids
        if tag == 'Literal':
            v = k[0]
            if isinstance(v, bool):
                return 'Bool'
            if v is MAYBE:
                return 'Trit'
            if isinstance(v, Word):
                return 'Lit'
            if isinstance(v, float):
                return 'F64'
            return 'Text'
        if tag == 'Name':
            n = k[0]
            if n in env:
                return env[n]
            if n in m.ctors:
                tn, fs = m.ctors[n]
                if fs:
                    m.err(line, f'constructor {n} needs its fields')
                return ('Data', tn)
            if n in m.rules:
                return ('Rule', n)
            m.err(line, f'unknown name {n}')
            return 'Any'
        if tag in ARITH_TAGS:
            a, b = self.tyof(k[0], env, line), self.tyof(k[1], env, line)
            if tag == 'Add' and a == b == 'Text':
                return 'Text'
            r = join(a, b, m, line, f'{expr_text(e)}')
            if r not in NUMERIC and r not in ('Lit', 'Any'):
                m.err(line, f'arithmetic needs numbers, found {tstr(r)}')
            return r
        if tag in CMP_TAGS:
            a, b = self.tyof(k[0], env, line), self.tyof(k[1], env, line)
            join(a, b, m, line, 'comparison')
            return 'Bool'
        if tag in ('And', 'Or', 'Not'):
            ts = [self.tyof(x, env, line) for x in k]
            for tt in ts:
                if tt not in ('Bool', 'Trit', 'Any'):
                    m.err(line, f'`{tag.lower()}` needs true, false or maybe, found {tstr(tt)}')
            return 'Trit' if 'Trit' in ts else 'Bool'   # Kleene's strong logic
        if tag == 'Negate':
            return self.tyof(k[0], env, line)
        if tag == 'Tuple':
            if not k:
                return 'Unit'
            return ('Tuple', tuple(self.tyof(x, env, line) for x in k))
        if tag == 'Field':
            bt = self.tyof(k[0], env, line)
            if bt == 'Any':
                return 'Any'
            fs = m.record_fields(bt)
            if fs is None or k[1] not in fs:
                m.err(line, f'{tstr(bt)} has no field {k[1]}')
                return 'Any'
            return fs[k[1]]
        if tag == 'Index':
            bt = self.tyof(k[0], env, line)
            it = self.tyof(k[1], env, line)
            if it not in INTS and it not in ('Lit', 'Any'):
                m.err(line, f'an index must be an integer, found {tstr(it)}')
            if isinstance(bt, tuple) and bt[0] == 'Array':
                return bt[1]
            if bt != 'Any':
                m.err(line, f'{tstr(bt)} cannot be indexed')
            return 'Any'
        if tag == 'Call':
            return self.call_type(e, env, line)
        if tag in ('Send', 'Ask'):
            req = k[1] if tag == 'Send' else k[0]
            op = req.kids[0]
            if tag == 'Send':
                it = self.tyof(k[0], env, line)
                if isinstance(it, tuple) and it[0] == 'Inst' and op in m.ops and not m.answers_op(it[1], op):
                    m.err(line, f'{it[1]} does not answer {op}: it has no rule for it, and no component '
                                f'of its state answers it')
            g = m.ops.get(op)
            if g in m.sealed and not m.holds_seal(self.place, g):
                m.err(line, f'{op} is a request of {g}, which is sealed to {m.sealed[g]}: only the system sends it')
            given = [self.tyof(a, env, line) for a in req.kids[1].kids]
            if op in m.ops:
                for at, (pn, pt) in zip(given, m.requests[m.ops[op]][op][0]):
                    expect(pt, at, m, line, f'argument {pn} of {op}')
                return m.requests[m.ops[op]][op][1]
            m.err(line, f'unknown request {op}')
            return 'Any'
        if tag == 'Undo':
            inner = k[0]
            info = self.clause_callee(inner)
            if info is None:
                m.err(line, '`undo` applies to a call of a clause rule')
                return 'Any'
            rule, params, inp = info
            self.check_call_params(rule, params, env, line)
            self.tyof(inp, env, line)
            return rule.takes
        if tag == 'Quote':
            return ('Data', 'Code')
        if tag == 'Decide':
            it = self.tyof(k[0], env, line)
            if it not in ('Bool', 'Trit', 'Any'):
                m.err(line, f'`decide` settles true, false or maybe, found {tstr(it)}')
            return 'Bool'
        if tag == 'Instance':
            ae = k[0]
            aname = ae.kids[0] if ae.tag == 'Name' else (ae.kids[0].kids[0] if ae.tag == 'Call' and ae.kids[0].tag == 'Name' else None)
            if aname not in m.answers:
                m.err(line, f'`from` makes an answer instance; {expr_text(ae)} is not an answer')
                return 'Any'
            self.seal_on_instance(aname, line)
            ans = m.answers[aname]
            if ae.tag == 'Call':
                if len(ae.kids[1].kids) != len(ans.params):
                    m.err(line, f'{aname} takes {len(ans.params)} parameter(s), given {len(ae.kids[1].kids)}')
                for a, (pn, pt) in zip(ae.kids[1].kids, ans.params):
                    expect(pt, self.tyof(a, env, line), m, line, f'parameter {pn} of {aname}')
            elif ans.params:
                m.err(line, f'{aname} takes {len(ans.params)} parameter(s), given 0')
            st = self.tyof(k[1], env, line)
            if not fits(ans.takes, st):       # R1: an instance holds a state of the shape its answer takes
                m.err(line, f'{aname} takes a state of type {tstr(ans.takes)}, found {tstr(st)}')
            return ('Inst', aname)
        if tag == 'With':
            inner = self.tyof(k[0], env, line)
            ht = self.tyof(k[1], env, line)
            if isinstance(ht, tuple) and ht[0] == 'Inst' and m.answers_op(ht[1], 'refuse') \
                    and settle(inner) not in ('Unit', 'Any'):
                m.err(line, f'{ht[1]} takes refusals, so what runs inside it may stop short: it must compute '
                            f'(), found {tstr(inner)}')
            return ('Tuple', (inner, ht))
        m.err(line, f'unexpected expression {tag}')
        return 'Any'

    def need_decided(self, ct, line, what):
        if ct == 'Trit':
            self.m.err(line, f'{what} needs a decided condition, and this one can be maybe; '
                             f'say `decide` to settle it')
        elif ct not in ('Bool', 'Any'):
            self.m.err(line, f'{what} needs true or false, found {tstr(ct)}')

    def clause_callee(self, e):
        """If e calls a clause rule, return (rule, param_exprs, input_expr)."""
        m = self.m
        if e.tag != 'Call':
            return None
        f, args = e.kids
        if f.tag == 'Name' and f.kids[0] in m.rules and m.rules[f.kids[0]].kind == 'clauses' \
                and not m.rules[f.kids[0]].params:
            if len(args.kids) != 1:
                return None
            return m.rules[f.kids[0]], [], args.kids[0]
        if f.tag == 'Call' and f.kids[0].tag == 'Name' and f.kids[0].kids[0] in m.rules:
            r = m.rules[f.kids[0].kids[0]]
            if r.kind == 'clauses' and len(args.kids) == 1:
                return r, list(f.kids[1].kids), args.kids[0]
        return None

    def seal_on_instance(self, aname, line):
        m = self.m
        under = m.sealed_by(aname)
        if under is not None and not m.holds_seal(self.place, m.sealed_answers[under]):
            what = f'{aname} is sealed' if under == aname else f'{aname} holds a {under}, which is sealed'
            m.err(line, f'{what}: only the system makes or opens one')

    def check_call_params(self, rule, params, env, line):
        if len(params) != len(rule.params):
            self.m.err(line, f'{rule.name} takes {len(rule.params)} parameter(s), given {len(params)}')
        for (pn, pt), a in zip(rule.params, params):
            at = self.tyof(a, env, line)
            expect(pt, at, self.m, line, f'parameter {pn} of {rule.name}')

    def call_type(self, e, env, line):
        m = self.m
        f, args = e.kids
        cc = self.clause_callee(e)
        if cc is not None:
            rule, params, inp = cc
            self.check_call_params(rule, params, env, line)
            it = self.tyof(inp, env, line)
            expect(rule.takes, it, m, line, f'input of {rule.name}')
            return rule.returns
        if f.tag != 'Name':
            m.err(line, f'cannot call {expr_text(f)}')
            return 'Any'
        n = f.kids[0]
        a = args.kids
        if n in CONVERSIONS:
            if len(a) != 1:
                m.err(line, f'{n}(...) converts one value')
            for x in a:
                self.tyof(x, env, line)
            return n
        if n in WIDENINGS:
            if len(a) != 1:
                m.err(line, f'{n}(...) takes one value')
            for x in a:
                if self.tyof(x, env, line) not in ('Bool', 'Trit', 'Any'):
                    m.err(line, f'{n}(...) takes a Bool or a Trit')
            return n
        if n in m.ctors:
            tn, fs = m.ctors[n]
            if len(a) != len(fs):
                m.err(line, f'{n} has {len(fs)} field(s), given {len(a)}')
            for (fname, ft), x in zip(fs, a):
                expect(ft, self.tyof(x, env, line), m, line, f'field {fname} of {n}')
            return ('Data', tn)
        if n in m.rules:
            r = m.rules[n]
            if r.kind == 'clauses':
                m.err(line, f'{n} is a clause rule: call it as {n}(params)(input)')
                return r.returns
            self.check_call_params(r, list(a), env, line)
            return r.returns
        if n in BUILTINS:
            ts = [None] * len(a)
            if n == 'array':
                if len(a) != 2 or a[0].tag != 'Name':
                    m.err(line, 'array(Type, length) makes a zero-filled array')
                    return 'Any'
                et = m.conv(Form('TypeName', (a[0].kids[0],)), line)
                lt = self.tyof(a[1], env, line)
                if lt not in INTS and lt not in ('Lit', 'Any'):
                    m.err(line, 'an array length must be an integer')
                return ('Array', et)
            ts = [self.tyof(x, env, line) for x in a]
            if n == 'length':
                return 'I64'
            if n in ('bitand', 'bitor', 'bitxor'):
                if len(ts) != 2:
                    m.err(line, f'{n} takes two words')
                    return 'Any'
                return join(ts[0], ts[1], m, line, n)
            if n in ('shift_left', 'shift_right'):
                return ts[0] if ts else 'Any'
            if n in ('sqrt', 'floor'):
                return 'F64'
            if n in ('identity', 'show'):
                return 'Text'
            if n == 'evaluate':
                if ts and ts[0] in (('Data', 'Declaration'), ('Data', 'Program')):
                    m.err(line, '`evaluate` runs an expression; a declaration or a program is not one, and holding it runs nothing')
                return 'Any'
            if n == 'definition':
                return ('Data', 'Declaration')
            if n == 'program':
                if a:
                    m.err(line, '`program()` takes nothing: it is the program as written')
                return ('Data', 'Program')
            if n == 'inverse':
                return ('Data', 'Declaration') if ts and ts[0] == ('Data', 'Declaration') else ('Data', 'Code')
            if n in ('sequence', 'block'):
                # a declaration or a program stays what it is; only the code in it is rewritten
                return ts[0] if ts and ts[0] in (('Data', 'Declaration'), ('Data', 'Program')) else ('Data', 'Code')
            if n == 'Any':
                return 'Any'
        m.err(line, f'unknown rule {n}')
        return 'Any'

    # ---- program ------------------------------------------------------------
    def check_program(self):
        m = self.m
        blocks = [r for r in m.rules.values() if r.kind == 'block']
        for r in blocks:
            r.declared_returns = r.returns != 'Any'
        for attempt in range(3):
            saved = len(m.errors)
            before = [r.returns for r in blocks]
            for r in blocks:
                if not r.declared_returns:
                    r.returns = 'Any' if attempt == 0 else r.returns
                self.check_expr_rule(r, {pn: pt for pn, pt in r.params})
            if attempt < 2 and [r.returns for r in blocks] != before:
                del m.errors[saved:]
                continue
            break
        # Clause rules and answers: iterate classification to a fixpoint
        # (lossiness propagates through moves and sends).
        cands = [r for r in m.rules.values() if r.kind == 'clauses'] + \
            [o for a in m.answers.values() for o in a.ops.values() if o.owner == a.name]
        for r in cands:
            r.cls = 'bijection'
        for _ in range(len(cands) + 2):
            changed = False
            before = {r.name: r.cls for r in cands}
            saved = len(m.errors)
            for r in cands:
                self.check_clause_rule(r, final=False)
            del m.errors[saved:]
            for r in cands:
                if r.cls != before[r.name]:
                    changed = True
            if not changed:
                break
        for r in cands:
            self.check_clause_rule(r, final=True)
        for a in m.answers.values():
            rank = {'bijection': 0, 'partial': 1, 'lossy': 2}
            ops = [(op, m.op_rule(a.name, op)) for op in m.answered_ops(a.name)]
            ops = [(op, o) for op, o in ops if o is not None]
            a.cls = max((o.cls for _, o in ops), key=lambda c: rank.get(c, 2), default='bijection')
            a.reasons = [f'{op}: {x}' for op, o in ops for x in o.reasons]
        self.answer_asks()
        for r in m.rules.values():
            self.check_rows(r)
            if r.kind == 'block':
                self.check_undos(r.block)
        if not m.errors:
            # The checked code becomes the code that runs: uncompute and losses made
            # explicit.  Then every clause rule's inverse is derived by `invert` and
            # checked by this same checker, with nothing special about it.
            for r in cands:
                self.elaborate(r)
            for r in cands:
                self.derive_inverse(r)

    def answer_asks(self):
        """For each answer's request rule, what it can reach by asking: the requests it asks
        itself, and the groups of the rules it calls.  An answer has no row, so this is
        carried to the row of whoever messages or installs it (R6)."""
        m = self.m
        rules = [o for a in m.answers.values() for o in a.ops.values()]
        for o in rules:
            o.asks = (frozenset(), frozenset())
        for _ in range(len(rules) + 1):
            changed = False
            for o in rules:
                asked, groups = set(), set()

                def walk(x, types):
                    if not isinstance(x, Form) or x.tag == 'Quote':
                        return
                    if x.tag == 'Ask' and x.kids[0].kids[0] in m.ops:
                        asked.add(x.kids[0].kids[0])
                    if x.tag == 'Decide' and settle(m.etypes.get(id(x.kids[0]), 'Any')) != 'Bool':
                        groups.add('Decide')
                    if x.tag == 'Call':
                        cc = self.clause_callee(x)
                        callee = cc[0] if cc else (m.rules.get(x.kids[0].kids[0]) if x.kids[0].tag == 'Name' else None)
                        if callee is not None:
                            groups.update(g for g in callee.uses if g in m.requests)
                    if x.tag == 'Send' and x.kids[0].tag == 'Name':
                        it = types.get(x.kids[0].kids[0])
                        if isinstance(it, tuple) and it[0] == 'Inst':
                            a2, g2 = m.reach(it[1], x.kids[1].kids[0])
                            asked.update(a2)
                            groups.update(g2)
                    for kid in x.kids:
                        walk(kid, types)
                for c in o.clauses:
                    walk(c.kids[2], o.var_types.get(id(c), {}))
                new = (frozenset(asked), frozenset(groups))
                if new != o.asks:
                    o.asks, changed = new, True
            if not changed:
                break

    # ---- elaboration and inversion --------------------------------------------
    def elaborate(self, r):
        m = self.m
        params = {pn for pn, _ in r.params}
        new = []
        for c in r.clauses:
            left, right, steps = c.kids
            taken = names_in(c) | params
            new.append(Form(c.tag, (left, right, self.elab_block(steps, taken)), c.line))
        for src, c in zip(r.clauses, new):
            m.elaborated[id(src)] = c
        r.source_clauses = r.clauses
        r.clauses = new
        saved = len(m.errors)
        r.var_types = {}
        for c in r.clauses:
            self.walk_clause(r, c, [], final=True)
        left_over = [b for b in self.blocks_of(r) if m.auto.get(id(b))]
        if len(m.errors) > saved or left_over:
            raise CheckError(f'internal: the elaborated code of {r.name} does not check: '
                             f'{m.errors[saved:] or "implicit uncompute left"}')

    def elab_block(self, b, taken):
        m = self.m
        after = {}
        for d, last, names in m.auto.get(id(b), ()):
            s = b.kids[d]
            after.setdefault(last, []).append((d, Form('Was', s.kids, s.line)))
        out = []
        for idx, s in enumerate(b.kids):
            out += self.elab_step(s, taken)
            for _, u in sorted(after.get(idx, []), key=lambda x: -x[0]):
                out.append(u)
        return Form('Block', tuple(out), b.line)

    def elab_step(self, s, taken):
        t, k, line = s.tag, s.kids, s.line
        if t == 'Set':
            value, under = k[1], self.m.set_as.get(id(s))
            if under is not None:
                value = Form('Call', (Form('Name', (under,), line), Form('Tuple', (value,), line)), line)
            return exchange_and_discard(k[0], value, taken, line)
        if t in ('AddTo', 'SubtractFrom') and id(s) in self.m.rounding:
            e, target = k
            new = Form('Add' if t == 'AddTo' else 'Subtract', (target, e), line)
            return exchange_and_discard(target, new, taken, line)
        if t == 'If':
            return [Form('If', (k[0], self.elab_block(k[1], taken), self.elab_block(k[2], taken)), line)]
        if t in ('RepeatWith', 'RepeatDown'):
            return [Form(t, k[:3] + (self.elab_block(k[3], taken),), line)]
        return [s]

    def blocks_of(self, r):
        out = []

        def walk(x):
            if isinstance(x, Form):
                if x.tag == 'Block':
                    out.append(x)
                for kid in x.kids:
                    walk(kid)
        for c in r.clauses:
            walk(c.kids[2])
        return out

    def derive_inverse(self, r):
        m = self.m
        inv = RuleInfo(flip_name(r.name), r.decl)
        inv.kind, inv.is_answer, inv.op, inv.owner = 'clauses', r.is_answer, r.op, r.owner
        inv.place = r.place
        inv.params, inv.uses, inv.group = r.params, r.uses, r.group
        inv.takes, inv.returns = (r.takes, r.returns) if r.is_answer else (r.returns, r.takes)
        inv.clauses = [invert_clause(c) for c in r.clauses]
        # a value taken back has the type it had when it was discarded
        inv.restored = {id(ic): dict(r.var_types.get(id(c), {})) for ic, c in zip(inv.clauses, r.clauses)}
        inv.line = r.line
        saved = len(m.errors)
        self.check_clause_rule(inv, final=True)
        undecided = len(m.errors) > saved and all(UNDECIDED in e for e in m.errors[saved:])
        if undecided:
            # read backward, the rule would put a Trit where a Bool is declared: a refusal of the
            # rule as written, with its reason, and not a failure of the toolchain
            found = sorted({e.split(': ', 1)[1] for e in m.errors[saved:]})
            del m.errors[saved:]
            m.err(r.line, f'{r.name} cannot be read backward: its inverse has a ' + '; '.join(found))
        elif len(m.errors) > saved:
            raise CheckError(f'internal: the inverse of {r.name} does not check: {m.errors[saved:]}')
        if not undecided and ((inv.cls == 'lossy') != (r.cls == 'lossy')
                              or [b for b in self.blocks_of(inv) if m.auto.get(id(b))]):
            raise CheckError(f'internal: the inverse of {r.name} classifies as {inv.cls}, {r.name} as {r.cls}')
        inv.source_clauses = inv.clauses
        r.inverse, inv.inverse = inv, r

    def check_undos(self, x):
        if not isinstance(x, Form):
            return
        if x.tag == 'Undo':
            cc = self.clause_callee(x.kids[0])
            if cc is not None and cc[0].cls == 'lossy':
                self.m.err(x.line, f'`undo` needs a certified rule; {cc[0].name} is lossy ({cc[0].reasons[0]})')
        if x.tag == 'Quote':
            return
        for k in x.kids:
            self.check_undos(k)

    # ---- expression rules -----------------------------------------------------
    def check_expr_rule(self, r, env):
        # the row says which: a function recomputes from its parameters alone; a procedure
        # from its parameters together with the world replies it kept
        r.cls = 'function' if not r.uses else 'procedure'
        self.place = r.place
        env = dict(env)
        t = self.check_block_expr(r.block, env, r, toplevel=True)
        if not getattr(r, 'declared_returns', True):
            r.returns = settle(t)
        else:
            expect(r.returns, t, self.m, r.line, f'result of {r.name}')
        r.var_types[id(r)] = env

    def check_block_expr(self, b, env, r, toplevel=False):
        result = 'Unit'
        n = len(b.kids)
        for i, s in enumerate(b.kids):
            last = i == n - 1
            result = self.check_stmt_expr(s, env, r, last)
        return result

    def bind_pattern(self, pat, t, env, line, owned_ok=True):
        m = self.m
        if not is_pattern(pat, m):
            m.err(line, f'{expr_text(pat)} is not a pattern')
            return
        tag = pat.tag
        if tag == 'Name':
            n = pat.kids[0]
            if is_ctor_name(n, m):
                return
            env[n] = settle(t)
            m.etypes[id(pat)] = settle(t)
        elif tag == 'Tuple':
            if isinstance(t, tuple) and t[0] == 'Tuple' and len(t[1]) == len(pat.kids):
                for x, tt in zip(pat.kids, t[1]):
                    self.bind_pattern(x, tt, env, line)
            elif not (t == 'Unit' and not pat.kids):
                if t not in ('Any',):
                    m.err(line, f'cannot match {expr_text(pat)} against {tstr(t)}')
                for x in pat.kids:
                    self.bind_pattern(x, 'Any', env, line)
            m.etypes[id(pat)] = t
        elif tag == 'Call':
            c = pat.kids[0].kids[0]
            fts = [ft for _, ft in m.ctors[c][1]] if c in m.ctors else ['Any'] * len(pat.kids[1].kids)
            for x, tt in zip(pat.kids[1].kids, fts):
                self.bind_pattern(x, tt, env, line)
            m.etypes[id(pat)] = ('Data', m.ctors[c][0]) if c in m.ctors else 'Any'
        elif tag == 'Literal':
            self.tyof(pat, env, line)

    def check_stmt_expr(self, s, env, r, last):
        m, tag, k, line = self.m, s.tag, s.kids, s.line
        if tag == 'Let':
            t = self.tyof(k[1], env, line)
            for n in pattern_vars(k[0], m):
                if n in dict(r.params):
                    m.err(line, f'{n} is a parameter; parameters are read, never rebound')
                elif n in env:
                    # one rule for every binding: a name is bound once where it can be seen
                    m.err(line, f'{n} is already bound; `set` overwrites it, and another value takes another name')
            self.bind_pattern(k[0], t, env, line)
            return 'Unit'
        if tag in ('AddTo', 'SubtractFrom', 'Set'):
            target, e = (k[1], k[0]) if tag != 'Set' else (k[0], k[1])
            self.check_target(target, env, r, line, write=True)
            tt = self.tyof(target, env, line)
            et = self.tyof(e, env, line)
            expect(tt, et, m, line, 'update')
            if tag != 'Set':
                self.r4(s, target, e, line)
            return 'Unit'
        if tag == 'Swap':
            self.check_target(k[0], env, r, line, write=True)
            self.check_target(k[1], env, r, line, write=True)
            alike(self.tyof(k[0], env, line), self.tyof(k[1], env, line), m, line, 'swap')
            return 'Unit'
        if tag == 'Was':
            pat, rhs = k
            if rhs.tag in ('Send', 'Ask', 'Decide', 'Instance') or self.clause_callee(rhs):
                m.err(line, '`was` in an expression rule releases a value it can recompute; '
                            'backward requests belong to clause rules')
                return 'Unit'
            t = self.tyof(rhs, env, line)
            for n in pattern_vars(pat, m):
                if n not in env:
                    m.err(line, f'{n} is not bound here')
                else:
                    del env[n]
            return 'Unit'
        if tag == 'Restore':
            m.err(line, '`was discarded` takes back what was kept, which belongs to clause rules and to the system')
            return 'Unit'
        if tag == 'Discard':
            if k[0] in dict(r.params):
                m.err(line, f'{k[0]} is a parameter; parameters are read, never discarded')
            elif k[0] not in env:
                m.err(line, f'unknown name {k[0]}')
            return 'Unit'
        if tag == 'Output':
            self.tyof(k[0], env, line)
            return 'Unit'
        if tag == 'Commit':
            return 'Unit'
        if tag == 'If':
            ct = self.tyof(k[0], env, line)
            self.need_decided(ct, line, '`if`')
            e1, e2 = dict(env), dict(env)
            t1 = self.check_block_expr(k[1], e1, r)
            t2 = self.check_block_expr(k[2], e2, r) if k[2].kids else 'Unit'
            if last and k[2].kids:
                return join(t1, t2, m, line, 'the branches of `if`')
            return 'Unit'
        if tag == 'RepeatWhile':
            ct = self.tyof(k[0], env, line)
            self.need_decided(ct, line, '`repeat while`')
            self.check_block_expr(k[1], dict(env), r)
            return 'Unit'
        if tag in ('RepeatWith', 'RepeatDown'):
            var, lo, hi, body = k
            t = settle(join(self.tyof(lo, env, line), self.tyof(hi, env, line), m, line, 'loop bounds'))
            if var in env or var in dict(r.params):
                m.err(line, f'{var} is already bound; a loop takes a counter of its own')
            e2 = dict(env)
            e2[var] = t
            m.etypes[id(s)] = t
            self.check_block_expr(body, e2, r)
            return 'Unit'
        if tag == 'Do':
            return self.tyof(k[0], env, line)
        m.err(line, f'unexpected statement {tag}')
        return 'Unit'

    def check_target(self, target, env, r, line, write):
        p = path_of(target)
        if p is None:
            self.m.err(line, f'{expr_text(target)} cannot be updated')
            return
        if p[0] in dict(r.params):
            self.m.err(line, f'{p[0]} is a parameter; parameters are read, never updated')
        elif p[0] not in env:
            self.m.err(line, f'unknown name {p[0]}')

    def r4(self, s, target, e, line):
        """R4: an update may read anything except its own target."""
        tp = path_of(target)
        checks = []
        for rp in read_paths(e):
            if rp[0] != tp[0]:
                continue
            n = min(len(rp), len(tp))
            disjoint, unknown = False, []
            for a, b in zip(rp[1:n], tp[1:n]):
                if a[0] == '.' and b[0] == '.':
                    if a[1] != b[1]:
                        disjoint = True
                        break
                elif a[0] == '[]' and b[0] == '[]':
                    rel = index_relation(a[1], b[1])
                    if rel == 'different':
                        disjoint = True
                        break
                    if rel == 'unknown':
                        unknown.append((b[1], a[1]))
            if disjoint:
                continue
            if len(rp) < len(tp) or not unknown:
                self.m.err(line, f'R4: the update reads its own target {expr_text(target)}; '
                                 f'use `set` for an overwrite')
                return
            checks += unknown
        if checks:
            self.m.alias_checks[id(s)] = checks

    def r4_targets(self, targets, line):
        """R4, for the cells a step changes: the index that selects a cell may not read
        anything the step changes, or the backward reading would select another cell.
        Reading only the length of an array whose elements change is allowed."""
        paths = [(t, path_of(t)) for t in targets]
        changed = {}      # root -> True when the whole value may change (so its length may too)
        for t, p in paths:
            if p is not None:
                whole = not any(c[0] == '[]' for c in p[1:])
                changed[p[0]] = changed.get(p[0], False) or whole
        for t, p in paths:
            for c in (p[1:] if p is not None else ()):
                if c[0] != '[]':
                    continue
                names, by_length = free_names(c[1]), length_only_names(c[1])
                for root, whole in changed.items():
                    if root in names and (whole or root not in by_length):
                        self.m.err(line, f'R4: the index of {expr_text(t)} reads {root}, which this step '
                                         f'changes, so the step cannot be read backward')
                        return

    # ---- clause rules -------------------------------------------------------------
    def check_clause_rule(self, r, final):
        m = self.m
        self.place = r.place
        reasons = []
        lefts, rights = [], []
        for c in r.clauses:
            left, right, steps = c.kids
            if not is_pattern(left, m):
                m.err(c.line, f'left side {expr_text(left)} is not a pattern')
                continue
            if not is_pattern(right, m):
                m.err(c.line, f'right side {expr_text(right)} is not a pattern; compute values in `where`')
                continue
            lefts.append(absp(left, m))
            rights.append(absp(right, m))
            self.walk_clause(r, c, reasons, final)
        left_overlap = [(i + 1, j + 1) for i in range(len(lefts)) for j in range(i + 1, len(lefts))
                        if overlap(lefts[i], lefts[j])]
        right_overlap = [(i + 1, j + 1) for i in range(len(rights)) for j in range(i + 1, len(rights))
                         if overlap(rights[i], rights[j])]
        if left_overlap:
            a, b = left_overlap[0]
            reasons.append(f'left sides of clauses {a} and {b} overlap, so the first match decides')
        if right_overlap:
            a, b = right_overlap[0]
            reasons.append(f'right sides of clauses {a} and {b} overlap, so the clause choice is lost')
        r.journal_choice = bool(left_overlap or right_overlap) and len(r.clauses) > 1
        r.first_match_decides = bool(left_overlap)     # then the order of the clauses is part of the rule
        in_t = r.takes if not r.is_answer else 'Any'
        if r.is_answer and r.op in m.ops and lefts:
            # one request per rule: exhaustive over its fields (or, read backward, its reply) and the state
            pts, ret = m.requests[m.ops[r.op]][r.op]
            if r.backward:
                in_t = ('Tuple', (ret, r.takes))
            else:
                in_t = ('Tuple', (('Tuple', tuple(pt for _, pt in pts)), r.takes))
                lefts = [('tuple', 2, ((('tuple', len(p[2][0][2]), p[2][0][2]) if p[2][0] != WILD else WILD),
                                       p[2][1])) if p != WILD and p[0] == 'tuple' else p for p in lefts]
        r.left_exhaustive = self.ex.exhaustive(lefts, in_t) if lefts else False
        reasons[:] = list(dict.fromkeys(reasons))
        r.reasons = reasons
        if reasons:
            r.cls = 'lossy'
        else:
            r.cls = 'bijection' if r.left_exhaustive else 'partial'
        if final and not r.backward:
            arrows = {c.tag for c in r.clauses}
            if len(arrows) > 1:
                m.err(r.line, f'{r.name} mixes `<->` and `=>`; the certificate belongs to the rule, so every '
                              f'clause carries the same arrow')
            elif r.cls == 'lossy' and arrows == {'Clause'}:
                m.err(r.line, f'{r.name} is lossy ({reasons[0]}); a lossy rule writes `=>`')
            elif r.cls != 'lossy' and arrows == {'LossyClause'}:
                m.err(r.line, f'{r.name} is certified (a {r.cls}); a certified rule writes `<->`')

    def walk_clause(self, r, c, reasons, final):
        m = self.m
        left, right, steps = c.kids
        env_types = {pn: pt for pn, pt in r.params}
        params = set(env_types)
        live = {}
        in_t = r.takes
        if r.is_answer:
            # (request, state) <-> (reply, state): the request's fields take the types its
            # group declares; read backward, the reply takes the request's reply type
            in_t = 'Any'
            if left.tag == 'Tuple' and len(left.kids) == 2:
                req = left.kids[0]
                if r.backward and r.op in m.ops:
                    self.bind_pattern(req, m.requests[m.ops[r.op]][r.op][1], env_types, c.line)
                elif req.tag == 'Call' and req.kids[0].kids[0] in m.ops:
                    op = req.kids[0].kids[0]
                    pts = m.requests[m.ops[op]][op][0]
                    for a, (_, pt) in zip(req.kids[1].kids, pts):
                        self.bind_pattern(a, pt, env_types, c.line)
                self.bind_pattern(left.kids[1], r.takes, env_types, c.line)
        else:
            self.bind_pattern(left, in_t, env_types, c.line)
        for n in pattern_vars(left, m):
            if n in params:
                m.err(c.line, f'{n} is a parameter and cannot be bound by a clause')
            if n in live:
                m.err(c.line, f'{n} is bound twice on the left side')
            live[n] = Var('input', env_types.get(n, 'Any'))
        ctx = {'r': r, 'params': params, 'types': env_types, 'reasons': reasons, 'final': final, 'clause': c}
        self.walk_block(steps, live, ctx)
        # the right side consumes
        seen = set()
        for n in pattern_vars(right, m):
            if n in seen:
                m.err(c.line, f'{n} appears twice on the right side; bind a second name with `is`')
            seen.add(n)
            if n not in live:
                if n in params:
                    m.err(c.line, f'{n} is a parameter; a clause builds its right side from what it owns')
                else:
                    m.err(c.line, f'{n} is not available for the right side (never bound, or already consumed)')
                continue
            del live[n]
        if r.is_answer and r.backward and right.tag == 'Tuple' and len(right.kids) == 2:
            self.tyof(right.kids[1], env_types, c.line)   # the request side is a pattern of the group's
        else:
            self.tyof(right, env_types, c.line)
        rt = m.etypes.get(id(right), 'Any')
        if r.is_answer and r.op in m.ops and right.tag == 'Tuple' and len(right.kids) == 2:
            # an answer's right side: its reply (read backward, its request) and its state (R1)
            pts, ret = m.requests[m.ops[r.op]][r.op]
            req, state = right.kids
            st = m.etypes.get(id(state), 'Any')
            expect(r.takes, st, m, c.line, f'the state of {r.name}')
            if not r.backward:
                expect(ret, m.etypes.get(id(req), 'Any'), m, c.line, f'the reply of {r.name}')
            elif req.tag == 'Call' and len(req.kids[1].kids) == len(pts):
                for a, (pn, pt) in zip(req.kids[1].kids, pts):
                    expect(pt, self.tyof(a, env_types, c.line), m, c.line, f'argument {pn} of {r.op}')
        if r.returns != 'Any' and not r.is_answer:
            expect(r.returns, rt, m, c.line, f'right side of {r.name}')
        self.finish_block(steps, live, ctx, top=True)
        r.var_types[id(c)] = env_types
        if r.is_answer and not r.backward and final:
            self.check_withdrawal(r, c, ctx)

    def check_withdrawal(self, r, c, ctx):
        """E8 (VII.2): a host that gives its copy back keeps nothing of it.  In a clause of an
        answer that takes back its own outward ask, what that ask returned, and whatever is
        computed from it or decided by it, may reach the reply and nothing else: not the
        answer's state, a message, another request, a decision that may reach the world, or
        the journal.  Otherwise the answers further out would be restored while this one kept
        what they disclosed."""
        m = self.m
        left, right, steps = c.kids
        op = r.op

        def inquiry(rhs):
            return rhs.tag == 'Ask' and rhs.kids[0].kids[0] == op

        def all_steps(b):
            for x in b.kids:
                yield x
                for k in x.kids:
                    if isinstance(k, Form) and k.tag == 'Block':
                        yield from all_steps(k)
        if not any(x.tag == 'Was' and inquiry(x.kids[1]) for x in all_steps(steps)):
            return
        taint = set()
        worldly = ctx.get('worldly', set())

        def refuse(line, what):
            m.err(line, f'{r.owner} gives back the copy {op} disclosed, and {what}; a host that gives '
                        f'its copy back keeps nothing of it')

        def flows(src, dst, under):
            if under or src & taint:
                taint.update(dst)

        def step(x, under):
            t, k, line = x.tag, x.kids, x.line
            if t in ('Let', 'Was'):
                pat, rhs = k
                if inquiry(rhs):
                    if t == 'Let':
                        taint.update(pattern_vars(pat, m))
                    return
                if rhs.tag == 'Ask':
                    if under or free_names(rhs) & taint:
                        refuse(line, f'asks {rhs.kids[0].kids[0]} with what it read')
                    return
                if rhs.tag == 'Send':
                    if under or set().union(*[free_names(a) for a in rhs.kids[1].kids[1].kids]) & taint:
                        refuse(line, f'sends what it read to {expr_text(rhs.kids[0])}')
                    return
                if rhs.tag == 'Decide':
                    if id(x) in worldly and (under or free_names(rhs.kids[0]) & taint):
                        refuse(line, 'asks for a decision about what it read')
                    if t == 'Let':
                        flows(free_names(rhs.kids[0]), set(pattern_vars(pat, m)), under)
                    return
                inner = rhs.kids[0] if rhs.tag == 'Undo' else rhs
                cc = self.clause_callee(inner)
                if t == 'Let':
                    src, dst = free_names(rhs), set(pattern_vars(pat, m))
                elif cc is not None and is_pattern(cc[2], m):
                    src = set(pattern_vars(pat, m)).union(*[free_names(p_) for p_ in cc[1]])
                    dst = set(pattern_vars(cc[2], m))
                elif rhs.tag == 'Instance' and is_pattern(rhs.kids[1], m):
                    src = set(pattern_vars(pat, m)) | free_names(rhs.kids[0])
                    dst = set(pattern_vars(rhs.kids[1], m))
                else:
                    return
                if cc is not None and cc[0].cls == 'lossy' and (under or src & taint):
                    refuse(line, f'keeps what it read through {cc[0].name}, which is lossy')
                flows(src, dst, under)
            elif t == 'Discard':
                if under or k[0] in taint:
                    refuse(line, f'keeps what it read (`discard {k[0]}`)')
            elif t in ('AddTo', 'SubtractFrom'):
                flows(free_names(k[0]), free_names(k[1]), under)
            elif t == 'Set':
                flows(free_names(k[1]), free_names(k[0]), under)
            elif t == 'Swap':
                both = free_names(k[0]) | free_names(k[1])
                flows(both, both, under)
            elif t == 'If':
                inside = under or bool(free_names(k[0]) & taint)
                block(k[1], inside)
                if len(k) > 2 and isinstance(k[2], Form):
                    block(k[2], inside)
            elif t in ('RepeatWith', 'RepeatDown', 'RepeatWhile'):
                bounds = set().union(*[free_names(e) for e in k[:-1] if isinstance(e, Form)])
                inside = under or bool(bounds & taint)
                while True:            # what one iteration taints, the next may carry further
                    n = len(taint)
                    block(k[-1], inside)
                    if len(taint) == n:
                        break

        def block(b, under):
            for x in b.kids:
                step(x, under)
        block(steps, False)
        if right.tag == 'Tuple' and len(right.kids) == 2 and set(pattern_vars(right.kids[1], m)) & taint:
            refuse(c.line, 'keeps what it read in its state')

    def finish_block(self, block, live, ctx, top):
        """Resolve variables still live at the end of a block (Bennett uncompute)."""
        m = self.m
        info = ctx.get(('block', id(block)))
        autos = []
        if info:
            temps = {n: v for n, v in live.items() if v.kind == 'temp' and v.block is block}
            changed = True
            while changed:
                changed = False
                for n, v in temps.items():
                    for src in v.reads & set(temps):
                        mine = info['lastuse'].get(n, v.defstep)
                        if info['lastuse'].get(src, temps[src].defstep) < mine:
                            info['lastuse'][src] = mine
                            changed = True
        for n, v in list(live.items()):
            if v.block is not block and not top:
                continue
            if v.kind == 'temp' and v.block is block:
                writes = info['writes'] if info else []
                last = info['lastuse'].get(n, v.defstep) if info else v.defstep
                bad = v.modified
                for idx in range(v.defstep + 1, last + 1):
                    if writes[idx] & (v.reads | {n}):
                        bad = True
                if not bad:
                    autos.append((v.defstep, last, n))
                    del live[n]
                    continue
                m.err(None if not info else info['lines'][v.defstep],
                      f'{n} is neither returned nor discarded, and it cannot be uncomputed '
                      f'because what it was computed from changes before its last use')
                del live[n]
            elif top:
                kind = {'input': 'bound on the left side', 'result': 'a result'}.get(v.kind, v.kind)
                m.err(ctx['r'].line, f'in {ctx["r"].name}: {n} ({kind}) is lost; '
                                     f'return it on the right side or `discard` it')
                del live[n]
        # group autos by defining step; a line is uncomputed whole
        grouped = {}
        for d, last, n in autos:
            g = grouped.setdefault(d, [d, last, []])
            g[1] = max(g[1], last)
            g[2].append(n)
        for d, last, names in grouped.values():
            s = block.kids[d]
            if s.tag == 'Let' and set(pattern_vars(s.kids[0], m)) != set(names):
                m.err(s.line, 'bind each temporary on its own line, so it can be uncomputed')
        m.auto[id(block)] = [tuple(x) for x in grouped.values()]

    def walk_block(self, block, live, ctx):
        info = {'writes': [], 'lastuse': {}, 'lines': [], 'shape': set()}
        ctx[('block', id(block))] = info
        for idx, s in enumerate(block.kids):
            reads, writes = self.walk_step(s, idx, block, live, ctx)
            info['writes'].append(writes)
            info['shape'] |= ctx.pop('_shape', set())
            info['lines'].append(s.line)
            for n in reads:
                if n in live and live[n].block is block:
                    info['lastuse'][n] = idx
        return info

    def drop_plan(self, n, v, idx, block, ctx):
        """What a dropped value is charged for (VII.5): its type; how many constructors it may
        still have, where the clause shows that; and whether it can still be computed from
        what remains, in which case dropping it loses nothing."""
        m = self.m
        t = settle(ctx['types'].get(n, v.ty))
        info = ctx.get(('block', id(block)))
        # the test of a proved uncompute (O5): bound in this block from an expression, and
        # nothing that expression read, nor the name itself, has changed since
        again = bool(info and v.kind == 'temp' and v.block is block and v.rhs is not None and not v.modified
                     and v.pat is not None and v.pat.tag == 'Name'
                     and not any(info['writes'][i] & (v.reads | {n}) for i in range(v.defstep + 1, idx)))
        top = None
        if isinstance(t, tuple) and t[0] == 'Data' and t[1] in m.types and t[1] != 'Code' and not v.modified:
            ctors = m.types[t[1]].ctors
            rhs = v.rhs
            made = rhs.kids[0].kids[0] if rhs is not None and rhs.tag == 'Call' and rhs.kids[0].tag == 'Name' else \
                rhs.kids[0] if rhs is not None and rhs.tag == 'Name' else None
            c, r = ctx.get('clause'), ctx['r']
            if v.kind == 'temp' and v.pat is not None and v.pat.tag == 'Name' and made in ctors:
                top = 1                          # made here, by this constructor
            elif v.kind == 'input' and c is not None:
                # bound by the left side: a constructor is not possible where one earlier
                # clause takes every input of this clause that has it there
                at = path_to(c.kids[0], n)
                earlier = []
                for other in r.clauses:
                    if other is c:
                        break
                    if is_pattern(other.kids[0], m):
                        earlier.append(absp(other.kids[0], m))
                else:
                    earlier = []
                if at is not None and earlier:
                    mine = absp(c.kids[0], m)
                    left = [k for k, fs in ctors.items()
                            if not any(covers(e, put_at(mine, at, ('ctor', k, (WILD,) * len(fs)))) for e in earlier)]
                    if 0 < len(left) < len(ctors):
                        top = len(left)
        return t, top, again

    def reads_of(self, e, live, ctx, line):
        """Names an expression reads; checks they are available."""
        m = self.m
        out = set()
        for n in free_names(e):
            if n in live:
                out.add(n)
            elif n in ctx['params'] or n in m.ctors or n in m.rules or n in BUILTINS \
                    or n in CONVERSIONS or n in WIDENINGS or n in m.answers or n in m.ops or n in m.types:
                continue
            else:
                m.err(line, f'{n} is not available here (never bound, or already consumed)')
        return out

    def check_pure(self, e, line):
        """Inside a clause, requests and consuming calls go on their own line."""
        m = self.m
        bad = []

        def walk(x, top):
            if not isinstance(x, Form):
                return
            if x.tag in ('Send', 'Ask', 'With', 'Decide') or (x.tag == 'Instance'):
                bad.append(x)
                return
            if x.tag == 'Quote':
                return
            if x.tag in ('Call', 'Undo') and not top and self.clause_callee(x.kids[0] if x.tag == 'Undo' else x):
                bad.append(x)
                return
            if x.tag == 'Call' and x.kids[0].tag == 'Name' and x.kids[0].kids[0] in m.rules:
                callee = m.rules[x.kids[0].kids[0]]
                if callee.kind == 'block' and callee.uses:
                    m.err(line, f'{callee.name} is a procedure (it uses {", ".join(sorted(callee.uses))}), so its '
                                f'result cannot be recomputed from its parameters; a step calls functions')
            for k in x.kids:
                walk(k, False)
        for k in e.kids:
            walk(k, False)
        for x in bad:
            m.err(line, f'{expr_text(x)} must stand on its own line as `pattern is ...`')

    def walk_step(self, s, idx, block, live, ctx):
        m, tag, k, line = self.m, s.tag, s.kids, s.line
        r, reasons, types = ctx['r'], ctx['reasons'], ctx['types']
        reads, writes = set(), set()
        shape = set()
        ctx['_shape'] = shape

        def consume_pattern(p):
            for n in pattern_vars(p, m):
                if n in live:
                    del live[n]
                    writes.add(n)
                    shape.add(n)
                elif n in ctx['params']:
                    m.err(line, f'{n} is a parameter and cannot be consumed')
                else:
                    m.err(line, f'{n} is not available (never bound, or already consumed)')

        def bind(p, kind, t, rd=frozenset()):
            self.bind_pattern(p, t, types, line)
            for n in pattern_vars(p, m):
                if n in live:
                    m.err(line, f'{n} is still live; return, discard or consume it before rebinding')
                if n in ctx['params']:
                    m.err(line, f'{n} is a parameter; parameters are read, never rebound')
                live[n] = Var(kind, types.get(n, 'Any'), frozenset(rd), idx, block)

        if tag in ('Let', 'Was'):
            # `p is e` and its backward reading `p was e`: one walk, two directions.  Read
            # forward, a step consumes what e takes and binds p; backward, it consumes p
            # and gives back what e took.
            back = tag == 'Was'
            pat, rhs = k
            if not is_pattern(pat, m):
                m.err(line, f'{expr_text(pat)} is not a pattern')
                return reads, writes
            inner = rhs.kids[0] if rhs.tag == 'Undo' else rhs
            cc = self.clause_callee(inner)
            if cc is not None:
                rule, params, inp = cc
                if rhs.tag == 'Undo' and not back and rule.cls == 'lossy':
                    m.err(line, f'`undo` needs a certified rule; {rule.name} is lossy')
                elif rule.cls == 'lossy':
                    reasons.append(f'it {"takes back" if back else "consumes through"} {rule.name}, which is lossy')
                consumed = set(pattern_vars(pat if back else inp, m)) if is_pattern(inp, m) else set()
                for p_ in params:
                    self.check_pure(p_, line)
                    rd = self.reads_of(p_, live, ctx, line)
                    if rd & consumed:
                        m.err(line, f'R4: a parameter of {rule.name} reads {sorted(rd & consumed)[0]}, which the '
                                    f'call consumes, so the call cannot be read backward')
                    reads |= rd
                if not is_pattern(inp, m):
                    m.err(line, f'the input to {rule.name} must be a pattern of names it consumes')
                if back:
                    consume_pattern(pat)
                    bind(inp, 'result', rule.returns if rhs.tag == 'Undo' else rule.takes)
                else:
                    t = self.tyof(rhs, types, line)
                    consume_pattern(inp)
                    bind(pat, 'result', t)
            elif rhs.tag in ('Send', 'Ask', 'Decide'):
                if rhs.tag == 'Send':
                    target = rhs.kids[0]
                    if target.tag != 'Name' or target.kids[0] not in live:
                        m.err(line, 'a message goes to an answer instance this clause owns')
                    else:
                        writes.add(target.kids[0])
                        shape.add(target.kids[0])
                        live[target.kids[0]].modified = True
                    args = rhs.kids[1].kids[1].kids
                elif rhs.tag == 'Ask':
                    args = rhs.kids[0].kids[1].kids
                else:
                    args = [Form('Tuple', (rhs.kids[0],))]
                for a in args:
                    self.check_pure(a, line)
                    rd = self.reads_of(a, live, ctx, line)
                    if rhs.tag == 'Send' and target.tag == 'Name' and target.kids[0] in rd:
                        m.err(line, 'a message cannot read the instance it is sent to')
                    reads |= rd
                t = self.tyof(rhs, types, line)
                if rhs.tag == 'Send':
                    it = types.get(target.kids[0]) if target.tag == 'Name' else None
                    op = rhs.kids[1].kids[0]
                    opr = m.op_rule(it[1], op) if isinstance(it, tuple) and it[0] == 'Inst' else None
                    if opr is None or opr.cls == 'lossy':
                        reasons.append(f'it sends {op} to an answer that answers it lossily or is unknown')
                elif rhs.tag == 'Ask':
                    reasons.append('it asks outside itself, so its reply is world input')
                    asked = rhs.kids[0].kids[0]
                    if r.is_answer and asked == r.op and not m.passes_outward(asked):
                        m.err(line, f'{r.owner} asks {asked} while it is answering {asked}; an answer passes its '
                                    f'request outward only where a sealed answer gives the final reply')
                elif settle(self.tyof(rhs.kids[0], types, line)) != 'Bool':
                    # statically crisp (a Bool) never leaves the program; a Trit may
                    reasons.append('it decides, and a decision about maybe is world input')
                    ctx.setdefault('worldly', set()).add(id(s))
                if back:
                    consume_pattern(pat)
                else:
                    bind(pat, 'result', t)
            elif rhs.tag == 'Instance' and is_pattern(rhs.kids[1], m) and \
                    (back or any(n in live for n in pattern_vars(rhs.kids[1], m))):
                ae = rhs.kids[0]
                aname = ae.kids[0] if ae.tag == 'Name' else ae.kids[0].kids[0]
                packed = set(pattern_vars(rhs.kids[1], m))
                self.seal_on_instance(aname, line)
                if ae.tag == 'Call':
                    for a in ae.kids[1].kids:
                        rd = self.reads_of(a, live if not back else {**live, **{n: None for n in packed}}, ctx, line)
                        if rd & packed:
                            m.err(line, f'R4: a parameter of {aname} reads {sorted(rd & packed)[0]}, which the '
                                        f'instance takes as its state, so the step cannot be read backward')
                        reads |= rd
                if back:   # unpack: the instance goes, its state comes back
                    consume_pattern(pat)
                    bind(rhs.kids[1], 'result', m.answers[aname].takes if aname in m.answers else 'Any')
                else:
                    t = self.tyof(rhs, types, line)
                    consume_pattern(rhs.kids[1])
                    bind(pat, 'result', t)
            elif rhs.tag == 'With':
                m.err(line, '`with` is available in expression rules in this build')
            else:
                self.check_pure(Form('Tuple', (rhs,)), line)
                rd = self.reads_of(rhs, live, ctx, line)
                reads |= rd
                t = self.tyof(rhs, types, line)
                if not back:
                    bind(pat, 'temp', t, rd)
                    for n in pattern_vars(pat, m):
                        live[n].rhs, live[n].pat = rhs, pat
                else:
                    pt = self.tyof(pat, types, line)
                    if widens(pt, t):
                        m.err(line, f'type mismatch in `was`: {tstr(pt)} and {tstr(t)} ({UNDECIDED})')
                    mine = set(pattern_vars(pat, m)) & rd
                    if mine:
                        m.err(line, f'`was` gives {", ".join(sorted(mine))} back against an expression that reads it; '
                                    f'what a name is given back against is computed without it')
                    # Proved: the temporary was bound in this block, by this same pattern,
                    # from this same expression, and nothing it read (nor itself) has changed
                    # since (O5).  The check is then redundant at run time.
                    info = ctx.get(('block', id(block)))
                    vs = [(n, live.get(n)) for n in pattern_vars(pat, m)]
                    if info and vs and all(v is not None and v.kind == 'temp' and v.block is block
                                           and v.rhs == rhs and v.pat == pat and not v.modified
                                           and not any(info['writes'][i] & (v.reads | {n})
                                                       for i in range(v.defstep + 1, idx))
                                           for n, v in vs):
                        m.proved.add(id(s))
                    consume_pattern(pat)
        elif tag in ('AddTo', 'SubtractFrom', 'Set'):
            target, e = (k[1], k[0]) if tag != 'Set' else (k[0], k[1])
            p = path_of(target)
            if p is None or p[0] not in live:
                if p and p[0] in ctx['params']:
                    m.err(line, f'{p[0]} is a parameter; parameters are read, never updated')
                else:
                    m.err(line, f'{expr_text(target)} is not owned here, so it cannot be updated')
            else:
                writes.add(p[0])
                if not any(comp[0] == '[]' for comp in p[1:]):
                    shape.add(p[0])
                live[p[0]].modified = True
                for comp in p[1:]:
                    if comp[0] == '[]':
                        reads |= self.reads_of(comp[1], live, ctx, line)
            self.r4_targets([target], line)
            self.check_pure(Form('Tuple', (e,)), line)
            reads |= self.reads_of(e, live, ctx, line)
            tt = self.tyof(target, types, line)
            et = self.tyof(e, types, line)
            expect(tt, et, m, line, 'update')
            if tag == 'Set':
                reasons.append('`set` overwrites, which is an exchange plus a discard')
                # the value is exchanged with the cell, so it is written in the cell's type
                cell = settle(tt)
                if et == 'Lit' and cell in CONVERSIONS and cell != 'I64':
                    m.set_as[id(s)] = cell
                elif et == 'Bool' and cell == 'Trit':
                    m.set_as[id(s)] = 'Trit'
                elif 'Any' not in (tt, et) and settle(et) != cell and not widens(tt, et) and fits(tt, et):
                    m.err(line, f'`set` gives a value of type {tstr(settle(et))} to a cell of type {tstr(cell)}; '
                                f'write the value in the cell\'s type')
            else:
                self.r4(s, target, e, line)
                if tt == 'F64':
                    reasons.append('an update on F64 rounds, so it is an exchange plus a discard')
                    m.rounding.add(id(s))
                elif tt not in INTS and tt != 'Lit':
                    reasons.append(f'an update on {tstr(tt)} is not certified exact')
                    m.rounding.add(id(s))
        elif tag == 'Swap':
            for t in k:
                p = path_of(t)
                if p is None or p[0] not in live:
                    m.err(line, f'{expr_text(t)} is not owned here, so it cannot be swapped')
                else:
                    writes.add(p[0])
                    if not any(comp[0] == '[]' for comp in p[1:]):
                        shape.add(p[0])
                    live[p[0]].modified = True
                    for comp in p[1:]:
                        if comp[0] == '[]':
                            reads |= self.reads_of(comp[1], live, ctx, line)
            self.r4_targets(list(k), line)
            alike(self.tyof(k[0], types, line), self.tyof(k[1], types, line), m, line, 'swap')
        elif tag == 'Restore':
            was = getattr(ctx['r'], 'restored', {}).get(id(ctx.get('clause')), {})
            bind(Form('Name', (k[0],), line), 'result', was.get(k[0], 'Any'))
            reasons.append('it takes back a discarded value, which only the system may do')
        elif tag == 'Discard':
            n = k[0]
            if n not in live:
                m.err(line, f'{n} is not available to discard')
            else:
                m.drops[id(s)] = self.drop_plan(n, live[n], idx, block, ctx)
                del live[n]
                writes.add(n)
                shape.add(n)
            reasons.append(f'it discards {n}')
        elif tag in ('Output', 'Commit'):
            m.err(line, f'`{tag.lower()}` is a commit point, which ends what can be rewound; '
                        f'it belongs in an expression rule, between rule calls')
        elif tag == 'If':
            cond, then, other = k
            self.check_pure(Form('Tuple', (cond,)), line)
            cr = self.reads_of(cond, live, ctx, line)
            reads |= cr
            ct = self.tyof(cond, types, line)
            self.need_decided(ct, line, '`if`')
            before = set(live)
            l1 = dict(live)
            l2 = dict(live)
            i1 = self.walk_block(then, l1, ctx)
            self.finish_block(then, l1, ctx, top=False)
            i2 = self.walk_block(other, l2, ctx)
            self.finish_block(other, l2, ctx, top=False)
            for li in (l1, l2):
                for n in list(li):
                    if n not in before:
                        m.err(line, f'{n} is bound inside a branch and must be consumed there')
            if set(l1) != set(l2):
                m.err(line, 'both branches of `if` must consume the same names')
            w = set().union(*i1['writes'], *i2['writes']) if (i1['writes'] or i2['writes']) else set()
            if w & cr:
                m.err(line, 'the branches may not change what the condition reads, '
                            'so the condition still decides the branch when run backward')
            writes |= w
            shape |= i1['shape'] | i2['shape']
            reads |= set(i1['lastuse']) | set(i2['lastuse'])
            for n in before - set(l1):
                live.pop(n, None)
                writes.add(n)
            for n in before & set(l1):
                if l1[n].modified or l2.get(n, l1[n]).modified:
                    live[n].modified = True
            # names read inside the branches
            for blk in (then, other):
                reads |= self.block_reads(blk) & before
        elif tag in ('RepeatWith', 'RepeatDown'):
            var, lo, hi, body = k
            bounds = [lo, hi]
            br = set()
            br_shape = set()
            for b in bounds:
                self.check_pure(Form('Tuple', (b,)), line)
                br |= self.reads_of(b, live, ctx, line)
                br_shape |= length_only_names(b)
            reads |= br
            t = settle(join(self.tyof(lo, types, line), self.tyof(hi, types, line), m, line, 'loop bounds'))
            types[var] = t
            m.etypes[id(s)] = t
            outer = var in ctx['params']        # a parameter, or the counter of a loop this one is in
            if var in live or outer:
                m.err(line, f'{var} is already bound; a loop takes a counter of its own')
            ctx['params'] = set(ctx['params']) | {var}
            before = set(live)
            lb = dict(live)
            ib = self.walk_block(body, lb, ctx)
            self.finish_block(body, lb, ctx, top=False)
            if not outer:
                ctx['params'] = set(ctx['params']) - {var}
            if set(lb) != before:
                m.err(line, 'a repeated block must leave the same names live (it may update them, '
                            'not consume or create them)')
            w = set().union(*ib['writes']) if ib['writes'] else set()
            if (w & (br - br_shape)) or (ib['shape'] & br_shape):
                m.err(line, 'the loop body may not change what the loop bounds read')
            shape |= ib['shape']
            writes |= w
            for n in before & set(lb):
                if lb[n].modified:
                    live[n].modified = True
            reads |= self.block_reads(body) & before
        elif tag == 'RepeatWhile':
            m.err(line, '`repeat while` has no exit assertion, so it is available in expression rules only')
        elif tag == 'Do':
            m.err(line, 'bind the result with `is`; a clause cannot drop a value silently')
        else:
            m.err(line, f'unexpected step {tag}')
        ctx['_shape'] = shape
        return reads, writes

    def block_reads(self, block):
        out = set()
        for s in block.kids:
            for k in s.kids:
                if isinstance(k, Form):
                    out |= free_names(k)
                elif isinstance(k, str):
                    out.add(k)
        return out

    # ---- rows (R6) --------------------------------------------------------------
    def check_rows(self, r):
        """R6: a rule's row names every request group it reaches.  An expression rule has no
        arrow, so its row also says when it reaches `keep`: it lists System when it calls a
        lossy rule, messages or installs an answer with a lossy request rule, or settles a
        condition that may be maybe (a reply from the world, which it keeps)."""
        m = self.m
        needed = set()
        block = r.kind == 'block'

        def inst_of(x):
            t = m.etypes.get(id(x))
            return t[1] if isinstance(t, tuple) and t[0] == 'Inst' else None

        def lossy_ops(aname):
            return [op for op in m.answered_ops(aname)
                    if (m.op_rule(aname, op) is not None and m.op_rule(aname, op).cls == 'lossy')]

        def taken(op, installed):
            return any(m.answers_op(a, op) for a in installed)

        def covered(g, installed):
            ops = m.requests.get(g, {})
            return bool(ops) and all(taken(op, installed) for op in ops)

        def reaches(a, ops, installed, line, why):
            # an answer has no row: what its rules ask is shown in the row of whoever
            # messages or installs it
            for op in ops:
                asked, groups = m.reach(a, op)
                for q in sorted(asked):
                    if not taken(q, installed):
                        needed.add((m.ops[q], line, f'{why}, whose rule for {op} asks {q}'))
                for g in sorted(groups):
                    if not covered(g, installed):
                        needed.add((g, line, f'{why}, whose rule for {op} uses {g}'))

        def walk(x, installed):
            if not isinstance(x, Form):
                return
            if x.tag == 'Quote':
                return
            if x.tag == 'Ask':
                op = x.kids[0].kids[0]
                if op in m.ops and not taken(op, installed):
                    needed.add((m.ops[op], x.line, f'asks {op}'))
            if x.tag == 'Output':
                needed.add(('Output', x.line, 'writes output'))
            if x.tag == 'Commit' and block:
                # a commit point dissipates what Root retains: the effect is System's
                needed.add(('System', x.line, 'commits, which dissipates what the journal holds'))
            if x.tag == 'Decide':
                crisp = settle(m.etypes.get(id(x.kids[0]), 'Any')) == 'Bool'
                if not crisp and not taken('settle', installed):
                    needed.add(('Decide', x.line, 'decides'))
                if not crisp and block:
                    needed.add(('System', x.line, 'may keep the world\'s reply to a decision'))
            if x.tag == 'Send':
                a, op = inst_of(x.kids[0]), x.kids[1].kids[0]
                o = m.op_rule(a, op) if a else None
                if o is not None and o.cls == 'lossy' and block:
                    needed.add(('System', x.line, f'sends {op} to {a}, which answers it lossily'))
                if a:
                    reaches(a, [op], installed, x.line, f'sends {op} to {a}')
            if x.tag == 'With':
                a = inst_of(x.kids[1])
                if a and block and lossy_ops(a):
                    needed.add(('System', x.line, f'installs {a}, which answers {lossy_ops(a)[0]} lossily'))
                if a:   # what its rules ask goes outward from it: to the answers installed around it
                    reaches(a, m.answered_ops(a), installed, x.line, f'installs {a}')
                walk(x.kids[1], installed)
                walk(x.kids[0], installed + [a] if a else installed)
                return
            if x.tag == 'Call':
                cc = self.clause_callee(x)
                callee = cc[0] if cc else (m.rules.get(x.kids[0].kids[0]) if x.kids[0].tag == 'Name' else None)
                if callee is not None:
                    for g in callee.uses:
                        if not covered(g, installed):
                            needed.add((g, x.line, f'calls {callee.name}, which uses {g}'))
                    if block and callee.kind == 'clauses' and callee.cls == 'lossy':
                        needed.add(('System', x.line, f'calls {callee.name}, which is lossy'))
            for k in x.kids:
                walk(k, installed)
        body = r.block if block else Form('Clauses', tuple(r.clauses))
        walk(body, [])
        said = set()
        for g, line, why in sorted(needed, key=lambda t: (t[1] or 0, t[0])):
            if g not in r.uses and g not in said:
                said.add(g)
                m.err(line, f'{r.name} {why}; declare `uses {g}`')
        for g in sorted(r.uses):
            if g == 'Discard':
                m.err(r.line, f'{r.name}: Discard is not a request group; a lossy rule writes `=>`')
            elif g not in m.requests:
                m.err(r.line, f'unknown request group {g}')


def definition_of(m, r):
    """A rule's or an answer's code as it runs (elaborated), as a value."""
    d = r.decl
    if r.is_answer and not r.op:
        name, params, groups, state, clauses = d.kids
        cs = tuple(m.elaborated.get(id(c), c) for c in clauses.kids)
        return Form('AnswerDecl', (name, params, groups, state, Form('Clauses', cs, clauses.line)), d.line)
    if r.kind == 'clauses' and not r.is_answer:
        name, params, takes, returns, uses, body = d.kids
        if r.backward:
            name, takes, returns = r.name, returns, takes
        return Form('RuleDecl', (name, params, takes, returns, uses, Form('Clauses', tuple(r.clauses), body.line)),
                    d.line)
    return d


def build_model(*programs):
    """Build and check a model from one or more parsed programs (prelude first)."""
    m = Model()
    m.requests['Output'] = {'output': ([('value', 'Any')], 'Unit')}  # the world's one request here
    m.ops['output'] = 'Output'
    # Code and the other form types are declared in the prelude: the parser's forms are their values
    code = ('Data', 'Code')
    # Decide: an undecided condition goes outward as settle(question, context) and
    # comes back true, false or maybe (maybe passes it on to the next answer out).
    m.requests['Decide'] = {'settle': ([('question', code), ('context', 'Any')], 'Trit')}
    m.ops['settle'] = 'Decide'
    decls = [d for p in programs for d in p.kids]
    # every declaration by its name, and the program as written: both are forms a program may hold
    m.decls = {d.kids[0]: d for d in decls}
    m.program = list(programs[-1].kids)
    prelude_ids = set()
    if len(programs) > 1:
        m.prelude_names = {d.kids[0] for d in programs[0].kids}
        prelude_ids = {id(d) for d in programs[0].kids}

    def place(d):
        return 'prelude' if id(d) in prelude_ids else 'program'

    def conv(tf, d):
        # `Any` is written only in the prelude's own declarations (the journal's entries)
        m.any_ok = id(d) in prelude_ids
        try:
            return m.conv(tf, d.line)
        finally:
            m.any_ok = False
    # pass 1: types, requests, answer names
    for d in decls:
        if d.tag == 'AnswerDecl':
            m.answer_names.add(d.kids[0])
        if d.tag == 'TypeDecl':
            name, ctors, parent = d.kids
            if name in m.types:
                m.err(d.line, f'type {name} is defined twice')
            m.types[name] = TypeInfo(name, {}, parent, d.line)
        elif d.tag == 'RequestDecl':
            g = d.kids[0]
            if g in m.requests:
                m.err(d.line, f'request group {g} is declared twice')
            m.requests[g] = {}
            m.group_place[g] = place(d)
            for op in d.kids[1:]:
                if op.tag == 'SealedTo':     # `request G for A`: G is sealed to the answer A
                    m.sealed[g] = op.kids[0]
                    continue
                oname, ps, ret = op.kids
                if oname in m.ops:
                    m.err(d.line, f'request {oname} is declared twice')
                m.ops[oname] = g
    for d in decls:
        if d.tag == 'TypeDecl':
            name, ctors, parent = d.kids
            info = m.types[name]
            for c in ctors.kids:
                cname, fields = c.kids
                fs = [(f.kids[0], conv(f.kids[1], d)) for f in fields.kids]
                info.ctors[cname] = fs
        elif d.tag == 'RequestDecl':
            g = d.kids[0]
            for op in d.kids[1:]:
                if op.tag != 'Op':
                    continue
                oname, ps, ret = op.kids
                m.requests[g][oname] = ([(p.kids[0], conv(p.kids[1], d)) for p in ps.kids],
                                        conv(ret, d))
    # inheritance: field-only derivation (parents first)
    done = set()

    def derive(name, stack=()):
        if name in done:
            return
        info = m.types[name]
        if info.parent:
            if info.parent not in m.types:
                m.err(info.line, f'{name} derives from unknown type {info.parent}')
            elif info.parent in stack:
                m.err(info.line, f'{name} derives from itself')
            else:
                derive(info.parent, stack + (name,))
                pinfo = m.types[info.parent]
                if len(pinfo.ctors) != 1:
                    m.err(info.line, f'`<-` derives from a record; {info.parent} has several constructors')
                else:
                    pf = next(iter(pinfo.ctors.values()))
                    own = info.ctors[name]
                    clash = {f for f, _ in pf} & {f for f, _ in own}
                    if clash:
                        m.err(info.line, f'{name} repeats inherited field(s) {", ".join(sorted(clash))}')
                    info.ctors[name] = list(pf) + own
        done.add(name)
    for name in list(m.types):
        derive(name)
    for name, info in m.types.items():
        for cname, fs in info.ctors.items():
            if cname in m.ctors:
                m.err(info.line, f'constructor {cname} is defined twice')
            m.ctors[cname] = (name, fs)
    # pass 2: rules and answers (signatures)
    for d in decls:
        if d.tag == 'RuleDecl':
            name, params, takes, returns, uses, body = d.kids
            if name in m.rules or name in m.ctors:
                m.err(d.line, f'{name} is defined twice')
            if name.startswith('undo '):
                m.err(d.line, f'{name} is derived from {name[5:]}; it is not declared')
            if name in BUILTINS or name in CONVERSIONS:
                m.err(d.line, f'{name} is a built-in rule and cannot be redefined')
            r = RuleInfo(name, d)
            r.place = place(d)
            r.params = [(p.kids[0], conv(p.kids[1], d)) for p in params.kids]
            r.takes = conv(takes, d)
            r.returns = conv(returns, d)
            r.uses = set(uses.kids)
            if body.tag == 'Clauses':
                r.kind = 'clauses'
                r.clauses = list(body.kids)
            else:
                r.kind = 'block'
                r.block = body
                if r.takes != 'Any':
                    m.err(d.line, f'{name} has no clauses, so it takes nothing; use parameters')
            m.rules[name] = r
            m.decl_order.append(name)
        elif d.tag == 'AnswerDecl':
            name, params, groups, state, clauses = d.kids
            if name.startswith('undo '):
                m.err(d.line, f'{name} is derived from {name[5:]}; it is not declared')
            if name in m.answers:
                m.err(d.line, f'answer {name} is defined twice')
            r = RuleInfo(name, d)
            r.is_answer = True
            r.place = place(d)
            r.takes = conv(state, d)
            r.kind = 'clauses'
            r.params = [(p.kids[0], conv(p.kids[1], d)) for p in params.kids]
            r.clauses = list(clauses.kids)
            r.group_order = list(dict.fromkeys(groups.kids))
            r.groups = set(r.group_order)
            r.group = r.group_order[0] if r.group_order else None
            for g in r.group_order:
                if g not in m.requests:
                    m.err(d.line, f'unknown request group {g}')
                elif g in m.sealed and not m.holds_seal(r.place, g):
                    # R5: only the place that holds a seal declares an answer for its group
                    m.err(d.line, f'{g} is sealed to {m.sealed[g]}: {name} cannot answer it')
            if not r.group_order:
                m.err(d.line, f'{name} answers no request group; write `answer {name} for Group`')
            m.answers[name] = r
    m.any_ok = False
    # R5, seals.  `request G for A` seals the group G and the answer A to the place that
    # declares them: only code there sends G's requests, declares an answer for G, or
    # makes an instance of A.  The rule names no declaration; the prelude seals System to
    # Root, and the system holds the other half: it makes the one Root and sends `keep`.
    for g, aname in m.sealed.items():
        a = m.answers.get(aname)
        if a is None:
            m.err(None, f'{g} is sealed to {aname}, which is not an answer')
        elif a.place != m.group_place[g]:
            m.err(a.line, f'{g} is sealed to {aname}, which is declared in another place')
        elif g not in a.groups:
            m.err(a.line, f'{g} is sealed to {aname}, and {aname} is not an answer for {g}')
        elif aname in m.sealed_answers:
            m.err(a.line, f'{aname} already holds the seal of {m.sealed_answers[aname]}')
        else:
            m.sealed_answers[aname] = g
    # Answers.  An answer's clauses for one request form one rule, certified on its own.  A
    # request of its groups that it has no rule for is delegated to the one component of
    # its state that answers it: the component's rule runs on the component's own state
    # and keeps its certificate.  Components are resolved first, so delegation chains.
    resolved = set()

    def resolve(a, stack=()):
        if a.name in resolved:
            return
        if a.name in stack:
            m.err(a.line, f'{a.name} holds an instance of itself; an answer delegates to another answer')
            return
        parts = m.components(a.takes)
        for _, cname in parts:
            if cname in m.answers:
                resolve(m.answers[cname], stack + (a.name,))
        own = {}
        for c in a.clauses:
            left, right = c.kids[0], c.kids[1]
            ok = left.tag == 'Tuple' and len(left.kids) == 2 and right.tag == 'Tuple' and len(right.kids) == 2
            req = left.kids[0] if ok else None
            opname = None
            if ok and req.tag == 'Call' and req.kids[0].tag == 'Name':
                opname = req.kids[0].kids[0]
            elif ok and req.tag == 'Name':
                opname = req.kids[0]
            if not ok or opname is None or m.ops.get(opname) not in a.groups:
                m.err(c.line, f'an answer clause has the form (request, state) <-> (reply, state), '
                              f'with a request of {" or ".join(sorted(a.groups))}')
                continue
            own.setdefault(opname, []).append(c)
        for op, cs in own.items():
            orule = RuleInfo(f'{a.name}.{op}', a.decl)
            orule.is_answer, orule.kind, orule.op, orule.owner = True, 'clauses', op, a.name
            orule.takes, orule.params, orule.uses, orule.group = a.takes, a.params, a.uses, m.ops[op]
            orule.place = a.place
            orule.clauses = cs
            orule.line = cs[0].line
            a.ops[op] = orule
        for g in a.group_order:
            for op in m.requests.get(g, {}):
                if op in a.ops:
                    continue
                if a.name in m.sealed_answers and a.place == 'prelude' and not parts:
                    # a request the system's sealed answer has no clause for is answered by the
                    # system itself: Root's final answer to a refusal is the end of the run
                    a.native.add(op)
                    continue
                able = [(path, cname) for path, cname in parts if m.answers_op(cname, op)]
                if len(able) == 1:
                    a.delegates[op] = able[0]
                elif len(able) > 1:
                    m.err(a.line, f'{a.name}: {len(able)} components of its state answer {op} '
                                  f'({", ".join(c for _, c in able)}); {a.name} must take {op} itself')
        resolved.add(a.name)
    for a in list(m.answers.values()):
        resolve(a)
    ch = Checker(m)
    ch.check_program()
    return m, ch
