# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

moop is a new programming language implemented in C23. Two influences anchor every design decision:

- **Naturalism** (Quorum, Andreas Stefik): syntax should read naturally and favor learnability; prefer design choices backed by evidence about how people read and write code.
- **Minimalism** (Io, Steve Dekorte): a tiny core with few concepts. Resist adding features, concepts, or implementation machinery — the whole language and its implementation should stay small enough to hold in your head.

When making language or implementation decisions, weigh them against both principles. If a change adds a concept, it needs to earn its place.

**We optimize for minimalism through synergy and orthogonality.** Every feature must compound with the rest of the design (synergy: reversibility × homoiconicity = causal closure; pruning × homoiconicity = GC and dead-code elimination as one operation) and own exactly one non-overlapping job (orthogonality: generation is who-made-you, inheritance is whom-you-defer-to, names are the only mutable handle). A feature that duplicates another's role, or that doesn't multiply the value of what's already there, doesn't get in.

**moop is a derived language** (`docs/derivation.md` — read it before proposing features). Constructs are derived from the axioms, never added by fiat, and they are *derived away* when a uniform rule covers them (`self` → headless chains; `generate` → the article). Apply the **deletion test** to every proposal: a construct is redundant iff a uniform contextual rule covers all its uses without creating silence (mistakes becoming actions) or ambiguity (one form, two meanings). A proposal must name what forces it, what it compounds with, and why the deletion test doesn't dissolve it. When an axiom and the implementation conflict, the implementation loses. Borrowings from Quorum/Io must be re-derivable in moop's own terms, not copied on authority.

## The computational core

The central primitive is a **CCNOT (Toffoli) gate connected to two counter-rotating circular Turing tape loops** (`src/tapeloop.{h,c}`, design notes in `docs/model.md`). Loop A rotates forward, loop B backward; each tick the gate fires symmetrically (controls = cells under both heads, driving two CCNOTs that target the next cell of *each* loop) and then the loops rotate.

**Reversibility and homoiconicity are the load-bearing invariants, and they work as a pair** (causal closure: the state alone determines future *and* past, and running backward recovers the program that produced any state — see `docs/model.md`).

- *Reversibility*: the two CCNOTs share controls and write distinct targets, so each tick is self-inverse before rotation; `moop_core_step_back()` must exactly undo `moop_core_step()` — `tests/test_core.c` enforces this with a full-cycle round-trip. Each loop needs ≥ 2 cells or its target aliases a control and reversibility breaks (asserted in `moop_core_init`).
- *Homoiconicity*: no loop may become a read-only "program tape" — both loops must remain writable by execution (the symmetric targets guarantee this; the tests assert both loops are transformed). Code and data are the same substrate by design.

Any change to the core (wiring, gate placement, tape encoding) must preserve both properties and keep those tests passing.

**Causal pruning is the one sanctioned exception.** Cells are marked into the causal web when they participate in an actual firing; `moop_core_prune()` zeroes unmarked (causally inert) cells — whose values are provably independent of the rest of the state — and `moop_core_run()` auto-prunes at each epoch boundary (`lcm(len_a, len_b)` ticks). Pruning is explicit, irreversible, and resets the causal epoch: the round-trip guarantee holds *between* prunes, never across them. Marks/ticks are heuristic metadata, not reversible state. Don't add any other information-losing path to the core.

The current gate wiring is **wiring 1**, frozen and pinned by `tests/tape_vectors.txt` (checked by `test_wiring_1_trace`), because Selvage's CCNOT tape (the prelude record `CcnotTape` and rules `tape_tick`, `draw`, `birth`) reimplements it and moop is its reference model (`docs/model.md`, `docs/comparisons/merge-plan.md`). The wiring may still iterate, but only as a new numbered wiring: keep wiring decisions confined to `src/tapeloop.c`, update `docs/model.md`, and regenerate the trace deliberately — never edit the trace to make a failing test pass. The trace also pins MAYBE's observation point and the seeding order of births.

## Two memories, two logics (segregation)

The machine has two memory systems and two operator layers, and the boundary between them is a hard rule:

