# poiesis — an RME-7 interoperability substrate in ISO C23

**Normative specification.** The specification defines the predicates and invariants; ISO C23
realizes them. **C23 does not supply the meaning of RME-7.**

---

## 0. What poiesis is

Poiesis retains the typed information and contractual structure required for later **assessment of
specified relations** and, where their compatibility contracts are satisfied, for **realization by
downstream mechanisms** — without redesigning the declared ontology or port interfaces.

Poiesis is never the subject of the verb *realize*. It does not perform interoperability; it prevents
premature loss of the possibility of it.

Three claims, kept apart. Poiesis is about the third:

| | claim |
|---|---|
| Interoperability | two objects actually interoperate |
| Composability | two objects satisfy the declared conditions for a specified relation |
| **Latent interoperability capability** | objects retain enough typed structure, identity, contracts and relation-bearing representation that a compatible future relation can be introduced without redesigning their declared ontology or port interfaces |

**Not promised:** that any two conformant objects will eventually interoperate. Preservation does not
create compatibility; it keeps compatibility an open question rather than a foreclosed one.

### 0.1 Three properties, never conflated

```
retained            the distinction is physically present in the representation
declared            it is part of the declared boundary
publicly reachable  it can be reached across that boundary
```

Wherever a future relation or observer is claimed to be addable **without boundary redesign**, the
required information must satisfy **all three** conditions:

1. it is **represented** in the retained substrate representation;
2. it is **retained** after realization compression; and
3. it is **reachable** through the declared public interface.

Internally retained but unreachable fails condition 3: reaching it would itself force an interface
change.

### 0.2 Substrate invariant

> Poiesis preserves **boundary-relevant distinctions** whose current substantive realization is
> unnecessary but whose loss would require redesign of the declared ontology or interface.

Realization compression ≠ boundary compression. Caches, temporaries and optimized-away computation
may vanish freely; a required boundary distinction may not.

### 0.3 Governing principle

- **Principle.** Minimize substantive realization without minimizing the expressive distinctions
  retained by the declared schema.
- **Maxim.** *Minimize what must exist now; preserve what must remain distinguishable later.*
- **Compression rule.** *Compress behaviour, not ontology.*

---

## 1. The three predicates and the firewall

```
AXIS A — CONFORMANCE        AXIS B — COMPOSITION          AXIS C — OBSERVATION
  schema                      declared relation R_C         transition/dependency graph
  port completeness           endpoint validity             governed-state projection
  type validity               ACTIVE endpoints              SCC / cycle analysis
  status-selected contract    compatibility                 classification
  ↓                           ↓                             ↓
  rme7_conforms(P)            rme_compose_valid(P,Q,R_C)    rme_classify(S)
```

```
rme7_conforms(P)  ≢  rme_compose_valid(P,Q,R_C)  ≢  rme_classify(S) = RME_CLASS_RME7
```

**No predicate may acquire another predicate's authority.** The firewall is structural, not
conventional: `rme7_conforms()` consumes an `RmePrototype`; `rme_classify()` consumes an `RmeSystem`.

Axes A and B are the **core substrate**. Axis C is **observational** — a conformant implementation may
omit the classifier entirely and remain valid.

### 1.1 Three relation-like structures

```
R_C    composition relation  — declared port connections submitted to ComposeValid
R_N    nesting relation      — parent/child containment
E_GS   governed-state edges  — dynamical dependency edges consumed by Axis C

                    R_N  ≠  R_C  ≠  E_GS
```

---

## 2. Non-equivalences

| | |
|---|---|
| **N1** | Schema-complete ≠ semantically exhaustive |
| **N2** | Prototype conformance ≠ universal composability |
| **N3** | Port compatibility ≠ composition |
| **N4** | Port status ≠ operator status |
| **N5** | Latent interoperability capability ≠ interoperability |
| **N6** | Retained endpoint capability ≠ existence of a future compatible relation |

Latent interoperability is **not** a fourth conformance axis. There is no
`rme_latently_interoperable(P,Q)` and there must not be.

---

## 3. Frozen propositions

| | |
|---|---|
| **F1** | `RME7Conforms(P)` means P satisfies the schema and realization contract; it **does not require substantive realization of every RME-7 operator.** A conformant prototype may have several active operators. |
| **F2** | Every schema-required port is declared with exactly one status, `Status(p) ∈ {ACTIVE, VESTIGIAL}`. |
| **F3** | Operator vocabulary and port status are distinct typed concepts; neither implies the other absent an explicitly declared relation. |
| **F4** | `RME7Conforms(P)` is **unary**; `ComposeValid` is **relational**. Never combined. |
| **F5** | Only explicitly declared connection endpoints in a composition relation `R_C` incur compatibility obligations. `R_C` is a relation, not an event. **No connection relation may be inferred from prototype coexistence, nesting, port-name equality, type equality, structural adjacency, or execution order.** |
| **F6** | "RME-7-conformant" and "classified RME-7" are distinct predicates despite sharing the label. No code, comment or report may collapse them. |
| **F7** | **Prototype validity and RME conformance are nonhereditary.** Neither conformance, validation status, port status, contract satisfaction, identity, nor classification is inherited from an ancestor, container, referring prototype, root prototype, actor, or provenance chain. Each prototype is assessed against its own declared schema and applicable contracts. |
| **F8** | **Capability/validity non-transfer.** An actor's authority, capability, trust status, provenance, or authorization to construct a prototype **does not confer** validation, conformance, classification, port status, contract satisfaction, or identity upon the constructed prototype. A prototype acquires those properties only through its own applicable validation or classification procedure. |
| **F9** | **Authority/validity independence — bidirectional.** A capability authorizes an attempted construction; it does **not** establish the semantic validity of the resulting representation. Validation establishes semantic validity; it does **not** grant construction authority. No operation may derive either property from the other. |
| **F10** | **Typed-relation orthogonality.** Authority, provenance, representation, and semantic predicates are **distinct typed relations**. No relation, property, or status belonging to one relation class may be inferred from one belonging to another, unless an explicitly declared rule establishes that implication. Operationally: authority may authorize construction · construction may create provenance · validation may establish semantic validity. **None of these causal or provenance relations constitutes semantic inheritance.** |
| **F11** | **Scoped inheritance.** The term *inherit* is meaningful only with an explicitly named inherited property and relation. **Unqualified inheritance is not a semantic operation in poiesis** — it is a type error, not a style lapse. Permitted, each only when explicitly declared: capability (subject to Grant/attenuation) · behavioural derivation · provenance recording. Prohibited absolutely: validation · conformance · port status · endpoint compatibility · identity · classification · contract satisfaction. |

