# moop surface syntax

Design notes for the surface language. The pipeline is lex
(`src/lexer.{h,c}`) → parse (`src/parser.{h,c}`) → eval
(`src/eval.{h,c}`). Every construct below evaluates today (see status
at the end).

Guiding principle: **minimalism through synergy and orthogonality** —
one grammar rule, four operators with one non-overlapping job each, and
every construct must compound with the machine model rather than sit
beside it.

## The four relational operators

**Io-like grammar, Quorum-like vocabulary** (decided). The grammar is
Io's shape — everything is a chain of sends — with arrows as its
operators, and the arrows are canonical: their shapes wear the
information behavior that words cannot show. Quorum's vocabulary lives
in the words the language does use — `is`, `a`/`an`, message names —
and in pythonic whitespace instead of `end`. The words `ask`,
`inherits`, `mirrors` remain exact aliases (the lexer maps both
spellings to the same token: one semantics, two notations) for readers
who prefer words; they are reserved and cannot name values or messages.
Code always prints with arrows.

| Arrow | Word alias | Reading | Symmetry | Layer |
|---|---|---|---|---|
| `->` | `ask` | message passing | asymmetric | user (irreversible) |
| `<-` | `inherits` | declares inheritance | asymmetric | user (irreversible) |
| `<->` | `mirrors` | bijection | symmetric | system (reversible) |
| `is` | — | identity | asymmetric | binding |
| `a` / `an` | — | birth | prefix | generation (the bridge) |

`mirrors` earns its name: every bijection form is an involution, so
mirroring twice restores. The arrows wear the same information behavior
in their shape — the two-layer model surfacing in the syntax:

- **`x -> y` (message passing).** Flow reads left to right: x is sent to y.
  Sending is consumption; the receiver is free to forget. Irreversible, so
  it belongs to the user layer.
- **`child <- parent` (inheritance — decided: `<-` declares it).**
  The child now defers to the parent: messages it does not know are
  looked up on the parent and its lineage, still addressed to the
  child. A birth starts with its generator as parent (`rex is a dog`
  inherits from dog); `<-` declares or re-declares it. This keeps the
  two relations orthogonal — the article is who made you, `<-` is whom
  you defer to — and matches Io, where a proto's parent can be set.
  Answers the child, so pipelines continue: `cat <- dog -> bark`.
  Refused, with nothing changed: inheriting from yourself, a
  declaration that would close a loop (the parent already inherits
  from the child — so every lineage still ends and lookups terminate),
  and any declaration touching a system-facing proto (delegation never
  crosses the layer boundary). This supersedes the earlier decision
  that `<-` was a predicate over birth-fixed parents: acyclicity now
  comes from one refusal instead of from immutability.
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
    receiver's own body). Re-teaching replaces the chain. `maybe` and
    `value` are innate and cannot be redefined — the interpreter says so.

## Birth: the indefinite article (decided: no creation word)

There is no `generate`/`create`/`new`. Birth is grammar — the
indefinite article, used exactly as English uses it:

```
rex is dog       ; identity: rex names that very proto (an alias)
rex is a dog     ; membership: rex names a NEW proto generated from dog
a world          ; an anonymous birth
```

"Clark is Superman" versus "Clark is a reporter" — the article is how
English separates identity from instantiation, so `is` keeps one
meaning per *syntactic* form (no type-dependent behavior). This follows
Quorum's own precedent: Quorum has no `new`; declaration instantiates.
`a` and `an` are the same token — use whichever reads well. The article
applies to a single term; `a 5` is refused (births come from protos).
Underneath, a birth is still `moop_proto_generate`: tapes seeded from
the generator's reversible dynamics, deterministic, costing the
generator nothing irreversible.

## The receiver (decided: no keyword)

There is no `self`/`me` word. Every context has a **receiver**, and a
*headless chain* — one that begins with an operator — addresses it:

```
animal -> mood is
    -> maybe             ; an imperative, read "ask maybe", addressed
                         ; to whoever was asked for mood
```

Inside a taught body the receiver is the object that was asked (even
when the message was found on an ancestor). At the top level the
receiver is the world: the REPL session is itself a body whose receiver
is `world`, so `-> maybe` at the prompt observes the world's body.
English drops the subject of imperatives; moop does the same.

