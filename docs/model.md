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

## Open questions

- Whether one gate suffices in practice or the core grows a ring of gates.
- How programs are encoded onto the loops, and how the surface language
  (natural, Quorum-like syntax) compiles down to initial tape states.
- Target placement: on A, on B, or alternating.
