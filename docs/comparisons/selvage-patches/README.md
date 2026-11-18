# Selvage 0.4.9 — merge-plan patches

Merge-plan Phases 1, 2, 3, 5, 6 and 7 (`../merge-plan.md`), built against
the 0.4.9 release archive. Phases 1 and 2 do not touch the CCNOT tape; Phase 3
admits it into Selvage's prelude against wiring 1, and changes neither
wiring 1 nor its trace.

**Terms.** *Iteration* (a loop, conditional or counted repetition, a
recursive rule call) is ordinary control flow in the language. The *CCNOT
tape* and its *tape step* are the reversible mechanism moop contributes to
the merge. Every change here, A1 and A2 included, is about iteration;
none concerns the CCNOT tape, its wiring or its tape step.

| File | What it is |
|---|---|
| `0001-phase1-and-a2.patch` | Phase 1 (two defects, answer-rule extents, the mutation count) and ruling A2 (`repeat n times` removed), with A3 in the description. Apply to the 0.4.9 archive |
| `0002-a1-remove-repeat-while.patch` | Ruling A1 (`repeat while` removed). **Not adopted:** A1 is decided in favour of keeping `repeat while` (section 2). Apply on top of 0001 only if a later decision reverses that |
| `0003-phase3-ccnot-tape.patch` | Phase 3: the CCNOT tape in Selvage's prelude (section 5). Apply on top of 0001; it does not need 0002 |
| `0004-phase5-tape-domain.patch` | Phase 5: the tape's domain, each rule's extent on it, and the refusals outside it (section 6). Apply on top of 0003 |
| `0005-phase6-reversible-profile.patch` | Phase 6: the reversible profile, in part (section 7). Apply on top of 0004 |
| `0006-phase7-measure.patch` | Phase 7: the request group `Measure`, declared and answered by nothing (section 8). Apply on top of 0005 |
| `a1-evidence/` | The five programs behind the A1 measurements (iteration only) |

```bash
cd selvage-0.4.9 && git apply 0001-phase1-and-a2.patch
```

```bash
git apply 0003-phase3-ccnot-tape.patch
```

```bash
git apply 0004-phase5-tape-domain.patch
```

```bash
git apply 0005-phase6-reversible-profile.patch
```

```bash
git apply 0006-phase7-measure.patch
```

0002 (not adopted) was written against 0001 alone and no longer applies
on top of 0003, since both edit the description's suite counts; it would
be regenerated if A1 were ever adopted.

Each patch was checked to apply cleanly to a fresh extraction of the
archive, after the patches before it, and to reproduce the tree that was
tested, byte for byte. The
version number is left at 0.4.9 throughout; setting it is the
maintainer's call.

The report keeps three things apart, as asked: what changed in the
implementation, what changed in the description, and what the evidence
shows. A passing suite is reported as a passing suite, not as proof of
the claims it exercises.

## 1. Implementation changes in 0001

| Change | Files | Regression test (fails without the change) |
|---|---|---|
| **A copied instance shares nothing.** `deep_copy` returned an answer instance as it was, so after `y is x` a message to `x` changed `y` — directly, and through records and tuples. Now an instance is copied with its state; its parameters stay shared, since the language never writes them | `interp.py` | `TestBuiltValues.test_a_copied_instance_shares_nothing` |
| **A text holds no NUL byte.** The lexer refuses a NUL in a text literal, raw or after a backslash, so `check`, `run` and `build` all refuse it alike (status 1). This is the only way a NUL could enter a text: no escape writes one, joining combines texts, and world replies are not text | `lexer.py` | `TestC23Backend.test_text_is_the_same_bytes_in_both_backends`, which also checks that tab, UTF-8, quote and backslash print and are charged alike in both backends |
| **Each answer rule reports its extent.** `extent()` refused answer rules outright. An answer's rule for one request now takes the request's fields with the state and gives the reply with the state, and is settled by running, by steps or by counting like any rule. `selvage check` lists each request's extent under the answer | `extent.py`, `__main__.py` | `TestExtent.test_an_answer_s_rules_report_their_extent` (all three methods); the extent generator now also hosts every generated rule in an answer and requires the same extent both ways (`TestGenerated04.test_how_far_a_certified_rule_reaches`, at least 130 answers) |
| **The mutation count.** The tool lists 140 mutations; the README said 120. README corrected | `README.md` | — |
| **`repeat n times` removed (A2).** Keyword `times`, the `RepeatTimes` constructor, `mirror`'s clause for it, and its paths in the checker, interpreter, C backend, inverter, printer, lineage and extent analysis. `repeat with i from 1 to n` replaces it in examples, benchmarks, tests and generators; the refusal names the replacement. 38 keywords | `parser.py`, `checker.py`, `interp.py`, `cgen.py`, `invert.py`, `printer.py`, `lineage.py`, `extent.py`, `prelude.selv`; `tests/reference_model.py` | `TestSemanticContracts.test_repeat_n_times_is_a_count` |

