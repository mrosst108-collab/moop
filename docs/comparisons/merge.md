# System-facing reversibility and a viable moop/Selvage merge

An exploration, not a decision. It asks what "system-facing
reversibility" has to mean for a merge to keep both performance and
minimalism, and tests the load-bearing claims against the Selvage 0.4.9
toolchain (Clang 18.1.3). The test programs are in
`experiments/`. Nothing here changes moop; see "What this means for
moop" at the end.

## 1. What system-facing reversibility is

Both languages hold the same invariant under different guarantees:

> The system never loses information, except at one declared boundary.
> Whatever a user process forgets, the system either never needed or
> retains until that boundary.

| | moop | Selvage |
|---|---|---|
| Guarantee | **Substrate**: the system layer is tapes and self-inverse gates, so it cannot lose information | **Certificate**: the checker proves each system rule one-to-one; the prelude has no lossy clause |
| What happens to a user loss | Forgotten silently in RAM | Kept by the system (`keep` to Root, a bijection on the journal) |
| The one declared boundary | `prune` — zeroes causally inert cells | `commit` — dissipates the journal |
| Reach of the round trip | Between prunes | Between commit points |

Two correspondences fall out:

- **`prune` and `commit` are the same act**: the single sanctioned
  forgetting on the system side, explicit, and the horizon past which
  nothing rewinds. They differ in selection — prune drops what was never
  causally used, commit drops everything retained. Selvage already does
  the selective part earlier: a value that can still be computed is
  dropped for nothing, so only what restoration needs is ever kept.
- **A user loss becomes a system retention.** This is Bennett's history
  tape, and it is what makes the system side reversible *while the user
  side forgets*. moop does not have it: its user layer forgets without
  the system retaining anything, so in moop reversibility holds for the
  substrate, not for a run.

The substrate guarantee is free where it applies and applies only to
what runs on the tapes. The certificate guarantee costs a checker and
applies to all system code wherever it runs. A merge that wants
performance needs the second: system code must be able to run natively
and still be proved reversible.

## 2. What it costs

Selvage's own measurements (`bench/results.md` in its archive; not
re-run here), compiled C23 against handwritten C23:

| Kind of code | Example | Ratio to C |
|---|---|---|
| Functions: nothing kept (overwrites are recomputable) | fib, collatz, sieve, nbody | 0.98 – 1.27 |
| Certified in-place rules, run forward and through the derived inverse | prefix, orbit | 1.19 – 1.23 |
| Lossy rule journaling 64 bits every step, committed every 1000 | damped | 1.16 |

So system-facing reversibility by certificate costs roughly nothing for
functions and under a quarter on the worst cases measured. That is the
performance a merge must not lose.

## 3. Experiments on the tape

All certified by the 0.4.9 checker; timings are compiled code, 100
million iterations, three runs.

| Experiment | File | Result |
|---|---|---|
| Tick as a certified rule | `tape.selv` | Certified. Extent *one-to-one*; defined-everywhere and onto not established |
| Draw as an answer | `tape.selv` | Certified (class *bijection*; the toolchain reports no extent for answers). `undo` with a flipped draw is refused — it behaves as an embedding |
| Empty / one-cell tape; counter wrap at length 3 | (variants of `tape.selv`) | Accepted statically, refused at run time: division by zero; R4 alias |
| **Birth as a certified rule** | `birth.selv` | Certified. Extent *one-to-one, not onto* — an embedding. `undo birth` returns the parent exactly |
| Tick cost, run-time lengths | — | ~2.5 ns per tick, one bit per tick |
| Tick cost, literal lengths | `tick_timing.selv` | ~2.9 ns per tick. **No improvement**: the modulo operations were not the bottleneck |
| **Feistel round** `add r * r + k to l; swap l and r` | `feistel.selv` | Certified as a full **permutation** by its steps alone. ~1.6 ns per round, 64 bits per round, forward and through the derived inverse |

Three findings:

1. **moop's birth is a certified Selvage rule.** "The generator can
   step back to before the birth" is `undo`. This was the merge's main
   untested claim; it holds.
2. **The tape's certificate is weaker than it looks.** R4 is checked
   per run, not proved for the type: no type states "length ≥ 2", so
   the tape is a *partial* injection guarded at run time.
3. **A three-line rule dominates the tape on classical hardware.** The
   Feistel round is about 100× faster per bit, has the stronger
   certificate (a permutation, defined everywhere, nothing left to
   run-time checks), and needs no prelude entry at all — any program can
   write it.

## 4. Where the tape earns a place

On classical hardware it does not win. On gates the ranking reverses:

