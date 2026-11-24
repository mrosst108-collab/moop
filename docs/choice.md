# Choice

**Status: draft for ruling (2026-11-24). Nothing here is adopted and
nothing is built.** This is step 3 of the synthesis plan: derive choice,
or show that moop should go without it. It ends in five questions, D1 to
D5, each with a recommendation.

Three of the options were built as throwaway prototypes outside the
repository, to check the claims made for them; what was measured on them
is marked *measured*. Everything said about how a form reads is
judgment: no reading evidence was gathered.

Terms: a **choice** is a point where a truth value decides which of two
taught bodies runs. A **draw** is what `ask maybe` answers.

## The questions, and what is recommended

| # | Question | Recommended | Note |
|---|---|---|---|
| D1 | How a truth value chooses | **A truth value hosts taught messages,** as a proto does: `true ask word is 1` | No word is added and none is reserved: choice is dispatch |
| D2 | Which values can be taught | Protos and the two truth values | Not numbers |
| D3 | The built-in words on a truth value | Found first, and they cannot be taught on a truth value | `equals`, the logic words, `maybe`, `value` |
| D4 | A truth value that was not taught the message | Refused at the send: *false was not taught "word"* | Teaching one truth value does not teach the other |
| D5 | A choosing word supplied by the language | None | A program teaches its own |

## What forces it

