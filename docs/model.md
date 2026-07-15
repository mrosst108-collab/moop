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
- Gate target: the *next* cell on A (the one about to rotate under the gate),
  so each tick's output becomes a control on the following tick — that
  feedback is what makes the core compute rather than merely permute.
- Loop A must have at least 2 cells, or the target would alias a control and
  self-inverseness (hence reversibility) breaks.

Counter-rotation means the pair of aligned cells shifts by (+1, −1) each
tick: with coprime loop lengths, every cell of A meets every cell of B once
per `lcm(len_a, len_b)` ticks.

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
- **MAYBE is the sole sanctioned bridge.** `moop_maybe(core)` advances the
  reversible core one tick and observes the cell under loop A's head. It is
  deterministic and reproducible (same tapes → same answers), and its only
  effect on the system layer is a reversible step, so even the bridge loses
  no information. This is the initial design for MAYBE — an unpredictable-
  looking but replayable truth value, with the reversible substrate as the
  oracle — and is expected to iterate.

## Open questions

- Whether one gate suffices in practice or the core grows a ring of gates.
- How programs are encoded onto the loops, and how the surface language
  (natural, Quorum-like syntax) compiles down to initial tape states.
- Target placement: on A, on B, or alternating.
- MAYBE's final semantics: nullary oracle draw (current design), or a binary
  operator (`a maybe b`) choosing between its operands.
- How user RAM and the surface language exchange values with the system
  layer beyond MAYBE (measurement/encoding discipline).
- The causal marking rule: should firing in reverse mark (current,
  conservative choice)? Should repeated-alignment history deepen the
  criterion (prune only after k inert epochs)?
- Whether pruned cells should be *reclaimed* (loops shrink) rather than
  zeroed in place.
