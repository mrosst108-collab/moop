# ProtoC — frozen semantic oracle

> **STATUS: FROZEN.** No S-statement changes while ProtoC is being implemented. A discovery made
> during implementation does **not** feed back into this file — it is raised as a discrepancy,
> classified, and only then may the oracle change. An oracle edited to match the code under
> construction is not an oracle.

**ProtoC is a CLEAN-ROOM RECONSTRUCTION.** This file and `../SPEC.md` are the authority.

### The independence constraint

Stronger than "do not `#include` `src/rme/`", which would be trivially satisfiable while defeating
the experiment:

> **ProtoC must not derive its semantics, its types, its admissibility decisions, or its expected
> classifications from AWV/RME implementation artifacts.**

It may of course implement the same *abstract requirements* — that is precisely what makes agreement
meaningful. What it must not do is recover a decision by consulting how the existing code decides
it. Reading `src/` to resolve an ambiguity converts the experiment into transcription.

**And the corresponding prohibition on this file:**

> **No S-statement may be justified by the current behaviour of AWV, by `rme_classify()`, or by an
> existing AWV test.**

Each S-statement below traces to `SPEC.md` or to a stated requirement, never to observed behaviour.
Without this rule the clean-room oracle silently becomes a disguised transcription of the
implementation, and the whole exercise proves only that a program agrees with itself.

## The question ProtoC answers

> Does the specification determine the implementation closely enough that two **independently
> structured** substrates converge on the same observable semantics?

- **Converge** → the specification is determinate; that is a real result about the spec.
- **Diverge** → the disagreement localizes exactly where the specification is still underspecified.

Neither implementation gets to declare itself correct on disagreement. A divergence is an
**adjudication item**, resolved against the specification, never against whichever code is older.

## Why this is worth the cost

Three defects this session were of a kind a single implementation cannot surface:

| | what it was | why one implementation misses it |
|---|---|---|
| **C18a** | the spec required a state the API could not represent | the test suite was written against the API, so the missing state was invisible |
| **R1** | `rme_validate()` and `rme7_conforms()` disagreed about one record | both were "right" by their own code; only the spec says which |
| **R3** | a documentation claim that was false | nothing executable contradicted it |

A second implementation built from the spec cannot inherit those, because it does not inherit the
first implementation's reading.

## Frozen semantic requirements

These are the observable semantics ProtoC must reproduce. Each is stated so it can be tested
without reference to any particular decomposition.

| # | requirement |
|---|---|
| **S1** | `Admissible ≠ Declared ≠ Executed`, and `Admissible ⇏ Declared`. A relation may be admissible while undeclared; evaluating admissibility declares nothing and mutates nothing. |
| **S2** | Port status and realization validity are **independently enforced**, and both are enforced **at the validation boundary**. An ACTIVE port aimed at the declared vestigial realization must not reach validated state. |
| **S3** | Vestigial means **retained, typed and reachable — not wireable**. `Participates(p,R_C) ⇒ Status(p) = ACTIVE`, unconditional, on **both** endpoints. |
| **S4** | RME-7 requires **reciprocal governed coupling**, not mere composition: a directed cycle entirely within `G_GS`. A governed self-edge is such a cycle; execution self-recursion is not. |
| **S5** | A **released identity must never become a valid identity for a later object.** |
| **S6** | Substrate ownership stops at the **record** boundary. Client realization objects remain client-owned; the substrate must not claim otherwise. |
| **S7** | `E_dispatch ⊆ E_envelope` is **construction-guaranteed**, not a load-bearing runtime test. Elision removes from dispatch, never from the envelope. |
| **S8** | A **malformed input is refused, never silently normalized** into a plausible verdict. Capacity, allocation failure, out-of-range indices and malformed relations all refuse. |
| **S9** | Validity, conformance, classification, port status and identity are **nonhereditary** (F7/F8). Authority may be inherited; validity must be earned. |
| **S10** | Authority and validity are independent **in both directions** (F9): capability establishes no validity, validation grants no authority. |
| **S11** | Classification is **observational**. It cannot establish or mutate conformance, and conformance sampled before and after classifying must be unchanged. |