Test infrastructure adjusted with A2: the two generators that wrote
`repeat n times` now write counted repetition with a fresh counter; the census
program and its expected counts (`Code`: 48 of 49 constructors met); one
mutation retargeted from the deleted `mirror` clause to the `RepeatWith`
clause ("a loop body is not mirrored"), and one re-anchored to re-indented
checker text. Still 140 mutations, every one of which finds its text
exactly once.

**Decision taken for you, reversible: NUL is refused rather than carried.**
The alternative is a length-carrying `Text` in compiled code, which
changes its C representation in printing, equality, charges and decision
contexts. Refusing fits `Text`'s role in the description (output; bytes
belong in `Array(U8)`), and a NUL in source is invisible — a mistake that
would otherwise become an action. If `Text` should hold arbitrary bytes,
the length-carrying change is the one to make instead.

## 2. A1 — decided: retain `repeat while`

**Decision (maintainer, 2026-11-17): retain `repeat while` for now.**
It supplies data-dependent iteration without copying mutable arrays
through recursive calls or imposing a fixed iteration count; its
advantage is large in the array workloads tested (2a), and the existing
benchmarks do not establish its cost across the full C-competitiveness
target. Removing it for grammar minimality alone would be premature.
0002 stays unadopted, built and verified, pending an explicit decision
that the grammar reduction outweighs the lost iteration capability.
A1 concerns conditional repetition only; it makes and authorizes no
change to the CCNOT tape or its pinned trace.

The audit's original ruling A1 would have deleted `repeat while` on the
ground that "a self tail call covers it", on condition that this be
confirmed against compiled-code speed before building. The three parts below keep apart what was
measured, why the implementation behaves so, and what remains to decide.

### 2a. Measured performance

Compiled with Clang 18.1.3, wall time; each a single program at the size
shown, except the two benchmark rows, which come from section 4's
interleaved runs.

| Program | Conditional repetition (`repeat while`) | Recursive rule call (self tail call) | Counted repetition (`repeat with`) |
|---|---|---|---|
| Collatz chain (stops on data, no array), limit 3,000,000 — benchmark | 0.530 s | 0.531 s | — |
| Sieve inner iteration (array updated in place, count computable), n = 80,000 | 0.005 s | **7.7 s** | 0.005 s |
| Sieve, n = 50,000,000 — benchmark | 0.428 s | not run (quadratic) | 0.429 s |
| Insertion sort, sorted input (array updated in place, stops on data), n = 40,000 | 0.005 s | not timed (copies on every call) | **0.29 s** |

### 2b. Implementation behaviour behind the numbers

- **A recursive rule call that ends a rule runs as iteration.** It adds
  nothing to the depth, in both backends (V.3); a test makes 200,000
  such calls without reaching the depth bound. Where no array is updated
  (collatz), it costs what `repeat while` costs.
- **A rule's parameters are read and never updated.** A recursive rule
  call that changes an array must therefore take a copy and pass it on,
  so each call copies the whole array: the sieve's 7.7 s.
- **Counted repetition updates in place but cannot stop early.** Where the
  number of iterations can be computed beforehand (the sieve), it matches
  `repeat while`; where iteration stops on what it finds (insertion sort
  on sorted input), it runs every iteration: the 0.29 s.
- Hence: iteration that both updates an array in place and stops on its
  contents has no replacement of the same complexity.

### 2c. The specification decision

The considerations the decision weighed:

- **C competitiveness** (soft constraint 11): removing `repeat while`
  changes the complexity of one class of in-place algorithms. The
  admission test's interference step asks whether a change weakens an
  admitted element.
- **Grammar minimality:** keeping it costs one keyword (38 rather than
  37), one `Code` constructor and its paths in the toolchain.
- **The semantics of iteration:** `repeat while` is the only form whose
  number of iterations is decided by data as it runs. It is already
  refused in clause rules, where the count could not be reconstructed
  backward, and available only in expression rules.

Were A1 ever adopted, 0002 also rewrites the collatz
benchmark as a recursive rule call and the sieve as counted repetition,
and states the cost in V.3.

## 3. Specification changes