Known, accepted losses (revisit when messages take arguments): the
receiver cannot appear as the right operand of `<-` (so a body can make
its receiver inherit — `<- dog` — but cannot make something inherit from
it), and a body cannot answer with the receiver itself.

## Ubiquitous homoiconicity (decided)

Homoiconicity holds everywhere, but each layer keeps its code in its own
medium — nothing user-facing lives on the tapes:

- **System layer**: code is data *on the loops* — every cell is
  simultaneously instruction (control) and data (target).
- **User layer**: code is data *in RAM* — a taught message body is the
  same chain structure the parser produced, stored and evaluated on
  send, and reachable as a value through quotes (below). Lisp-style
  homoiconicity in the user medium.

The layer discipline is untouched: the two homoiconicities never share a
substrate, and the bridge shape (reversible effect inside, observation
outside) remains the only crossing. Reversibility is reserved for
system-facing code; user code is homoiconic and forgetful by design.

## Reflection: quotes mention code (decided)

Quotation marks mark *mention* instead of *use*, exactly as they do in
English. A quote is the quoted code itself, as a value:

```
plan is "-> maybe"               ; plan names the code, not its result
plan                             ; "-> maybe"
dog -> "mood"                    ; dog's code for mood (read)
dog -> "mood" is plan            ; teach mood from a code value (write)
cat -> "mood" is dog -> "mood"   ; copy a behavior
world -> "go" is plan            ; running code is teaching it...
-> go                            ; ...and asking
```

- **A quote is code.** `"…"` holds one statement — a chain, or even a
  definition — parsed when it is read, never evaluated. Code values bind
  to names, answer messages, and print in canonical spelling (arrows,
  `a`/`an` chosen by the next word), so printed code can be typed back
  in.
- **Nesting alternates the marks**, as English prose does: inside a
  quote the same mark closes and the other mark opens a deeper quote —
  `"rex -> mood is '-> maybe'"`. A quote that never closes is an
  error, never a guess.
- **A quoted message is mentioned, not sent.** In message position a
  quoted name designates the receiver's code for that message, found by
  the same lookup a send uses (innate, then taught up the lineage, then
  hosted). Innate and C-hosted messages have no moop code, and say so.
- **The quote moves across `is`.** `dog -> mood is -> maybe` and
  `dog -> "mood" is "-> maybe"` teach the same thing: with the
  unquoted designator the right side is written as code; with the quoted
  designator the right side evaluates now (like a name designator) and
  must be code. A block after a quoted designator evaluates now and its
  last value must be code.
- **Values never alias teachings.** Reading copies the code out;
  teaching copies it in. Re-teaching cannot change a code value someone
  already holds.
- Quoted definitions are code too, but installing one as a message body
  is refused — definitions cannot nest (yet), as in blocks.

Derivation. *Forced by* ubiquitous homoiconicity: user code was data in
RAM but unreachable as a value, so the user layer was homoiconic in
storage only. *Compounds with* `is` (the quote moving across `is` means
teaching needs no new form), delegation (reading follows the lineage
exactly like a send), headless chains (a quoted headless chain is
receiver-neutral code that addresses whoever it is taught to), and
names (code binds like any value). *Deletion test*: running code needs
no form of its own — teach it, then ask — so `eval` was derived away;
quoting and reading are not covered by any existing rule (teaching
mentions code only at definition time, and keeps it). *Naturalism*:
quotation marks are written English's sign for mention.

Costs, accepted: quotation marks now belong to code, so future string
literals need another form; and building code from pieces waits for
user-layer data operators and message arguments.

## Taking code apart: first and rest (decided)

Code is a sequence of parts. Every code value answers two innate
messages, the way every proto answers `maybe` and `value`: `first` is
its first part, and `rest` is the code that follows it.

```
plan is "dog -> mood <-> 5"
plan -> first                  ; "dog"
plan -> rest                   ; "-> mood <-> 5"
plan -> rest -> first          ; "-> mood"
plan -> rest -> rest           ; "<-> 5"
plan -> rest -> rest -> rest   ; "5"
```

| code | its parts |
|---|---|
| a block | its lines |
| a definition | what it defines, then what it is (`is` is the joint, as line breaks are in a block) |
| a chain | its head term, then its steps |
| a headless chain | its first step, then the remaining steps |
| one step | its operator, then its operand |
| a birth | its article, then the term it births from |
| a quote | its inside |

