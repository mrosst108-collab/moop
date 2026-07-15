# moop

moop is a new programming language. Its implementation is written in C23.

Two influences guide its design:

- **Naturalism**, in the spirit of Quorum (Andreas Stefik): syntax that reads
  naturally and favors learnability, with design choices grounded in evidence
  about how people actually read and write code.
- **Minimalism**, in the spirit of Io (Steve Dekorte): a tiny core with few
  concepts, kept simple enough to hold in your head — implementation included.

## The core model

moop's central primitive is a **CCNOT (Toffoli) gate connected to two
counter-rotating circular Turing tapes**. The tapes are reversible *and*
homoiconic, and the pair is synergistic: the gate fires symmetrically into
both loops, so there is no designated program tape — code rewrites code —
while every tick remains exactly invertible. The system is causally closed:
running any state backward recovers the program that produced it.

The loops auto-prune: cells that stay causally unrelated to the rest of the
state through a full alignment cycle are discarded at the epoch boundary —
the machine's single, explicit act of forgetting.

Around that core sit two segregated memory systems with matching operator
layers: gate-based system memory driven by reversible operators (NOT, CNOT,
CCNOT, SWAP), and conventional user-facing RAM driven by irreversible ones
(AND, OR, NAND, NOR, XOR, MAYBE). MAYBE is the one bridge between the
layers: an unpredictable-looking but replayable truth value drawn from the
reversible core. See [docs/model.md](docs/model.md) for the wiring and open
design questions.

## Building

```sh
make        # builds build/moop
make test   # runs the smoke tests
make clean
```

Requires a C compiler with C23 support (`-std=c23`, or `-std=c2x` on older
compilers such as GCC 13 — the Makefile detects which one to use).

## Status

Early days: the reversible tape-loop core (`src/tapeloop.c`) and the lexer
are implemented and tested. The surface language has four relational
operators — `->` message passing, `<-` inheritance, `<->` bijection, `is`
asymmetric identity (see [docs/syntax.md](docs/syntax.md)) — whose shapes
mirror the machine: one-way arrows forget, the two-way arrow is reversible.
The parser, evaluator, and the compilation of surface syntax onto the loops
do not exist yet.
