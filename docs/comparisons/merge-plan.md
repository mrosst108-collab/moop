# Merge plan: moop's tape into Selvage

A plan, not a decision. It follows from `merge.md`: Selvage's kernel
stays as it is, and moop contributes one certified prelude answer — the
CCNOT tape, for draws and births. Each phase names the repository it
happens in, what it depends on, and how to tell it is done. The claims
the plan rests on were tested against Selvage 0.4.9 with Clang 18.1.3;
the programs are in `experiments/`.

## Goal

Selvage gains the CCNOT tape as a certified prelude answer whose
behaviour is pinned, bit for bit, to moop's C implementation. Nothing on
a hot path gets slower, and the language grows by six names and no
keyword, mechanism or checking rule.

**Not goals:** the tape as an execution machine; moop's surface syntax
(the article, the lineage `<-`, rebindable names); retiring moop; a
wider multi-language synthesis; quantum features beyond a request that
refuses until hardware is present.

## End state

| Where | What exists |
|---|---|
| Selvage prelude | `type Tapes`, `rule tape_tick`, `request Draw` (`draw`, `birth`), `answer CcnotTape` — 26 lines |
| Shared | One trace file (`tests/tape_vectors.txt`) that both implementations must reproduce |
| moop | The language unchanged, plus a test that pins its tape to the shared trace; moop is the tape's reference model |

Use, once merged:

```selvage
tape is CcnotTape from Tapes(a, b, 0, 0)
bit is tape -> draw()
child is tape -> birth()
```

## Evidence in hand