- **Every answer is code**: it prints, can be typed back in, and can be
  taught — `dog -> "m" is plan -> rest` installs a piece of plan.
  Taking apart plus teaching from code is editing by selection.
- **An operator or an article is a part but not code on its own**, so
  `first` refuses it and says so; the part stays visible in the printed
  step (`"<-> 5"`). A single word or number has no parts.
- Code answers only `first` and `rest`. The names are innate to code
  values only; protos can still be taught messages called `first` or
  `rest`.

Derivation. *Forced by* homoiconicity: code that can be held but not
examined is a value, not data. *Compounds with* headless chains — a
chain may begin with an operator, so whatever follows a chain's first
part is always well-formed code; that is what makes `rest` total — and
with quotation (parts print and re-enter) and teaching from code (parts
can be installed). *Deletion test*: no existing rule yields a part of
code. Two messages, no new syntax and no reserved words: code answers
innate messages through the same `ask` every proto does.

Not yet: assembling code from pieces. Joining two code values needs a
binary form or message arguments, and moop has neither for any kind of
data yet.

## Blocks (pythonic whitespace)

An `is` with nothing after it opens an indented block — the definition
body follows, one chain per line, closed by a blank line:

```
animal -> mood is
    -> maybe

treasure is
    a world
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
  underscore. Keywords (`is`, `ask`, `inherits`, `mirrors`, `a`, `an`)
  are matched exactly, so `island`, `asked`, and `answer` stay words.
- Numbers: decimal digit runs.
- `<->` is matched before `<-` (longest match).
- A bare `-`, `<`, or any other stray character is a lex error: the
  interpreter reports it rather than guessing.

## Evaluation status

Implemented: `name is chain` (binds; definitions are quiet), teaching
(`receiver -> message is chain`, deferred body, implicit receiver,
delegation, override — moop is a working prototype-based OOP language),
the article (`a dog` births), `x -> maybe` (observes the body), `child
<- parent` (declares inheritance), numbers, and the preopened `world`
(user-facing root proto, generated at startup through actor → system
root). Chains associate left: `p -> q -> r` is a pipeline. Dispatch
order: innate (`maybe`, `value`), then taught (walking the lineage),
then C-hosted tables.

`<->` is implemented for value↔body (XOR deposit) and body↔body
(exchange); `x -> value` decodes a body. Interpreter bodies carry 8-cell
A-loops: values 0..255.

Reflection is implemented: quotes are code values, `x -> "m"` reads
x's code for m, and `x -> "m" is code` teaches it (see above).

Not implemented, and honestly erroring: number↔number bijections
(general invertible functions — `celsius <-> fahrenheit` — remain the
open design work), running files, installing quoted definitions as
message bodies (definitions cannot nest yet).

## Decisions

- Io-like grammar, Quorum-like vocabulary: arrows are canonical (code
  prints with them), the words `ask`/`inherits`/`mirrors` are the same
  tokens, resolved in the lexer.
- Blocks are indentation-shaped: trailing `is` opens, blank line
  closes, bodies are sequences whose last value answers.
- Chains associate left (pipelines read naturally).
- `<-` declares inheritance; a birth starts with its generator as
  parent; loops and layer crossings are refused (see above).
- Ubiquitous homoiconicity is layered: user code is data in RAM, system
  code is data on tapes; nothing user-facing on the tapes (see above).
- No receiver keyword: headless chains address the receiver; the top
  level's receiver is the world (see above).
- No creation word: the indefinite article births; `is` + article
  introduces, `is` alone aliases (see above).
- Reflection by mention: quotes are code values; a quoted message reads
  or (with `is`) writes a receiver's code; running code is teaching it
  and asking (see above).
- Code is taken apart by `first` and `rest`, innate to code values; every
  part is code (see above).

## Open questions

- General invertible functions under `<->` (`celsius <-> fahrenheit`):
  the primitive involutions exist (deposit, exchange); composing them
  into definable bijections is the next design step.
- Whether inheritance interacts with `<->` (bijective inheritance would be
  strange — flag if it ever seems tempting).
- Assembling code from pieces (taking it apart exists). Waits for a
  binary form or message arguments; with it, general bijections could be
  inverted by reversing a chain of involutions.
- String and boolean literal forms (quotation marks now mean code);
  whether the logic operator words (and, or, nand, nor, xor) are
  keywords or ordinary messages.