### Deliberately NOT in this list

Two requirements offered for inclusion belong to **AWV, not to poiesis**:

- `Dδ ≠ D`
- batch boundaries do not themselves establish temporal semantics

Both are AWV's temporal and measurement semantics (v0.15). Placing them in the substrate's oracle
would invert the dependency `AWV → poiesis` that `make layering` enforces mechanically, and ProtoC
would then be built against a spec that already knows about AWV. They belong in an AWV-side oracle
if AWV is reconstructed.

Likewise **AWV constitutional permission stays outside `rme/`** — that is a layering rule, and it is
already checked by `make layering`; ProtoC inherits the check, not a copy of the constitution.

## Required decomposition — deliberately different

If ProtoC has the same module structure as `src/rme/`, agreement is weak evidence: the two would
likely make the same mistakes in the same places. ProtoC is therefore organized by **concern**
rather than by artifact:

```
protoc/
  types/          representation and its invariants
  admissibility/  the compatibility predicate  (S1, S3)
  declaration/    relational configuration     (S1)
  realization/    status/contract enforcement  (S2, S7)
  identity/       lifetime and released identities (S5, S6)
  graph/          projection, cycles, classification (S4, S8, S11)
  composition/    the relational operations
```

Note what this splits that `src/rme/` fuses: **admissibility and declaration are separate
directories**, because their conflation was a real defect (C18a). And what it fuses that `src/rme/`
splits: `conform`/`contract`/`validate` all land in `realization/` and `identity/`, because the
boundary between them was where R1 hid.

## Oracle discipline

The 94-test suite is the **external oracle, not the design document.** ProtoC is written against
this file; the suite is run against it afterwards. A test that fails is first checked against the
specification — it may be the test that is wrong, as C17 was.

Tests that must be preserved verbatim in intent, because each caught a real defect:

```
C18a  admissible-but-undeclared            C18d  retained but non-admissible vestigial
V4    ACTIVE -> vestigial realization refused at the boundary
V6    a released identity cannot resurrect  V7    record ownership vs realization ownership
K8    AWV classifies 6B                     K10   governed self-edge is a cycle
D1    P-side ACTIVE guard (mutation-proven) D3    malformed relation refused, not dereferenced
D4    out-of-range projection refused       C17   conformance sampled before AND after
```

## ProtoC does NOT contain a classifier

The two roles are distinct, and keeping them distinct is what preserves the firewall:

```
ProtoC          independently implements the semantic OBJECT and its operations
AWV/RME         classifies the resulting object
the oracle      compares the observable CONSEQUENCES, classification included
```

ProtoC must **not** reproduce `rme_classify()`. Were it to carry its own classifier, the two systems
would validate one another circularly and agreement would mean only that two classifiers written by
the same author agree. Classification enters the comparison as a consequence applied *to* ProtoC's
object by the existing observer — which is exactly the Axis-C position that classification is
observational and its input is a declared system.

## Differential testing — THREE outcomes

```
AGREE        both substrates produce the same observable consequence
DISAGREE     they differ, and the specification decides which is right
UNDECIDABLE  the specification does not determine the case
```

**Classification is ORDERED, and the order is what keeps `UNDECIDABLE` honest:**

```
1. AGREE        both consequences are permitted by the frozen semantics
2. DISAGREE     the frozen semantics DETERMINE a consequence and one implementation violates it
3. UNDECIDABLE  the frozen semantics genuinely permit MULTIPLE consequences
```

Try them in that order. `UNDECIDABLE` is reachable only after establishing that S1–S11 do not
determine the case — it means *"the frozen material does not fix which consequence is correct,"*
never *"the two implementations differ and I would rather not adjudicate."* Used as an escape hatch
it destroys the experiment, because every real disagreement would be relabelled as a specification
gap.

`UNDECIDABLE` is not a convenience. Without it, a clean-room implementation meeting an
underspecified case is **forced into a false disagreement** merely to complete the matrix, and the
matrix then reports a specification defect as an implementation defect. An `UNDECIDABLE` cell is a
finding in its own right: it names a point the specification does not determine.

Cross-validate on identical valid and invalid records:

