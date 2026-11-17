# Selvage 0.4.9 — Phase 1 and 2 patches

Merge-plan Phases 1 and 2 (`../merge-plan.md`), built against the 0.4.9
release archive. Nothing here touches the CCNOT tape or its pinned trace.

**Terms.** *Iteration* (a loop, conditional or counted repetition, a
recursive rule call) is ordinary control flow in the language. The *CCNOT
tape* and its *tape step* are the reversible mechanism moop contributes to
the merge. Every change here, A1 and A2 included, is about iteration;
none concerns the CCNOT tape, its wiring or its tape step.

| File | What it is |
|---|---|
| `0001-phase1-and-a2.patch` | Phase 1 (two defects, answer-rule extents, the mutation count) and ruling A2 (`repeat n times` removed), with A3 in the description. Apply to the 0.4.9 archive |
| `0002-a1-remove-repeat-while.patch` | Ruling A1 (`repeat while` removed). **Held for re-ruling, not adopted** (section 2). Apply on top of 0001 only if A1 is ruled again in its favour |
| `a1-evidence/` | The five programs behind the A1 measurements (iteration only) |

```bash
cd selvage-0.4.9 && git apply 0001-phase1-and-a2.patch
```

```bash
git apply 0002-a1-remove-repeat-while.patch
```

Both patches were checked to apply cleanly to a fresh extraction of the
archive and to reproduce the trees that were tested, byte for byte. The
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

## 2. A1 — held for re-ruling

**Status: held by the maintainer (2026-11-17); 0002 is not adopted.** It
is built and verified so that the ruling can be acted on either way, and
it stays separate from 0001. A1 concerns conditional repetition only; it
makes and authorizes no change to the CCNOT tape or its pinned trace.

Ruling A1 deleted `repeat while` on the ground that "a self tail call
covers it", on condition that this be confirmed against compiled-code
speed before building. The three parts below keep apart what was
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

### 2c. The specification decision (open)

Considerations named for the re-ruling, without a recommendation:

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

If A1 is ruled again in its favour, 0002 also rewrites the collatz
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

In 0002 (held; not adopted):
- 37 keywords; the grammar loses `repeat while`.
- V.3's `repeat while` line replaced by the recursive-rule-call rule and its stated cost.
- V.6's `repeat while` row removed; VI.4's decided-condition rule names `if` alone.
- Census 47 of 48; suite 177.
- XII.2 and XII.4 entries.

Left for the maintainer: entering rulings A1 to A7 in XII.1, and the
version number.

## 4. Verification evidence

All runs on x86_64 Linux, 4 cores, Python 3.13, Clang 18.1.3.

| Check | 0.4.9 | 0001 | 0001 + 0002 (held) |
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
