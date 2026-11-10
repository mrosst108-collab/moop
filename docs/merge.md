# Merge record: Moop × Unicore × Weft × Warp

10 November 2026. Revised the same day, four times: after review, with
the provisional rulings entered in §10; after the author supplied an
account of early Moop's four levels, entered in §13; after two further
documents were located, reconciled in §14; and after the second merge
corrected itself, entered at the end of §14.

This record investigates one architecture for merging four designs. It
takes Warp's three mechanisms — term, clause, port — as the foundation,
uses Weft's selection rule to govern what is admitted, and draws scope
and guarantee structure from the Moop and Unicore material as Weft and
Warp describe it. Moop's own records, located later, contest that
description at ten points, and a second merge built from those records
proposes a different kernel; §14 sets the two side by side and does not
choose. It is a candidate to investigate, not a ratified synthesis. The merged
architecture has no name (M1). Several of its derivations are
conditional on tests that do not exist yet (§11). Nothing in it reopens
a prior ruling: where it differs from a decided item, the decided item
stands. The proposal is checked against early Moop's four levels in §13.

## Reading this record

Every claim carries a provenance and a status. They are kept apart so
that a reconstructed claim never acquires the standing of a documented
one.

| Provenance | Meaning |
|---|---|
| **Direct** | Stated in a source that was read: Weft, Warp, this repository, and, from §14 on, the two documents located on 10 November |
| **Author's account** | Stated by the author in review on 10 November 2026 and entered in §13. First-hand and retrospective: it is a source for what early Moop was, and it is not one of the unlocated design records |
| **Mediated** | A claim about a record this session did not open, known only through another document's description of it. It establishes what the describing document says, not what the original says. Before §14 that meant everything about Unicore and Moop's design records, relayed by Weft and Warp. It still covers `MOOP.md`, `moop.c` and Unicore's `SPEC.md`, which the two located documents cite by section and which could not be opened here |
| **Derived** | This record's own inference. Stated in no source |

| Status | Meaning |
|---|---|
| **Source-established** | Directly stated in an available source. A mediated claim does not qualify; it is recorded as reported |
| **Derived proposal** | Follows from this record's definitions, pending verification |
| **Ruled and implemented** | Explicitly decided and reflected in the implementation and its tests. Only items of this repository have this status |

A passing `make test` establishes what its tests assert. No test
exercises the three-mechanism architecture.

**The sources.** The assignment of one question to each source is this
record's reading (derived). The table does not claim equal documentary
support.

| Source | Question assigned | Evidentiary standing |
|---|---|---|
| Weft | How is a mechanism selected? | Direct: Specification rev 72, Moop correspondence rev 9, Derivations rev 6, register |
| Warp | What are the mechanisms? | Direct: Proposal of 9 November 2026, dossiers, register |
| Unicore | Who answers for each guarantee? | Mediated. Its specification, `SPEC.md`, exists: the second merge read it and cites it by section (§14). It could not be opened here. Before §14 everything attributed to Unicore came from Warp's proposal and Dossier T, and from Weft's correspondence tab, which calls Moop "formerly Unicore" |
| Moop | What is it made of, and how does it read? | Three things carry the name (§14). Early Moop, March to April 2026: direct through the handoff document, and the author's account in §13; its specification and source were not opened. The current Moop, which Weft calls "formerly Unicore": see Unicore. This repository, begun in July 2026: direct, and a separate implementation that shares none of early Moop's history. Sections 2 to 12 say "Moop" for this repository together with Weft's and Warp's descriptions, which is the conflation §14 corrects |

## 1. Method

| Rule | Statement | Standing |
|---|---|---|
| Admission | `Admit(f) ⟺ [Strengthens(f, ≥2) ∨ Eliminates(f, ≥2)] ∧ Noninterfering(f)`. The two counts are never added. Wider coverage is a reason to look for a candidate, never a reason to admit one | Direct, Weft §1 |
| Deletion | A construct is redundant iff a uniform contextual rule covers all its uses without creating silence (a mistake becoming an action) or ambiguity (one form, two meanings) | Direct, `docs/derivation.md` |
| Order | Unify from the lowest level upward, keep every distinction that carries its own guarantee, and promote an admitted composite to a building block of the next level | Direct, Weft §1 |
| Evidence | Provenance, rule, semantic status and test status are separate claims. Nothing is presented as proven unless it was discharged | Direct, Weft's correspondence tab and constraint 6; this repository's rule that an unimplemented behavior reports itself |

Reading admission and deletion as one discipline in two directions is
derived. So is the rule this record adds for itself: a merge selects
mechanisms, and it does not select away a distinction that a source
keeps on purpose. A simplification that would erase provenance, lineage,
pruning semantics or version policy by vocabulary alone is not a
derivation.

## 2. Three invariants, three mechanisms

Each cell below is a statement by the source in its column. Reading the
rows as the same three invariants is derived.

| Invariant | Warp's mechanism | This repository (direct) | Weft (direct) | Warp (direct) | Mediated |
|---|---|---|---|---|---|
| Homoiconicity | Term | No read-only program tape; every cell is control and target | The canonical typed graph; `Code(T)` as candidate D2 | Every component of machine state is a term | Unicore: `homoiconicity_guarantor` |
| Reversibility | Clause | CCNOT and rotation; the gate layer; `mirrors` | `Iso` and `PartialIso`, inside a sector | Every machine step is a certified bijection on terms | Unicore: `reversibility_guarantor` |
| Segregation | Port | Two memories, two logics; one sanctioned bridge shape | The sector boundary: entry through lifts, exit through `Dissipate` | Information enters or leaves only by crossing a port | Unicore: dissipation is user-facing. Moop records: coupling only through typed ports |
| The one exception | Root pruning | Causal pruning | — | Root pruning, outside the machine step | — |

The third column is this repository, begun in July 2026. It is not early
Moop; §14 gives early Moop's own statements.

**Derived proposal.** One mechanism carries one invariant, so removing a
mechanism removes exactly its invariant, and the count is three. Weft's
seven kernel mechanisms would then be composites. Warp's register
classifies most of them that way already, in its table of the relay's
eight foundations; the rest is this record's reading. Moop's five constituents, a
mediated list, would be two realizations, two crossings and one
composite. The count is not one: a term that is not a clause still
exists, and a clause across a boundary still needs the boundary.

Whether the repository's causal pruning and Warp's root pruning are the
same exception is not settled. §10, M6 records a tested difference.

## 3. The kernel, as Warp rules it

Direct, Warp §3: three mechanisms and eight operational rules, with a
ninth pending admission.

| Mechanism | Rules |
|---|---|
| **Term** | (a) A term is an atom, or a tagged node with labelled children. (b) A term's identity is the hash of its normalized form. Nominal-type, role-seal and resource identity are kept apart from it, and none confers authority |
| **Clause** | (c) A template is a term with holes, each used exactly once on each side; it builds read forward and matches read backward; it may apply another clause set. (d) A clause set selects by match and is exclusive on both sides, in either direction. (e) The certified primitives of Weft §6: swap, XOR update, modular add and subtract updates, Toffoli update |
| **Port** | (f) `v -> p` crosses outward and `x <- p` crosses inward; the nearest enclosing handler receives the request and the continuation, both as terms. (g) A handler is a clause set over request terms; it stays installed and holds the continuation as a linear term |
| Order | (h) Evaluation is strict and left to right, so the order of crossings is fixed |
| Pending | (i) A term takes a role — code, type, request, continuation — only through that role's seal (Dossier T) |