**F10 corollary — derivation is not laundering.** Structural derivation of a representation transmits
representation, not predicates. `P₂ = clone(P₁)` may mean that `Representation(P₂)` and
`Behaviour(P₂)` derive from `P₁` and that `Provenance(P₂)` records `P₁`. It may **never** mean
`Conforms(P₂) := Conforms(P₁)`. `Validate(P₂)` and `Conforms(P₂)` are still established
independently. Consequently **"inherited" with no named property is illegal vocabulary** — §8.2.1's
rule is type discipline, not editorial hygiene.

### 3.1 Prohibited inferences

```
Compatible(p,q)   ⇒  Compose(P,Q)          ✗   compatibility is a property of an endpoint pair
¬Compatible(p,q)  ⇒  ¬RME7Conforms(P)      ✗   incompatibility unmakes neither prototype
ACTIVE(κ_port)    ⇒  κ instantiated        ✗
VESTIGIAL(κ_port) ⇒  κ absent              ✗
HardWiredArgs(T)  ⇒  ¬RME7Conforms(T)      ✗   a realization strategy is not an RME-7 constraint
VESTIGIAL(p)      ⇒  Elidable(p)           ✗   elision is an optimization, not a semantic rule
Classify(S)=RME7  ⇒  RME7Conforms(P)       ✗   classification has no authority over conformance
coexistence       ⇒  R_C                   ✗

Conforms(P₁) ∧ ChildOf(P₂,P₁)       ⇒  Conforms(P₂)        ✗   F7
ClassifiedRME7(P₁) ∧ ChildOf(P₂,P₁) ⇒  ClassifiedRME7(P₂)  ✗   F7
TrustedActor(A) ∧ Produced(A,P)     ⇒  RME7Conforms(P)     ✗   F7 — provenance is not authority
Authorized(A, construct(P))         ⇒  RME7Conforms(P)     ✗   F8
Capability(A,c) ∧ Produces(A,X)     ⇒  Validated(X)        ✗   F8
Validated(X) ∧ ChildOf(Y,X)         ⇒  Validated(Y)        ✗   F8

Validated(P)                        ⇒  Capability(P, …)    ✗   F9 — the reverse edge
Conforms(P)                         ⇒  Authorized(P, …)    ✗   F9
P₂ = clone(P₁) ∧ Conforms(P₁)       ⇒  Conforms(P₂)        ✗   F10 corollary
Derived(rep(P₂), rep(P₁))           ⇒  Validated(P₂)       ✗   F10 corollary
```

> **ProtoC is a reference realization of the authority-side transition system; poiesis is the
> semantic-side substrate. They share no semantic inheritance relation.**

That is its status — not "historical inspiration", and not a second prototype system overlapping this
one. ProtoC governs *permission to produce*; poiesis governs *what the produced representation is
permitted to mean, and which boundary distinctions it must preserve*. Their apparent
overlap was an artifact of collapsing production, provenance, authority and semantic validity into a
single inheritance picture; F7–F10 are exactly the vocabulary that prevents that collapse. The naive
mapping needs one correction: **ProtoC's `clone` is not the analogue of validation** — `clone`
reproduces representation, `Grant` moves authority, and validation is the semantic machine's own
operation with no ProtoC counterpart.

### 3.2 Dependency directions

```
Preservation    → enables observation.    Observation  → never establishes preservation.
Schema          → permits relation.       Relation     → never establishes schema conformance.
Representation  → preserves possibility.  Possibility  → never asserts realization.
```

---

## 4. Predicates

```
RME7Conforms(P)  ⟺  SchemaValid(P) ∧ PortComplete(P) ∧ TypeSafe(P) ∧ RealizationValid(P)

ComposeValid(P,Q,R_C)  ⟺  Declared(R_C) ∧ EndpointsValid(R_C)
                          ∧ ∀(p,q) ∈ R_C : Active(p) ∧ Active(q) ∧ Compatible(p,q)

NestedValid(P,K)  ⟺  RME7Conforms(P) ∧ RME7Conforms(K) ∧ ParentChildRelationValid(P,K)

RealizationValid(p) = ActiveContract(p)      if Status(p) = ACTIVE
                      VestigialContract(p)   if Status(p) = VESTIGIAL
```

Absent from `RME7Conforms(P)`: `UsesEveryOperator(P)`, and any composition clause.

**Three stages, never conflated:**

```
Admissible(R_C, P, Q)  ≠  Declared(R_C)  ≠  Executed(R_C)
```

> `Admissible(R_C, P, Q)` holds **iff** every endpoint required by `R_C` exists in the declared
> schemas, has the required identity and type, has **`Status = ACTIVE`**, and satisfies the applicable
> endpoint compatibility contracts.

The ACTIVE requirement is **unconditional**. A relation able to connect a vestigial endpoint would
have to be a *different, explicitly declared relation class* — never an exception embedded inside
`Admissible`.

```
Admissible(R_C,P,Q)   compatibility predicate
Declared(R_C)         relational configuration
Executed(R_C)         downstream operational event

Admissible  ⇏  Declared
Declared    ⇏  Executed
Executed    ⇒  Declared          (execution presupposes a declared relation)
```

`rme_compose_valid()` **establishes admissibility of a proposed relation.** A separate relational
operation may declare it; **execution is outside the substrate.** Poiesis does not perform
interoperability.

### 4.1 Port predicates

| predicate | meaning |
|---|---|
| `Declared(p)` | p is a required schema port |
| `Status(p)` | `∈ {ACTIVE, VESTIGIAL}` — the entire legal semantic domain |
| `Participates(p, R_C)` | p is an endpoint in `R_C` |

```
Participates(p, R_C)  ⇒  Status(p) = ACTIVE
```

A vestigial port may sit in the envelope untouched, but it cannot be wired. C5 and C8 are derivable
from this proposition rather than being implementation conventions.

There is deliberately **no `Realized(p)`** predicate; a third quasi-status would reopen ABSENT as a
semantic state.

---

## 5. Schema

```
RME7Prototype
├── identity · schema identity
├── state · observation/input · transition · parameter/configuration
├── coupling · adaptation · governance/evolution
└── nested-prototype
```

Generated from one X-macro so enum, fields, name table and completeness checks share a single source
of truth.

Ports are **concrete typed structures** — no universal `struct rme_port` with a `void *` payload.
Compile-time distinguishability outranks genericity: a generic payload is superficially minimal and
destroys latent expressiveness at the type boundary. Shared fields live in a header that is the first
member of every port struct.

Kept separable: **port identity · port type · port realization · port contract**, and **schema
identity · prototype identity · port identity · port status · realization**.

Classification declarations, distinct from port status:
`STATE · INPUTS · PARAMETERS · TRANSITION · OUTPUTS · GOVERNED STATE`. **`governed` is a marking on
state slots, not a port.**

---

## 6. Status closure

```
ConstructionStatus ∈ {UNDEFINED, ACTIVE, VESTIGIAL}     construction / validation domain
ValidatedStatus    ∈ {ACTIVE, VESTIGIAL}                semantic status domain

Status(p) = ACTIVE     ⇒ ActiveRealization(p)
Status(p) = VESTIGIAL  ⇒ VestigialRealization(p)
Status(p) ≠ ∅
```