In 0001:
- **I.0, I.1, XI.4:** suite size 178; per-class counts for `TestBuiltValues`, `TestC23Backend`, `TestExtent` and `TestSemanticContracts`.
- **I.2 (H2), IV:** 38 keywords; the grammar loses `repeat expr times`; a lexical rule naming counted repetition, and how to repeat n times.
- **III.1:** `Bit` described as the 1-bit unsigned word (A3); `Text` holds no NUL byte.
- **IV:** a NUL in a text literal is refused, and why.
- **V.2:** answers listed with each request rule's extent, plus a status row (Built, Proposed).
- **V.2, V.6:** code blocks rewritten with counted repetition; the `repeat n times` row of the inversion table removed.
- **VIII.1, VIII.2:** census figures (48 of 49); `mirror`'s listing without the `RepeatTimes` clause.
- **XI.3:** the `repeat n times` row of the step table and its case of the proof removed. The model keeps `repeat with`, so counted repetition remains inside the proved model.
- **XII.2:** `repeat n times` listed as replaced (A2).
- **XII.4:** a "Built after 0.4.9" list.
- **XII.6:** three defect rows: the instance copy, NUL text, and answer extents.

In 0002 (not adopted):
- 37 keywords; the grammar loses `repeat while`.
- V.3's `repeat while` line replaced by the recursive-rule-call rule and its stated cost.
- V.6's `repeat while` row removed; VI.4's decided-condition rule names `if` alone.
- Census 47 of 48; suite 177.
- XII.2 and XII.4 entries.

Left for the maintainer: entering rulings A1 to A7 in XII.1, and the
version number.

## 4. Verification evidence

All runs on x86_64 Linux, 4 cores, Python 3.13, Clang 18.1.3.

| Check | 0.4.9 | 0001 | 0001 + 0002 (not adopted) |
|---|---|---|---|
| Full suite | 174 / 174 pass | 178 / 178 pass (205 s) | 177 / 177 pass (204 s) |
| Description check (`tools/check_description.py`: every code block in SPEC.md) | — | Pass | Pass |
| Mutation check (`tools/mutation_check.py`) | 140 / 140 noticed (31 min) | 140 / 140 noticed, the two retargeted mutations included (32 min) | 140 / 140 noticed (32 min) |
| Examples and test programs: interpreter output against 0.4.9 | — | All 11 examples and 9 programs identical | All 11 examples and 9 programs identical |
| Benchmarks: compiled output against the published numbers | — | Identical | Identical (collatz 2298025, sieve 3001134) |

**Benchmarks**, interleaved: each round times every binary once, in a
rotated order. Each toolchain compiles its own benchmark sources, and C
is handwritten.

Seven interleaved rounds, median seconds; every binary printed the same numbers.

| Benchmark | 0.4.9 | 0001 | 0001 + 0002 | C | 0.4.9 / C | 0001 / C | 0001 + 0002 / C |
|---|---:|---:|---:|---:|---:|---:|---:|
| fib | 0.145 | 0.135 | 0.137 | 0.118 | 1.23 | 1.14 | 1.16 |
| collatz | 0.530 | 0.525 | 0.531 | 0.521 | 1.02 | 1.01 | 1.02 |
| sieve | 0.428 | 0.431 | 0.429 | 0.402 | 1.06 | 1.07 | 1.06 |
| prefix | 0.387 | 0.377 | 0.386 | 0.326 | 1.19 | 1.16 | 1.18 |
| orbit | 0.840 | 0.834 | 0.814 | 0.700 | 1.20 | 1.19 | 1.16 |
| damped | 0.539 | 0.530 | 0.530 | 0.454 | 1.19 | 1.17 | 1.17 |
| nbody | 0.593 | 0.592 | 0.598 | 0.592 | 1.00 | 1.00 | 1.01 |
| **geometric mean** |  |  |  |  | **1.12** | **1.10** | **1.11** |

No change beyond noise. `fib`'s source is identical in all three trees, and its 0.145 s against 0.135 s shows the noise is about 7%. The published 0.4.9 geometric mean was 1.12, reproduced here. Under 0002 the collatz benchmark is a recursive rule call and the sieve counted repetition; both match their `repeat while` originals. These benchmarks contain no iteration of the kind that has no replacement (section 2b), so they do not show its cost.

**What the evidence does not show.**
- The suite and the generators are tests of the cases they run.
- The new answer extents rest on the same analysis as clause-rule extents, and are cross-checked against it on generated rules. They are not proved.
- The A1 timings in 2a are single programs at one size each, chosen to show complexity, not a benchmark suite.
- Measured performance does not settle A1. It is an input to a specification decision that also weighs grammar minimality and the semantics of iteration (2c).

