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
