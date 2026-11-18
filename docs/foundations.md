# Shared foundations: reader, values, numeric messages, certified transformations

**Status: a draft for rulings. Nothing here is decided or built.** Each
realization needs its own authorization after the rulings. A throwaway
prototype outside the repository tested the claims that carry the
design; what it showed is marked *measured* and collected at the end.
How a form reads is judgment, not evidence.

## The criterion

Every proposal below answers one question: **does it create a reusable
capability that makes other capabilities simpler, rather than a
mechanism used once?** In practice:

- messages over new expression forms;
- the existing truth values, not a parallel boolean type;
- invertibility derived and established, never declared;
- one reader policy for the REPL and files;
- an inspectable representation only when several consumers need it.

The seven open items reduce to four areas and two deferrals:

| Area | Items | What they share |
|---|---|---|
| 1. Reader | comments, blank lines in bodies | one rule for which lines the reader sees |
| 2. Values | truth, text and number literals, the numeric model | one printing law, one equality |
| 3. Numeric messages | arithmetic | the argument machinery of 0.8.0 |
| 4. Certified transformations | definable invertible functions | `mirrors`, the pipeline grammar, exact numbers |
| Deferred | reflection; wiring 2 | — |

## Rulings asked for

| # | Area | Proposal | Recommended |
|---|---|---|---|
| F1 | Reader | `;` begins a comment that runs to the end of the line, outside a text literal. A comment is lexical: not a value, not kept in a taught chain | Adopt |
| F2 | Reader | A line holding only a comment is not read: it neither opens, continues nor closes a block, in the REPL or a file | Adopt |
| F3 | Reader | A blank line still closes a block, so a body holds no blank lines; a `;` line spaces a body instead. This closes the open question | Adopt |
| F4 | Values | Numbers are exact rationals, numerator and denominator 64-bit, kept in lowest terms with a positive denominator. Every operation is exact or refused: no wrapping, no rounding, no floating point | Adopt |
| F5 | Values | Number literals: an optional `-`, digits, and optionally `/` and digits, with no spaces (`-7`, `9/5`, `-5463/20`). A literal too large, or with denominator 0, is refused | Adopt |
| F6 | Values | `true` and `false` are literal words, reserved, denoting the existing truth values | Adopt |
| F7 | Values | Text: `"…"`, printable ASCII, `""` for a quote and no other escape; one immutable value no longer than a line; it answers `equals` | Adopt the form; realize when a second consumer exists |
| F8 | Values | Every number, truth and text prints as a literal that reads back as an equal value. A proto prints as `a proto` | Adopt |
| F9 | Values | `equals` is one innate message on every kind: numbers and text by value, truths by truth, protos by identity; different kinds are unequal | Adopt |
| F10 | Numeric messages | `plus`, `minus`, `times`, `over` are messages on numbers: exact, eager, refused on overflow and on `over 0`, not reserved, read left to right | Adopt |
| F11 | Certified transformations | `receiver inverse mirrors forward` teaches `inverse` as the mirror of `forward` | Adopt |
| F12 | Certified transformations | A mirror exists exactly when the forward body is one chain from its parameter through `plus`/`minus` by any number literal and `times`/`over` by a non-zero one. The mirror is those steps reversed, each inverted; the mirror of a mirror is the forward | Adopt |
| F13 | Certified transformations | The mirror is derived at each send, from the forward that the receiver's lineage gives then | Adopt |
| F14 | Certified transformations | The domain is the numbers of F4. Wherever both directions are defined they are inverses; outside the representable range both refuse | Adopt |

They can be ruled area by area. F10 depends on F4; F11 to F14 depend on
F4 and F10; F7's printing depends on F8.

## 1. Reader: one policy for comments and blank lines

**What forces comments.** Files are read by people, and a program cannot
explain itself. The deletion test asks whether something present can
carry an explanation. A text literal on a line of its own cannot: a file
prints the value of every statement, so the note would be output. Binding
it to a name adds a name to the program. Nothing present covers the job
without becoming an action, so the construct is not dissolved.

**Why `;`.** moop's own documentation already writes its notes that
way. Seven lines of examples in `docs/syntax.md` annotate code with `;`
(`rex is dog       ; identity: …`). With F1 and F2 those examples run as
written (*measured*). `;` is currently a stray character, so adopting it
changes the meaning of no program. Lisp writes comments the same way;
moop's reason is its own usage, not the precedent.