## 5. Phase 3 — the CCNOT tape (0003)

Built against wiring 1 under the maintainer's rulings G3 to G7
(`../merge-plan.md`), entered in Selvage's description as C1 to C5,
because Selvage's register already uses G1 to G11. All are ruled
(2026-11-17).

G7 replaced the first version of this patch. That version had a request
group `Draw` and an answer `CcnotTape`, which any program could answer as
well. Now `draw` and `birth` are prelude rules over the tape record.
Wiring 1 and birth's definition are unchanged; wiring 2 is not included.
The trace changed format only, as authorized under G7.

### 5a. Implementation

| Change | Files |
|---|---|
| The tape in the prelude: the record `CcnotTape` and the certified rules `tape_tick` (inline head arithmetic, C2), `draw` and `birth`; no request group, no answer (C5). 23 lines of code; no lossy clause | `selvage/prelude.selv` |
| Named tests (`TestCcnotTape`, 6) | `tests/test_selvage.py`; `tests/programs/ccnot_tape.selv` and `ccnot_tape.trace`, the latter a byte-for-byte copy of moop's regenerated `tests/tape_vectors.txt` |
| A generator against a model of wiring 1 that shares no code with the interpreter: random tapes of 2 to 16 cells, draws, births, child draws, every one taken back by its derived inverse, and the tick against its own | `tests/generated_04.py` (`tape`); `TestGenerated04.test_the_ccnot_tape_agrees_with_a_model_of_wiring_1` |
| Five mutations the tape generator must notice: a CCNOT dropped, a CCNOT aimed two cells ahead, head `j` turned round, a draw observing before its tick, a child started with its head moved. 145 mutations | `tools/mutation_check.py` |

The six named tests check:
- moop's trace, byte for byte, in the interpreter;
- the same trace from compiled code;
- draws and births taken back, and a draw the tape did not give refused;
- that a tape of fewer than two cells is refused;
- that `draw`, `birth` and `tape_tick` cannot be declared again and there is no request for the tape — and, pinning the reservation's stated limit, that a program's own request named `draw` is accepted as its own;
- that the tick is realized by `ccnot`, and the extents are as established.

Each new mutation was run alone against the rules version; each is
noticed by a mismatch with the model (148 to 409 findings), not by a
refused prelude.

**Extents, reported as established:** the tick and the draw are
one-to-one, with nothing more established. The birth is one-to-one and
*not onto*, because every child starts with its heads at 0. None is a
permutation, and the description says so. Not onto is consistent with
birth's ruled promise, a valid reversible initialization, not surjectivity.

### 5b. Specification

- **VI.6 The CCNOT tape**, a new section, which states:
  - the record and the three rules;
  - that a draw is a deterministic observation, never a random bit, with no claim of independence (C1). It gives the 74.8% figure;
  - that another generator is a rule of its own, never an implementation of the tape;
  - that `draw` is the tape's (C5), stated precisely: the three are reserved as prelude rule names, not as identifiers in every namespace, so a program's own request may be named `draw`;
  - that a birth is one-to-one and not onto and promises valid reversible initialization only;
  - that a program makes its tape and passes it along, and starting tapes are an explicit initialization, not entropy (C3);
  - the domain, guarded at run time in both backends;
  - both backends, and moop's trace;
  - the admission case under I.4. No request is needed, so no compiled answers; the synergy step is still named as the weakest;
  - a status table.

  Its code block is checked against the prelude by the description check.
- **XI.2:** the tape generator's row and 145 mutations.
- **XI.4:** suite 185; `TestCcnotTape` (6) and `TestGenerated04` counts.
- **XII.4:** a Built entry.
- **XII.6:** decisions C1 to C5 with their alternatives. C5 names the rejected answer-only seal and leaves the shared-namespace question separate.
- **README:** the tape among the prelude's contents; 145 mutations.

**The residual word, as ruled.** A program may still declare a request
named `draw` in a group of its own. `m -> draw()` is then that program's
message, a different form from the rule call `draw(t)`. A namespace
shared by rules and requests would close it, but that is a broader
language change and is left as a separate, optional question.

### 5c. Verification

| Check | 0001 | 0001 + 0003 (rules version) |
|---|---|---|
| Full suite | 178 / 178 pass | 185 / 185 pass (243 s), none skipped |
| Description check | Pass | Pass; the VI.6 block is the prelude's text |
| Moop's regenerated trace | — | Byte for byte, interpreter and compiled; Selvage's copy is moop's file |
| Mutation check | 140 / 140 noticed | 145 / 145 noticed (40 min); the five tape mutations each by a mismatch with the model (148 to 409 findings) |
| Examples and test programs: output against 0001 | — | All 11 examples and 9 programs identical |
| Benchmarks against 0001 | — | Geometric mean against C 1.11 for both; table below |
| 0003 applied to a fresh archive after 0001 | — | Applies; reproduces the tested tree exactly |