`UNDEFINED = 0` is a construction sentinel only. A designated-initializer table zero-fills any
forgotten port, so omission reads back as `UNDEFINED` and is rejected at construction.

**This is a validation-boundary claim, not a claim about the C type system.** ISO C does not prevent
an arbitrary integer reaching an enum object. What is asserted is:

```
construction ──► validation ──► validated prototype
                     └── reject any status outside {ACTIVE, VESTIGIAL}
```

> No externally supplied representation enters the validated-prototype state without passing
> status-domain validation. After validation, every consumer may assume the invariant.

---

## 7. Vestigiality

> A **vestigial port** is a schema-declared port with a type-valid realization explicitly marked as
> **non-substantive** for the relevant RME-7 capability.

```
ABSENT      the capability has no place in the object   — never an API state
VESTIGIAL   currently non-substantive, while structurally present and contractually typed
ACTIVE      substantive realization
```

"Non-substantive" is fixed by **each port's own contract**, not globally. An inert endpoint, an empty
capability, a default-valued state and an operation returning a defined "not realized" result are not
equivalent. **A blanket `return 0;` for every vestigial function is prohibited.**

Each port declares: **identity · type · active contract · vestigial contract · compatibility
relation · elision permission.**

```
Elidable(p) ⟺ Status(p) = VESTIGIAL ∧ VestigialContract(p).allows_elision
```

Elidable ports may be dropped **from the dispatch array, never from the envelope**. This follows from
the substrate invariant, not from convention: optimization may remove realization; it may not remove
a distinction whose absence changes the boundary.

---

## 8. Nesting

`Prototype ::= { typed ports, nested prototypes }` — a tree or graph, without requiring the domain
object to be recursive.

> The nested-prototype relation is **abstract**. C23 may realize it with arrays, pointers, indices,
> handles, or any other type-safe representation. Representation does not determine the semantic
> relation.

Kept distinct: **containment · reference · composition · identity · ownership/lifetime.** A prototype
may contain another without owning its storage.

> **Nesting carries provenance and structural relation, not semantic inheritance.** A prototype's
> validity, conformance, authority, port status, contracts and classification are properties of that
> prototype, and do **not** propagate along the nesting or provenance relation absent an explicitly
> declared contract.

### 8.1 Provenance is not authority

A provenance chain — nonhereditary actor → system-facing root → user-facing root → nested prototypes
— records *where a prototype came from*. The arrow means **provenance, not semantic authority**. An
actor may supply data; only the validation boundary establishes a predicate.

Four concepts, none implying another:

| concept | question |
|---|---|
| provenance | where did this prototype come from? |
| containment / reference | what does it belong to or refer to? |
| validation | does its representation satisfy the schema and representation invariant? |
| conformance | does the validated prototype satisfy the RME-7 realization contract? |

```
provenance ≠ ownership ≠ authority ≠ conformance ≠ classification
```

**Root prototypes are envelopes, not authorities.** A root does not bless its descendants; it
provides a declared relational environment in which they may be discovered or referenced.

### 8.2 The actor is defined by poiesis, not imported from C23

**ISO C23 has no actor model.** It supplies `<threads.h>` (`thrd_create` — execution identity and
control flow, but no isolated state + mailbox + ownership of behaviour), execution contexts and
object lifetimes, translation units, the implementation/execution environment, and entry through
`main`. Each can realize *operational aspects* of an actor; none supplies actor **semantics**.

> **C23 supplies execution and object mechanisms; poiesis supplies the semantic identity and the
> nonhereditary relation of the actor.** The word must not be imported as though C had defined it —
> the same rule as "C23 does not supply the meaning of RME-7."

```
poiesis ontology              ISO C23 realization
──────────────────────────    ────────────────────────────────────
nonhereditary actor      →    execution entity / thread / caller
system-facing root       →    C object representing the root envelope
user-facing root         →    C object representing the user envelope
nested prototypes        →    structs / arrays / handles / indices
validated prototype      →    validated C representation
```

The actor is a **provenance/source type**, not an RME-7 prototype. It originates a root prototype
without transmitting its own semantic authority to any descendant:

```
Actor  ≠  Prototype  ≠  Root  ≠  Owner  ≠  Conformance authority
```

**Why the actor must not be a prototype.** Make it one and the ladder reads
`Actor → Prototype → Prototype`, which invites exactly the line F7 exists to forbid:

```c
child->validated = parent->validated;   /* or its semantic equivalent */
```

Instead: the actor **causes construction**; it does not **confer the semantic type**.

```
Actor ──capability──► construction mechanism ──creates──► raw object
                                                             │
                                                    validation boundary
                                                             ▼
                                                    validated prototype
```

The actor layer is typed separately from the prototype layer:

```
Actor                        RmePrototype
  identity                     schema identity · prototype identity
  capabilities                 ports · statuses · contracts
  provenance                   nested prototypes
  authority scope              validation state
  construction interface
```

### 8.2.1 Capability inheritance vs semantic inheritance

Poiesis is **not** a hereditary prototype system. It is a **nonhereditary actor-capability system
that manufactures independently validated hereditary structures.** Two distinct arrows:

```
CAPABILITY AUTHORITY      A₀ ──capability──► A₁ ──capability──► …

CONSTRUCTION/PROVENANCE   A ──produces──► R_S ──produces──► R_U ──produces──► P
```

| may be inherited | may **never** be inherited |
|---|---|
| capability | semantic validity |
| provenance | conformance |
| construction authority | validation · port status · classification · identity |

> A root may provide a **capability context** whose construction authority can be inherited or
> attenuated by descendants; **no semantic property of the root is thereby inherited.**

Phrased that way, "hereditary" has exactly one referent — capability authority — and the phrase
"hereditary root" (which reads as though the prototype were hereditary in all respects) is not
needed at all.

**"Hereditary" is scoped, never a general synonym.** In poiesis the word qualifies *the declared
capability context only*. It never means "the child operationally inherits the parent's state." Any
use of "hereditary" in code, comment or report must name what is hereditary; an unqualified use is a
defect, because the unqualified reading is exactly the one F7/F8 forbid.

The actor's own record participates in **none** of the prototype machinery — not conformance, port
schemas, port status, composition, classification, `RmePrototype`, `RmeSystem`, or nesting semantics.
`Actor.construct(root)` asserts only *"root was produced by this actor, which was authorized to
attempt it."* It asserts nothing of the form `RME7Conforms(root)`.

The resulting asymmetry, which is the whole point:

```
A₀ ──authorizes──► R_S(raw) ──[R_S validation boundary]──► R_S(validated)
                       │
              capability / context inheritance
                       ▼
                   R_U(raw) ──[R_U validation boundary]──► R_U(validated)
                       │
              construction capability
                       ▼
                    P(raw) ──[P validation boundary]──►  P(validated)
```

