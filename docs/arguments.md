# Messages that take something

**Status: ruled 2026-11-18. Q1 to Q5 are adopted as recommended, with
the qualifications below. The design is not implemented**: the
interpreter still refuses `box add 5` (*expected an operator between
expressions*). No new language construct is authorized by these
decisions.

The options and their analysis are kept below as the record of why. Two
of the options were built as throwaway prototypes outside the
repository, to check the claims made for them; what was measured is
marked *measured*. Everything said about how a form reads is judgment:
no reading evidence was gathered, and the prototypes do not establish
that the two shapes read equally well.

Terms: an **argument** is the value a message is given when it is sent;
a **parameter** is the name a teaching gives that value.

## Rulings (2026-11-18)

| # | Question | Adopted | Qualification |
|---|---|---|---|
| Q1 | How a message is given an argument | **A:** the message occupies the operator position — `box add 5` | One grammar: no second message syntax |
| Q2 | How a taught body reaches the argument | **P1:** the teaching names it — `box add n is mirrors n` | |
| Q3 | How a body sends its own receiver such a message | **It cannot** (A1) | A limitation of the selected grammar, not an unimplemented feature that is promised |
| Q4 | How many arguments, and when they are evaluated | **Exactly one, evaluated before dispatch; strict arity** | No optional, variadic or lazy arguments |
| Q5 | The logic words | **`and`, `or`, `nand`, `nor`, `xor` are built-in messages on truth values;** no word is reserved | **Eager**, not short-circuit: under Q4 the argument is evaluated before dispatch |

The two forms fit together: `box add 5` sends a message with an
argument, and `box add n is mirrors n` defines the teaching that
answers it and binds the argument to `n`.

## What forces it

1. **The user layer's own logic cannot be written.** `src/logic.c` has
   AND, OR, NAND, NOR and XOR. Each relates two values, and the surface
   language has no form for that: `x and y` is refused (*expected an
   operator between expressions*), and nothing in the evaluator calls
   them.
2. **A taught message can be given nothing.** The only forms that relate
   two values are innate: `child inherits parent` and `5 mirrors box`.
   A program can teach what a proto does when asked, and never what it
   does *with* something.

**Can arguments be derived away?** The deletion test's candidate is the
body itself: deposit the value, then ask (`5 mirrors box`, then
`box ask add`). It covers one number given to one body. It does not
cover a proto given to a proto, since a body holds 8 bits and not a
reference, and it does not cover relating two values at all. No uniform
rule already present covers the uses, so the construct is not dissolved.

## Q1 — the shape of a send with an argument

| | A. Operator position | B. After the asked word | C. A linking word | D. Parentheses |
|---|---|---|---|---|
| A send | `box add 5` | `box ask add 5` | `box ask add with 5` | `box ask add(5)` |
| The teaching | `box add n is …` | `box ask add n is …` | `box ask add with n is …` | `box ask add(n) is …` |
| A relation | `x and y` | `x ask and y` | `x ask and with y` | `x ask and(y)` |
| To the receiver, in a body | not expressible (Q3) | `ask add n` | `ask add with n` | `ask add(n)` |
| Grammar | `op` gains WORD; the rule keeps its shape | the term after `ask` may be followed by a term | `ask WORD ["with" term]` | `ask WORD ["(" term {"," term} ")"]` |
| Reserved words added | none | none, or five if relations are to read as relations | `with`, and the same five | the same five; three new token kinds |
| Arguments | one | one | one | several |
| Prototype | built | built | not built | not built |

**A. The message in operator position.** The grammar already has the
shape: `chain := [term] (op term)*`. `inherits` and `mirrors` are
two-place relations written `left OP right`. A lets a taught word stand
where `OP` stands. Nothing else in the grammar changes.

- *What it makes of `ask`.* `ask` stays, and its job gets sharper: it is
  the send that gives nothing. It cannot be deleted. If `box size` were
  the send with no argument, `a b c d` could be read as `(a b c) d` or
  as `((a b) c) d` only by knowing what `b` takes: one form, two
  meanings. With `ask`, every chain parses without knowing any teaching.
- *What it makes of the operators.* `inherits` and `mirrors` are the two
  innate messages that take something, as `maybe` and `value` are the
  two that take nothing. "Operators differ in meaning, never in shape"
  extends to what programs teach.
