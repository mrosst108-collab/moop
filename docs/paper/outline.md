# Paper outline: reversibility × homoiconicity in moop

> Superseded by the full paper, `paper.tex` / `paper.pdf`. Kept as the
> planning outline. Two of its claims changed when the work was done:
> the "every non-trivial orbit rewrites B" observation holds at the nine
> sizes below but not in general (a sweep over all 100 loop pairs with
> a + b ≤ 22 found 184 short *restoring* orbits — paper §5), and births
> are now literally create + observe + deposit, so the `seed()` note in
> §8.6 no longer applies.

Working title: **No Conserved Program: Reversibility and Homoiconicity
as One Design Principle**

Alternates: *Causal Closure in a Two-Loop Toffoli Machine*;
*Programs That Remember Being Rewritten*.

Target: a full paper (~25 pp., e.g. *The Art, Science, and Engineering
of Programming*), or ~16 pp. for the Reversible Computation (RC)
conference by cutting §9 to a page.

Every number below comes from `docs/paper/experiments.c` (exhaustive
results are exact; sampled ones use a fixed seed). Each section lists
the repository sources it draws on. A claims ledger at the end records
what each claim currently rests on.

---

## Abstract (draft)

Reversibility and homoiconicity are studied in separate communities:
one as a property of computation's semantics and thermodynamics, the
other as a property of how a language represents code. We study them
together in moop, a machine whose system memory is two counter-rotating
circular tapes coupled by a pair of Toffoli gates, and whose user memory
is conventional RAM under irreversible logic. We give a closed form for
the core — two nonlinear feedback shift registers coupled by a single
AND term — and define homoiconicity *dynamically*, as the absence of an
autonomous program subsystem. Against a control wiring in which one
tape is a read-only program (a Harvard machine), an exhaustive census of
all 2²¹ tape states shows the difference: the control conserves its
program, splitting into 442,990 orbits none longer than 255 epochs;
moop's wiring has 8,938 orbits, *every* non-trivial one rewrites the
would-be program tape, and the longest tours 8,191 of the 8,192
possible programs. We then state the synergy as theorems: with both
properties, a mutable program's full history is recoverable from any
state, and distinct programs never converge — so any many-to-one notion
of "answer" must live in an observation layer. This *derives* the
machine's two-layer segregation instead of assuming it. Causal pruning,
the one sanctioned erasure, unifies garbage collection and dead-code
elimination; we prove it never alters the past of the cells it keeps.
We close with what the synergy implies for a language built on top, and
where it currently stops.

---

## 1. Introduction

1.1 **Two properties, two literatures.** Reversible computing (Landauer,
Bennett, Toffoli) versus homoiconicity (Lisp; the stored-program
concept). Neither literature asks what each property does *for the
other*.

1.2 **The claim to test.** `docs/model.md`: "Neither property alone
yields any of this: reversibility with an external program keeps the
*system* irreversible; homoiconicity without reversibility is
self-modification with amnesia." The paper turns that 2×2 into
definitions, theorems, and measurements.

1.3 **The vehicle.** moop's core, its two-layer memory, and the
language on top. Kept small enough that every state of an 8/13-cell
machine can be enumerated.

1.4 **Contributions.**
1. A closed form for the core: coupled nonlinear shift registers (§4).
2. A dynamical definition of homoiconicity, plus an exhaustive census
   against a Harvard control (§5).
3. The synergy as four results: recoverable program history, no
   convergence, answers-are-observations, recurrence (§6).
4. Causal pruning with a rewind lemma, and a proof that its metadata is
   derivable (§7).
5. The two-layer segregation derived from §6, with moop's crossings
   mapped onto known information effects (§8).
6. Consequences for the language surface: involutions, program
   inversion, and the synergy's missing half (§9).

1.5 **Non-claims (stated up front).** No universality result. No
hardware. No efficiency claim. moop programs do not yet execute *on* the
core: the interpreter runs on a conventional host and uses the core for
observation, deposits, and birth seeds.

*Draws on:* `README.md`, `docs/model.md` ("Reversible + homoiconic:
causal closure"), `CLAUDE.md`.

---

## 2. Background

2.1 **Logical reversibility.** Landauer's principle; Bennett's reversible
Turing machine and uncomputation; the Toffoli gate's universality (with
ancilla); conservative logic.

