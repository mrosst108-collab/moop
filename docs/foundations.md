# Shared foundations: reader, values, numeric messages, certified transformations

**Status: adopted in principle on 2026-11-18, with qualifications.**
This text carries those qualifications. The decisions are to be entered
as ratified once this wording is confirmed and the four points under
*Not yet ruled* are settled. **Nothing is implemented**, and each
realization needs its own authorization.

The ruling covered the common architecture, and it keeps the fourteen
decisions as separate entries so that approving one does not blur
another. Wiring 2 stays independent and gated. Reflection stays
deferred as a user-facing capability.

## The criterion

Each decision answers one question: **does it create a reusable
capability that makes other capabilities simpler, rather than a
mechanism used once?**

| Capability | What it reuses |
|---|---|
| Comments | the existing reader |
| Truth literals | the existing truth values |
| Arithmetic | the argument and message machinery of 0.8.0 |
| Equality and printing | two protocols shared by every value kind |
| Certified mirrors | the existing chain grammar and the word `mirrors` |
| Re-deriving a mirror at each send | the nearest-teaching lookup already ruled for arity |

That synergy is not a licence to expand. Text and user-facing reflection
stay deferred.

## Numbering

The rulings were made on a summary and numbered by topic. This document
now follows that numbering. The draft numbered differently:

- its F5 (number literal forms) and F11 (the form that defines a mirror)
  are not covered by the rulings, and are listed under *Not yet ruled*;
- its F14 (the domain) is replaced by the partial-bijection
  qualification on F11 to F14.

## The fourteen decisions

| # | Decision | Ruling, 2026-11-18 | As recorded |
|---|---|---|---|
| F1 | `;` comments | Adopted | **Full-line comments only.** A line whose first non-whitespace character is `;` is a comment, and the whole line is ignored. Comments on the same line as code are not part of this decision: a `;` after code stays a stray character, and the line is refused |
| F2 | Comment lines and blocks | Adopted | A comment line is set aside before indentation and blocks are considered. It does not run, does not open or close a block, and its indentation never triggers the refusal of an indented line under no open block. Inside a block it leaves the block open, even when the comment line is not indented |
| F3 | Blank lines | Retained | A blank line still closes a block |
| F4 | Rational values | Adopted, with a qualification | Exact, canonical and **bounded** (below) |
| F5 | Overflow and division by zero | Adopted | Refused. Never wrapped, rounded or saturated |
| F6 | Truth literals | Adopted | `true` and `false` are reserved literals denoting the existing truth values |
| F7 | Text | Deferred | No text-literal syntax now (below) |
| F8 | Round-trip printing | Adopted | *Every implemented literal value has a canonical representation that can be read back as an equal value* |
| F9 | Equality | Adopted, with a qualification | One `equals` protocol, with semantics defined for each value kind (below) |
| F10 | Arithmetic | Adopted | Messages on numbers, not new infix operators |
| F11 | Arithmetic inverses | Adopted, with a qualification | Only mathematically invertible steps (below) |
| F12 | Chain inversion | Adopted | Reverse the chain and invert each step |
| F13 | Dynamic derivation | Adopted | Derive the mirror from the current nearest teaching, at each send |
| F14 | Mirror involution | Adopted, with a qualification | The mirror of a mirror restores the original, **under an unchanged teaching environment** |

### F1 to F3: one reader, two kinds of line that do not run

A blank line and a comment line both run nothing, and the reader treats
them differently on purpose:
- a **blank line** closes an open block;
- a **comment line** is set aside before blocks are considered, so it
  changes nothing.

Comments add this second kind of line; they do not remove the
blank-line question. The draft said they did, and that is corrected. A
body still cannot hold a blank line.

- **Why `;`.** moop's own documentation already writes its notes that
  way. One of its examples, `docs/syntax.md` line 100, is a comment-only
  line inside an open block, and under F2 it runs. The other example
  notes sit after code on the same line, so under F1 they remain prose,
  not moop.
- **Why a blank line still closes.** If a block closed at the first
  unindented line, a body line whose indent was forgotten would end the
  block silently and run against the world: a mistake becoming an
  action. With a blank line as the close, that line is refused.
