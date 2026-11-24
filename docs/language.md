# The moop language (version 0.10.0)

This describes moop as it stands in 0.10.0, for someone who wants to
read or write it. The reasons behind each decision are in `syntax.md`,
`arguments.md` and `foundations.md`. The machine underneath is in
`model.md`. The method that admits or removes a feature is in
`derivation.md`. Every example below was run, and shows its actual
output. In the examples, `→` marks what a line prints; it is not part of
the program.

## What moop is

moop is a small prototype-based language built on a reversible machine.
Two influences shape it:

- **Naturalism** (Quorum): code should read like what it means. moop
  uses words before symbols, and English grammar where English already
  draws the distinction.
- **Minimalism** (Io): a few concepts, each with exactly one job,
  small enough to hold in your head.

moop is a *derived* language. A construct exists only if the design's
axioms force it, and it is removed again when a uniform rule covers its
uses. `self` and `generate` both went that way.

```
; A first program: protos, teaching, delegation
animal is a world
animal ask legs is 4
animal speak n is n
cat is an animal
cat ask legs                 → 4
cat speak 7                  → 7
cat inherits animal          → true
animal inherits cat          → false
```

## Running moop

```sh
make                       # builds build/moop
./build/moop               # the REPL; "quit" leaves
./build/moop program.moop  # runs a file
make test                  # the test suites
```

**A file is a REPL session without the banner and the prompts.** Every
statement that is not a definition prints its value. A file stops at
its first error, reports it as `FILE:LINE: error: …`, and exits with
status 1. The REPL reports an error and carries on. `quit` is the REPL's
command, not a word of the language.

## Lines, blocks and comments

moop is read one line at a time. A line that ends with `is` opens a
**block**: the definition's body follows on indented lines, and the
first blank line closes it. A body is a sequence, and its last line
gives the value.

```
treasure is
    a world
    42

treasure                     → 42
```

A **comment** is a whole line whose first character other than a space
or a tab is `;`. A comment runs nothing and prints nothing. It neither
opens nor closes a block, so it can sit inside a body, indented or not.
A `;` after code is not a comment, and is refused.

```
box is a world
box twice n is
    ; deposit n twice: the two cancel, since mirrors is an involution
    mirrors n
    mirrors n

box twice 5                          → a proto
```

**The reader refuses rather than guesses.** It refuses:
- an indented line with no open block;
- a line longer than 1,023 bytes, rather than splitting it;
- a NUL byte;
- input that cannot be read, such as a directory;
- a character it does not know.

None of these is run as something else.

## Grammar

moop has one rule:

```
statement := chain ["is" [chain]]
chain     := [term] ((ask | inherits | mirrors | WORD) term)*
term      := ("a" | "an") term | WORD | NUMBER | true | false
```

- **Chains read left to right.** `p ask q ask r` asks `p` for `q`, then
  asks the result for `r`. There is no precedence and no grouping: give
  an intermediate result a name instead.
- **A chain may begin with an operator.** Such a *headless* chain
  addresses the current receiver: inside a taught body, the object that
  was asked; at the top level, the world. moop has no `self` keyword:
  English drops the subject of an imperative, and moop does the same.
- **Arrows.** `->`, `<-` and `<->` are exact aliases of `ask`,
  `inherits` and `mirrors`. The one-way arrows forget; the two-way arrow
  preserves.

## Values

There are three kinds of value: numbers, truth values and protos.

- **Numbers are exact rationals.** A number is p/q in lowest terms,
  with a positive denominator, and zero is 0/1. Both |p| and q are at
  most 2⁶³ − 1. Within that range everything is exact; beyond it, moop
  refuses, and never wraps, rounds or saturates.
- **Number literals.** An optional `-`, digits, then optionally `/` and
  digits, with no spaces: `7`, `-7`, `9/5`, `-9/5`. There is no decimal
  point. A literal is reduced as it is read, and each written part may
  be up to 2¹²⁷ − 1 before reduction.
- **Truth values** are written `true` and `false`. They are reserved:
  `true is 5` is refused.
- **Protos** are the objects. They are made by birth (below).

Every number and truth value prints as text that reads back as an equal
value: a whole number without `/1`, a fraction reduced with its sign in
front. A proto prints as `a proto`.

```
10/4                                 → 5/2
-9/5                                 → -9/5
x is 18446744073709551614/2
x                                    → 9223372036854775807
```

### Equality

`equals` is built in on every kind of value:
- numbers are equal when they are the same rational;
- truth values when they are the same truth value;
- protos only when they are the same proto. Equality is identity, and
  never compares structure.

Values of different kinds are always unequal. `equals` cannot be taught.

```
2/3 equals 4/6                       → true
5 equals true                        → false
```

## Names and births

`name is chain` binds a name, evaluating the right side now. Names are
the one mutable handle in moop: rebinding is allowed.

The **indefinite article births a proto**, just as English separates
identity from membership. There is no `new` and no `create`.

```
dog is a world
; identity: rex names that very proto
rex is dog
; membership: rex names a new proto, born from dog
rex is a dog
; an anonymous birth
a world                              → a proto
```

The session starts with one name, **`world`**: the root proto that
users build from. It was itself born from the system's root, which was
born from the machine's actor.

**What a birth gives a proto.** The proto gets a body: two small tapes,
seeded deterministically from its parent's machine (below). It also
gets a parent, fixed at birth.

## Messages

- **`receiver ask message`** sends a message that takes nothing.
- **`receiver message argument`**, with the message word where an
  operator stands, sends a message that takes exactly one argument.

**Teaching.**
- `receiver ask m is chain` teaches a message that takes nothing.
- `receiver m p is chain` teaches one that takes something, and names it
  `p`.
