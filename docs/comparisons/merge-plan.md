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
| Selvage prelude | `type CcnotTape` and the rules `tape_tick`, `draw`, `birth` (G7) — 23 lines of code; the request group `Measure`, answered by nothing (Phase 7) — 2 lines |
| Shared | One trace file (`tests/tape_vectors.txt`) that both implementations must reproduce |
| moop | The language unchanged, plus a test that pins its tape to the shared trace; moop is the tape's reference model |

Use, once merged:

```selvage
tape is CcnotTape(a, b, 0, 0)
(bit, tape2) is draw(tape)
(child, tape3) is birth(tape2)
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

Each blocks the phase named. All seven are decided by the maintainer
(2026-11-17). G3 to G7 are entered in Selvage's description as C1 to C5,
because Selvage's own register already uses G1 to G11. C1 to C5 were
ratified on 2026-11-18 and moved into Selvage's register of rulings
(XII.1) unchanged (`selvage-patches/0008`).

| # | Decision | Status | Blocks |
|---|---|---|---|
| G1 | moop's role after the merge | **Decided:** moop stays a separate language — the study of the tape as the machine — and is the tape's reference model | Phase 0 |
| G2 | Freeze the wiring that is merged | **Decided:** frozen as "wiring 1", pinned by the shared trace. The wiring may still iterate, but as a new numbered wiring with a new trace, which Selvage must rule on — not a silent drift | Phase 0 |
| G3 | What defines `draw` | **Adopted (C1): the CCNOT tape defines `draw`.** A draw is the tape's deterministic observation; both backends must produce the same tape-defined values. The Feistel rule is a separate generator, never an interchangeable implementation of the tape: the CPU speed difference (~100× per bit) does not justify substituting it. The tape's case is its gate realization (2 Toffolis and 1 CNOT per bit) and its correspondence with moop, not randomness: draws agree with the draw `len_a` back 74.8% of the time (`docs/model.md`), so the description must forbid treating `draw` as a random source or claiming independence. G3 says what `draw` means; it does not create a general generator abstraction | Phase 3 |
| G4 | Prelude text: inline head arithmetic, or two helper functions | **Adopted (C2): inline.** 6 reserved names and 26 lines; the transition stays visible where it is defined. The helper version's ~1.9 ns against ~3.5 ns per tick is real but not decisive off the hot path, and does not justify two more names. The helper text is not kept | Phase 3 |
| G5 | How a program gets a tape | **Adopted (C3): explicitly.** A program makes a tape from a seed and passes it to `draw` and `birth` (originally "sends it messages"; carried out as rule calls after G7), so it controls which tape, which seed, and how its state flows. No ambient tape in `Object`: that would be a hidden dependency and need a ruling on seed provenance. A seed is an explicit initialization input, not entropy: seeding does not make the tape a random source | Phase 3 |
| G6 | Names | **Adopted (C4):** `CcnotTape`, `tape_tick`, `draw`, `birth`. As first ruled the list also had `Tapes` and `Draw`, which G7 removed. `tick` is not available: `examples/declarations.selv` declares it. `tape_tick` kept over `tape_step` (2026-11-17): *step* is a Selvage clause statement; the naming convention is in `docs/model.md` | Phase 3 |
| G7 | Reserve `draw` to the tape | **Adopted (C5), 2026-11-17: prelude rules.** Under the first 0003 any program could answer the `Draw` group itself. Now `draw` and `birth` are prelude rules over the `CcnotTape` record, with no request group and no answer: a prelude rule cannot be declared again, so no program can stand in for the tape's draw. Preferred to an answer-only seal, which would add a declaration form and a case of R5 and leave the tape interpreter-only. The trace was regenerated in the record format (format only; authorized). Residual, accepted as a separate namespace question: a program's own request may be named `draw` (`m -> draw()`, a different form from `draw(t)`) | Phase 3 |

## Phases

| Phase | Repository | Depends on | Outcome |
|---|---|---|---|
| 0. Pin the reference | moop | G1, G2 | **Done:** moop's tape is tested against the shared trace |
| 1. Clear known defects | Selvage | — | **Complete** (2026-11-18): built and validated as `selvage-patches/0001`. Both defects are fixed, with regression tests in both backends; answers report an extent; the mutation count is reconciled. Suite 178/178 and mutation check 140/140 under Clang 18. Every later patch applies on top of 0001, and the last validation of the whole stack passed 199/199 |
| 2. Build the audit rulings | Selvage | — | **Complete** (2026-11-18), as ruled: A2 and A3 built in `0001` (38 keywords). **A1 decided: retain `repeat while`** (2026-11-17), so `0002` is not adopted, and the phase's original criterion of 37 keywords gives way to that ruling. A1 is about ordinary iteration and does not touch the CCNOT tape or its trace |
| 3. Admit the tape | Selvage | 0, 1 (the instance-copy fix), G3–G7 (decided); against wiring 1 | **Complete** (2026-11-18): built and validated as `selvage-patches/0003` (rules version): suite 185/185, mutation check 145/145, 20 programs unchanged, moop's trace byte for byte in the interpreter and compiled, benchmarks unchanged (`selvage-patches/README.md`) |
| 4. Compile answers | Selvage | 3 | **Not needed for the tape** after G7: `draw` and `birth` are rules, which compile; compiled code prints moop's trace (verified). Answers in C remain backlog item 5 for other reasons |
| 5. State the domain | Selvage | 1, 3 | The tape's valid inputs and extent are written down and reported. **Complete** (2026-11-18): built and validated as `selvage-patches/0004`: suite 187/187, mutation check 145/145, the domain a model claim with a proof, refusals outside it in both backends |
| 6. Reversible profile | Selvage | 3 | The tape is the first program lowered to gates. **Complete** (2026-11-18): built and validated as `selvage-patches/0005` (the profile in part): suite 194/194, mutation check 150/150, the epoch 208 CCNOT against 104 interpreted ticks, benchmarks' emitted C unchanged |
| 7. Quantum interface | Selvage | 3 | A `measure` request that refuses until a profile answers it. **Complete** (2026-11-18): built and validated as `selvage-patches/0006`, the `Measure` group in the prelude, answered by nothing: suite 199/199, mutation check 153/153, benchmarks' emitted C unchanged. N1 to N3 adopted, N2 with a qualification; the rulings are entered in Selvage's description by `0007` (description only) |

**The plan is complete (2026-11-18).** Every phase is complete, apart
from Phase 4, which turned out not to be needed for the tape. What
remains is outside this repository (*Status*, at the end).

Phases 1 and 2 are independent of the tape and of each other. Phase 0 is
done. Birth is decided
(`docs/model.md`): it promises valid reversible initialization, not
diversity, so wiring 1 stays and Phase 3 does not wait on a wiring 2.
Diversity remains a separate design objective; if a wiring 2 is ever
adopted for it, that wiring's trace must exist before Phase 3.

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
tape B's CCNOT (caught by older tests too), observing a draw before the
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

*As ruled:* A1 retained `repeat while` (2026-11-17), so the parts of this
criterion that remove it do not apply. The phase is complete with A2 and
A3: `repeat n times` and its `Code` constructor and `mirror` clause are
gone, `Bit` is ratified as the 1-bit word, and there are 38 keywords.

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

### Phase 4 — Compile answers (Selvage) — not needed for the tape

After G7 the tape has no answer: `draw` and `birth` are clause rules,
which the C backend already compiles, and compiled code prints moop's
trace. What follows was the plan before G7, kept for the record.

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
  *As built (0004):* the description states the domain D and each
  rule's extent on it, with a proof: the tick is a permutation of D, and
  a draw and a birth are embeddings, not onto. Every state with 2 or 3
  cells per tape (1,024) is run to confirm it. Every input outside D is
  refused in both backends, and a head is never wrapped round. One part
  could not be done as planned. The extent report cannot show the draw
  as not onto without D in the types, so it still says only what it
  establishes, and the description says so.
- Later, and only if another program needs it: a length invariant in
  types. That is a language feature with its own admission case; the
  tape does not justify it alone.

### Phase 6 — Reversible profile (Selvage)

Backlog item 9. The tape is the natural first program, with one
adjustment: its heads are data, so its indices carry lineage links and
are not free circuit layout. An *epoch* form — the ticks of one full
alignment cycle, starting from heads (0, 0), with tape steps indexed by a counted-repetition counter —
is pure layout.

*Done when* the epoch of the 8- and 13-cell tapes lowers to exactly 208
CCNOTs (2 per tick, 104 ticks) and simulating that circuit equals 104
interpreted ticks.

*As built (0005):* the profile lowers certified rules whose bits are
wires and whose words are layout, and checks every circuit against the
interpreter by simulation. The epoch criterion holds: 208 CCNOTs, equal
to 104 interpreted ticks. The heads are words, so no separate epoch form
was needed; laying out ticks from known heads makes the indices layout.
The tape is the first program, not the definition: the same lowering
handles `ripple_add`, the gates of `examples/gates.selv` and generated
gate rules, and it refuses, with reasons, rules outside it.

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

*As built (0006):* the toolchain is unchanged. Selvage's existing rules
already refuse a request nobody answers (status 70), make a clause rule
that asks lossy, and put the group in the asker's row, so Q3 held for the
asker before anything was added. 0006 declares the group in the prelude:
Selvage has no library, and the prelude is its one shared place. It
states the two limits in the description (IX.4) and tests all of it.
Three choices are entered as proposed decisions N1 to N3: the group in
the prelude; not sealed, so a program may install a stand-in, which
cannot make an asking rule certified; `measure` takes no argument until
qubits exist. Compiled code has no `ask`, so there the program is refused
at build time (status 1), not at run time.

*Rulings (2026-11-18).* N1 to N3 are adopted, and ratified the same day
in Selvage's register of rulings (XII.1, `selvage-patches/0008`):

| # | Ruling | Reason |
|---|---|---|
| N1 | **Adopted.** `Measure` in the prelude, unanswered | Measurement is an environmental request, not a simulation the prelude provides. An answer comes from the world the program runs in, or from an answer the program installs explicitly. The prelude claims no implementation of quantum measurement |
| N2 | **Adopted, with a qualification.** The group is unsealed; a program may install an answer | It allows explicit environmental adapters and test stand-ins without changing what physical measurement means, and it needs no seal made for measurement alone. The qualification: *environmental measurement* (an answer from the actual execution environment) and a *stand-in* (a modelled reply the program supplies for tests, simulations or controlled experiments) are kept apart. A stand-in implements the request's contract. It does not establish that a physical measurement occurred, and it does not make what follows quantum measurement |
| N3 | **Adopted for now.** `measure()` takes no argument | No qubit type or register exists, so no argument model is invented in advance. When quantum registers or qubit types are introduced, the signature is revisited together with the semantics of measurement, state update, outcome representation and irreversibility |

*Enforcement points.* The interpreter refuses an unanswered `measure`
at run time (status 70). Compiled code refuses at build time (status 1).
These are different enforcement points, not contradictory semantics:
neither backend runs past a `measure` that nothing answers. The build
refusal is the broader of the two. Compiled code has no `ask` at all
(Selvage backlog item 5), so it refuses a program that asks `measure`
even where a stand-in would answer it.

*Disposition.* Further quantum work stays gated by actual quantum-state
and backend support, not by the existence of the `Measure` request. A
request can be declared before its physical realization exists;
declaring it does not establish the realization.

## Budgets

**Performance.** After every Selvage phase, run `bench/run.py`. The
geometric mean against C (1.12 in the archive) must not rise beyond
noise, and no benchmark may have the tape on its hot path. Hot
randomness stays a library rule of the Feistel kind.

**Minimalism.**

| | Before | After audit | After merge |
|---|---|---|---|
| Keywords | 39 | 38 (A1 retained `repeat while`) | 38 |
| Mechanisms | 3 | 3 | 3 |
| Checking rules | 8 | 8 | 8 |
| Arrows | 4 | 4 | 4 |
| Prelude | — | — | + 25 lines of code; 6 reserved names: 4 for the tape (after G7), 2 for `Measure` (Phase 7) |

## Risks

| Risk | Handling |
|---|---|
| moop's wiring changes after it is pinned | G2: versioned wiring; the trace test fails until the trace is deliberately regenerated, and Selvage then rules on the new wiring |
| The admission's synergy step is not accepted | The fallback in Phase 3: an example file, not prelude |
| "Answers in C" grows into the whole of backlog item 5 | Removed for the tape by G7: it compiles without answers |
| `draw` and `birth` collide with a program's own request names | Checked against Selvage's programs so far; re-check against any external code before ratifying G6 |
| More aliasing defects where instances hold arrays | Phase 1 fixes the known one first; Phase 3's generated tests copy and message instances |
| The tape drifts onto a hot path | The performance budget above; the description says where it belongs |
| `draw` is read as randomness | The description calls it a deterministic observation and cites the lag-`len_a` correlation; simulations use a certified rule of the Feistel kind |

## What happens in this repository

Only Phase 0, now done: one test, one moved file, and a section in
`docs/model.md`. moop's language, its two-layer rule and its open
questions are untouched by this plan. Everything that remains happens in
Selvage.

## Status: complete (2026-11-18)

| | |
|---|---|
| Phases 0, 1, 2, 3, 5, 6 and 7 | Complete |
| Phase 4 | Not needed for the tape (G7) |
| Rulings | G1 to G7 decided; in Selvage's register, C1 to C5 and N1 to N3 ratified (XII.1); A1 retains `repeat while`, so `0002` is not adopted |

**Outside this repository, and the maintainer's:**
- **Applying the patches to Selvage.** Patches `0001` and `0003` to
  `0008` (`selvage-patches/`, with instructions in its README) apply in
  order to the 0.4.9 release archive, and reproduce the validated tree
  byte for byte. No Selvage repository was reachable from the sessions
  that built them, so none has been applied anywhere.
- **Selvage's version number.** It is 0.4.9 throughout the patches.

**Permanent, on moop's side.** Wiring 1 stays frozen, and both languages
reproduce `tests/tape_vectors.txt` byte for byte. A change of wiring is
a new numbered wiring with a new trace, which Selvage would then rule
on (G2).
