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

## Test derivations

`P1–P13` in `tests/pc_test.c`; each names its S-statement inline. No expected value was taken from
an AWV fixture. `P8` and `P4` deserve note: each exercises **both** directions of a symmetric
requirement, because this session established that a one-sided fixture cannot distinguish a
symmetric guard from a one-sided one — the defect D1 caught in AWV.

## Status

```
types/           implemented, 13 ProtoC-derived tests pass
admissibility/   implemented, same suite
declaration/     NOT STARTED
realization/     NOT STARTED
identity/        NOT STARTED
graph/           NOT STARTED  (no classifier -- see SEMANTICS.md)
composition/     NOT STARTED
differential/    NOT STARTED
```

**These 13 tests are not evidence about AWV, and AWV's 94 are not evidence about ProtoC.** The
differential result does not exist until both substrates are complete and compared.
