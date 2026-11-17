# The moop computational core

The central primitive of moop is a single **CCNOT (Toffoli) gate** connected
to two **counter-rotating circular Turing tapes** ("loops").

- CCNOT — `target ^= (control1 AND control2)` — is reversible and universal
  for classical computation.
- Tape rotation is a permutation of cell positions.

Because every tick is a reversible gate followed by a permutation, the whole
machine is reversible: the core can run backward, exactly. This is the
load-bearing invariant of the runtime.

## Wiring 1 (frozen; a new wiring gets a new number)

Implemented in `src/tapeloop.{h,c}`:

- Loop **A** rotates forward one cell per tick; loop **B** rotates backward.
- Gate controls: the cell under A's head and the cell under B's head.
- Gate targets, symmetric: the shared controls drive two CCNOTs, one on the
  *next* cell of each loop (the one about to rotate under the gate). Each
  tick's outputs become controls on later ticks — that feedback is what
  makes the core compute rather than merely permute.
- The two CCNOTs share controls and write distinct targets, so they commute
  and the pair is self-inverse: reversibility survives the double write.
- Each loop must have at least 2 cells, or its target would alias a control
  and self-inverseness (hence reversibility) breaks.

Counter-rotation means the pair of aligned cells shifts by (+1, −1) each
tick: with coprime loop lengths, every cell of A meets every cell of B once
per `lcm(len_a, len_b)` ticks.

### Pinned, with a second implementation

The wiring above is **wiring 1**, frozen when the tape gained a second
implementation: Selvage's `CcnotTape`, a certified answer whose
candidate prelude text is `docs/comparisons/experiments/ccnot_tape.selv`
(see `docs/comparisons/merge-plan.md`). moop stays a separate language
and is that answer's **reference model**.

- `tests/tape_vectors.txt` is a trace of wiring 1 on the interpreter's
  8/13-cell bodies: 40 draws, a birth through `moop_proto_generate`, 20
  draws from the child, and the birth undone. `test_wiring_1_trace` in
  `tests/test_core.c` checks that moop reproduces it byte for byte, and
  Selvage's interpreter reproduces the same file. It is written in
  Selvage's output format so both sides compare against one file.
- It pins more than the gate: MAYBE's observation point (loop A's head,
  after the tick) and the seeding order of a birth (A's cells, then B's).
  Changing either fails the trace and no other test.
- Iterating the wiring is still allowed, but as a **new wiring, not an
  edit**: give it the next number, update this section, and regenerate
  the trace (on a mismatch the test leaves this run's trace in
  `build/tape_vectors.txt`). The second implementation then no longer
  matches, and says so, until Selvage rules on the new wiring.

## Reversible + homoiconic: causal closure

The loops are required to be both **reversible** and **homoiconic**, and the
two properties are synergistic — each makes the other worth having:

- Homoiconicity puts the program on the tapes: there is no designated
  program loop (the symmetric targets guarantee this — a read-only loop
  would be a frozen external program). Every cell is simultaneously
  potential instruction (control) and potential data (target).
- Reversibility means the state alone determines both future and past.
- Together the system is **causally closed**: nothing outside the loops is
  needed to run forward or backward — and running backward from any state
  recovers *the program that produced it*. Every program carries its own
  provenance.
- Self-modifying code becomes safe: every self-rewrite is invertible, so
  the audit trail is never destroyed — time-travel debugging of
  self-modifying code.
- Evaluation is a bijection on program-space: running code *is* a
  reversible transformation of code.
- It composes with causal pruning: when code and data share a substrate,
  garbage collection and dead-code elimination are the same operation —
  causally inert cells are dead code and dead data at once.

Neither property alone yields any of this: reversibility with an external
program keeps the *system* irreversible; homoiconicity without
reversibility is self-modification with amnesia.

## Causal pruning

The loops auto-prune: information not causally related to the current state
is discarded.

- **Causal web.** Each cell carries a mark. A cell is marked the first time
  it participates in a *firing* — a tick where both controls are set, so
  state actually changes. Controls and target all join the web (the marking
  rule is actual-cause, not counterfactual: a 0 control that "prevented" a
  flip does not join).
- **Inert = independent.** An unmarked cell has never influenced, nor been
  influenced by, any other cell: the state factorizes into (causal web) ⊗
  (inert cells). Zeroing an inert cell loses only its own value — nothing
  about the rest of the state.