**Benchmarks** (measured; seven interleaved rounds, median seconds, on
the reconstructed tree; every binary printed the same numbers):

| Benchmark | 0001 | 0001 + 0003 | C | 0001 / C | 0001 + 0003 / C |
|---|---:|---:|---:|---:|---:|
| fib | 0.165 | 0.167 | 0.139 | 1.18 | 1.20 |
| collatz | 0.578 | 0.578 | 0.566 | 1.02 | 1.02 |
| sieve | 0.308 | 0.311 | 0.303 | 1.02 | 1.03 |
| prefix | 0.291 | 0.279 | 0.236 | 1.24 | 1.18 |
| orbit | 0.954 | 0.951 | 0.777 | 1.23 | 1.22 |
| damped | 0.575 | 0.568 | 0.515 | 1.12 | 1.10 |
| nbody | 0.648 | 0.661 | 0.643 | 1.01 | 1.03 |
| **geometric mean** |  |  |  | **1.11** | **1.11** |

No change: the geometric mean against handwritten C is 1.11 for both.
Absolute times differ from section 4's run, which was taken before the
session's worker restarted; compare only within one run. None of these
benchmarks draws from the tape, so they show that admitting it slows
nothing else, not what a draw costs.

**What a draw costs.**
- *Measured, compiled:* 100 million draws in 0.375 to 0.393 s (three runs), about 3.8 ns per draw. That is one tick plus a copy, consistent with the 3.5 ns per tick measured before G7.
- *Counted from the circuit, not measured:* 2 Toffolis and 1 CNOT per draw on gates.
- *Estimated, not measured:* the ~100 Toffolis per bit for an arithmetic generator mentioned elsewhere.

**Which tree.** The suite and the mutation check run in a work copy at
commit `87eaabc`, checked clean and byte-identical to the 0.4.9 archive
with 0001 and 0003 applied, before the runs and again after them
(unchanged). The example comparison and the benchmarks run on that
reconstructed tree itself.

The first, answer version of 0003 passed its suite (184 / 184) and left
all 20 programs' output unchanged. Its mutation check was stopped
unfinished when G7 superseded it, and no result is claimed for it.

## 6. Phase 5 — the tape's domain (0004)

Phase 3 is complete (2026-11-18). 0004 changes only `SPEC.md` and
`tests/test_selvage.py`; the toolchain, the prelude, the generators, the
mutation tool and the benchmark sources are untouched.

### 6a. What it states (VI.6)

Three related statements, kept apart because they are not
interchangeable.

**1. The mathematical claim, over the model's domain.** D is every
`CcnotTape(a, b, i, j)` with:
- both lengths at least 2 (they need not be equal; the trace uses 8
  and 13);
- both heads inside their tapes;
- the cells otherwise any bits.

D belongs to the model the claims are made in. It is not a type, and
nothing checks it statically. On D, for any lengths:

| Rule | On D | Not onto, because |
|---|---|---|
| `tape_tick` | A permutation of D, keeping both lengths | — |
| `draw` | An embedding of D into `Bit` × D | The bit is always the cell under head `i` of the tape given |
| `birth` | An embedding of D into D × D | A child's heads are always 0 |

The general argument is a proof, for every length. The two CCNOTs
neither write their controls nor share a target once each tape has two
cells, so they undo themselves. The head move is a bijection of the head
positions, so the tick is a permutation of D, total on D, with its
inverse also mapping D onto D. A draw and a birth carry the ticked tape
whole, so they are one-to-one. The test that runs every state with 2 or
3 cells on each tape (1,024 states) is a finite exhaustive check,
evidence for those sizes only.

**2. The checker's report.** No type carries D, so `selvage check`
reports what it can establish without it: the tick and the draw as
one-to-one, with nothing more established; the birth as one-to-one and
not onto.

The plan asked for the draw to be reported as not onto. That would need
D in the types, a language feature with its own admission case, and it
is not made to serve one report.

**3. Run-time enforcement.** A program can build a tape outside D,
because nothing stops it statically. Every such input that was tested is
refused when it runs, in both backends, with status 70:
- a tape of no cells, by division by zero;
- a tape of one cell, by R4;
- a head outside its tape, negative or past the end, by the index
  check.

