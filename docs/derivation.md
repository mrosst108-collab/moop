# moop is a derived language

"Derived" is true of moop in four senses, at four different levels, and
the senses reinforce each other. This document records the
understanding; treat it as methodology, not history.

## 1. Derived from principles, not assembled from features

Most languages are assembled: features are chosen, collected, and made
to coexist. moop is derived: every construct must be *forced* — or at
least strongly suggested — by the axioms (naturalism, minimalism
through synergy and orthogonality, the reversibility/homoiconicity
pair) acting on what already exists. The git history is a chain of
derivations, and reads like one:

- Homoiconicity **forced** the symmetric gate wiring: the original
  wiring made loop B a read-only program tape, and the axiom rejected
  the implementation. The design pushed back on the code.
- The segregation axiom **derived** the bridge shape (reversible effect
  inside, irreversible observation outside), and everything that later
  crossed the boundary — MAYBE, actors, generation — had to arrive in
  that shape.
- The involution requirement **derived** the `<->` forms: only
  operations that are their own inverse could give "bijective" as a
  tested fact rather than a promise.

Derivation also runs in reverse: constructs get **derived away** when a
uniform rule is found that covers every use. `self` dissolved into the
headless chain ("every context has a receiver"); `generate` dissolved
into the indefinite article ("introduction is instantiation"). The
working rule — call it the **deletion test**:

> A construct is redundant iff a uniform contextual rule covers all its
> uses without creating silence (mistakes becoming actions) or
> ambiguity (one form, two meanings). If such a rule exists, the
> construct must go; if none exists, the construct has earned its name.

`self` failed the test and died; `generate` failed it once the article
was seen; `is`, `ask`, `inherits`, `mirrors`, and the article itself
have all survived it.

## 2. Derived from ancestors, without delegating to them

moop's parents are Quorum (Stefik: evidence-based naturalism) and Io
(Dekorte: tiny-core prototype minimalism), with reversible computing
(Toffoli, Bennett, Landauer) as the substrate tradition. But moop
relates to its ancestors the way its own actors relate to theirs:
**non-hereditarily**. It does not delegate to a parent — no feature is
present *because* a parent has it. What it takes, it takes
constitutionally, re-derived from its own substrate:

- From Io it re-derived prototypes, messages, and differential
  inheritance — but declined `clone` (moop births are seeded from the
  generator's dynamics, not copied), declined re-parenting (lineage is
  physics), and ultimately declined `self` (Io's own word).
- From Quorum it re-derived word-operators and the evidence standard —
  and followed Quorum's deepest precedent (no `new`; introduction
  instantiates) to a place Quorum itself never took it: the indefinite
  article as the creation form.

A test that a borrowing was re-derived rather than copied: moop can
explain each one in its own terms, without citing the ancestor.

## 3. Derived at runtime: every object is a derivation

Nothing in a running moop system exists ex nihilo. The generative chain
— system actor → system root → world → protos all the way down — means
every body's birth state is a deterministic function of its generator's
dynamics at the moment of birth. An object is not a blank allocated
thing; it is a *derivative* of its generator, and the derivation is an
information-preserving act (the generator can step back to before the
birth). The language's own vocabulary agrees: `a dog` does not "make"
or "allocate" — it derives a new thing *from* dog.

## 4. Derivable pasts: every state derives its own history

Causal closure — the reversibility × homoiconicity synergy — means a
moop state is not a brute fact but a **conclusion whose premises are
recoverable**: run backward and the program that produced the state is
derived from the state itself. Provenance needs no pointer, no log, no
metadata; derivation is the machine's native direction, both ways.
Causal pruning is then exactly the discharge of premises that were
never used in any inference — the one sanctioned act of forgetting,
performed only on what provably contributed nothing.

## What this demands of future work

Derivation is an obligation, not a compliment. A proposed feature must
present its derivation: which axiom or existing mechanism forces it,
what it compounds with (synergy), what single job it owns
(orthogonality), and why the deletion test does not dissolve it into
something already present. A feature that cannot answer is not rejected
as *bad* — it is rejected as *underived*, and may return with a better
proof. When an axiom and an implementation conflict, the implementation
loses (see the wiring). When a uniform rule is found that covers a
construct, the construct goes (see `self`, `generate`).

The aspiration, honestly held: that the whole language should feel, to
someone who has understood the core, like something they could have
derived themselves — and that anything they *couldn't* have derived is
either documented as an open question or is a bug in the design.
