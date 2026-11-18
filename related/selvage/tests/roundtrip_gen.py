"""Generated-program testing for the inversion guarantee (G1).

Generates random clause rules, and for every rule the checker certifies checks, on
random inputs, that
  - `undo` of the output is the input (the derived inverse is the inverse),
  - no two inputs share an output (the rule is injective), and
  - a value the inverse accepts is in the image: if `undo` of a random value returns
    without a refusal, the rule takes what it returned back to that value.
A rule the checker refuses is skipped; a checker failure that is not a refusal counts
as a finding.  Run: python3 tests/roundtrip_gen.py [programs] [seed]
"""
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from selvage import load, CheckError          # noqa: E402
from selvage.forms import Word, Arr, Fault, identity   # noqa: E402
from selvage.interp import Interp, deep_copy  # noqa: E402

N = 5   # array length; values stay small so that indices are often valid

HEAD = ('rule f takes (Array(I64), Array(I64), I64, I64) returns (Array(I64), Array(I64), I64, I64)\n'
        '    (a, b, x, y) <-> (a, b, x, y) where\n')


class Gen:
    def __init__(self, rng):
        self.r = rng
        self.fresh = 0

    def index(self, loop):
        c = self.r.random()
        if c < 0.35:
            return str(self.r.randrange(N))
        if c < 0.5 and loop:
            return self.r.choice(loop)
        if c < 0.62:
            return f'{self.r.choice("ab")}[{self.r.randrange(N)}]'
        if c < 0.74:
            return self.r.choice('xy')
        if c < 0.84:
            return f'length({self.r.choice("ab")}) - {self.r.randrange(1, 3)}'
        return f'{self.r.choice("xy")} + {self.r.randrange(2)}'

    def target(self, loop):
        if self.r.random() < 0.4:
            return self.r.choice('xy')
        return f'{self.r.choice("ab")}[{self.index(loop)}]'

    def expr(self, loop, depth=0):
        c = self.r.random()
        if c < 0.25:
            return str(self.r.randrange(4))
        if c < 0.5 or depth > 1:
            return self.target(loop)
        op = self.r.choice(['+', '-', '*'])
        return f'{self.expr(loop, depth + 1)} {op} {self.expr(loop, depth + 1)}'

    def cond(self, loop):
        return f'{self.target(loop)} {self.r.choice(["=", ">", "<", "not="])} {self.expr(loop, 2)}'

    def block(self, pad, depth, loop):
        lines = []
        for _ in range(self.r.randrange(1, 4)):
            c = self.r.random()
            if c < 0.34:
                verb, prep = self.r.choice([('add', 'to'), ('subtract', 'from')])
                lines.append(f'{pad}{verb} {self.expr(loop)} {prep} {self.target(loop)}')
            elif c < 0.52:
                lines.append(f'{pad}swap {self.target(loop)} and {self.target(loop)}')
            elif c < 0.66:
                self.fresh += 1
                t = f't{self.fresh}'
                lines.append(f'{pad}{t} is {self.expr(loop)}')
                lines.append(f'{pad}add {t} to {self.target(loop)}')
            elif c < 0.8 and depth < 2:
                lines.append(f'{pad}if {self.cond(loop)}')
                lines += self.block(pad + '    ', depth + 1, loop)
                if self.r.random() < 0.5:
                    lines.append(f'{pad}otherwise')
                    lines += self.block(pad + '    ', depth + 1, loop)
            elif c < 0.92 and depth < 2:
                self.fresh += 1
                i = f'i{self.fresh}'
                lines.append(f'{pad}repeat with {i} from 0 to {self.r.randrange(1, N)}')
                lines += self.block(pad + '    ', depth + 1, loop + [i])
            elif depth < 2:
                self.fresh += 1
                i = f'i{self.fresh}'
                lines.append(f'{pad}repeat with {i} from 1 to {self.target(loop)}')
                lines += self.block(pad + '    ', depth + 1, loop + [i])
            else:
                lines.append(f'{pad}swap x and y')
        return lines

    def program(self):
        return HEAD + '\n'.join(self.block('        ', 0, [])) + '\n'


def value(rng):
    arr = lambda: Arr('I64', [Word(rng.randrange(N), 'I64') for _ in range(N)])  # noqa: E731
    return (arr(), arr(), Word(rng.randrange(-1, N), 'I64'), Word(rng.randrange(-1, N), 'I64'))


def run(programs=300, seed=1, inputs=24):
    """Returns (certified, refused, findings); a finding is (kind, source, detail)."""
    rng = random.Random(seed)
    certified = refused = 0
    findings = []
    for _ in range(programs):
        src = Gen(rng).program()
        try:
            m = load(src)[0]
        except CheckError as e:
            if 'internal' in str(e):
                findings.append(('checker failure', src, str(e)))
            refused += 1
            continue
        r = m.rules['f']
        if r.cls not in ('bijection', 'partial'):
            findings.append(('class', src, r.cls))
            continue
        certified += 1
        it = Interp(m)
        seen = {}
        for _ in range(inputs):
            x = value(rng)
            try:
                y = it.forward(r, (), deep_copy(x))
            except Fault:
                continue           # a refusal at run time (index, alias): defined behaviour
            ix, iy = identity(x), identity(y)
            if seen.setdefault(iy, ix) != ix:
                findings.append(('not injective', src, f'{seen[iy]} and {ix} both give {iy}'))
                break
            try:
                back = it.undo(r, (), deep_copy(y))
            except Fault as e:
                findings.append(('undo refused a value in the image', src, str(e)))
                break
            if identity(back) != ix:
                findings.append(('undo is not the inverse', src, f'{x} -> {y} -> {back}'))
                break
            # part 3: outside the image the inverse refuses; what it accepts, the rule produces
            z = value(rng)
            try:
                w = it.undo(r, (), deep_copy(z))
            except Fault:
                continue
            try:
                again = it.forward(r, (), deep_copy(w))
            except Fault as e:
                findings.append(('the inverse accepted a value the rule refuses to produce', src, f'{z}: {e}'))
                break
            if identity(again) != identity(z):
                findings.append(('the inverse accepted a value outside the image', src, f'{z} -> {w} -> {again}'))
                break
    return certified, refused, findings


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    s = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    certified, refused, findings = run(n, s)
    print(f'{n} programs: {certified} certified and checked, {refused} refused, {len(findings)} findings')
    for kind, src, detail in findings[:5]:
        print(f'--- {kind}: {detail}\n{src}')
    sys.exit(1 if findings else 0)
