"""The identity of code (III.3, VII.3).

Code is identified by what it structurally is and what it references, not by the names it
happens to be given.  Four responsibilities are kept apart:

    a name            identifies a thing for readers
    an identity       identifies a thing for execution: the hash of a canonical form
    a canonical form  establishes structural equality; an identity is checked against it
    authority         determines what execution may do, and is no part of any of this:
                      knowing the identity of a request or an answer grants nothing

There is one identity function, forms.identity.  This module builds the canonical form it
is applied to.

Canonical form of code
  - Variables are not named.  Each binding is numbered where it is made, in the order the
    code makes them, and every use holds the number of the binding it refers to.  So
    renaming a variable consistently changes nothing, while which binding a use refers to
    and the shape of patterns are kept.  A name cannot be bound where it is already bound
    (the checker refuses it), so a use always refers to the latest binding of its name: a
    name bound again after it was given back, or in another block, is another variable.
    A rule's parameters are held by their place.  A name bound nowhere stays a name.
  - References are resolved.  A call holds the identity of the rule called; a message and
    an `ask` hold the identity of the request; `from` holds the identity of the answer.
  - Quoted code is data, and is left as written.
  - Types and constructors keep their names: values carry them.

Rules are identified by their code, without their own names.  Clauses whose left sides are
exclusive are a set; where the first match decides, their order is part of the rule.

Rules and answers that refer to one another in a cycle are identified as a whole: members
are told apart by their code and by which members they refer to, refined until nothing
more separates them; a member's identity is the cycle's together with its place in it.
Rules that nothing separates are the same code and have one identity.

Requests and answers are declarations, not interchangeable code: two with the same content
stay two.  A request is identified by its group and its place in it; a group by the
signatures of its requests; an answer by its code.  Declarations with the same content are
told apart by the order in which they are declared.
"""
from .forms import Form, encode, identity


class SharedIdentity(Exception):
    """Two different things under one identity (III.3): refused, never guessed."""


class Refs:
    """What identifies each rule, request, group and answer, by the name it is written with."""
    def __init__(self, rules=None, answers=None, requests=None, groups=None):
        self.rules, self.answers = rules or {}, answers or {}
        self.requests, self.groups = requests or {}, groups or {}


