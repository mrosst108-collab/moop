"""Command line: python3 -m selvage <command> FILE ...

  check FILE                       certify every rule and report its class
  run FILE                         run `main` in the interpreter (status 70 if a refusal ends the run)
  print FILE                       print the canonical text of FILE
  census FILE                      which constructs of FILE and the prelude have a form, which a rule
                                   can take apart and which it can put back together
  invert FILE NAME                 print the derived inverse of a rule or answer, as Selvage
  lineage FILE [NAME ...]          what each rule's reversibility rests on, down to ccnot,
       --verify                    with every link's certificate; run each realization now
  circuit FILE RULE INPUT          lay out a certified rule as X, CNOT and CCNOT gates (the
                                   reversible profile, IX.4): bits are wires, INPUT's words
                                   are the layout; check it against the interpreter on INPUT
       --params "a, b"             parameters of the rule
       --gates                     print every gate
  call FILE RULE INPUT [options]   run one clause rule on INPUT
       --params "a, b"             parameters of the rule
       --undo                      then run it backward with `undo` (certified rules)
       --rewind                    then rewind it through the journal (any rule)
  repl [FILE]                      interactive prompt (declarations, statements, expressions)
  emit-c FILE [-o OUT.c]           translate to C23
  build FILE [-o EXE]              translate to C23 and compile with clang -std=c23 -O2

Option for run, call, repl, emit-c and build:
  --depth N                        how deep a run may nest rule calls before it is refused
                                   (default: $SELVAGE_DEPTH, else 10000; a compiled program
                                   has the bound it was built with)

Options for run, call and repl:
  --decide refuse|true|false|ask|command:CMD|replay:FILE
                                   who settles `decide` when no answer in the program does
                                   (default: $SELVAGE_DECIDE, else refuse)
  --record FILE                    write every question the world was asked, with its reply
"""
import os
import subprocess
import sys

from . import load, __version__
from .forms import Fault, show, identity
from .parser import parse, parse_expr
from .printer import program_text
from .extent import extent


def classify_report(m, user_only=True):
    lines = []
    prelude = m.prelude_names
    for name in m.decl_order:
        r = m.rules[name]
        if user_only and name in prelude:
            continue
        if r.kind == 'block':
            why = 'recomputable from its parameters' if r.cls == 'function' else \
                f'recomputable from its parameters and the replies it kept (uses {", ".join(sorted(r.uses))})'
            lines.append(f'  {name:<20} {r.cls:<15} {why}')
        else:
            if r.reasons:
                lines.append(f'  {name:<20} {r.cls:<15} {"; ".join(r.reasons)}')
            else:
                # certified: one-to-one.  How far it reaches is a separate question (V.2)
                kind, how = extent(m, r)
                lines.append(f'  {name:<20} {kind:<15} {how}')
    for name, a in m.answers.items():
        if user_only and name in prelude:
            continue
        why = '; '.join(a.reasons) if a.reasons else 'certified'
        gave = ', '.join(f'{op} to its {part}' for op, (_, part) in a.delegates.items())
        lines.append(f'  {name:<20} {a.cls:<15} (answer for {", ".join(a.group_order)}) {why}'
                     + (f'; delegates {gave}' if gave else ''))
        for op, r in a.ops.items():
            # each request rule is certified on its own, and reaches as far as it reaches (V.2)
            kind, how = extent(m, r)
            if kind is not None:
                lines.append(f'    {op:<18} {kind:<15} {how}')
    return '\n'.join(lines)


def option(rest, name):
    if name in rest:
        i = rest.index(name)
        v = rest[i + 1]
        del rest[i:i + 2]
        return v
    return None


def make_interp(m, rest):
    from .interp import Interp
    from .deciders import from_spec
    spec = option(rest, '--decide') or os.environ.get('SELVAGE_DECIDE')
    return Interp(m, decider=from_spec(spec))


def depth_option(argv):
    """`--depth N` sets the bound for this command, as SELVAGE_DEPTH does."""
    if '--depth' in argv:
        i = argv.index('--depth')
        if i + 1 >= len(argv) or not argv[i + 1].isdigit() or int(argv[i + 1]) < 1:
            raise Fault('--depth takes a positive whole number')
        os.environ['SELVAGE_DEPTH'] = argv[i + 1]
        del argv[i:i + 2]


