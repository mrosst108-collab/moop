# moop and Selvage: merge report

**18 November 2026. The merge is complete.** Selvage 0.5.0 carries
moop's CCNOT tape and lives in this repository at `related/selvage/`.
moop 0.10.0 stays a separate language and is the tape's reference
model. Both are under the MIT licence, copyright 2026 Mark Rosst. The
sizes below were measured at commit `5355806`, before this report was
added.

The detail lives elsewhere:
- `merge-plan.md`: the plan and its rulings;
- `selvage-patches/README.md`: the handoff, patch by patch;
- `merge.md`: the exploration that started it;
- `../../related/README.md`: provenance, and how to run Selvage.

## 1. The outcome

| | moop | Selvage |
|---|---|---|
| Role after the merge | A separate language, for studying the tape as the machine. It is the tape's reference model (ruling G1) | The practical language. It carries moop's tape in its prelude |
| Version | 0.10.0 | 0.5.0, from 0.4.9 |
| Implementation | A C23 interpreter | A Python toolchain with a C23 backend |
| Size (tracked files) | 84 files, 732,163 bytes | 96 files, 1,209,962 bytes |
| Licence | MIT | MIT |
| Shared | The CCNOT tape, its frozen wiring 1, and one trace: `tests/tape_vectors.txt`, which both reproduce byte for byte | |

**What moved, and what did not.** Only one mechanism crossed: moop's
CCNOT tape, which became Selvage's prelude record `CcnotTape` and its
rules `tape_tick`, `draw` and `birth`. The rest of the work was
Selvage's own: two defects, the audit rulings, the tape's domain, the
reversible profile and the `Measure` request. Selvage's kernel did not
grow: it still has three mechanisms, eight checking rules and four
arrows. It has one keyword fewer (39 to 38), and its prelude gained 25
lines of code and six reserved names. moop's language was untouched by
the merge; its part was to pin wiring 1 to the shared trace (Phase 0).

## 2. Phases and patches

The patches apply in order to the Selvage 0.4.9 release archive (sha256
`ef8b7e70…aa2e2`, given in full in `related/README.md`), and reproduce
`related/selvage/` byte for byte.

