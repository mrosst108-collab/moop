# moop and Selvage

Selvage (specification 0.4, toolchain 0.4.9) is a sibling design: the
same parents (Quorum, Io, Toffoli/Bennett) and nearly the same
vocabulary — CCNOT, MAYBE, `->`, `<-`, `<->`, a system root and a user
root, two tiers, homoiconicity, pythonic blocks. On almost every shared
word it made the opposite decision. This note records the comparison and
runs moop's deletion test (`docs/derivation.md`) on what Selvage
suggests. Per the derivation rule, nothing here is adopted on Selvage's
authority; each item is either re-derived in moop's terms or left out.

Source read: Selvage's README, SPEC.md, examples and benchmark results.
Its claims are reported as its specification states them; none were run.

## One-line contrast

Selvage is a large, certified systems language that uses CCNOT to
*justify* reversibility (a realization lineage beside native execution).
moop is a tiny language that *runs on* CCNOT (the tape loops are the
machine).

## Scale

| | moop | Selvage |
|---|---|---|
| Implementation | ~2.2k lines of C23 | ~11k lines of Python, plus a C23 code generator and runtime |
| Design text | ~500 lines | 2.4k-line spec; every entry carries Implementation / Design / Evidence status |
| Keywords | 6 (`is ask inherits mirrors a an`) | 39 |
| Grammar | one rule, `chain ["is" [chain]]` | full grammar (`rule … takes … returns`, `add p to q`, `repeat with …`) |
| Values | 0..255 on 8-cell loops | words, floats, text, arrays, records; C23 output within 12% of handwritten C |

## Point by point

| Topic | moop | Selvage |
|---|---|---|
| CCNOT | The machine: one gate between two counter-rotating loops, firing every tick | A four-clause prelude rule; the root of a *realization lineage*; not on the execution path |
| `<->` | An operator on values and bodies; only involutions (XOR deposit, exchange) | A clause arrow: the checker certifies a rule as a bijection, and the prelude rule `mirror` derives its inverse as code |
| `<-` | Lineage predicate; parents fixed at birth | Field-only record derivation; behaviour is delegation to the one state component that answers |
| MAYBE | Deterministic oracle draw: step the core, observe a cell (the primitive bridge) | Kleene `Trit` plus `decide`, which routes only undecided cases outward (rule book, person, model), recorded for replay |
| Loss | User layer forgets freely (`logic.c`); the system's one forgetting is causal pruning | No irreversible primitive: an ordinary gate is a reversible gate plus a declared `discard`, journaled to Root and rewindable |
| Layer boundary | Segregated by **memory** (tapes vs RAM) | Segregated by **authority** (a seal on Root) over one set of gates |
| Roots | Nothing delegates into the system root | `Object` (user root) delegates *everything* to `Root` |
| Names | The mutable handle; rebinding is fine | One binding per name; `set` is an explicit, journaled overwrite |
| Homoiconicity | Layered (tapes / chains in RAM); no reflection yet | Everything is a form, declarations and the whole program included; a census tool checks nothing escapes |
| Receiver | No keyword; headless chains | `ask op()` goes to the nearest installed answer (dynamic, handler-like); `inst -> op()` to a named one |
| Method | Deletion test: remove what a uniform rule covers | Admission test: foundation, synergy, interference, uniformity |
| Honesty | Unimplemented things error plainly | Per-claim status and evidence fields; a list of defects found and corrected |

The two methods are complementary: Selvage's test filters what may
enter, moop's removes what a uniform rule already covers. Both reject
the same thing — a construct with no derivation.

## Three suggestions, put through the deletion test

### 1. Irreversible operators as reversible gate + declared discard

**Selvage's claim.** An irreversible gate is not a second kind of
primitive: `and_gate(a, b)` is `and_into(a, b) = (a, b, a∧b)` (CCNOT
into a zeroed cell) followed by discarding `a` and `b`.

