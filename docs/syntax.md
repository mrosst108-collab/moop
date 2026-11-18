# moop surface syntax

Design notes for the surface language. The pipeline is lex
(`src/lexer.{h,c}`) → parse (`src/parser.{h,c}`) → eval
(`src/eval.{h,c}`). `is`, `->`, `<-` and `<->` evaluate today (see
status at the end); what does not is listed there, and says so.

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
| `a` / `an` | — | birth | prefix | generation (the bridge) |

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
animal ask mood is
    ask maybe            ; an imperative: "ask maybe", addressed to
                         ; whoever was asked for mood
```

Inside a taught body the receiver is the object that was asked (even
when the message was found on an ancestor). At the top level the
receiver is the world: a session, at the REPL or in a file, is itself a
body whose receiver is `world`, so `ask maybe` at the prompt observes
the world's body. English drops the subject of imperatives; moop does
the same.

Known limits. The receiver cannot appear as the right operand of
`inherits`. Under the adopted design for messages that take something
(`arguments.md`), a body cannot send its own receiver such a message: a
limitation of that grammar, not a feature promised for later.

A body *can* answer with its receiver, by the existing identity idiom
`mirrors 0` (retained 2026-11-18): depositing 0 changes nothing, and
`mirrors` yields its left side, here the receiver. An earlier entry here
said a body could not; it was inaccurate. The idiom belongs to
`mirrors`; it is not a general way to name the receiver.

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
    a world
    42
```

A body is a *sequence*: chains evaluate in order and the last value
answers. Teaching designators store the sequence (deferred, receiver-
bound at each send); name designators evaluate it now and bind the last
value. Unindented body lines, empty bodies, and nested definitions are
refused with plain errors. The parser stays line-shaped — indentation
is handled entirely by the reader.

Indentation says a line belongs to a block, so **an indented line under
no open block is refused**: *an indented line belongs to a block, and
none is open*. It is not run as if it were flush left. A body therefore
cannot hold a blank line: the blank line closes it, and an indented line
after it is refused, not run as a statement of its own. (Decided
2026-11-18, for the REPL and files alike: the REPL's prompt does not
justify a different rule.)

## Running a file

`./build/moop FILE` runs a file. **A file is a session without the
banner and the prompts**: one reader (`src/main.c`) serves the REPL and
a file, the same lines mean the same thing in both, and a statement that
is not a definition prints its value. Nothing was added to the language
for it — there is no output word. The end of the file closes an open
block, as a blank line does.

They differ in two places only:

| | REPL | File |
|---|---|---|
| An error | Reported; the session goes on | Reported as `FILE:LINE: error: …`; the run stops there, and the exit status is 1 |
| `quit` | The REPL's command: it ends the session | Not a word of the language: a name like any other, unknown unless bound |

An error found when a block is evaluated names the body line that
failed. A message that fails while a taught chain runs is reported at
the statement that sent it, not where the chain was taught.

**Reader constraints** (decided 2026-11-18). The reader refuses these,
in both, so that a mistake never runs as something else; none is
tolerated silently or split into several statements:

- a line longer than 1,023 bytes (*line too long*): it is refused whole,
  never split into two statements;
- a line holding a NUL byte;
- an indented line under no open block (above);
- input that cannot be read, such as a directory: it is an error, not
  an empty file.

LF and CRLF both end a line. A carriage return anywhere else is a stray
byte, and a byte that does not print is named by its code (*unexpected
byte 0xC3*), so the message stays readable. Source is ASCII: no word or
number is written with any other byte.

## Messages that take something (0.8.0)

Ruled 2026-11-18 (`arguments.md`, Q1–Q5) and implemented in 0.8.0. A
word in operator position is a message that takes something, as
`inherits` and `mirrors` take their right side:

```
box add n is mirrors n      ; teaching: add takes something, called n
box add 5                   ; sending: add, given 5
box add 5 tag 7             ; a pipeline: what box add 5 answers is sent tag with 7
t and f                     ; and, or, nand, nor, xor on truth values
```

Grammar: `chain := [term] ((-> | <- | <-> | WORD) term)*`. `ask` stays
the send that gives nothing, so every chain parses without knowing any
teaching. A chain that begins with a word is headed by that name; only
`ask`, `inherits` and `mirrors` begin a headless chain.

- **Exactly one argument**, the term after the message. A second cannot
  be written: `box add 5 6` and `box add 5 x` are refused when the line
  is read (*add takes one argument, and '6' would be a second*). A word
  followed by a term is a pipeline step, so `box add 5 x 7` is valid.
- **Evaluated before dispatch**, receiver first, then the argument, then
  the message is looked up. Whatever evaluating them did stands, even if
  dispatch then refuses: `f and a w` births from `w` before `and`
  refuses the proto (*and relates two truths*).
- **Strict arity.** The teaching decides whether a message takes
  something. `box ask add`, when `add` takes something, and `box size 5`,
  when `size` takes nothing, are refused with the form to write. `maybe`
  and `value` take nothing. Re-teaching replaces a teaching, whatever it
  takes.
