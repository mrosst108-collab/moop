#!/usr/bin/env python3
"""An independent model of reading number literals (docs/foundations.md, U1).

Not part of `make test`: an optional check, run and reported with the
stages that concern numbers. It shares no code with moop. Python's own
integers and fractions decide, for each literal, what moop must do:

  - a written part above 2^127 - 1: refused, too large to read;
  - a denominator of 0: refused;
  - otherwise the reduced value; refused if |p| or q exceeds 2^63 - 1;
  - a value read is printed in canonical form, and that text, read
    again, is equal to it (checked in moop with `equals`).

Usage:  python3 tests/model/literals.py BINARY [SEED ...]
        (BINARY is a moop interpreter; build one with MOOP_PORTABLE_WIDE
        defined to check the portable implementation)
"""
import random
import subprocess
import sys
from fractions import Fraction

L = 2**127 - 1
M = 2**63 - 1


def expected(text):
    neg = text.startswith('-')
    body = text[1:] if neg else text
    num_s, _, den_s = body.partition('/')
    num, den = int(num_s), int(den_s) if den_s else 1
    if num > L or den > L:
        return ('refused', 'has a part too large to read')
    if den == 0:
        return ('refused', 'has a denominator of 0')
    value = Fraction(-num if neg else num, den)
    if abs(value.numerator) > M or value.denominator > M:
        return ('refused', 'cannot be represented')
    if value.denominator == 1:
        return ('value', str(value.numerator))
    return ('value', f"{value.numerator}/{value.denominator}")


def literals(rng, count):
    """Literals from every region that matters, from a seeded generator."""
    special = [0, 1, M, M + 1, L, L + 1, 2**64, 2**126, 2**128, 2**130]
    def part():
        r = rng.random()
        if r < 0.25:
            return rng.randint(0, 1000)
        if r < 0.45:
            return rng.randint(0, M)
        if r < 0.65:
            return rng.choice(special) + rng.randint(-2, 2)
        if r < 0.8:
            return rng.randint(0, L)
        return rng.getrandbits(rng.randint(1, 132))
    out = []
    for _ in range(count):
        n = max(part(), 0)
        k = rng.random()
        if k < 0.2:                       # a whole number
            text = str(n)
        elif k < 0.3:                     # reducible: a common factor
            f = rng.choice([2, 3, 10, 2**40, 2**64, M])
            d = max(part() % (2**70), 1)
            text = f"{n * f}/{d * f}"
        elif k < 0.35:                    # a denominator of 0
            text = f"{n}/0"
        else:
            text = f"{n}/{max(part(), 0)}"
        if rng.random() < 0.15:           # leading zeros
            text = '000' + text
        if rng.random() < 0.5:
            text = '-' + text
        out.append(text)
    return out


def run(binary, lines):
    """One result per line: the printed value, or the refusal."""
    proc = subprocess.run([binary], input='\n'.join(lines) + '\nquit\n',
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    items = [x.strip() for x in proc.stdout.split('moop> ')[1:]]
    return items[:len(lines)]


def main():
    binary = sys.argv[1]
    seeds = [int(s) for s in sys.argv[2:]] or [1, 2, 3]
    total = agree = refused = values = round_trips = 0
    for seed in seeds:
        rng = random.Random(seed)
        lits = literals(rng, 3000)
        got = run(binary, lits)
        printed = []
        for lit, g in zip(lits, got):
            kind, what = expected(lit)
            total += 1
            if kind == 'refused':
                ok = g.startswith('error:') and what in g
                refused += ok
            else:
                ok = g == what
                values += ok
                if ok:
                    printed.append((what, lit))
            agree += ok
            if not ok:
                print(f"seed {seed}: {lit!r}: expected {kind} {what!r}, got {g!r}")
        back = run(binary, [f"{p} equals {lit}" for p, lit in printed])
        round_trips += sum(1 for b in back if b == 'true')
        if any(b != 'true' for b in back):
            print(f"seed {seed}: a printed value did not read back equal")
    print(f"{binary}: seeds {seeds}: {total} literals; as the model says {agree} "
          f"({values} values, {refused} refusals); printed values read back equal "
          f"{round_trips} of {values}")
    return 0 if agree == total and round_trips == values else 1


if __name__ == '__main__':
    sys.exit(main())
