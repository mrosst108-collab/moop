# rme7 — a C23 type layer for the RME-7 format

This library represents the format's **distinctions**. It integrates nothing:
there is no floating point in it and no manifold. What it does is **refuse** —
a slot in the wrong equation, a route with no contract, a system declared at a
rung it does not reach, a verdict asked to be a score.

```sh
make        # build/librme7.a
make test   # build and run the test binary
make clean
```

C23 throughout. The Makefile probes the compiler and falls back to `-std=c2x`
(gcc 13 knows C23 under the older name). Warnings are errors to fix.

## The ladder

The object hierarchy is borrowed in **shape** from this repository's own object
model, and deliberately not in substrate:

```
actor  ──generates──▶  system root proto  ──generates──▶  user root proto  ──generates──▶  protos…
```

Two relations, kept strictly apart:

- **Generation** — who made you. The only downward path and the only way
  anything crosses the layer boundary. Recorded immutably at birth.
- **Delegation** — whom you defer to for a slot definition you did not make.
  Walks parent links, never crosses the boundary, never reaches the actor.

The actor is **non-hereditary by construction**: it has no parent field and no
delegation entry point, so nothing can delegate into it and it can defer to
nothing. That is what protects the grammar — a realization can never reach up
the ladder and redefine the format it is a realization of.

Generation behaves differently either side of the boundary, and this is the
one sanctioned crossing shape rather than two mechanisms:

| where | what generation does |
|---|---|
| across the layer boundary | **seeds** — the child receives a copy of the definitions, because it cannot delegate back across |
| inside the user layer | **links** — the child defines nothing and delegates upward for everything |

## Three levels, and only the first is inherited

This is the part the design turns on. Writing the tests is what surfaced it:
if definitions and evidence were one thing, a proto generated from a root that
defines all seven slots would *exhibit* all seven, and the restriction
staircase would vanish on contact with the hierarchy.

| what | scope | why |
|---|---|---|
| slot **definitions** | delegated | what a slot *is* is inherited |
| activation **profile** | local | what an object *shows* is evidence, not lineage |
| **payload** (purpose, energy, state) | local | i-indexed, never shared by default |

The payload rule is load-bearing: there is no function in `proto.h` that walks
a parent chain looking for a purpose, so the forbidden collapse `Φ_i = Φ_j`
cannot arise from the hierarchy at all. Two objects that agreed a purpose by
inheritance would be one object.

## The channel is not delegation

`Σ_ij = A_i ∘ κ_i ∘ T_ij` — translate, admit, assimilate, in that order,
short-circuiting. It is the **horizontal** relation among peers: gated, and
translating into the receiver's own terms without sharing anything.
Delegation is **vertical**, transitive, and shares definitions. Spelling
either as the other produces the collapse the format forbids.

A route missing any stage is not a weak channel; it is structurally
unclassified, and `rme7_channel_cross` refuses to run it rather than running
it partially.

## What is prevented, and what is checked

Prevention beats detection, so several type errors are simply unspellable
here. The distinction matters more than the list:

**Prevented by the types**

- κ as a score — `Rme7Verdict` has exactly two values and no arithmetic.
- Splitting Σ into two slots — `Σ_ii`/`Σ_ij` are instances in `channel.h`
  and cannot reach the slot enum.
- Ψ as an eighth slot — it is not in the enum; it is an argument of F.
- γ carrying a value — no field anywhere holds one.
- F as a term in the state equation — `rme7_slot_admits(RME7_F)` is
  `GENERATOR` only, and kind and equation-admission are asserted to agree.

**Checked at runtime**

- Staircase gaps (κ without F, and so on) — decidable, and the fault names
  its slot.
- `Δ_L` = observed − declared, in both directions.
- Uncontracted channels.
- Exhibiting a slot no rung of the chain defines.

**Neither — an adjudication**