**Why comment lines are not read (F2) rather than treated as blank.**
One of those examples, `docs/syntax.md` line 100, is a comment-only line
inside an open block. If comment lines counted as blank, that line would
close the block, and the documentation's own example would fail. Read
as nothing, it runs (*measured*). The rule also matches how prose reads:
a blank line breaks a paragraph, while a note in the margin does not.

**Why a blank line still closes (F3).** The alternative closes a block
at the first unindented line, as Python does, and lets bodies hold blank
lines. It has a hazard: a body line whose indent was forgotten would end
the block silently and run as a statement addressed to the world, a
mistake becoming an action. With a blank line as the close, that line
is refused (*expected an indented line or a blank line*). The
alternative brings no advantage that F2 does not already give, so the
existing behaviour stays. F2 also dissolves the open question about
blank lines in bodies: a `;` line spaces a body without closing it.

**What F1 to F3 compound with.**
- **The single reader.** One rule serves the REPL and files.
- **Text.** A `;` inside a text literal is part of the text. The lexer
  reads a literal before it looks for a comment. A comment-only line is
  recognized by its first character that is not a space, which cannot be
  inside a literal.
- **Homoiconicity.** Comments are not data, so a taught chain holds no
  comment, and later reflection would show none. Lisp makes the same
  trade.

## 2. Values: one model

Four kinds of value: numbers, truths, text and protos. Two laws apply to
all of them.

**One printing law (F8).** A number, truth or text prints as a literal
that reads back as an equal value. It is the value-level form of
homoiconicity: what moop prints, moop can read. It is also what makes
the printed forms unambiguous. Text prints with its quotes, because the
text `"5"` and the number `5` must not print alike. Protos are
references and print as `a proto`, as now. *Measured*: 702 values (500
computed numbers, 200 texts with quotes and `;` in them, both truths)
were printed and read back, and all 702 were equal to the originals.

**One equality (F9).** `equals` is innate on every kind, so a proto
cannot be taught its own, as it cannot for `maybe` and `value`. Values of
different kinds are unequal, and that is an answer, not a refusal:
`5 equals true` is `false`. Protos are equal only when they are the same
proto, the identity `is` creates by aliasing. One message replaces the
per-kind equality an expression grammar would need.

### Numbers (F4, F5)

**Why exact rationals.**
- **The demanding test needs them.** F(C) = 9/5·C + 32 is a bijection
  on the rationals and not on the integers: an integer Celsius gives a
  whole Fahrenheit only when it is a multiple of 5. Over the integers,
  every conversion of this kind would need a declared domain and a way
  to write one. Over the rationals the domain is the same for every
  number, so no domain annotation is needed (F14). The value model
  removes a construct from area 4.
- **Arithmetic stays invertible.** Adding any number is undone by
  subtracting it, and multiplying by any non-zero number is undone by
  dividing by it. Every arithmetic step carries its own inverse, which
  is what area 4 derives mirrors from.
- **Floating point is excluded.** Rounding breaks inverses, so
  invertibility could only be asserted, never established.
- **Unbounded integers are excluded for now.** They would grow the
  implementation by more than the rest of this plan. The bound is
  honest instead: anything past 64-bit numerators and denominators is
  refused, never wrapped or rounded.

Checked arithmetic uses the compiler's overflow builtins. C23's
`<stdckdint.h>` wraps them, but GCC 13, the compiler here, does not ship
it; Clang 18 does (*measured*).

**Literals (F5).** `9/5` is one literal, with no spaces, read in lowest
terms (`10/4` is `5/2`). It is needed by F8: a computed fraction prints
as `9/5`, so `9/5` must read back. Negative literals are needed for the
same reason. `-` followed by a digit cannot be confused with `->`.

A body still carries whole numbers from 0 to 255: depositing a fraction
or a negative number is refused, as an oversized one is now.

**A defect fixed now, separately.** A literal past 9223372036854775807
used to saturate silently, and one of more than 31 digits was cut short
before being read. That is fixed and tested in commit `8a5b78f`
(*literal is too large*). It is a defect fix only: any numeric model must
refuse such literals, and the fix decides nothing here.

### Truth literals (F6)

There are two alternatives. Truth values could be names bound when the
session starts, as `world` is. That needs no new token, but names can be
rebound, so `true is false` would silently break F8, since `true` would
no longer read back as true. As reserved words they cannot be rebound,
and the printing law holds by construction. This is the deciding
argument. Reserving `true` and `false` does not reverse Q5, which
declined to reserve the logic *messages*: these are values, which stand
in term position and never in operator position.

