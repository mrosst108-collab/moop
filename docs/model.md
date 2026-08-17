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
per `lcm(len_a, len_b)` ticks. Coprimality is asserted at init, not merely
recommended: loop lengths select semantics, not just capacity. With a
shared factor, the pairings split into `gcd(len_a, len_b)` alignment
classes that never meet — a cell could then be pruned not because it is
causally dead but because the geometry can never consult its would-be
partners, and "one epoch = every pairing consulted once" (which the prune
semantics lean on below) would silently stop holding. A non-coprime core
is a different machine; we refuse it rather than select it by accident.

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
  them — and `moop_core_step_back()` asserts `ticks > 0`, so walking back
  into a pruned past fails loudly instead of inverting wrongly. A prune
  resets marks and starts a fresh epoch, so causal status must be
  re-earned each epoch.

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

### The chart is not the state

Four things get loosely called "the state of a body", and the rules
above are already keeping them apart. Naming them stops the confusion
from coming back:

- **Configuration space** — every assignment of bits to the two loops,
  times the head alignment: for an interpreter body (8/13) that is
  2^21 x 104 = 218,103,808 configurations. What *could* be on the tapes.
- **Orbit** — the configurations actually reached from a given birth
  state. The wiring is a bijection, so an orbit is a cycle, and which
  cycle a body is on is fixed at birth.
- **Wiring** — `moop_core_step`: the law, not its solutions. Every
  body runs the same law on different tapes.
- **Chart** — the value encoding above: bit i of a value is cell i of
  loop A. A reading of a configuration, not the configuration.

None of the four hands you the next one:

- *Configuration space does not give the orbit.* Measured on an 8/13
  body: from an all-ones birth the orbit is 8,020,272 configurations
  (3.7% of the space); from an all-zero birth it is 104 — bare rotation,
  because a loop with no set cell never supplies a control. Same
  geometry, five orders of magnitude apart. This is the coprimality
  assert seen from the other side: lengths are the ambient geometry and
  say nothing about what is reachable.
- *An orbit does not give the wiring.* Solutions do not identify the law
  that produced them; only `src/tapeloop.c` does.
- *The chart does not give the state.* `value` reads 8 of the 21 cells
  and none of loop B, so two bodies can agree on every coordinate and
  still be different machines: deposit 37 in each, set one cell of one
  body's loop B, and their `maybe` observations diverge within an
  alignment cycle while one body's reading never moves at all
  (`tests/test_core.c`). Equal readings, unequal bodies.

The practical ruling: `x -> value` answers what loop A currently reads,
never what x *is*. `<->` writes through the chart and its consequences
are not confined to it — a deposit also marks cells causal and changes
which cells later fire. Nothing may treat a chart reading as an identity
(no comparing bodies by decoding them), and nothing may promote the
geometry of the loops into a claim about a body's dynamics.

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