`⊥_sib` is not computable from the problem. Whether a sibling formalism serves
better depends on what the practitioner needs, so it has its own constructor,
requires a stated reason, and `rme7_profile_classify` can never return it. A
test asserts that no profile out of all 128 computes its way there. `⊥_static`
*is* computable and is returned normally: certified non-membership, and a
deliverable rather than a failure.

## Autopoietic-interoperability readiness

**This is the framework's stated goal**, so the contract is named and checked
rather than asserted. A framework is **autopoietic-interoperability-ready**
when an independently realized object can do these ten things. The verdicts
are against this code:

| # | condition | status |
|---|---|---|
| 1 | identify its RME-7 type and rung | met — `rme7_proto_classify` |
| 2 | expose only the distinctions it instantiates | met — exhibition is local, and refused for a slot the chain does not define |
| 3 | preserve local purpose rather than inherit it | met — no resolver for the payload exists |
| 4 | resolve definitions without inheriting activation | met — the three-scope split |
| 5 | present a typed crossing port | met at the stage level — `rme7_channel_contracted` |
| 6 | translate foreign representations into local terms | met — a claim is typed, and translation must land well typed |
| 7 | gate admission | met — a two-valued verdict with no arithmetic |
| 8 | assimilate admitted content | met |
| 9 | report exactly where crossing failed | met — stage plus outcome, distinguishing untranslatable from refused from unassimilable |
| 10 | preserve provenance and non-heredity across the crossing | met — crossings carry `from`/`to`, and assimilation that installs a definition is caught |

**Ten of ten.** Two were not, and how they closed is worth keeping.

**Condition 6** was partial: the channel's *stages* were typed while a claim
was a `void *`, so the port was typed as a pipeline and untyped as a carrier.
A claim now declares which slot it concerns, at what rung it was made, its
custody at the sender, and whether it purports to legislate — while its
*content* stays opaque, because the operator semantics are not the port's to
invent. Three structural checks then run with no semantics whatever:

- a slot the receiver's chain never **defines** means nothing there;
- a claim made **above the receiver's rung** cites distinctions it does not
  exhibit — rung-matched, never rung-inflated;
- a claim that **purports to legislate** is refused, and not even an anchored
  custody grade licenses one.

These run as **translation's postcondition, not a fourth stage**. The
factorization has three factors and this does not add one: a translation that
yields something ill typed for the receiver has not put the claim in the
receiver's terms, which was its whole job. Typing is therefore separate from
policy — an ill-typed claim never reaches `κ` at all.

**Condition 10** was absent: a crossing recorded no provenance, and nothing
stopped an assimilation from installing a slot definition. Because definitions
delegate, the receiver's own children would then inherit foreign content as
though the receiver had established it — content becoming grammar by passing
through a port. Crossings now carry `from`/`to`, and the receiver's local
definitions are fingerprinted either side of assimilation.

## Readiness status, stated precisely

"Ready" is one word doing four jobs, so it is split. Only the first is
established:

| status | verdict |
|---|---|
| **contract-complete** — all ten declared conditions implemented and tested | **yes**, by 81 assertions |
| **RME-7-compatible at the port/typing layer** | only to the extent this contract defines compatibility |
| **RME-7 semantically interoperable** | **not established** — a claim's content is opaque and stays so until the operator semantics arrive |
| **autopoietically interoperable in operation** | **not established** — nothing has yet run in an ecology |

The goal is readiness. **The status is contract-complete.** The two are not the
same sentence, and the contract itself is a correspondent's proposal adopted
for being checkable — not something derived from RME-7. A different contract
gives a different verdict.

**And contract-completeness is not structural completeness.** Q1 is a
*blocker*, not a background question: a profile exhibiting `G♯` alone returns
`MALFORMED`, and pure gradient flow is not malformed. 122 of 128 profiles are
malformed. So:

> **Readiness status: contract-complete; structural RME-7 profile completeness
> remains blocked by Q1.**

## What a port certifies: comprehension or exhibition

The open architectural question, implemented rather than argued. Both
predicates ship; `RME7_TYPING_COMPREHENSION` is the default because it is the
behaviour that was already there, and a default is not an endorsement.