# ---- canonical form of code --------------------------------------------------------------
class Canon:
    def __init__(self, m, refs, params=()):
        self.m, self.refs = m, refs
        self.params = {name: i for i, name in enumerate(params)}
        self.env, self.n = {}, 0

    def fresh(self, name):
        self.n += 1
        self.env[name] = str(self.n)
        return Form('Var', (self.env[name],))

    def name(self, n):
        if n in self.env:
            return Form('Var', (self.env[n],))
        if n in self.params:
            return Form('Param', (str(self.params[n]),))
        return Form('Name', (n,))            # a constructor, or a name bound nowhere here

    def head(self, n):
        """A name where something is called, made or matched: a reference, if it is one."""
        r = self.refs
        if n in r.rules:
            return Form('Rule', (r.rules[n],))
        if n in r.requests:
            return Form('Request', (r.requests[n],))
        if n in r.answers:
            return Form('Answer', (r.answers[n],))
        return Form('Name', (n,))

    def bind(self, p):
        """A pattern whose variables are bound here."""
        if not isinstance(p, Form):
            return p
        if p.tag == 'Name':
            n = p.kids[0]
            if n in self.m.ctors or n in self.m.ops:
                return self.head(n)
            return self.fresh(n)
        if p.tag == 'Tuple':
            return Form('Tuple', tuple(self.bind(x) for x in p.kids))
        if p.tag == 'Call' and p.kids[0].tag == 'Name':
            return Form('Call', (self.head(p.kids[0].kids[0]), self.bind(p.kids[1])))
        return self.use(p)

    def answer(self, ae):
        """`A` or `A(params)` where an instance is made or opened."""
        if ae.tag == 'Name':
            return self.head(ae.kids[0])
        return Form('Call', (self.head(ae.kids[0].kids[0]), self.use(ae.kids[1])))

    def use(self, e):
        """An expression, or a pattern of names already bound."""
        if not isinstance(e, Form):
            return e
        t, k = e.tag, e.kids
        if t == 'Name':
            return self.name(k[0])
        if t == 'Quote':
            return e                          # quoted code is data
        if t == 'Block':
            return self.steps(e)
        if t == 'Call':
            head = self.head(k[0].kids[0]) if isinstance(k[0], Form) and k[0].tag == 'Name' else self.use(k[0])
            return Form('Call', (head,) + tuple(self.use(x) for x in k[1:]))
        if t == 'Request':
            return Form('Request', (self.refs.requests.get(k[0], k[0]), self.use(k[1])))
        if t == 'Instance':
            return Form('Instance', (self.answer(k[0]), self.use(k[1])))
        return Form(t, tuple(self.use(x) if isinstance(x, Form) else x for x in k))

    def clause_call(self, e):
        """(the params, the input pattern) if e calls a clause rule, as the checker reads it."""
        if e.tag != 'Call':
            return None
        f, args = e.kids
        rules = self.m.rules
        if f.tag == 'Name' and f.kids[0] in rules and rules[f.kids[0]].kind == 'clauses' and len(args.kids) == 1:
            return f.kids[0], None, args.kids[0]
        if f.tag == 'Call' and f.kids[0].tag == 'Name' and f.kids[0].kids[0] in rules \
                and rules[f.kids[0].kids[0]].kind == 'clauses' and len(args.kids) == 1:
            return f.kids[0].kids[0], f.kids[1], args.kids[0]
        return None

    def step(self, s):
        t, k = s.tag, s.kids
        if t == 'Let':                       # what it reads and consumes, then what it binds
            value = self.use(k[1])
            return Form('Let', (self.bind(k[0]), value))
        if t == 'Was':                       # what it consumes, then what it gives back
            pat, rhs = self.use(k[0]), k[1]
            inner = rhs.kids[0] if rhs.tag == 'Undo' else rhs
            call = self.clause_call(inner)
            if call is not None:
                name, params, given = call
                head = self.head(name)
                if params is not None:
                    head = Form('Call', (head, self.use(params)))
                back = Form('Call', (head, Form('Tuple', (self.bind(given),))))
                return Form('Was', (pat, Form('Undo', (back,)) if rhs.tag == 'Undo' else back))
            if inner.tag == 'Instance':
                made = self.answer(inner.kids[0])
                return Form('Was', (pat, Form('Instance', (made, self.bind(inner.kids[1])))))
            return Form('Was', (pat, self.use(rhs)))
        if t == 'Discard':
            return Form('Discard', (self.name(k[0]),))
        if t == 'Restore':
            return Form('Restore', (self.fresh(k[0]),))
        if t in ('RepeatWith', 'RepeatDown'):
            first, last = self.use(k[1]), self.use(k[2])
            counter = self.fresh(k[0])       # the counter is a binding of its own
            return Form(t, (counter, first, last, self.steps(k[3])))
        return Form(t, tuple(self.use(x) if isinstance(x, Form) else x for x in k))

    def steps(self, b):
        return Form('Block', tuple(self.step(s) for s in b.kids))


def canonical(m, refs, code, params=()):
    """The canonical form of a clause, a body, or any piece of code."""
    c = Canon(m, refs, params)
    if code.tag in ('Clause', 'LossyClause'):
        left = c.bind(code.kids[0])
        steps = c.steps(code.kids[2])
        return Form(code.tag, (left, c.use(code.kids[1]), steps))
    if code.tag == 'Block':
        return c.steps(code)
    return c.use(code)


# ---- what a declaration refers to ----------------------------------------------------------
def type_form(t, refs):
    if isinstance(t, tuple):
        if len(t) == 2 and t[0] == 'Inst':
            return ('Inst', refs.answers.get(t[1], t[1]) if refs is not None else '?')
        return tuple(type_form(x, refs) for x in t)
    return t