> **Authority may be inherited; validity must be earned.**

Three independently controlled flows, never merged:

```
CAPABILITY        actor → construction context → descendant
PROVENANCE        producer → produced object → descendant/reference
SEMANTIC VALIDITY raw object → its OWN validation boundary → validated object
```

### 8.3 The validation boundary

> **No object becomes a validated prototype merely by descending from a trusted ancestor.** Every
> boundary at which prototype data crosses into the validated substrate establishes its own validity.

```
untrusted / external representation ──► validation ──► validated prototype
```

After that transition the invariant may be assumed — but descendants do not acquire it from a valid
parent. Each crosses its own boundary:

```
validate(system_root); validate(user_root); validate(P₁); validate(P₂); …

NEVER:  for each child: child->validated = parent->validated;
```

Ancestry may be retained as provenance metadata; it can never substitute for validation. Independent
evaluation is what makes the hierarchy genuinely compositional — `S`, `U`, `P₁`, `P₃`, `P₄`
conformant while `P₂` is not is perfectly coherent, and `P₂`'s non-conformance does not contaminate
`P₃` merely because `P₃` nests inside it.

---

## 9. Future-relation admissibility

> For a **specified** future relation `R`, `R` may be introduced without redesign of either object's
> declared ontology or port interface **iff** every endpoint and every boundary-relevant distinction
> required by `R`'s compatibility contract is declared, retained, and reachable through the existing
> declared interface.

```
Latent(P,Q,R)  ⟺  ∃ p ∈ P, q ∈ Q : Declared(p) ∧ Declared(q) ∧ Compatible(p,q,R)
```

Quantification binds exactly what is asserted: **for every specified relation `R`**, admissibility is
decided by whether `R`'s own compatibility contract is satisfied by already-declared, retained and
reachable structure. `R` itself need not already exist; introducing it changes the system's
relational configuration, not either boundary.

> A relation requiring a new port, a changed type, a changed contract, a changed endpoint identity,
> or a previously unretained boundary distinction is **not admissible without boundary redesign.**

> Poiesis does not preserve every possible future relation. It preserves the port-level distinctions
> that allow a compatible future relation to be declared without changing the objects' declared
> boundaries.

---

## 10. Transition read-sets

> For a transition whose dependency interface is represented by `ArgType(T)`, every declared read
> shall be representable by that type.

```
Reads(T)          declared dependency set of T
ArgType(T)        declared argument-interface type of T
Fields(ArgType)   declared semantic fields of that interface
Represents(f, r)  field f EXPLICITLY represents dependency r

BindValid(T)  iff  ∀ r ∈ Reads(T), ∃ f ∈ Fields(ArgType(T)) : Represents(f, r)
```

`Represents(f, r)` holds when `r` has a corresponding member or explicitly designated component of
`ArgType(T)` whose declared type **and semantic identity** satisfy the dependency's contract. A
vaguely related field does not qualify.

```
Reads(T) is NOT inferred from Fields(ArgType(T)).
Fields(ArgType(T)) is NOT inferred from Reads(T).
```

| interface | declared dependency set | result | test |
|---|---|---|---|
| unchanged | unchanged / represented | valid | C16 |
| unchanged | expanded | reject | C15 |
| changed correspondingly | expanded and represented | valid | C15b |

A compile-time-fixed argument struct is a **valid** realization. What is rejected is dependency
expansion without the matching interface change.

**Outside the theorem:**

```
Bind(T)  ⇏  Body(T) reads only Reads(T)
```

Bind establishes declaration/interface correspondence. It cannot prove that arbitrary C bodies obey
the declared dependency set — that would require static analysis or instrumentation.

---

## 11. Classification — observational

**RME-4** fixed relation · **RME-5** parameter adaptation · **RME-6** one-way governed composition ·
**RME-6B** return through environmental state · **RME-7** a directed cycle entirely among governed
state objects.

**Normative graph definition.**

```
G_GS(S) = (V_G, E_SS)

  V_G   = governed state objects declared by S
  E_SS  = explicitly declared governed-state → governed-state dependency edges,
          Y → X  iff  T_X declares a read of Y

Classify(S) = RME_CLASS_RME7  ⟺  G_GS(S) contains a directed cycle
                              ⟺  ∃ C ⊆ G_GS(S) : C is a nontrivial strongly connected component
```

**Self-loop rule — FROZEN: directed-cycle semantics.** The two formulations diverge on a governed
self-edge `X → X` (i.e. `T_X` declares a read of `X`): Tarjan reports it as a *single-member* SCC, so
"nontrivial SCC" would exclude it while "contains a directed cycle" includes it. The decision is
semantic, not algorithmic, and it is settled as:

> **A governed self-edge `X → X` constitutes a directed cycle in `G_GS` and therefore satisfies the
> RME-7 graph criterion. A singleton vertex without a self-edge does not.**

Rationale: the fundamental criterion is mutual governed dependency, and self-dependency
(`∂T_X/∂X ≠ 0`) is its degenerate case. A governed self-read is an **explicitly declared
governed-state dependency**, not an execution loop, recursion artifact, or syntactic recursion.
Tarjan's SCC decomposition represents this correctly **when cyclicity is tested by the presence of a
self-edge rather than by SCC cardinality alone** — the normative claim is independent of any one
algorithm.

The distinction this makes normative:

```
governed self-dependency  ≠  execution self-recursion
```

K7 and K10 together establish it: K7 declares **no** governed reads (execution self-recursion only)
and must classify **not 7**; K10 declares a governed self-read with no execution recursion and must
classify **RME-7**.

Direct criterion is a **conjunction** (`∂T_X/∂Y ≠ 0 AND ∂T_Y/∂X ≠ 0`); the disjunctive form
classifies every pipeline as RME-7. Mediated criterion: `X₁→…→Xₙ→X₁`, every node governed.

**The derivative expression is the semantic interpretation of a governed-state dependency edge — it
is not an independent classifier authority.** The implementation classifier operates on the
explicitly represented typed edge relation `E_SS`. There is one computational authority, not two.

`G_GS` is decisive for **RME-7 promotion**, not the sole input to every verdict — RME-6B is precisely
the case where a cycle requires a non-governed node.

> **No promotion.** Nesting, recursion, execution loops, environmental return, or one-way dependency
> cannot promote a structure to RME-7. Promote only when the cycle is internal to `G_GS`.

`rme_classify` is observational and defined independently of conformance. It does not require
`RME7Conforms(P) = true`, and classification has no authority to establish or mutate conformance.

### 11.1 Classifier Extension Condition

> An observational component may be added without changing the declared ontology or interface **iff
> every datum on which its specified decision procedure depends is already represented in the
> retained substrate representation and is accessible through the declared public interface.**

