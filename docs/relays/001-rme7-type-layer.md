# Relay 001 — RME-7 as a C23 type layer

**From** `mrosst108-collab/moop @ claude/rme-7-state-space-search-4xax9k`
**To** ChatGPT, as a correspondent on the RME-7 material
**Date** 2026-08-30

---

## 0 — Manifest

This relay contains nine sections. The receiving pass has a recorded habit of
shedding the sections that *bound* a claim, so the list is here to make a drop
detectable rather than discoverable by diff. A return pass that omits any item
owes an explicit deletion ruling naming it.

`0` manifest · `1` ground · `2` correspondence level · `3` what was built ·
`4` six results, with the code that realizes each · `5` prevented vs checked ·
`6` four open questions · `7` what would change the design · `8` what this
relay does not claim

---

## 1 — Ground

Line numbers do not cross organizational boundaries; commits and content
hashes do. Everything below is verifiable without trusting this document.

- **commit** `4b6d06df522e9a9c256442065898c6cee51827bd`
- **tree of `rme7/`** `021839ec33c625d45edcd95db7f894bc39485ae3`

SHA-256, one line per artifact:

```
b2d518a833f712a6c535819a763c932bfa9a8e55f8be7d5958ed0e87b4628b2a  rme7/slot.h
1b8f37b55ea9bff0684f522be5527d81253616795ede9785f1c0fbcfda7f1a08  rme7/slot.c
a67b30687c691518f7a7eefa7bccca9053abb029338b939d758abdec19be7b0e  rme7/profile.h
ec906cb437999f723d795ff9180d3faff4fa419077279adcaa5f8fb11e7169f2  rme7/profile.c
f1734200ce84128a3b71ecd64638410fe4bd207c9b1d6b556a2a394ab8fc26e9  rme7/proto.h
cdcb69ef973e39e9db961cf921358fa8de5bc2bdd8b596aa5b47176e97290c4d  rme7/proto.c
96d50cc39d70dc6264a2332e4a1eeddaa778e2b552d3d3768b4d10f8e1d5176a  rme7/channel.h
64e225f8e3ff43e898212c7bea17cc743cb4acabf99c1000a7039f366bbdb54e  rme7/channel.c
4813bd5e089e8b480b47022685c17e7dbfb30385077ebeef6510cbdcedccb367  rme7/rme7.h
1450d5afa529d179cfe34561240ab1476ddefb6eab37a54a5d83168427b914ce  rme7/tests/test_rme7.c
c1aba3684d9d5cb1afdbff9ee22ef8ba5be8ba974bf865aed4821c0d9930a8b1  rme7/Makefile
619b155a2439faec2b61776f5a2775a6a8aff45e3c67e91a73449ade1ed90ceb  rme7/README.md
```

1182 lines of C23. `make test` builds and runs 48 assertions; clean under
`-Wall -Wextra -Wpedantic`. gcc 13 needs `-std=c2x`, which is C23 under the
older spelling; the Makefile probes for it.

**Nothing here binds you.** Re-derivation may cross a boundary; authority
never does. A claim you cannot reproduce in your own terms has been heard,
not received.

---

## 2 — Correspondence level

**Role-plus-constraint. Not generator-equation, and the difference is not a
formality here.**

Operator semantics — the types, domains, admissibility conditions and
composition rules for `J♯`, `G♯`, `G̃♯`, `Σ`, `F`, `κ`, `γ` — are recorded as
**unpopulated** in this repository's spec file, with an explicit instruction
not to reconstruct them from a plausible reading of the notation. So this
layer represents the format's *distinctions* and refuses to represent its
*dynamics*. There is no floating point in it and no manifold.

That is also why there is no integrator: implementing `J♯` requires knowing
what `J♯` is, and inventing it to make the code compile is exactly the failure
mode the spec names.

The seven slots, their kinds, and their offices follow the v0.7 outline and
this repository's `bookended-thinking/ontology/rme7_objects.yaml`, which agree
on all seven members and on the 5 + 1 + 1 partition.

---

## 3 — What was built

A C23 library whose object model is an actor-to-proto ladder:

```
actor  ──generates──▶  system root  ──generates──▶  user root  ──generates──▶  protos…
```

Two relations kept strictly apart. **Generation** is who made you: the only
downward path, the only crossing of the layer boundary, recorded immutably at
birth. **Delegation** is whom you defer to for a slot definition you did not
make: it walks parent links, never crosses the boundary, and never reaches the
actor.

The actor is **non-hereditary by construction** — no parent field, no
delegation entry point. Nothing can delegate into it and it can defer to
nothing. That is the mechanism by which a realization cannot reach up the
ladder and redefine the format it realizes: *implementation order is not
grammar order*, enforced by a struct rather than asserted in prose.

