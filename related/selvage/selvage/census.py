"""The form census (VIII.1): which constructs of a program have a form, which a rule can take
apart, and which it can put back together.

Nothing here is asserted from a table.  The census takes the prelude and a program as the
values a program itself would hold — `definition`, `program()` and `sequence` — and, for every
node in them, establishes three things by doing them:

  represented     the node's tag is a constructor of a declared form type, with as many
                  fields as the node has children
  taken apart     a one-clause rule, written for that constructor and checked by the ordinary
                  checker, matches the node and binds every field
  put together    the same clause builds the node again from what it bound, and the result is
                  the same value

and, for every declaration, that its printed text reads back as the same declaration.
A construct that prints but cannot be taken apart does not count as inspectable.
"""
import os
import re

from .forms import Form, Fault, encode
from .parser import parse
from .invert import as_sequence, as_block, OPAQUE
from .declared import declared, undeclared
from .printer import code_text

FORM_TYPES = ('Code', 'Parts', 'TypeExpr', 'Param', 'Slot', 'Ctor', 'Op', 'Declaration', 'Program')

# what the parser writes with as many children as there are members, and how a program holds it
REWRITTEN = {'Params': 'Parts', 'Uses': 'Parts', 'Groups': 'Parts', 'Ctors': 'Parts', 'Fields': 'Parts',
             'Clauses': 'Parts', 'Block': 'Then … Done (by `sequence`)', 'Tuple': 'Tupled (by `sequence`)',
             'SealedTo': 'the `sealed` field of RequestDecl'}

# what a run has that no program holds as a value
NOT_FORMS = ('the answers installed around a run, as a list',
             'a run in progress, and the runs the system may still rewind',
             'the depth of a run and its bound',
             'the world decider, and the record it replays')


def parser_tags():
    """Every tag the parser can write, read off the parser's own text."""
    with open(os.path.join(os.path.dirname(__file__), 'parser.py')) as f:
        text = f.read()
    tags = set(re.findall(r"\bF\('([A-Za-z]+)'", text))
    tags |= set(re.findall(r"'(Less|LessEqual|Greater|GreaterEqual|Equal|NotEqual|Add|Subtract|Multiply|Divide|Mod|And|Or|"
                           r"Clause|LossyClause|RepeatWith|RepeatDown|AddTo|SubtractFrom|Negate|Not)'", text))
    return tags


def held(d):
    """A declaration as a program holds it, with all its code written to be taken apart."""
    return as_sequence(declared(d), whole=True)


def nodes(v, out):
    if isinstance(v, Form):
        out.append(v)
        if v.tag not in OPAQUE:
            for k in v.kids:
                nodes(k, out)
    elif isinstance(v, tuple):
        for k in v:
            nodes(k, out)
    return out


def census(m, samples=3):
    """(rows, escaped, unmet, round_trips): one row per constructor met, the tags that are no
    constructor, the parser's tags this program does not use, and the declarations whose text
    does not read back."""
    from . import load
    from .interp import Interp
    from .checker import definition_of
    decls = list(m.decls.values())
    met = {}
    # every declaration as written, and every rule's derived inverse as it runs
    derived = [definition_of(m, r.inverse) for r in m.rules.values()
               if r.kind == 'clauses' and not r.backward and getattr(r, 'inverse', None) is not None]
    for d in decls + derived:
        for n in nodes(held(d), []):
            met.setdefault(n.tag, []).append(n)
    for n in nodes(held(Form('Program', tuple(m.program))), [])[:1]:
        met.setdefault(n.tag, []).append(n)
    escaped = {}
    probes, probed = [], []
    for tag, ns in sorted(met.items()):
        if tag not in m.ctors or any(len(n.kids) != len(m.ctors[tag][1]) for n in ns):
            escaped[tag] = len(ns)
            continue
        fields = [f'f{i}' for i in range(len(m.ctors[tag][1]))]
        side = tag + (f'({", ".join(fields)})' if fields else '')
        t = m.ctors[tag][0]
        probes.append(f'rule probe_{tag} takes {t} returns {t}\n    {side} <-> {side}\n')
        probed.append(tag)
    rows = []
    pm = load('\n'.join(probes))[0] if probes else None
    for tag in probed:
        apart = together = 0
        tried = met[tag][:samples]
        for n in tried:
            try:
                out = Interp(pm).forward(pm.rules[f'probe_{tag}'], (), n)
                apart += 1
                together += encode(out) == encode(n)
            except Fault:
                pass
        rows.append((m.ctors[tag][0], tag, len(met[tag]), apart == len(tried), together == len(tried)))
    unmet = sorted(t for t in parser_tags() if t not in met and t not in REWRITTEN and t != 'Field' and t != 'Program'
                   or t == 'Field' and 'Slot' not in met and 'Field' not in met)
    round_trips = []
    for d in decls:
        try:
            v = declared(d)
            again = declared(parse(code_text(undeclared(as_block(as_sequence(v, whole=True), whole=True)))).kids[0])
            if encode(again) != encode(v):
                round_trips.append(d.kids[0])
        except Exception:
            round_trips.append(d.kids[0])
    return rows, escaped, unmet, round_trips


def report(m):
    rows, escaped, unmet, round_trips = census(m)
    lines = [f'{"form type":<13}{"constructors met":>17}{"nodes":>8}   taken apart   put together']
    by_type = {}
    for t, tag, n, apart, together in rows:
        c = by_type.setdefault(t, [0, 0, True, True, []])
        c[0] += 1
        c[1] += n
        c[2] &= apart
        c[3] &= together
        if not (apart and together):
            c[4].append(tag)
    for t in FORM_TYPES:
        if t in by_type:
            c = by_type[t]
            of = len(m.types[t].ctors)
            lines.append(f'{t:<13}{str(c[0]) + " of " + str(of):>17}{c[1]:>8}   {"yes" if c[2] else "NO":<14}'
                         f'{"yes" if c[3] else "NO"}' + (f'   ({", ".join(c[4])})' if c[4] else ''))
    others = sorted(t for t in by_type if t not in FORM_TYPES)
    if others:
        lines.append(f'constructors of the program\'s own types, met in patterns and values: {", ".join(others)}')
    lines.append('')
    lines.append(f'declarations: {len(m.decls)}; printed and read back as the same declaration: '
                 f'{len(m.decls) - len(round_trips)}' + (f'; not: {", ".join(round_trips)}' if round_trips else ''))
    lines.append('escapes (a tag that is no constructor of a form type): '
                 + (', '.join(f'{t} ({n})' for t, n in sorted(escaped.items())) if escaped else 'none'))
    lines.append('written otherwise in the value: ' + '; '.join(f'{a} as {b}' for a, b in sorted(REWRITTEN.items())))
    lines.append('the parser\'s tags this program does not use: ' + (', '.join(unmet) if unmet else 'none'))
    lines.append('not forms: ' + '; '.join(NOT_FORMS))
    return '\n'.join(lines)
