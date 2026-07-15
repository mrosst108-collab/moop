# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

moop is a new programming language implemented in C23. Two influences anchor every design decision:

- **Naturalism** (Quorum, Andreas Stefik): syntax should read naturally and favor learnability; prefer design choices backed by evidence about how people read and write code.
- **Minimalism** (Io, Steve Dekorte): a tiny core with few concepts. Resist adding features, concepts, or implementation machinery — the whole language and its implementation should stay small enough to hold in your head.

When making language or implementation decisions, weigh them against both principles. If a change adds a concept, it needs to earn its place.

## The computational core

The central primitive is a **CCNOT (Toffoli) gate connected to two counter-rotating circular Turing tape loops** (`src/tapeloop.{h,c}`, design notes in `docs/model.md`). Loop A rotates forward, loop B backward; each tick the gate fires symmetrically (controls = cells under both heads, driving two CCNOTs that target the next cell of *each* loop) and then the loops rotate.

**Reversibility and homoiconicity are the load-bearing invariants, and they work as a pair** (causal closure: the state alone determines future *and* past, and running backward recovers the program that produced any state — see `docs/model.md`).

- *Reversibility*: the two CCNOTs share controls and write distinct targets, so each tick is self-inverse before rotation; `moop_core_step_back()` must exactly undo `moop_core_step()` — `tests/test_core.c` enforces this with a full-cycle round-trip. Each loop needs ≥ 2 cells or its target aliases a control and reversibility breaks (asserted in `moop_core_init`).
- *Homoiconicity*: no loop may become a read-only "program tape" — both loops must remain writable by execution (the symmetric targets guarantee this; the tests assert both loops are transformed). Code and data are the same substrate by design.

Any change to the core (wiring, gate placement, tape encoding) must preserve both properties and keep those tests passing.

**Causal pruning is the one sanctioned exception.** Cells are marked into the causal web when they participate in an actual firing; `moop_core_prune()` zeroes unmarked (causally inert) cells — whose values are provably independent of the rest of the state — and `moop_core_run()` auto-prunes at each epoch boundary (`lcm(len_a, len_b)` ticks). Pruning is explicit, irreversible, and resets the causal epoch: the round-trip guarantee holds *between* prunes, never across them. Marks/ticks are heuristic metadata, not reversible state. Don't add any other information-losing path to the core.

The gate wiring is an initial design and expected to iterate — keep wiring decisions confined to `src/tapeloop.c` and update `docs/model.md` when they change.

## Two memories, two logics (segregation)

The machine has two memory systems and two operator layers, and the boundary between them is a hard rule:

- **System layer** — gate-based memory (the tape loops) operated on only by the reversible gates in `src/gates.{h,c}`: NOT, CNOT, CCNOT, SWAP. All self-inverse; never touch RAM from this layer.
- **User layer** — conventional byte-addressable RAM (`src/ram.{h,c}`) operated on by the irreversible logic in `src/logic.{h,c}`: AND, OR, NAND, NOR, XOR, MAYBE. These consume values and forget; never write system memory from this layer.
- **Bridging has exactly one sanctioned shape** — reversible effect inside, irreversible observation outside. MAYBE is the primitive bridge: it steps the reversible core once and observes the cell under loop A's head, deterministic given the same tapes. **Actors** (`src/actor.{h,c}`) generalize that shape into the object model: an actor's body is a reversible core (so actors inherit reversibility and homoiconicity from the substrate, not from each other), and its surface is a table of hosted, irreversible, user-facing messages. Actors are non-hereditary — message lookup is strictly local, a miss never delegates, and `<-` has no meaning for them. Handlers may act on the body only via reversible operations and observation. Don't add cross-layer paths of any other shape without updating `docs/model.md` and the tests.

When adding operators, put them in the layer that matches their information behavior: if it loses information it cannot be a gate; if it's self-inverse it belongs in `gates.{h,c}` and must be covered by a self-inverse test in `tests/test_core.c`.

## Commands

```sh
make          # build the interpreter to build/moop
make test     # build, then run tests/run_tests.sh against build/moop
make clean    # remove build/
./build/moop            # start the REPL ("quit" exits)
./build/moop --version  # print version
```

There is no separate lint step; the build uses `-Wall -Wextra -Wpedantic` and warnings should be treated as errors to fix.

## Toolchain notes

- The Makefile probes the compiler and uses `-std=c23` when supported, falling back to `-std=c2x` (GCC 13, the compiler in this environment, only knows `c2x`). Both mean C23; write C23 code.
- Tests come in two layers, both run by `make test`: `tests/test_core.c` (C unit tests linked against everything in `src/` except `main.c`, built to `build/test_core`) and `tests/run_tests.sh` (POSIX-sh smoke tests against the binaries, using the `check` expected-vs-actual helper). Add C tests for core semantics, `check` lines for CLI behavior.

## Structure and state

- `src/` — interpreter sources. All `.c` files in `src/` are compiled and linked into the single `moop` binary (`src/moop.h` holds the version constant). `src/tapeloop.{h,c}` is the computational core; `src/gates.{h,c}` the reversible operators; `src/logic.{h,c}` the irreversible operators; `src/ram.{h,c}` user-facing memory; `src/actor.{h,c}` the actor runtime; `src/lexer.{h,c}` the surface-syntax lexer.
- `docs/model.md` — the core model's design rationale and open questions; keep it in sync with wiring changes.
- `docs/syntax.md` — surface syntax design notes; semantics documented there are intent until the evaluator exists.
- `tests/` — see the test layers above.

## Surface syntax (lexer stage)

Four relational operators, whose shapes mirror the two-layer model — one-way arrows are irreversible (user layer), the two-way arrow is information-preserving and must eventually compile to the gate layer:

- `->` message passing (asymmetric), `<-` inheritance (asymmetric), `<->` bijection (symmetric, reversible), `is` asymmetric identity (naming; the only keyword — matched exactly, `island` stays a word). `<->` lexes before `<-` (longest match); stray characters are lex errors, never guessed at.

Current state: the reversible tape-loop core, the actor runtime, and the lexer are implemented and tested. `src/main.c` is a REPL (`--version`, "quit") that lexes input for real and reports lex errors; the parser, evaluator, and compilation of surface syntax onto tape states are not implemented — the REPL deliberately reports "evaluation is not implemented yet" rather than pretending to work. Keep that honesty: never stub behavior in a way that silently looks functional.

Update this file as the interpreter grows (e.g., when the lexer/parser/evaluator land, document the pipeline and where each stage lives).