- **What forces comments.** A program read by people cannot explain
  itself, and nothing present can carry an explanation: a value on a
  line of its own would print, and binding it to a name adds a name.
- **Comments are not data.** A taught chain holds none.

### F4 and F5: bounded exact rationals

A number is a rational **p/q** in canonical form:

- q > 0 and gcd(|p|, q) = 1, so zero is 0/1;
- **|p| ≤ 2⁶³ − 1 and 1 ≤ q ≤ 2⁶³ − 1.**

That is a finite subset of ℚ, not ℚ itself. "Exact" means exact
representation, not unbounded representation: arithmetic is not closed
on this set, so every operation is partial on it. A result is exact
whenever it is representable, and refused when it is not.

**Proposed precision for F5: refuse exactly when the reduced result does
not fit.** An operation is refused when its exact result, in lowest
terms, falls outside the bounds above, and for that reason only.
Division by zero is always refused. Three reasons:

- **No needless refusals.** With 64-bit temporaries, even with
  cross-cancellation, an operation can be refused although its result
  fits. `4000000000000000001/2 plus -6000000000000000001/3` is exactly
  1/6, yet the 64-bit prototype refused it, as it refused 2 of 3,985
  operations drawn near the bounds. With 128-bit intermediates the
  prototype followed this rule exactly in all 3,985 (*measured*).
- **One answer.** The rule depends on the value, not on how it is
  computed, so every implementation gives the same refusals and
  conformance tests can be exact.
- **It makes F11 to F14 precise** (below).

**Implementation note, not a language rule.** Checked arithmetic goes
through a small portability layer:
- `__int128` (as `__extension__`, so `-Wpedantic` stays quiet) works in
  GCC 13 and Clang 18;
- C23's `_BitInt(128)` and `<stdckdint.h>` work in Clang 18 but not
  GCC 13, so the language does not depend on them.

The layer is tested on its own.

A body still carries whole numbers from 0 to 255. Depositing a fraction
or a negative number is refused, as an oversized one is now.

### F6: truth literals

`true` and `false` are reserved, and denote the truth values moop
already has; there is no second boolean type.

- **Why not names bound at startup**, as `world` is: a name can be
  rebound, and `true is false` would break F8.
- **The logic words stay messages.** Reserving these two values does not
  reserve `and`, `or`, `nand`, `nor` or `xor`.

### F7: text, deferred

No text syntax is chosen now, delimiter included. F1 does not force one,
since a full-line comment rule cannot meet a `;` inside a literal. Text
returns when a second substantial consumer exists, as one immutable
value with an explicit encoding, length, escaping, equality, and
printing that reads back. Until then F8 and F9 say nothing about text.

### F8 and F9: printing and equality, the value protocols

- **F8 applies to every implemented literal value:** numbers and truths
  now, text when it exists. A proto is not a literal value and prints as
  `a proto`, as now.
- **F9:**
  - **Numbers** are equal when numerically equal, whatever their
    spelling (`2/3 equals 4/6` is true).
  - **Truths** are equal when they are the same truth value.
  - **Text**, when introduced, will compare by its specified contents.
  - **Different kinds are unequal,** even when their printed forms look
    alike. That is an answer, not a refusal.
  - **Protos:** equality is never structural, and its semantics are
    defined separately (*Not yet ruled*, U4).

The 702 print-and-read-back checks the prototype passed are evidence,
not conformance; the boundary tests listed below are the conformance
requirement.

### F10: arithmetic as messages

Arithmetic extends the message grammar. The adopted argument mechanism
already supplies the dispatch form, parameter binding, eager evaluation
and receiver-first order, so there is no arithmetic parser and no infix
operator:

```
c times 9/5 plus 32
```

- **No precedence.** Chains read left to right, so `2 plus 3 times 4`
  is 20. That cost against school arithmetic is stated, not hidden;
  naming an intermediate result writes anything else.
- **Negation** is `0 minus x`.
- **Refusals:** overflow and division by zero (F5), and an argument
  that is not a number.
- **Not reserved:** the arithmetic words are messages.
- **Layer:** these are user-layer operations, since as two-place
  functions they lose information.

The word for division is not yet ruled (U3). *divide* stands for it
below.

### F11 to F14: certified mirrors

**F11: the steps that can be inverted.**

