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

Words are the canonical spellings (Quorum's evidence: words read better
than symbols, especially for newcomers); the arrows are exact aliases —
the lexer maps both to the same token, so there is one semantics with
two notations. The words are reserved and cannot name values or
messages.

| Word | Arrow | Reading | Symmetry | Layer |
|---|---|---|---|---|
| `ask` | `->` | message passing | asymmetric | user (irreversible) |
| `inherits` | `<-` | lineage predicate | asymmetric | user (irreversible) |
| `mirrors` | `<->` | bijection | symmetric | system (reversible) |
| `is` | — | identity | asymmetric | binding |

`mirrors` earns its name: every bijection form is an involution, so
mirroring twice restores. The arrows wear the same information behavior
in their shape — the two-layer model surfacing in the syntax:

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
- **`x <-> y` (bijection).** An information-preserving, invertible relation,
  compiled to gate-layer constructions — the syntax's window onto the
  reversible core. Every implemented form is an **involution**: applying
  the same `<->` twice is the identity, so "bijective" is a tested fact.
  - `5 <-> box` (value ↔ body): XOR-encodes the number onto the body's
    loop A via gate-layer NOTs. Self-inverse — depositing and erasing are
    the same act. Values that don't fit are refused, never truncated
    (truncation would make `<->` lossy — the one thing it must never be).
  - `a <-> b` (body ↔ body): exchanges the two bodies' A-tapes via
    gate-layer SWAPs; causal marks travel with their bits.
  - Yields the (left) body, so pipelines continue: `5 <-> box -> value`.
  - The innate message `value` decodes loop A as binary (bit i = cell i):
    pure observation, the bridge shape with zero effect.
- **`name is thing` (asymmetric identity).** Definitional naming, written as
  the natural word rather than a symbol (naturalism: `is` reads aloud).
  Asymmetric: the name becomes a way to reach the thing; the thing is not
  altered and does not refer back. `is` is identity, not equality-testing.
  Two designator shapes, one meaning ("the left now denotes the right"):
  - `name is chain` — the right side evaluates now; the name denotes the
    value.
  - `receiver -> message is chain` — teaching. The right side is NOT
    evaluated; it is stored as a chain and evaluated at each send,
    addressed to the receiver (so delegated sends answer from the
    receiver's own body). Re-teaching replaces the chain. `generate` and
    `maybe` are innate and cannot be redefined — the interpreter says so.

## The receiver (decided: no keyword)

There is no `self`/`me` word. Every context has a **receiver**, and a
*headless chain* — one that begins with an operator — addresses it:

```
animal ask mood is
    ask maybe            ; an imperative: "ask maybe", addressed to
                         ; whoever was asked for mood
```

Inside a taught body the receiver is the object that was asked (even
when the message was found on an ancestor). At the top level the
receiver is the world: the REPL session is itself a body whose receiver
is `world`, so `ask generate` at the prompt births a proto from the
world. English drops the subject of imperatives; moop does the same.

Known, accepted losses (revisit when messages take arguments): the
receiver cannot appear as the right operand of `inherits`, and a body
cannot answer with the receiver itself.

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

## Blocks (pythonic whitespace)

An `is` with nothing after it opens an indented block — the definition
body follows, one chain per line, closed by a blank line:

```
animal ask mood is
    ask maybe

treasure is
    world ask generate
    42
```

A body is a *sequence*: chains evaluate in order and the last value
answers. Teaching designators store the sequence (deferred, receiver-
bound at each send); name designators evaluate it now and bind the last
value. Unindented body lines, empty bodies, and nested definitions are
refused with plain errors. The parser stays line-shaped — indentation
is handled entirely by the reader.

## Lexical rules

- Words: letters, digits, underscores; must start with a letter or
  underscore. Keywords (`is`, `ask`, `inherits`, `mirrors`) are matched
  exactly, so `island` and `asked` stay words.
- Numbers: decimal digit runs.
- `<->` is matched before `<-` (longest match).
- A bare `-`, `<`, or any other stray character is a lex error: the
  interpreter reports it rather than guessing.

## Evaluation status

Implemented: `name is chain` (binds; definitions are quiet), teaching
(`receiver -> message is chain`, deferred body, implicit receiver, delegation,
override — moop is a working prototype-based OOP language), `x ->
generate` (births a proto), `x -> maybe` (observes the body), `child <-
parent` (lineage predicate), numbers, and the preopened `world`
(user-facing root proto, generated at startup through actor → system
root). Chains associate left: `a -> b -> c` is a pipeline. Dispatch
order: innate, then taught (walking the lineage), then C-hosted tables.

`<->` is implemented for value↔body (XOR deposit) and body↔body
(exchange); `x -> value` decodes a body. Interpreter bodies carry 8-cell
A-loops: values 0..255.

Not implemented, and honestly erroring: number↔number bijections
(general invertible functions — `celsius <-> fahrenheit` — remain the
open design work), running files, reflection (reading a taught chain
back as a value).

## Decisions

- Words are canonical, arrows are aliases: `ask`/`inherits`/`mirrors`
  are the same tokens as `->`/`<-`/`<->`, resolved in the lexer.
- Blocks are indentation-shaped: trailing `is` opens, blank line
  closes, bodies are sequences whose last value answers.
- Chains associate left (pipelines read naturally).
- `<-` is a predicate; parents are birth-fixed (see above).
- Ubiquitous homoiconicity is layered: user code is data in RAM, system
  code is data on tapes; nothing user-facing on the tapes (see above).
- No receiver keyword: headless chains address the receiver; the top
  level's receiver is the world (see above).

## Open questions

- General invertible functions under `<->` (`celsius <-> fahrenheit`):
  the primitive involutions exist (deposit, exchange); composing them
  into definable bijections is the next design step.
- Whether inheritance interacts with `<->` (bijective inheritance would be
  strange — flag if it ever seems tempting).
- Reflection: `is` stores chains as data, but the surface language
  cannot yet read one back (quote a chain, inspect a body, rewrite a
  teaching programmatically). The data is there; the mirror is missing.
- String and boolean literal forms; whether the logic operator words
  (and, or, nand, nor, xor) are keywords or ordinary messages.