| | Classical cost per bit | Gate cost per bit |
|---|---|---|
| CCNOT tape | ~2.9 ns | 2 Toffolis (the tick *is* its own circuit) |
| Feistel round | ~0.025 ns | On the order of 100 Toffolis — a 64-bit multiplier and adder per 64 bits (an estimate from schoolbook circuit sizes, not derived from Selvage's lineage tool) |

Both backends must give the same values, so `draw` needs one
definition. The asymmetry picks it:

- Draws that seed births are **rare**. A 12-cell birth costs ~35 ns on
  the tape — irrelevant.
- Gates are the scarce resource in the reversible and quantum
  realization profiles.

So: **define `draw` and `birth` by the CCNOT tape, and keep them off hot
paths.** Hot randomness (a stochastic simulation) is a library rule of
the Feistel kind, which costs the language nothing. The tape passes the
deletion test only in this role; as a general generator it is covered
by an ordinary certified rule.

## 5. The merge

**Kernel: Selvage's, unchanged.** Form, Rule, Request; checking rules
R1–R8; native execution; gate lineage as realization.

**What moop contributes**

| moop idea | Form in the merge | Adds |
|---|---|---|
| CCNOT tape | Prelude answer `CcnotTape for Draw` (requests `draw`, `birth`); rule `tick` | One type, one request group, one answer — about 20 lines of prelude |
| Bridge shape (reversible effect, observation outside) | Copy into an empty name: a certified embedding | Nothing: already V.4 |
| Generation distinct from delegation | `birth` (who made you) is a message to a tape; delegation (whom you defer to) is to a state component | Nothing: two existing mechanisms, kept apart |
| ≥ 2 cells per loop | R4 | Nothing |
| `prune` | `commit` | Nothing |
| Deletion test | Governance beside the admission test (applied in the audit: `repeat while`, `repeat N times` deleted) | Nothing in the language |

**What does not carry over**

| Item | Why |
|---|---|
| The tape as the machine | One fixed permutation; ~100× slower per bit; universality unshown |
| Memory segregation (tapes vs RAM), `logic.c` | One set of gates; an irreversible gate is a reversible gate and a declared discard |
| The article `a` / `an` | It would be notation for `x -> birth()`, but reserving `a` collides with the commonest name in Selvage programs (`a` is the array in nearly every example). The message form needs no keyword |
| `<-` as a lineage predicate | Delegation to a state component covers it |
| Rebindable names | Linearity needs one binding per name |
| Causal marks | Heuristic metadata in moop already; Selvage's "dropped for nothing" does the principled part |

**Minimalism account.** Against Selvage after the audit rulings (37
keywords): zero keywords, zero mechanisms, zero checking rules added;
one small prelude answer. **Performance account.** Nothing on a hot
path changes; compiled Selvage is as fast as before. The tape is paid
for only at births and draws.

## 6. What must be built first

In dependency order; each is already an open item in Selvage:

1. **Answers in compiled code** (IX.2). Until then `draw` and `birth`
   as messages run only in the interpreter. (`birth` as a plain clause
   rule compiles today.)
2. **Extent for answer rules.** The report says "bijection" for an
   answer that is an embedding and gives no extent line.
3. **A static length invariant, or fixed-size arrays.** Without it the
   tape's R4 condition is a run-time guard and its domain is partial.
4. **The reversible realization profile**, with the tape as its first
   program — its circuit is its own definition.
5. **Bounded head counters**, so counter wrap cannot break the ring at
   lengths that do not divide 2⁶⁴.

Quantum features stay vestigial: a `measure` request group with no
answer installed is refused at Root until a quantum profile installs
one. `draw` (deterministic, certified) and `measure` (world input, a
commit point) are separate requests, because a rule's class is decided
statically and cannot depend on which answer is installed.

## 7. What this means for moop

The merge keeps moop's *ideas* and almost none of its implementation.
Two honest readings:

- **moop converges.** Then moop is the design record for a prelude
  answer and three correspondences, and this repository's interpreter
  is retired.
- **moop stays separate**, as the study of the substrate guarantee —
  what a language is like when the tape *is* the machine. Then its open
  problems are the ones this exploration sharpened: the tape is not
  programmable (one fixed permutation), its user layer forgets without
  declaring it, and reversibility is asserted by tests rather than
  proved. A programmable reversible tape (a universal reversible
  cellular automaton in place of the single gate) is the direction that
  would address the first; it trades more speed for it.

These are not exclusive: moop can remain the small substrate study
while the tape, as specified here, becomes Selvage's `CcnotTape`.
