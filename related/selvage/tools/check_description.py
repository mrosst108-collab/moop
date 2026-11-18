"""The description check (P4): every code block of SPEC.md, checked with the toolchain.

The description and the toolchain share one notation, so a block is checked as written.
Each block gets one verdict:

  prelude    it shows prelude declarations, and its text is the prelude's
  checks     it passes the checker, together with the blocks before it
  inverse    it shows a derived inverse, and `invert` derives the same text
  refused    it shows a program the checker refuses: its first line is the comment
             `# refused: <reason>`, and the checker refuses it for that reason
  awaits     it shows prelude declarations in a ratified form the toolchain has not
             built.  The difference must be exactly the one named in AWAITED: with it
             taken out, the block is the prelude's text, and anything else FAILS
  FAILS      anything else

Run: python3 tools/check_description.py [SPEC.md]     (exit status 1 on any FAILS)
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from selvage import load, CheckError, PRELUDE_PATH      # noqa: E402
from selvage.checker import definition_of               # noqa: E402
from selvage.invert import invert                       # noqa: E402
from selvage.lexer import SyntaxFault                   # noqa: E402
from selvage.parser import parse                        # noqa: E402
from selvage.printer import code_text, decl_lines       # noqa: E402

# Declarations the description's examples rely on but does not print.
ASSUMED = '''type Phase(q: I64, p: I64)
type Receipt
    Deposited(amount: I64)
    Withdrew(amount: I64)
request Account
    deposit(amount: I64) returns Receipt
    withdraw(amount: I64) returns Receipt
request Counter
    bump(n: I64) returns I64
    reset() returns ()
'''


# Ratified forms the toolchain has not built, as (what a block shows, the ruling, a
# function giving the block as built).  A block that shows one is not skipped: with the
# named difference taken out it must be the prelude's text.  There is none at present.
AWAITED = ()


def declarations(block):
    """Split a block into its top-level declarations (comments dropped)."""
    out, cur = [], []
    for line in block.split('\n'):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if not line.startswith(' ') and cur:
            out.append(cur)
            cur = []
        cur.append(line)
    return out + ([cur] if cur else [])


def name_of(decl):
    m = re.match(r'(?:rule|answer|type|request)\s+(undo\s+)?(\w+)', decl[0])
    return (m.group(2), bool(m.group(1))) if m else (None, False)


def same_as_prelude(decls, prelude):
    try:
        return all('\n'.join(decl_lines(parse('\n'.join(d) + '\n').kids[0])) == prelude.get(name_of(d)[0])
                   for d in decls)
    except SyntaxFault:
        return False


def check(path):
    text = open(path, encoding='utf-8').read()
    blocks = re.findall(r'```selvage\n(.*?)```', text, flags=re.S)
    prelude = {d.kids[0]: '\n'.join(decl_lines(d)) for d in parse(open(PRELUDE_PATH).read()).kids}
    program, results = ASSUMED, []
    for i, block in enumerate(blocks, 1):
        decls = declarations(block)
        names = [name_of(d) for d in decls]
        label = ', '.join(('undo ' if u else '') + n for n, u in names if n)
        waits = [(why, built) for pat, why, built in AWAITED if pat.search(block)]
        if waits:
            for why, built in waits:
                block = built(block)
            ok = same_as_prelude(declarations(block), prelude)
            results.append((i, label, 'awaits' if ok else 'FAILS',
                            '; '.join(w for w, _ in waits) if ok else 'differs from the prelude by more than '
                            + '; '.join(w for w, _ in waits)))
            continue
        if all(n in prelude for n, _ in names):
            same = same_as_prelude(decls, prelude)
            results.append((i, label, 'prelude' if same else 'FAILS', '' if same else 'differs from the prelude'))
            continue
        if any(u for _, u in names):
            try:
                m = load(program)[0]
                want = '\n'.join(code_text(invert(definition_of(m, m.rules[n]))) for n, _ in names)
                got = '\n'.join('\n'.join(d) for d in decls)
                results.append((i, label, 'inverse' if got == want else 'FAILS',
                                '' if got == want else 'is not what invert derives'))
            except (CheckError, KeyError, SyntaxFault) as e:
                results.append((i, label, 'FAILS', str(e).splitlines()[-1].strip()))
            continue
        candidate = program + '\n'.join('\n'.join(d) for d in decls) + '\n'
        first = block.lstrip('\n').split('\n', 1)[0]
        if first.startswith('# refused:'):
            reason = first[len('# refused:'):].strip()
            try:
                load(candidate)
                results.append((i, label, 'FAILS', 'accepted, and the description says it is refused'))
            except (CheckError, SyntaxFault) as e:
                ok = reason in str(e)
                results.append((i, label, 'refused' if ok else 'FAILS',
                                reason if ok else 'refused for another reason: ' + str(e).splitlines()[-1].strip()))
            continue
        try:
            load(candidate)
            program = candidate
            results.append((i, label, 'checks', ''))
        except (CheckError, SyntaxFault) as e:
            results.append((i, label, 'FAILS', str(e).splitlines()[-1].strip()))
    return results


if __name__ == '__main__':
    results = check(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'SPEC.md'))
    for i, label, verdict, note in results:
        print(f'{i:>3}  {verdict:<8} {label}' + (f'   ({note})' if note else ''))
    tally = {}
    for _, _, verdict, _ in results:
        tally[verdict] = tally.get(verdict, 0) + 1
    print(', '.join(f'{n} {v}' for v, n in sorted(tally.items())))
    sys.exit(1 if tally.get('FAILS') else 0)