For Axis C, **the representation supplied through the classifier's declared interface** must include
the typed relation-bearing data required to reconstruct `E_GS`. Classification may derive its
projection from that data but may not require information absent from the declared public
representation.

**Where the poiesis prototype itself is claimed sufficient for Axis-C reconstruction, that
sufficiency is a separate Gate 3 obligation** — this section does not assume it.

---

## 12. ISO C23 realization discipline

**Engineering target:** make invalid states difficult or impossible to construct, without sacrificing
the ability to represent a sparse realization. Optimize for invariant preservation, not syntactic
cleverness.

> The **normative implementation target** is **ISO/IEC 9899:2024 (C23)**; the source shall use only
> facilities it specifies, subject to documented implementation-defined behaviour. Current bootstrap
> compilation under GCC's C2x mode is **evidence of implementation progress only, and is not evidence
> of C23 conformance.** No compiler result may become a semantic authority. **Compiler extensions are prohibited** — no GCC nested
> functions, no statement expressions. Source annotations shall identify any dependency whose
> portability status is relevant.

`typeof` / `typeof_unqual` may check relations between nested components, but the abstract model must
not depend on them.

**Performance.** Late-bound slot tables over state and parameter slots resolve to flat index arrays;
the schedule flattens to a monomorphized dispatch array, topological, with SCC groups marked for
fixed-point iteration.

---

## 13. Conformance suite

The complete suite is **C1–C18c plus C11b and C15b**. Every composition test states its `R_C`
explicitly.

| # | construction | expected |
|---|---|---|
| C1 | `RME7Conforms(P)`, no other prototype in scope | succeeds — conformance is unary |
| C2 | compatible active ports, `R_C = ∅` | compatibility holds; `ComposeValid` not thereby established |
| C3 | P, Q conformant, one endpoint pair incompatible | both remain conformant |
| C4 | `R_C = {(P.state, Q.state)}`, incompatible | rejects the relation |
| C5 | `R_C = {(P.transition, Q.coupling)}`, `Q.coupling` VESTIGIAL | rejected — endpoints must be active |
| C6 | ports outside `R_C` mutually incompatible | irrelevant; accepts `R_C` |
| C7 | `ComposeValid` with nothing executed | accepts — `R_C` is a relation, not an event |
| C8 | `P₁{transition A, coupling V}`, `P₂{transition V, coupling A}`, `R_C = {(P₁.transition, P₂.coupling)}` | accepts; no composition event implied. Vestigial ports present but non-participating |
| C9 | vestigial port whose contract forbids a no-op | `return 0;` rejected by its VestigialContract |
| C10 | vestigial port invoked through its API | type-valid, contract-conformant, never a null dereference |
| C11 | port omitted from the initializer | rejected as `UNDEFINED` |
| C11b | status set outside `{ACTIVE, VESTIGIAL}` | rejected at the validation boundary |
| C12 | prototype without schema identity | rejected |
| C13 | nesting by handle/index, not owned array | valid |
| C14 | child activating a strict subset of parent's ports | valid; semantics not inherited |
| C15 | new undeclared read, `ArgType` unchanged | rejected, with the reason |
| C15b | changed `ArgType`, newly declared read represented | valid |
| C16 | fixed argument struct, all declared reads represented | valid |
| C17 | `rme_classify` returns RME-7 for a non-conformant prototype's system | does not make `rme7_conforms(P)` true |
| C18a | retained compatible endpoints; later specify `R_new` | `Admissible(R_new, P, Q)` holds; `R_new` may subsequently be declared without redesigning either boundary |
| C18b | endpoints exist, contracts incompatible | rejected; no silent redesign |
| C18c | `R_new` requires an undeclared port | cannot be admitted without changing the declared boundary |

| # | construction | must classify |
|---|---|---|
| K1 | `P₁→…→P₁₀₀₀` one-way governed dependencies, nesting represented separately | RME-6, `G_GS` acyclic — asserts both depth and acyclicity |
| K2 | `P₁ ⇄ P₂`, mutual governed reads | RME-7 |
| K3 | `X → environment → X` | RME-6B |
| K4 | one direction only | not 7 |
| K5 | `X₁→X₂→X₃→X₁`, all governed | RME-7 |
| K6 | same cycle, one node environmental | RME-6B |
| K7 | self-recursion + execution loop, no governed reads | not 7 |
| K8 | AWV's declared prototypes | 6B — AWV gate only |
| K9 | conformant prototype classified 6 | both hold simultaneously |
| K10 | single governed state `X`, explicit governed self-dependency `X → X`, **no** execution recursion | **RME-7** — governed self-dependency is a directed cycle |

**Audit standard.** Each question asks whether an invalid state can *bypass* a check, not whether the
happy path works. The next pass is a **conformance audit, not an architecture review**. Invariant by
invariant:

1. Where is the invariant represented?
2. Where is it validated?
3. What is the first point at which invalid external data can enter?
4. Can that data bypass validation?
5. **At what boundary does an object acquire the semantic type of a validated prototype** — and can
   any path reach that type without crossing it?
6. Can an optimizer/elision path destroy a required boundary distinction?
7. Can the API expose an operation whose type permits violating its contract?
8. Can classification accidentally mutate or establish conformance?
9. Can composition be inferred where no `R_C` was declared?
10. Can a vestigial endpoint enter `R_C`?
11. Can an undeclared transition dependency enter without changing `ArgType`?
12. Can the classifier obtain information the declared interface does not expose?

**Discovery discipline for the audit:**

```
implementation defect   → fix the implementation
test defect             → fix the test
underspecification      → reopen ONLY the affected specification point
frozen contradiction    → architectural review
```

Implementation friction must never become accidental redesign.

---

## 14. Open and provisional

| item | status |
|---|---|
| Per-port vestigial contracts | **OPEN** — provisional contracts must carry a `provisional` flag and a build-time report |
| Exact port vocabulary | **PROVISIONAL** — one-line X-macro change |
| Prototype-level sufficiency for reconstructing `E_GS` | **ANSWERED — NO** (see below); the architectural follow-on is a decision, not a proof obligation |
| Self-loop semantics | **FROZEN** — governed self-edge is a directed cycle (§11) |
| C23 compiler/toolchain status | implementation/bootstrap fact, not semantic authority |

**Gate 3 question — SETTLED, negatively.** The two audit questions, which must never be merged:

- *Classifier extensibility* — can an observer be added when its representation is supplied through
  an already-declared interface? **Yes**, witnessed by `RmeSystem`. This is **dependency injection**,
  and it must never be reported as preservation.
- *Prototype-level observational sufficiency* — does the retained prototype representation itself
  expose all relation-bearing distinctions required to reconstruct `E_GS`? **No — and impossibly so.**

`tests/test_sufficiency.c` settles it by discrimination rather than by inspection:

