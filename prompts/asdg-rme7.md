# ASDG / RME-7 — Specification

**Status: PARTIAL.** This file is the retrieval target named in §7 of the Rosst–CP Code Constitution
(`rosst-cp-v6.md`). Sections below are marked **[carried]** or **[unpopulated]**.

**[carried]** — transcribed verbatim or near-verbatim from Rosst–CP v5 §10. Provenance: the v5
constitution. Not independently verified against a primary ASDG source.

**[relayed]** — transcribed from a relay recorded in `docs/crossing.md` (the entry is named at each
use). Provenance and status are the ledger's: `testimony` unless that entry says `re-derived`, and a
`[relayed]` section is never promoted to `[carried]` by transcription. The relay's own custody rule
applies — anchored in the Rosst register unless marked `[pending]`; relays assemble and criticize,
never adjudicate or promote.

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

**Correction [relayed, crossing entry 3].** The relay states the canonical form as

```
dX_t = J♯(dH) − G♯(dH) − G̃♯(dΦ) + Σ dW_t + F dt
dθ   = F(X, θ, Φ, κ, Ψ) dt
```

— κ and Ψ are *arguments* of F, and the product `κ · F` carried above from v5 is "a documented
realization variant", not the grammar. The two second lines are kept side by side because neither is
grounded here: the v5 line is carried on the constitution's authority, the relayed line on the
register's, and this tree can resolve neither. `Ψ` is defined by no source available here and is not
to be read off the notation.

---

## 3 — Operator semantics **[unpopulated]**

No definitions available for: `X`, `θ`, `Φ`, `H`, `J♯`, `G♯`, `G̃♯`, `Σ`, `W_t`, `F`, `κ`.

The symbols above are transcribed from the canonical form. Their **types, domains, admissibility
conditions, and composition rules are not supplied here.** Reading a plausible meaning off the
notation — `J♯` as a Poisson structure, `G♯` as a metric/gradient term, `Σ·dW_t` as additive noise —
is exactly the reconstruction the constitution prohibits, however natural the shapes look.

Populate from the primary ASDG source before any generator-equation work.

### 3.1 — Offices **[relayed, crossing entry 3]**

The relay supplies the *office* of each primitive — its job in the signature — and nothing more:

| primitive | office |
|-----------|--------|
| `J♯` | conservative circulation |
| `G♯` | dissipative; the only office that converges |
| `G̃♯` | symplectic confinement of Φ to its level sets (`G̃♯* = −G̃♯`); not dissipative |
| `Σ` | stochastic driving — `Σ_ii` intra-track, `Σ_ij` port coupling |
| `F` | generator-level self-modification (adaptation of θ) |
| `κ` | integrity gate: what may modify the generator. Two sites, `κ_F` (generator) and `κ_Σ` (port) — a site distinction; their identity is open, not decided by notation |
| `γ = [G♯, G̃♯]` | derived endomorphism — not an operator, not itself an observable |

An office is a role. It is not a type, a domain, an admissibility condition, or a composition rule,
so **§3 remains unpopulated and the gate above stays down.** `X`, `θ`, `Φ`, `H`, `W_t` and `Ψ` are
still undefined. The γ row is the one office this tree has independently: it agrees with
`bookended-thinking/ontology/rme7_objects.yaml` (retrieved before the relay). The relay's count —
"7 primitives, 6 operators", κ among the six — does *not* agree with that file, which types κ an
indicator and whose loader refuses a six-operator axis; see the ledger entry. Neither side is
promoted by the disagreement.

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

---

## 11 — Realization cards **[relayed, crossing entry 3]**

A card is a realization of the canonical form, not the grammar. **Standing instruction, verbatim:
do not expand the grammar from a card.** Track indices and the port factorization are realization
data.

### B.7 — multi-track, port-coupled (autopoietic-ecology regime)

Per track i ∈ 𝓘:

```
dX_i = ( J♯_i(dH_i) − G♯_i(dH_i) − G̃♯_i(dΦ_i) ) dt + Σ_ii ∘ dW_i + Σ_{j≠i} Σ_ij(X_j → X_i) ∘ dW_ij
dθ_i = κ(𝒯_i; φ_i) · F_i(X_i, θ_i, Φ_i) dt
Σ_ij = A_i ∘ κ_i ∘ T_ij        (adapter ∘ gate ∘ translation)
```

