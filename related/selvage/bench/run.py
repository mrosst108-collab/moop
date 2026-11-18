"""Benchmark harness: Selvage -> C23 (clang -O2), handwritten C23 (clang -O2), Rust (rustc opt-level 2).

Builds every benchmark three ways, checks that all three print the same numbers,
then reports the median wall time of N runs.  Usage: python3 run.py [N]
"""
import os
import platform
import re
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BIN = os.path.join(HERE, 'bin')
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5

BENCHES = [
    ('fib', 'recursive calls, fib(38)', 'function'),
    ('collatz', 'loops, division and remainder on U64, limit 3,000,000', 'function'),
    ('sieve', 'array writes with bounds checks, primes below 50,000,000', 'function'),
    ('prefix', 'in-place prefix sum and its derived inverse, 10M words x 10 rounds', 'bijection'),
    ('orbit', '100M certified leapfrog steps forward, then 100M through the derived inverse', 'bijection'),
    ('damped', '100M lossy steps; each journals 64 bits, committed every 1000', 'lossy'),
    ('nbody', 'floating point, five bodies, 10M steps', 'function'),
]


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise SystemExit(f'failed: {" ".join(cmd)}\n{r.stderr}')
    return r


def build(name):
    os.makedirs(BIN, exist_ok=True)
    sv = os.path.join(BIN, f'sv_{name}')
    env = dict(os.environ, PYTHONPATH=ROOT)
    sh([sys.executable, '-m', 'selvage', 'build', os.path.join(HERE, 'selvage', f'{name}.selv'), '-o', sv], env=env)
    c = os.path.join(BIN, f'c_{name}')
    sh(['clang', '-std=c23', '-O2', os.path.join(HERE, 'c', f'{name}.c'), '-o', c, '-lm'])
    rs = os.path.join(BIN, f'rs_{name}')
    sh(['rustc', '-C', 'opt-level=2', '-C', 'debug-assertions=off', os.path.join(HERE, 'rust', f'{name}.rs'), '-o', rs])
    return sv, c, rs


def numbers(text):
    return [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?(?:e[+-]?\d+)?', text)]


def timed(exe):
    t0 = time.perf_counter()
    r = subprocess.run([exe], capture_output=True, text=True)
    dt = time.perf_counter() - t0
    if r.returncode != 0:
        raise SystemExit(f'{exe} failed: {r.stderr}')
    return dt, r.stdout


def main():
    rows = []
    for name, what, cls in BENCHES:
        exes = build(name)
        outs = [timed(e)[1] for e in exes]
        same = numbers(outs[0]) == numbers(outs[1]) == numbers(outs[2])
        times = [[], [], []]
        for _ in range(N):
            for i, e in enumerate(exes):
                times[i].append(timed(e)[0])
        med = [statistics.median(t) for t in times]
        rows.append((name, what, cls, med, same, outs[0].strip().replace('\n', ' | ')))
        print(f'{name:8} selvage {med[0]:.3f}s  c {med[1]:.3f}s  rust {med[2]:.3f}s  '
              f'same output: {same}  [{outs[0].strip()}]'.replace('\n', ' | '),
              flush=True)
    clang = subprocess.run(['clang', '--version'], capture_output=True, text=True).stdout.splitlines()[0]
    rustc = subprocess.run(['rustc', '--version'], capture_output=True, text=True).stdout.strip()
    with open(os.path.join(HERE, 'results.md'), 'w') as f:
        f.write('# Benchmark results\n\n')
        f.write(f'Median wall time of {N} runs. Machine: {platform.machine()}, {os.cpu_count()} cores, '
                f'{platform.system()}. Compilers: {clang}; {rustc}. '
                'Selvage and C23 are compiled with `clang -std=c23 -O2`; Rust with `-C opt-level=2`.\n\n')
        f.write('| Benchmark | What it exercises | Selvage rule class | Selvage → C23 | C23 | Rust | '
                'Selvage / C23 | Selvage / Rust | Same output |\n')
        f.write('|---|---|---|---:|---:|---:|---:|---:|---|\n')
        for name, what, cls, med, same, out in rows:
            f.write(f'| {name} | {what} | {cls} | {med[0]:.3f} s | {med[1]:.3f} s | {med[2]:.3f} s | '
                    f'{med[0] / med[1]:.2f} | {med[0] / med[2]:.2f} | {"yes" if same else "NO"} |\n')
        geo_c = statistics.geometric_mean([r[3][0] / r[3][1] for r in rows])
        geo_r = statistics.geometric_mean([r[3][0] / r[3][2] for r in rows])
        f.write(f'| **geometric mean** | | | | | | **{geo_c:.2f}** | **{geo_r:.2f}** | |\n\n')
        f.write('Outputs:\n\n')
        for name, what, cls, med, same, out in rows:
            f.write(f'- {name}: `{out}`\n')
    print(open(os.path.join(HERE, 'results.md')).read())


if __name__ == '__main__':
    main()