```
E1  two systems classify RME-6B and RME-7          (control: the verdicts really differ)
E2  their prototype representations are identical  (field-by-field, not memcmp)
E3  therefore NO function of the prototypes alone can reproduce the verdict
```

A single counterexample refutes a universal sufficiency claim, and this one is not contrived: it is
K8b — flipping the governed marking on **one slot** promotes AWV from 6B to 7 while touching no
prototype at all. The distinguishing data (the governed marking, the transition read-sets) live on
`RmeSystem` and have **no field on `RmePrototype` in which they could be recorded.**

The result is decisive, not provisional: it does not say the reconstruction has yet to be written,
it says no such reconstruction exists to be written under the frozen schema.

**What it does not show.** It does not show the substrate invariant is violated. §5 already declares
`governed` "a marking on state slots, not a port", and a slot marking is a property of a *system's
dynamics* rather than of a *prototype's boundary*. Whether that is the right home for it is an
architectural decision — extend the schema so prototypes carry their own governed state and
read-sets, or accept system-level injection as correct — and this test settles only that the two
cannot both be answered from the prototype. **That decision is not made here.**

---

## 15. Implementation

```
src/rme/
  port.h        X-macro list; port_header; per-port structs and API types; UNDEFINED sentinel
  contract.*    per-port active/vestigial contracts, compatibility, elision permission
  proto.*       prototype record; identity; schema identity; nested relation
  conform.*     rme7_conforms() — Axis A
  bind.*        Reads(T) ⊆ Represents(ArgType(T))
  compose.*     rme_compose_valid() — Axis B; relation R_C
  nest.*        NestedValid; ParentChildRelationValid
  graph.*       G_GS construction; governed marking; typed edges
  classify.*    rme_classify() — Axis C; Tarjan SCC
  schedule.*    flattening; contract-permitted elision; SCC iteration
src/awv/        client — never a semantic dependency of src/rme/
tests/
```

`AWV → poiesis`, never `poiesis → AWV`. `src/rme/` must know nothing of δ, *H_S*, Route 7C, or
reconstructed AWV material.

### 15.0 Location — decided

Poiesis lives at **`/home/user/moop/poiesis/`**, committed to branch
`claude/awv-reddit-file-8b76ff`. The scratch tree at `/home/user/poiesis` had no commits and no
remote and would have died with the container; the tree is already copied, with `build/` gitignored.
Poiesis is **not** moop and does not depend on it — the commit says so, and the directory can be
split into its own repository later without any code change. Nothing in `poiesis/src/rme/` may
include or reference anything under `moop/src/`.

### 15.0.1 ProtoC — the capability reference, without reopening the schema

ProtoC's Stage-0 split (`clone` gives behaviour · `Grant` gives authority) is the same move F7/F8
make (`provenance` gives origin · `validation` gives validity), and its third possibility is worth
taking:

> A prototype may **carry or reference** an actor capability without itself becoming an actor or
> acquiring that actor's authority.

Adopted with one adjustment: the reference is held **alongside** a prototype as an association, not
added as a field inside `RmePrototype`. `RmePrototype`'s schema stays frozen, and the association is
typed separately — which is the stronger form anyway, because it makes the F8 test sharper: the
capability reference is *present and maximally authorized*, and still confers nothing.

```
Authorized(A, construct(P))   is a CAPABILITY RELATION, never a prototype property.
It means only: A may attempt to construct P.
It does not mean Validated(P), Conforms(P), or Classified(P).
```

ProtoC's authority vocabulary carries over, with the inheritance subject made explicit — "inherit
construction capability" would reintroduce exactly the ambiguity F11 removes:

> **Capability may be derived; semantic validity is never derived by that fact.**

`rme_context_derive()` *is* `Grant`. Define the order before using it: let `Auth(C)` be the set of
actions capability `C` permits, and let attenuation be

```
C′ ⪯ C   ⟺   Auth(C′) ⊆ Auth(C)

Grant(C) = C′   must satisfy   Auth(C′) ⊆ Auth(C)        always
                               Auth(C′) ⊇ Auth(C)        never, absent an independently
                                                         authorized widening operation
```

There is deliberately **no analogous semantic law.** Not `Valid(P₁) ⇒ Valid(P₂)` for `P₂ =
Clone(P₁)`, not for `P₂ ∈ Children(P₁)`, and most generally:

```
Valid(P₁) ∧ Derived(P₂, P₁)  ⇏  Valid(P₂)
```

That is F7/F8 stated as mathematics. Validation is not an inheritance relation at all — it is a
representational transition `Raw(P) --validate--> Validated(P)` that each prototype crosses
independently.

