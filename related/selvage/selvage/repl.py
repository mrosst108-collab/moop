"""An interactive prompt.

Declarations (rule, type, request, answer) are checked against everything
declared so far.  Statements run in one persistent scope and are checked first,
so a refused line changes nothing.  An expression on its own prints its value.
A block (a declaration, `if`, `repeat`) ends with an empty line.
"""
import os
import sys

from . import PRELUDE_PATH
from .checker import build_model, Checker, RuleInfo
from .forms import Fault, show, Form
from .parser import parse, Parser
from .printer import program_text

OPENERS = ('rule', 'type', 'request', 'answer', 'if', 'repeat')
DECL = ('rule', 'type', 'request', 'answer')


class Session:
    def __init__(self, decider_spec=None, out=None):
        from .deciders import from_spec
        from .interp import Interp
        self.decider = from_spec(decider_spec or os.environ.get('SELVAGE_DECIDE'))
        self.out = out or sys.stdout
        with open(PRELUDE_PATH) as f:
            self.prelude = parse(f.read())
        self.source = ''
        self.env, self.types = {}, {}
        self.rebuild('')
        self.Interp = Interp

    def rebuild(self, extra):
        prog = parse(self.source + '\n' + extra)
        m, ch = build_model(self.prelude, prog)
        if m.errors:
            raise Fault('\n'.join(m.errors))
        self.m, self.ch = m, ch
        self.source = program_text(prog) if prog.kids else ''
        from .interp import Interp
        handlers = getattr(self, 'it', None)
        self.it = Interp(m, self.out, self.decider)
        if handlers is not None:   # the run goes on: same root, same journal
            self.it.root, self.it.handlers, self.it.epsilon = handlers.root, handlers.handlers, handlers.epsilon
            self.it.kept, self.it.runs = handlers.kept, handlers.runs
        self.scope = RuleInfo('repl', Form('RuleDecl', (), 0))
        self.scope.kind = 'block'
        self.scope.cls = 'procedure'
        self.scope.uses = set(m.requests)
        return prog

    def feed(self, text):
        first = text.lstrip().split(None, 1)[0] if text.strip() else ''
        if first in DECL:
            before = set(self.m.rules) | set(self.m.answers) | set(self.m.types)
            self.rebuild(text)
            new = [n for n in list(self.m.rules) + list(self.m.answers) + list(self.m.types) if n not in before]
            for n in new:
                r = self.m.rules.get(n) or self.m.answers.get(n)
                if r is None:
                    self.out.write(f'type {n}\n')
                elif r.kind == 'block':
                    self.out.write(f'{n}: function\n')
                else:
                    self.out.write(f'{n}: {r.cls}' + (f' ({"; ".join(r.reasons)})' if r.reasons else '') + '\n')
            return
        p = Parser(text)
        stmts = p.block_items().kids
        for s in stmts:
            types = dict(self.types)
            saved = len(self.m.errors)
            t = self.ch.check_stmt_expr(s, types, self.scope, last=True)
            self.ch.check_undos(s)
            errs = self.m.errors[saved:]
            del self.m.errors[saved:]
            if errs:
                raise Fault('\n'.join(errs))
            if s.tag == 'Do':
                v = self.it.ev(s.kids[0], self.env)
                if v != ():
                    self.out.write(show(v) + '\n')
            else:
                self.it.step_fwd(s, self.env, self.scope, journal=False)
                self.env.pop('$result', None)
            self.types = types


def repl(args):
    spec = None
    if '--decide' in args:
        i = args.index('--decide')
        spec = args[i + 1]
        del args[i:i + 2]
    s = Session(spec)
    if args:
        with open(args[0]) as f:
            s.feed_file = f.read()
        try:
            s.rebuild(s.feed_file)
        except Fault as e:
            sys.stderr.write(f'selvage: {e}\n')
            return 1
    interactive = sys.stdin.isatty()
    if interactive:
        sys.stdout.write('Selvage 0.2.0. A block ends with an empty line; Ctrl-D leaves.\n')
    while True:
        try:
            line = input('selvage> ' if interactive else '')
        except EOFError:
            break
        if not line.strip():
            continue
        text = line
        if line.lstrip().split(None, 1)[0] in OPENERS or line.rstrip().endswith('where'):
            while True:
                try:
                    more = input('.......  ' if interactive else '')
                except EOFError:
                    break
                if not more.strip():
                    break
                text += '\n' + more
        try:
            s.feed(text + '\n')
        except Fault as e:
            sys.stdout.flush()
            sys.stderr.write(f'refused: {e}\n')
    return 0
