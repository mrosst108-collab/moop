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
| Original C | annotated tag `v0.6.0-uncorrected` → commit `a83d087`, moop 0.6.0 | Historical comparison only. Its bugs are not semantics. |
| Corrected C | moop 0.6.1 onward (first: commit `6674520`) | The reference implementation. |
| RV64 | `build/moop-rv` (from P1) | Conforms to the corrected reference, as judged by the specification. |

The original is addressed by its tag, so it never depends on a branch
remaining available, and the commit is never rewritten. It rebuilds
without touching the working tree (the commit id works too):

```sh
mkdir -p build/original
git archive v0.6.0-uncorrected | tar -x -C build/original
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

The declared target ISA is **`rv64im_zbb_zbs`** with the `lp64` ABI:
RV64I plus M, Zbb, and Zbs — a subset of the RVA22U64 profile, so any
RVA22U64 core runs it. It is written once, in the Makefile
(`RV_MARCH`), and each extension is there for a named use:

| Extension | Use |
|---|---|
| RV64I | everything else |
| M | decimal conversion of 64-bit numbers (P4) |
| Zbb | `cpop` counts pruned bits (P2) |
| Zbs | `bext`, `binv`, `bset` address one cell (P2) |

Left out on purpose: A (single-threaded), F and D (no floating point),
C (every instruction is a full 32-bit encoding), and Zba (an earlier
draft listed it; nothing needs it). Adding an extension is a change to
the frozen infrastructure: it needs a named use and a docs update.

Three guards keep every instruction inside the declaration:

1. **Assembler.** `-march=rv64im_zbb_zbs` rejects any other mnemonic.
2. **Binary audit** (authoritative). `make test-rv` disassembles the
   final binary with only the declared extensions enabled and fails on
   anything undecodable — this also catches raw encodings (`.insn`,
   `.word`) and `.option arch` regions that bypass the assembler.
3. **Emulated CPU.** The tests run on a QEMU CPU whose ISA string must
   equal the declaration (checked through a probe that prints QEMU's
   synthesized `/proc/cpuinfo`). Known gap: QEMU 8.2.2 still executes
   A-extension atomics with `a=false`, so the emulator is a second line
   of defense, not the guarantee.

Each guard was checked by mutation: a 1024-character reader, a
smuggled Zba instruction, Zba left on in the emulator, and an audit set
drifting from the declaration all fail `make test-rv`.

Platform: Linux user mode, no C library — `_start` and raw `ecall`s,
all in `rv/sys.S`, so a bare-metal backend later replaces one file.
Toolchain: `clang --target=riscv64-linux-gnu`, `ld.lld`, `llvm-objdump`,
and `qemu-riscv64` (package `qemu-user`); verified with clang/LLD 18.1.3
and QEMU 8.2.2. `make` and `make test` never use any of them.

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
| **P1 — RV64 infrastructure** (done, frozen) | `make rv`/`make test-rv`, `sys.S`, `_start`, QEMU runner, the reader | `--version` and `quit` match the reference byte for byte; ISA guards pass; clean, reproducible build from a fresh checkout |
| **P2 — Reversible core** | Gates, packed registers, encoding, logic, RAM | Trace diff against C for every loop-length pair 2..64, random seeds, full epochs with auto-prune; branch inspection of the gate transition; self-inverse and round-trip tests |
| **P3 — Objects and world** | Actors, protos, message dispatch, world startup | `world`'s tapes after startup identical to the reference; generator step-back restores the pre-birth state |
| **P4 — Language** | Lexer, parser, evaluator, formatter, REPL | `tests/run_tests.sh` passes with `BIN=build/moop-rv` |
| **P5 — Verification and hardening** | Differential fuzzing, exhaustion, malformed input, docs, independent build verification | No unexplained differences; every difference found is resolved against the specification |

## P1: the frozen infrastructure

Changes to anything below need a stated reason and a docs update; P2
onward builds on it rather than reshaping it.

- `rv/sys.S` — the operating-system boundary. Its interface:
  `moop_main(argc, argv) -> status` (provided by `main.S`, called from
  `_start`), `sys_write_all(fd, buf, len)`, and `sys_getc() -> byte or
  -1` (stdin buffered in 4 KiB reads; end of input is sticky, as in C
  stdio).
- `rv/main.S` — argument handling, the banner and prompts, the reader
  (the same rules as the reference, `docs/syntax.md`), blank lines,
  `quit`, and end of input. The version string comes from
  `src/moop.h`, so the two implementations cannot drift apart on it.
- `tests/rv_tests.sh` — the ISA guards, the entry-point check, and
  parity cases comparing stdout, stderr, the merged stream, and exit
  status byte for byte against `build/moop`.
- `tests/rv_cpuinfo.S` — the probe that reports the emulated ISA.

Evaluation is not ported. moop-rv refuses every other statement with
`error: evaluation is not ported to moop-rv yet` — a deliberate,
tested divergence (a REPL that silently skipped statements would look
functional while doing nothing), and the only one P1 allows.

The build is reproducible: two fresh checkouts in different
directories produce a byte-identical `build/moop-rv`.

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
finding. A difference inside an unresolved specification issue (U1 and
successors, `docs/syntax.md`) is reported against that issue, not fixed
in either implementation.

## Deferred: a reversible intermediate representation

moop's reversible model maps closely onto machine instructions, which
suggests a longer-term shape: moop semantics → reversible intermediate
representation → architecture-specific realization, with RV64 as the
first realization and C as the reference interpreter. It is
deliberately not part of this port: first establish that a direct RV64
implementation works, then factor an IR from two working realizations
rather than designing one in advance.

## Open questions

- U1, recovery after a refused block — an unresolved specification
  issue (`docs/syntax.md`); neither implementation decides it.
- The C-hosted message tier is empty in the interpreter (nothing hosts
  a C handler on a proto); moop-rv ports it to keep dispatch order
  identical, but it is a candidate for the deletion test.
- Whether the 64-cell maximum becomes permanent or loops grow to
  multiple words.