No head is wrapped round into a valid one: the negative heads were
tested before this was written down.

### 6b. Tests

| Test | Checks |
|---|---|
| `TestCcnotTape.test_on_its_domain_the_tick_is_a_permutation` | Every state of D with 2 or 3 cells on each tape (1,024): the tick maps D onto D; a draw and a birth are one-to-one; a draw's bit is the cell under `i`; a child's heads are 0 |
| `TestCcnotTape.test_outside_its_domain_every_input_is_refused` | Seven inputs outside D, each refused with status 70 and the stated reason, in the interpreter and compiled |

These bring the CCNOT tape's own named tests to 8 (`TestCcnotTape`). The
whole suite is a separate count: 187 tests, of which the tape accounts
for those 8 and the tape generator's test in `TestGenerated04`.

### 6c. Verification

| Check | 0001 + 0003 | 0001 + 0003 + 0004 |
|---|---|---|
| Full suite (all tests) | 185 / 185 | 187 / 187 pass on the final tree (265 s), and before the wording change (270 s) |
| Description check | Pass | Pass |
| Mutation check | 145 / 145 | 145 / 145 noticed (40 min), on the tree before the wording change. That change touched only `SPEC.md`, which neither the mutation tool nor its generators read, so the result stands for the final tree |
| Benchmarks | 1.11 against C | Not re-run: 0004 changes no code and no benchmark source, so the compiled programs are built by the same toolchain from the same sources |
| 0004 applied to a fresh archive after 0001 and 0003 | — | Applies; reproduces the tested tree exactly |
| Tree identity | — | Work copy clean at `d31de45` and byte-identical to the archive with 0001, 0003 and 0004 applied, after every run |

## 7. Phase 6 — the reversible profile, in part (0005)

Phase 5 is complete (2026-11-18). 0005 builds part of the reversible
realization profile, which Selvage's description specified and did not
build (IX.4). The CCNOT tape is the first program tried on it, not its
definition.

### 7a. Implementation

| Change | Files |
|---|---|
| The lowering: a certified clause rule laid out as X, CNOT and CCNOT. Bits are wires; words are layout, worked out with the interpreter's own arithmetic, so a circuit holds for every input with those words | `selvage/circuit.py` (new) |
| Simulation: forward, and backward from an output. It is exact for these gates, which permute basis states. Every wire given back must be 0 where it is given back, and a backward run refuses an output the circuit does not give | `selvage/circuit.py` |
| `selvage circuit FILE RULE INPUT [--params P] [--gates]`: the layout, gate counts and ancillas, checked against the interpreter on INPUT | `selvage/__main__.py` |
| Named tests (`TestReversibleProfile`, 6) | `tests/test_selvage.py` |
| A generator: gate rules over bits from the extent generator on every input, and the prelude's array rules and the tape's rules at random sizes, each checked forward, backward and against its derived inverse laid out on its own | `tests/generated_04.py` (`circuits`) |
| Five mutations the generator must notice. 150 mutations | `tools/mutation_check.py` |

Each new mutation was first run alone against the generator, and each is
noticed (38 to 257 findings). The five break the lowering:
- a CNOT with its control and target exchanged;
- a copy sharing its wire instead of copying it;
- an uncompute that lays out no gate;
- a constant 0 counted as 1;
- a loop laid out one pass short.

What it lays out:
- bit updates: `add x * y to z` (CCNOT), `add x to z` (CNOT), `add 1 to z` (X);
- calls of `ccnot` and of its derived inverse, the same gate;
- other certified rules, inlined;
- copies into fresh names (a fresh wire and a CNOT);
- fresh bit arrays;
- swaps (relabelled wires);
- loops and conditions on words;
- uncomputes, whose wire is given back at 0.

What it refuses, with the reason:
- a rule that is not certified;
- a rule with no bit on a wire, such as `orbit` and `prefix_sum`;
- a word computed from a bit;
- a condition, an index or a clause choice that reads a bit;
- messages, decisions and other steps.

### 7b. The obligations, one by one

