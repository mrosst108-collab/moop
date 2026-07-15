# moop surface syntax

Design notes for the surface language. The lexer (`src/lexer.{h,c}`)
recognizes these forms; parsing and evaluation are not yet implemented, so
everything below the token level is design intent, not behavior.

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
- **`child <- parent` (inheritance).** The child draws from the parent;
  reads naturally as "child from parent". Asymmetric — the parent does not
  know its children. Io-style prototype lineage rather than class
  hierarchy is the working assumption.
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

## Open questions

- Precedence and grouping among the four operators; whether chains like
  `a -> b -> c` associate left (pipeline) — likely, it reads naturally.
- What `<->` binds at the value level: paired names, invertible function
  definitions, or literal tape-region aliasing.
- Whether inheritance interacts with `<->` (bijective inheritance would be
  strange — flag if it ever seems tempting).
- `<-` applies to user-layer values only: actors are non-hereditary, so
  `actor <- anything` should be rejected by the evaluator when it exists.
- String and boolean literal forms; whether the logic operator words
  (and, or, nand, nor, xor, maybe) are keywords or ordinary messages.