- **System layer** — gate-based memory (the tape loops) operated on only by the reversible gates in `src/gates.{h,c}`: NOT, CNOT, CCNOT, SWAP. All self-inverse; never touch RAM from this layer.
- **User layer** — conventional byte-addressable RAM (`src/ram.{h,c}`) operated on by the irreversible logic in `src/logic.{h,c}`: AND, OR, NAND, NOR, XOR, MAYBE. These consume values and forget; never write system memory from this layer.
- **Bridging has exactly one sanctioned shape** — reversible effect inside, irreversible observation outside. MAYBE is the primitive bridge: it steps the reversible core once and observes the cell under loop A's head, deterministic given the same tapes. It is an observation, not randomness: on wiring 1 a draw agrees with the draw `len_a` back 74.8% of the time, and births inherit that correlation (measured in `docs/model.md`) — never describe or use MAYBE as a random source. **Actors** (`src/actor.{h,c}`) generalize that shape into the object model: an actor's body is a reversible core (so actors inherit reversibility and homoiconicity from the substrate, not from each other), and its surface is a table of hosted, irreversible, user-facing messages. Actors are non-hereditary — message lookup is strictly local, a miss never delegates, and `<-` has no meaning for them. Handlers may act on the body only via reversible operations and observation. Don't add cross-layer paths of any other shape without updating `docs/model.md` and the tests.

## Protos: generation vs. inheritance

The object ladder (`src/proto.{h,c}`): the system-facing actor generates the system-facing root proto → which generates user-facing root protos → which generate protos, all the way down. Two relations, kept strictly apart:

- **Generation** (who made you) is the only downward system→user path. It seeds the child's tapes via MAYBE draws from the generator's dynamics — deterministic, and reversible for the generator (tests assert the generator can step back to before the birth). Birth promises valid reversible initialization and nothing more (decided): diversity of children is a separate design objective, never a correctness condition on wiring 1 (`docs/model.md`). Every generated body is a core on the substrate, so all protos inherit reversibility and homoiconicity *by construction*.
- **Inheritance/delegation** (whom you defer to, `<-`) walks parent links among user-facing protos only; the original receiver stays the one addressed. It never crosses the layer boundary: user roots have no parent; nothing delegates into the system root or the actor.

Preserve both rules when extending the object model: generation may cross the boundary (in that one shape); delegation never does.

When adding operators, put them in the layer that matches their information behavior: if it loses information it cannot be a gate; if it's self-inverse it belongs in `gates.{h,c}` and must be covered by a self-inverse test in `tests/test_core.c`.

## Commands

```sh
make          # build the interpreter to build/moop
make test     # build, then run tests/run_tests.sh against build/moop
make clean    # remove build/
./build/moop            # start the REPL ("quit" exits)
./build/moop FILE       # run a file: a session without banner or prompts; stops at the first error (exit 1)
./build/moop --version  # print version
```

There is no separate lint step; the build uses `-Wall -Wextra -Wpedantic` and warnings should be treated as errors to fix.

## Toolchain notes

- The Makefile probes the compiler and uses `-std=c23` when supported, falling back to `-std=c2x` (GCC 13, the compiler in this environment, only knows `c2x`). Both mean C23; write C23 code.
- Error messages are formatted into buffers of `MOOP_ERR_MAX` bytes (256, in `src/parser.h`), raised from 128 in 0.8.0 so that no refusal is cut short. It is an implementation limit, not part of the language; keep new messages well under it.
- Tests come in two layers, both run by `make test`: `tests/test_core.c` (C unit tests linked against everything in `src/` except `main.c`, built to `build/test_core`) and `tests/run_tests.sh` (POSIX-sh smoke tests against the binaries, using the `check` expected-vs-actual helper). Add C tests for core semantics, `check` lines for CLI behavior, and programs under `tests/programs/` (run as files; `NAME.out` holds the expected output where it does not depend on the wiring) for behavior best shown by a whole program. `test_core` reads `tests/tape_vectors.txt` by relative path, so it runs from the repository root (as `make test` does).

## Structure and state

