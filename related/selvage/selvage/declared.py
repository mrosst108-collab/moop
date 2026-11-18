"""Declarations and programs as forms a rule can take apart (VIII.1).

The parser writes a declaration with as many children as it has parameters, clauses or
constructors.  A clause matches a constructor with a fixed number of fields, so the value a
program holds writes each such list as Parts — Part(first, rest), ending in NoParts — and is of
the types the prelude declares: Declaration, Param, Ctor, Slot, Op, TypeExpr, Program.  The two
writings hold the same things in the same order; `declared` and `undeclared` go between them,
and each undoes the other.

A declaration is not Code.  Its header names and types it; the clauses in a rule's or an
answer's body are Code, as they are anywhere else.
"""
from .forms import Form, Fault

NO_PARTS = Form('NoParts', ())
DECLARATIONS = ('RuleDecl', 'AnswerDecl', 'TypeDecl', 'RequestDecl')


def parts(items):
    out = NO_PARTS
    for x in reversed(list(items)):
        out = Form('Part', (x, out))
    return out


def items(p, what='a list of parts'):
    out = []
    while isinstance(p, Form) and p.tag == 'Part' and len(p.kids) == 2:
        out.append(p.kids[0])
        p = p.kids[1]
    if not (isinstance(p, Form) and p.tag == 'NoParts'):
        raise Fault(f'{what} ends in NoParts')
    return out


def is_parts(v):
    return isinstance(v, Form) and v.tag in ('Part', 'NoParts')


def is_declared(v):
    """Whether a form is a declaration, or a program, as a program holds it."""
    if not isinstance(v, Form):
        return False
    if v.tag == 'Program':
        return len(v.kids) == 1 and is_parts(v.kids[0])
    return v.tag in DECLARATIONS and len(v.kids) > 1 and is_parts(v.kids[1])


def type_value(t):
    if t.tag == 'TypeName':
        return t
    if t.tag == 'TypeApp':
        return Form('TypeApp', (t.kids[0], parts(type_value(x) for x in t.kids[1:])))
    return Form('TupleType', (parts(type_value(x) for x in t.kids),))


def type_form(t):
    if not isinstance(t, Form) or t.tag not in ('TypeName', 'TypeApp', 'TupleType'):
        raise Fault('a type is a TypeName, a TypeApp or a TupleType')
    if t.tag == 'TypeName':
        return t
    if t.tag == 'TypeApp':
        return Form('TypeApp', (t.kids[0],) + tuple(type_form(x) for x in items(t.kids[1])))
    return Form('TupleType', tuple(type_form(x) for x in items(t.kids[0])))


def params_value(ps):
    return parts(Form('Param', (p.kids[0], type_value(p.kids[1]))) for p in ps.kids)


def params_form(ps):
    return Form('Params', tuple(Form('Param', (p.kids[0], type_form(p.kids[1]))) for p in items(ps, 'the parameters')))


def declared(d):
    """A declaration, or a program, as the parser wrote it -> as a program holds it."""
    t, k = d.tag, d.kids
    if t == 'Program':
        return Form('Program', (parts(declared(x) for x in k),))
    if t == 'RuleDecl':
        name, params, takes, returns, uses, body = k
        return Form(t, (name, params_value(params), type_value(takes), type_value(returns), parts(uses.kids),
                        parts(body.kids) if body.tag == 'Clauses' else body), d.line)
    if t == 'AnswerDecl':
        name, params, groups, state, clauses = k
        return Form(t, (name, params_value(params), parts(groups.kids), type_value(state), parts(clauses.kids)), d.line)
    if t == 'TypeDecl':
        name, ctors, parent = k
        return Form(t, (name, parts(Form('Ctor', (c.kids[0], parts(Form('Slot', (f.kids[0], type_value(f.kids[1])))
                                                                    for f in c.kids[1].kids)))
                                    for c in ctors.kids), parent), d.line)
    if t == 'RequestDecl':
        ops = [x for x in k[1:] if x.tag == 'Op']
        sealed = [x.kids[0] for x in k[1:] if x.tag == 'SealedTo']
        return Form(t, (k[0], parts(Form('Op', (o.kids[0], params_value(o.kids[1]), type_value(o.kids[2]))) for o in ops),
                        sealed[0] if sealed else ''), d.line)
    raise Fault(f'{t} is not a declaration')


def undeclared(v):
    """The other way.  A value that is not put together as a declaration is refused."""
    if not is_declared(v):
        raise Fault('not a declaration or a program')
    t, k = v.tag, v.kids
    try:
        if t == 'Program':
            return Form('Program', tuple(undeclared(x) for x in items(k[0], 'the declarations')))
        if t == 'RuleDecl':
            name, params, takes, returns, uses, body = k
            body = Form('Clauses', tuple(items(body, 'the clauses'))) if is_parts(body) else body
            if not (isinstance(body, Form) and body.tag in ('Clauses', 'Block')):
                raise Fault('the body of a rule is its clauses, or a block')
            return Form(t, (name, params_form(params), type_form(takes), type_form(returns),
                            Form('Uses', tuple(items(uses, 'the row'))), body), v.line)
        if t == 'AnswerDecl':
            name, params, groups, state, clauses = k
            return Form(t, (name, params_form(params), Form('Groups', tuple(items(groups, 'the groups'))),
                            type_form(state), Form('Clauses', tuple(items(clauses, 'the clauses')))), v.line)
        if t == 'TypeDecl':
            name, ctors, parent = k
            return Form(t, (name, Form('Ctors', tuple(
                Form('Ctor', (c.kids[0], Form('Fields', tuple(Form('Field', (f.kids[0], type_form(f.kids[1])))
                                                               for f in items(c.kids[1], 'the slots')))))
                for c in items(ctors, 'the constructors'))), parent), v.line)
        name, ops, sealed = k
        return Form(t, (name,) + tuple(Form('Op', (o.kids[0], params_form(o.kids[1]), type_form(o.kids[2])))
                                       for o in items(ops, 'the requests'))
                    + ((Form('SealedTo', (sealed,)),) if sealed else ()), v.line)
    except (ValueError, IndexError, AttributeError, TypeError):
        raise Fault(f'this {t} is not put together as a declaration')