def mentions(x, rules, answers, out):
    """The rules and answers a piece of code or a type refers to, in the order it does."""
    if isinstance(x, Form):
        if x.tag == 'Quote':
            return out
        if x.tag == 'Call' and isinstance(x.kids[0], Form) and x.kids[0].tag == 'Name':
            n = x.kids[0].kids[0]
            key = ('R', n) if n in rules else ('A', n) if n in answers else None
            if key and key not in out:
                out.append(key)
        if x.tag == 'Instance' and x.kids[0].tag == 'Name' and x.kids[0].kids[0] in answers \
                and ('A', x.kids[0].kids[0]) not in out:
            out.append(('A', x.kids[0].kids[0]))
        for k in x.kids:
            mentions(k, rules, answers, out)
    elif isinstance(x, tuple):
        if len(x) == 2 and x[0] == 'Inst' and x[1] in answers:
            if ('A', x[1]) not in out:
                out.append(('A', x[1]))
        else:
            for k in x:
                mentions(k, rules, answers, out)
    return out


def clauses_form(m, refs, r):
    params = [name for name, _ in r.params]
    clauses = [encode(canonical(m, refs, c, params)) for c in r.clauses]
    if not getattr(r, 'first_match_decides', False):
        clauses.sort()                       # exclusive left sides: the clauses are a set
    return '[' + ','.join(clauses) + ']'


def rule_form(m, refs, r):
    """A rule's code in canonical form: its parameters by type, its types, its row, and its
    clauses or body; not its name."""
    head = (f'Rule({[type_form(t, refs) for _, t in r.params]!r};{type_form(r.takes, refs)!r};'
            f'{type_form(r.returns, refs)!r};{sorted(refs.groups.get(g, g) for g in r.uses)!r})')
    if r.kind == 'clauses':
        return head + clauses_form(m, refs, r)
    return head + encode(canonical(m, refs, r.block, [name for name, _ in r.params]))


def answer_form(m, refs, a):
    """An answer's code in canonical form: its parameters, the state it takes, its groups, and
    its clauses request by request; not its name."""
    head = (f'Answer({[type_form(t, refs) for _, t in a.params]!r};{type_form(a.takes, refs)!r};'
            f'{sorted(refs.groups.get(g, g) for g in a.groups)!r})')
    ops = sorted((refs.requests.get(op, op), clauses_form(m, refs, a.ops[op])) for op in a.ops)
    return head + '{' + ','.join(f'{op}:{cs}' for op, cs in ops) + '}'


def components(nodes, edges):
    """Strongly connected components, what is referred to before what refers to it (Tarjan)."""
    index, low, on, stack, out, n = {}, {}, set(), [], [], [0]

    def enter(v):
        index[v] = low[v] = n[0]
        n[0] += 1
        stack.append(v)
        on.add(v)
    for start in nodes:
        if start in index:
            continue
        enter(start)
        work = [(start, iter(edges[start]))]
        while work:
            node, it = work[-1]
            for w in it:
                if w not in index:
                    enter(w)
                    work.append((w, iter(edges[w])))
                    break
                if w in on:
                    low[node] = min(low[node], index[w])
            else:
                work.pop()
                if work:
                    low[work[-1][0]] = min(low[work[-1][0]], low[node])
                if low[node] == index[node]:
                    comp = []
                    while True:
                        w = stack.pop()
                        on.discard(w)
                        comp.append(w)
                        if w == node:
                            break
                    out.append(comp)
    return out


class Register:
    """Every identity given, with the canonical form it names (III.3)."""
    def __init__(self):
        self.forms = {}

    def __call__(self, form):
        ident = identity(form)
        if self.forms.setdefault(ident, form) != form:
            raise SharedIdentity(f'two different declarations share the identity {ident}; code that refers to '
                                 f'one cannot be told from code that refers to the other')
        return ident