- **Epoch.** One full alignment cycle, `lcm(len_a, len_b)` ticks — every
  cell of A has met every cell of B exactly once. `moop_core_run()`
  auto-prunes at each epoch boundary; `moop_core_prune()` prunes on demand.
- **Pruning is the sanctioned forgetting.** The reversible layer never
  loses information *except* here, explicitly — prunes are the system
  layer's analogue of Bennett-style uncomputation checkpoints. The
  step/step_back round-trip guarantee holds between prunes, not across
  them. A prune resets marks and starts a fresh epoch, so causal status
  must be re-earned each epoch.

Honest caveats of this initial design: an inert cell pruned today might
have fired in a *future* epoch (its alignments repeat, but A's contents
will have changed), so pruning trades never-yet-used information for a
smaller live state; and marks are a conservative, monotone approximation
(stepping backward also marks).

## Two memories, two logics

moop segregates the machine into layers that must not blur:

| | System layer | User layer |
|---|---|---|
| Memory | gate-based tape loops (`src/tapeloop.h`) | conventional RAM, byte-addressable (`src/ram.h`) |
| Operators | reversible: NOT, CNOT, CCNOT, SWAP (`src/gates.h`) | irreversible: AND, OR, NAND, NOR, XOR, MAYBE (`src/logic.h`) |
| Character | never loses information; every op is self-inverse | forgets freely; values are consumed into results |

Segregation rules:

- Reversible operators act only on system memory cells; they must never
  touch RAM.
- Irreversible operators act only on user-facing values; they must never
  write system memory.
- **Bridging is sanctioned only in one shape**: reversible effect inside,
  irreversible observation outside. MAYBE is the primitive bridge:
  `moop_maybe(core)` advances the reversible core one tick and observes the
  cell under loop A's head — deterministic and reproducible (same tapes →
  same answers), and its only effect on the system layer is a reversible
  step, so even the bridge loses no information. Actors (below) generalize
  this same shape into the object model.

## Value encoding

Numbers live on tape states as binary: bit i of a value is cell i of
loop A (`src/encode.{h,c}`). The primitives are involutions, keeping
`<->` bijective as a fact:

- **Deposit** (`moop_encode_xor`): XOR the value in via gate-layer NOTs.
  Self-inverse — writing and unwriting are the same reversible act.
  Deposited cells are causally marked so pruning spares deliberate
  deposits.
- **Exchange** (`moop_exchange`): pairwise gate-layer SWAPs between two
  bodies' A-tapes; marks travel with their cells.
- **Decode** (`moop_decode`): pure observation, no effect.

Values wider than the loop are refused, never truncated: silent
truncation would make a "bijection" lossy.

## Actors

Actors (`src/actor.{h,c}`) are the bridging construct between the layers.

- **Non-hereditary, yet they inherit.** Actors have no parents: message
  lookup is strictly local, and a miss never delegates — `<-` has no
  meaning for an actor. What an actor *does* inherit comes from the
  substrate, constitutionally: its body is a reversible core, so every
  actor is reversible and homoiconic by construction, not by lineage.
- **They host irreversible, user-facing messages.** The hosted surface is
  a table of named messages; sending consumes a reply into the forgetful
  user world. Handlers may act on the body only through reversible
  operations (gates, steps) and observation. Hosting and un-hosting are
  themselves irreversible, user-layer acts.
- The paradox resolves into the layer boundary drawn through each object:
  reversible interior, irreversible interface. Undo the reversible steps
  and the actor's whole state returns — the replies it gave are the only
  irreversible product (covered by tests).

## Protos and generation

Above the actor sits a generative hierarchy (`src/proto.{h,c}`): the
system-facing actor generates the system-facing root proto; the system
root generates user-facing root protos; user-facing protos generate
protos, which generate protos... All of them inherit reversibility and
homoiconicity — by construction, because every generated body is a
reversible core on the substrate. That inheritance flows down the
*generative* chain, and is independent of message delegation.

Generation and inheritance are distinct relations, and moop keeps them
apart where other object models fuse them:

- **Generation is an act** (who made you). It is the only downward path
  from system to user layer, and it has the sanctioned bridge shape: a
  child's initial tapes are seeded by observing the generator's
  reversible dynamics — one MAYBE draw per cell. Generation is therefore
  deterministic given the generator's state, and *costs the generator
  nothing irreversible*: step it back and it returns to the moment before
  the birth. Provenance needs no pointer; the substrate can always run
  backward.