### Text (F7)

- **Form:** `"…"`, printable ASCII (0x20 to 0x7E). A quote is written
  `""`; there is no backslash escape and no other escape.
- **Size and encoding:** at most one line long. The source is ASCII
  (the reader refuses other bytes), so the encoding is ASCII.
- **Behaviour:** immutable. It answers `equals` and prints by F8.
- **What it is not:** it cannot be deposited on a body or born from.

**Realization.** Text has one consumer today: labels in a program's
output. By the criterion that is thin, so I recommend fixing its form
now, because it shapes the lexer and the comment rule, and building it
when a second consumer is ready. Reflection would be one: a teaching's
name is text.

**Left out until something consumes them:** ordering of numbers
(`below`, `above`), since moop has no conditional that would use a truth
produced that way, and any operation on text beyond `equals`.

## 3. Numeric messages (F10)

`plus`, `minus`, `times` and `over` are messages on numbers. They use
the 0.8.0 machinery unchanged: the message in operator position, one
argument evaluated before dispatch, strict arity, and no reserved words.
This is the precedent the logic words set, so arithmetic adds no
expression form. They are user-layer operations: as two-place functions
they consume two values and return one, so they lose information.

- **Refusals:** overflow (*the number is too large*), `over 0`
  (*division by zero*), and an argument that is not a number (*plus
  relates two numbers*). A number refuses any other message, naming the
  ones it answers.
- **Left to right, with no precedence.** `2 plus 3 times 4` is 20, not
  14 (*measured*). Chains associate left, and precedence would need a
  second shape or grouping, which the grammar does not have. This is a
  naturalism cost against school arithmetic, stated rather than hidden;
  naming an intermediate result is the way to write anything else.
  Smalltalk made the same choice for message arithmetic; here it follows
  from moop's own one-rule grammar.
- **Negation** is `0 minus x`; no prefix operator is added.

## 4. Certified transformations (F11 to F14)

**The synergy.** A chain such as `c times 9/5 plus 32` is already a
pipeline: left to right, each step a message applied to the value so
far. When every step has a known inverse and an argument that does not
read the value, the whole chain is invertible. Its inverse is the same
steps read backward, each inverted: `f minus 32 over 9/5`. So moop needs
no inversion language and no annotation. Exact numbers (F4), the
argument grammar (Q1) and left-associative chains together give
certified inverses. The checker reads the chain and either derives the
mirror or names the step that loses information.

**The form (F11).** It is a definition, alongside `is`:

```
world fahrenheit c is c times 9/5 plus 32
world celsius mirrors fahrenheit
world celsius 212        ; 100
```

- `mirrors` keeps its one job: an information-preserving correspondence.
  In an expression it applies an involution. In a definition it names
  the other side of a bijection.
- The law that defines the word carries over: the mirror of the mirror
  is the original (*measured*). Applying the same `mirrors` twice is the
  identity, for teachings as for bodies.
- The shape `receiver message mirrors message` is refused today: a
  message in operator position needs an argument. So it gives no
  existing line a new meaning.
- Both directions are defined and named, and neither is written twice.

**When a mirror exists (F12).** The forward teaching must:
- take something (one parameter);
- have a body of one chain that starts from that parameter;
- use only steps `plus` or `minus` by a number literal, or `times` or
  `over` by a non-zero number literal.

Arguments must be literals. A name could be rebound between the two
sends, and the parameter itself would make a step read the value it
changes, as `c times c` does. Anything else is refused with the step
named (*measured*):

| Forward | Refusal |
|---|---|
| `c times c` | *sq has no certified mirror: times takes a number written out, not a name* |
| `c times 0` | *zero has no certified mirror: times 0 loses what it is given* |
| `c times k`, `k` a name | the same as `c times c`: a name, not a literal |
| a two-line body | *two is not one chain, so it has no certified mirror* |
| a message that takes nothing | *flat takes nothing, so it has no mirror* |
| two mirrors of each other | *mirrors form a cycle* |
| a forward nothing teaches | *none mirrors nothing, and nothing in the lineage teaches nothing* |

Lossy transformations stay distinct: they are ordinary teachings, and
they have no mirror.