| Forward step | Inverse step | Condition |
|---|---|---|
| plus n | minus n | always |
| minus n | plus n | always |
| times n | *divide* n | n ≠ 0 |
| *divide* n | times n | n ≠ 0 |

Multiplication by 0 is ordinary arithmetic, but it is not invertible,
so it is never a certified step. `equals` observes and transforms
nothing, so it is never a step. A step's argument must be a number
literal:
- a name could be rebound between the two directions;
- the parameter itself would make the step read the value it changes,
  as `c times c` does.

**F12: inversion.** The mirror of a certified chain is the same steps in
reverse order, each inverted: the mirror of `c times 9/5 plus 32` is
`f minus 32` then *divide* `9/5`.

**F13: derivation at each send.** The mirror is derived from the
forward that the receiver's lineage gives at that moment, which is the
same nearest-teaching lookup ruled for arity. Deriving once would leave
the mirror out of date after a re-teaching: a stale inverse that still
answers. A child that re-teaches the forward gets its own mirror; the
parent's is unchanged.

The boundary on reflection:
- the implementation may traverse a taught chain internally to derive a
  mirror;
- returning a taught chain to a program as a value is still
  unauthorized;
- so is editing or running a reflected chain.

**F14: involution.** The mirror of a mirror restores the original as
long as the teachings involved are unchanged. If a relevant teaching
changes, later derivations use the new one; nothing is cached.

**The partial-bijection qualification, on F11 to F14.** Over ℚ,
F(C) = 9/5·C + 32 and C(F) = 5/9·(F − 32) are inverses. Over the
bounded set of F4 the claim is narrower:

> The realized transformation is a partial bijection over the
> representable values for which its forward steps succeed, with its
> inverse defined over the resulting image.

**Proposed sharpening, which holds under the exact refusal rule of F5.**
The mirror is defined on the forward's image and nowhere else. Let D be
the representable inputs on which every forward step succeeds.
- **Forward then mirror.** For x in D, each step of the mirror applied
  to f(x) reproduces one of the forward's intermediate values, in
  reverse. Those values are representable, so no mirror step refuses,
  and the mirror gives x back.
- **Mirror then forward.** Symmetrically, if the mirror succeeds on y,
  the forward succeeds on its result and gives y back.

So the forward is a bijection from D onto its image E, and the mirror is
exactly its inverse: defined on E, refused outside it.

The argument needs refusal to depend only on values. With
implementation-dependent temporaries, a mirror could refuse a point of
the image that the forward reached. No such case appeared in 1,000
probes with either prototype (*measured*), but under the exact rule none
can occur.

Lossy transformations stay distinct. They are ordinary teachings, and
they have no mirror.

## Not yet ruled

These were in the draft and are not covered by the rulings above. Each
needs a ruling before the wording is ratified or the affected step is
realized.

**U1. Literal forms for fractions and negative numbers.** F8 requires
that a computed 9/5 or −7 read back as an equal value, so some readable
form must exist.
- **The draft:** literals `9/5` and `-7`, with no spaces, read in lowest
  terms. `-` followed by a digit cannot be confused with `->`.
- **The alternative:** print them as chains that compute them, `9 over
  5` and `0 minus 7`. That needs no new lexical form, but a printed value
  is then not a literal, and negatives read badly.
- **Recommended:** the literals.

**U2. The form that defines a mirror.** The draft proposes
`world celsius mirrors fahrenheit`, which teaches `celsius` as the
mirror of `fahrenheit`.
- *For it:* the shape is refused today, since a message in operator
  position needs an argument, so it gives no existing line a new
  meaning. `mirrors` keeps its one job, an information-preserving
  correspondence. F14's involution law matches the existing law of
  `mirrors`.
- *Against it:* it is a new statement shape, and the 0.8.0 ruling
  authorized no further grammar expansion. So it needs a ruling of its
  own.
- *Declined alternatives:*
  - writing both directions and having moop verify they are inverses,
    which duplicates the work;
  - an operator that sends a message's inverse with no name for it,
    which needs message names as values, that is, reflection.

**U3. The word for division.**
- *The draft:* `over`, as in `c over 5`, which reads like spoken
  arithmetic.
- *Your table:* `divide`. `c divide 5` reads as a command, and
  `divided_by` would be two words joined.