| Obligation | What shows it |
|---|---|
| Lowering `tape_tick` | 2 CCNOT, no ancillas, at every size laid out |
| Lowering `draw` and `birth` | `draw`: 2 CCNOT and 1 CNOT, 1 ancilla becoming the bit drawn. `birth`, tapes of m and n cells: 2(m + n) CCNOT and m + n CNOT, m + n ancillas becoming the child's cells |
| State and output correspondence with the interpreter | The three rules on 40 random tapes each; one alignment (104 ticks of 8 and 13 cells) as **208 CCNOT**, equal to 104 interpreted ticks with the heads back at 0 and 0; the generator at random sizes and heads |
| Inverse correctness | Every circuit run backward gives its input back, and each derived inverse, laid out on its own, gives it back too. Run backward from an output it does not give, the draw's circuit refuses it, as `undo` does |
| Ancilla cleanup | Every wire given back is checked to be 0 where it is given back, and no wire may be left neither output nor given back. A copy, used and uncomputed, leaves no garbage |
| Gate counts, apart from CPU timings | The table below, counted from the circuits; no timing is claimed for a circuit |
| Eligibility against availability | A rule the profile lays out is eligible to be realized as a reversible oracle. Nothing runs on reversible or quantum hardware, and no backend for it exists |

| Rule | Gates, counted | Ancillas |
|---|---|---|
| `tape_tick` | 2 CCNOT | none |
| `draw` | 2 CCNOT, 1 CNOT | 1, the bit drawn |
| `birth`, tapes of m and n cells | 2(m + n) CCNOT, m + n CNOT | m + n, the child's cells |
| One alignment of 8 and 13 cells from heads 0 | 208 CCNOT | none |
| `ripple_add` at width w (laid out at w = 1 to 8) | 2w CCNOT, 4w CNOT | none |
| `and_into`; `or_into`; `nand_into` | 1 CCNOT; 1 CCNOT and 5 X; 1 CCNOT and 1 X | 1 each, the result |

**Not tape-specific.** `ripple_add` at width 4 agrees with the
interpreter on all 512 inputs, and generated gate rules are checked on
every input. A certified rule is not thereby lowerable: the refusals
above are certified rules.

**What is not built:**
- conditions and clause choices on bits (controlled blocks);
- word arithmetic as adder circuits;
- extending a partial bijection to a permutation (IX.4);
- a backend that runs the circuits.

### 7c. Specification

- **IX.4:** a "What is built of the reversible profile" paragraph, the gate-count table, and the Reversible row marked Partial.
- **IX.1, I.0, I.3:** the profile marked Partial.
- **VI.6:** a Gates entry for the tape.
- **XI.2:** the circuits generator's row, and 150 mutations.
- **XI.4:** suite 194, and the `TestReversibleProfile` row.
- **XII.4:** a Built entry, and backlog item 9 noting what remains.
- **README:** the profile, `selvage circuit`, and 150 mutations.

### 7d. Verification

| Check | 0001 + 0003 + 0004 | + 0005 |
|---|---|---|
| Full suite (all tests) | 187 / 187 | 194 / 194 pass (273 s) |
| Mutation check | 145 / 145 | 150 / 150 noticed (41 min); the five new ones each by a substantive finding (38 to 257) |
| Description check | Pass | Pass |
| Benchmarks | 1.11 against C | The C emitted for all seven benchmarks is byte-identical with and without 0005, and the runtime header is unchanged, so the compiled programs, and so the timings, are those of 0003 |
| 0005 applied to a fresh archive after 0001, 0003 and 0004 | — | Applies; reproduces the tested tree exactly |
| Tree identity | — | Work copy clean at `3a9ecf9` and byte-identical to the archive with 0001, 0003, 0004 and 0005 applied, before and after the runs |

## 8. Phase 7 — the quantum interface, as far as it goes (0006)

Phase 6 is complete (2026-11-18). The plan's Phase 7 asks, for now, for a
`measure` request that refuses until a profile answers it, and for no
quantum types. 0006 does that and nothing more: the toolchain is not
changed. It declares one request group in the prelude, states two limits
in the description, and adds the tests.

### 8a. What already held, and what 0006 adds

Probed on the 0005 tree before anything was written. A program that
declared its own `Measure` group already behaved as the plan asks:
- `ask measure()`, with nothing installed to answer it, was refused with
  status 70: *no answer for request measure*;
- a clause rule that asks was lossy and had to write `=>`, *it asks outside
  itself, so its reply is world input*, and a rule that reached it needed
  `Measure` in its row.

These are Selvage's existing rules for any request: Q3 (measurement is a
request, world input, `=>`) already held for whoever asks. So 0006 adds
no mechanism and no special case. It adds the one shared declaration:

```selvage
request Measure
    measure() returns Bit
```

| Change | Files |
|---|---|
| The group `Measure` in the prelude, with no answer anywhere: not in the prelude, not in the toolchain, not Root | `selvage/prelude.selv` (+8 lines with the comment) |
| Named tests (`TestMeasure`, 4) | `tests/test_selvage.py` |
| A generator (`measure`) with an oracle that knows nothing of the toolchain, and its `TestGenerated04` test | `tests/generated_04.py`, `tests/test_selvage.py` |
| Three mutations the generator must notice. 153 mutations | `tools/mutation_check.py` |
| The description: VII.4 (what is built), IX.4 (the two limits), XI.2, XI.4, XII.4 to XII.6 | `SPEC.md` |
| The README | `README.md` |

