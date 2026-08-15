# ProtoC — derivation record

Every design decision and every expected test result traces to an S-statement in `SEMANTICS.md`.
Nothing here was obtained by running AWV or by reading `../src/rme/`.

**Why this file exists.** Without a recorded derivation, an expected consequence is indistinguishable
from a transcription of whatever the existing code happens to do — and the differential result would
then be circular. A consequence with no entry below is not an oracle expectation.

## types/ — structural decisions

| decision | forced by | derivation |
|---|---|---|
| ports are **data** (descriptor table + parallel instance vector), not named struct members | none — a free choice | S1–S11 constrain what a status *means*, never how many ports exist or how they are addressed. Treating the vocabulary as data is therefore faithful, and it is maximally distant from a fixed record of named members. Chosen **because** it is distant: see `SEMANTICS.md`, "deliberately different". |
| `status` and `realization` are separate fields with separate validators | **S2** | S2 says the two are *independently* enforced. One field encoding both, or one validator deciding both, makes "which of the two failed" unanswerable. |
| `PC_STATUS_UNSET = 0` | **S8** | A zero-filled port must be *detectably* unset. Were 0 a semantic status, omission would normalize silently into a plausible answer — exactly what S8 forbids. It is a construction sentinel and never an answer. |
| refusals are a **reason code**, not `false` | **S8** | "Refused" must be distinguishable from "answered no". A bare boolean fuses them. |
| `realization` / `vestigial_form` are `const void *`, never copied or freed | **S6** | Ownership stops at the record. ProtoC only ever *compares* these addresses; comparison is the sole operation S2 requires of them. |
| `elidable_when_vestigial` is a per-port field | **S7** | Elision is a permission, not a consequence of status. A global rule would make `VESTIGIAL ⇒ elidable` true by construction. |
| **no** `pc_dispatch_within_envelope()` predicate | **S7** | S7 states the containment is *construction-guaranteed*. Since omission is the only operation available, the relation cannot fail; offering a runtime predicate would imply it might, and would be vacuous exactly as the corresponding AWV check turned out to be. |
| **no** validity field anywhere on `PcSurface` | **S9, S10** | Validity is nonhereditary and non-transferable. A field is the obvious way to violate both; the representation has nowhere to record it. |

## admissibility/ — structural decisions

| decision | forced by | derivation |
|---|---|---|
| the **endpoint-pair predicate is primary**; a connection set is a fold | **S1** | `Admissible ⇏ Declared` must hold. The primary entry point receives no relation, so it *cannot* consult a declared flag — S1 holds by the shape of the API rather than by remembering not to read a field. |
| declaration is not visible from `pc_admit.h` | **S1** | Same reason, at file scope. |
| both endpoints checked for ACTIVE, symmetrically | **S3** | S3 is symmetric and unconditional. An asymmetric implementation is undetectable by any single-sided fixture — which is why P8 exercises both sides. |
| `obligations == |set|`, never the count of compatible pairs | **S1** | Admissibility is a property of the *declared* endpoints. A pair compatible outside the set contributes nothing (P11). |
| malformed input has its own code, not `INCOMPATIBLE` | **S8** | A caller must distinguish "these do not connect" from "you handed me nonsense". |

## What S1–S11 do NOT determine

Recorded rather than resolved by consulting the other implementation.

| undetermined | consequence |
|---|---|
| **which endpoint pairs are compatible** | S3 requires *compatible* endpoints but never fixes the relation. ProtoC therefore takes compatibility as a **client-supplied parameter**. If AWV hardcodes a table, the frozen material does not adjudicate the difference: the differential oracle must record **UNDECIDABLE**, not a defect on either side. |
| **the port vocabulary** | No S-statement fixes a port set. ProtoC's schema is data; a fixed vocabulary is equally faithful. A differing vocabulary is **UNDECIDABLE**. |
| **whether compatibility is symmetric** | Not stated. ProtoC makes it an explicit flag rather than assuming. |

## identity/ — structural decisions

| decision | forced by | derivation |
|---|---|---|
| **identity is a VALUE** `(slot, serial)`, not a reference | **S5** | S5 forbids a released identity ever becoming valid for a later object. It does **not** name a mechanism. Comparing two *values* means a recycled slot cannot resurrect a released identity, so **slots may be reused freely**. A substrate handing out *pointers into slots* cannot do this — the stale handle and the reused slot are the same address, so any generation stamped in the slot reads through the stale handle as current — and must forbid reuse instead. Both satisfy S5. |
| serial `0` never issued | **S5, S8** | A zero-filled identity must be dead, not name slot 0. |
| the boundary returns an **identity**, not a flag or wrapper | **S9, S10** | Validity is nonhereditary and non-transferable. Returning a *value that names a registry entry* means there is no transferable "validated" property for `child = parent` to move: copying the value aliases the same object (P16). S9/S10 fall out of the representation instead of being defended by a rule. |
| the boundary takes **only** a surface | **S9, S10** | No actor, capability, parent or provenance is relevant to the answer, so there is no parameter through which to offer one. |