- The body is stored as written, and runs each time the message is sent.
- Teaching the same name again replaces it.

**Dispatch.** A message is looked up in this order:
1. the built-in messages;
2. what the receiver was taught;
3. what its parents were taught, nearest first.

The receiver stays the one that was asked.

**Arity is strict.** The nearest teaching decides whether a message
takes something. Sending it the other way is refused, and the search
never falls back to an ancestor's teaching. So a child may change what
an inherited message takes, and is then not interchangeable with its
parent.

**The argument is evaluated before the message is sent:** the receiver
first, then the argument, then the dispatch. Whatever evaluating them
did stands, even if the message is then refused.

**Parameters.** A parameter belongs to its own body, and shadows an
outer name of the same spelling there.

**Built-in messages.**

| Message | Receiver | What it does |
|---|---|---|
| `ask maybe` | a proto | Steps the proto's body once and observes one cell: a truth value. It is deterministic: an observation, not a random draw |
| `ask value` | a proto | Reads the body's first tape as a whole number from 0 to 255 |
| `equals x` | any value | Equality, as above |
| `and`, `or`, `nand`, `nor`, `xor` | a truth value | Logic. Both sides are always evaluated, so nothing short-circuits. These words are not reserved |

**Answering with the receiver.** A body cannot name its receiver, but
`mirrors 0` deposits nothing and gives back the receiver:

```
dog is a world
dog ask me is mirrors 0
rex is a dog
rex ask me equals rex                → true
```

**One limitation of the grammar.** A body cannot send its own receiver
a message that takes something. A headless chain must begin with
`ask`, `inherits` or `mirrors`, and `ask` gives nothing.

## Lineage

`child inherits parent` asks whether `parent` is the proto `child` was
born from: `true` or `false`. Parents never change, so the lineage can
never form a cycle. To change behaviour, birth a new proto and rebind
the name; there is no re-parenting.

## Mirrors: the reversible operator

`mirrors` relates two things without losing information, and it is
carried out with real reversible gates. Every form undoes itself:
applied twice, it is the identity.

- **A number and a proto:** `5 mirrors box` XORs 5 onto the proto's
  body. A body holds whole numbers from 0 to 255; anything else is
  refused, never truncated.
- **Two protos:** `box mirrors tin` exchanges their first tapes.

Either form gives back the left-hand proto, so a chain can continue.

```
box is a world
box ask value                        → 181
5 mirrors box                        → a proto
box ask value                        → 176
5 mirrors box                        → a proto
box ask value                        → 181
```

The values come from the body's tapes, so they depend on the machine.
They are deterministic: the same program gives the same values.

## The machine underneath

Every proto's body is a small reversible machine: two circular tapes of
bits turning in opposite directions, joined by a CCNOT (Toffoli) gate
that fires into both.

- **Every step runs backward exactly.** Both tapes stay writable, so on
  the tapes code and data are the same cells. Run backward, a state
  yields the states that led to it.
- **One sanctioned way to forget.** Causal pruning clears only cells
  whose values provably affect nothing else.
- **What a program reaches of this.** These are properties of the
  machine, shown by its C tests. A program reaches the machine through
  births, `ask maybe`, `ask value` and `mirrors`, and through nothing
  else. In 0.10.0 a program cannot run a body backward, and no body is
  pruned while a program runs (`model.md`).
- **Two memories, two logics.**
  - Gates act on the tapes; ordinary logic acts on values in memory.
  - They meet in one shape only: a reversible effect inside, an
    observation outside. `maybe` is that bridge.
  - `maybe` is not random. On the current wiring, a draw agrees with the
    draw eight before it 74.8% of the time.
- **Frozen wiring.** The current wiring, wiring 1, is frozen and pinned
  by a trace that the sibling language Selvage reproduces byte for byte
  (`../related/README.md`).

## When moop says no

moop never pretends. What it cannot do, or will not do, it refuses with
a reason.

| You write | moop answers |
|---|---|
| `box add 5 6` | *add takes one argument, and '6' would be a second* |
| `box ask add`, when `add` takes something | *add takes something: write it after add, without ask* |
| `box ask add 5` | *ask sends a message that takes nothing: to give add something, write it without ask* |
| `5 plus 3` | *a number answers equals, not "plus"*. Arithmetic is not built yet |
| `5/0` | *5/0 has a denominator of 0* |
| `a 5` | *births come from protos* |
| `x is 5 ; five` | *unexpected character ';'* |
| `world ask dance` | *nothing in the lineage hosts "dance"* |

## Words

| Kind | Words |
|---|---|
| Reserved operators | `is`, `ask` (`->`), `inherits` (`<-`), `mirrors` (`<->`) |
| Reserved for birth | `a`, `an` |
| Reserved values | `true`, `false` |
| Built in, not reserved | `maybe`, `value`, `equals`, `and`, `or`, `nand`, `nor`, `xor` |
| Predefined name | `world` |

## Not in the language yet

| Feature | Status |
|---|---|
| Arithmetic: `plus`, `minus`, `times`, `over` on numbers | Ratified (`foundations.md`, F10); not yet built |
| Certified inverses: `world celsius mirrors fahrenheit` | Ratified (F11 to F14, U2); not yet built |
| Text values | Deferred, and so is its syntax |
| Reflection: reading a taught body back as a value | Deferred |
| Running a body backward, and pruning a body | The machine can do both; no message reaches either |
| Choosing what runs next from a truth value | Not designed. A truth value can be printed, named, compared and combined, and nothing more |
| Definitions nested inside a block | Refused (*definitions cannot nest (yet)*) |
| A comment on the same line as code | Not part of the language |