1. **A truth value decides nothing.** Five things in the language answer
   one: `ask maybe`, `inherits`, `equals`, the logic words and the
   literals. A truth value can then be printed, named, compared and
   combined, and the last two only answer another truth value. Nothing a
   program does next depends on one (`model.md`, "What the core is, and
   what a program reaches").
2. **A taught body does the same thing each time it runs.** What differs
   between two sends comes only from who was asked and what was given.
   So a body that sends its own message can never stop:
   `box ask loop is ask loop` is refused as *message recursion too deep*
   (*measured*), and so is every other body that repeats.
3. **The machine's dynamics have no use in a program.** A draw is the
   one thing a program gets from them, and a draw is a truth value.

## What the grammar already settles

Three facts about moop as ruled fix the shape of any choice that keeps
the grammar. Each was checked on 0.10.0.

1. **In a body, a computed truth value can only be the receiver of the
   next send.** A chain's value is used by the rest of its chain, or it
   answers the sender, where the same holds. It cannot become an
   argument, because an argument is a term (`arguments.md`, Q4). It
   cannot be named, because a body holds no `is` (*definitions cannot
   nest (yet)*). At the top level a truth value can be named, and a name is a
   term; but the top level does not repeat.
2. **Only a taught body waits to run.** An argument is evaluated before
   its message is dispatched, and no value holds code. So choosing
   between two values that are both already computed cannot end a
   repetition. A choice has to select which body runs.
3. **A send gives one term.**

So a choosing send is `truth ask word` or `truth word term`, with the
truth value as its receiver, and what it selects is a taught body. The
open part is who says what the word does: the language, or the program.

## Can choice be derived away?

The deletion test asks whether a uniform rule already present covers
every use. The candidate is dispatch. *Which body runs is decided by who
is asked* is already moop's one way of selecting behaviour: a child
overrides its parent by it. It covers choice as soon as the two truth
values can be asked, that is, as soon as a truth value hosts taught
messages.

- **No silence.** A message a truth value was not taught is refused, as
  now. Teaching one truth value leaves the other refusing.
- **No ambiguity.** `receiver … is chain` keeps its one meaning: it
  teaches.

So a construct for choice is redundant. What choice needs is the removal
of a restriction, *only protos host messages*, and the interpreter
already words that restriction as provisional: a message sent to a truth
value is refused as *only protos host messages (yet)*.

## D1 — how a truth value chooses

| Option | What it is | Verdict |
|---|---|---|
| **Taught truths** | A truth value hosts taught messages, as a proto does. No word is added | **Recommended.** Choice is dispatch |
| `then` and `else` | Two built-in words. `t then x` answers `x`, or passes `false` along; `v else y` answers `y` for `false`, and `v` otherwise | One form, two meanings: `true then false else true` answers `true` (*measured*) |
| `keeps` | One built-in word. `t keeps p` answers the proto `p`, or its parent when `t` is false | Works (*measured*). The word and its meaning are chosen, not forced |
| Cases by argument | A literal where a teaching's parameter stands: `box go true is 1`, `box go false is 0` | The truth value would be the argument, and in a body a computed one cannot be (fact 1, above). It could choose only at the top level. Not built |
| Fixed messages | A built-in word that sends its argument `yes` or `no` | The language would own two message names in every program. Not built |
| Truths as protos | `true` and `false` become two protos | A birth from a truth value, a body for one, and `maybe` and `mirrors` on one all stop being refused. Not built |
| New grammar | A conditional statement with nested blocks, or a three-part form `t then a else b` read as one operator | Needs the grammar to grow and words to be reserved. Not built |
| No choice | moop stays as it is | Costs nothing; the three points under "What forces it" stay |

### Taught truths (recommended)

**The rule.** A truth value hosts taught messages. `true ask m is chain`
and `false m p is chain` each teach one truth value, in one line or as a
block. A message sent to a truth value is looked up among the built-in
words first, and then among what that truth value was taught.

Run on the prototype (the numbers depend on the wiring, as every draw
does; `→` marks what a line prints):

```
true ask word is 1
false ask word is 0
box is a world
box ask maybe ask word           → 0
box ask maybe ask word           → 1
2/3 equals 4/6 ask word          → 1
world inherits box ask word      → 0
```

A truth value given a proto can send it one of two messages, so one pair
of teachings serves every decision in a program:

```
true pick p is p ask yes
false pick p is p ask no
door is a world
door ask yes is 1
door ask no is 0
door ask maybe pick door         → 0
door ask maybe pick door         → 1
door ask maybe pick door         → 1
5 equals 5 pick door             → 1
```

And a repetition can end. Here a proto draws until a draw is true:

```
true again p is p
false again p is p try p
box is a world
box try me is ask maybe again me
box try box ask value            → 181
kid is a box
kid try kid ask value            → 189
```

The loop on `box` made two draws, the first false and the second true
(*measured*, by comparing the draws that follow with a session that
makes two draws by hand).

**Why it is derived.** Nothing is added: no word, no statement form, no
value kind. The teaching form, strict arity, re-teaching and the order
of dispatch are the ones already ruled. One restriction goes.

**Its cost.**
- **Hosting is no longer the protos' alone.** A truth value hosts
  messages and has no body, no births and no parent, so `maybe`,
  `value`, `mirrors` and `inherits` still refuse it.
- **A choice is spread over two teachings.** moop has no code as a
  value, so the two arms of a choice are two taught bodies, written
  apart from the place that chooses.
- **A missing arm is found when it is reached.** Teaching `true` alone
  is allowed, and `false` then refuses the message at the send.
- **A mistake can become an action in one case.** A message sent to a
  truth value by mistake is refused today whatever its name. It would
  run if the program had taught truth values a message of that name.

### `then` and `else`

`t then yes else no ask word` reads well (judgment), and it selects a
proto before anything is sent to it, so only one body runs. It fails on
what stands between the two words. `t then x` must answer something when
`t` is false, and with no new kind of value that can only be `false`
itself. Then a `then` arm that is `false` cannot be told from a choice
not yet made:

| Line | Meant | Answered (*measured*) |
|---|---|---|
| `true then true else false` | true | true |
| `true then false else true` | false | **true** |
| `false then true else false` | false | false |
| `false then false else true` | true | true |

It also makes `else` a built-in word on every kind of value, since
`v else y` must answer `v`. *Measured:* `box else 5` and `5 else 6`
answer where they are refused today, and a proto taught its own `else`
loses it: `box else 5` answers the proto where today it is refused as
*else takes nothing*. That is silence. A new kind of value, meaning "not
chosen", would remove the ambiguity and add a concept with its own
printing and equality.

### `keeps`

A proto already stands for a pair: itself and its parent. `t keeps p`
answers `p` when `t` is true and `p`'s parent when it is not, so the two
arms are an override and what it overrides. *Measured:* it works, and
`false keeps world` is refused, since a root has no parent.

It needs no change to hosting. But nothing forces this word or this
meaning, the two arms must be a child and its parent, and the reading is
not one a newcomer would guess (judgment). Taught truths dissolve it: a
program that wants it can teach truth values a word of its own.

### New grammar

A three-part form, `t then a else b`, read by the parser as one
operator, has no value in the middle and so no ambiguity, and it reads
best of all the options (judgment). A conditional statement would need
blocks inside blocks. Both need the grammar to grow, which is not
authorized (`arguments.md`), both reserve words, and the three-part form
would be the only operator that relates three things.

### No choice

moop can stay as it is: a small language of objects on a reversible
body, whose taught bodies are straight lines. Programs that decide would
be written in Selvage, which has `if … otherwise` and rules written as
clauses. This is a coherent
position and costs nothing. Its price is the three points under "What
forces it": truth values stay answers that nothing uses, no repetition
can end, and a draw steers nothing.

## D2 — which values can be taught

**Recommended: protos and the two truth values.** A truth value can be
taught because each one can be named, and teaching both covers every
truth value there is.

The same rule would reach numbers one at a time: `0 ask fact is 1`. Not
recommended. It gives cases with no general case, since no form names
every number. And `n equals 0`, followed by a message to the truth value
it answers, already decides each case, so the deletion test dissolves
it.

## D3 — the built-in words on a truth value

**Recommended: built-in words are found first, and cannot be taught on a
truth value.** `equals` is innate on every kind, and `and`, `or`,
`nand`, `nor` and `xor` are built in on truth values. A teaching of one
of those names on a truth value would never run. Storing it would be
silence, so it is refused: *and is built in on truth values*. `maybe`
and `value` stay innate names that no teaching may take, and asking a
truth value for either is refused, since it has no body.

The logic words stay unreserved: a proto may still be taught its own
`and`.

## D4 — a truth value that was not taught the message

**Recommended: refused at the send, naming the truth value and the
message:** *false was not taught "word"*. Nothing falls back from one
truth value to the other, and no default is supplied. This replaces
today's *a truth value answers and, or, nand, nor, xor and equals, not
"word"*.

## D5 — a choosing word supplied by the language

**Recommended: none.** `pick`, `yes` and `no` above are the program's
own words. A word supplied by the language would be a name chosen by
fiat in every program, which is what Q5 declined for the logic words
("no word is reserved"). The documents can show the `pick` idiom, as
they show `mirrors 0`.

## What it compounds with

- **`maybe`.** A draw can steer a program, so the machine's dynamics get
  their first use in one. The open question in `model.md`, whether
  `maybe` should become a two-place word that chooses between its
  operands, would be answered: it need not.
- **`equals`, `inherits` and the logic words.** Every source of a truth
  value becomes a way to decide.
- **Arguments (0.8.0).** The one term names what to act on. Strict
  arity, parameter binding and re-teaching are reused unchanged.
- **Arithmetic (Stage 3).** `n equals 0` becomes a decision, which is
  what lets a count end.
- **The layer rule.** Untouched. A teaching on a truth value is a chain
  in user memory, and nothing reaches the tapes.
- **Certified mirrors.** Untouched. A forward that sends to a truth
  value is not a chain of F11 steps, so the derivation refuses it as it
  refuses any other body.
- **Selvage.** Selvage chooses with `if … otherwise` and with clauses,
  and moop would choose by dispatch: each by its own mechanism, neither
  copied from the other.

## Limits that remain

These hold for every option that keeps the grammar. Both were measured
on the taught-truths prototype.

- **A body cannot hand its receiver on.** The receiver is not a term, so
  it cannot be an argument. A body that names a proto acts on that
  proto, whoever was asked:

  ```
  true again p is p
  false again p is p ask try
  box is a world
  box ask try is ask maybe again box
  kid is a box
  kid ask try ask value            → 220, the value of box; kid's is 246
  ```

  The way round it is to hand the receiver in, as `kid try kid` does
  above. It has the same root as Q3: the receiver has no name.
- **A computed value never becomes an argument in a body.** So a body
  cannot hand on what it has just worked out, a proto included. It can
  only send to it.
- **Repetition is recursion, and recursion is 32 sends deep.** A loop
  that takes two sends a round is refused after 16 rounds (*measured*:
  it had made 16 draws, and they stand). Today only a program that never
  ends meets that limit. With choice, a correct one can.
- **Before Stage 3 a program cannot count.** Choice lets it steer by
  draws, lineage and equality, and repeat until one of them changes.

## What the prototypes showed (measured)

Each prototype is a copy of 0.10.0 with `src/eval.c` changed and nothing
else: no lexer or parser change in any of them. None is kept in the
repository.

| Prototype | Lines of `eval.c` | Smoke checks | C checks | Notes |
|---|---|---|---|---|
| Taught truths | 56 added, 10 removed | 126 of 127 | 102 of 102 | The one check that differs is the wording of D4's refusal |
| `then` and `else` | 9 added | 127 of 127 | 102 of 102 | One of the four truth cases answers wrongly; three forms refused today answer |
| `keeps` | 17 added | 127 of 127 | 102 of 102 | `false keeps world` refused: no parent |

On the taught-truths prototype, also *measured*:

| Line | Answer |
|---|---|
| `false ask word`, with only `true` taught | *false was not taught "word"* |
| `true and x is 5` | *and is built in on truth values* |
| `true ask value is 3`, `true ask equals is 3` | *value is innate*, *equals is innate* |
| `true ask maybe` | *a truth value has no body: maybe is asked of a proto* |
| `true word 5`, with `word` taught as taking nothing | *word takes nothing: ask word* |
| `true ask again`, taught as `ask word` | 1: a headless chain addresses the truth value |
| A block taught on `true`; `true ask word` taught again | The block's last line answers; the new teaching replaces the old |
| `inherits world` and `mirrors 0` in a truth value's body | Refused, as for any truth value |
| A truth value from a name, from a parameter and from `true xor false`, then `ask word` | Each answers what that truth value was taught |
| `5 ask word`, `a true`, `true is 5`, `5 mirrors true` | Refused, as now |

## Not proposed

- Lazy arguments, code as a value, or names local to a body.
- Grouping, a receiver keyword, or any change to the grammar.
- A conditional statement, or `then` and `else` as words.
- Numbers that host messages, or a way to teach every value of a kind.
- A construct for repetition, a deeper recursion limit, or sends that do
  not nest. Choice will press on the limit; lifting it is its own
  question.
- A two-place `maybe`.

## If D1 to D5 are adopted

Adoption would settle the design. Building it would be a change of its
own, authorized separately, as arguments were. It would have to show:

- teaching on `true` and on `false`, with and without a parameter, in
  one line and as a block, and re-teaching;
- dispatch on a computed truth value from each source: a draw,
  `inherits`, `equals`, a logic word, a literal, a name and a parameter;
- strict arity, both ways round;
- every refusal in the tables above, and that `true is 5`, `a true`,
  `5 mirrors true` and a message to a number are refused as now;
- a program under `tests/programs/` with an `.out` that does not depend
  on the wiring, and one that steers by a draw;
- that a copy with the lookup broken, or with one truth value's
  teachings answering for the other, fails those tests.

`language.md`, `syntax.md`, `model.md` ("What a draw can be used for")
and `CLAUDE.md` would change with it.