2.2 **Two homoiconicities.**
- *Representational* (Lisp): programs are the language's own data
  structures.
- *Architectural* (stored program): code lives in writable memory.
  Contrast this with Harvard, where the program store is separate and
  read-only to execution.
- Note that circulating memory is itself old (EDVAC's mercury delay
  lines), so the novelty is not the loops.

2.3 **Where irreversibility goes in reversible languages.** Janus and
program inversion. James & Sabry's *information effects* (create and
erase as the only two effects over a reversible core). Causal-consistent
reversibility (Danos & Krivine). Knill's QRAM model: a classical host
around a reversible interior.

2.4 **Shift-register sequences.** LFSRs and NLFSRs (Golomb). Invertible
NLFSR state updates in stream ciphers (Trivium, Grain). This is a
prerequisite for §4.

---

## 3. The machine

3.1 **State and tick.** Two loops with cells and heads. Each tick does
*fire* (two CCNOTs: shared controls under the heads, targets on the next
cell of each loop), then *rotate* (A +1, B −1). Figure 1. Table 1:
tick semantics.

3.2 **Proposition 1 (exact inverse).** *fire* is an involution (shared
controls, distinct targets, CCNOT is self-inverse). Rotation is a
permutation. So step = R∘F and step_back = F∘R⁻¹. Note for §9: the
inverse is the *reversed sequence* of self-inverse parts.

3.3 **Why each loop needs ≥ 2 cells.** Otherwise a target aliases a
control, and a cell controlling its own flip is not self-inverse.

3.4 **The control: the original wiring.** Commit `2231ab2` had one
CCNOT targeting A only, so B was a read-only program tape. Commit
`745ecae` made the targets symmetric because the homoiconicity axiom
rejected a frozen program. Present this as a natural experiment: the
same machine with and without architectural homoiconicity. All later
comparisons use it.