**Vocabulary** (direct, Warp §4). A *sector* is a handler and the
computation it encloses; the *root handler* encloses them all. The
*system sector* holds certified clauses with an empty row, so it cannot
cross and cannot lose. *User sectors* are handler layers whose *rows*
declare each crossing. `hide` is the outward crossing the root answers
by retaining the term; ε counts each `hide` event once, in bits. The
*complement* is what the root retains so that a run can be reversed. A
*witness* is an ordinary handler layer that copies what crosses its own
boundary, and it is never the complement. The machine is one term,
`M = ⟨system store, dynamic store, focus, continuation, complement⟩`,
and the language is one clause set, `step : M <-> M`. The system store
is fixed from `RUNTIME_START` until termination.

**Three things that are not the same** (direct, Warp §4, which calls
them hidden, pruned, and physically reclaimed or zeroed; the names here
and the sentence after the table are the review's):

| Stage | Unit | What it is |
|---|---|---|
| Logical hiding | Bits | Information becomes inaccessible to the program and stays reconstructible. Counted by ε |
| Root pruning | Bits | Hidden information is removed from the reconstructible state. The only operation that is not a bijection, and the only one outside `step` |
| Physical reclamation | Bytes | The realization reclaims or zeroes storage. Two distinct measurement events. Weft's M_heap measures here |

Reclamation does not imply that a value was previously hidden by a
program-level `hide`, and it is not by itself a violation of ε
accounting.

### Proposed merger decision M3: rule (e)

This is a decision of the merger. It is not attributed to Warp, whose
ruled count is eight.

*Proposal.* Over a two-atom type the certified primitives are ordinary
clause sets under rules (c) and (d), so rule (e) is not an independent
rule of the format:

```
cnot:
    (0, b) <-> (0, b)
    (1, 0) <-> (1, 1)
    (1, 1) <-> (1, 0)

ccnot:
    (0, b, c) <-> (0, b, c)
    (1, 0, c) <-> (1, 0, c)
    (1, 1, 0) <-> (1, 1, 1)
    (1, 1, 1) <-> (1, 1, 0)
```

*Count.* If M3 is adopted, the merged kernel has seven admitted
operational rules and one pending role-seal rule. Until it is adopted,
it has Warp's eight and the pending ninth.

*What the sketch does not establish.* Writing the tables down shows
that the gates are bijections a clause set can express. It does not
show that a certifier accepts them, that a realization executes them, or
that the word-level updates follow. Obligation V1 (§11) names what must
be shown. The realization obligation remains under either outcome: a
native adder, or the tape's gate, has to agree with whatever the format
says it stands for.

## 4. Foundational structure

**What is Warp's.** Warp §5 files its thirteen pairings under four
headings: Term × Clause (1–5), Clause × Port (6–9), Port × Term (10–12)
and all three (13, the role seal). The grouping is direct.

**What is this record's.** Treating the three pairs and the triple as
the foundation on which everything else is built, and the four names
below, are derived. No source names these four compositions as such.
Where a name is borrowed, the source used it for something narrower,
and the note says so.

| Composition | Proposed name | What the composition supplies | Textual support |
|---|---|---|---|
| Term × Clause | Causal closure | State and transformation are represented in the same domain: a clause is a term, inversion is a clause over clause terms, and a template builds forward and matches backward | Direct: Warp §1 and pairings 1–5; Weft's Derivations, "central reference pairing: reversibility × homoiconicity". The name is this repository's (`docs/model.md`), where it means reversible plus homoiconic tapes |
| Clause × Port | The bridge | Transformations become interactions at declared boundaries: a function is a clause whose complement leaves through a port, and inversion exchanges `->` and `<-` | Direct: Warp pairings 6–9; Weft §6, the lift followed by `drop`. The name is this repository's, where it means one shape: reversible effect inside, irreversible observation outside. Mediated: Unicore's two axes |
| Port × Term | The message | Interactions and requests are represented as terms: a handler is a clause set over requests, and an unanswered request goes to the enclosing handler | Direct: Warp pairings 10–12; Weft §2, "handler clauses are match arms". The name is this record's. "Message" as a Moop constituent is mediated |
| Term × Clause × Port | The machine | The architecture that composes the three: state is one term, `step` is one clause set over it, and the root handler is where it meets the world | Direct: Warp §4 and its level-4 composite. Derived: reading the machine as the triple. Warp's own all-three pairing is the role seal |

Each pairing supplies a relation the other two cannot supply alone.
That claim is derived, and it is the reason for building these four
before anything in §5.

This foundation is symmetric: three pairs and a triple. Early Moop's
was ordered: four cumulative levels, from reversible operations up to
prototypes. §13 sets the two side by side. They are different
structures over the same material, and neither is derived from the
other.

## 5. Corollaries

### 5.1 As Warp states them

Direct, Warp §6. Level 2 unifies kernel mechanisms, level 3 unifies
level-2 composites, level 4 is machine-wide.

| Level | Composite | Unified from | Distinction kept |
|---|---|---|---|
| 2 | Function | Clause + `-> hide` | Logical reversal against reversal by retention |
| 2 | Update | Clause applied in place + `-> hide` | Exchange against disposal |
| 2 | Object and prototype | Handler layer + state term | Answering against forwarding |
| 2 | Role seal (pending) | `PartialIso` from raw term to role + fresh salt, issued by the system sector | Interpretation against authority |
| 2 | Codec | `PartialIso` between two term forms | Total against partial |
| 2 | Stores | Terms behind a port | Fixed against governed; code by hash against a name |
| 2 | Witness | Handler layer + explicit fan-out | Witness against complement |
| 2 | Ask and Sample | Inward crossings | Agent-resolved against measure-resolved |
| 2 | Addressed memory (candidate) | Memory handler + address terms | Port identity against access lease |
| 3 | Certifier | The code seal + templates as types + rows | Certification against meaning |
| 3 | Commit barrier | Handler + speculation + inspection of the request | Compatibility against permission |
| 3 | Lineage and attenuation | Nested handlers for delegation and attenuation + construction for generation and inheritance | Generation, inheritance, reversibility and authority |
| 3 | Complement and ε | The root handler's retained term | Hidden, pruned, reclaimed or zeroed |
| 4 | Machine | `step : M <-> M` | Format against realization |
| 4 | Governed self-modification | Dynamic store + certifier + barrier + complement | Inspect, transform, verify, patch and install |
| 4 | Tasks | Sectors + a scheduler as root handler | Reproduced schedule against replayed execution |

### 5.2 Derived proposals

Each is this record's inference from reading the sources against each
other. Each holds only under the stated condition, and none is closed
until its obligation in §11 is specified and passes.

| # | Proposal | Support | Holds only if | Obligation |
|---|---|---|---|---|
| P1 | One mechanism per invariant fixes the count at three | §2 | The three invariants are the same across the sources, which rests in part on mediated claims | — |
| P2 | Certified primitives are clause sets (M3) | Direct: Weft §6 certifies a non-recursive `iso` by construction | A certifier accepts the tables and a realization executes them | V1 |
| P3 | The object is the bridge as a standing thing: an actor (reversible body, hosted irreversible messages) is Warp's handler layer plus state term | Direct on both sides. Author's account: L3 | Hosted messages and handler clauses have the same dispatch and the same accounting, and the actor is not merged into the prototype | V3, V12 |
| P4 | The ladders coincide: actor → system root → user roots → protos; root handler → system sector → user sectors; Weft's system root and user root | Direct for those three. Author's account for `root_proto` → `Object` → user prototypes | The system/user split is the same split in each. Weft's is a sector typing, this repository's a `facing` field | V5 |
| P5 | Freshness is one inward crossing: a clean bit, a seal's salt, a type's salt, a birth seed, a MAYBE draw | Direct for clean bits, salts, `Ask` and `Sample` (Warp). Derived for the birth seed and for this repository's MAYBE | The merged reading reproduces MAYBE, which here also advances the body by one tick and is not a bare inward crossing. Early Moop's MAYBE is a third thing again: an unresolved boolean (§14) | V3 |
| P6 | Stage is store-sealing: compile time, `RUNTIME_START` and the two stores are one distinction, with one evaluator | Direct: Weft's comptime; Warp's two stores and its register ("one compile-time and runtime representation and evaluator", design-level). Mediated: Moop's `RUNTIME_START`, Unicore's bootstrap arc | One evaluator serves both stages, and a prior run can produce the next system image | V8 |
| P7 | A handler layer or an explicit operations argument replaces Weft's meta records; lowering a resolved handler is one obligation (Weft Q3, Warp VP8) | Direct: Warp §6, "types do not direct dispatch; a handler or an explicit operations argument does". Mediated: Unicore's hoisted chain walk | The replacement keeps the coherence that meta records give by declaration | V9 |
| P8 | `mirrors` generalizes from involutions to any certified clause, with the involution moving to `invert` | Direct: Weft §6, exclusivity on the output side selects the backward clause | A certifier exists. Until then this repository's rule stands: every implemented form is an involution, and that is tested. Early Moop's `<->` is a different thing, a relation over integers. Neither is a case of the other as the sources stand (§14) | V1, V13 |
| P9 | The three placements of the pairing are levels, not rivals: grammar, format, realization, each a codec of the one above; a spelling is a projection | Direct: Weft's grammar → format → realization, its two projections, its profiles; this repository's word and arrow aliases | Print and parse, and encode and decode, round-trip as certified codecs; a projection reproduces every crossing | V10 |
| P10 | Lineage may be computed from construction history | Direct: Weft §11, the child retains its parent and its local specification | The birth relations preserve enough ancestry, and the computed relation reproduces the existing lineage predicate | V5 |
| P11 | Rebinding and re-teaching are exchanges | Direct: Warp pairing 12; Weft D2 case 5 | See M7: an exchange's inverse operand, complement retention and a live-version policy are three things | V6 |
| P12 | A taught chain can be read back because code is a term | Direct: Warp pairing 2 | The surface gains a way to hold a chain, and reading executes nothing | V2 |
| P13 | Early Moop's L2 is Warp's Function: an irreversible operation is a reversible gate into a prepared target, followed by a declared disposal | Author's account: L2 and Ancilla Discard. Direct: Warp's level-2 Function; Weft §6, lifting | The disposal is an explicit, counted operation, and the gate step stays reversible until it happens | V11 |
| P14 | Each of early Moop's four levels keeps a distinct composite: L1 the clause rules; L2 Function, and Complement and ε; L3 Object; L4 Lineage and attenuation, and the root | The author's correspondence table (§13). Direct: Warp §6 | The composites that share a pairing, and the uses that share rule (f), stay separately specified | V12 |

Two earlier claims are withdrawn rather than made conditional. "Hidden
is declared inertness" asserted that causal marks detect what `hide`
declares; that depends on a witness and instrumentation model and is
now obligation V4. "The lineage predicate is the construction clause
read backward" is replaced by P10.

## 6. The surface, as the existing records have it

This record assigns no merged reading to any glyph or word. Weft's
register settles that the divergence between Weft's and Moop's arrows is
intentional and that no equivalence is inferred from a shared glyph.
The records are:

| Form | This repository | Weft | Warp | Early Moop | Current Moop, as Weft describes it |
|---|---|---|---|---|---|
| `<->` | `mirrors`: a bijection, every form an involution | One clause of an `iso` | Clause | A persistent relation, a constraint over integers: free to declare, paid when realized | A bijective transformation |
| `->` | `ask`: message passing | A message to an existing task | Outward crossing | Binds, sends a message, routes output; ε increments on every bind | Marks dissipation |
| `<-` | `inherits`: a lineage predicate | Field-only inheritance | Inward crossing, and binding | Prototype delegation; ε increments | An ε = 0 operator |
| `is` | Binds a name; teaches a message | — | — | Categorical membership: walks the prototype chain and changes nothing | — |
| Birth | The article `a` / `an`; `clone` declined | A lineage constructor | `clone`, borrowed from Moop and retained | User protos clone from `Object` | — |
| Standing | Ruled and implemented | Settled in Weft's register | R3 and R4 assumed in Warp until ruled; `clone` retained by its register | Direct, from the handoff document (§14) | Mediated |

Two of these records disagree with each other on birth: Warp's register
retains `clone`, and this repository records the article as decided and
`clone` as declined. Neither is reopened here (M5).

No reading is shared by every record. Even `<->` divides: a persistent
relation in early Moop, a bijection in Weft, Warp and this repository.
`is` has two unrelated jobs, and `<-` costs ε in early Moop and nothing
in the current one.

## 7. Proposed deletions

A deletion is a claim that a uniform rule covers every use of a
construct. The first group is Warp's own; the second is conditional; the
third was proposed in the first draft and is withdrawn.

| Construct | Would be covered by | Standing |
|---|---|---|
| Weft's seven-mechanism kernel | Term, clause, port, the order rule and the certifier's rules | Direct in part: Warp's register classifies the relay's eight foundations, which cover Weft's mechanisms 1 and 3 to 7, several of them marked design-level, not shown or not derived. Derived for mechanism 2, structural records and variants |
| Reversibility as a bounded sector | Every machine step is a certified clause | Direct, Warp C01: an architectural assessment, with test status not implemented |
| `Dissipate`, ε_drop, the authorized receiver | `hide` to the root, and ε | Direct, Warp C02 and C03 |
| A general undo log; a destructive-update primitive | A certified clause supplies its own inverse; an overwrite is an update plus a declared disposal | Direct, Warp Dossier C; Weft D1, a first pass with nothing admitted |
| Meta records | P7 | Derived proposal |
| Comptime as a second evaluator | P6 | Derived proposal |
| The certified-primitive list | P2 | Derived proposal (M3) |
| This repository's irreversible logic layer, as an independent definition | Function: a clause plus `hide` | Derived proposal P13, supported by the author's account of L2 (§13) |
| `<->` as involution only | P8 | Derived proposal |
| The lineage predicate | — | Withdrawn. See M4 |
| Causal marks as the licence to prune | — | Withdrawn. See M6 |
| `clone` in favor of the article | — | Withdrawn. See M5 |
| The `Rebind` slot's version policy | — | Withdrawn. See M7 |
| The actor as a separate kind | — | Withdrawn. Early Moop gives actors and prototypes different responsibilities (§13) |

For this repository's own open questions, the merge proposes an
architectural answer at most. A design decision can close an
architectural question; it does not close a realization or verification
question.

| Open in `docs/model.md` or `docs/syntax.md` | Architectural answer proposed | Still open |
|---|---|---|
| General invertible functions under `<->` | The clause: two templates, exclusive on both sides (P8) | A certifier; arithmetic on a stated number type; floating-point rounding is not certified |
| Reflection | A taught chain is a code term (P12) | The surface form; that reading executes nothing; V2 |
| MAYBE's final semantics | A request answered by the body, with the reply an inward crossing (P5) | Whether that reproduces today's MAYBE; keeping agent-resolved and measure-resolved apart; V3 |
| How RAM exchanges values with the system layer | Through ports; addressed memory as a handler | Dossier P is a candidate with nine open obligations |
| How programs are encoded onto the loops | A codec between format and realization (P9) | Entirely open |
| Whether pruned cells are reclaimed or zeroed | Two measurement events of the third stage | Which of them this repository's prune is. See M6 |

## 8. Orthogonality

Direct, Warp §8:

| Mechanism | Its guarantee | How the other two preserve it |
|---|---|---|
| Term | Identity is content; no term changes | A clause builds new terms and never edits one. A port moves terms and never aliases one |
| Clause | The two readings are mutually inverse on the declared domain, and every hole is used once | A term has no hidden state, so matching is deterministic. A crossing has an inverse crossing or is a declared commit point |
| Port | Every crossing meets exactly one enclosing handler, and authority never exceeds the forwarder's | Holding a code term confers no port. A clause reaches nothing past its sector except through a crossing |

**Kept apart.** Warp's list stands (direct): logical reversal and
reversal by retention; hidden, pruned, and reclaimed or zeroed;
complement and witness; `Iso` and `PartialIso`; interpretation and
authority; inspect, execute and install; system store and dynamic
store; certification and meaning; generation, inheritance, reversibility
and authority; answering and forwarding; format and realization.

The author's review adds four that this record must not collapse:

- **Construction, delegation path, lineage.** A birth clause records a
  generation event. It does not by itself establish the lineage
  relation, least of all where inheritance, attenuation, cloning,
  replacement and authority provenance are involved. Warp's register
  already rules that the handler stack is the delegation path and not
  the lineage.
- **Logical hiding, root pruning, physical reclamation** (§3).
- **The inverse operand of an exchange, retention in the complement, a
  live version under a version policy** (M7).
- **The four responsibilities of early Moop's levels** (§13):
  reversible transformation, declared irreversibility, the entity that
  acts, and how such entities are defined, related, extended and
  governed. One pairing, Port × Term, carries the last two.

**Rejected** (direct, Weft §2 and Warp §8): implicit copy or drop in the
core; shared mutable references; a general undo log; installing over a
system binding; laziness; overlapping clauses resolved by order;
multi-shot continuations; raw-syntax macros; type-directed dispatch;
subtyping; ambient ports.

## 9. Guarantees

G1 to G7 are Warp's (direct). Warp says each follows from its
definitions if `step` passes its own certifier, and that none is proven.
The mapping to `root_proto`'s invariants is Warp's statement about
Unicore, so it is mediated. The last column is direct: it is what this
repository's tests assert, at the level of tapes and gates.

| Property | Statement | `root_proto` invariant | Asserted by this repository's tests |
|---|---|---|---|
| G1 Reversibility | `step` then its inverse is the identity on reachable, unpruned states | `reversibility_guarantor` | The core round-trips over a full cycle; each gate is self-inverse; `<->` twice is the identity |
| G2 Totality of ε | Pruning is the only map that is not injective, and nothing is pruned that was not first hidden | — | The opposite, for the core: pruning discards live state that was never hidden (M6). Pruned bits are counted; ε does not exist |
| G3 Closure | Every component of machine state is a term the root can match on | `homoiconicity_guarantor` | Both loops are written by execution. Names, taught chains and parent links are outside any reversible state |
| G4 Attenuation | A sector's crossings are a subset of what its enclosing handler forwards | `attenuation_terminus` | Actor lookup is local; delegation never crosses into the system root |
| G5 Enforcement | A rejected crossing does not take effect | `enforcement_binding` | Nothing |
| G6 Neutrality | Erasing every certificate changes no run | — | Nothing |
| G7 Fixed system store | No candidate replaces a system binding during a run | — | `maybe` and `value` refuse redefinition |

Warp's costs stand (direct): space for the complement, linear use,
interpretation, world effects as commit points, and concurrency.

## 10. Register of decisions

Entered from the review of 10 November 2026. Rulings are provisional. A
decision that conflicts with a prior ruling is not made by being listed
here; it needs that ruling formally reopened.

| Ref | Decision exposed | Prior record | Provisional ruling | Standing |
|---|---|---|---|---|
| M1 | The name of the merged architecture | Warp R1: "Warp" is a working name. Moop already names a source | `moop` is not ratified: reusing a source's name would collapse source and merger. Keep "Warp" as the working name or use an explicitly provisional label. If `moop` is chosen, record that it names the merged successor | Open. This record uses the label "the merged architecture", which is not a name |
| M2 | Standing of the sources | Warp R2 assumes Warp is a third design beside Weft and Moop | Not ruled; the relationship is undecided | Open. No source's standing changes |
| M3 | Removing rule (e) | Warp rules eight operational rules with a ninth pending | A plausible derivation, to be entered as a merger decision and not attributed to Warp. Definability and certification must be shown; the realization obligation remains | Proposed merger decision. Not adopted. V1 |
| M4a | `<-` as the inward crossing | This repository: a lineage predicate, decided. Weft's register: field-only inheritance, settled. Warp R3: inward crossing, assumed until ruled | Follows the existing record unless formally reopened | Not reopened. §6 |
| M4b | Dissolving lineage into the birth clause | This repository: generation and inheritance are distinct relations. Warp's register: the delegation path is not the lineage | Not dissolved. Lineage may be computed from construction history if the birth relations preserve sufficient ancestry and the result reproduces the existing predicate | Derived proposal P10. V5. Finding below |
| M5 | The article over `clone` | Warp's register retains `clone`. This repository decides the article and declines `clone` | Too compressed to settle. Preserve the existing `clone` ruling until the exact syntactic proposal and its consequences are shown. A keyword change is not a semantic derivation | Withdrawn. Both records stand in their own source |
| M6 | Pruning only what was hidden | This repository: causal auto-pruning is the one sanctioned exception, decided | Rejected as stated. Distinguish logical hiding, root pruning and physical reclamation. If auto-pruning removes logical state, the conflict is substantive and needs an explicit ruling | Rejected as stated. The conflict is substantive: finding below. Awaiting an explicit ruling; the implemented behavior stands |
| M7 | Re-teaching and rebinding as exchanges that keep the previous version | This repository: re-teaching replaces the chain. Weft §10: at most two live versions, "a resource policy, independent of hash identity" | Keep three things apart: the old value as inverse operand, the old value in the complement, the old version live under a version policy. The first two are requirements of reversible execution; the third is a separate policy | Not settled. P11, V6 |
| M8 | Stage as store-sealing | — | Not ruled | Derived proposal P6 |
| M9 | Warp's rulings | R1 to R10 | Not ruled | Stand as Warp records them. This record alters none |
| M10 | Early Moop's four levels as a source | Previously known only through Weft and Warp | The author's account: four cumulative levels with distinct guarantees. Their relation to the three mechanisms "is a correspondence, not a one-to-one derivation", and the later architecture "must not erase their different responsibilities" | Entered in §13. A handoff document for the same period was located the same day and differs from the account in places (§14). P13, P14; V11, V12 |
| M11 | Differences between early Moop and this repository | This repository: the logic layer is segregated from system memory; actors are non-hereditary; nothing user-facing goes on the tapes. All decided | Not ruled | Open. §13 lists two and §14 the rest. Nothing is changed |
| M12 | Which kernel: Term, Clause, Port, or Term, Relation, Message | Warp's register rules the count as three: Term, Clause and Port | Not ruled | Open. §14 sets the two side by side and does not choose. V13 has since been answered no, so the choice rests on K9 and K1, which are design decisions. V14 |
| M13 | A collision of identifiers | The second merge lists its own questions for ruling as M1 to M8, with other meanings | Not ruled | This record cites them as K1 to K8 |
| M14 | Whether early Moop's standing rules bind this repository and this record | The handoff: say commitment, rule, by construction, and not theorem, proof or iff; add no operators; count every overwrite. This repository's documents use "iff", "provably" and "proof", and re-teaching overwrites without a count | Not ruled | Open. This record now avoids those words outside quotation. Nothing else is changed |

### Finding for M6: what auto-pruning removes

Direct, from this repository's source and tests.

- `moop_core_prune` zeroes, in place, every set cell that has not been
  marked since the epoch began, and returns how many set bits it
  discarded. It reclaims no storage: the loops keep their length.
- A zeroed cell is not unreachable. It stays in the loop and passes
  under the gate once per rotation. On loop A it is also what `maybe`
  and `value` observe.
- `tests/test_core.c`, `test_pruned_value_fires_later`, pins a witness.
  With loops of 2 and 5 cells, A = `01`, B = `11000`: cell B[1] is set
  and unmarked at the epoch boundary (tick 10). Left alone it fires at
  tick 14, because A[0] was set at tick 5. Auto-pruning discards it at
  tick 10, and the pruned run then differs from the unpruned run in
  A[1] and B[0], which pruning never touched.
- An exhaustive scratch enumeration, not committed, covered every
  initial tape at the interpreter's body size (8 and 13 cells). Of
  2,097,152 states, 9,624 hold a set, unmarked cell at the first
  boundary. In 1,178 of them that cell fires within twelve epochs, and
  in those the pruned run diverges in other cells. Some small coprime
  pairs (3/4, 3/5, 4/5, 5/6, 5/7, 6/7) show no such state within forty
  epochs.
- The interpreter never calls `moop_core_prune` or `moop_core_run`.
  Bodies in a REPL session are never pruned; only the unit tests prune.

So auto-pruning removes logical machine state. It is not physical
reclamation, and the state it removes was never hidden by any
declaration. That conflicts with G2 as Warp states it. The witness also
bears on a sentence in `CLAUDE.md`, that unmarked cells hold values
"provably independent of the rest of the state": that is true of the
epoch just ended and not of the next. `docs/model.md` already records
the caveat. Neither file is changed here.

The ruling that is needed is which of these the merged architecture
takes. The record does not choose.

1. Auto-pruning stays a second lawful removal, beside pruning of the
   complement. Then "nothing is pruned that was not first hidden" does
   not hold, and its discarded bits need their own count. The
   repository already returns that count.
2. Pruning is restricted to what was hidden. That reverses a decided
   item and needs it reopened.
3. Auto-pruning is reclassified as part of the realization's dynamics
   rather than of the format. Then a run's result depends on the
   pruning schedule, and the format must say so.

### Finding for M4b: birth and lineage already differ here

Direct, from this repository's source and tests.

- `moop_proto_generate` sets `parent` to the generator only when the
  generator is user-facing. The system root generates `world`, and
  `world` has no parent (tested: "the system root generates user-facing
  roots with no parent").
- A proto stores no record of its generator. Generation is undone by
  stepping the generator back, not by reading anything in the child.
- `inherits` compares the child's `parent` with its right operand. It
  answers for the direct parent only (tested: "grandchildren do not lie
  about lineage").

So a relation computed from birth events alone would answer "the system
root" for `world`, where the predicate answers "no parent". P10 can hold
only if the birth relation carries the delegation parent separately from
the generator.

## 11. Verification obligations, foundational first

Each obligation names what must be shown before the proposal it guards
is treated as closed, and what exists today. They are ordered as §4 is:
the pairings before anything built on them. That is also early Moop's
direction of construction (§13): reversible operations, then declared
irreversibility, then actors and prototypes. Identifiers are not
renumbered, so V11 and V12 sit where they belong rather than at the
end. Warp's own obligations (VT1–7, VC1–8, VP1–9) are unchanged and not
repeated.

| ID | Guards | Must be shown | Exists today |
|---|---|---|---|
| V1 | Term × Clause; M3, P2, P8 | (a) CNOT and CCNOT, written as clause sets over a two-atom type, meet the clause conditions: first-order patterns, each hole once per side, exclusive and exhaustive on both sides. (b) A certifier establishes (a) and the inverse; a hand check does not count. (c) A realization executes the clause set in both directions and agrees with the gate layer. (d) The word-level updates certify as recursions that are structural in both directions | The gate layer's truth table and self-inverse tests. No clause form and no certifier |
| V2 | Term × Clause; P12 | A taught chain read back is a term; reading executes nothing; print then parse returns the same tree; a chain read back and taught again behaves identically | Nothing. The REPL reports that reflection is absent |
| V3 | Clause × Port; P3, P5 | The merged reading reproduces MAYBE as implemented: the same tapes give the same answers, the body's step is undone by stepping back, and the reply is the only irreversible product. Agent-resolved and measure-resolved stay distinguishable, and logic stays two-valued | The first two, at the level of tapes (`test_maybe`). Nothing for the merged reading |
| V4 | Clause × Port; `hide` and causal marks | Under a stated witness and instrumentation model: whether every hidden term is unmarked while it stays hidden, and whether marks ever flag what was not hidden | The second is answered no: an unmarked cell can be live (M6). Marks are documented as heuristic, conservative metadata |
| V11 | Clause × Port; P13 | AND is CCNOT into a clean target and NAND is CCNOT into a set one, as the account states. Repeating the gate undoes the step for as long as the inputs are retained. The result becomes irreversible only at an explicit disposal, and that disposal is counted once | CCNOT's truth table and the logic results are each tested, separately. `logic.c` computes its results directly; there is no disposal operation and no count |
| V5 | Port × Term; M4b, P4, P10 | The birth relations retain enough ancestry, and the relation computed from them equals the existing predicate for every proto in a session, including a user root and a grandchild | The predicate's own tests. No construction history |
| V6 | Port × Term; M7, P11 | Three separate results: an exchange returns the old value as its inverse operand; a disposed old value is in the complement and counted once; a version stays live only under a declared version policy, implied by neither | Nothing. Re-teaching frees the old chain |
| V12 | Port × Term; P3, P14 | A disposal reaching the root, an actor answering a message, and delegation through prototypes stay separately specified although one rule, (f), carries all three. In particular a `hide` reaches the root handler, while delegation stops at a user root and never enters the system root | Delegation stopping at the user root is tested. Nothing for the rest |
| V7 | The machine; M6 | After the ruling: the three measures stay separate and correctly dimensioned (Warp VC6), and whichever removal is lawful is the only one | The classification itself: auto-pruning removes live state (`test_pruned_value_fires_later`) |
| V8 | The machine; P6 | One evaluator serves both stages; no candidate replaces a system binding during a run (Warp VT1, VT6); the bootstrap chain is stated and checked (VT7) | Nothing |
| V9 | Corollary; P7 | A statically resolved handler lowers to a direct call without semantic drift; the replacement for meta records is coherent | Nothing |
| V10 | Corollary; P9 | Print and parse, and encode and decode, round-trip; a native projection reproduces every crossing | Deposit twice is the identity; decode observes without effect |
| V13 | Term × Clause; M12, P8 | Warp's clause is exactly the certified case of early Moop's relation: every hole determined in both directions, templates exclusive. For each remaining case, one unknown, several, and none, either what covers it in a clause-only kernel or that nothing does | The first half is answered no, by the second merge's reading of early `moop.c` (mediated; §14). This repository has neither form |
| V14 | The machine; M12 | Under either kernel, no state change bypasses the barrier, bootstrap included, and a rejected attempt leaves what that kernel says it leaves: nothing unless a witness sits there (Warp G5), or κ and γ (early Moop) | Nothing. This repository has no barrier |

A build order for this repository would follow the same sequence. None
is scheduled, and no step that depends on an open ruling can start.

## 12. Status

**Source-established.** Weft: the selection rule and nine constraints,
the dossier, recursive unification, `Iso` and `PartialIso` with their
clause conditions, code identity, realization profiles. Warp: the three
mechanisms and their rules, the grouping of pairings, the composites of
§5.1, the machine term, the fixed system store, complement against
witness, the three stages of loss, G1 to G7 as design claims. This
repository: the tape model, the bridge shape, generation against
inheritance, the surface, the deletion test.

**Author's account.** Early Moop's four levels and their cumulative
order; Ancilla Discard at L2 and Message at L3; the prototype lineage
`root_proto` → `Object` → user prototypes, with the root as the
terminus for system-wide guarantees (§13).

**Located on 10 November** (direct, §14). From the handoff document:
early Moop's five-box design layering and its generation order; the
commit barrier at L1; ε, κ and γ as independent observables; the four
operators with their costs; MAYBE as an unresolved boolean in two forms;
`clone`; "the tape is reality, RAM is a view". From the second merge: a
different kernel for the same four sources, and its ten objections to
Warp's reading of Moop.

**Reported, not established** (mediated). Everything about `MOOP.md`,
`moop.c` and Unicore's `SPEC.md` that the two located documents cite and
this session could not open. Unicore: the two axes, the four named
invariants of `root_proto`, the hoisted chain walk, the bootstrap arc,
the operator order as the prototype chain. The current Moop's arrow
readings, admission on every write, 𝒯_Moop and `RUNTIME_START`, as Weft
and Warp describe them.

**Derived proposals.** P1 to P14, the four names of §4 and the reading
of the machine as the triple, each pending its obligation.

**Ruled and implemented.** Only this repository's own items, as
`CLAUDE.md` lists them. Among those this record touched and did not
change: `<-` as a lineage predicate, the article as birth, causal
auto-pruning, and re-teaching replacing the chain.

**Open.** M1, M2, M6, M11, M12 and M14 await rulings. M3, M5 and M7 await the
showing each provisional ruling asks for. Warp's open items stand,
chiefly whether `step` can be written as a certified clause set,
inference under linear use, static exclusivity, iteration without
history, the pruning policy and where its authority sits, and the causal
order of crossings between concurrent sectors.

## 13. Early Moop's four levels

Entered on 10 November 2026 from the author's account. It is first-hand
and retrospective. A handoff document for the same period was located
afterwards and differs from this account in places; §14 compares them.
Formulas are given in plain text.

"Early Moop was layered from the logic of computation to the
organization of the entities that compute." Each level introduces a new
kind of structure and depends on the guarantees established below it.

| Level | Introduces | The account's statement | Constituent it names |
|---|---|---|---|
| L1 | Reversible operations and gates | An operation's output determines its input: a bijection over the relevant state space. NOT, CNOT, CCNOT. Computation is a transformation of an existing state, so the program need not be treated as separate from the state it transforms | CCNOT |
| L2 | Irreversible logic | AND, OR and NAND do not replace L1. They are constructed from its gates together with an explicit operation that discards information: (a, b, 0) → (a, b, a ∧ b), and (a, b, 1) → (a, b, ¬(a ∧ b)). "Irreversibility is an explicit construction, not an unexplained property of the underlying machine" | Ancilla Discard |
| L3 | Actors | The entities that perform computation. They execute operations, maintain state and interact through messages. An actor is not another gate | Message |
| L4 | Prototypes | How actors are defined, related, extended and governed: shared behavior, inherited operations, delegation when an actor does not handle a message, and a root that is the structural terminus for system-wide guarantees. Later documented as `root_proto` → `Object` → user prototypes | — |

The account places neither Tape nor Commit Barrier, and does not mention
MAYBE. The handoff document places all three (§14).

**The composition rule.** "The levels are cumulative, but their
guarantees remain distinct. A prototype does not make an operation
reversible. An actor does not make information disposal legitimate
merely by invoking it. An irreversible logical operation does not change
the reversible character of the gates from which it was constructed."

**The direction.** In the account's words, "the object system was built
over a theory of computation, rather than the computation being defined
as an incidental behavior of objects."

### The author's correspondence

"This is a correspondence, not a one-to-one derivation." The last
column is this record's: where Warp's composites (direct, §5.1) would
hold each level.

| Early Moop | Concern | Later correspondence | Warp's composites |
|---|---|---|---|
| L1 | Reversible transformation | Clause | Rules (c), (d) and (e). M3 is a question about exactly this level |
| L2 | Declared irreversibility | Clause + Port | Function and Update; Complement and ε |
| L3 | Actors and interaction | Port + Term | Object: answering |
| L4 | Prototypes and inheritance | Term + Port | Lineage and attenuation, and the root handler: forwarding, construction, governance |

### What the comparison shows

All four points are derived.

1. **Four levels do not map onto three pairs and a triple.** L1 is one
   mechanism. L2 is one pairing. L3 and L4 are the same pairing. Term ×
   Clause has no level: in the account it is a consequence stated inside
   L1, that the program need not be separate from the state. Term alone
   has no level either.
2. **Early Moop orders what Warp places side by side.** Function and
   Object are both level-2 composites in Warp. In early Moop,
   irreversible logic lies below actors, and nothing at L2 needs an
   actor or a message. In Warp a disposal is a `hide`, a request that
   propagates to the root handler, so declared loss is expressed with
   the mechanism that also yields actors and prototypes. The author's
   correspondence accepts Port at L2. The order still matters for
   construction: a build or a demonstration that follows early Moop establishes
   disposal before it establishes entities.
3. **One rule carries three responsibilities.** Warp's rule (f),
   propagation to the nearest enclosing handler, covers a disposal
   reaching the root (L2), an actor answering a message (L3) and
   delegation through prototypes (L4). Warp states directly that
   prototype delegation and the propagation of an unhandled request are
   one rule. That is where the unification sits, and it is where the
   account says the responsibilities differ. Warp does keep answering
   apart from forwarding, and holds delegation and attenuation as
   separate clause sets on a shared stack. Its level-2 composite is
   nonetheless named "Object and prototype": one composite for L3 and
   L4. Whether one rule with three uses is one rule, or three behind one
   name, is obligation V12.
4. **The three sentences on distinct guarantees each have a direct
   counterpart.** A prototype does not make an operation reversible:
   in this repository bodies take reversibility from the substrate and
   not from each other. An actor does not legitimate a disposal by
   invoking it: in Warp no handler can absorb a `hide`. An irreversible
   result does not change the gates beneath it: in Warp a function is a
   certified clause plus a crossing, and the clause stays certified.

### The account and this repository

Direct, from the source and the commit history. The differences are
recorded for ruling (M11) and nothing is changed.

| Level | Agrees | Differs |
|---|---|---|
| L1 | `src/gates.c`: NOT, CNOT, CCNOT, each tested as self-inverse, and SWAP | — |
| L2 | `src/logic.c`: AND, OR, NAND, NOR, XOR as an irreversible layer | The results are computed directly on plain values. They are not constructed from the gate layer, and there is no disposal operation and no count of what is disposed. `CLAUDE.md` forbids this layer from writing system memory at all. MAYBE lives in this file |
| L3 | `src/actor.c`: a reversible body and a table of hosted messages | Lookup is local and a miss never delegates. The interpreter has one actor, the static system-facing one |
| L4 | `src/proto.c`: delegation up parent links, under a root | A proto is a separate type from an actor: the same body and message table, plus `parent` and `facing`. In the account prototypes organize actors and give them delegation; here "actor" names only what has no lineage |
| Order | The history adds the core, then the logic layer, then actors, then protos | — |

The label "L1" also occurs in Warp's description of Unicore ("an L1-wide
invariant", "`<->` pairs at L1"). Whether that is this L1 is not
established, and nothing is inferred from the shared label.

The second row's difference about actors is explained in §14: this
repository follows the distinction between actor and proto that the
second merge reports from Moop's later sources, while early Moop's own
L3 actors carry a prototype chain.

## 14. Two documents located on 10 November

### What was read, and what could not be

| Document | What it is | Read |
|---|---|---|
| *Early Moop: Handoff and Layering* | A handoff for early Moop: the system from its first commit on 20 March 2026 through its release of 14 April, last changed on 20 April, after which work moved to Unicore. It reports on that system's specification (`MOOP.md`), its build plan and its source (`moop.c`) | In full, with its diagram |
| *Merged Kernel: Moop, Unicore, Weft, Warp* | A second merge of the same four sources. It read Moop's and Unicore's own records (`MOOP.md`, `moop-bootstrap.c`, Unicore's `SPEC.md`), Warp as pasted, and of Weft the correspondence tab and §1, §2, §11, §13 and §14. It did not read Warp's dossiers or either register | In full, except its one diagram; the table that diagram draws was read |

The repository that holds `MOOP.md`, `moop.c` and `SPEC.md` is not
available to this session, so none of the three was opened. What the two
documents say about them is mediated, though it comes with section
citations.

The two merges read complementary halves. This record read Weft and
Warp whole and none of Moop's or Unicore's records. The second merge
read Moop's and Unicore's records and neither dossier nor register.

### Three things named Moop

| | Early Moop | Current Moop (Unicore) | This repository |
|---|---|---|---|
| When | 20 March to 20 April 2026 | After April 2026 | From 15 July 2026 |
| What | One C file that builds a prototype-based message-passing language on a reversible gate tape, later partly rewritten in itself | The successor. The handoff says Moop is "evidence for those projects, not their substrate" | A separate C23 implementation. It contains none of early Moop's commits |
| Known here through | The handoff document (direct) and §13 | The second merge's citations of `SPEC.md`, and Weft and Warp: all mediated | Its source and tests (direct) |

This repository follows early Moop's design layering closely at the
bottom and leaves most of the rest out.

- **Shared**, direct on both sides: two counter-rotating tape loops; the
  gates NOT, CNOT, CCNOT and SWAP; causal pruning; the irreversible
  gates AND, OR, NAND, NOR and MAYBE; one bootstrap actor that generates
  the root; an Io-like, Quorum-like, whitespace-structured surface.
- **In early Moop and absent here:** the commit barrier; the observables
  ε, κ and γ; reversible compositions that host the irreversible gates;
  ancilla bits that keep hidden state; MAYBE as an unresolved boolean;
  `<->` as a relation; `is` as membership; message queues on tape, a
  scheduler, and governance.
- **Opposite here:** early Moop's first commitment is "the tape is
  reality, RAM is a view": wipe RAM, rebuild from tape, and state must
  be identical. This repository keeps user code in RAM and puts nothing
  user-facing on the tapes, by decision.

### Early Moop's design layering, from the handoff document

"The runtime is a generation chain from a reversible tape up to a
governed language. L2 is split in two, so the stack has five boxes."

| Layer | Name | Contents |
|---|---|---|
| L1 | McCarthy: the reversible tape, "ground, not generated" | Two counter-rotating tape loops; NOT, CNOT, CCNOT, SWAP; the commit barrier (simulate, classify, execute); κ detection; region lifecycle; causal pruning |
| L2a | Prigogine substrate: reversible compositions | Reusable compositions of L1 gates, still fully reversible. Hosts every L2b gate |
| L2b | Prigogine interface: irreversible gates | AND, OR, NAND, NOR and MAYBE: "irreversible to the user, hidden state kept in ancilla bits". MAYBE is an unresolved boolean: MAYBE? is agent-resolvable, MAYBE~ stochastic |
| L3 | Turchin: actors and messages | Actors with slots, actions and a prototype chain; message send and delegation; message queues commit to tape; a scheduler |
| L4 | Moop: the language the programmer writes | `root_proto` (governance, system-facing) generates `Object`; user protos clone from `Object`; tokenizer, parser, interpreter, bootstrap, transactions. "Selection criteria live here as policy" |

The line between L2a and L2b is marked: "Irreversibility emerges above
this line; everything below it is reversible."

Each layer is generated by the layer below. L2a generates L3 directly;
L2b is the interface L2a hosts, "not a rung actors are built from"; one
bootstrap actor generates `root_proto`. The specification's stated
reason for the order is reversibility first (possibility),
irreversibility second (mechanism), actors third (negotiation),
governance fourth (criteria).

Every state change at any layer passes the L1 commit barrier: simulate
on shadow state, classify as VALID, SIGMA_BOUNDARY or KAPPA_VIOLATION,
execute on tape only if classification passes, then project into RAM.
"Rejection is not a no-op." Three observables are independent: ε records
irreversible intended work, κ records structural divergence with failed
attempts included, and γ is the commit log of both.

The handoff also lists standing rules for anyone changing Moop. Three
bear on this record (M14): say commitment, rule, by construction, and
not theorem, proof or iff; add no operators; count every overwrite,
because an ε mismatch between two implementations is an audit signal.

**Against the author's account in §13.** The order of the levels
agrees. Five things differ.

| Point | §13 | Handoff document |
|---|---|---|
| L1 | Reversible operations and gates | The tape itself, with the commit barrier and causal pruning at this level |
| L2 | One level: irreversible logic built from gates plus an explicit discard | Two: reversible compositions, and the irreversible gates they host |
| What makes L2 irreversible | The system discards information | Hidden state is kept in ancilla bits; the gate is irreversible "to the user" |
| Delegation | Arrives with prototypes, at L4 | Already at L3: actors have a prototype chain |
| L4 | Prototypes | The language and its governance |

The third row matters for M6 and V11. Keeping hidden state in ancilla
bits is logical hiding in the sense of §3. It is not disposal.

### Ten points where the second merge says Warp misreads Moop

Its summary: "Warp reads Moop as a reversible machine with an erasure
counter. Moop is a relational language on a governed substrate." What it
says about the Moop sources is mediated. The fourth column says whether
the handoff document, which is direct, bears it out.

| # | Warp (direct) | The Moop sources, as the second merge reports them | Handoff document | Carried in this record |
|---|---|---|---|---|
| 1 | `<->` is a certified bijection with "the same local meaning as in Moop" | A persistent constraint relation. One unknown: solve by inversion. None: a consistency check. Two or more: it stays active and propagates to a fixpoint | In part. A persistent relation, yes. The four cases are not early Moop's: see the correction below | P8; §6 |
| 2 | `<-` is an inward crossing and a binding | The prototype edge: declared once, traversed on read, free of ε | In part. Delegation, yes; but in early Moop `<-` increments ε | Rule (f), as Warp's; M4a |
| 3 | No `is` | The fourth operator: a readout that walks the chain and changes nothing | Yes | Nowhere. `is` here has another job |
| 4 | The commit barrier is a level-3 composite | One of five bootstrap primitives | Yes: no write bypasses it, bootstrap included | §5.1 |
| 5 | A rejected crossing is run back, and recorded only where a witness sits | "Every rejection writes a κ scar" | Yes: "Rejection is not a no-op" | G5 |
| 6 | No divergence measure | κ is a structural measure, the popcount of Δ | Yes | Nowhere |
| 7 | A witness is optional and removable | γ sits in the operator chain; every step leaves a record | Yes: γ is the commit log | §5.1; G6 |
| 8 | MAYBE is two inward crossings over two-valued logic | An unresolved boolean that propagates through logic before anything resolves it | In part. Unresolved boolean, yes; propagation is not stated | P5 |
| 9 | The mechanisms are "complementary aspects, not modules" | The layers are a generation chain, and the operator order is the prototype chain itself | In part. The generation chain, yes; the operator order is not stated | §4 |
| 10 | An object is a handler layer plus a state term | Actors, without delegation, and protos, with it, are different things; a non-hereditary bootstrap actor generates `root_proto` | In part. The bootstrap actor, yes; but early Moop's L3 actors delegate | P3; M11 |

Five are borne out and five in part. On point 10 this repository matches
the second merge's statement exactly, which is why M11's second
difference appeared.

The second merge also says what Warp gets right: its pairing of
homoiconicity and reversibility, and its closure rule.

### Two candidate kernels

| | This record (§2 to §5) | The second merge |
|---|---|---|
| Mechanisms | Term, Clause, Port | Term, Relation, Message |
| Written with | No reading assigned (§6) | Moop's four operators: `<-` and `is` for Term, `<->` for Relation, `->` for Message |
| Transformation | A clause: two linear templates, exclusive on both sides | A relation, solved by how many holes remain. By its own correction this generalizes both sides: it widens Moop's relation from integers to terms, and Warp's clause from one case to four |
| Interaction | A crossing to the nearest enclosing handler, outward or inward | A send, resolved along the `<-` chain to `root_proto`. Input is a send whose answer fills a hole, so there is no inward arrow |
| The barrier | A level-3 composite | "The rule of sending": first, not built later |
| The record | A witness: optional, and removing it changes no result | γ: what the barrier leaves, not removable |
| A rejection | Run back | Leaves κ and γ |
| Measures | ε in bits per `hide`; pruned bits; bytes | ε, κ and γ, with Warp's three stages kept |
| Foundation | Three pairs and a triple, symmetric | Five pairings in Moop's generation order: the reversible ground, then measurement, then the barrier; dynamics after |
| Role seals and addressed memory | Pending and candidate, with their dossiers read | "Enter as compositions or not at all"; dossiers not read |
| RME-7 | A model written in the language (Warp R8, Weft §14) | Constitutive (Unicore's specification); flagged as a conflict between sources |

They agree on three mechanisms, Weft's selection rule, Warp's term-level
scope and closure rule, the three stages of loss, linear holes, the
rejections carried from Weft and Warp, no name, and that nothing is
implemented.

The second merge lists nine questions for ruling, the ninth added with
its correction. They are cited here as K1 to K9 (M13). Five touch this
record directly.

| Ref | Its question | Bears on |
|---|---|---|
| K1 | Are a hole, an unknown and a MAYBE one notion? It assumes yes, calls this its one new unification, and notes the stretch | M12: its joining of clause and relation rests on this |
| K2 | Is RME-7 constitutive of the language, or a model written in it? | M9. Weft §14 says RME-7 is a model represented in Weft, as the second merge notes. Weft's register, which it did not read, adds that Moop's κ, a popcount meter, shares a symbol with RME-7's admissibility gate, and leaves that for ratification |
| K5 | What does ε count? Warp's three stages with Moop's one-per-overwrite as the event count; "the two units have not been reconciled" | §3: this record's ε is Warp's, in bits |
| K8 | The name | M1. It proposes none |
| K9 | Is Warp's clause the certified case of Moop's relation? "Not as the sources stand." It becomes so only if the relation is widened from integer arithmetic to terms and its lossy solves are declared as `PartialIso` domains, which it assumes and does not treat as ruled | M12, V13, P8 |

### The second merge's correction

Read from the second merge at its ninth revision, dated 10 November.
The correction itself is direct. What it reports of early `moop.c` is
mediated.

V13 asked whether Warp's clause is exactly the certified case of early
Moop's relation. The second merge checked its own claim against the
relation solver in early `moop.c` and answers no, in three ways.

| | Early Moop's relation | Warp's clause |
|---|---|---|
| Domain | Integer arithmetic over three participants: `+`, `-`, `*`, `/`, `=` | A pair of templates over arbitrary terms |
| Inversion | Solving `*` and `/` uses truncating division, and a zero operand solves to 0. Those solves lose information | A bijection on its declared domain |
| Lifetime and violation | A relation deactivates once it solves or checks, and a failed check prints `false` | Not applicable |

Treating a violated relation as Φ = ∅ is Unicore's later adaptation and
not early Moop's behavior. So the four-case relation is the second
merge's proposal, not a finding about the sources: in its words, it
"generalizes both sides". Point 1 of the ten is borne out only as far as
this: Warp's clause would cover one case of the four.

This bears on the present repository too. Its `<->` is restricted to
involutions so that bijectivity is a tested fact, and oversized values
are refused. Early Moop's solver took the other course and let a solve
lose information.

### What follows for this record

1. **Its foundation describes Warp, not the four sources together.**
   Sections 2 to 5 take Warp's reading of Moop. On five of the ten
   points Moop's own handoff document supports the second merge against
   that reading, and on five more in part.
2. **Its tested findings stand.** The pruning witness (M6) and the
   difference between birth and lineage (M4b) are facts about this
   repository. Whether early Moop's causal pruning also removes live
   state is not known here.
3. **Each merge holds what the other lacks.** This record holds Warp's
   register rulings (the count ruled as Term, Clause and Port; the
   handler stack as the delegation path and not the lineage; `clone`
   retained), both dossiers, Weft's register and whole specification,
   the author's provisional rulings, and the verification obligations.
   The second merge holds Moop's and Unicore's records.
4. **The choice of kernel is M12, and it now rests on two design
   decisions.** V13 was the one question of fact, and its answer is no:
   neither kernel's transformation contains the other's as the sources
   stand. The relation contains the clause only after it is widened by
   decision (K9). The joining of hole, unknown and MAYBE is likewise a
   decision (K1); the only source support its author reports is that a
   MAYBE participant counts as an unknown inside the solver, and nothing
   in Moop makes a non-boolean term unresolved.
   Neither can be settled by reading a source.
5. **Early Moop puts first what Warp builds late.** §13 found this for
   disposal. The located documents add the barrier and the measure of
   divergence, both at L1 in early Moop, and the record the barrier
   leaves. In Warp the first is a level-3 composite, the second is
   absent and the third is optional. Of the two foundations, the second
   merge's follows early Moop's direction of construction and §4's does
   not.