| Phase | Status | Patch | Patch size | Validation at the time |
|---|---|---|---:|---|
| 0. Pin the reference (moop) | Complete | — (moop's `test_wiring_1_trace`) | — | The trace reproduced in moop; three deliberate breakages caught |
| 1. Clear known defects | Complete | `0001` | 74,056 B | Suite 178/178; mutation check 140/140 |
| 2. Audit rulings | Complete, as ruled: A2 and A3 built; A1 keeps `repeat while` | `0001`. `0002` is excluded | 32,876 B (excluded) | as Phase 1 |
| 3. Admit the tape | Complete | `0003` | 51,582 B | Suite 185/185; mutation check 145/145; moop's trace byte for byte, interpreted and compiled |
| 4. Compile answers | Not needed for the tape (G7) | — | — | — |
| 5. State the domain | Complete | `0004` | 17,416 B | Suite 187/187; mutation check 145/145 |
| 6. Reversible profile | Complete | `0005` | 76,514 B | Suite 194/194; mutation check 150/150 |
| 7. Quantum interface | Complete | `0006`, with `0007` the rulings in the description | 54,319 + 12,037 B | Suite 199/199; mutation check 153/153 |
| Ratification | Done | `0008` | 14,881 B | Suite 199/199 |
| Release 0.5.0 | Done | `0009` | 6,866 B | Final validation (section 6) |
| Licence | Done | `0010` | 1,641 B | No code changed |

**The rulings.**
- **G1 to G7** (between the languages):
  - moop stays separate;
  - wiring 1 is frozen;
  - the tape defines `draw`, a deterministic observation, not a random
    bit;
  - head arithmetic is inline;
  - a program owns its tape explicitly;
  - the names are `CcnotTape`, `tape_tick`, `draw` and `birth`;
  - `draw` and `birth` are prelude rules.
- **In Selvage's register:** C1 to C5 (the same decisions) and N1 to N3
  (`Measure`) are ratified in XII.1.
- **Audit:** A1 keeps `repeat while`; A2 removes `repeat n times`; A3
  makes `Bit` the 1-bit word.

## 3. File structure and sizes

Sizes are in bytes (B), with line counts.

**The whole repository:** 180 tracked files, 1,942,125 B. Of that,
84 files and 732,163 B are moop and its records, and 96 files and
1,209,962 B are the vendored Selvage.

### moop

```
moop/
├── LICENSE  README.md  CLAUDE.md  Makefile  .gitignore      5 files      30,202 B
├── src/            the interpreter                       24 files      82,205 B   2,432 lines
├── tests/          unit tests, smoke tests, programs     21 files      64,728 B   1,524 lines
├── docs/           design records and the merge          33 files     551,421 B   8,287 lines
│   └── comparisons/
│       ├── selvage-patches/   0001–0010 and the handoff  16 files     391,697 B   5,151 lines
│       └── experiments/       merge-era programs          9 files      22,412 B     601 lines
└── related/
    ├── README.md   the related project, and its provenance  1 file       3,607 B      73 lines
    └── selvage/    Selvage 0.5.0                          96 files   1,209,962 B  21,721 lines
```

**`src/`, the interpreter: 12 C files (60,160 B, 1,868 lines) and 12
headers (22,045 B, 564 lines).**

| Module | Bytes (.c + .h) | Lines (.c + .h) | Role |
|---|---:|---:|---|
| `eval` | 22,612 + 2,666 | 644 + 66 | The evaluator: dispatch, teaching, arguments, mirrors, equality |
| `parser` | 9,998 + 3,402 | 298 + 85 | The one grammar rule; refuses rather than guesses |
| `main` | 9,314 | 301 | One reader for the REPL and files; comments, blocks, line numbers |
| `number` | 5,809 + 2,170 | 216 + 54 | Bounded exact rationals; native or portable 128-bit magnitudes |
| `tapeloop` | 3,489 + 3,174 | 111 + 74 | The computational core: two counter-rotating loops and a CCNOT |
| `proto` | 2,988 + 3,244 | 81 + 79 | Generation and inheritance, kept apart |
| `lexer` | 2,788 + 2,000 | 86 + 53 | Words, arrows, literals |
| `actor` | 1,060 + 1,941 | 34 + 53 | The system-facing actor |
| `encode` | 1,039 + 1,237 | 41 + 32 | Values onto tapes, through gates |
| `logic` | 387 + 1,032 | 13 + 27 | The user layer's logic, and MAYBE |
| `ram` | 391 + 565 | 20 + 20 | User-facing memory |
| `gates` | 285 + 545 | 23 + 15 | NOT, CNOT, CCNOT, SWAP |
| `moop.h` | 69 | 6 | The version |

**`tests/`.**

| File | Bytes | Lines | What it is |
|---|---:|---:|---|
| `test_core.c` | 25,026 | 646 | C unit tests, including the wiring-1 trace (102 checks) |
| `run_tests.sh` | 23,335 | 225 | The smoke tests (127 checks) |
| `test_number.c` | 7,610 | 178 | Number unit tests, built native and portable (23 each) |
| `model/literals.py` | 4,503 | 122 | An independent Python model of reading literals (outside `make test`) |
| `tape_vectors.txt` | 620 | 66 | **The shared wiring-1 trace** |
| `programs/` | 3,634 | 287 | 16 files: programs run as files, and their expected output |

**`docs/`.**

| File | Bytes | Lines |
|---|---:|---:|
| `foundations.md` | 26,820 | 555 |
| `merge-plan.md` | 23,962 | 358 |
| `syntax.md` | 21,593 | 436 |
| `arguments.md` | 19,593 | 362 |
| `model.md` | 18,440 | 336 |
| `merge.md` | 12,195 | 224 |
| `selvage.md` | 9,401 | 163 |
| `derivation.md` | 5,308 | 101 |
| `selvage-patches/README.md`, the handoff | 47,599 | 792 |
| `experiments/tape_statistics.c`, which measures wiring 1 exhaustively | 12,757 | 367 |

### Selvage 0.5.0 (`related/selvage/`)

```
related/selvage/
├── LICENSE  README.md  SPEC.md          3 files     304,256 B    2,703 lines
├── selvage/        the toolchain       20 files     383,794 B    8,869 lines
│   └── runtime/    the C23 runtime      1 file       18,953 B      356 lines
├── tests/          the suite, generators, the model   4 files   388,237 B   7,171 lines
│   └── programs/   including ccnot_tape.selv and .trace    11 files    8,651 B    356 lines
├── tools/          description and mutation checks      2 files    41,221 B      524 lines
├── examples/                                           13 files    22,892 B      634 lines
└── bench/          Selvage, C, Rust and Io benchmarks  42 files    41,958 B    1,108 lines
```

| File | Bytes | Lines | What it is |
|---|---:|---:|---|
| `SPEC.md` | 292,364 | 2,588 | The language description: status of each claim, evidence, the register of rulings |
| `selvage/checker.py` | 104,821 | 2,278 | Certification: the checking rules, classes and extents |
| `selvage/interp.py` | 54,609 | 1,207 | The reversible interpreter, with the journal |
| `selvage/cgen.py` | 45,807 | 1,006 | The C23 backend |
| `selvage/circuit.py` | 25,164 | 614 | **Added by the merge:** the reversible profile, lowering rules to gates |
| `selvage/prelude.selv` | 13,227 | 303 | The prelude, now with the CCNOT tape and `Measure` |
| `tests/test_selvage.py` | 192,730 | 3,155 | The named suite (199 tests in all) |
| `tests/generated_04.py` | 169,832 | 3,422 | 22 generators, each with an oracle |
| `tools/mutation_check.py` | 35,105 | 385 | 153 mutations, each of which the generators must notice |
| `tests/programs/ccnot_tape.trace` | 620 | 66 | **Added by the merge:** Selvage's copy of the shared trace |

## 4. Unique features

### Of moop

- **A machine whose state contains its own history.** Two circular tape
  loops turn in opposite directions, joined by a symmetric CCNOT. Every
  tick is reversible, and both loops stay writable, so code and data
  share one substrate. Run backward, a state yields the program that
  produced it (causal closure). The one sanctioned way to forget is
  causal pruning, which zeroes only cells provably independent of the
  rest. (Added 2026-11-24: these are properties of the machine, and "the
  program" is the tapes' own contents. A moop program cannot run a body
  backward, and no session prunes one: `../model.md`, "What the core is,
  and what a program reaches".)
- **Two memories and two logics, with one bridge.**
  - Gates (NOT, CNOT, CCNOT, SWAP) act on the tapes; irreversible logic
    acts on RAM.
  - They meet only in one shape: a reversible effect inside, an
    observation outside. MAYBE is that bridge.
  - MAYBE is measured, not assumed: on wiring 1 a draw agrees with the
    draw eight back 74.8% of the time. It is an observation, never a
    random source.
- **Objects born, not allocated.**
  - The indefinite article births a proto: `rex is a dog`. Its tapes are
    seeded from its generator's dynamics, and the generator can step
    back to before the birth.
  - Generation (who made you) and inheritance (whom you defer to) are
    kept strictly apart. Parents are fixed at birth, so `inherits` is a
    predicate and delegation can never form a cycle.
- **A derived language.** Every construct must be forced by the axioms,
  and is removed when a uniform rule covers it: `self` became headless
  chains, and `generate` became the article. Each proposal faces the
  deletion test, and the record of that is in `docs/`.
- **One grammar rule, and words first.** `ask`, `inherits` and `mirrors`
  have the arrows `->`, `<-` and `<->` as exact aliases. Their shapes
  mirror the layers: one-way arrows forget, the two-way arrow
  preserves. A taught word in operator position takes one argument
  (`box add 5`); that argument is evaluated eagerly, and arity is
  strict, decided by the nearest teaching.
- **`mirrors` compiles to real gates.** Every form is an involution:
  applied twice, it is the identity.
- **Exact numbers, refused rather than rounded.** Numbers are bounded
  rationals: parts up to 2⁶³ − 1, read through 128-bit intermediates
  that are native or portable and tested both ways. Every number prints
  as text that reads back equal. One `equals` covers every kind of
  value, and protos compare by identity.
- **A reader that refuses rather than guesses.** It rejects overlong
  lines, NUL bytes, stray indentation and a `;` after code. Comments are
  whole lines, set aside before blocks are considered.

### Of Selvage 0.5.0

- **Every rule reads both ways, or says what it loses.**
  - `<->` marks a certified bijection; `=>` declares a loss.
  - Inverses are derived by `mirror`, a prelude rule that is certified
    and is its own inverse.
  - Every loss is kept in Root's journal, so even lossy runs rewind.
- **A soundness theorem, with heavy testing.** The theorem is proved
  for a model of the language, and that model is also a second
  evaluator compared with the interpreter. 22 generators with oracles
  check the toolchain, and a mutation check of 153 breakages confirms
  the generators notice each one.
- **Fast compiled code.** The C23 backend measured 1.13 times C's time
  and 1.05 times Rust's in the geometric mean of seven benchmarks
  (section 6).
- **What the merge added:**
  - **The CCNOT tape as prelude rules.** Draws are deterministic
    observations and births are certified. The domain is stated with a
    proof: the tick is a permutation, a draw and a birth are
    embeddings, and every input outside the domain is refused in both
    backends.
  - **The reversible profile.** Certified rules over bits are lowered to
    X, CNOT and CCNOT gates and checked by simulation:
    - a tick is 2 CCNOT;
    - a draw is 2 CCNOT and 1 CNOT;
    - a birth on tapes of m and n cells is 2(m + n) CCNOT and m + n CNOT;
    - one alignment of 8 and 13 cells is exactly 208 CCNOT.
  - **`Measure`.** It is declared and answered by nothing: a request can
    be declared before its physical realization exists. Two limits on
    any future quantum profile are stated: the journal cannot keep a
    qubit, and births do not generalize to quantum states.

### Of the merge itself

- **One trace, two independent implementations.** moop's C core,
  Selvage's interpreter and Selvage's compiled code all reproduce the
  same 66-line trace byte for byte. The trace pins wiring 1, the
  observation point of a draw, and the order in which a birth seeds.
- **Three kinds of trace evidence, kept apart:**
  - moop's runtime reproduces the trace (`test_wiring_1_trace`);
  - Selvage's runtime reproduces it (Selvage's own suite);
  - the two stored copies are the same file (a moop check that runs
    neither language).
- **A reproducible integration.** The archive's sha256 plus nine patches (0001 and 0003 to 0010)
  give the vendored tree byte for byte. Each patch was validated on a
  tree rebuilt from the archive, never on a working copy alone.
- **Honest claims.** The record keeps apart:
  - the model, the checker and the runtime;
  - certified and lowerable;
  - eligible and available;
  - measured and estimated.

  The tape's draws are never called random.

## 5. What did not merge

- **No merged language.** G1 decided against one; `merge.md` stays an
  exploration.
- **moop's surface syntax** did not go to Selvage: the article,
  lineage, rebindable names.
- **The tape is not on any hot path.** For hot randomness, a certified
  rule over words is about 100 times faster per bit, and stays a
  separate generator, never an implementation of the tape (C1).
- **Patch 0002** (removing `repeat while`) is excluded under A1.

## 6. Final validation of Selvage 0.5.0

| Check | Result |
|---|---|
| Full suite | 199 / 199 pass (251 s) |
| Mutation check | 153 / 153 noticed, none missed (37 min) |
| Description check | Pass |
| Benchmarks, Clang 18.1.3 and rustc 1.97.0 | 1.13 against C23 and 1.05 against Rust in the geometric mean; every output as expected |
| Reproduction | The archive with 0001 and 0003 to 0010 gives `related/selvage/` byte for byte |
| moop's `make test` | 127 smoke checks, 102 C unit tests, and 23 number unit tests in each of the native and portable builds, all passing |

## 7. Open

- **A Selvage repository of its own.** The maintainer's decision; none
  is reachable from these sessions.
- **The specification number.** SPEC.md still says "Specification 0.4";
  this is separate from the 0.5.0 release.
- **Wiring 2.** It stays unscheduled until it has a positive objective
  and acceptance criteria. Any new wiring needs a new trace, which
  Selvage would then rule on.
- **moop's own roadmap,** which is independent of the merge. Arithmetic
  (Stage 3) and certified mirrors (Stage 4) are ratified in
  `docs/foundations.md` but not yet authorized.
