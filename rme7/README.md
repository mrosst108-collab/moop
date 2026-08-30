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
