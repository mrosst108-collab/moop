# moop-rv: a second implementation in RISC-V assembly

The plan for implementing moop in RV64 assembly. moop-rv is a **second
implementation of the same language** — not a new language, and not a
replacement for the C interpreter. It adds no language concept; every
behavior it has is one the specification already defines.

Initial scope, deliberately narrow: a corrected C reference, an RV64
Linux user-mode implementation, loops of at most 64 cells, and
differential verification. Out of scope for now: bare metal, a shared
intermediate representation, optimization.

## Precedence

> The implementation is subordinate to the semantics. The reference
> implementation is subordinate to the specification.

The specification is the documentation: `docs/syntax.md`,
`docs/model.md`, and `CLAUDE.md`. The C interpreter is the reference
implementation, and it can be wrong. A disagreement between C and
moop-rv is not automatically a moop-rv bug: both are judged against the
specification. Where the specification is silent, the question is
recorded as an open question in the docs and decided there — neither
implementation's behavior settles it by existing. (Example: recovery
after a refused block, listed in `docs/syntax.md`.)

## Baselines

| Baseline | Where | Role |
|---|---|---|
| Original C | commit `a83d087`, moop 0.6.0 | Historical comparison only. Its bugs are not semantics. |
| Corrected C | moop 0.6.1 onward | The reference implementation. |
| RV64 | `build/moop-rv` (from P1) | Conforms to the corrected reference, as judged by the specification. |

The original rebuilds from history without touching the working tree:

```sh
mkdir -p build/original
git archive a83d087 | tar -x -C build/original
make -C build/original            # -> build/original/build/moop
```

## The guarantee, stated precisely

> The reversible gate transition contains no data-dependent
> control-flow branches.

"The reversible gate transition" is `fire`, `step` and `step_back`.
The property is structural and independently checkable: disassemble
those routines and find no branch instruction. A spike (packed core,
both interpreter loop sizes, full epochs forward and back) matched the
C core's cells and marks state-for-state, with `fire` at 37
instructions and no branches.

What this does **not** claim: constant-time execution on any
processor. Cache behavior, instruction latency, memory-access timing,
and speculative execution are outside the guarantee. Further
properties (data-independent addresses, branch-free deposit, exchange,
prune) are design objectives for the rest of the system layer, each
claimed only once it has its own check.

## Target

- RV64GC with Zba/Zbb/Zbs (the RVA22U64 bit-manipulation set): `bext`,
  `binv`, `bset` address cells; `cpop` counts pruned bits. Fallback
  macros keep plain RV64I possible.
- Linux user mode, no C library: `_start` and `ecall` for `read`,
  `write`, `exit`, `brk`, all confined to `sys.S` so a bare-metal
  backend later replaces one file.
- Toolchain: `clang --target=riscv64-linux-gnu` and `ld.lld`; run under
  `qemu-riscv64` (Debian/Ubuntu package `qemu-user`). New targets
  `make rv` and `make test-rv`; `make` and `make test` stay unchanged
  and never require QEMU.

## Core data layout

One loop is one 64-bit word (bit i = cell i), so loops hold 2..64
cells — the 64-cell maximum is provisional, and init refuses longer
loops rather than truncating. All fields are doublewords: uniform
`ld`/`sd`, the same widths as the C core's `size_t`.

| Offset | Field | Bytes | Meaning |
|---|---|---|---|
| 0 | `A` | 8 | loop A cells |
| 8 | `B` | 8 | loop B cells |
| 16 | `MA` | 8 | loop A causal marks |
| 24 | `MB` | 8 | loop B causal marks |
| 32 | `la` | 8 | loop A length, 2..64 |
| 40 | `lb` | 8 | loop B length, 2..64 |
| 48 | `ha` | 8 | loop A head, 0..la−1 |
| 56 | `hb` | 8 | loop B head, 0..lb−1 |
| 64 | `ticks` | 8 | ticks since epoch start |

Total: 72 bytes, 8-byte aligned. (Narrowing lengths and heads to one
byte each would give 44 bytes, 48 aligned; not worth mixed-width
accesses at today's object counts, and available later if they grow.)

Values return in `a0`/`a1` (tag, payload): number (int64, per the
specification's literal range), bool, proto, or error with a message
pointer. Proto, actor, and syntax-tree layouts are specified here when
P3 and P4 begin. Memory: static tables at the reference's exact limits,
fixed-size syntax-tree blocks with a free list, a `brk` arena for protos
and names.

## Phases

| Phase | Work | Exit criteria |
|---|---|---|
| **P0 — Correctness of C** (done, 0.6.1) | Refuse over-long lines, NUL bytes, and out-of-range literals instead of splitting, truncating, or clamping; spec first, then C; regression tests | New tests fail on 0.6.0 and pass on 0.6.1; full suite green |
| **P1 — RV64 infrastructure** | `make rv`/`make test-rv`, `sys.S`, `_start`, QEMU runner | `--version` and `quit` match the reference |
| **P2 — Reversible core** | Gates, packed registers, encoding, logic, RAM | Trace diff against C for every loop-length pair 2..64, random seeds, full epochs with auto-prune; branch inspection of the gate transition; self-inverse and round-trip tests |
| **P3 — Objects and world** | Actors, protos, message dispatch, world startup | `world`'s tapes after startup identical to the reference; generator step-back restores the pre-birth state |
| **P4 — Language** | Lexer, parser, evaluator, formatter, REPL | `tests/run_tests.sh` passes with `BIN=build/moop-rv` |
| **P5 — Verification and hardening** | Differential fuzzing, exhaustion, malformed input, docs, independent build verification | No unexplained differences; every difference found is resolved against the specification |

## Differential verification

The objective is semantic equivalence, not matching successful output.
Each comparison checks stdout, stderr, the merged stream (`2>&1`, so
error ordering is pinned), and exit status. The corpus:

- Grammar-generated programs: births, teaching, blocks, lineage,
  `mirrors`, delegation.
- Randomized token streams, including malformed programs and stray
  bytes.
- Integer boundaries: 0, 255, 256, INT64_MAX, INT64_MAX + 1, long
  zero-padded literals.
- Empty input, input without a final newline, truncated input, EOF
  inside a block.
- Every limit at and one past its edge: 1023/1024-character lines, 128
  tokens, 64 tree nodes, message depth 32, 64 names, 128 teachings, 16
  body lines.
- Repeated teaching and re-teaching of the same message.
- Allocation exhaustion. Where a limit is a resource rather than a
  table size (protos until memory runs out), the exhaustion point may
  differ between implementations; the behavior at exhaustion — an
  honest error, no silent partial effect — may not.

moop is deterministic (`maybe` is replayable), so any difference is a
finding.

## Deferred: a reversible intermediate representation

moop's reversible model maps closely onto machine instructions, which
suggests a longer-term shape: moop semantics → reversible intermediate
representation → architecture-specific realization, with RV64 as the
first realization and C as the reference interpreter. It is
deliberately not part of this port: first establish that a direct RV64
implementation works, then factor an IR from two working realizations
rather than designing one in advance.

## Open questions

- Recovery after a refused block (see `docs/syntax.md`).
- The C-hosted message tier is empty in the interpreter (nothing hosts
  a C handler on a proto); moop-rv ports it to keep dispatch order
  identical, but it is a candidate for the deletion test.
- Whether the 64-cell maximum becomes permanent or loops grow to
  multiple words.
