# Benchmark results

Median wall time of 5 runs. Machine: x86_64, 2 cores, Linux. Compilers: Ubuntu clang version 18.1.3 (1ubuntu1); rustc 1.97.0 (2d8144b78 2026-07-07). Selvage and C23 are compiled with `clang -std=c23 -O2`; Rust with `-C opt-level=2`.

| Benchmark | What it exercises | Selvage rule class | Selvage → C23 | C23 | Rust | Selvage / C23 | Selvage / Rust | Same output |
|---|---|---|---:|---:|---:|---:|---:|---|
| fib | recursive calls, fib(38) | function | 0.140 s | 0.110 s | 0.123 s | 1.27 | 1.13 | yes |
| collatz | loops, division and remainder on U64, limit 3,000,000 | function | 0.529 s | 0.530 s | 0.571 s | 1.00 | 0.93 | yes |
| sieve | array writes with bounds checks, primes below 50,000,000 | function | 0.435 s | 0.412 s | 0.390 s | 1.06 | 1.12 | yes |
| prefix | in-place prefix sum and its derived inverse, 10M words x 10 rounds | bijection | 0.348 s | 0.284 s | 0.300 s | 1.23 | 1.16 | yes |
| orbit | 100M certified leapfrog steps forward, then 100M through the derived inverse | bijection | 0.840 s | 0.705 s | 0.828 s | 1.19 | 1.01 | yes |
| damped | 100M lossy steps; each journals 64 bits, committed every 1000 | lossy | 0.536 s | 0.464 s | 0.536 s | 1.16 | 1.00 | yes |
| nbody | floating point, five bodies, 10M steps | function | 0.588 s | 0.601 s | 0.535 s | 0.98 | 1.10 | yes |
| **geometric mean** | | | | | | **1.12** | **1.06** | |

Outputs:

- fib: `39088169`
- collatz: `2298025`
- sieve: `3001134`
- prefix: `7230603733893087744 | 15613905710790456896`
- orbit: `Phase(-96294, -2691) | Phase(100000, 0)`
- damped: `Phase(-25806, -3179)`
- nbody: `-0.16907516382852447 | -0.1690778416543499`

## The cost of the depth bound (toolchain 0.4.2)

Compiled code passes the depth of the run to each rule and compares it with the bound. Timed alternately against 0.4.1's compiled code on the same machine, median of nine runs each:

| Benchmark | 0.4.1 | 0.4.2 | 0.4.2 / 0.4.1 |
|---|---:|---:|---:|
| fib | 0.093 s | 0.137 s | 1.48 |
| collatz | 0.514 s | 0.522 s | 1.02 |
| sieve | 0.431 s | 0.433 s | 1.01 |
| prefix | 0.350 s | 0.345 s | 0.98 |
| orbit | 0.833 s | 0.830 s | 1.00 |
| damped | 0.530 s | 0.537 s | 1.01 |
| nbody | 0.587 s | 0.581 s | 0.99 |
| **geometric mean** | | | **1.06** |

In the same session 0.4.1's code measured 1.05 against C23 in the geometric mean; the C23 and Rust times vary between sessions, so ratios measured together are what to compare.
