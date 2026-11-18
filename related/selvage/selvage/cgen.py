"""C23 backend.

Translates the statically typed fragment of a checked program to C23:
fixed-width integers, Bit, Bool, F64, text output, tuples, records and
variants, arrays of scalars, expression rules, and clause rules.

For every certified clause rule the backend emits two functions, the rule and
its inverse `<rule>_inv`, which is the code `invert` derived, compiled forward by
the same emitter; there is no reverse emitter.  Uncomputes the checker proved
compile to nothing.  Lossy clause rules push their complements onto the runtime
journal (the C realization of Root's `keep`); rewinding stays in the interpreter.  Answers,
requests other than output, quoted code and `with` stay in the interpreter.
"""
import math

from .forms import Word, INT_TYPES, Form, Fault, MAYBE
from .account import clog2
from .checker import settle, pattern_vars, is_ctor_name, NUMERIC, INTS, CONVERSIONS, WIDENINGS, tstr

SCALAR_C = {'I8': 'int8_t', 'I16': 'int16_t', 'I32': 'int32_t', 'I64': 'int64_t',
            'U8': 'uint8_t', 'U16': 'uint16_t', 'U32': 'uint32_t', 'U64': 'uint64_t',
            'Bit': 'uint8_t', 'Bool': 'bool', 'Trit': 'uint8_t', 'F64': 'double', 'Text': 'const char *'}
MANGLE = {'I8': 'i8', 'I16': 'i16', 'I32': 'i32', 'I64': 'i64', 'U8': 'u8', 'U16': 'u16',
          'U32': 'u32', 'U64': 'u64', 'Bit': 'bit', 'Bool': 'bool', 'Trit': 'trit', 'F64': 'f64', 'Text': 'text'}
ARITH = {'Add': 'add', 'Subtract': 'sub', 'Multiply': 'mul', 'Divide': 'div', 'Mod': 'mod'}
FARITH = {'Add': '+', 'Subtract': '-', 'Multiply': '*', 'Divide': '/'}
CMP = {'Equal': '==', 'NotEqual': '!=', 'Less': '<', 'Greater': '>', 'LessEqual': '<=', 'GreaterEqual': '>='}


class Unsupported(Fault):
    pass


# Depth (R8).  Every rule function takes the depth of its invocation as its last argument,
# refuses beyond the bound on entry, and starts each rule it calls one deeper.  The count
# is the interpreter's: one for each rule invocation in progress, none for a self tail call.
ENTER = '    if (sv_d > SV_DEPTH) sv_fault_depth();'
DEEPER = 'sv_d + 1'