**In moop's terms.** CCNOT with target 0 computes AND into the target;
NOT on the inputs and a target of 1 give OR (De Morgan); target 1 alone
gives NAND; CNOT gives XOR. So every operator in `logic.c` *except*
MAYBE is "a gate the system already has, followed by forgetting the
inputs". The forgetting is the only part that belongs to the user
layer — and that is already the bridge shape (reversible effect inside,
irreversible observation outside).

**Deletion test.**
- *Uniform rule:* "a user-layer operator is a system gate on fresh
  cells, then an observation of the target." Covers AND, OR, NAND, NOR
  and XOR.
- *Silence?* No: the loss still happens where it happened before (the
  user discards the inputs); nothing that was an error becomes an action.
- *Ambiguity?* No: each operator name keeps one meaning.
- *Evidence from the code:* `moop_and`, `moop_or`, `moop_nand`,
  `moop_nor` and `moop_xor` are called nowhere except their own unit
  tests. The evaluator uses only `moop_maybe`.

**Verdict: the five operators fail the test as *primitives*.** They
should become derived — gate followed by observation — whenever the
surface language gains logic words (an open question in `syntax.md`).
MAYBE survives: it is the bridge itself, not a derivable gate. This
does **not** import Selvage's journal: moop's user layer still forgets
for real; the change is only that forgetting is never a primitive of
its own.

*Next step (not taken here):* when `and`/`or`/… reach the surface,
implement them through `gates.{h,c}` on scratch cells plus observation,
and delete the bespoke bodies in `logic.c`.

### 2. Derived inverses for `<->`

**Selvage's claim.** A rule whose clauses are exclusive and exhaustive
is certified as a bijection, and its inverse is derived by reading each
step backward; the inverse is itself code.

**In moop's terms.** moop already has the ingredients: every `<->` form
is an involution, involutions are their own inverses, and a *sequence*
of involutions `f₁ … fₙ` has the inverse `fₙ … f₁`. So a taught chain
built only from `mirrors` steps is a bijection whose inverse is the
same chain reversed — derived, not written. This answers the open
question (`celsius <-> fahrenheit`) without a checker of Selvage's
size: the certificate is *structural* (only `<->` steps allowed), not
analytical (clause exclusivity).

**Deletion test.** No existing construct covers definable bijections;
`<->` today accepts only primitive involutions. Reversing a chain is a
uniform rule with no new keyword: run the steps in reverse order. The
risk to check is ambiguity: such a chain composed of involutions is in
general *not* itself an involution, so "applying the same `<->` twice is
the identity" would stop being true of user-defined forms. That must be
decided before building: either `<->` keeps the involution guarantee
(and composite bijections need an explicit reverse direction), or the
documented guarantee becomes "every `<->` form has a derived inverse".

**Verdict: earns a design, not yet code.** It is the strongest import.
It compounds with homoiconicity (inverses come from reading taught
chains as data — the reflection moop is still missing) and with
reversibility (the inverse is the backward run).

### 3. MAYBE as Kleene logic plus `decide`

**Selvage's claim.** `maybe` means "not yet decided"; Kleene logic
carries it, and `decide` routes only undecided cases outward, recorded
for replay.

**In moop's terms.** moop's MAYBE is not a truth value; it is an
*observation* of the reversible core — the primitive bridge, which also
seeds every birth (`proto.c`). Renaming it into a third truth value
would give one word two meanings: oracle draw and "undecided".

**Deletion test.** Adopting Kleene `maybe` as well creates ambiguity
(one form, two meanings), and replacing the oracle draw would remove
what births are built from. Selvage's *idea* — escalating undecided
questions to an outside decider, replayably — has no derivation in
moop yet: nothing in the axioms forces a third truth value.

**Verdict: rejected as stated.** Recorded so that the open question in
`model.md` (nullary draw vs. `a maybe b`) is settled with this option
in view.

## Left out deliberately

- **Delegation from the user root into the system root.** Contradicts
  moop's rule that delegation never crosses the layer boundary.
- **One binding per name.** Contradicts names as moop's one mutable
  handle; lineage is fixed, names move.
- **A journal of every loss under Root's authority.** moop's sanctioned
  forgetting is causal pruning of provably inert cells; a second,
  general retention mechanism would duplicate its job.