Signature ⟨J♯, G♯, G̃♯, Σ, F, κ, γ⟩. Card conditions: block-diagonal offices; `G♯_ij = 0` held
throughout the trace, not only at endpoints (optimization stays local); cross-track relation carried
on the ports `Σ_ij`; Stratonovich; `F_X = 0` in this realization.

The relay's claim for the format: minimal because the six non-derived components carry independent
distinctions and compression never merges two (orthogonality is the minimality criterion);
expressive because it makes first-class what engineering notation leaves implicit — state ≠
parameter, execution ≠ adaptation, adaptation ≠ governed evolution, local dynamics ≠ cross-object
coupling, stochastic perturbation ≠ structural memory, object ≠ composition, realization ≠
representational grammar. RME-7 heads a family RME-4 → RME-7; the family is a classifier, not a
regime ladder. The strength of the claim is not that conventional notation cannot express these
phenomena but that RME-7 makes the distinctions first-class, and that the value of doing so is
testable — ρ_rel, an answer-to-question ratio against a fixed, executed sota baseline — rather than
inherited. Unparameterized, RME-7 is qualitative; parameterization yields the quantitative instance.

**Parked here:** no executed baseline exists in this tree, so ρ_rel is a claim about a measurement
nobody has made — the same class `bookended-thinking` stamps `COHERENCE_ONLY`.

---

## 12 — Use as the structure of an object framework **[relayed, crossing entry 3]**

Rosst objects are *expressed in* RME-7, not produced by it: U₁, U₂ ⊆ Expr(RME-7). The format neither
generates the objects nor sits above them; "U₁ → U₂ → RME-7" is not to be written, even as a
dependency chain.

| handle | meaning |
|--------|---------|
| track i | one object's state `X_i` and generator `θ_i` |
| U₁[𝒮] | qualified persistence on a track — a trajectory fact indexed by its solution set; "emergent" only when the route is exhibited, else "persists" |
| port `Σ_ij` | a typed relation between objects — adapter, gate, translation |
| U₂ | the composite: a gluing of qualified objects along the coupling graph (a colimit only if the interface algebra is shown to be a category) |
| coordinate office | a supplied carrier — M₁₁₂ or an ordinary frame; invariant office, swappable occupant |
| Del(U₂) | typed predicate over composites, not a fifth object: G♯ cross-terms vanish, permitted cross-sector relation sits in G̃♯, κ governs admission, witness preserves provenance |
| capture | the failure condition: `G♯_ij ≠ 0` — one sector's objective forming the other's ends |
| N(U₂) = ⋃N_i ∪ N_𝓘 | negative space, two grains: refused ports vs absent ports — **[pending]** |
| flux / veil / witness | := `T_ij` / `κ_i` / `A_i`, channel lexicon — **[pending]** |

`[pending]` rows are recorded, not adopted: nothing in this tree uses the lexicon, and the negative
space is realized below under the relay's grains without claiming the item is ratified.

**What a framework built on this must make machine-checkable** (relay, verbatim): what an object is,
where it is located, what claims are licensed, what promotion would be a category error — object
card, operation algebra, answerability domain, lifecycle with *located* before *warranted*.

**How this tree realizes it** (`src/rme7.{h,c}`, `docs/model.md`): the port is not a new mechanism —
moop's `<->` is already translate ∘ refuse ∘ deposit. The framework's handles are protos: the world
generates `port`, which generates one proto per primitive, and `port` hosts four exclusive verdicts
(`admitted` / `refused` / `absent` / `open`) answering whether a cross-track port of that primitive is
admitted. Σ and κ admitted; G♯ refused (capture); J♯, F, γ absent; G̃♯ open. The derivation is the
deletion test, recorded in the ledger. The verdicts are the negative space with both grains filled;
`refused` vs `absent` is exactly the pending distinction, exercised without being ratified.

**Guards, verbatim:** object ≠ coordinate space ≠ representation format · representation format ≠
quantitative realization · office ≠ carrier ≠ theory · localization ≠ derivation · exhibited ≠
inserted · signature typing ≠ localization ≠ realization-level observable · derived ≠ ruled ≠ RUN.