**Late derivation (F13).** The mirror is derived at each send, from the
forward that the receiver's lineage gives at that moment.
- **Not stale.** Deriving once, at definition, would leave the mirror
  out of date as soon as the forward is re-taught: a stale inverse that
  still answers, a mistake becoming an action. Derived at each send,
  re-teaching `fahrenheit` changes `celsius` with it (*measured*).
- **Same lookup as every send.** A child that re-teaches `fahrenheit`
  gets its own `celsius`, and the parent's is unchanged (*measured*).
  This is the nearest-teaching rule already ruled for arity.
- **Strict arity.** A mirror takes one number: `world ask celsius` and
  `world celsius true` are refused.

**Domain (F14).** The domain is the numbers of F4, for every certified
transformation. On every number where both directions are defined, they
are inverses. Where a step would overflow, that direction refuses
(*the number is too large*), so each transformation is a bijection on
the numbers it can represent, and refuses outside them. That is stated,
not hidden. No domain annotation exists or is needed (see F4).

**What the same rule would cover later.** A teaching made of `mirrors`
deposits on a body is a sequence of involutions, and its inverse is the
same lines in reverse. F12's rule (each step invertible, inverse
reversed) covers it unchanged. It is not proposed here.

## 5. Deferred: reflection

Nothing above needs reflection. The plan does create its first real
consumers, so the case can be made later on evidence:
- derived mirrors are chains in RAM, and showing one would let a person
  read what moop derived;
- text (F7) would give teachings' names a value;
- the printing law (F8) is already half of serialization.

When those exist, a read-only representation of a taught chain can be
weighed. Executable reflection, or changing a teaching through it, is
not proposed.

## 6. Independent: wiring 2

It is unchanged and unscheduled. It needs a positive objective and
measurable acceptance criteria first (`docs/model.md`).

## Realization order, each step authorized on its own

1. **Reader (F1 to F3).** Small and independent. The documentation's
   examples become runnable.
2. **Numbers, truths, equality and printing (F4 to F6, F8, F9).** The
   value model, without text.
3. **Arithmetic (F10).**
4. **Certified transformations (F11 to F14).** The Celsius/Fahrenheit
   program becomes the acceptance test.
5. **Text (F7),** when a second consumer is ready.

## What the prototype showed (measured)

It was built on 0.8.0, outside the repository, with all of F1 to F14
including text. It adds about 326 lines to `src/`. It is not proposed
as a patch.

| Claim | Result |
|---|---|
| Existing checks still hold | 92 of 93 pass. The one that changed is meant to: numbers now answer messages, so *a number answers no message that takes something* is gone |
| The documentation's `;` examples run as written | Yes, with the lines that define `dog` and `animal` added before them, including the comment-only line inside an open block (`docs/syntax.md` line 100) |
| Exact arithmetic, left to right | `2 plus 3 times 4` is 20; `1/3 plus 1/3` is 2/3; `10/4` reads as 5/2; `2/3 equals 4/6` is true; `1/3 times 3 equals 1` is true |
| Refusals | A literal one past the bound, an overflowing sum, `5 over 0`, `1/0`, `5 plus true` and `"a" plus "b"` are each refused with a reason |
| Celsius and Fahrenheit | `fahrenheit 100` is 212; `celsius 212` is 100; `fahrenheit -40` is -40; `celsius 98` is 110/3; `fahrenheit 110/3` is 98; from 37 to Fahrenheit and back, with a name holding the middle value, `equals 37` is true |
| The mirror of the mirror | equals the forward |
| Late derivation | After `fahrenheit` is re-taught, `celsius` follows it; a child's own `fahrenheit` gives the child its own `celsius`, and the parent's is unchanged |
| Random pipelines, 3 seeds | 1,200 forwards of 1 to 6 steps (literals −50 to 50, over 1 to 12) and 3,600 inputs. All 10,800 round trips hold (mirror after forward, forward after mirror, mirror of mirror equals forward), all 3,600 mirror values equal an independent model in Python fractions, and none is refused |
| Printing round trip | 702 of 702 values read back equal |
| Sanitizers | The checks, the example programs and one seed of the random pipelines (1,200 inputs) run clean under ASan and UBSan, after one prototype bug UBSan found was fixed (a copy from a null pointer when a mirror stores no body) |

**What it does not show:**
- that these forms read well to people (no reading evidence was
  gathered);
- that 64-bit rationals are big enough for the programs moop will
  actually have;
- anything about text beyond its form and its printing.