- **Inheritance is a pointer** (whom you defer to). Message lookup
  delegates up parent links among user-facing protos, with the original
  receiver remaining the one addressed (where Io answers to `self`, moop
  keeps the receiver implicit). Delegation never crosses the layer
  boundary: user-facing roots have no parent, nothing delegates into the
  system-facing root, and nothing delegates into the actor.

So the full object ladder is: actor (non-hereditary) → system root proto
(delegation root, generative factory) → user root protos (roots of user
delegation trees) → protos all the way down.

## Wiring 1's draws, measured

Measured on the interpreter's 8/13-cell bodies with
`docs/comparisons/experiments/tape_statistics.c` (exhaustive over all
2²¹ tape contents; one epoch, 104 ticks, returns both heads to 0, so the
epoch map is a permutation and every period is a multiple of 104):

- **Periods.** 8,938 cycles. 0.44% of states repeat within 416 draws;
  90% have periods of 6.8 to 54 million draws; the longest is 52,670,488
  draws (a quarter of the 218 million states counting head positions).
  The short cycles include the obvious degenerate families: with B all
  zeros the gate never fires and draws replay A; with A all zeros every
  draw is 0.
- **Correlation at lag `len_a`.** A draw agrees with the draw 8 places
  back 74.8% of the time (0.5 would be none). The cause is structural: a
  draw reads the A cell under the head, that cell returns under the head
  every `len_a` ticks, and in between it flips only when both controls
  were set, about a quarter of the time. Single-draw bias (50.2% ones)
  and adjacent pairs look unbiased, so a casual check misses it.
- **Births inherit it.** A child's A cells are draws 0–7 and its B cells
  draws 8–20, so over all parent states its B[k] equals its A[k] in
  exactly 75% of cases (k < 8), as does B[k+8] with B[k].

So MAYBE is a deterministic observation, not a source of randomness, and
should never be described as one. This does not touch reversibility or
homoiconicity; it bounds what draws may be used for.

## Open questions

- **Wiring 2: open, not scheduled.** Wiring 1 stays: the tape is not a
  random source, so its correlation is a defect only against an objective
  nobody has set, and changing it moves the pinned trace. A wiring 2
  needs a positive objective first, and must then show that it keeps the
  gate cost (2 Toffolis per drawn bit), keeps births certified and
  undoable, improves the specific property targeted, keeps a fully
  specified state domain, keeps both loops writable (homoiconicity), and
  is pinned by its own trace. Passing that would still not make it
  "random"; that claim needs its own statistical evaluation.
  The leading candidate, kept as an experimental observation rule (not
  adopted here, not promoted into Selvage's prelude): observe **A xor B
  under the two heads** instead of A alone. The tape's dynamics and its
  observation are separable, so this is a narrow change:
  - *Gate cost:* 2 Toffolis and 2 CNOTs per drawn bit (wiring 1 has 1
    CNOT). No Toffoli added.
  - *Domain, reversibility, homoiconicity:* met by construction. The
    tick, the state and the cells written are wiring 1's exactly, so the
    periods, the step/step_back round trip and "both loops transformed"
    are unchanged.
  - *Births* (all 2²¹ parents): a child's B[k] equals its A[k] in
    50.00% of cases, and B[k+8] its B[k] in 50.00% (wiring 1: 75.00%
    each). The internal correlation is gone.
  - *Draws* (every lag 1 to 104): worst agreement 51.0% at lag 39 on the
    trace seed's cycle, 51.2% at lag 104 on the longest (wiring 1: 74.8%
    at lag 8 on both). Sampling noise is ~0.01 to 0.02 points, so this
    residual is real: about twenty times smaller, not zero.
  - *Not done:* a new trace, regression tests, other cycles, lags past
    104, and any statistical test suite.
  Moving the observation to a single other cell does not work: every
  cell returns under a head periodically, so observing B moves the 74.8%
  to lag 13, and A's parity moves it to lag 1. All figures:
  `docs/comparisons/experiments/tape_statistics.c`.
- Whether one gate suffices in practice or the core grows a ring of gates.
- How programs are encoded onto the loops, and how the surface language
  (natural, Quorum-like syntax) compiles down to initial tape states.
- MAYBE's final semantics: nullary oracle draw (current design), or a binary
  operator (`a maybe b`) choosing between its operands.
- How user RAM and the surface language exchange values with the system
  layer beyond MAYBE (measurement/encoding discipline).
- The causal marking rule: should firing in reverse mark (current,
  conservative choice)? Should repeated-alignment history deepen the
  criterion (prune only after k inert epochs)?
- Whether pruned cells should be *reclaimed* (loops shrink) rather than
  zeroed in place.