```
ProtoA(record) ⋈ ProtoC(record)   for
    validation · admissibility · declaration · composition
    projection · SCC/cycle detection · classification · dispatch · lifetime
```

Then **mutate one implementation** and confirm the differential test detects it — otherwise the
comparison is as vacuous as the subset check was.

Disagreement is adjudicated against `SPEC.md` and this file, never against whichever code is older.
If neither resolves it, the cell is `UNDECIDABLE` and the specification is underspecified there.

## The symmetric distinction rule

> **If a distinction is not required by S1–S11, ProtoC must not manufacture it merely because AWV
> has one. Conversely, ProtoC must not remove a distinction merely because AWV lacks one.**

The test is **semantic consequence, not structural correspondence.** Mirroring AWV's distinctions is
transcription; inverting them to look different is theatre. Both make the eventual comparison less
informative, and only the first is usually noticed.

## Meta-test: an UNDECIDABLE cell reported as DISAGREE is an ORACLE DEFECT

The three cells below are undetermined by S1–S11 (see `DERIVATION.md`):

| question | ProtoC | AWV | required verdict |
|---|---|---|---|
| which endpoint pairs are compatible | client-supplied parameter | fixed table | **UNDECIDABLE** |
| the port vocabulary | unconstrained descriptor table | fixed vocabulary | **UNDECIDABLE** |
| whether compatibility is symmetric | explicit flag | fixed choice | **UNDECIDABLE** |

If the differential oracle ever reports one of these as **DISAGREE**, the fault is in the ORACLE,
not in either substrate: it has promoted an implementation choice into a semantic requirement. That
is itself a finding, and it is filed against `SEMANTICS.md`.

This is the counterpart to the escape-hatch risk. `UNDECIDABLE` used too freely hides real
disagreements; `DISAGREE` used on an undetermined cell invents requirements. Both are oracle
defects, in opposite directions.

## Invariants are compared, not mechanisms

Where a requirement names an **invariant**, the oracle compares the invariant and not the machinery
that achieves it.

- **S5** requires that a released identity never become valid for a later object. It does **not**
  require monotonic allocation. AWV reached it that way because its handle is a *pointer into the
  slot*; a substrate whose identity is a *value* may recycle slots safely and satisfy S5 exactly.
  Both are conformant.
- **S4** requires a directed cycle among governed nodes. It does **not** require SCC decomposition,
  an edge list, a materialized projection, or a self-edge special case. A substrate using
  reachability gets the self-edge rule for free; one using SCC cardinality must add a check. Both
  are conformant, and a differing edge-direction convention is not a disagreement at all, since
  cycle existence is invariant under reversal.
- **S6** bounds ownership at the record. It does **not** require any particular ownership
  architecture. ProtoC need not deep-copy client realization machinery to imitate AWV; reaching the
  same semantic boundary by different means is a **successful divergence**, not a discrepancy.

## Clean-room prohibitions, enumerated

The constraint reduces to: **ProtoC may know the frozen semantic specification; it may not know how
AWV realizes it.** Concretely, ProtoC must not —

- copy AWV data structures under different names;
- consult `rme_classify()`, or any AWV code, to decide ProtoC behaviour;
- derive ProtoC's expected outputs from AWV fixtures;
- import an AWV test as a ProtoC test without independently deriving its expected result from
  S1–S11;
- amend S1–S11 because ProtoC exposed an inconvenient case.

**Derivation record.** Every expected oracle consequence is derived in `DERIVATION.md` from S1–S11
*before* either implementation is consulted, and the derivation is recorded. A consequence with no
recorded derivation is not an oracle expectation — it is a transcription of whatever the code
happens to do.

## What counts as success

**Not** "ProtoC passes." The regression suite going green is useful regression information and is
**not evidence for ProtoC** — the entire epistemic value of this exercise is that ProtoC is
*allowed to disagree*.

```
strongest outcome        ProtoC independently reaches the same boundary behaviour DESPITE a
                         deliberately different decomposition
strongest INTERESTING    a disagreement that survives reproduction -- that is where the frozen
outcome                  specification gets its next real test
```

A run in which ProtoC agreed everywhere because it was written by consulting `src/` produces
neither.
