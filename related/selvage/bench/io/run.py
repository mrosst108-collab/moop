"""Selvage against Io on the same computations.

Io is an interpreter whose numbers are doubles, so these programs are sized to
keep every value exact.  Three measurements per benchmark:
  io            Io's native interpreter (set IO to its binary), start-up subtracted
  selvage C23   the same algorithm compiled, run at ~100x the work and scaled down
  selvage interp the Python reference interpreter on the same work as Io

Usage: IO=/path/to/io python3 run.py
"""
import math
import os
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
IO = os.environ.get('IO', 'io')
ENV = dict(os.environ, PYTHONPATH=ROOT)
# how much more work the 100x programs do than the Io-sized ones
WORK = {'fib': 63245986 / 514229, 'collatz': 428343467 / 2864311,
        'sieve': (3e7 * math.log(math.log(3e7))) / (3e5 * math.log(math.log(3e5))),
        'prefix': 100, 'orbit': 100, 'nbody': 100}


def median_time(cmd, n=5):
    ts = []
    for _ in range(n):
        t0 = time.perf_counter()
        r = subprocess.run(cmd, capture_output=True, text=True, env=ENV)
        ts.append(time.perf_counter() - t0)
        if r.returncode != 0:
            raise SystemExit(f'{cmd} failed: {r.stderr}')
    return statistics.median(ts), r.stdout


def main():
    with open('/tmp/empty.io', 'w') as f:
        f.write('nil\n')
    io0, _ = median_time([IO, '/tmp/empty.io'])
    with open('/tmp/empty.selv', 'w') as f:
        f.write('rule main uses Output\n    output 1\n')
    sv0, _ = median_time([sys.executable, '-m', 'selvage', 'run', '/tmp/empty.selv'])
    rows = []
    for name in WORK:
        exe = f'/tmp/sv100_{name}'
        subprocess.run([sys.executable, '-m', 'selvage', 'build',
                        os.path.join(HERE, 'selvage-100x', f'{name}.selv'), '-o', exe],
                       env=ENV, capture_output=True, check=True)
        io_t, io_out = median_time([IO, os.path.join(HERE, 'io', f'{name}.io')])
        c_t, _ = median_time([exe])
        in_t, in_out = median_time([sys.executable, '-m', 'selvage', 'run',
                                    os.path.join(HERE, 'selvage-same', f'{name}.selv')], n=1)
        per = c_t / WORK[name]
        rows.append((name, io_t - io0, per, (io_t - io0) / per, (in_t - sv0) / (io_t - io0), io_out, in_out))
        print(f'{name:8} io {io_t - io0:.3f}s  selvage C23 {per * 1000:.2f}ms  '
              f'{(io_t - io0) / per:.0f}x faster; interpreter {(in_t - sv0) / (io_t - io0):.1f}x slower', flush=True)
    g = lambda xs: math.exp(sum(map(math.log, xs)) / len(xs))  # noqa: E731
    print(f'geometric mean: compiled {g([r[3] for r in rows]):.0f}x faster than Io; '
          f'interpreter {g([r[4] for r in rows]):.1f}x slower than Io')


if __name__ == '__main__':
    main()