def cstr(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


class CGen:
    def __init__(self, m):
        self.m = m
        self.types = {}       # mangle -> type (compound types to emit)
        self.order = []       # emission order of compound types
        self.arrays = {}      # element mangle -> element C type
        self.tmp = 0
        self.reachable = []
        self.decide_fns = {}   # id(expr) -> (name, C source)

    # ---- types ------------------------------------------------------------
    def mg(self, t):
        if isinstance(t, str):
            if t in MANGLE:
                return MANGLE[t]
            if t == 'Lit':
                return 'i64'
            raise Unsupported(f'type {tstr(t)} has no C form')
        if t[0] == 'Tuple':
            return f't{len(t[1])}_' + '_'.join(self.mg(x) for x in t[1])
        if t[0] == 'Array':
            return 'a_' + self.mg(t[1])
        if t[0] == 'Data':
            if t[1] == 'Code':
                raise Unsupported('quoted code stays in the interpreter')
            return 'd_' + t[1]
        raise Unsupported(f'type {tstr(t)} has no C form')

    def ct(self, t):
        t = settle(t)
        if isinstance(t, str):
            if t in SCALAR_C:
                return SCALAR_C[t]
            if t == 'Unit':
                return 'void'
            raise Unsupported(f'type {tstr(t)} has no C form')
        self.need(t)
        return 'sv_' + self.mg(t)

    def need(self, t):
        t = settle(t)
        if isinstance(t, str):
            if t not in SCALAR_C and t != 'Unit':
                raise Unsupported(f'type {tstr(t)} has no C form')
            return
        key = self.mg(t)
        if key in self.types:
            return
        if t[0] == 'Tuple':
            for x in t[1]:
                self.need(x)
        elif t[0] == 'Array':
            if not (isinstance(t[1], str) and t[1] in SCALAR_C and t[1] != 'Text'):
                raise Unsupported('arrays hold scalars in the C backend')
            self.arrays[self.mg(t[1])] = SCALAR_C[t[1]]
        elif t[0] == 'Data':
            info = self.m.types[t[1]]
            self.types[key] = t  # guard recursion
            for c, fs in info.ctors.items():
                for _, ft in fs:
                    if ft == t or (isinstance(ft, tuple) and ft[0] == 'Data' and ft[1] == t[1]):
                        raise Unsupported(f'{t[1]} is recursive; recursive data stays in the interpreter')
                    self.need(ft)
            del self.types[key]
        self.types[key] = t
        self.order.append(key)

    def fields(self, c):
        return self.m.ctors[c][1]

    def tag_of(self, c):
        return f'SV_TAG_{c}'

    def is_scalar(self, t):
        return isinstance(t, str) and t in SCALAR_C

    # ---- literals -------------------------------------------------------------
    def lit(self, v, t):
        t = settle(t)
        if v is MAYBE:
            return 'SV_MAYBE'
        if isinstance(v, bool):
            if t == 'Trit':
                return 'SV_TRUE' if v else 'SV_FALSE'
            return 'true' if v else 'false'
        if isinstance(v, str):
            return cstr(v)
        if isinstance(v, float) or t == 'F64':
            f = float(v.v) if isinstance(v, Word) else v
            if math.isnan(f):
                return '(0.0/0.0)'
            if math.isinf(f):
                return '(1.0/0.0)' if f > 0 else '(-1.0/0.0)'
            r = repr(f)
            return r if ('.' in r or 'e' in r) else r + '.0'
        if t == 'Bit':
            return f'((uint8_t){v.v & 1})'
        if t not in INT_TYPES:
            raise Unsupported(f'literal {v.v} at type {tstr(t)}')
        w = Word(v.v, t)
        bits, signed = INT_TYPES[t]
        if signed:
            body = 'INT64_MIN' if w.v == -(1 << 63) else f'INT64_C({w.v})'
        else:
            body = f'UINT64_C({w.v})'
        return f'(({SCALAR_C[t]}){body})'

    # ---- expression types -----------------------------------------------------
    def ty(self, e, want=None):
        t = self.m.etypes.get(id(e), 'Any')
        return self.resolve(t, want)

    def resolve(self, t, want):
        if t == 'Lit':
            if want in NUMERIC:
                return want
            return 'I64'
        if isinstance(t, tuple) and t[0] == 'Tuple':
            ws = want[1] if isinstance(want, tuple) and want[0] == 'Tuple' and len(want[1]) == len(t[1]) \
                else [None] * len(t[1])
            return ('Tuple', tuple(self.resolve(a, b) for a, b in zip(t[1], ws)))
        if t == 'Any':
            if want is not None and want != 'Any':
                return want
            raise Unsupported('a value of unknown type; declare the types for the C backend')
        return t

    # ---- expressions ------------------------------------------------------------
    def ex(self, e, want=None, env=None):
        if want == 'Trit' and self.m.etypes.get(id(e)) == 'Bool':   # Bool is a sub-shape of Trit
            if e.tag == 'Literal':
                return self.lit(e.kids[0], 'Trit')
            return f'sv_trit_of_bool({self._ex(e, want, env)})'
        return self._ex(e, want, env)

    def _ex(self, e, want=None, env=None):
        tag, k = e.tag, e.kids
        m = self.m
        if tag == 'Literal':
            return self.lit(k[0], self.ty(e, want))
        if tag == 'Name':
            n = k[0]
            if n in m.ctors:
                self.need(('Data', m.ctors[n][0]))
                return f'sv_mk_{n}()'
            return f'v_{n}'
        if tag in ARITH:
            t = self.ty(e, want)
            a, b = self.ex(k[0], t, env), self.ex(k[1], t, env)
            if t == 'F64':
                if tag == 'Mod':
                    return f'fmod({a}, {b})'
                return f'({a} {FARITH[tag]} {b})'
            if t == 'Text':
                raise Unsupported('joining text stays in the interpreter')
            return f'sv_{ARITH[tag]}_{self.mg(t)}({a}, {b})'
        if tag in CMP:
            lt = self.m.etypes.get(id(k[0]), 'Any')
            rt = self.m.etypes.get(id(k[1]), 'Any')
            t = lt if lt not in ('Lit', 'Any') else (rt if rt not in ('Lit', 'Any') else 'I64')
            t = self.resolve(t, None)
            a, b = self.ex(k[0], t, env), self.ex(k[1], t, env)
            if self.is_scalar(t):
                return f'({a} {CMP[tag]} {b})'
            if tag not in ('Equal', 'NotEqual'):
                raise Unsupported('ordering compares scalars')
            self.need(t)
            eq = f'sv_eq_{self.mg(t)}({a}, {b})'
            return eq if tag == 'Equal' else f'(!{eq})'
        if tag in ('And', 'Or', 'Not') and self.m.etypes.get(id(e)) == 'Trit':
            args = ', '.join(self.ex(x, 'Trit', env) for x in k)
            return f'sv_k3_{tag.lower()}({args})'
        if tag == 'And':
            return f'({self.ex(k[0], "Bool", env)} && {self.ex(k[1], "Bool", env)})'
        if tag == 'Or':
            return f'({self.ex(k[0], "Bool", env)} || {self.ex(k[1], "Bool", env)})'
        if tag == 'Not':
            return f'(!{self.ex(k[0], "Bool", env)})'
        if tag == 'Decide':
            # in an expression rule: a reply from the world is kept, and counted at the next commit
            return self.decide_call(e, journal=True)
        if tag == 'Negate':
            t = self.ty(e, want)
            a = self.ex(k[0], t, env)
            return f'(-{a})' if t == 'F64' else f'sv_neg_{self.mg(t)}({a})'
        if tag == 'Tuple':
            t = self.ty(e, want)
            if not k:
                raise Unsupported('the empty tuple as a value')
            items = ', '.join(self.ex(x, tt, env) for x, tt in zip(k, t[1]))
            return f'(({self.ct(t)}){{{items}}})'
        if tag == 'Field':
            bt = self.ty(k[0])
            if not (isinstance(bt, tuple) and bt[0] == 'Data'):
                raise Unsupported('field of a non-record')
            c = next(iter(m.types[bt[1]].ctors))
            return f'({self.ex(k[0], bt, env)}).u.{c}.f_{k[1]}'
        if tag == 'Index':
            at = self.ty(k[0])
            return f'(*sv_at_{self.mg(at[1])}({self.ex(k[0], at, env)}, (uint64_t)({self.ex(k[1], None, env)})))'
        if tag == 'Call':
            return self.call(e, want, env)
        if tag == 'Undo':
            return self.clause_call(k[0], env, inverse=True)
        raise Unsupported(f'{tag} stays in the interpreter')

    def decide_call(self, e, journal):
        """One C function per decide site: crisp values pass through; maybe goes to
        the host decider with the printed question, its context and the rules it calls."""
        import json
        from .printer import expr_text, decl_lines
        inner = e.kids[0]
        names = {}

        def walk(x, callee=False):
            if not isinstance(x, Form):
                return
            if x.tag == 'Name':
                n = x.kids[0]
                if not callee and n not in self.m.ctors and n not in self.m.rules:
                    names[n] = settle(self.m.etypes.get(id(x), 'Any'))
                return
            if x.tag == 'Call':
                walk(x.kids[0], callee=True)
                for a in x.kids[1].kids:
                    walk(a)
                return
            for kid in x.kids:
                walk(kid)
        walk(inner)
        order = sorted(names)
        key = id(e)
        if key not in self.decide_fns:
            self.tmp += 1
            fname = f'sv_decide_{self.tmp}'
            called = []

            def calls(x):
                if isinstance(x, Form):
                    if x.tag == 'Call' and x.kids[0].tag == 'Name' and x.kids[0].kids[0] in self.m.rules:
                        if x.kids[0].kids[0] not in called:
                            called.append(x.kids[0].kids[0])
                    for kid in x.kids:
                        calls(kid)
            calls(inner)
            question = expr_text(inner)
            defs = json.dumps(['\n'.join(decl_lines(self.m.rules[n].decl)) for n in called])
            ps = ', '.join(f'{self.ct(names[n])} v_{n}' for n in order)
            ps = (ps + ', ' if ps else '') + 'bool journal, int64_t sv_d'
            body = [f'static bool {fname}({ps}) {{',
                    f'    uint8_t _t = {self.ex(inner, "Trit")};',
                    '    if (_t != SV_MAYBE) return _t == SV_TRUE;',
                    '    char *_c = NULL, *_k = NULL; size_t _cn = 0, _kn = 0;',
                    '    FILE *_co = open_memstream(&_c, &_cn), *_ko = open_memstream(&_k, &_kn);',
                    f'    fputs({cstr(question)}, _ko); fputc(\'\\n\', _ko); fputc(\'{{\', _co);']
            for i, n in enumerate(order):
                self.need(names[n])
                sep = 'fputs(", ", _co); ' if i else ''
                body.append(f'    {{ char *_b = NULL; size_t _bn = 0; FILE *_bo = open_memstream(&_b, &_bn); '
                            f'sv_print_{self.mg(names[n])}(_bo, v_{n}); fclose(_bo); {sep}'
                            f'sv_json_text(_co, {cstr(n)}); fputs(": ", _co); sv_json_text(_co, _b); '
                            f'fprintf(_ko, "%s=%s\\n", {cstr(n)}, _b); free(_b); }}')
            body += ['    fputc(\'}\', _co); fclose(_co); fclose(_ko);',
                     f'    bool _r = sv_decide_world({cstr(question)}, _c, _k, {cstr(defs)}, {e.line or 0});',
                     '    free(_c); free(_k);',
                     '    if (journal) sv_jpush(&_r, 1, 1);',
                     '    return _r;', '}']
            self.decide_fns[key] = (fname, body)
        fname = self.decide_fns[key][0]
        args = [f'v_{n}' for n in order] + ['true' if journal else 'false', 'sv_d']
        return f'{fname}({", ".join(args)})'

    def clause_callee(self, e):
        from .checker import Checker
        return Checker(self.m).clause_callee(e)

    def clause_call(self, e, env, inverse=False):
        cc = self.clause_callee(e)
        rule, params, inp = cc
        self.mark(rule)
        if inverse and rule.cls == 'lossy':
            raise Unsupported(f'undo of lossy {rule.name}')
        args = [self.ex(p, pt, env) for p, (_, pt) in zip(params, rule.params)]
        in_t = rule.returns if inverse else rule.takes
        args.append(self.ex_owned(inp, in_t, env))
        return f'sv_{rule.name}{"_inv" if inverse else ""}({", ".join(args + [DEEPER])})'

    def ex_owned(self, e, t, env=None):
        """An expression whose value is handed over: arrays named here are copied,
        so an expression rule keeps value semantics when a clause rule consumes."""
        t = settle(t)
        if e.tag == 'Name' and isinstance(t, tuple) and t[0] == 'Array':
            return f'sv_arr_copy_{self.mg(t[1])}({self.ex(e, t, env)})'
        if e.tag == 'Tuple' and isinstance(t, tuple) and t[0] == 'Tuple':
            items = ', '.join(self.ex_owned(x, tt, env) for x, tt in zip(e.kids, t[1]))
            return f'(({self.ct(t)}){{{items}}})'
        return self.ex(e, t, env)

    def call(self, e, want, env):
        m = self.m
        f, args = e.kids
        if self.clause_callee(e) is not None:
            return self.clause_call(e, env)
        n = f.kids[0]
        a = args.kids
        if n in WIDENINGS:
            return self.ex(a[0], n, env)
        if n in CONVERSIONS:
            st = self.ty(a[0])
            x = self.ex(a[0], st, env)
            if n == 'F64':
                return f'((double)({x}))'
            if st == 'F64':
                return f'sv_f64_to_{self.mg(n)}({x})'
            if st == 'Bool':
                return f'sv_to_{self.mg(n)}((uint64_t)({x}))'
            return f'sv_to_{self.mg(n)}((uint64_t)({x}))'
        if n in m.ctors:
            self.need(('Data', m.ctors[n][0]))
            vals = [self.ex(x, ft, env) for x, (_, ft) in zip(a, self.fields(n))]
            return f'sv_mk_{n}({", ".join(vals)})'
        if n in m.rules:
            r = m.rules[n]
            self.mark(r)
            vals = [self.ex(x, pt, env) for x, (_, pt) in zip(a, r.params)]
            return f'sv_{n}({", ".join(vals + [DEEPER])})'
        if n == 'array':
            et = a[0].kids[0]
            self.need(('Array', et))
            return f'sv_arr_new_{self.mg(et)}((int64_t)({self.ex(a[1], None, env)}))'
        if n == 'length':
            return f'(({self.ex(a[0], None, env)}).len)'
        if n in ('bitand', 'bitor', 'bitxor'):
            t = self.ty(e, want)
            op = {'bitand': '&', 'bitor': '|', 'bitxor': '^'}[n]
            return f'(({self.ct(t)})({self.ex(a[0], t, env)} {op} {self.ex(a[1], t, env)}))'
        if n in ('shift_left', 'shift_right'):
            t = self.ty(e, want)
            fn = 'shl' if n == 'shift_left' else 'shr'
            return f'sv_{fn}_{self.mg(t)}({self.ex(a[0], t, env)}, (uint64_t)({self.ex(a[1], None, env)}))'
        if n == 'sqrt':
            return f'sqrt({self.ex(a[0], "F64", env)})'
        if n == 'floor':
            return f'floor({self.ex(a[0], "F64", env)})'
        raise Unsupported(f'{n}(...) stays in the interpreter')

    def lvalue(self, t, env):
        if t.tag == 'Name':
            return f'v_{t.kids[0]}'
        if t.tag == 'Index':
            at = self.ty(t.kids[0])
            return f'(*sv_at_{self.mg(at[1])}({self.ex(t.kids[0], at, env)}, (uint64_t)({self.ex(t.kids[1], None, env)})))'
        if t.tag == 'Field':
            bt = self.ty(t.kids[0])
            c = next(iter(self.m.types[bt[1]].ctors))
            return f'{self.lvalue(t.kids[0], env)}.u.{c}.f_{t.kids[1]}'
        raise Unsupported('update target')

    def mark(self, r):
        if r.name not in self.reachable:
            self.reachable.append(r.name)

    # ---- patterns ---------------------------------------------------------------
    def pat_cond(self, p, acc, t):
        tag = p.tag
        if tag == 'Name':
            n = p.kids[0]
            if n in self.m.ctors:
                return [f'({acc}).tag == {self.tag_of(n)}']
            return []
        if tag == 'Literal':
            lt = settle(t) if t != 'Any' else self.resolve(self.m.etypes.get(id(p), 'Any'), None)
            v = p.kids[0]
            if lt == 'F64' or isinstance(v, float):
                return [f'sv_same_f64({acc}, {self.lit(v, "F64")})']
            return [f'({acc}) == {self.lit(v, lt)}']
        if tag == 'Tuple':
            out = []
            ts = t[1] if isinstance(t, tuple) and t[0] == 'Tuple' else ['Any'] * len(p.kids)
            for i, (x, tt) in enumerate(zip(p.kids, ts)):
                out += self.pat_cond(x, f'({acc}).f{i}', tt)
            return out
        if tag == 'Call':
            c = p.kids[0].kids[0]
            out = [f'({acc}).tag == {self.tag_of(c)}']
            for x, (fname, ft) in zip(p.kids[1].kids, self.fields(c)):
                out += self.pat_cond(x, f'({acc}).u.{c}.f_{fname}', ft)
            return out
        raise Unsupported('pattern')

    def pat_bind(self, p, acc, t, lines, pad, declare, types):
        tag = p.tag
        if tag == 'Name':
            n = p.kids[0]
            if n in self.m.ctors:
                return
            vt = settle(types.get(n, t)) if types is not None else settle(t)
            if declare:
                lines.append(f'{pad}{self.ct(vt)} v_{n} = {acc};')
            else:
                lines.append(f'{pad}v_{n} = {acc};')
            return
        if tag == 'Literal':
            return
        if tag == 'Tuple':
            ts = t[1] if isinstance(t, tuple) and t[0] == 'Tuple' else ['Any'] * len(p.kids)
            for i, (x, tt) in enumerate(zip(p.kids, ts)):
                self.pat_bind(x, f'({acc}).f{i}', tt, lines, pad, declare, types)
            return
        if tag == 'Call':
            c = p.kids[0].kids[0]
            for x, (fname, ft) in zip(p.kids[1].kids, self.fields(c)):
                self.pat_bind(x, f'({acc}).u.{c}.f_{fname}', ft, lines, pad, declare, types)
            return
        raise Unsupported('pattern')

    def bind_value(self, p, cexpr, t, lines, pad, declare, types, line, what='pattern'):
        """Bind pattern p to a C expression; literal parts become checks."""
        t = settle(t)
        if p.tag == 'Name' and p.kids[0] not in self.m.ctors:
            self.pat_bind(p, cexpr, t, lines, pad, declare, types)
            return
        self.tmp += 1
        tv = f'_v{self.tmp}'
        lines.append(f'{pad}{self.ct(t)} {tv} = {cexpr};')
        conds = self.pat_cond(p, tv, t)
        if conds:
            lines.append(f'{pad}if (!({" && ".join(conds)})) sv_fault({cstr(f"line {line}: {what} does not match")});')
        self.pat_bind(p, tv, t, lines, pad, declare, types)

    def build(self, p, t, env=None):
        """The C expression that builds a pattern's value (its right-to-left reading)."""
        tag = p.tag
        t = settle(t) if t != 'Any' else self.resolve(self.m.etypes.get(id(p), 'Any'), None)
        if tag == 'Name':
            n = p.kids[0]
            if n in self.m.ctors:
                self.need(('Data', self.m.ctors[n][0]))
                return f'sv_mk_{n}()'
            return f'v_{n}'
        if tag == 'Literal':
            return self.lit(p.kids[0], t)
        if tag == 'Tuple':
            ts = t[1] if isinstance(t, tuple) and t[0] == 'Tuple' else ['Any'] * len(p.kids)
            items = ', '.join(self.build(x, tt) for x, tt in zip(p.kids, ts))
            return f'(({self.ct(t)}){{{items}}})'
        if tag == 'Call':
            c = p.kids[0].kids[0]
            self.need(('Data', self.m.ctors[c][0]))
            vals = [self.build(x, ft) for x, (_, ft) in zip(p.kids[1].kids, self.fields(c))]
            return f'sv_mk_{c}({", ".join(vals)})'
        raise Unsupported('pattern')

    # ---- weights (must agree with the interpreter's) ----------------------------
    def weight_expr(self, cexpr, t, top=None):
        t = settle(t)
        if top is not None and isinstance(t, tuple) and t[0] == 'Data':
            # fewer constructors are possible here than the type declares
            full = clog2(len(self.m.types[t[1]].ctors))
            return f'(sv_weight_{self.mg(t)}({cexpr}) - UINT64_C({full}) + UINT64_C({clog2(top)}))'
        if t == 'Text':
            # an array of bytes: 64 bits for its length and eight a byte, as the interpreter counts
            return f'(UINT64_C(64) + UINT64_C(8) * (uint64_t)strlen({cexpr}))'
        if isinstance(t, str):
            return str({'Bool': 1, 'Trit': 2, 'F64': 64}.get(t, INT_TYPES.get(t, (0,))[0]))
        if t[0] == 'Tuple':
            return '(' + ' + '.join(self.weight_expr(f'({cexpr}).f{i}', x) for i, x in enumerate(t[1])) + ')'
        if t[0] == 'Array':
            w = self.weight_expr('0', t[1])
            return f'(UINT64_C(64) + (uint64_t)({cexpr}).len * {w})'
        if t[0] == 'Data':
            return f'sv_weight_{self.mg(t)}({cexpr})'
        raise Unsupported('weight')

    def jpush(self, cexpr, t, pad, lines, top=None, again=False):
        t = settle(t)
        self.tmp += 1
        tv = f'_j{self.tmp}'
        # the charge (VII.5): nothing where the value can still be computed from what remains
        bits = (lambda: 'UINT64_C(0)') if again else (lambda: self.weight_expr(tv, t, top))
        if isinstance(t, tuple) and t[0] == 'Array':
            lines.append(f'{pad}{{ {self.ct(t)} {tv} = {cexpr}; '
                         f'sv_jpush({tv}.data, sizeof({tv}.data[0]) * (size_t){tv}.len, {bits()}); '
                         f'sv_jpush(&{tv}.len, sizeof {tv}.len, 0); sv_free_{self.mg(t)}({tv}); }}')
            return
        if isinstance(t, tuple) and t[0] == 'Tuple' and any(isinstance(x, tuple) and x[0] == 'Array' for x in t[1]):
            raise Unsupported('discarding a tuple that holds arrays')
        lines.append(f'{pad}{{ {self.ct(t)} {tv} = {cexpr}; sv_jpush(&{tv}, sizeof {tv}, {bits()}); }}')

    # ---- statements -------------------------------------------------------------
    def block(self, b, lines, pad, ctx):
        for s in b.kids:
            self.stmt(s, lines, pad, ctx)

    def stmt(self, s, lines, pad, ctx):
        tag, k, line = s.tag, s.kids, s.line
        m = self.m
        clause = ctx['clause']
        journal = ctx.get('journal', False)
        types = ctx.get('types')
        if tag == 'Let':
            pat, rhs = k
            if clause and self.consuming(s, False, lines, pad, types):
                return
            if rhs.tag in ('Send', 'Ask', 'Instance', 'With', 'Quote'):
                raise Unsupported(f'{rhs.tag.lower()} stays in the interpreter')
            if rhs.tag == 'Decide':
                # a clause rule keeps a decision when its run is journaled; an expression rule
                # (a procedure) always keeps a reply the world gave
                self.bind_value(pat, self.decide_call(rhs, journal or not clause), 'Bool', lines, pad,
                                not clause, types, line)
                if not clause:
                    self.note_vars(pat, ctx)
                return
            t = settle(self.ty(rhs))
            val = self.ex(rhs, t) if rhs.tag == 'Call' else self.ex_owned(rhs, t)
            self.bind_value(pat, val, t, lines, pad, not clause, types, line)
            if not clause:
                self.note_vars(pat, ctx)
            return
        if tag in ('AddTo', 'SubtractFrom', 'Set'):
            target, e = (k[1], k[0]) if tag != 'Set' else (k[0], k[1])
            t = settle(self.ty(target))
            for ti, ri in m.alias_checks.get(id(s), ()):
                lines.append(f'{pad}if (({self.ex(ti)}) == ({self.ex(ri)})) '
                             f'sv_fault({cstr(f"line {line}: R4: the update reads its own target")});')
            lv = self.lvalue(target, None)
            val = self.ex(e, t)
            if tag == 'Set':
                if journal:
                    self.jpush(lv, t, pad, lines)
                elif isinstance(t, tuple) and t[0] == 'Array':
                    if e.tag != 'Call':
                        val = self.ex_owned(e, t)
                    lines.append(f'{pad}{{ {self.ct(t)} _old = {lv}; {lv} = {val}; sv_free_{self.mg(t)}(_old); }}')
                    return
                lines.append(f'{pad}{lv} = {val};')
                return
            if t == 'F64':
                if journal:
                    self.jpush(lv, t, pad, lines)
                op = '+' if tag == 'AddTo' else '-'
                lines.append(f'{pad}{lv} = {lv} {op} {val};')
                return
            fn = 'add' if tag == 'AddTo' else 'sub'
            lines.append(f'{pad}{lv} = sv_{fn}_{self.mg(t)}({lv}, {val});')
            return
        if tag == 'Swap':
            t = settle(self.ty(k[0]))
            a, b = self.lvalue(k[0], None), self.lvalue(k[1], None)
            lines.append(f'{pad}{{ {self.ct(t)} _s = {a}; {a} = {b}; {b} = _s; }}')
            return
        if tag == 'Was':
            self.was(s, lines, pad, ctx)
            return
        if tag == 'Restore':
            raise Unsupported('taking back what was discarded stays in the interpreter')
        if tag == 'Discard':
            n = k[0]
            t = settle(types[n] if types and n in types else ctx['vt'].get(n, 'Any'))
            if journal:
                _, top, again = m.drops.get(id(s), (t, None, False))
                self.jpush(f'v_{n}', t, pad, lines, top, again)
            elif isinstance(t, tuple) and t[0] == 'Array':
                lines.append(f'{pad}sv_free_{self.mg(t)}(v_{n});')
            return
        if tag == 'Output':
            t = settle(self.ty(k[0]))
            self.need(t)
            lines.append(f'{pad}sv_print_{self.mg(t)}(stdout, {self.ex(k[0], t)}); putchar(\'\\n\'); sv_commit();')
            return
        if tag == 'Commit':
            lines.append(f'{pad}sv_commit();')
            return
        if tag == 'If':
            lines.append(f'{pad}if ({self.ex(k[0], "Bool")}) {{')
            self.scoped(k[1], lines, pad + '    ', ctx)
            if k[2].kids:
                lines.append(f'{pad}}} else {{')
                self.scoped(k[2], lines, pad + '    ', ctx)
            lines.append(f'{pad}}}')
            return
        if tag == 'RepeatWith':
            var, lo, hi, body = k
            t = settle(m.etypes.get(id(s), 'I64'))
            c = self.ct(t)
            self.tmp += 1
            i = self.tmp
            lines.append(f'{pad}{{ {c} _lo{i} = {self.ex(lo, t)}, _hi{i} = {self.ex(hi, t)};')
            lines.append(f'{pad}  if (_lo{i} <= _hi{i}) for ({c} v_{var} = _lo{i};; v_{var}++) {{')
            vt = ctx['vt']
            vt[var] = t
            self.scoped(body, lines, pad + '    ', ctx)
            lines.append(f'{pad}    if (v_{var} == _hi{i}) break;')
            lines.append(f'{pad}  }}')
            lines.append(f'{pad}}}')
            return
        if tag == 'RepeatDown':
            var, first, last, body = k
            t = settle(m.etypes.get(id(s), 'I64'))
            c = self.ct(t)
            self.tmp += 1
            i = self.tmp
            lines.append(f'{pad}{{ {c} _first{i} = {self.ex(first, t)}, _last{i} = {self.ex(last, t)};')
            lines.append(f'{pad}  if (_first{i} >= _last{i}) for ({c} v_{var} = _first{i};; v_{var}--) {{')
            ctx['vt'][var] = t
            self.scoped(body, lines, pad + '    ', ctx)
            lines.append(f'{pad}    if (v_{var} == _last{i}) break;')
            lines.append(f'{pad}  }}')
            lines.append(f'{pad}}}')
            return
        if tag == 'RepeatWhile':
            lines.append(f'{pad}while ({self.ex(k[0], "Bool")}) {{')
            self.scoped(k[1], lines, pad + '    ', ctx)
            lines.append(f'{pad}}}')
            return
        if tag == 'Do':
            lines.append(f'{pad}(void)({self.ex(k[0])});')
            return
        raise Unsupported(f'{tag} stays in the interpreter')

    def note_vars(self, p, ctx):
        if p.tag == 'Name' and p.kids[0] not in self.m.ctors:
            ctx['vt'][p.kids[0]] = settle(self.m.etypes.get(id(p), 'Any'))
        elif p.tag == 'Tuple':
            for x in p.kids:
                self.note_vars(x, ctx)
        elif p.tag == 'Call':
            for x in p.kids[1].kids:
                self.note_vars(x, ctx)

    def scoped(self, b, lines, pad, ctx):
        saved = dict(ctx['vt'])
        self.block(b, lines, pad, ctx)
        ctx['vt'] = saved

    def consuming(self, s, back, lines, pad, types):
        """`p is g(x)` / `p was g(x)` (and with `undo g`): build one side, call g or its
        derived inverse, bind the other side."""
        (pat, rhs), line = s.kids, s.line
        inner = rhs.kids[0] if rhs.tag == 'Undo' else rhs
        cc = self.clause_callee(inner) if inner.tag == 'Call' else None
        if cc is None:
            return False
        rule, params, inp = cc
        self.mark(rule)
        inv = back != (rhs.tag == 'Undo')
        if inv and rule.cls == 'lossy':
            raise Unsupported(f'taking back lossy {rule.name} (rewind stays in the interpreter)')
        src, dst = (pat, inp) if back else (inp, pat)
        args = [self.ex(p, pt) for p, (_, pt) in zip(params, rule.params)]
        args.append(self.build(src, rule.returns if inv else rule.takes))
        call = f'sv_{rule.name}{"_inv" if inv else ""}({", ".join(args + [DEEPER])})'
        self.bind_value(dst, call, rule.takes if inv else rule.returns, lines, pad, False, types, line)
        return True

    def was(self, s, lines, pad, ctx):
        """The backward reading of `is`, compiled forward like any other step."""
        (pat, rhs), line = s.kids, s.line
        if self.consuming(s, True, lines, pad, ctx['types']):
            return
        if rhs.tag in ('Send', 'Ask', 'Decide', 'Instance'):
            raise Unsupported(f'taking back {rhs.tag.lower()} stays in the interpreter')
        t = settle(self.ty(rhs))
        if id(s) not in self.m.proved:
            built = self.build(pat, t)
            want = self.ex(rhs, t)
            if self.is_scalar(t):
                cond = self.eq_expr(built, want, t, same=True)
            else:
                self.need(t)
                cond = f'sv_same_{self.mg(t)}({built}, {want})'
                if isinstance(t, tuple) and t[0] == 'Array' and rhs.tag != 'Name':
                    self.tmp += 1
                    lines.append(f'{pad}{{ {self.ct(t)} _w{self.tmp} = {want};')
                    cond = f'sv_same_{self.mg(t)}({built}, _w{self.tmp})'
                    lines.append(f'{pad}  if (!({cond})) sv_fault({cstr(f"line {line}: value is not what it was computed from")});')
                    lines.append(f'{pad}  sv_free_{self.mg(t)}(_w{self.tmp}); }}')
                    cond = None
            if cond:
                lines.append(f'{pad}if (!({cond})) sv_fault({cstr(f"line {line}: value is not what it was computed from")});')
        if pat.tag == 'Name' and isinstance(t, tuple) and t[0] == 'Array':
            lines.append(f'{pad}sv_free_{self.mg(t)}(v_{pat.kids[0]});')

    # ---- rules -------------------------------------------------------------------
    def sig(self, r, inverse=False):
        ps = [f'{self.ct(pt)} v_{pn}' for pn, pt in r.params]
        if r.kind == 'clauses':
            in_t = r.returns if inverse else r.takes
            out_t = r.takes if inverse else r.returns
            if in_t == 'Any' or out_t == 'Any':
                raise Unsupported(f'{r.name} needs `takes` and `returns` for the C backend')
            ps.append(f'{self.ct(in_t)} in')
            ret = self.ct(out_t)
        else:
            ret = self.ct(r.returns) if r.returns != 'Unit' else 'void'
        for pn, pt in r.params:
            if pt == 'Any':
                raise Unsupported(f'parameter {pn} of {r.name} needs a type for the C backend')
        return f'static {ret} sv_{r.name}{"_inv" if inverse else ""}({", ".join(ps + ["int64_t sv_d"])})'

    def loop_vars(self, b, out):
        for s in b.kids:
            if s.tag in ('RepeatWith', 'RepeatDown'):
                out.add(s.kids[0])
            for k in s.kids:
                if isinstance(k, Form) and k.tag == 'Block':
                    self.loop_vars(k, out)
        return out

    def clause_rule(self, r, inverse):
        """A clause rule, or its inverse: the code `invert` derived, compiled forward."""
        lines = [self.sig(r, inverse) + ' {', ENTER]
        rr = r.inverse if inverse else r
        lossy = rr.cls == 'lossy'
        for ci, c in enumerate(rr.clauses):
            src, dst, steps = c.kids
            src_t, dst_t = rr.takes, rr.returns
            types = rr.var_types[id(c)]
            conds = self.pat_cond(src, 'in', src_t)
            lines.append(f'    if ({" && ".join(conds) if conds else "true"}) {{')
            loops = self.loop_vars(steps, set())
            params = {pn for pn, _ in r.params}
            for n, t in sorted(types.items()):
                if n in params or n in loops:
                    continue
                lines.append(f'        {self.ct(settle(t))} v_{n};')
            sub = []
            self.pat_bind(src, 'in', src_t, sub, '        ', False, types)
            lines += sub
            ctx = {'clause': True, 'journal': lossy, 'types': types, 'vt': dict(types)}
            self.block(steps, lines, '        ', ctx)
            if rr.journal_choice:
                # the choice is lost only among the clauses whose right side this output matches
                lines.append(f'        {self.ct(settle(dst_t))} _out = {self.build(dst, dst_t)};')
                lines.append('        uint64_t _n = 0;')
                for other in rr.clauses:
                    oc = self.pat_cond(other.kids[1], '_out', dst_t)
                    lines.append(f'        _n += ({" && ".join(oc) if oc else "true"}) ? 1 : 0;')
                lines.append(f'        if (_n > 1) {{ uint32_t _c = {ci}; sv_jpush(&_c, sizeof _c, sv_clog2(_n)); }}')
                lines.append('        return _out;')
            else:
                lines.append(f'        return {self.build(dst, dst_t)};')
            lines.append('    }')
        what = 'is not in its image' if inverse else 'matches no clause'
        lines.append(f'    sv_fault({cstr(f"{r.name}: the value {what}")});')
        lines.append('}')
        return lines

    def tail_self(self, e, r):
        return e.tag == 'Call' and e.kids[0].tag == 'Name' and e.kids[0].kids[0] == r.name

    def expr_rule(self, r):
        lines = [self.sig(r) + ' {', ENTER]
        body = []
        ctx = {'clause': False, 'journal': False, 'types': None, 'vt': {pn: pt for pn, pt in r.params},
               'tail': False}
        self.result_block(r.block, body, '    ', ctx, r)
        if ctx['tail']:
            lines.append('sv_top:;')     # a self tail call comes back here: the same invocation
        lines += body
        lines.append('}')
        return lines

    def result_block(self, b, lines, pad, ctx, r):
        n = len(b.kids)
        for i, s in enumerate(b.kids):
            last = i == n - 1
            if last and s.tag == 'Do' and r.returns != 'Unit':
                self.ret(s.kids[0], lines, pad, ctx, r)
                return
            if last and s.tag == 'If' and s.kids[2].kids and r.returns != 'Unit':
                lines.append(f'{pad}if ({self.ex(s.kids[0], "Bool")}) {{')
                saved = dict(ctx['vt'])
                self.result_block(s.kids[1], lines, pad + '    ', ctx, r)
                ctx['vt'] = dict(saved)
                lines.append(f'{pad}}} else {{')
                self.result_block(s.kids[2], lines, pad + '    ', ctx, r)
                ctx['vt'] = saved
                lines.append(f'{pad}}}')
                return
            self.stmt(s, lines, pad, ctx)

    def ret(self, e, lines, pad, ctx, r):
        if self.tail_self(e, r):
            args = e.kids[1].kids
            tmps = []
            for (pn, pt), a in zip(r.params, args):
                self.tmp += 1
                tv = f'_a{self.tmp}'
                lines.append(f'{pad}{self.ct(pt)} {tv} = {self.ex(a, pt)};')
                tmps.append((pn, tv))
            for pn, tv in tmps:
                lines.append(f'{pad}v_{pn} = {tv};')
            lines.append(f'{pad}goto sv_top;')
            ctx['tail'] = True
            return
        if e.tag == 'Name' and e.kids[0] in dict(r.params):
            lines.append(f'{pad}return {self.ex_owned(e, r.returns)};')
            return
        lines.append(f'{pad}return {self.ex(e, r.returns)};')

    # ---- type support functions ---------------------------------------------------
    def type_defs(self):
        out = []
        for en, ec in self.arrays.items():
            out.append(f'SV_ARR({ec}, {en})')
        done = set()
        for key in self.order:
            if key in done:
                continue
            done.add(key)
            t = self.types[key]
            if t[0] == 'Tuple':
                fs = ' '.join(f'{self.ct(x)} f{i};' for i, x in enumerate(t[1]))
                out.append(f'typedef struct {{ {fs} }} sv_{key};')
            elif t[0] == 'Data':
                info = self.m.types[t[1]]
                tags = ', '.join(self.tag_of(c) for c in info.ctors)
                out.append(f'enum {{ {tags} }};')
                arms = []
                for c, fs in info.ctors.items():
                    if fs:
                        arms.append(f'struct {{ {" ".join(f"{self.ct(ft)} f_{fn};" for fn, ft in fs)} }} {c};')
                union = f' union {{ {" ".join(arms)} }} u;' if arms else ''
                out.append(f'typedef struct {{ uint32_t tag;{union} }} sv_{key};')
                for c, fs in info.ctors.items():
                    ps = ', '.join(f'{self.ct(ft)} f_{fn}' for fn, ft in fs) or 'void'
                    init = ', '.join(f'.f_{fn} = f_{fn}' for fn, _ in fs)
                    body = f'sv_{key} v = {{ .tag = {self.tag_of(c)} }};'
                    if fs:
                        body += f' v.u.{c} = (typeof(v.u.{c})){{ {init} }};'
                    out.append(f'static inline sv_{key} sv_mk_{c}({ps}) {{ {body} return v; }}')
        return out

    def eq_fn(self, t, key):
        """Two functions per aggregate: sv_eq_ for the `=` operator (IEEE on floats) and
        sv_same_ for `was` and patterns (equality on the canonical form)."""
        out = []
        for name, same in (('eq', False), ('same', True)):
            if t[0] == 'Tuple':
                parts = [self.eq_expr(f'a.f{i}', f'b.f{i}', x, same) for i, x in enumerate(t[1])]
                out.append(f'static inline bool sv_{name}_{key}(sv_{key} a, sv_{key} b) '
                           f'{{ return {" && ".join(parts) or "true"}; }}')
            elif t[0] == 'Data':
                info = self.m.types[t[1]]
                arms = []
                for c, fs in info.ctors.items():
                    parts = [self.eq_expr(f'a.u.{c}.f_{fn}', f'b.u.{c}.f_{fn}', ft, same) for fn, ft in fs]
                    arms.append(f'case {self.tag_of(c)}: return {" && ".join(parts) or "true"};')
                out.append(f'static inline bool sv_{name}_{key}(sv_{key} a, sv_{key} b) '
                           f'{{ if (a.tag != b.tag) return false; switch (a.tag) {{ {" ".join(arms)} }} return false; }}')
        return '\n'.join(out)

    def eq_expr(self, a, b, t, same=False):
        t = settle(t)
        if self.is_scalar(t):
            return f'sv_same_f64({a}, {b})' if same and t == 'F64' else f'({a} == {b})'
        return f'sv_{"same" if same else "eq"}_{self.mg(t)}({a}, {b})'

    def print_fn(self, t, key):
        def item(acc, x):
            x = settle(x)
            if isinstance(x, str) and x == 'Text':
                return f'fprintf(o, "\\"%s\\"", {acc});'
            return f'sv_print_{self.mg(x)}(o, {acc});'
        if t[0] == 'Tuple':
            parts = []
            for i, x in enumerate(t[1]):
                if i:
                    parts.append('fputs(", ", o);')
                parts.append(item(f'v.f{i}', x))
            if len(t[1]) == 1:
                parts.append('fputc(\',\', o);')
            return f'static void sv_print_{key}(FILE *o, sv_{key} v) {{ fputc(\'(\', o); {" ".join(parts)} fputc(\')\', o); }}'
        if t[0] == 'Array':
            return (f'static void sv_print_{key}(FILE *o, sv_{key} v) {{ fputc(\'[\', o); for (int64_t i = 0; i < v.len; i++) '
                    f'{{ if (i) fputs(", ", o); {item("v.data[i]", t[1])} }} fputc(\']\', o); }}')
        if t[0] == 'Data':
            info = self.m.types[t[1]]
            arms = []
            for c, fs in info.ctors.items():
                parts = [f'fputs("{c}", o);']
                if fs:
                    parts.append('fputc(\'(\', o);')
                    for i, (fn, ft) in enumerate(fs):
                        if i:
                            parts.append('fputs(", ", o);')
                        parts.append(item(f'v.u.{c}.f_{fn}', ft))
                    parts.append('fputc(\')\', o);')
                arms.append(f'case {self.tag_of(c)}: {" ".join(parts)} break;')
            return f'static void sv_print_{key}(FILE *o, sv_{key} v) {{ switch (v.tag) {{ {" ".join(arms)} }} }}'
        return ''

    def weight_fn(self, t, key):
        if t[0] != 'Data':
            return ''
        info = self.m.types[t[1]]
        arms = []
        for c, fs in info.ctors.items():
            parts = [f'UINT64_C({clog2(len(info.ctors))})'] + [self.weight_expr(f'v.u.{c}.f_{fn}', ft) for fn, ft in fs]
            arms.append(f'case {self.tag_of(c)}: return {" + ".join(parts)};')
        return f'static inline uint64_t sv_weight_{key}(sv_{key} v) {{ switch (v.tag) {{ {" ".join(arms)} }} return 0; }}'


def emit_program(m, entry='main'):
    g = CGen(m)
    if entry not in m.rules:
        raise Unsupported(f'no rule {entry}')
    g.mark(m.rules[entry])
    bodies = []
    protos = []
    done = set()
    i = 0
    while i < len(g.reachable):
        name = g.reachable[i]
        i += 1
        if name in done:
            continue
        done.add(name)
        r = m.rules[name]
        try:
            if r.kind == 'clauses':
                protos.append(g.sig(r) + ';')
                bodies.append(g.clause_rule(r, False))
                if r.cls != 'lossy':
                    protos.append(g.sig(r, True) + ';')
                    bodies.append(g.clause_rule(r, True))
            else:
                protos.append(g.sig(r) + ';')
                bodies.append(g.expr_rule(r))
        except Unsupported as e:
            raise Unsupported(f'{name}: {e}') from None
    # make sure every compound type has its helpers
    for key in list(g.order):
        g.need(g.types[key])
    out = ['/* Generated by the Selvage C23 backend. Every certified rule has a derived inverse (_inv). */',
           '#include "selvage_rt.h"', '']
    out += g.type_defs()
    for key in g.order:
        t = g.types[key]
        for fn in (g.eq_fn(t, key), g.weight_fn(t, key)):
            if fn:
                out.append(fn)
    for key in g.order:
        fn = g.print_fn(g.types[key], key)
        if fn:
            out.append(fn)
    out.append('')
    out += protos
    out.append('')
    for fname, body in g.decide_fns.values():
        out += body
        out.append('')
    for b in bodies:
        out += b
        out.append('')
    main = m.rules[entry]
    call = f'sv_{entry}(1);' if main.returns == 'Unit' else f'(void)sv_{entry}(1);'
    out.append(f'static void sv_main_(void) {{ {call} }}')
    out.append('int main(void) { atexit(sv_report); sv_start(sv_main_); return 0; }')
    return '\n'.join(out) + '\n'