- **Recommended:** `over`, but the choice is yours, and nothing above
  depends on which.

**U4. Proto equality.**
- *The draft:* identity. Two protos are equal only when they are the
  same proto, and the message is innate, so it cannot be re-taught.
  That is never structural, which meets F9's qualification.
- *Your ruling:* proto equality is defined separately.
- **Needed:** your confirmation of identity, or another definition.

## Conformance requirements for realization

The prototype's random-pipeline tests and its independent model in
Python fractions are kept. Each realization must also pass
deterministic boundary tests:

- **Reader:** a comment line inside a block, indented and not indented;
  a comment line under no open block; a blank line after a comment line;
  a `;` after code (refused).
- **Numbers:**
  - bounds: the largest and smallest numerators, the largest
    denominator, one past each (refused);
  - canonical form: zero as 0/1, negatives, lowest terms and spelling
    (`10/4` reads as 5/2);
  - refusals: division by zero, overflow at an intermediate step, and
    the needless-refusal case above (it must give 1/6);
  - printing: every boundary value reads back equal.
- **Arithmetic:** each message with negative operands, zero operands and
  operands at the bounds.
- **Mirrors:**
  - refusals: `times 0`, a name as an argument, the parameter as an
    argument, a body of more than one line, a message that takes
    nothing, a cycle, a missing forward;
  - forward then mirror, and mirror then forward, at the edges of the
    domain, and refusal outside the image;
  - re-teaching the forward after a mirror was used; a child's own
    forward;
  - the mirror of a mirror;
  - Celsius and Fahrenheit as the acceptance case: 100 to 212, −40 to
    −40, 98 to 110/3 and back.

## Realization order, each step authorized on its own

1. **Reader:** F1 to F3.
2. **Values:** F4 to F6, F8 and F9. Bounded exact rationals, the
   refusal rule, truth literals, equality and printing for the
   implemented kinds. U1 and U4 must be ruled first.
3. **Arithmetic:** F10. U3 must be ruled first.
4. **Certified mirrors:** F11 to F14, with Celsius and Fahrenheit as the
   acceptance case. U2 must be ruled first.
5. **Text:** F7, when a second substantial consumer exists.

## Prototype evidence (measured)

It was built on 0.8.0, outside the repository, and it is not proposed
as a patch. It implemented the draft rather than the rulings: inline
comments, a text literal, and the `over` and `mirrors`-definition forms
of U2 and U3. Its arithmetic was then rebuilt on 128-bit intermediates.

| Claim | Result |
|---|---|
| Existing checks | 92 of 93 pass. The one that changed is meant to: numbers now answer messages |
| Comment-only line in an open block (`docs/syntax.md` line 100) | The block stays open, and the example runs |
| Exact arithmetic, left to right | `2 plus 3 times 4` is 20; `1/3 plus 1/3` is 2/3; `10/4` reads as 5/2; `2/3 equals 4/6` and `1/3 times 3 equals 1` are true |
| The refusal rule of F5 | 64-bit temporaries: 2 of 3,985 operations near the bounds refused though their results fit. 128-bit intermediates: refused exactly when the reduced result does not fit, in 3,985 of 3,985 |
| Celsius and Fahrenheit | 100 to 212 and back; −40 to −40; 98 to 110/3 and back; the round trip from 37, checked with `equals`, is true |
| The mirror of a mirror | equals the forward, with teachings unchanged |
| Derivation at each send | after the forward is re-taught, the mirror follows it; a child's own forward gives the child its own mirror, and the parent's is unchanged |
| Random pipelines, 3 seeds | 1,200 forwards of 1 to 6 steps and 3,600 inputs. All 10,800 round trips hold, all 3,600 mirror values equal the independent model, and none is refused |
| Pipelines near the bounds | 1,000 probes on 40 pipelines. Wherever the forward succeeded (202 cases), the mirror gave the input back, with either kind of arithmetic |
| Printing round trip | 702 of 702 values read back equal |
| Sanitizers | the checks, the example programs and one seed of the random pipelines run clean under ASan and UBSan, after one prototype bug was fixed |

**What it does not show:**
- that these forms read well to people;
- that the bounds of F4 are large enough for the programs moop will
  have;
- anything about text, whose syntax is deferred.
