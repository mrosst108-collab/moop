# moop surface syntax

Design notes for the surface language. The pipeline is lex
(`src/lexer.{h,c}`) → parse (`src/parser.{h,c}`) → eval
(`src/eval.{h,c}`). `is`, `->`, and `<-` evaluate today (see status at
the end); `<->` does not, and says so.

Guiding principle: **minimalism through synergy and orthogonality** —
one grammar rule, four operators with one non-overlapping job each, and
every construct must compound with the machine model rather than sit
beside it.

## The four relational operators

| Operator | Reading | Symmetry | Layer |
|---|---|---|---|
| `->` | message passing | asymmetric | user (irreversible) |
| `<-` | inheritance | asymmetric | user (irreversible) |
| `<->` | bijection | symmetric | system (reversible) |
| `is` | identity | asymmetric | binding |

The operators wear their information behavior in their shape — this is the
two-layer model surfacing in the syntax:

- **`x -> y` (message passing).** Flow reads left to right: x is sent to y.
  Sending is consumption; the receiver is free to forget. Irreversible, so
  it belongs to the user layer.
- **`child <- parent` (inheritance — decided: a lineage predicate).**
  Parents are fixed at generation and can never be rewired; `<-` asks
  "is parent my birth parent?" and evaluates to true/false. Reads
  naturally as a statement of standing fact ("child inherits from
  parent"), and facts that can't silently stop being true are what
  naturalism wants. Immutable parents also make delegation cycles
  impossible by construction — no cycle-detection machinery to carry
  (minimalism). To change behavior, generate a fresh proto and rebind
  names; lineage is physics, names are the mutable handle.
- **`x <-> y` (bijection).** An information-preserving, invertible relation:
  each side is derivable from the other. This is the syntax's window onto
  the reversible core — a `<->` must compile down to gate-layer
  constructions (self-inverse, no information loss). The only symmetric
  operator, and the only one that can run backward.
- **`name is thing` (asymmetric identity).** Definitional naming, written as
  the natural word rather than a symbol (naturalism: `is` reads aloud).
  Asymmetric: the name becomes a way to reach the thing; the thing is not
  altered and does not refer back. `is` is identity, not equality-testing.
  Two designator shapes, one meaning ("the left now denotes the right"):
  - `name is chain` — the right side evaluates now; the name denotes the
    value.
  - `receiver -> message is chain` — teaching. The right side is NOT
    evaluated; it is stored as a chain and evaluated at each send, with
    `self` bound to the receiver (so delegated sends answer from the
    receiver's own body). Re-teaching replaces the chain. `generate` and
    `maybe` are innate and cannot be redefined — the interpreter says so.

## Ubiquitous homoiconicity (decided)

Homoiconicity holds everywhere, but each layer keeps its code in its own
medium — nothing user-facing lives on the tapes:

- **System layer**: code is data *on the loops* — every cell is
  simultaneously instruction (control) and data (target).
- **User layer**: code is data *in RAM* — a taught message body is the
  same chain structure the parser produced, stored and evaluated on
  send. Lisp-style homoiconicity in the user medium.

The layer discipline is untouched: the two homoiconicities never share a
substrate, and the bridge shape (reversible effect inside, observation
outside) remains the only crossing.

## Lexical rules

- Words: letters, digits, underscores; must start with a letter or
  underscore. `is` is the only keyword so far — matched exactly, so
  `island` stays a word.
- Numbers: decimal digit runs.
- `<->` is matched before `<-` (longest match).
- A bare `-`, `<`, or any other stray character is a lex error: the
  interpreter reports it rather than guessing.

## Evaluation status

Implemented: `name is chain` (binds; definitions are quiet), teaching
(`receiver -> message is chain`, deferred body, `self`, delegation,
override — moop is a working prototype-based OOP language), `x ->
generate` (births a proto), `x -> maybe` (observes the body), `child <-
parent` (lineage predicate), numbers, and the preopened `world`
(user-facing root proto, generated at startup through actor → system
root). Chains associate left: `a -> b -> c` is a pipeline. Dispatch
order: innate, then taught (walking the lineage), then C-hosted tables.

Not implemented, and honestly erroring: `<->` (the encoding problem),
running files, reflection (reading a taught chain back as a value).

## Decisions

- Chains associate left (pipelines read naturally).
- `<-` is a predicate; parents are birth-fixed (see above).
- Ubiquitous homoiconicity is layered: user code is data in RAM, system
  code is data on tapes; nothing user-facing on the tapes (see above).

## Open questions

- What `<->` binds at the value level: paired names, invertible function
  definitions, or literal tape-region aliasing — this is the encoding
  problem, the next major design step.
- Whether inheritance interacts with `<->` (bijective inheritance would be
  strange — flag if it ever seems tempting).
- Reflection: `is` stores chains as data, but the surface language
  cannot yet read one back (quote a chain, inspect a body, rewrite a
  teaching programmatically). The data is there; the mirror is missing.
- String and boolean literal forms; whether the logic operator words
  (and, or, nand, nor, xor) are keywords or ordinary messages.