- *The cost.* A misspelt operator word is no longer caught when the line
  is read: `rex inherit world` becomes a send of `inherit`, refused when
  it runs (*nothing in the lineage hosts "inherit"*). Inside a taught
  body that is when the message is asked, not when it is taught.
  Message names after `ask` are already late-bound this way.

**B. The argument after the asked word.** One send form, with or without
an argument, and headless chains extend to it directly (`ask add n`).

- *The cost.* A two-place relation does not read as one: `x ask and y`.
  To read `x and y`, the logic words would have to be reserved infix
  operators, and so would every later relation (`plus`, `above`). A
  program's own relations would stay second-class in how they read.
- *Slips.* A term left after an asked word, today an error, becomes an
  argument. Strict arity (Q4) turns most such slips back into errors.

**C. A linking word.** B with a marker, so no slip turns a stray term
into an argument. It costs a reserved word and reads no better for
relations.

**D. Parentheses.** The form programmers know, and the only option with
several arguments. It adds three token kinds and a second shape beside
the operators, and it invites nested expressions, which the one-rule
grammar does not have. As it stands it is borrowed on authority: nothing
in moop forces it.

**Adopted: A.** It is the only option that adds no shape and no
reserved word, and the only one in which a program's own relations read
like the built-in ones. What it gives up is in Q3.

## Q2 — how a body reaches the argument

| | P1. Named by the teaching | P2. By position | P3. A reserved word |
|---|---|---|---|
| Teaching | `box add n is mirrors n` | `box add is mirrors` | `box add is mirrors it` |
| Rule | The word after the message in the designator is the parameter | A chain that ends with an operator addresses the argument, as one that begins with an operator addresses the receiver | One word always means the argument |
| The argument can stand | anywhere a name can, any number of times | last in a chain, once | anywhere |
| Adds | a name local to one body | nothing | a reserved word |

- **P1** makes the teaching mirror the send, as `dog ask speak is …`
  mirrors `dog ask speak` today. The parameter is moop's first local
  name: visible in that body's chains only, shadowing a name bound
  outside for the length of the body, and never rebound, since a body
  holds no `is`. The receiver is already saved and restored around each
  send; the parameter and its value join it as one frame.
- **P2** is the receiver's rule mirrored, and adds no concept. It cannot
  put the argument on the left (`other ask value`) or use it twice.
- **P3** reopens the decision against a receiver keyword: a word for
  the argument and none for the receiver is hard to defend.

**Adopted: P1.** The teacher chooses the word, as English does
("to add *something* to a box…"), and no word is reserved.

## Q3 — sending the receiver a message with an argument

Under A, a chain that begins with a plain word is headed: the word is a
name. So a body cannot write `add n` to its own receiver.

| | What it means | Cost |
|---|---|---|
| **A1. Not expressible** | Only `ask`, `inherits` and `mirrors` begin a headless chain, as now | A body cannot send its receiver a taught message with an argument |
| A2. Imperatives by count | A chain that cannot be read with a head is read without one: `add n` | The whole line must be counted; adding or dropping one word changes who is addressed |
| A3. Both shapes | `ask add n` when headless, `box add 5` when headed | Two spellings of one send |

**Adopted: A1, as a limitation of the selected grammar.** Under A a body
cannot send its own receiver a message that takes something, and
nothing in this design promises that it will. The limitation has the
same root as the one with `inherits`: the receiver has no name, so it
can stand only at the head of a chain that begins with a reserved
operator.

B would have allowed it (`ask add n`), at the cost of a second form of
argument-bearing send and of relations that read less naturally; that
trade was judged not worth it at this stage.

## Q4 — limits

- **Exactly one argument.** The shape `left OP right` has one right
  side. It matches the user layer's logic, which is all two-place. A
  second argument cannot be written: in the prototype, `box add 5 6` is
  refused when the line is read (*expected an operator between
  expressions*), and so is `box add 5 x` (*'x' stands where a message
  that takes something stands, and nothing follows it*). `box add 5 x 7`
  is a pipeline, not two arguments: it sends `x` with `7` to what
  `box add 5` answers.
- **Arguments are terms.** A name, a number or a birth; a chain is given
  by naming it first (`t is tin ask value`, then `box add t`). The
  grammar has no grouping and gains none.
- **Evaluated before dispatch,** receiver first, as `inherits` and
  `mirrors` evaluate their sides. Arguments passed as unevaluated chains
  belong with reflection, which is open.
- **Strict arity.** A message taught with a parameter refuses a send
  without an argument, and the reverse, naming the form to write. One
  teaching per proto and name: re-teaching replaces it, whatever it
  takes.