| Claim | Result | Where |
|---|---|---|
| The prelude text certifies | Passes the 0.4.9 checker as written, `birth` included | `experiments/ccnot_tape.selv` |
| It is moop's tape | A 66-line trace (`tests/tape_vectors.txt`) is identical between moop's C tape and the Selvage interpreter: 40 draws, a birth, 20 draws from the child, and the birth undone (which equals moop's `step_back`) | `conform.selv`; moop's side is `test_wiring_1_trace` |
| It does not disturb existing programs | Appended to a copy of Selvage's prelude: all 12 examples and 7 benchmarks still pass the checker; the form census reports nothing escaping; a program uses `CcnotTape` with no declarations of its own | scratch copy of the toolchain |
| It does not break the existing suite | All 174 tests pass under Clang 18.1.3, on the original toolchain (196 s) and on the copy with the tape in its prelude (240 s). The mutation check was not run | scratch copy |
| The gate is realized, not cited | `selvage lineage --verify` links the tick's bit update to `ccnot [realized]`; its head arithmetic carries `theorem` links | lineage run on `ccnot_tape.selv` |
| The cost is small and off the hot path | ~3.5 ns per tick compiled (one bit per tick); a 21-cell birth is ~75 ns | timing of `tape_tick` |

Two Selvage defects surfaced while testing, both independent of the
tape:

- **Text containing NUL** (reported in review, reproduced here under
  Clang 18): the interpreter prints `NUL a`, compiled code prints
  an empty line.
- **A copy of an answer instance shares its arrays** (found by the
  conformance test): after `y is x`, a message to `x` changes `y`.
  Records copy correctly; instances do not. Six-line reproduction in
  `instance_copy_defect.selv`.

## Decisions

Each blocks the phase named. G1 and G2 are decided (2026-11-17, as
recommended). G3 to G6 are Selvage's to rule on; the recommendation is
what the plan assumes.

| # | Decision | Status | Blocks |
|---|---|---|---|
| G1 | moop's role after the merge | **Decided:** moop stays a separate language — the study of the tape as the machine — and is the tape's reference model | Phase 0 |
| G2 | Freeze the wiring that is merged | **Decided:** frozen as "wiring 1", pinned by the shared trace. The wiring may still iterate, but as a new numbered wiring with a new trace, which Selvage must rule on — not a silent drift | Phase 0 |
| G3 | What defines `draw` | Recommended: the tape. A Feistel rule is ~100× faster per bit on a CPU, but the tape is 2 Toffolis and 1 CNOT per bit on gates (the Feistel's gate count, ~100, is an estimate), draws are rare, and both backends must give the same values. The description must call a draw a deterministic observation, never random: draws agree with the draw `len_a` back 74.8% of the time (`docs/model.md`) | Phase 3 |
| G4 | Prelude text: inline head arithmetic, or two helper functions | Recommended: inline. 6 reserved names and 26 lines at ~3.5 ns per tick. The helper version is ~1.9 ns per tick but reserves 8 names; the tape is not on a hot path | Phase 3 |
| G5 | How a program gets a tape | Recommended: explicitly. it makes one from a seed and sends it messages. An ambient tape held by `Object`, so that `ask draw()` works anywhere, is Selvage's open question 10 and needs a ruling on where the seed comes from | Phase 3 |
| G6 | Names | Recommended: `CcnotTape`, `Tapes`, `tape_tick`, `Draw`, `draw`, `birth`. `tick` is not available: `examples/declarations.selv` declares it | Phase 3 |

## Phases

| Phase | Repository | Depends on | Outcome |
|---|---|---|---|
| 0. Pin the reference | moop | G1, G2 | **Done:** moop's tape is tested against the shared trace |
| 1. Clear known defects | Selvage | — | **Built as a patch** (`selvage-patches/0001`): both defects fixed; answers report an extent; suite green under Clang 18 |
| 2. Build the audit rulings | Selvage | — | **A2 and A3 built** (`0001`, 38 keywords). **A1 built separately** (`0002`) and held: it needs a re-ruling (`selvage-patches/README.md`) |
| 3. Admit the tape | Selvage | 0, 1 (the instance-copy fix), G3–G6; and wiring 2's trace, only if wiring 2 is adopted | The tape is in the prelude, interpreted, tested against the trace |
| 4. Compile answers | Selvage | 3 | `tape -> draw()` runs in compiled code |
| 5. State the domain | Selvage | 1, 3 | The tape's valid inputs and extent are written down and reported |
| 6. Reversible profile | Selvage | 3 | The tape is the first program lowered to gates |
| 7. Quantum interface | Selvage | 3 | A `measure` request that refuses until a profile answers it |

Phases 1 and 2 are independent of the tape, of each other and of the
open birth-diversity requirement (`docs/model.md`), and can start now.
Phase 0 is done. No tape changes are made until the birth requirement
is decided; if it adopts wiring 2, that wiring's trace must exist before
Phase 3.

### Phase 0 — Pin the reference (moop) — done

- `test_wiring_1_trace` in `tests/test_core.c` replays the scenario
  through moop's real birth path (`moop_proto_generate`) and compares it
  with `tests/tape_vectors.txt`, byte for byte. On a mismatch it leaves
  that run's trace in `build/tape_vectors.txt`, which is how a
  deliberate new wiring regenerates the file.
- `docs/model.md` names the wiring "wiring 1" and records the second
  implementation; `CLAUDE.md` says a change is a new numbered wiring.

*Done when* `make test` passes with the new test, and the trace file is
byte-identical to the output of `selvage run conform.selv`. **Both
hold.** Three deliberate breakages were checked against it: retargeting
loop B's CCNOT (caught by older tests too), observing a draw before the
tick, and seeding a child's B tape before its A tape. The last two are
caught by this test and by no other.

### Phase 1 — Clear known defects (Selvage)

- Text with an embedded NUL: carry a length in compiled code, or
  exclude NUL from `Text` in the lexer and the description.
- Copying an answer instance: copy its state as a record's is copied.
- Report the extent of answer rules. Today an answer that is an
  embedding is printed as "bijection" with no extent line.
- Reconcile the mutation count (the description says 140, the README
  120).

*Done when* each defect has a regression test, in both backends where
both apply, and the full suite and the mutation check pass under
Clang 18. (The unmodified 0.4.9 suite already passes there, all 174
tests; the mutation check is unrun.) The instance-copy defect comes before Phase 3 because the tape
is exactly its shape: an instance holding arrays.

### Phase 2 — Build the audit rulings (Selvage)

Rulings A1 to A3: delete `repeat while` and `repeat N times`; ratify
`Bit` as the 1-bit word.

*Done when* the keyword count is 37, `RepeatWhile`, `RepeatTimes` and
the `RepeatTimes` clause of `mirror` are gone, and the collatz and sieve
benchmarks, rewritten as self tail calls, are no slower.

### Phase 3 — Admit the tape (Selvage, interpreter)

1. **The admission case** (I.4), for a ruling:
   - *Foundation:* an answer (tier 4) over bit updates (tier 1).
   - *Synergy:* strengthens Request, which gains generation — a
     certified, undoable birth; and strengthens the gate lineage, which
     gains an answer whose defining step is `ccnot` itself and so a
     first program for the reversible profile. This is the weakest of
     the four steps; it makes nothing unnecessary today.
   - *Interference:* six reserved names; existing programs unaffected
     (tested).
   - *Uniformity:* no special case — only existing constructs, with the
     domain guarded by R4 and bounds checks.
2. **The prelude text**, as in `experiments/ccnot_tape.selv`.
3. **Tests**, in the description's own categories:
   - *Named:* the trace; a birth undone; a draw that was not produced
     refused by `undo`; empty and one-cell tapes refused with status 70;
     lineage reaching `ccnot` as realized.
   - *Generated:* random lengths (2 to 16) and contents — tick then
     `undo` is the identity; draws and births against an independent
     model of the tape.
   - *Mutation:* reverse one head; drop one CCNOT; target the wrong
     cell; observe before the tick. Each must be noticed.
   - *Standing:* the prelude still has no lossy clause; the census still
     finds nothing escaping; the description's code blocks still check.
4. **The register:** G3 to G6 entered as proposed decisions.

*Done when* the suite passes with the new tests and the interpreter's
trace equals moop's.

*If the admission is not ratified:* ship the same text as
`examples/ccnot_tape.selv`, tested against the trace, at no cost to the
prelude. Everything after this phase still applies to it.

### Phase 4 — Compile answers (Selvage)

Backlog item 5 lists answers in C with much else (FFI, atomics,
freestanding operation). The tape needs only one part: a message to a
named instance, which is resolved statically, lowered to a direct call.

*Done when* `conform.selv`, compiled, prints the trace; the benchmark
geometric mean against C is unchanged within noise; and a compiled draw
costs no more than the compiled tick does today.

`tape_tick` is a clause rule and compiles already, so a program can tick
and take births as plain rules in compiled code before this phase lands.

### Phase 5 — State the domain (Selvage)

The checker certifies the tape and guards it at run time: an empty tape
refuses on division by zero, a one-cell tape on R4. No type can say
"length at least 2", so the tick is reported as one-to-one with nothing
further established.

- Now: write the valid domain into the description (both lengths at
  least 2, both heads in range), and let the extent report from Phase 1
  show `draw` and `birth` as one-to-one and not onto.
- Later, and only if another program needs it: a length invariant in
  types. That is a language feature with its own admission case; the
  tape does not justify it alone.

### Phase 6 — Reversible profile (Selvage)

Backlog item 9. The tape is the natural first program, with one
adjustment: its heads are data, so its indices carry lineage links and
are not free circuit layout. An *epoch* form — the ticks of one full
alignment cycle, starting from heads (0, 0), indexed by a loop counter —
is pure layout.

*Done when* the epoch of the 8- and 13-cell tapes lowers to exactly 208
CCNOTs (2 per tick, 104 ticks) and simulating that circuit equals 104
interpreted ticks.

### Phase 7 — Quantum interface (Selvage)

Backlog item 10. `draw` (deterministic, certified) and `measure` (world
input, a commit point) are separate requests, because a rule's class is
fixed statically.

*Done now, cheaply:* declare the `Measure` group in a library with no
answer, and test that `ask measure()` is refused at Root with status 70.
*Done later:* a quantum profile installs the answer.

Two limits the profile must state, because the classical language does
not carry them over:

- **The journal cannot keep a qubit.** Keeping a copy of a discarded or
  measured qubit would be cloning it. Rewinding past a measurement is
  impossible in principle; replay reproduces the recorded outcome, not
  the state before it (VII.4). Selvage's `discard`, which journals what
  it drops, does not apply to qubits.
- **Births do not generalize.** A birth copies classical bits; no-cloning
  rules out the same for unknown quantum states.

No quantum types (qubits, unitaries, circuits) before a backend exists;
until then the `Measure` group is the whole of it.

## Budgets

**Performance.** After every Selvage phase, run `bench/run.py`. The
geometric mean against C (1.12 in the archive) must not rise beyond
noise, and no benchmark may have the tape on its hot path. Hot
randomness stays a library rule of the Feistel kind.

**Minimalism.**

| | Before | After audit | After merge |
|---|---|---|---|
| Keywords | 39 | 37 | 37 |
| Mechanisms | 3 | 3 | 3 |
| Checking rules | 8 | 8 | 8 |
| Arrows | 4 | 4 | 4 |
| Prelude | — | — | + 26 lines, 6 reserved names |

## Risks

| Risk | Handling |
|---|---|
| moop's wiring changes after it is pinned | G2: versioned wiring; the trace test fails until the trace is deliberately regenerated, and Selvage then rules on the new wiring |
| The admission's synergy step is not accepted | The fallback in Phase 3: an example file, not prelude |
| "Answers in C" grows into the whole of backlog item 5 | Phase 4 is scoped to static lowering of messages to named instances |
| `draw` and `birth` collide with a program's own request names | Checked against Selvage's programs so far; re-check against any external code before ratifying G6 |
| More aliasing defects where instances hold arrays | Phase 1 fixes the known one first; Phase 3's generated tests copy and message instances |
| The tape drifts onto a hot path | The performance budget above; the description says where it belongs |
| `draw` is read as randomness | The description calls it a deterministic observation and cites the lag-`len_a` correlation; simulations use a certified rule of the Feistel kind |

## What happens in this repository

Only Phase 0, now done: one test, one moved file, and a section in
`docs/model.md`. moop's language, its two-layer rule and its open
questions are untouched by this plan. Everything that remains happens in
Selvage.