**"In a library."** The plan says to declare the group in a library.
Selvage has none: a program is one file, and modules are open (XII.5,
question 8). The prelude is the one shared place, so the group is
declared there. That reserves two names, `Measure` and `measure`, since
request names are shared by every group. A program's own *rule* may still
be called `measure`, as for `draw` (tested).

### 8b. Three decisions, entered as proposed (XII.6, N1 to N3)

| # | Decision | The alternative |
|---|---|---|
| N1 | The group `Measure`, with the one request `measure() returns Bit`, in the prelude, answered by nothing | In an example: no names reserved, but no signature every program shares and a profile could answer. Or no declaration until a backend exists |
| N2 | `Measure` is not sealed: a program may install its own answer, a stand-in, as for `Refusal` and `Witness` | Sealed to Root, which under R5 would also forbid programs to ask it. Or a seal that lets anyone ask and only the system answer: a new declaration and a new case of R5, the alternative C5 also declined |
| N3 | `measure` takes no argument; what is measured is left to the quantum interface, and the signature may change with it | An argument naming a qubit, such as an index: a way of naming qubits before any qubit management |

On N2, keep two things apart:
- A stand-in can reply with anything, the tape's `draw` included. Inside
  its `with`, `measure` is then not a measurement, and the description
  says so (C1).
- It cannot make an *asking* rule certified. A clause rule that asks is
  lossy whatever is installed, so `draw` (certified) and `measure` (lossy)
  stay apart statically, as the plan requires. That is tested.

### 8c. The two limits (IX.4)

- **The journal cannot keep a qubit.** Classical rewind rests on Root
  keeping every loss. Keeping what a discarded qubit held, or a measured
  qubit's state before measurement, would be cloning. So `discard` does not
  apply to qubits, a measurement keeps only its classical outcome, and
  rewinding past a measurement or a reset is impossible in principle.
- **Births do not generalize.** The birth circuit (Phase 6: 2(m + n)
  CCNOT, m + n CNOT) is a valid reversible oracle. On basis states the
  child's cells are copies. On a parent in superposition the same CNOTs
  entangle child and parent instead: no circuit copies an unknown
  quantum state.

### 8d. What is and is not established

| Kind | Claim |
|---|---|
| Built, and tested | The group is declared and nothing answers it; `ask measure()` is refused at Root with status 70, after what the run output before; a rule that asks lists `Measure` and, as a clause rule, is lossy; a stand-in takes the request only inside its `with` |
| Built, in one backend only | The run-time refusal is the interpreter's. Compiled code has no `ask` (IX.2, backlog item 5): a program that asks `measure` is not built, and is refused with status 1 before anything runs. That is the general limit of `ask` in C, not something special to `measure` |
| Stated in the description, not enforced | The two limits: there are no qubits for the toolchain to enforce them on |
| Absent | Any answer to `measure`, the outcome kept, measurement as a commit point, reset, qubits, every quantum type |

No eligibility claim is new here: a rule the reversible profile lays out
is eligible to be a reversible oracle (0005), and still no backend runs
one.

### 8e. Verification

| Check | 0001 + 0003 + 0004 + 0005 | + 0006 |
|---|---|---|
| Focused tests | — | `TestMeasure` 4 / 4 and the generated `measure` test 1 / 1 pass |
| Generator alone | — | 0 findings at 150 programs (seed 5) and 600 (seeds 1 and 7) |
| Each new mutation, run alone | — | Noticed: Root answering `measure` (101 findings), a request nobody answers given 0 (101), an `ask` taken as no world input (92) |
| Full suite (all tests) | 194 / 194 | Running; not yet recorded |
| Mutation check | 150 / 150 | Running; not yet recorded |
| Description check | Pass | Pass: 14 blocks check, 1 inverse, 6 prelude (the new `Measure` block among them), 1 refused |
| Census | Nothing escaping | Nothing escaping |
| Benchmarks | 1.11 against C | The C emitted for all seven benchmarks is byte-identical with and without 0006, and the runtime header is unchanged, so the timings are those of 0003 |
| 0006 applied to a fresh archive after 0001, 0003, 0004 and 0005 | — | Applies; reproduces the work copy (`49ecb90`) byte for byte. The suite and mutation check run on that reconstructed tree |