- **Comprehension** — the receiver has the definitional machinery to
  understand the distinction: `defines(σ) ∧ ℓ(claim) ≤ ℓ(receiver)`. It is
  **relational**, comparing sender to receiver.
- **Exhibition** — the receiver actually instantiates it: `exhibits(σ)`, per
  slot rather than per level. It is **unary**, and the sender's rung does not
  appear in it at all.

**They are incomparable.** Enumerated over all 175 (receiver rung, slot, claim
rung) triples: comprehension accepts 112, exhibition accepts 125, both accept
88. So 24 are accepted only by comprehension and 37 only by exhibition —
neither direction is empty, and exhibition is *not* a strengthening.

Two cases decide it:

| case | comprehension | exhibition | both |
|---|---|---|---|
| `Σ` claim at rung 4 → RME-4⁰ receiver | well typed *(the hole)* | refused | refused |
| `J♯` claim at rung 7 → RME-4 receiver | refused | well typed *(loses directionality)* | refused |

They guard different failures. Comprehension refuses **level inflation** —
being addressed in terms of a stratum you have not reached. Exhibition refuses
**vacuous reference** — being addressed about a distinction you do not
instantiate. A predicate that never reads the sender's rung cannot order
senders against receivers, so **exhibition alone destroys the directionality
result**. `RME7_TYPING_BOTH` is the conjunction, accepts 88, and is the only
mode that refuses both failures.

## Negative tests

Interoperability readiness is mostly about refusing the wrong input, so the
suite is mostly refusals:

| case | expected | held by |
|---|---|---|
| lower rung → higher rung | accept | directionality tests |
| same rung → same rung | accept | " |
| higher rung → lower rung | reject (`RUNG_ABOVE_RECEIVER`) | " |
| slot the receiver's chain never defines | reject (`UNDEFINED_SLOT`) | typing tests |
| claim purporting to legislate | reject under every mode | " |
| assimilation installing a definition | reject (`MADE_HEREDITARY`) | non-heredity test |
| route missing a stage, or `i = j` | reject (`UNCONTRACTED`), never partially run | channel tests |
| translation failure | reject (`UNTRANSLATABLE`), gate never reached | " |
| opaque payload carrying no slot | accept if policy permits | " |
| `Σ` claim → RME-4⁰ receiver | **exposes the fork** — accepted under comprehension, refused under exhibition | incomparability test |

The last row is the useful one: the suite found an architectural limitation
rather than certifying a happy path.

## What the contract does and does not mean

The ten conditions are a contract about *structure*: that an independently
realized object can type itself, expose only what it instantiates, keep its
own purpose, and cross a boundary without losing provenance or leaking
grammar. They are not a claim that RME-7-governed content has been carried —
the content of a claim is still opaque here, and must be, until the operator
semantics arrive from a primary source.

## What this is not

- **Not an integrator.** The value layer sits above this one and is blocked on
  content this repository does not have: implementing `J♯` requires its type,
  domain and admissibility conditions, and `prompts/asdg-rme7.md` §3 records
  those as unpopulated and not to be reconstructed. Building it now would mean
  inventing operator semantics to make the code compile. The first exhibit that
  is *not* blocked is the three offices as linear algebra — `Ḣ = 0` under an
  antisymmetric `J♯`, `Ḣ ≤ 0` under a positive-semidefinite `G♯`, `Φ̇ = 0` under
  an antisymmetric `G̃♯` — which needs no manifold and would make the first
  three removal witnesses executable.
- **Not a claim that this repository's language realizes RME-7.** The ladder's
  shape is borrowed; its substrate is not. Giving the grammar actor a tape body
  would import a realization into the grammar, which is the error the format's
  own custody rules name. Implementation order is not grammar order.
- **Not adjudicating the format.** Where the sources this was built from
  disagree, the disagreement is recorded in `docs/crossing.md`, not resolved
  here. The slot set, kinds, and offices follow the v0.7 outline and
  `bookended-thinking/ontology/rme7_objects.yaml`, which agree on all seven.