## declaration/ and composition/ — structural decisions

| decision | forced by | derivation |
|---|---|---|
| declaration is an **act in a registry**, not a flag on the set | **S1** | A flag would sit inside the object admissibility receives, one dereference from every endpoint check. As a separate registry, the connection set has no such field and `admissibility/` does not include `pc_declare.h` — `Admissible ⇏ Declared` is enforced by reachability. |
| `pc_declare()` does **not** evaluate admissibility | **S1** | They are different stages. Checking here would make `Declared ⇒ Admissible`, which S1 licenses in neither direction (P20). |
| **no execution operation exists** | **S1** | S1 places Executed outside the substrate. `Executed ⇒ Declared` holds vacuously and cannot be violated by an operation that is absent. |
| declaration binds to its **participants** | **S1** | A declaration for (A,B) is not one for (C,D); binding by argument position would make declaration positional rather than relational (P19). |
| composition reports `declared` and `admissibility` **separately** | **S1** | Fusing them into one boolean makes "which stage failed" unanswerable, the same defect shape as S2's independent enforcement. |

## realization/ — a distinction NOT manufactured

Per the symmetric-distinction rule: ProtoC implements **one** boundary, not a validation predicate
*and* a conformance predicate. S1–S11 name one boundary and one set of requirements on it. AWV has
two — and this session showed them disagreeing about a single record (its R1 defect). ProtoC does
not reproduce the split merely because AWV has it; if the two substrates differ in consequence
there, that is something to compare, not a structure to imitate.

## graph/ — structural decisions

**What S4 constrains:** that a governed/non-governed distinction exists; that the criterion is a
*directed cycle*; that the cycle lies *entirely* among governed nodes; that a self-edge qualifies
and execution self-recursion does not.

**What S4 leaves slack:** representation, algorithm, edge direction.

| decision | forced by | derivation |
|---|---|---|
| dependencies are **bitset rows**, not an edge list | slack | S4 fixes no representation. Chosen for distance from an edge array. |
| the governed restriction is a **mask applied during the computation** | **S8** + slack | No projected structure is ever materialized, so there is nothing that can be truncated or fall out of step with the original. AWV's projection-into-an-array is equally faithful — and it *was* the site of a silent-truncation defect, which is a fact about that mechanism, not about S4. |
| cycles by **transitive-closure reachability**, not SCC | slack | S4 asks for a directed cycle, not for components. |
| **no self-edge special case** | consequence | Under reachability, `x reaches x` is true exactly when a path of length ≥ 1 returns to `x` — which already includes a self-edge. A substrate testing cycles by *SCC cardinality* must add an explicit self-loop check, because a self-loop is a one-member component. **S4's self-edge rule is free here and requires machinery there.** Same invariant, different mechanism: the S5 pattern again. |
| edge direction is a **convention** | — | Cycle existence is invariant under reversing every edge, so nothing in S4 depends on which way the arrow is read. Recorded so a differing convention is never mistaken for a disagreement. |
| **no classifier** | `SEMANTICS.md` | ProtoC realizes the object; an external observer classifies it. A classifier here would make the substrates validate one another circularly. This module answers a graph question and says nothing about RME levels. |

## Test derivations

`P1–P13` in `tests/pc_test.c`; each names its S-statement inline. No expected value was taken from
an AWV fixture. `P8` and `P4` deserve note: each exercises **both** directions of a symmetric
requirement, because this session established that a one-sided fixture cannot distinguish a
symmetric guard from a one-sided one — the defect D1 caught in AWV.

## Status

```
types/           implemented   P1-P6, P13
admissibility/   implemented   P7-P12
identity/        implemented   P14-P16
realization/     implemented   P17
declaration/     implemented   P18-P20
composition/     implemented   P18, P20
graph/           implemented   P21-P26  (cycles only -- NO classifier, see SEMANTICS.md)
differential/    NOT STARTED   -- written LAST, after ProtoC has had the chance to surprise
```

**These 13 tests are not evidence about AWV, and AWV's 94 are not evidence about ProtoC.** The
differential result does not exist until both substrates are complete and compared.
