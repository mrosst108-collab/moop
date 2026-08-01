# ASDG / RME-7 — Specification

**Status: PARTIAL.** This file is the retrieval target named in §7 of the Rosst–CP Code Constitution
(`rosst-cp-v6.md`). Sections below are marked **[carried]** or **[unpopulated]**.

**[carried]** — transcribed verbatim or near-verbatim from Rosst–CP v5 §10. Provenance: the v5
constitution. Not independently verified against a primary ASDG source.

**[unpopulated]** — not supplied by any source available when this file was written. **Not omitted
for brevity, and not to be filled in from memory by a reader.** The constitution's own rule applies
here first: *reconstruction has a demonstrated failure record — invented levels, mistyped operators —
and a plausible reconstruction is worse than none, because it looks right.*

> **Gate.** While §3 (operator semantics) is unpopulated, **generator-equation correspondence cannot
> be claimed.** The canonical form in §2 may be read and cited; it may not be asserted as satisfied.
> Work at role-plus-constraint level or decline the instrument, and say which.

---

## 1 — The two instruments **[carried]**

**ASDG** is a grammar: a formal language for representing distinctions, relations, transformations,
and admissible compositions.

**RME-7** is the maximally expressive minimal format specified *within* ASDG for compressing
**dynamic systems**, holding the orthogonality of the distinctions their dynamics require. It is
neither a software notation nor an optional visualization. It is general-purpose **within that
domain**, and not a container into which anything may be put.

**RME-7 ⊅ ASDG.** The format is not the grammar that specifies it, and an instance of the format does
not become the grammar of the system it represents.

Reasoning may be treated as a dynamic system and compressed in RME-7 **where its state, generator
evolution, admissibility conditions, and stochastic or perturbative terms can be meaningfully
distinguished.** Where they cannot, the fit is asserted rather than found. Reasoning qualifies often;
it does not qualify automatically.

---

## 2 — Canonical form **[carried]**

```
dX_t = J♯(dH) − G♯(dH) − G̃♯(dΦ) + Σ·dW_t + F dt
dθ   = κ(θ, F) · F(X, θ, Φ) dt
```

The two-scale structure is the point: the first line evolves state, the second evolves what governs
the evolution. Collapsing them loses the distinction between a system that runs and a system that
changes how it runs.

---

## 3 — Operator semantics **[unpopulated]**

No definitions available for: `X`, `θ`, `Φ`, `H`, `J♯`, `G♯`, `G̃♯`, `Σ`, `W_t`, `F`, `κ`.

The symbols above are transcribed from the canonical form. Their **types, domains, admissibility
conditions, and composition rules are not supplied here.** Reading a plausible meaning off the
notation — `J♯` as a Poisson structure, `G♯` as a metric/gradient term, `Σ·dW_t` as additive noise —
is exactly the reconstruction the constitution prohibits, however natural the shapes look.

Populate from the primary ASDG source before any generator-equation work.

---

## 4 — ASDG grammar **[unpopulated]**

Primitives, well-formedness conditions, composition rules, and the specification relation by which
RME-7 is a format *within* ASDG are not supplied.

Consequence: the claim "RME-7 is specified within ASDG" is currently **[carried]** from v5 and cannot
be checked against this file.

---

## 5 — Correspondence levels **[carried]**

Two levels. They are not interchangeable, and the characteristic failure of this instrument is silent
promotion of the first to the second.

**Role-plus-constraint.** Operations are matched to operator offices and the carried constraints are
named. Establishes that the structure is present and what it holds.

**Generator-equation.** The equations are actually written and satisfied.

**Declare which level you are at whenever compressing reasoning.**

---

## 6 — Prior adjudications **[carried, partial]**

**Reasoning-as-dynamic-system, tested case.** Correspondence established at **role-plus-constraint**
level. **Generator-equation correspondence remains unestablished:** that case had no inverses to
support Hamiltonian flow. Scoped to the case tested — not a general theorem. Do not silently promote.

The finding is a limitation on that object, not an invalidation of the instrument: an instrument can
fail to fully model an object while still exposing useful structure in it. Six constraints were
carried at role-plus-constraint level.

**[unpopulated]** — the identity of the tested case, and the six carried constraints, are not recorded
here. Without them this adjudication can be cited but not reused as precedent for a new object.

---

## 7 — Retrieval cue **[carried]**

When a task involves something changing over time, adapting its own parameters, being held inside
constraints, or perturbed by what isn't modelled:

1. **What is evolving?** — the state.
2. **What governs the evolution?** — the generator and the admissibility horizon.
3. **What constrains or dissipates it?** — what converges, and what confines without converging.
4. **What remains stochastic, external, or unmodelled?**
5. **What modifies the generator, and what gates that modification?** — the two-scale structure. This
   is the one usually skipped.

Use the format where it clarifies structure. Do not force a representation that adds no information.
**No compliance is earned by using it, and no failure is implied by not using it.**

---

## 8 — Claim-level safeguards **[carried]**

1. **Formal expression does not itself promote status.** An expression copied from a specification may
   be anchored; one derived from anchored premises follows from them. Its formal character adds no
   warrant beyond the evidence supporting it. A transformation may be represented correctly while its
   premises are false, the implementation defective, the evidence thin, or the result locally
   incompatible.
2. **Analogy is not instantiation.** Software does not implement an operator because a transformation
   can be pictured as one.
3. **Load the specification; do not reconstruct it.**

When the instrument is used, keep apart **the object**, **the grammar** describing it, **the format**
compressing that description, and **the evidence** for claims about the object.

**Standing reference is not standing procedure.** Availability for retrieval is not an instruction to
deploy.

---

## 9 — Worked examples **[unpopulated]**

## 10 — Known failure cases **[unpopulated]**

Beyond the single adjudication in §6, no failure cases are recorded. The v5 constitution refers to a
"demonstrated failure record — invented levels, mistyped operators" without enumerating instances;
those instances are not available here.