- `src/` — interpreter sources. All `.c` files in `src/` are compiled and linked into the single `moop` binary (`src/moop.h` holds the version constant). `src/tapeloop.{h,c}` is the computational core; `src/gates.{h,c}` the reversible operators; `src/logic.{h,c}` the irreversible operators; `src/ram.{h,c}` user-facing memory; `src/actor.{h,c}` the actor runtime; `src/proto.{h,c}` the generative proto hierarchy; `src/encode.{h,c}` the value-onto-tapes encoding; `src/lexer.{h,c}`, `src/parser.{h,c}`, `src/eval.{h,c}` the interpreter pipeline.
- `docs/model.md` — the core model's design rationale and open questions; keep it in sync with wiring changes.
- `docs/syntax.md` — surface syntax design notes and decisions.
- `docs/derivation.md` — the design methodology: moop as a derived language, the deletion test, and what a feature proposal must prove.
- `docs/foundations.md` — a draft for rulings (F1–F14), not decided or built: one reader policy (`;` comments, comment lines not read, blank line still closes), one value model (exact 64-bit rationals, `true`/`false`, text, one printing law, one `equals`), arithmetic as messages, and certified mirrors (`world celsius mirrors fahrenheit`, derived at each send). Do not implement from it before rulings and a separate authorization.
- `docs/arguments.md` — messages that take arguments: the design adopted on 2026-11-18 (Q1–Q5), the options weighed, and the implementation in 0.8.0 with its own validation.
- `docs/comparisons/` — comparisons with sibling languages, each import put through the deletion test (`selvage.md`: Selvage 0.4.9; `merge.md`: system-facing reversibility and a moop/Selvage merge, an exploration with its Selvage test programs in `experiments/`; `merge-plan.md`: the phased plan — decided: moop stays a separate language and is the reference model for Selvage's `CcnotTape`; moop's part, pinning wiring 1 to a shared trace, is done).
- `tests/` — see the test layers above; `tests/tape_vectors.txt` is the shared wiring-1 trace; `tests/programs/` holds moop programs run as files.

## Surface syntax and the interpreter pipeline