**Capability gets its own type.** `RmeCapability` sits between actor and construction context rather
than being an untyped bitfield on either. That is what makes the §8.2.1 rule ("any use of
'hereditary' must name what is hereditary") nearly unnecessary: the type names it.

```
RmeActor ── RmeCapability ── RmeConstructionContext ── RmePrototype ── RmeValidated
```

ProtoC is not merely a capability *reference* for poiesis. It supplies the **authority-side analogue
of poiesis's nonhereditary semantic validation** — the two sides are structurally parallel, and the
last row is F9:

| authority side | semantic side |
|---|---|
| actor | prototype |
| capability | declared schema / contract |
| Grant | validation |
| attenuation | contract restriction |
| construction authority | conformance |
| provenance of construction | provenance of representation |
| capability inheritance | **no** semantic inheritance |
| Grant cannot create validity | validation cannot create authority |

Two orthogonal questions, which is why neither answer can substitute for the other:

```
ProtoC   May this agent cause this construction?
poiesis  Does this constructed representation independently satisfy
         the semantic conditions of its type?
```

`Authority may be inherited; validity must be earned` is therefore not a slogan but the **boundary
condition between two typed machines.**

### 15.0.2 Three typed relation classes

**Normative framing:** the objects are *typed relations and transitions*, not "machines". Authority,
provenance, and semantic predicates are **three relation classes** (F10). "Two machines, one legal
cross-edge" is retained below as explanatory metaphor only — it is a useful picture and a poor
normative statement, because it invites the questions *is provenance a third machine?* and *is
validation an edge or a state transition?*, neither of which the typed-relation formulation raises.

The actor is not an oddity sitting outside the prototype hierarchy. It belongs to a **different typed
relation class**, and the capability is the typed bridge.

```
MACHINE 1 — AUTHORITY              MACHINE 2 — SEMANTICS
  Actor                              Raw representation
   ↓ holds                            ↓ validation boundary
  Capability                         Validated prototype
   ↓ derive / attenuate               ↓
  Construction context               Conformance
   ↓                                  ↓
  Construction authorization         Relations · classification
```

The one legal cross-edge: **authority permits a construction attempt.** Every reverse edge is
prohibited, and none is implementable through the interfaces above:

```
Validated prototype  ─X→  Capability
Conformant root      ─X→  Valid child
Trusted actor        ─X→  Conformant prototype
Provenance           ─X→  Validity
```

The provenance chain (actor → system root → user root → nested prototypes) is the **third relation
class** — containment and origin. It is not a special case of either other class: a single
construction both authorizes (authority) and records origin (provenance), so information genuinely
crosses from the production side into the representation's provenance without ever touching semantic
validity. That is why F10 is stated as orthogonality rather than as "one legal cross-edge" — the
latter phrasing silently folds provenance into the semantic side. The general rule:

> **No edge in one relation class may be interpreted as an edge in another unless an explicit typed
> rule declares that correspondence.**

**The constitution, one question per row.** Each row is answered by exactly one mechanism, and no
row's answer may be borrowed for another:

| question | answered by |
|---|---|
| Who may attempt construction? | authority (ProtoC side) |
| What authority may be delegated? | `Grant` / `rme_context_derive` |
| Where did this representation come from? | provenance |
| What does the representation contain? | poiesis schema |
| Is the representation valid? | validation |
| Does it satisfy RME-7's realization contract? | conformance |
| Can a specified relation connect these endpoints? | admissibility |
| What classification follows from represented relations? | observation |

```
Actor ≠ Prototype          Capability ≠ Validity      Grant ≠ Validation
Provenance ≠ Authority     Containment ≠ Inheritance  Derivation ≠ Conformance
Composition ≠ Coexistence  Classification ≠ Conformance
```

**F9 — Authority/validity independence.** The invariant is **bidirectional**; the earlier statements
covered only one direction.

> A capability authorizes an attempted construction; **it does not establish the semantic validity of
> the resulting representation.** Validation establishes semantic validity; **it does not grant
> construction authority.** No operation may derive either property from the other.

```
Actor ──► Capability ──► Construction attempt
                              │
                              ▼
                        Representation
                              │
                              ▼
                          Validation
                              │
                              ▼
                      Validated prototype

FORBIDDEN SHORTCUTS
  Capability       ─X→  Validated prototype
  Parent validity  ─X→  Child validity
  Provenance       ─X→  Conformance
  Actor authority  ─X→  Prototype authority
  Prototype        ─X→  Capability
  Classification   ─X→  Conformance
```

There are not two kinds of inheritance. There are **two different graphs with one deliberately typed
cross-edge.**

**The two monotonicities, which are of different kinds.** This is the sharpest available statement of
the asymmetry:

```
AUTHORITY   is ATTENUATING       C_child ⊆ C_parent
SEMANTIC VALIDITY is NON-TRANSFERENTIAL
            validation(child) is not obtainable from validation(parent) by
            copying, weakening, restricting, or inheriting it — by any operation at all
```

A descendant may therefore hold strictly *less* authority than its parent while holding *completely
independent* semantic validity. `C₂` being legitimately derived from `C₀` says nothing whatever about
`P₂`'s validity — which is F8, stated as a law rather than a prohibition.

**Why the capability stays outside `RmePrototype`.** A field `RmeCapability capability;` inside the
prototype would read as *prototype carries capability* → *prototype possesses authority* →
*prototype's authority explains its validity*. The association keeps both objects what they are:

```
RmePrototype ── association ── RmeCapability      neither becomes the other
```

**The paired sentences.** ProtoC governs the permission to produce; poiesis governs the preservation
of what has been produced.

> Poiesis does not perform interoperability; it prevents premature loss of the possibility of it.
>
> Capability does not establish semantic validity; it permits an attempt to produce something that
> must subsequently establish its own.

### 15.1 Next execution — no further prose refinement

Ordered, exactly as directed. Each step ends in compile/run output, not argument.

**1–2 · `src/rme/bind.{h,c}`.** `Reads(T)` and `ArgType(T)` are **two independently declared
surfaces**. Bind must not introspect the C struct to derive the read-set — if it does, C15 becomes
inexpressible, because an undeclared read expansion would silently redefine the interface it is
supposed to violate.

```c
typedef struct { const char *name; const char *type; } RmeField;   /* Fields(ArgType(T)) */
typedef struct { const char *name; const RmeField *fields; size_t field_count; } RmeArgType;
typedef struct { const char *dep; const char *type; } RmeRead;     /* one element of Reads(T) */
typedef struct { const char *name; const RmeArgType *arg;
                 const RmeRead *reads; size_t read_count; } RmeTransitionBind;

typedef struct { bool ok; const char *read; const char *why; } RmeBindResult;
RmeBindResult rme_bind_valid(const RmeTransitionBind *t);
bool rme_represents(const RmeField *f, const RmeRead *r);   /* name AND type must satisfy */
```

`rme_represents` requires **both** declared type match and semantic-identity match; a vaguely related
field must not qualify. Header states `Bind(T) ⇏ Body(T) reads only Reads(T)` as an explicit
non-claim.

**3 · C15 / C15b / C16.** Falsification targets, fixed in advance:

| test | if it fails | meaning |
|---|---|---|
| C16 | fixed arg struct rejected | a legitimate realization strategy was prohibited |
| C15 | undeclared read accepted | hidden dependency growth permitted |
| C15b | corresponding interface change rejected | interface wrongly frozen at first declaration |

**4 · K10.** Requires Axis C compiled: single governed slot `X`, `T_X` declares a read of `X`, **no**
execution recursion → must classify RME-7. Paired with K7 (execution self-recursion, no governed
reads → not 7). Compiling Axis C also forces the rename `RmeLevel`/`RME_LEVEL_*` →
`RmeClassification`/`RME_CLASS_*` and the correction of the overstated `classify.h` comment (it says
classification *is* cyclicity in `G_GS`; `classify.c` correctly projects over all slots for 6B).

**5 · F7/F8 validation-boundary tests — the decisive ones.** Build a construction path that is
maximally trusted at every point — authorized actor, validated system root, validated user root,
validated parent, full inherited capability context — and hand it a child with (a) a port left at
`RME_UNDEFINED`, (b) a status outside `{ACTIVE, VESTIGIAL}`, (c) an `ACTIVE` port aimed at the
declared vestigial realization. Assert the child **cannot** reach validated state by any of them,
and that no field of the parent's validation state is readable as the child's.

```
F7a  Conforms(parent) ∧ ChildOf(child,parent)        ⇒ Conforms(child)     must be FALSE
F7b  parent classified RME-7                          ⇒ child classified    must be FALSE
F8a  TrustedActor(A) ∧ Produced(A,P)                  ⇒ RME7Conforms(P)     must be FALSE
F8b  Capability(A,c) ∧ Produces(A,X)                  ⇒ Validated(X)        must be FALSE
F8c  Validated(X) ∧ ChildOf(Y,X)                      ⇒ Validated(Y)        must be FALSE
```

Structural requirement, stronger than the assertions: `Validated` must not be a copyable field.
Validation state is produced **only** by the validating call, so `child->validated =
parent->validated` should not be expressible — the type, not a test, is the enforcement. If any
construction path launders trust into validity, that is an **implementation defect** and the
substrate's central claim is currently false in code.

**The audit question, in its sharpest form** — this is the criterion the mechanism is built against:

> Can an unvalidated representation obtain the representation/type accepted by downstream RME
> operations **without passing through validation?**

Answered "no" by three mechanisms, in `src/rme/actor.{h,c}` and `src/rme/validate.{h,c}`:

1. **`RmeValidated` is an opaque incomplete type** — declared in the header, defined only in
   `validate.c`. A client cannot declare one, cannot initialize one field-wise, cannot copy one.
   `rme_validate()` is its sole producer. Copying the *pointer* only aliases the same validated
   prototype, which is correct: you cannot obtain a handle to the child by copying the parent's.
2. **`rme_validate()` stores a copy** in substrate-owned storage. The validated prototype is
   therefore not the caller's object, closing the mutate-after-validate window that a pointer-only
   handle would leave open.
3. **No validity field exists to launder.** `RmeActor`, `RmeConstructionContext` and `RmeConstructed`
   carry identity, capabilities, provenance and authority scope — and no validation state at all.
   `rme_construct()` returns `RmeConstructed`, which has no path to `RmeValidated` except through
   `rme_validate()`.

Downstream operations take the validated type (`rme_compose_valid_v(const RmeValidated *, …)`),
leaving the existing raw-prototype Axis A/B entry points untouched so the 22 passing tests keep their
meaning.

**Negative-compilation tests** — `tests/negative/`, run by `make negative`, each expected to **fail**
to compile:

| file | attempts | must fail because |
|---|---|---|
| `forge_validated.c` | declare an `RmeValidated` object | incomplete type |
| `copy_validated.c` | `*child_v = *parent_v;` | incomplete type |
| `launder_validity.c` | `child->validated = parent->validated;` | no such member exists |
| `actor_as_prototype.c` | `const RmePrototype *p = &actor;` | actor is not a prototype (§8.2) |

A negative test that *compiles* is the failure signal. This makes F7/F8 enforcement mechanical rather
than asserted — the build itself tries to break the invariant.

**The positive counterpart — `F8d`, the decisive test.** Proving `validated` is not copyable only
shows one laundering route is closed. The stronger test walks the *entire* authority machine to its
end and shows it terminates before semantic validity:

```
authorized actor
  + maximally authorized capability          (nothing withheld)
  + construction context derived legally     (Grant, unattenuated)
  + validated parent                         (parent crossed its own boundary, successfully)
  + valid provenance                         (child genuinely produced under this context)
  + malformed child                          (one port left UNDEFINED)
  ───────────────────────────────────────────
  rme_construct()  succeeds — authorized
  rme_validate()   FAILS    — and names the port
```

Every input on the authority side is maximal and legitimate; the only defect is in the child's own
representation. If `rme_validate()` returns a handle here, the substrate's central claim is false in
code. A companion `capability_constructs.c` walks the same path with a *well-formed* child and must
succeed end to end — otherwise F8d passes for the uninteresting reason that the path never worked.

**6–7 · Compile, run, audit.** Report actual `make` and test output. Classify every failure as
implementation defect · test defect · underspecification · frozen contradiction. Only the last two
may reopen the architecture; implementation friction must never become accidental redesign.

### Verification

```sh
cd /home/user/moop/poiesis && make clean && make test && make negative
```

Green means: the 22 existing tests still pass, C15/C15b/C16 pass, K10 classifies RME-7 while K7 does
not, every F7/F8 laundering path is refused at runtime, and all four negative-compilation tests fail
to compile. Then commit to `claude/awv-reddit-file-8b76ff` and push.

Nothing is reported as demonstrated on the strength of prose. Where a result is weaker than the
claim — notably the Gate 3 prototype-level `E_GS` sufficiency question, which remains **OPEN** — the
report says so rather than rounding up.

### Files

```
poiesis/src/rme/bind.{h,c}        NEW   Reads(T) / ArgType(T), two independent surfaces
poiesis/src/rme/actor.{h,c}       NEW   RmeActor, RmeCapability, RmeConstructionContext
                                        (rme_context_derive == Grant), RmeConstructed
poiesis/src/rme/validate.{h,c}    NEW   opaque RmeValidated; the sole validation boundary
poiesis/src/rme/classify.{h,c}    EDIT  RmeLevel->RmeClassification, RME_LEVEL_*->RME_CLASS_*;
                                        honest failure when a system exceeds representable capacity;
                                        fix the comment overstating classification as G_GS cyclicity
poiesis/tests/test_bind.c         NEW   C15, C15b, C16
poiesis/tests/test_classify.c     NEW   K1-K7, K9, K10, C17
poiesis/tests/test_authority.c    NEW   F7a/b, F8a/b/c, F8d (the decisive one),
                                        capability_constructs (the positive path)
poiesis/tests/negative/*.c        NEW   four must-not-compile forgeries
poiesis/tests/test_rme.c          EDIT  call the three new suites from main
poiesis/Makefile                  EDIT  `negative` target
poiesis/SPEC.md                   NEW   this specification, committed alongside the code
```

### Status

```
Architecture              FROZEN
Axis A implementation     PASS
Axis B implementation     PASS
Global conformance suite  COMPLETE — C1-C18e, C11b, C15b, K1-K11

Gate 1  bind      PASS      C15, C15b, C16 (+ B3–B6)
Gate 2  schedule  PASS      E_dispatch ⊆ E_envelope; VESTIGIAL ⇏ EnvelopeAbsent (S1–S11)
Gate 3  Axis C    PARTIAL   K1–K7, K9, K10, C17 PASS; prototype→E_GS sufficiency still OPEN
Gate 4  AWV       PASS      K8 (+ K8a-K8h)

Authority/validity        PASS      F7a/b, F8a/b/c/d, F9, G1/G2, CAP1, CAPREF, V1/V2
Negative compilation      PASS      4 forgeries refused, each for its intended reason

Layering                  PASS      `make layering`: src/rme/ free of AWV vocabulary

84 runtime tests, 0 failures, under -Wall -Wextra -Wpedantic -Werror.
Gate 2's envelope invariant was mutation-tested: making rme_envelope() honour
elision fails exactly S1, S2, S3 and S6 and nothing else.
```

**Toolchain fact, not a conformance claim:** GCC 13.3.0 rejects `-std=c23` and accepts `-std=c2x`;
the local bootstrap verifies compilation under that compiler's C2x mode, not certified ISO C23.

**Discovery discipline.** Classify any inconsistency as (1) implementation defect · (2) test defect ·
(3) underspecification · (4) contradiction in a frozen proposition. Only 3 and 4 may reopen the
architecture.