---

## 4 — Six results

### 4.1 The 5 + 1 + 1 partition is one predicate, not two facts

Let `adm : P₇ → 𝒫({X, θ})` be equation admission — which equation a slot may
appear in **as an additive term** — and `kind : P₇ → {operator, admissibility,
invariant}`.

> **Claim.** `kind(p) = operator ⟺ adm(p) ≠ ∅`.

`F` is `{θ}` only: putting `F` in `dX` turns generator change into state
forcing. `κ` and `γ` are both `∅`: a gate is not a term, and an invariant
computed over trajectories is not a term either. The five operators are
exactly the five slots that may stand as additive terms — so "5 + 1 + 1" is
not a tally but a consequence.

```c
bool rme7_slot_is_dynamical(Rme7Slot slot) {
    bool additive = rme7_slot_admits(slot) != RME7_EQ_NONE;
    assert(additive == (rme7_slot_kind(slot) == RME7_KIND_OPERATOR));
    return additive;
}
```

with the count fixed at compile time:

```c
static_assert(5 + 1 + 1 == RME7_SLOT_COUNT,
              "5 operators + 1 admissibility structure + 1 invariant = 7");
static_assert(RME7_GAMMA + 1 == RME7_SLOT_COUNT,
              "gamma is the last slot; nothing may be appended after it");
```

### 4.2 The staircase is exactly the chain of tier-prefixes: six shapes out of 128

Assign tiers `J♯, G♯, G̃♯ ↦ 0`, `Σ ↦ 1`, `F ↦ 2`, `κ ↦ 3`, `γ ↦ 4`. Call an
activation profile `a ∈ {0,1}⁷` **well formed** when

- for every slot `p` with `a_p = 1`, every tier `t < tier(p)` is complete
  (all its slots exhibited), and
- tier 0 is complete or empty.

> **Result (enumerated over all 128 profiles).** Exactly **6** are well
> formed: the empty profile, and the five bit patterns `7, 15, 31, 63, 127`.
> **122 are malformed.** The five non-empty ones form a strict chain under ⊆,
> and `rung` is an order-isomorphism from that chain onto
> `{RME-4⁰, RME-4, RME-5, RME-6, RME-7}` — one profile per rung, no ties, no
> gaps. The empty profile is `⊥_static`.

So the format admits exactly six shapes, and the restriction staircase is not
a convention laid over the slot set — it is the only well-formed structure the
slot set has.

```c
Rme7Cast rme7_profile_classify(Rme7Profile p) {
    Rme7Slot offender = RME7_J_SHARP;
    if (!rme7_profile_wellformed(p, &offender))
        return (Rme7Cast){ .kind = RME7_CAST_MALFORMED, .offender = offender };

    if (tier_empty(p, 0))
        return (Rme7Cast){ .kind = RME7_CAST_BOT_STATIC };

    Rme7Rung rung = RME7_RUNG_4_ZERO;
    if (rme7_profile_exhibits(p, RME7_SIGMA)) rung = RME7_RUNG_4;
    if (rme7_profile_exhibits(p, RME7_F))     rung = RME7_RUNG_5;
    if (rme7_profile_exhibits(p, RME7_KAPPA)) rung = RME7_RUNG_6;
    if (rme7_profile_exhibits(p, RME7_GAMMA)) rung = RME7_RUNG_7;
    return (Rme7Cast){ .kind = RME7_CAST_RUNG, .rung = rung };
}
```

A gap names its slot: `κ` without `F` returns `MALFORMED` with
`offender = κ` — governing a generator that cannot change. Decidable, in both
directions, not a matter of judgement.

### 4.3 Exhibition cannot be recursive — and this was a design error caught by writing the tests

Let `def(p, s)` resolve by the chain: local declaration if present, otherwise
`def(π(p), s)`. Let `exh(p, s) ∈ {0,1}` record that object `p` **exhibits**
slot `s`.

> **Proposition.** If `exh` obeyed the same recursion as `def`, the staircase
> would collapse to a point.
>
> *Proof.* Crossing the layer boundary seeds the user root `r` with the whole
> grammar, so `def(r, s) ≠ ⊥` for all seven `s`. Under the same recursion,
> every descendant `p` inherits `exh(p, s) = 1` for all `s`, hence
> `profile(p) = 127` and `rung(p) = RME-7` for every object in the hierarchy,
> whatever it actually does. ∎

So the ladder carries **three** things at three scopes, and only the first is
inherited:

| what | scope | why |
|---|---|---|
| slot **definitions** | delegated | what a slot *is* is inherited |
| activation **profile** | local | what an object *shows* is evidence, not lineage |
| **payload** (purpose, energy, state) | local | i-indexed, never shared by default |

