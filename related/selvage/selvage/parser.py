"""Parser: text -> forms.

The syntax tree is made of the same Form values a program manipulates, so a
quoted expression is ordinary data and a pattern is an ordinary expression form.
"""
from .forms import Form, Word, MAYBE
from .lexer import lex, SyntaxFault

KEYWORDS = {
    'rule', 'type', 'takes', 'returns', 'uses', 'is', 'where', 'add', 'to', 'subtract',
    'from', 'swap', 'and', 'was', 'discarded', 'down', 'discard', 'set', 'output', 'commit', 'if', 'otherwise', 'repeat', 'with', 'while', 'not', 'or', 'mod',
    'ask', 'answer', 'for', 'request', 'undo', 'quote', 'true', 'false', 'maybe', 'decide',
}

BINOPS = {'=': 'Equal', 'not=': 'NotEqual', '<': 'Less', '>': 'Greater',
          '<=': 'LessEqual', '>=': 'GreaterEqual'}


def F(tag, *kids, line=None):
    return Form(tag, kids, line)


class Parser:
    def __init__(self, src):
        self.toks = lex(src)
        self.i = 0

    # ---- token helpers -------------------------------------------------
    @property
    def tok(self):
        return self.toks[self.i]

    def peek(self, k=1):
        return self.toks[min(self.i + k, len(self.toks) - 1)]

    def at(self, kind, val=None):
        t = self.tok
        return t.kind == kind and (val is None or t.val == val)

    def at_word(self, w):
        return self.at('NAME', w)

    def take(self, kind=None, val=None):
        t = self.tok
        if kind and (t.kind != kind or (val is not None and t.val != val)):
            want = val if val is not None else kind
            got = t.val if t.val is not None else t.kind
            raise SyntaxFault(f'line {t.line}: expected {want!r}, found {got!r}')
        self.i += 1
        return t

    def word(self, w):
        return self.take('NAME', w)

    def name(self):
        t = self.take('NAME')
        if t.val in KEYWORDS:
            raise SyntaxFault(f'line {t.line}: {t.val!r} is a keyword, not a name')
        return t.val

    def skip_newlines(self):
        while self.at('NEWLINE'):
            self.i += 1

    # ---- program -------------------------------------------------------
    def program(self):
        decls = []
        self.skip_newlines()
        while not self.at('EOF'):
            decls.append(self.decl())
            self.skip_newlines()
        return F('Program', *decls)

    def decl(self):
        t = self.tok
        if self.at_word('rule'):
            return self.rule_decl()
        if self.at_word('type'):
            return self.type_decl()
        if self.at_word('request'):
            return self.request_decl()
        if self.at_word('answer'):
            return self.answer_decl()
        raise SyntaxFault(f'line {t.line}: expected rule, type, request or answer')

    def typeexpr(self):
        if self.at('OP', '('):
            self.take()
            items = []
            while not self.at('OP', ')'):
                items.append(self.typeexpr())
                if not self.at('OP', ')'):
                    self.take('OP', ',')
            self.take('OP', ')')
            return F('TupleType', *items)
        n = self.take('NAME').val
        if self.at('OP', '('):
            self.take()
            args = [self.typeexpr()]
            while self.at('OP', ','):
                self.take()
                args.append(self.typeexpr())
            self.take('OP', ')')
            return F('TypeApp', n, *args)
        return F('TypeName', n)

    def fields(self):
        self.take('OP', '(')
        out = []
        while not self.at('OP', ')'):
            fname = self.name()
            self.take('OP', ':')
            out.append(F('Field', fname, self.typeexpr()))
            if not self.at('OP', ')'):
                self.take('OP', ',')
        self.take('OP', ')')
        return out

    def type_decl(self):
        line = self.word('type').line
        tname = self.name()
        fields = self.fields() if self.at('OP', '(') else None
        parent = None
        if self.at('OP', '<-'):
            self.take()
            parent = 'undo ' if self.at_word('undo') else ''
            if parent:
                self.take()
            parent += self.name()
        ctors = []
        self.take('NEWLINE')
        if fields is not None or parent is not None:
            ctors.append(F('Ctor', tname, F('Fields', *(fields or []))))
        if self.at('INDENT'):
            if ctors:
                raise SyntaxFault(f'line {line}: a record type has no constructor block')
            self.take()
            while not self.at('DEDENT'):
                cname = self.name()
                cf = self.fields() if self.at('OP', '(') else []
                self.take('NEWLINE')
                ctors.append(F('Ctor', cname, F('Fields', *cf)))
            self.take('DEDENT')
        if not ctors:
            raise SyntaxFault(f'line {line}: type {tname} has no constructors')
        return F('TypeDecl', tname, F('Ctors', *ctors), parent or '', line=line)

    def params(self):
        out = []
        if not self.at('OP', '('):
            return out
        self.take()
        while not self.at('OP', ')'):
            pname = self.name()
            ptype = None
            if self.at('OP', ':'):
                self.take()
                ptype = self.typeexpr()
            out.append(F('Param', pname, ptype if ptype is not None else F('TypeName', '')))
            if not self.at('OP', ')'):
                self.take('OP', ',')
        self.take('OP', ')')
        return out

    def rule_decl(self):
        line = self.word('rule').line
        backward = False
        if self.at_word('undo'):      # a derived inverse, as `invert` prints it
            self.take()
            backward = True
        rname = ('undo ' if backward else '') + self.name()
        params = self.params()
        takes = returns = None
        uses = []
        while True:
            if self.at_word('takes'):
                self.take()
                takes = self.typeexpr()
            elif self.at_word('returns'):
                self.take()
                returns = self.typeexpr()
            elif self.at_word('uses'):
                self.take()
                uses.append(self.take('NAME').val)
                while self.at('OP', ','):
                    self.take()
                    uses.append(self.take('NAME').val)
            else:
                break
        self.take('NEWLINE')
        self.take('INDENT')
        body = self.rule_body()
        self.take('DEDENT')
        none = F('TypeName', '')
        return F('RuleDecl', rname, F('Params', *params), takes or none, returns or none,
                 F('Uses', *uses), body, line=line)

    def rule_body(self):
        # A clause line has `<->` or `=>` at its top level.
        save = self.i
        first_is_clause = False
        try:
            self.expr()
            first_is_clause = self.at('OP', '<->') or self.at('OP', '=>')
        except SyntaxFault:
            first_is_clause = False
        self.i = save
        if first_is_clause:
            clauses = []
            while not self.at('DEDENT'):
                clauses.append(self.clause())
            return F('Clauses', *clauses)
        return self.block_items()

    def clause(self):
        line = self.tok.line
        left = self.expr()
        # `<->`: a clause of a certified rule.  `=>`: a clause of a lossy rule.
        tag = 'LossyClause' if self.at('OP', '=>') else 'Clause'
        self.take('OP', '=>' if tag == 'LossyClause' else '<->')
        right = self.expr()
        steps = F('Block')
        if self.at_word('where'):
            self.take()
            self.take('NEWLINE')
            steps = self.block()
        else:
            self.take('NEWLINE')
        return F(tag, left, right, steps, line=line)

    def request_decl(self):
        line = self.word('request').line
        g = self.name()
        sealed = []
        if self.at_word('for'):      # `request G for A`: the group is sealed to the answer A
            self.take()
            sealed = [F('SealedTo', self.name())]
        self.take('NEWLINE')
        self.take('INDENT')
        ops = []
        while not self.at('DEDENT'):
            op = self.name()
            ps = self.params()
            ret = F('TypeName', '')
            if self.at_word('returns'):
                self.take()
                ret = self.typeexpr()
            self.take('NEWLINE')
            ops.append(F('Op', op, F('Params', *ps), ret))
        self.take('DEDENT')
        return F('RequestDecl', g, *ops, *sealed, line=line)

    def answer_decl(self):
        line = self.word('answer').line
        backward = False
        if self.at_word('undo'):
            self.take()
            backward = True
        aname = ('undo ' if backward else '') + self.name()
        params = self.params()
        if self.at('OP', '<-'):
            raise SyntaxFault(f'line {line}: `<-` derives record types; an answer shares behaviour by '
                              f'delegating to an instance it holds in its state')
        self.word('for')
        groups = [self.name()]
        while self.at('OP', ','):
            self.take()
            groups.append(self.name())
        state = F('TypeName', '')
        if self.at_word('takes'):
            self.take()
            state = self.typeexpr()
        self.take('NEWLINE')
        clauses = []
        if self.at('INDENT'):      # an answer without clauses delegates every request
            self.take('INDENT')
            while not self.at('DEDENT'):
                clauses.append(self.clause())
            self.take('DEDENT')
        return F('AnswerDecl', aname, F('Params', *params), F('Groups', *groups), state, F('Clauses', *clauses),
                 line=line)

    # ---- blocks and statements ------------------------------------------
    def block(self):
        self.take('INDENT')
        b = self.block_items()
        self.take('DEDENT')
        return b

    def block_items(self):
        items = []
        while not self.at('DEDENT') and not self.at('EOF'):
            items.append(self.stmt())
        return F('Block', *items)

    def target(self):
        line = self.tok.line
        t = F('Name', self.name(), line=line)
        while True:
            if self.at('OP', '.'):
                self.take()
                t = F('Field', t, self.name(), line=line)
            elif self.at('OP', '['):
                self.take()
                idx = self.expr()
                self.take('OP', ']')
                t = F('Index', t, idx, line=line)
            else:
                return t

    def stmt(self):
        t = self.tok
        line = t.line
        w = t.val if t.kind == 'NAME' else None
        if w == 'add':
            self.take()
            e = self.expr()
            self.word('to')
            s = F('AddTo', e, self.target(), line=line)
        elif w == 'subtract':
            self.take()
            e = self.expr(no_from=True)
            self.word('from')
            s = F('SubtractFrom', e, self.target(), line=line)
        elif w == 'set':
            self.take()
            tg = self.target()
            self.word('to')
            s = F('Set', tg, self.expr(), line=line)
        elif w == 'swap':
            self.take()
            a = self.target()
            self.word('and')
            s = F('Swap', a, self.target(), line=line)
        elif w == 'discard':
            self.take()
            s = F('Discard', self.name(), line=line)
        elif w == 'output':
            self.take()
            s = F('Output', self.expr(), line=line)
        elif w == 'commit':
            self.take()
            s = F('Commit', line=line)
        elif w == 'if':
            return self.if_stmt()
        elif w == 'repeat':
            return self.repeat_stmt()
        else:
            e = self.expr()
            if self.at_word('is'):
                self.take()
                s = F('Let', e, self.expr(), line=line)
            elif self.at_word('was'):
                self.take()
                if self.at_word('discarded'):
                    # the backward reading of `discard x`: a step of its own, so code that
                    # reads code can tell it from every other `was`
                    self.take()
                    if e.tag != 'Name':
                        raise SyntaxFault(f'line {line}: `was discarded` gives back one name, as `discard` takes one')
                    s = F('Restore', e.kids[0], line=line)
                else:
                    s = F('Was', e, self.expr(), line=line)
            else:
                s = F('Do', e, line=line)
        self.take('NEWLINE')
        return s

    def if_stmt(self):
        line = self.word('if').line
        cond = self.expr()
        self.take('NEWLINE')
        then = self.block()
        other = F('Block')
        if self.at_word('otherwise'):
            self.take()
            if self.at_word('if'):
                other = F('Block', self.if_stmt())
            else:
                self.take('NEWLINE')
                other = self.block()
        return F('If', cond, then, other, line=line)

    def repeat_stmt(self):
        # a counted loop, or one that runs while a condition holds; `repeat n times` is
        # `repeat with i from 1 to n`
        line = self.word('repeat').line
        if self.at_word('while'):
            self.take()
            cond = self.expr()
            self.take('NEWLINE')
            return F('RepeatWhile', cond, self.block(), line=line)
        if not self.at_word('with'):
            raise SyntaxFault(f'line {line}: a loop is `repeat with i from a to b` or `repeat while c`; '
                              f'to repeat n times, count from 1 to n')
        self.take()
        var = self.name()
        self.word('from')
        first = self.expr()
        down = False
        if self.at_word('down'):
            self.take()
            down = True
        self.word('to')
        last = self.expr()
        self.take('NEWLINE')
        if down:   # counts from first down to last; the backward reading of counting up
            return F('RepeatDown', var, first, last, self.block(), line=line)
        return F('RepeatWith', var, first, last, self.block(), line=line)

    # ---- expressions ------------------------------------------------------
    def expr(self, no_from=False):
        line = self.tok.line
        e = self.from_expr(no_from)
        if self.at_word('with'):
            self.take()
            e = F('With', e, self.from_expr(False), line=line)
        return e

    def from_expr(self, no_from):
        line = self.tok.line
        e = self.or_expr()
        if not no_from and self.at_word('from'):
            self.take()
            e = F('Instance', e, self.or_expr(), line=line)
        return e

    def or_expr(self):
        e = self.and_expr()
        while self.at_word('or'):
            line = self.take().line
            e = F('Or', e, self.and_expr(), line=line)
        return e

    def and_expr(self):
        e = self.not_expr()
        while self.at_word('and'):
            line = self.take().line
            e = F('And', e, self.not_expr(), line=line)
        return e

    def not_expr(self):
        if self.at_word('not'):
            line = self.take().line
            return F('Not', self.not_expr(), line=line)
        return self.cmp_expr()

    def cmp_expr(self):
        e = self.sum_expr()
        if self.tok.kind == 'OP' and self.tok.val in BINOPS:
            t = self.take()
            e = F(BINOPS[t.val], e, self.sum_expr(), line=t.line)
        return e

    def sum_expr(self):
        e = self.term()
        while self.tok.kind == 'OP' and self.tok.val in ('+', '-'):
            t = self.take()
            e = F('Add' if t.val == '+' else 'Subtract', e, self.term(), line=t.line)
        return e

    def term(self):
        e = self.unary()
        while (self.tok.kind == 'OP' and self.tok.val in ('*', '/')) or self.at_word('mod'):
            t = self.take()
            tag = {'*': 'Multiply', '/': 'Divide', 'mod': 'Mod'}[t.val]
            e = F(tag, e, self.unary(), line=t.line)
        return e

    def unary(self):
        if self.at('OP', '-'):
            line = self.take().line
            inner = self.unary()
            if inner.tag == 'Literal' and isinstance(inner.kids[0], Word):
                w = inner.kids[0]
                return F('Literal', Word(-w.v, w.ty, w.flex), line=line)
            if inner.tag == 'Literal' and isinstance(inner.kids[0], float):
                return F('Literal', -inner.kids[0], line=line)
            return F('Negate', inner, line=line)
        return self.postfix()

    def args(self):
        self.take('OP', '(')
        out = []
        while not self.at('OP', ')'):
            out.append(self.expr())
            if not self.at('OP', ')'):
                self.take('OP', ',')
        self.take('OP', ')')
        return out

    def postfix(self):
        e = self.primary()
        while True:
            line = self.tok.line
            if self.at('OP', '('):
                e = F('Call', e, F('Tuple', *self.args()), line=line)
            elif self.at('OP', '.'):
                self.take()
                e = F('Field', e, self.name(), line=line)
            elif self.at('OP', '['):
                self.take()
                idx = self.expr()
                self.take('OP', ']')
                e = F('Index', e, idx, line=line)
            elif self.at('OP', '->'):
                self.take()
                op = self.name()
                a = self.args() if self.at('OP', '(') else []
                e = F('Send', e, F('Request', op, F('Tuple', *a)), line=line)
            else:
                return e

    def primary(self):
        t = self.tok
        line = t.line
        if t.kind == 'INT':
            self.take()
            return F('Literal', Word(t.val, 'I64', flex=True), line=line)
        if t.kind == 'FLOAT':
            self.take()
            return F('Literal', t.val, line=line)
        if t.kind == 'STR':
            self.take()
            return F('Literal', t.val, line=line)
        if t.kind == 'OP' and t.val == '(':
            self.take()
            if self.at('OP', ')'):
                self.take()
                return F('Tuple', line=line)
            first = self.expr()
            if self.at('OP', ')'):
                self.take()
                return first
            items = [first]
            while self.at('OP', ','):
                self.take()
                if self.at('OP', ')'):
                    break
                items.append(self.expr())
            self.take('OP', ')')
            return F('Tuple', *items, line=line)
        if t.kind == 'NAME':
            w = t.val
            if w == 'true' or w == 'false':
                self.take()
                return F('Literal', w == 'true', line=line)
            if w == 'maybe':
                self.take()
                return F('Literal', MAYBE, line=line)
            if w == 'decide':
                self.take()
                return F('Decide', self.or_expr(), line=line)
            if w == 'ask':
                self.take()
                op = self.name()
                a = self.args() if self.at('OP', '(') else []
                return F('Ask', F('Request', op, F('Tuple', *a)), line=line)
            if w == 'undo':
                self.take()
                return F('Undo', self.postfix(), line=line)
            if w == 'quote':
                self.take()
                return F('Quote', self.or_expr(), line=line)
            if w in KEYWORDS:
                raise SyntaxFault(f'line {line}: unexpected keyword {w!r}')
            self.take()
            return F('Name', w, line=line)
        got = t.val if t.val is not None else t.kind
        raise SyntaxFault(f'line {line}: unexpected {got!r}')


def parse(src):
    return Parser(src).program()


def parse_expr(src):
    p = Parser(src)
    e = p.expr()
    p.skip_newlines()
    if not p.at('EOF'):
        raise SyntaxFault(f'line {p.tok.line}: trailing input after expression')
    return e