The pipeline is lex (`src/lexer.{h,c}`) → parse (`src/parser.{h,c}`) → eval (`src/eval.{h,c}`), driven line-by-line by the reader in `src/main.c`, which serves the REPL and a file alike (a file is a session without the banner and the prompts; it stops at its first error, named `FILE:LINE`, with exit status 1; `quit` is the REPL's command, not a word of the language). One grammar rule: `statement := chain ["is" [chain]]`, `chain := [term] ((-> | <- | <-> | WORD) term)*`, `term := ("a"|"an") term | WORD | NUMBER`, left-associative — `p ask q ask r` is a pipeline. A WORD in operator position is a message that takes something (below). A trailing `is` opens an indented block (pythonic whitespace): one chain per line, blank line closes, the body is a sequence whose last value answers; indentation is handled by the reader, never the parser. The reader refuses rather than guesses (decided 2026-11-18): an indented line under no open block, a line over 1,023 bytes, a NUL byte and unreadable input such as a directory are errors, never run as something else or split. Comments are not part of the language (open).

Four relational operators. **Words are canonical** (Quorum-like vocabulary; naturalism), arrows are exact lexer-level aliases of the same tokens: `ask` = `->`, `inherits` = `<-`, `mirrors` = `<->`; the words are reserved. The arrow shapes mirror the two-layer model — one-way arrows are irreversible (user layer), the two-way arrow is information-preserving and compiles to the gate layer. Each has exactly one job:

- `a` / `an` — **birth, with no creation word** (decided; there is no `generate`/`create`/`new`): the indefinite article births a new proto from a term, exactly as English separates identity from membership — `rex is dog` aliases, `rex is a dog` introduces a new proto generated from dog, bare `a dog` is an anonymous birth. One token for both spellings; article + non-proto is refused ("births come from protos"). Follows Quorum's own precedent (no `new`; declaration instantiates). Underneath it is still `moop_proto_generate` — the concept keeps its name in the model and C API.
- `->` message passing: `x -> maybe` observes x's reversible body, `x -> value` decodes it; other messages look up x's taught and hosted tables (delegating; the original receiver stays the one addressed).
- `<-` **lineage predicate** (decided, not open): parents are fixed at generation and `<-` cannot rewire them — it evaluates to true/false ("is this my birth parent?"). Immutable parents keep the delegation graph acyclic by construction; behavior changes are done by generating anew and rebinding names, never by re-parenting.
- `<->` bijection: gate-backed and implemented as **involutions** (applying the same `<->` twice is the identity — tested). `5 <-> box` XOR-deposits a value onto the body's loop A via NOTs (self-inverse; oversized values are refused, never truncated); `a <-> b` exchanges two bodies' A-tapes via SWAPs (marks travel with bits). Yields the (left) body so pipelines continue. The innate `value` message decodes loop A (bit i = cell i). The value encoding lives in `src/encode.{h,c}` — general invertible *functions* under `<->` are still open. Never add a `<->` form that isn't gate-backed or that can lose information.
- `is` asymmetric identity, two designator shapes: `name is chain` binds a name (right side evaluates now; names are the mutable user-layer handle, rebinding is fine); `receiver -> message is chain` teaches — the body is stored *unevaluated* as a chain and runs at each send, addressed to the receiver. Re-teaching replaces the chain; `maybe`/`value` are innate and refuse redefinition.

**No receiver keyword** (decided; `self`/`me` do not exist): a *headless chain* — one that begins with an operator, e.g. `ask maybe` — addresses the current receiver (grammar: `chain := [term] (op term)*`, the parser inserts a RECEIVER node). In a taught body that is the object that was asked, even for delegated sends; at the top level it is the world (a session, at the REPL or in a file, is a body whose receiver is `world`). Known limits: the receiver can't be the right operand of `inherits`, and under the adopted argument design a body can't send its own receiver a message that takes something — a limitation of that grammar, not a promised feature. A body *can* answer with its receiver through the identity idiom `mirrors 0` (deposits nothing, yields the receiver; regression-checked in both test layers) — an idiom of `mirrors`, not a receiver expression.

**Messages that take something** (adopted 2026-11-18, implemented in 0.8.0; `docs/arguments.md`): the message occupies the operator position — `box add 5` sends, `box add n is mirrors n` teaches and names the parameter; `ask` stays the send that gives nothing. Exactly one argument, evaluated before dispatch, strict arity; no optional, variadic or lazy arguments. `and`/`or`/`nand`/`nor`/`xor` are built-in messages on truth values: eager (the argument is evaluated before dispatch, so no short-circuit) and not reserved. Order is receiver, then argument, then dispatch, and what evaluating them did (a birth) stands even if dispatch refuses — tested, keep it. The parser refuses a second argument (`box add 5 6`, `box add 5 x`) but not a pipeline (`box add 5 x 7`), prototype B's `box ask add 5`, and `ask add n` in a body (the Q3 limitation). A parameter belongs to its own body, shadows an outer name there (ruled: parameter binding only, not body-local declarations), and is saved and restored with the receiver. Arity across inheritance (ruled): the nearest teaching in the receiver's lineage decides; a child may re-teach with a different arity, a mismatch is refused with no fallback to an ancestor's teaching, and the parent keeps its own — so a child is not substitutable for its parent in general (tested in `tests/programs/arity.moop`). Not authorized: `box ask add 5`, names local to a body, optional/variadic/lazy arguments; no further grammar expansion.

**Ubiquitous homoiconicity is layered** (decided): each layer keeps code as data in its own medium — system code on the tapes, user code (taught chains) in RAM. Nothing user-facing goes on the tapes, and no taught behavior may bypass the bridge shape. Dispatch order: innate → taught (delegating up the lineage) → C-hosted tables.

At startup the evaluator builds the world as the model prescribes: static actor → system root → user-facing root proto, bound to the name `world`. Values are numbers, booleans, and proto references. `<->` lexes before `<-` (longest match); stray characters are lex errors, never guessed at.

Current state: core, gates, logic, RAM, actors, protos, encoding, lexer, parser, and an evaluator with user-defined messages (single-line and indented-block bodies) and gate-backed bijections are implemented and tested — moop is a working prototype-based OOP language (article births, teaching, delegation, override, implicit receiver, late binding, word vocabulary, whitespace blocks, messages that take one argument, logic on truth values) whose `mirrors` compiles to real gates. Interpreter bodies use 8/13-cell loops (values 0..255). Not implemented (and honestly erroring): number↔number bijections (definable invertible functions), reflection (reading taught chains back as values), nested definitions inside blocks, comments. The REPL deliberately reports what it cannot do rather than pretending — keep that honesty: never stub behavior in a way that silently looks functional.

Update this file as the interpreter grows (e.g., when the lexer/parser/evaluator land, document the pipeline and where each stage lives).