- **Arity across inheritance** (ruled 2026-11-18): the nearest teaching
  in the receiver's lineage decides. A child may re-teach a message with
  a different arity; a send to it must then satisfy the child's
  teaching, a mismatch is refused with no fallback to an ancestor's, the
  parent keeps its own, and descendants inherit the nearest one. So a
  child can change the calling contract of an inherited message: it is
  not substitutable for its parent in general.
- **The parameter** is named by the teaching (`box add n is …`). It is
  that body's own: no other body sees it, a name bound outside is
  shadowed inside the body and unchanged after it (ruled 2026-11-18),
  and it is never rebound. This is parameter binding only, not
  body-local declarations or a mutable lexical environment.
- **The logic words** `and`, `or`, `nand`, `nor`, `xor` are built-in
  messages on truth values, calling the user layer's logic
  (`src/logic.c`). They are eager: the right side is always evaluated, so
  nothing short-circuits. They are not reserved: a name or a proto's own
  message may use the word.
- **A limitation of this grammar:** a body cannot send its own receiver a
  message that takes something. `ask add n` is refused (*ask sends a
  message that takes nothing, and a body cannot give its own receiver
  something*). It is not a feature promised for later.

## Lexical rules

- Words: letters, digits, underscores; must start with a letter or
  underscore. Keywords (`is`, `ask`, `inherits`, `mirrors`, `a`, `an`)
  are matched exactly, so `island`, `asked`, and `answer` stay words.
  The logic words are not keywords.
- Numbers: decimal digit runs.
- `<->` is matched before `<-` (longest match).
- A bare `-`, `<`, or any other stray character is a lex error: the
  interpreter reports it rather than guessing.

## Evaluation status

Implemented: `name is chain` (binds; definitions are quiet), teaching
(`receiver -> message is chain`, deferred body, implicit receiver,
delegation, override — moop is a working prototype-based OOP language),
the article (`a dog` births), `x -> maybe` (observes the body), `child
<- parent` (lineage predicate), numbers, and the preopened `world`
(user-facing root proto, generated at startup through actor → system
root). Chains associate left: `p -> q -> r` is a pipeline. Dispatch
order: innate (`maybe`, `value`), then taught (walking the lineage),
then C-hosted tables. Messages that take something (0.8.0, above):
`box add 5`, `box add n is …`, and the logic words on truth values.

`<->` is implemented for value↔body (XOR deposit) and body↔body
(exchange); `x -> value` decodes a body. Interpreter bodies carry 8-cell
A-loops: values 0..255.

Not implemented, and honestly erroring: number↔number bijections
(general invertible functions — `celsius <-> fahrenheit` — remain the
open design work), reflection (reading a taught chain back as a value),
comments (a file cannot carry one).

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
- No creation word: the indefinite article births; `is` + article
  introduces, `is` alone aliases (see above).
- Files (0.7.0, 2026-11-18): a file is a session without the banner and
  the prompts; it stops at its first error, named `FILE:LINE`, with exit
  status 1; `quit` is the REPL's command, not a word of the language.
- An indented line under no open block is refused, at the REPL and in a
  file (2026-11-18).
- Reader constraints: a line over 1,023 bytes, a NUL byte, and input
  that cannot be read (such as a directory) are refused, never tolerated
  or split (2026-11-18).
- Messages that take something (ruled 2026-11-18; implemented in 0.8.0;
  `arguments.md`): `box add 5` sends, `box add n is mirrors n` teaches
  and names the parameter; exactly one argument, evaluated before
  dispatch, strict arity; a body cannot send its receiver such a message;
  `and`, `or`, `nand`, `nor`, `xor` are built-in, eager messages on truth
  values, not reserved words.
- `mirrors 0` is the identity idiom: it answers with the receiver and
  changes nothing (2026-11-18).

## Open questions

The items below that concern comments, blank lines in bodies, literals,
arithmetic and invertible functions are treated together in
`foundations.md`, ratified on 2026-11-18. Nothing there is built yet;
building it is authorized stage by stage.

- General invertible functions under `<->` (`celsius <-> fahrenheit`):
  the primitive involutions exist (deposit, exchange); composing them
  into definable bijections is the next design step.
- Whether inheritance interacts with `<->` (bijective inheritance would be
  strange — flag if it ever seems tempting).
- Reflection: `is` stores chains as data, but the surface language
  cannot yet read one back (quote a chain, inspect a body, rewrite a
  teaching programmatically). The data is there; the mirror is missing.
- String and boolean literal forms. (Whether the logic words are
  keywords is settled: built-in messages, not reserved; `arguments.md`.)
- **Comments.** A file cannot carry one, so a program cannot explain
  itself. Not built: a comment is a lexical construct and needs its
  derivation like any other (what forces it is that files are read by
  people; the open part is its form, and whether anything already
  present can carry the job).
- Whether a body may hold blank lines (a block closed by the first line
  that is not indented, as in Python). Decided otherwise for now — a
  blank line closes — and files make the cost visible: a long body
  cannot be spaced out.