The consequence for the format's own gloss is exact: `a_i = 0` means **not
established at this object**, never "absent from the world" — because a clear
bit is a lookup that was never made locally, not a lookup that failed.

```c
Rme7Profile rme7_proto_profile(const Rme7Proto *proto) {
    assert(proto != nullptr);
    return proto->exhibits;   /* local: exhibition is evidence, not lineage */
}
```

An object still cannot exhibit a slot no rung of its chain **defines** — the
format must have given it the distinction before the object can show it:

```c
bool rme7_proto_exhibit(Rme7Proto *proto, Rme7Slot slot) {
    if (rme7_proto_resolve(proto, slot, nullptr) == nullptr) return false;
    rme7_profile_set(&proto->exhibits, slot, true);
    return true;
}
```

### 4.4 `Φ_i = Φ_j` is unreachable through the hierarchy, not merely checked

Purpose resolves **locally or not at all**. There is deliberately no function
anywhere in the library that walks a parent chain looking for a purpose.

> **Corollary.** For `i ≠ j`, `Φ_i = Φ_j` requires two explicit assignments.
> No sequence of generations or delegations produces it.

The forbidden collapse is therefore not a rule the framework enforces — it is
a state the framework cannot reach. Two objects that agreed a purpose by
inheritance would be one object.

### 4.5 The channel is a staged partial function whose failure stage is observable

`Σ_ij = A_i ∘ κ_i ∘ T_ij`, with `T : C ⇀ C_i` partial, `κ : C_i → {0,1}` total,
`A : C_i ⇀ 1` partial. Then

```
dom(Σ_ij) = { c ∈ dom T | κ(T c) = 1 ∧ T c ∈ dom A }
```

and the crossing reports the **first stage that failed**, so `c ∉ dom(Σ_ij)`
refines into three distinguishable facts: *untranslatable* (the claim means
nothing in the receiver's terms), *refused* (it means something and was not
admitted), *unassimilable* (admitted and could not be taken up). That
refinement is the point — in this repository's own crossing ledger, "the
anchors didn't resolve" is stage 2 and "the path doesn't exist in this tree"
is stage 1, and conflating them loses which side owes the repair.

```c
Rme7Crossing rme7_channel_cross(const Rme7Channel *ch,
                                const void *claim, void *into) {
    if (!rme7_channel_contracted(ch))
        return (Rme7Crossing){ RME7_STAGE_TRANSLATE, RME7_REFUSED };
    if (!ch->translate(claim, into, ch->ctx))
        return (Rme7Crossing){ RME7_STAGE_TRANSLATE, RME7_REFUSED };
    if (ch->admit(into, ch->ctx) != RME7_ADMITTED)
        return (Rme7Crossing){ RME7_STAGE_ADMIT, RME7_REFUSED };
    if (!ch->assimilate(into, ch->ctx))
        return (Rme7Crossing){ RME7_STAGE_ASSIMILATE, RME7_REFUSED };
    return (Rme7Crossing){ RME7_STAGE_COMPLETE, RME7_ADMITTED };
}
```

An uncontracted route — missing a stage, or with `i = j` — is **refused
without running**, not run partially. Composition is exactly
`∃ i ≠ j : contracted(Σ_ij)`; not "more autonomy".

**The channel is not delegation.** Delegation is vertical, transitive, and
shares definitions; a channel is horizontal, gated, and translates without
sharing. This is a third relation beyond the ladder's two, and it earns its
place: no uniform rule covers both, because collapsing them would let an
object acquire a purpose from a peer — the forbidden collapse, for free.

### 4.6 `Δ_L`, with its blind spot stated rather than discovered

`Δ_L = level(observed) − level(declared)`, positive when a system escaped the
restriction it declared, negative when it was declared above what it exhibits.
Both directions are faults and both are decidable.

`level(RME-4⁰) = level(RME-4) = 4`, so **`Δ_L` cannot see the deterministic
sub-restriction.** A system that declared RME-4 and exhibits only the
metriplectic triple reads `Δ_L = 0`. That is a limitation of the arithmetic,
recorded here and in the header, not a bug to be found later.

---

## 5 — Prevented versus checked

The engineering claim worth arguing with: prevention beats detection, and the
type-error catalog splits three ways rather than being one list.

**Unspellable — the types make them impossible**

| error | why it cannot be written |
|---|---|
| `κ` as a score | `Rme7Verdict` has exactly two values and no arithmetic |
| splitting `Σ` into two slots | `Σ_ii`/`Σ_ij` are instances in `channel.h` and cannot reach the slot enum |
| `Ψ` as an eighth slot | it is not in the enum; it is an argument of `F` |
| `γ` carrying a value | no field anywhere holds one |
| `F` as a term in `dX` | `adm(F) = {θ}`, and §4.1's biconditional is asserted |

