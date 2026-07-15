# The moop computational core

The central primitive of moop is a single **CCNOT (Toffoli) gate** connected
to two **counter-rotating circular Turing tapes** ("loops").

- CCNOT — `target ^= (control1 AND control2)` — is reversible and universal
  for classical computation.
- Tape rotation is a permutation of cell positions.

Because every tick is a reversible gate followed by a permutation, the whole
machine is reversible: the core can run backward, exactly. This is the
load-bearing invariant of the runtime.

## Wiring (initial design, expected to iterate)

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

## Open questions

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
