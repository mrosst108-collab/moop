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

## Lexical rules

- Words: letters, digits, underscores; must start with a letter or
  underscore. `is` is the only keyword so far — matched exactly, so
  `island` stays a word.
- Numbers: decimal digit runs.
- `<->` is matched before `<-` (longest match).
- A bare `-`, `<`, or any other stray character is a lex error: the
  interpreter reports it rather than guessing.

## Evaluation status

Implemented: `name is chain` (binds; definitions are quiet), `x ->
generate` (births a proto), `x -> maybe` (observes the body), other
messages via delegating lookup of hosted tables, `child <- parent`
(lineage predicate), numbers, and the preopened `world` (user-facing
root proto, generated at startup through actor → system root). Chains
associate left: `a -> b -> c` is a pipeline.

Not implemented, and honestly erroring: `<->` (the encoding problem),
running files, hosting user-defined messages from the surface language.

## Decisions

- Chains associate left (pipelines read naturally).
- `<-` is a predicate; parents are birth-fixed (see above).

## Open questions

- What `<->` binds at the value level: paired names, invertible function
  definitions, or literal tape-region aliasing — this is the encoding
  problem, the next major design step.
- Whether inheritance interacts with `<->` (bijective inheritance would be
  strange — flag if it ever seems tempting).
- How the surface language hosts user-defined messages (the syntax for
  defining behavior, not just wiring values).
- String and boolean literal forms; whether the logic operator words
  (and, or, nand, nor, xor) are keywords or ordinary messages.