def resolve(m, nodes, edges, fixed, register):
    """Identities for `nodes` (rules and answers), given what is already `fixed`."""
    refs = Refs(dict(fixed.rules), dict(fixed.answers), fixed.requests, fixed.groups)

    def table(kind):
        return refs.rules if kind == 'R' else refs.answers

    def form(node):
        kind, name = node
        return rule_form(m, refs, m.rules[name]) if kind == 'R' else answer_form(m, refs, m.answers[name])
    for comp in components(nodes, edges):
        if len(comp) == 1 and comp[0] not in edges[comp[0]]:
            table(comp[0][0])[comp[0][1]] = register(form(comp[0]))
            continue
        # a cycle: tell its members apart by their code and by which members they refer to
        place = {node: 0 for node in comp}
        while True:
            for kind, name in comp:
                table(kind)[name] = f'cycle:{place[(kind, name)]}'
            encoded = {node: form(node) for node in comp}
            order = sorted(set(encoded.values()))
            finer = {node: order.index(encoded[node]) for node in comp}
            if len(set(finer.values())) == len(set(place.values())):
                break                        # nothing more separates them
            place = finer
        members = {place[node]: encoded[node] for node in comp}
        cycle = '|'.join(members[i] for i in sorted(members))
        for kind, name in comp:
            table(kind)[name] = register(f'Cycle[{cycle}]#{place[(kind, name)]}')
    return refs


def identities(m):
    """What identifies every rule, request, group and answer of the program and the prelude."""
    got = getattr(m, '_identities', None)
    if got is not None:
        return got
    register = Register()
    # requests: a group is identified by the signatures of its requests, a request by its
    # group and its place in it.  Groups with the same signatures are still different
    # groups: they are told apart by the order in which they are declared
    groups, requests, seen = {}, {}, {}
    for g, ops in m.requests.items():
        form = 'Group[' + ';'.join(repr(([type_form(t, None) for _, t in pts], type_form(ret, None)))
                                   for pts, ret in ops.values()) + ']'
        nth = seen[form] = seen.get(form, -1) + 1
        groups[g] = register(f'{form}#{nth}')
        for i, op in enumerate(ops):
            requests[op] = register(f'Request[{groups[g]}.{i}]')
    rules = {name: r for name, r in m.rules.items() if not r.backward}
    answers = dict(m.answers)

    def edges_of(kind, name):
        out = []
        if kind == 'R':
            r = rules[name]
            mentions(tuple(r.clauses) if r.kind == 'clauses' else r.block, rules, answers, out)
            mentions((tuple(t for _, t in r.params), r.takes, r.returns), rules, answers, out)
        else:
            a = answers[name]
            for opr in a.ops.values():
                mentions(tuple(opr.clauses), rules, answers, out)
            mentions((tuple(t for _, t in a.params), a.takes), rules, answers, out)
        return out
    nodes = [('A', n) for n in answers] + [('R', n) for n in rules]
    edges = {node: edges_of(*node) for node in nodes}
    # answers by their code first, as if they were interchangeable; then those with the same
    # code are told apart by the order in which they are declared, because an answer is a
    # declaration and its instances carry it
    by_code = resolve(m, nodes, edges, Refs(requests=requests, groups=groups), Register())
    seen, named = {}, {}
    for name in answers:
        code = by_code.answers[name]
        nth = seen[code] = seen.get(code, -1) + 1
        named[name] = register(f'Answer[{code}]#{nth}')
    # and the rules, with every answer now fixed
    rule_nodes = [('R', n) for n in rules]
    rule_edges = {node: [e for e in edges[node] if e[0] == 'R'] for node in rule_nodes}
    refs = resolve(m, rule_nodes, rule_edges, Refs(answers=named, requests=requests, groups=groups), register)
    refs.forms = register.forms
    m._identities = refs
    return refs


def rule_identities(m):
    return identities(m).rules


def code_form(m, code, rule=None):
    """The canonical form of a piece of code of this program, as text.  `rule` is the rule or
    the answer's request rule the code stands in, whose parameters it may read."""
    params = [name for name, _ in rule.params] if rule is not None else ()
    return encode(canonical(m, identities(m), code, params))


def code_identity(m, code, rule=None):
    """The identity of a piece of code of this program: of a clause, a body, or any form."""
    return identity(code_form(m, code, rule))