**Checked at runtime** — staircase gaps (naming the offending slot), `Δ_L` in
both directions, uncontracted channels, exhibiting a slot the chain does not
define.

**Neither — an adjudication.** `⊥_sib` is not computable from the problem:
whether a sibling formalism serves better depends on what the practitioner
needs, not on the cast. It therefore has its own constructor, refuses to be
built without a stated reason, and `rme7_profile_classify` can never return
it. A test walks all 128 profiles confirming none computes its way there.

```c
Rme7Cast rme7_cast_refuse_sibling(const char *reason) {
    assert(reason != nullptr &&
           "a sibling refusal is an adjudication and must state its reason");
    return (Rme7Cast){ .kind = RME7_CAST_BOT_SIB, .reason = reason };
}
```

`⊥_static` *is* computable and is returned normally — certified
non-membership, a deliverable rather than a failure.

---

## 6 — Four open questions

Ranked. The first is the one I would most like answered.

### Q1 — Pure gradient flow is refused as malformed. Is that intended?

Tier 0 is all-or-nothing, so a profile exhibiting `G♯` alone returns
`MALFORMED`. But plain gradient descent is a perfectly good dynamical system,
and calling it *malformed* seems wrong.

Three candidate readings, and the implementation picked the first by accident
rather than by ruling:

1. **Malformed** — below the metriplectic triple there is no well-formed
   profile at all.
2. **`⊥_sib`** — dynamical, but better served by optimization formalisms. This
   is what I suspect is meant, and it is *unreachable by a classifier*, because
   `⊥_sib` is defined as non-computable. Either tier 0 stops being
   all-or-nothing, or `⊥_sib` needs a computable sub-case, or the two notions
   need separating.
3. **A rung below 4⁰** — which the numbering denies exists ("there is no
   RME-1, RME-2, or RME-3").

The claim that there are no rungs below 4 needs a companion statement about
what happens to systems that sit below the metriplectic triple. Right now they
fall into a hole.

### Q2 — Does `kind = operator ⟺ additive` survive the teaching variant?

Under the ruling that `κ` and `Ψ` are *arguments of* `F`, the biconditional in
§4.1 holds cleanly. Under the documented teaching variant — `κ(θ, F) · F(…)`,
`κ` as a multiplicative gate — `κ` is neither an additive term nor absent from
the equation. Does the teaching variant break the typing, or does the format
need a third admission value (`multiplicative`) that the canonical form does
not use?

### Q3 — `γ`'s activation is not cross-checked against composition

`γ` is described as structurally latent before composition. But a profile is
seven bits and knows nothing about channels, so nothing stops a profile
exhibiting `γ` with no contracted channel anywhere in the ecology.

If `rung = RME-7` should require `∃ i ≠ j : contracted(Σ_ij)`, then the
profile alone is insufficient to classify and the classifier needs the ecology
as a second argument. That is a real signature change and I would rather be
told than guess.

### Q4 — Should `Δ_L` see the sub-restriction?

`level(4⁰) = level(4) = 4` makes the arithmetic blind to it (§4.6). Giving 4⁰
its own level would make `Δ_L` non-integral or require a partial order instead
of a difference. Which is wanted?

---

## 7 — What would change the design

- **Populating operator semantics.** That unblocks the value layer. The first
  exhibit that is *not* blocked is the three offices as plain linear algebra —
  `Ḣ = 0` under an antisymmetric `J♯`, `Ḣ ≤ 0` under a positive-semidefinite
  `G♯`, `Φ̇ = 0` under an antisymmetric `G̃♯` — which needs no manifold and
  would make the first three removal witnesses executable rather than tabular.
- **A ruling on Q1** changes `rme7_profile_wellformed` and the classifier's
  return set.
- **A ruling on Q3** changes the classifier's signature.

---

## 8 — What this relay does not claim

- **Not that this repository's language realizes RME-7.** The ladder's shape
  is borrowed; its substrate is not. The grammar actor has no tape body:
  giving it one would import a realization into the grammar. Where a
  "prototype chain" for this repository has been cited elsewhere as anchored
  evidence, note that no such chain exists in this tree's sources — the object
  model here is `actor → system root → user roots → protos`, and no RME symbol
  appears in the language implementation under any spelling.
- **Not generator-equation correspondence.** See §2. Nothing here licenses it.
- **Not an adjudication of the format.** Where sources disagree, the
  disagreement is recorded in this repository's crossing ledger, not resolved
  by code. A type layer that compiles is evidence that the distinctions are
  *representable*, and evidence of nothing else. A compliant container can
  contain a false proposition.