- **No exceptions:** no optional, variadic or lazy arguments.

## Q5 — the logic words

Under A, `and`, `or`, `nand`, `nor` and `xor` are built-in messages on
truth values, calling `src/logic.c`. They are not reserved: their
built-in meaning comes from the position, a message sent to a truth
value, and a proto may be taught its own `and`. This settles the open
question in `docs/syntax.md` (keywords or ordinary messages). Numbers
would host arithmetic the same way; which arithmetic belongs to the user
layer is its own question, not ruled here.

**Eager, not short-circuit.** Under Q4 the argument is evaluated before
the message is dispatched, so `and` and `or` evaluate their right side
whatever the left is. An argument is a term, so the one right side whose
evaluation can be seen is a birth, which steps its generator's tapes.
*Measured* in the prototype: with `f` false, `f and a w` births a proto
from `w` (its value goes from 52 to 44) before `and` is dispatched, and
`and` then refuses the proto (*and relates two truths*).

Without grouping, `p ask maybe and q ask maybe` reads left to right as
`((p ask maybe) and q) ask maybe` and is refused, since `q` is a proto.
The second draw is named first.

## What it compounds with

- **The layer rule is untouched.** An argument is a user-layer value in
  RAM. Nothing reaches the tapes except through `mirrors`, as now.
- **Definable bijections.** A taught body made only of `mirrors` lines
  is a sequence of involutions, so the same lines read last-to-first
  undo it. With an argument, such a body is a candidate for the
  definable invertible function `docs/syntax.md` leaves open. Not
  designed here.
- **Reflection.** A teaching becomes a name, a parameter and chains:
  still data in RAM, and what a mirror would read back.

## Limits that remain

- **The receiver cannot be the right operand of `inherits`.** A relation
  can be taught from the other side, which covers most of the need:
  `cat child_of animal` with the body `inherits elder`.
- **A body cannot send its own receiver a message that takes something**
  (Q3), as above.
- **Answering with the receiver: corrected.** The earlier record said a
  body cannot answer with its receiver. That was inaccurate: the
  existing identity idiom `mirrors 0` does it, and is retained
  (2026-11-18). Depositing 0 sets no cell, no mark and no head, and
  `mirrors` yields its left side, which in a headless chain is the
  receiver. The idiom belongs to `mirrors`: the receiver still has no
  name, and the language has no general receiver-returning expression.
  Regression checks: `tests/test_core.c` (depositing 0 changes nothing)
  and `tests/run_tests.sh` (`kid ask me inherits box` is `true` with `me`
  taught on `box` as `mirrors 0`, and the body's value is unchanged).

## What the prototypes showed (measured)

Both prototypes are outside the repository and are not proposed as
patches. They establish that both shapes pass the existing checks. They
do not establish equal readability, and do not settle the semantic cost
of Q3: those were design judgments.

| | A | B |
|---|---|---|
| Change to `src/` | 126 lines added, 9 removed, 3 files | 127 added, 9 removed, 3 files |
| Of which the parser | 14 added, 2 removed | 15 added, 2 removed |
| Existing checks (`make test`, as of 0.7.0) | 63 of 63 pass, none edited | 63 of 63 pass, none edited |

The evaluator's part is the same in both: the frame, the arity
refusals, the logic words. The options differ by about fifteen parser
lines, so cost does not choose between them.

Under A, as run:

```
box is a world
box add n is mirrors n
box ask value                  181
box add 5 ask value            176
animal child_of elder is inherits elder
cat child_of animal            true
x and y                        false     (x false, y true, from two draws)
x xor y                        true
```

Refused, as run:

| Line | Refusal |
|---|---|
| `box ask add` | *add takes something: write it after add, without ask* |
| `box size 5`, `size` taught with `ask` | *size takes nothing: ask size* |
| `box add` | *'add' stands where a message that takes something stands, and nothing follows it* |
| `box helper is 1`, the `ask` forgotten | the same refusal, for `helper` |
| `box add 5 is 3` | *only names and messages can be defined* |
| a body naming another body's parameter | *unknown name 'n'* |

A parameter `n` left a name `n` bound outside as it was. A2, C and D
were not built.

## Still open

- Whether a parameter may take a name already bound outside, or is
  refused.
- Whether a child may re-teach a message with a different arity than
  its parent's.
- Arrow spellings: the word operators have none.
- Arithmetic on numbers, and which of it is the user layer's.