*Draws on:* `src/tapeloop.{h,c}`, `src/gates.{h,c}`; `git show 2231ab2`
versus `745ecae`; `docs/derivation.md` §1 ("the design pushed back on
the code").

---

## 4. A closed form: two coupled nonlinear shift registers

4.1 **Theorem 1.** Let x_t, y_t be the cells under A's and B's heads at
tick t, with loop lengths a and b. Then

    x_{t+1} = x_{t+1−a} ⊕ (x_t ∧ y_t)
    y_{t+1} = y_{t+1−b} ⊕ (x_t ∧ y_t)

*Proof idea.* Each tick's targets are exactly the next tick's controls.
A cell is written only on the tick before it is read, so between reads
it is untouched for one full revolution.
*Check (E1):* 999,400 ticks, 0 violations.

4.2 **The inverse in closed form.** x_{t+1−a} = x_{t+1} ⊕ (x_t ∧ y_t).
Reversibility is visible in the recurrence itself.

4.3 **The Harvard control in closed form.** y_{t+1} = y_{t+1−b}: a
periodic drive with no feedback. x is a register driven by an external
clock. Homoiconicity is precisely the shared AND term feeding *both*
registers.

4.4 **What this explains.** MAYBE is the x-sequence, i.e. one keystream
bit per draw (E7: 0.4976 ones over 10⁶ draws). It is "unpredictable-
looking but replayable" for the same reason invertible NLFSR ciphers
are. Births are seeded from a keystream.

*Draws on:* `src/tapeloop.c` (`fire`), `src/logic.c` (`moop_maybe`),
README ("unpredictable-looking but replayable").

---

## 5. Homoiconicity as the absence of a conserved program

5.1 **Definition 1 (dynamical homoiconicity).** A system is homoiconic
if no proper subsystem evolves autonomously. Equivalently, its influence
graph is strongly connected. A "program tape" is exactly an autonomous
subsystem: it acts on the rest without being acted on. Contrast this
with the representational sense (§2.2), which §9 takes up.

5.2 **Proposition 2 (Harvard conserves the program).** Under the
control wiring, B is invariant. The state space splits into 2^b sectors,
one per program, each closed under the dynamics, so no orbit exceeds
2^a − 1 epochs (the all-zero data state is fixed). The bound is attained
at every size measured.

5.3 **Census (E2, Table 2).** Every tape state is enumerated under the
epoch map (one full alignment cycle, heads back at (0, 0)).

| loops | wiring | orbits | fixed | non-trivial | rewrite B | longest |
|---|---|---|---|---|---|---|
| 5/7 | moop | 194 | 159 | 35 | **35** | 1,424 |
| 5/7 | Harvard | 1,616 | 1,097 | 519 | 0 | 31 |
| 8/9 | moop | 850 | 767 | 83 | **83** | 32,509 |
| 8/9 | Harvard | 16,376 | 10,859 | 5,517 | 0 | 255 |
| 8/13 | moop | 8,938 | 8,551 | 387 | **387** | 506,447 |
| 8/13 | Harvard | 442,990 | 339,427 | 103,563 | 0 | 255 |

(The full table covers nine coprime pairs, from 2/3 to 8/13.)

5.4 **Observation 1 (every computation rewrites its program).** For
every size measured, every non-trivial orbit under moop's wiring changes
loop B. 99.6% of 8/13 states lie on such orbits. Status: verified
exhaustively up to 2²¹ states; a general proof is open (a candidate
argument uses firing parity — each firing flips one cell of each loop).

5.5 **A single orbit tours program-space (E3).** The longest 8/13 orbit
visits 8,191 of 8,192 B-values and 255 of 256 A-values: every non-zero
"program" and every non-zero "datum". In the control, every orbit
visits exactly one program.

5.6 **Reading.** Homoiconicity, dynamically, is *breaking a
conservation law*: the program stops being a constant of motion.
Reversibility then guarantees that breaking it loses nothing (§6).

*Draws on:* `docs/model.md` ("there is no designated program loop"),
CLAUDE.md ("no loop may become a read-only program tape"),
`tests/test_core.c` (both loops are transformed).

---

## 6. The synergy, stated as theorems

6.1 **Definition 2 (causal closure).** Step and its inverse are
functions of the state alone, with no external parameters.

6.2 **The 2×2 made formal (Table 3).**

| | program conserved (Harvard) | program in mutable state (homoiconic) |
|---|---|---|
| **irreversible** | data history lost; program constant | program history lost — "amnesia" |
| **reversible** | data history recoverable; program constant | program *and* data history recoverable |

6.3 **Theorem 2 (recoverable program history).** Under reversibility
and homoiconicity, the program trajectory P₀…P_T is non-constant
(Observation 1) and fully determined by any single state S_t:
H(P₀…P_T | S_t) = 0. Each of the other three cells of Table 3 fails one
of the two conjuncts.

6.4 **Theorem 3 (results carry their programs).**
- *Homoiconic side:* distinct initial states never reach the same state
  (injectivity), so a computation's state always encodes which program
  produced it.
- *Harvard contrast:* in the reversible control with uniformly random
  data, I(P; D_t) = 0. Each program permutes the data bijectively, so
  the data alone says *nothing* about which program ran.
- Relate this to "reversible programs compute exactly the injective
  functions" (Axelsen & Glück).

6.5 **Corollary 1 (answers are observations).** Extensional semantics —
many programs, one answer — is impossible inside the core. Any notion
of "result" must be a many-to-one projection π: S → V, and projections
forget. Hence the bridge shape ("reversible effect inside, irreversible
observation outside") and the two-layer memory are *forced* by the
synergy, not chosen. This is the paper's central derivation.

6.6 **Theorem 4 (recurrence; program identity is the orbit).** A
finite reversible system is a permutation, so every state is periodic.
With homoiconicity, every self-modification is eventually undone. "Which
program is running" is not well-defined; only the orbit is invariant.
The 8/13 machine has exactly 8,938 computations (orbits). Caveat:
recurrence takes up to 506,447 epochs (≈ 52.7M ticks). It is a theorem
about identity, not an undo mechanism; step_back is the practical undo.

6.7 **Self-modification with an audit trail.** Time-travel debugging of
code that rewrites itself: the bug may sit in an instruction that no
longer exists, and step_back recovers it exactly. Relate to omniscient
debugging and record/replay, which must *log* what moop recomputes.

*Draws on:* `docs/model.md` (causal closure bullets), `docs/derivation.md`
§4 ("Derivable pasts"), CLAUDE.md (segregation).

---

## 7. Forgetting exactly once: causal pruning

7.1 **Mechanism.** A cell is marked when it takes part in a firing
(actual cause, not counterfactual). An epoch is lcm(a, b) ticks.
Pruning zeroes unmarked cells, resets marks, and starts a new epoch.

7.2 **Lemma 1 (rewind).** Run k ticks, prune, run k ticks back: every
unpruned cell returns to its initial value. *Proof:* an unmarked set
cell was only ever a control beside a 0, so it never decided a firing.
*Check (E5):* 100,000 trials (41,520 actually pruned), 0 mismatches.
Note: `docs/model.md` says the state "factorizes" into web ⊗ inert.
That holds for the past (this lemma) but not counterfactually — a 0
cell that blocked a firing did shape the rest. State the lemma, not
the factorization.

7.3 **Pruning × homoiconicity: GC = DCE.** An inert cell is dead code
and dead data at once. Extreme case: 8,447 of the 2²¹ states never fire
in an epoch, and are pruned to zero entirely — dead programs vanish
wholesale.

7.4 **Proposition 3 (the metadata is derivable).**
- *Check (E6):* 20,000 trials. Stepping back within an epoch adds no
  marks, and rewinding to the epoch start then replaying reproduces the
  marks exactly. Marks are a *cache* of the trajectory, which causal
  closure makes recomputable.
- The tick count is recoverable from the head positions by the Chinese
  remainder theorem (coprime lengths, epoch-aligned prunes).
- So under the deletion test (`docs/derivation.md`), pruning adds no
  new state concept.
- Correction to `docs/model.md`: the "conservative over-approximation"
  from stepping back happens only when stepping back past the epoch
  start.

7.5 **Where pruning matters (E4, Figure 3).** Share of set bits that
are inert in the first epoch, by tape density:

| density | 2% | 4% | 6% | 8% | 10% | 20% | 30% | 40% | 50% |
|---|---|---|---|---|---|---|---|---|---|
| inert set bits | 82.9% | 68.4% | 55.5% | 44.6% | 35.7% | 12.0% | 3.4% | 0.9% | 0.2% |

Pruning is a sparsity phenomenon. On dense tapes it is nearly a no-op.

7.6 **Landauer accounting.** The prune's return value is the system
layer's *entire* erasure budget. Relate to Bennett's uncomputation
checkpoints and pebbling.

7.7 **Related.** Garbage collection in reversible languages; dependency
tracking in causal-consistent reversibility.

*Draws on:* `docs/model.md` ("Causal pruning", its caveats and open
questions), `src/tapeloop.c` (`prune_loop`, `moop_core_run`).

---

## 8. Two memories, two logics — derived

8.1 **The segregation (Table 4).** System memory is the tape loops
under NOT/CNOT/CCNOT/SWAP. User memory is RAM under
AND/OR/NAND/NOR/XOR/MAYBE.

8.2 **Proposition 4 (placement by information behaviour).** XOR appears
in both layers. As a 2→1 function (`logic.c`) it forgets; as CNOT
(`gates.c`) it keeps its control. What decides the layer is whether the
inputs survive, not which function is computed.

8.3 **The crossings as information effects (Table 5).** The system
layer is information-preserving except at exactly these points:

| crossing | moop construct | effect class |
|---|---|---|
| copy-out | `maybe`, `value` (observation) | measurement (QRAM) |
| controlled-in | `n mirrors box` (XOR deposit) | classically controlled gate |
| create | birth (`a dog`): fresh cells seeded | *create* / ancilla |
| erase | epoch prune | *erase* / Landauer |

This maps one-to-one onto James & Sabry's create/erase plus Knill's
measurement and classical control. In linear-logic terms, the core is
linear; birth is a controlled *contraction* and pruning a controlled
*weakening* — the "discharge of premises never used" in
`docs/derivation.md` §4.

8.4 **Theorem 5 (crossing rule) — to prove.** On a small calculus of the
core plus RAM: the user layer affects system state only through
involutions, and system state affects the user layer only through
observation. This is a non-interference-style result. Its proof would
replace enforcement-by-convention (§11).

8.5 **Actors and protos.** Actors have a reversible interior and an
irreversible surface: "the replies it gave are the only irreversible
product". The irreversibility lives entirely in what was *said*, never
in what *is*. Generation (who made you) is the only downward path;
delegation (`inherits`) never crosses the boundary.

8.6 **Generation as a Bennett copy.** A birth copies the generator's
keystream onto fresh cells; stepping the generator back returns it to
before the birth (tested). Formal-model note: `seed()` in `src/proto.c`
*assigns* cells. That is equivalent to CNOT onto zeroed ancilla only
because freshly allocated cells hold no prior information (the
interpreter does not even zero them). The paper's model should use the
CNOT form.

*Draws on:* CLAUDE.md ("Two memories, two logics", "Protos"),
`src/logic.c`, `src/gates.c`, `src/encode.c`, `src/actor.{h,c}`,
`src/proto.{h,c}`, `docs/model.md` ("Actors", "Protos and generation").

---

## 9. The synergy at the language surface

9.1 **Syntax that tracks information behaviour.** One-way arrows forget
(`ask` = `->`, `inherits` = `<-`). The two-way arrow preserves
(`mirrors` = `<->`). `is` names. The article births.

9.2 **`mirrors`: code that is its own inverse.** Deposit and exchange
are involutions; the tests check that applying one twice is the
identity. For an involution, the program text *is* its own undo.

9.3 **Derivation: general bijections without a new concept**
(proposal). The two open questions in `docs/syntax.md` — number↔number
bijections and reflection — are linked:
- *In place.* A bijection written as a chain of involutions inverts by
  *reversing the chain* (Prop. 1's template). With code as data, that
  reversal is an operation on a chain, so it needs reflection.
  Circuit-level existence is known: every permutation of n-bit values
  is synthesizable from NOT/CNOT/CCNOT; for n ≥ 4, odd permutations
  need one ancilla (Shende et al. 2003).
- *Out of place.* Any function f, even an irreversible one, becomes an
  involution as (x, y) ↦ (x, y ⊕ f(x)) (Bennett's embedding). moop's
  deposit is already the constant-f case.

9.4 **Layered homoiconicity, and the synergy's missing half.** Taught
chains are code as data in RAM (representational homoiconicity), but
re-teaching *replaces* the old chain. That is exactly what
`docs/model.md` calls "self-modification with amnesia". The synergy
currently stops at the layer boundary. Open: should re-teaching be an
exchange that hands the old chain back? Weigh this against the rule that
reversible operators belong to the system layer: is a layer defined by
medium or by information behaviour?

9.5 **Method.** The design was derived from axioms, and constructs were
derived *away* (`self`, `generate`) by the deletion test. This is only a
pointer; the method deserves its own essay.

*Draws on:* `docs/syntax.md`, `src/encode.{h,c}`, `src/eval.c`
(teachings), `docs/derivation.md`.

---

## 10. Experimental method and reproducibility

- Harness: `docs/paper/experiments.c`, linked against the real core.
  The Harvard control reimplements commit `2231ab2`'s `fire()`.
- Exhaustive: E2 and E3 (nine coprime loop pairs, up to 2²¹ states).
- Sampled, fixed-seed xorshift: E1 (50 × 20,000 ticks), E4 (4,000 per
  density), E5 (100,000), E6 (20,000), E7 (10⁶ draws).
- Runtime ≈ 8 s on one core. The unit tests (`make test`) cover the
  invariants the paper relies on: the round-trip, symmetric
  transformation, involutions, and generator rewind.

---

## 11. Limitations and threats to validity

1. **The language does not execute on the core.** This is the gap
   between "architecture model" and "architecture"
   (`docs/model.md`: program encoding is open).
2. **No universality.** The loops are finite and the wiring fixed;
   "Turing tape" is a misnomer for fixed-length loops. Universality
   would need unbounded loops and an embedding of a known universal
   reversible system.
3. **Dynamical ≠ instruction-level homoiconicity.** No instruction
   encoding exists. Theorems 2–4 are about state, not about "code" in
   the usual sense.
4. **Observation 1 is exhaustive only for small sizes**, and only for
   one wiring and coprime lengths.
5. **Recurrence times make Theorem 4 conceptual**, not operational.
6. **Pruning barely acts on dense tapes** (§7.5). The marks are
   metadata, and a manual mid-epoch prune breaks tick derivability by
   CRT.
7. **Segregation is enforced by convention in C** until Theorem 5 or a
   type/effect system exists.

---

## 12. Related work

- **Reversible computing:** Landauer 1961; Bennett 1973, 1989
  (time/space, pebbling); Toffoli 1980; Fredkin & Toffoli 1982;
  Toffoli & Margolus 1987; Morita 2017.
- **Reversible languages:** Janus (Lutz & Derby 1982; Yokoyama & Glück
  2007); Axelsen & Glück 2011; James & Sabry 2012 (information
  effects); Mogensen on reversible memory management (verify title and
  year).
- **Causality and reversibility:** Danos & Krivine 2004; Halpern &
  Pearl 2005 (actual causation, the basis of the marking rule).
- **Architecture:** von Neumann 1945 (EDVAC, delay lines); Harvard;
  Knill 1996 (QRAM); Vieri 1999 (Pendulum reversible processor).
- **Shift registers:** Golomb 1967; Trivium (De Cannière & Preneel);
  Grain (Hell, Johansson & Meier 2007).
- **Homoiconicity and reflection:** McCarthy 1960; Smith 1984.
- **Objects:** Self (Ungar & Smith 1987); Io (Dekorte); actors
  (Hewitt et al. 1973).
- **Naturalism:** Stefik & Siebert 2013 (Quorum syntax evidence).
- **Debugging:** Lewis 2003 (omniscient debugging); O'Callahan et al.
  2017 (rr).
- **Logic:** Girard 1987 (structural rules, for §8.3).

---

## 13. Future work

1. Compile taught chains onto initial tape states, so the language runs
   on the core.
2. Universality with unbounded loops, or a ring of gates
   (`docs/model.md` open question).
3. A proof of Observation 1.
4. Theorem 5 and a type/effect system for the layers.
5. Reversible re-teaching and reflection (§9.3–9.4).
6. Reclaiming pruned cells (shrinking loops) instead of zeroing them.
7. A k-epoch inertness criterion.
8. Hardware: adiabatic/reversible CMOS realization of the two-loop core.

## 14. Conclusion

Homoiconicity removes the conserved program. Reversibility makes that
removal lossless. Together they force meaning out into observation —
which is why moop has two memories.

---

## Appendices

- **A. Proofs:** Prop. 1, Theorem 1, Prop. 2, Theorems 2–4, Lemma 1,
  Prop. 3.
- **B. Experiment harness and full census table** (all nine sizes, both
  wirings, including silent-state counts).
- **C. REPL transcript** (README session: births, teaching, delegation,
  `mirrors` twice).
- **D. Design history as a derivation chain:** commit table from
  `2231ab2` (core) to `a83d087` (derivation), each row giving the axiom
  that forced the change.

## Figures and tables

- Fig. 1: two loops, two CCNOTs, heads and targets.
- Fig. 2: orbit-length distributions, moop vs. Harvard (8/13).
- Fig. 3: pruning yield vs. density.
- Fig. 4: the layer boundary, with the four crossings.
- Tables 1–5 as placed above.

---

## Claims ledger

| claim | where | rests on |
|---|---|---|
| step_back inverts step | §3.2 | proof + round-trip unit test |
| coupled-NLFSR closed form | §4.1 | proof sketch + E1 |
| Harvard conserves program, orbits ≤ 2^a − 1 | §5.2 | proof + E2 (bound attained at all 9 sizes) |
| every non-trivial orbit rewrites B | §5.4 | E2 exhaustive ≤ 2²¹; **proof open** |
| longest orbit tours 8,191/8,192 programs | §5.5 | E3 exhaustive |
| program history recoverable | §6.3 | proof (injectivity + Obs. 1) |
| I(P; D_t) = 0 under Harvard | §6.4 | proof (each program is a bijection) |
| answers must be observations | §6.5 | corollary; the central derivation |
| rewind lemma | §7.2 | proof + E5 |
| marks derivable by replay | §7.4 | E6; proof straightforward |
| crossing rule | §8.4 | **to prove** on a core calculus |
| bijections = involutions + reversal | §9.3 | known circuit results; language design **proposal** |
| moop programs run on the core | — | **not true yet**; stated as a non-claim |