def save_record(it, path):
    if path:
        import json
        with open(path, 'w') as f:
            json.dump(it.decisions, f, indent=2)


def main(argv=None):
    """Run a command on a stack large enough for the depth bound: the interpreter then
    reaches the bound, and refuses there, before Python's own limits are met."""
    import threading
    from .interp import DEPTH
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        depth_option(argv)
        bound = int(os.environ.get('SELVAGE_DEPTH', DEPTH))
    except (ValueError, Fault) as e:
        sys.stderr.write(f'selvage: {e}\n')
        return 2
    result = []

    def body():
        sys.setrecursionlimit(max(sys.getrecursionlimit(), bound * 150 + 20000))
        result.append(run_command(argv))
    old = threading.stack_size(min(max(bound, 1000) * 96 * 1024, 2 << 30))
    try:
        thread = threading.Thread(target=body)
        thread.start()
        thread.join()
    finally:
        threading.stack_size(old)
    return result[0] if result else 1


def run_command(argv):
    if not argv or argv[0] in ('-h', '--help', 'help'):
        print(__doc__)
        return 0
    if argv[0] == '--version':
        print('selvage', __version__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == 'repl':
        from .repl import repl
        return repl(rest)
    if not rest:
        print(__doc__)
        return 2
    path = rest[0]
    with open(path) as f:
        src = f.read()
    try:
        if cmd == 'print':
            sys.stdout.write(program_text(parse(src)))
            return 0
        m, ch, prog = load(src, path)
        if cmd == 'invert':
            from .checker import definition_of
            from .invert import invert
            from .printer import code_text
            name = rest[1]
            r = m.rules.get(name) or m.answers.get(name)
            if r is None:
                raise Fault(f'no rule or answer {name}')
            print(code_text(invert(definition_of(m, r))))
            return 0
        if cmd == 'lineage':
            from .lineage import report
            check = '--verify' in rest
            rest = [x for x in rest if x != '--verify']
            names = rest[1:] or [n for n in list(m.rules) + list(m.answers) if n not in m.prelude_names]
            print(report(m, names, check))
            return 0
        if cmd == 'census':
            from .census import report as census_report
            print(census_report(m))
            return 0
        if cmd == 'circuit':
            from .circuit import lower, simulate, simulate_back, NotLowerable, Dirty, layout_text
            from .interp import Interp, deep_copy, unflex_to
            gates = '--gates' in rest
            params_src = option(rest, '--params')
            rest = [x for x in rest if x != '--gates']
            r = m.rules.get(rest[1])
            if r is None:
                raise Fault(f'no rule {rest[1]}')
            it = Interp(m)
            value = it.ev(parse_expr(rest[2]), {})
            params = it.ev(parse_expr('(' + params_src + ',)'), {}) if params_src else ()
            params = tuple(unflex_to(v, t) for v, (_, t) in zip(params, r.params))
            value = unflex_to(value, r.takes)
            try:
                c = lower(m, r, params, value)
            except NotLowerable as e:
                print(f'{r.name}: not lowered: {e}')
                return 1
            n = c.counts()
            kept = len(set(c.ancillas) & set(c.output_wires()))
            print(f'{r.name}, laid out for the words of its input')
            print(f'input    {layout_text(c.input)}')
            print(f'output   {layout_text(c.output)}')
            print(f'wires    {c.wires}: {len(c.input_wires())} for the input, {len(c.ancillas)} ancillas '
                  f'starting at 0 ({kept} become output, {len(c.released)} are given back at 0)')
            print(f'gates    {n["CCNOT"]} CCNOT, {n["CNOT"]} CNOT, {n["X"]} X; '
                  f'{c.relabels} swap{"s" if c.relabels != 1 else ""} done by relabelling wires')
            if gates:
                for g in c.gates:
                    print('         ' + g[0] + ' ' + ' '.join(f'w{w}' for w in g[1:]))
            want = it.forward(r, params, deep_copy(value))
            got = simulate(c, value)
            print('checked  ' + ('the circuit gives what the interpreter gives' if got == want
                                 else 'THE CIRCUIT AND THE INTERPRETER DISAGREE') +
                  ('; run backward, it gives the input back' if simulate_back(c, got) == value
                   else '; RUN BACKWARD, IT DOES NOT GIVE THE INPUT BACK'))
            return 0 if got == want else 1
        if cmd == 'check':
            print(f'{path}: all rules certified or declared')
            print(classify_report(m))
            return 0
        if cmd == 'run':
            record = option(rest, '--record')
            it = make_interp(m, rest)
            try:
                it.run_main()
            finally:
                save_record(it, record)
            if os.environ.get('SELVAGE_STATS'):
                sys.stderr.write(f'epsilon={it.epsilon} journal_bits={it.journal_bits()}\n')
            return 0
        if cmd == 'call':
            record = option(rest, '--record')
            rule = rest[1]
            inp_src = rest[2]
            params_src = None
            undo = '--undo' in rest
            rewind = '--rewind' in rest
            if '--params' in rest:
                params_src = rest[rest.index('--params') + 1]
            it = make_interp(m, rest)
            r = m.rules[rule]
            env = {}
            value = it.ev(parse_expr(inp_src), env)
            params = it.ev(parse_expr('(' + params_src + ',)'), env) if params_src else ()
            from .interp import unflex_to
            params = tuple(unflex_to(v, t) for v, (_, t) in zip(params, r.params))
            print(f'{rule} is {r.cls}' + (f' ({"; ".join(r.reasons)})' if r.reasons else ''))
            print(f'input    {show(value)}    identity {identity(value)}')
            out = it.forward(r, params, value)
            print(f'output   {show(out)}')
            print(f'journal  {len(it.journal)} entries, {it.journal_bits()} bits held')
            if undo:
                back = it.backward(r, params, out, 'undo')
                print(f'undo     {show(back)}    identity {identity(back)}')
            if rewind:
                back = it.backward(r, params, out, 'rewind')
                print(f'rewind   {show(back)}    identity {identity(back)}')
                print(f'journal  {len(it.journal)} entries after rewind')
            save_record(it, record)
            return 0
        if cmd in ('emit-c', 'build'):
            from .cgen import emit_program
            from .interp import depth_bound
            csrc = emit_program(m)
            if depth_bound() != 10000:     # the bound is part of the built program
                csrc = f'#define SV_DEPTH {depth_bound()}\n' + csrc
            out = None
            if '-o' in rest:
                out = rest[rest.index('-o') + 1]
            if cmd == 'emit-c':
                if out:
                    with open(out, 'w') as f:
                        f.write(csrc)
                else:
                    sys.stdout.write(csrc)
                return 0
            base = os.path.splitext(path)[0]
            exe = out or base
            cfile = exe + '.c'
            with open(cfile, 'w') as f:
                f.write(csrc)
            rt = os.path.join(os.path.dirname(__file__), 'runtime')
            cc = os.environ.get('CC', 'clang')
            # a frame larger than half of what the runtime reserves for a call is refused, so the
            # depth bound is always reached before the stack ends (selvage_rt.h)
            cmdline = [cc, '-std=c23', '-O2', '-pthread', '-Wframe-larger-than=16384', '-Werror=frame-larger-than',
                       '-Wall', '-Wno-parentheses-equality', '-Wno-unused-function',
                       '-Wno-unused-variable', '-Wno-unused-but-set-variable', '-I', rt, cfile, '-o', exe, '-lm']
            res = subprocess.run(cmdline, capture_output=True, text=True)
            if res.returncode != 0:
                sys.stderr.write(res.stderr)
                return 1
            print(f'built {exe} from {cfile}')
            return 0
        print(__doc__)
        return 2
    except RecursionError:
        # R8: the depth bound refuses a run before this.  What can still get here is a value
        # or an expression nested deeper than the interpreter can follow: refused, not crashed
        sys.stdout.flush()
        sys.stderr.write('selvage: refused: a value or an expression is nested deeper than the interpreter follows\n')
        return 70
    except Fault as e:
        sys.stdout.flush()
        from .checker import CheckError
        from .lexer import SyntaxFault
        from .cgen import Unsupported
        if isinstance(e, (CheckError, SyntaxFault, Unsupported)):
            sys.stderr.write(f'selvage: {e}\n')      # the program is not accepted: nothing ran
            return 1
        # a refusal no installed answer took: Root's answer is the end of the run
        sys.stderr.write(f'selvage: refused: {e}\n')
        return 70


if __name__ == '__main__':
    sys.exit(main())
