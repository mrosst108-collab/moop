# moop, merged

Moop × Unicore × Weft × Warp as one design. 10 November 2026.

Merged, moop is three mechanisms, one per axiom. A **term** is what
exists (homoiconicity). A **clause** `l <-> r` is how it changes
(reversibility). A **port** is where it meets anything else
(segregation). Every component of machine state is a term, every machine
step is a certified bijection on terms, and information enters or leaves
only at a declared crossing. Root pruning is the one act outside the
step, and the only loss.

The four sources are not four feature sets. Each answers a question the
other three leave open, so the merge is a selection, not a union:

| Source | The question it answers | Its answer |
|---|---|---|
| Weft | How is a mechanism selected? | Admit only what strengthens two mechanisms or eliminates two, and interferes with none |
| Warp | What are the mechanisms? | Term, clause, port |
| Unicore | Who answers for each guarantee? | Reversibility is the system's; dissipation is the user's to declare; the root is guarantor and terminus |
| Moop | What is it made of, and how does it read? | One CCNOT on two counter-rotating tapes; words, an article and a headless chain |

This is a design record. The repository implements the Moop realization
that `docs/model.md` and `docs/syntax.md` describe; nothing else here is
implemented or tested. Where the merge contradicts a decided item, §10
lists the conflict, and the implemented behavior stands until it is
ruled.

**Sources read.** Weft — Design Specification (rev 72), with its Moop
correspondence (rev 9), Derivations (rev 6) and register. Warp — Design
Proposal (9 November 2026), with its dossiers and register. Moop: this
repository. No Unicore record and no Moop design record from March to
September 2026 was available; their commitments are taken from how Weft
and Warp describe them. Weft's correspondence tab treats Unicore as
Moop's former name and Warp lists the two separately; here "Unicore"
means the two axes and `root_proto`, and "Moop" means the tape model and
this repository.

## 1. Method: one rule, two directions

Weft supplies the rule for what may enter. Moop supplies the test for
what must leave. Both count independent semantic rules, not names.

- **Admission** (Weft).
  `Admit(f) ⟺ [Strengthens(f, ≥2) ∨ Eliminates(f, ≥2)] ∧ Noninterfering(f)`.
  The two counts are never added. Wider coverage is a reason to look for
  a candidate, never a reason to admit one.
- **Deletion** (Moop). A construct is redundant iff a uniform contextual
  rule covers all its uses without creating silence (a mistake becoming
  an action) or ambiguity (one form, two meanings).
- **Order** (Weft). Unify from the lowest level upward, keep every
  distinction that carries its own guarantee, and promote an admitted
  composite to a building block of the next level. This is why §4 comes
  before §5.
- **Honesty** (all four). Provenance, rule, semantic status and test
  status are four separate claims. Nothing is presented as proven unless
  it was discharged, and an unimplemented behavior reports itself.

A derivation in `docs/derivation.md` and an admission dossier in Weft
are the same form: what forces the candidate, what it strengthens or
eliminates, every rule it adds, no special cases, non-interference
shown, and the tests that would discharge it. Two rules behind one name
remain two rules.

## 2. Three axioms, three mechanisms

The four sources hold the same three invariants and the same single
exception. Each named them at its own level.

| Axiom | Mechanism | Moop | Unicore | Weft | Warp |
|---|---|---|---|---|---|
| **Homoiconicity**, ubiquitous: every component of state has one representation | Term | Tape content: every cell is control and target | `homoiconicity_guarantor` | The canonical typed graph; `Code(T)` (D2) | Term |
| **Reversibility**, system-facing: every step is a bijection | Clause | CCNOT and rotation; the gate layer; `mirrors` | `reversibility_guarantor`; `<->` pairs | `Iso` and `PartialIso` | Clause |
| **Segregation**: information enters or leaves only at a declared boundary, and dissipation is user-facing | Port | Two memories, two logics; the one bridge shape; Message | The second axis; the G♯ receiver | Effects and handlers; the sector boundary; `Dissipate` | Port |
| The one exception | Root pruning | Causal pruning | — | — | Root pruning |

One mechanism carries one axiom, and removing a mechanism removes
exactly its axiom. That is the orthogonality argument at the base, and
it fixes the count.

- **Not seven.** Weft's seven kernel mechanisms are composites of these
  three (§7).
- **Not five.** Moop's five constituents are two realizations (Tape of
  term, CCNOT of clause), two crossings (Ancilla Discard outward,
  Message as request) and one composite (Commit Barrier).
- **Not one.** The clause is where homoiconicity and reversibility
  coincide, but a term that is not a clause still exists, and a clause
  across a boundary still needs the boundary. Calling the three
  "aspects of the clause" would hide three rules behind one name.

## 3. The kernel

Three mechanisms and seven rules, with one more pending. Warp's rule
letters are kept; (e) is vacated, not renumbered.

| Mechanism | Rules |
|---|---|
| **Term** | (a) A term is an atom, or a tagged node with labelled children. It is immutable. (b) A term's identity is the hash of its normalized form. Nominal-type, role-seal and resource identity are kept apart from it, and none confers authority |
| **Clause** | (c) A template is a term with holes. Each hole is used exactly once on each side. Read left to right a template builds; read right to left it matches. A template may apply another clause set. (d) A clause set selects by match and is exclusive on both sides, in either direction |
| **Port** | (f) `v -> p` crosses outward and `x <- p` crosses inward. The nearest enclosing handler receives the request and the continuation, both as terms. (g) A handler is a clause set over request terms. It stays installed, and it holds the continuation as a linear term |
| Order | (h) Evaluation is strict and left to right, so the order of crossings is fixed |
| Pending | (i) A term takes a role — code, type, request, continuation — only through that role's seal (Warp Dossier T) |

**Vocabulary.** A *sector* is a handler and the computation it encloses;
sectors nest and the *root handler* encloses them all. The *system
sector* holds certified clauses with an empty row, so it cannot cross
and cannot lose. *User sectors* are handler layers whose *rows* (sets of
request templates) declare each crossing. `hide` is the outward crossing
that the root answers by retaining the term, and ε counts what is
hidden, in bits, once per `hide` event. The *complement* is what
the root retains so a run can be reversed: hidden terms, and world
inputs and outputs. A *witness* is an ordinary handler layer that copies
what crosses its own boundary; it is never the complement.

**Machine.** `M = ⟨system store, dynamic store, focus, continuation,
complement⟩` is one term, and the language is one clause set,
`step : M <-> M`. The system store is fixed from `RUNTIME_START` until
termination: inspectable, never installed over. The dynamic store holds
the rebindable user bindings. The world lies outside `M`.

**Rule (e) is derived away.** Warp and Weft list certified primitives —
swap, XOR, modular and Toffoli updates — as the base case of
certification. Over a two-atom type each is an ordinary clause set,
certified by (c) and (d) alone:

```
swap:
    (a, b) <-> (b, a)

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

Word-level updates are structural recursions over bit tuples, which
Weft certifies as an `Iso` when the recursion is structural in both
directions. "Certified primitive" then names a realization obligation —
a native adder, or the tape's gate, must agree with the clause set it
stands for — and not a rule of the format. The realization's base case
is Moop's: CCNOT. Derived here; not shown. The sketch is illustrative
and its syntax is unruled.

**Certifier.** Three rules are counted apart from the kernel, as in
Warp: a type is a set of templates; rows give open records, open
variants and port sets; a clause set is a certified `Iso` when its
templates are exclusive and exhaustive on both sides, and a certified
`PartialIso` when exclusive on both sides over a declared domain and
image. Certification never changes what a program does, and types never
direct dispatch.

**Loss** has three stages, each measured separately:

| Stage | Unit | Jurisdiction | Meaning |
|---|---|---|---|
| Hidden | Bits | User-facing | Retained as complement, out of the program's reach. ε counts each `hide` event once |
| Pruned | Bits | System-facing | Removed from the reconstructible state. The only map that is not a bijection, and outside `step`. Never exceeds ε |
| Reclaimed or zeroed | Bytes | Realization | Two distinct measurement events: reclaiming storage does not show its contents were erased. Weft's M_heap is not absorbed; it measures this stage |

## 4. Foundational synergies

Three mechanisms give three pairs and one triple. These four are the
foundation: each is a product of mechanisms alone, with no composite in
its statement. Each already had a name in a source.

**F1. Term × Clause — causal closure** (Moop's name). A clause is a
term, so every program transformation has an inverse, and inversion is
itself a clause over clause terms: `clause(l, r) <-> clause(r, l)`, an
involution. A template builds forward and matches backward, so quoting
code and matching on code need no sublanguage. The state alone
determines future and past, and running backward recovers the program
that produced it. Neither half gives this alone: reversibility with an
external program keeps the system irreversible, and homoiconicity
without reversibility is self-modification with amnesia.
*Held by:* Moop at the bit, Weft at the format (D2), Warp at the term,
Unicore as two guarantors on one root.

**F2. Clause × Port — the bridge** (Moop's name: reversible effect
inside, irreversible observation outside). A function is a clause
completed to a bijection by a complement that leaves through a port.
Loss is therefore always a crossing, always declared, and always
counted. Inversion exchanges `->` and `<-`, so disposal and injection
are inverse crossings, and so are output and input.
*Held by:* Moop's MAYBE, and NAND as CCNOT plus Ancilla Discard;
Unicore's two axes; Weft's lift followed by `drop`; Warp's `l -> r`.

**F3. Port × Term — the message** (Moop's constituent). A request is a
term, so a handler is a clause set over requests, a row is a set of
request templates, and a request that no layer answers goes to the
enclosing handler, which is delegation. The continuation, the stores and
the complement are terms behind ports, so reflection is a crossing and
needs no interface of its own.
*Held by:* Moop's taught messages and lineage lookup; Unicore's
prototype chain; Weft's handler clauses as match arms; Warp's handler
stack.

**F4. Term × Clause × Port — the machine.** State is one term, `step`
is one certified clause set over it, and the root handler is where it
meets the world. The language's own definition is an object of the
language, so no interpreter state, checkpoint format or debugger
protocol exists outside it.
*Held by:* Moop's stack-wide tape; Unicore's root as guarantor; Weft's
grammar → format → realization; Warp's `step : M <-> M`.

## 5. Corollaries, in construction order

Every feature above the kernel is a composite. Level 2 unifies
mechanisms directly, level 3 unifies level-2 composites, and level 4 is
machine-wide. Each row names the foundational synergy it rests on, the
constructs it absorbs from the sources, and the distinction it keeps
because that distinction carries a guarantee.

**Level 2**

| Composite | Rests on | Absorbs | Distinction kept |
|---|---|---|---|
| Inversion and codec | F1 | Weft's parse/print round trip; Moop's encode/decode; serializer and deserializer | Total against partial |
| Function | F2 | Moop's AND, OR, NAND, NOR, XOR; Weft's ordinary code | `<->` against `->`: logical reversal against reversal by retention |
| Update | F2 | Assignment and initialization (Weft D1: swap plus declared disposal). Moop's deposit and exchange are the updates that dispose of nothing | Exchange against disposal |
| Freshness | F2 | Moop's MAYBE and birth seed; Weft's `Ask`, `Sample`, type salt and lineage seed; Warp's clean bits and seal salt | Agent-resolved against measure-resolved |
| Object | F3 | Slots, dispatch and delegation; Moop's actor and proto; Unicore's prototypes; Weft's meta records | Answering against forwarding |
| Stores and names | F3 | Modules; Moop's names and `is`; Weft's `Rebind` slot | Fixed against governed; code by hash against a name |
| Witness | F3 | Moop's trace 𝒯_Moop; audit records | Witness against complement |
| Role seal (pending) | F1, F2, F3 | Nominal types, opacity (Weft Q15), sealed wrappers | Interpretation against authority |
| Addressed memory (candidate) | F3 | Moop's RAM; Weft's raw-storage sector (Q17) | Port identity against access lease |

**Level 3**

| Composite | Built from | Absorbs | Distinction kept |
|---|---|---|---|
| Complement and ε | `hide` + the term the root retains | Moop's ε; Weft's ε_drop; any general undo log | Hidden, pruned, reclaimed or zeroed |
| Certifier | The code seal + templates as types + rows | Weft's inference, comptime evaluator and runtime checker (Q7); Unicore's static chain check | Certification against meaning |
| Commit barrier | Handler + speculation + inspection of the request | Moop's Commit Barrier and admission on every write; Unicore's `enforcement_binding`; Weft's admission policy | Compatibility against permission |
| Lineage | Construction clause + nested handlers | Moop's generation and inheritance; Unicore's `root_proto` → `Object` → user prototypes; Weft §11 | Generation, inheritance, reversibility, authority |
| Stage | Stores + certifier | Weft's comptime; Moop's `RUNTIME_START`; Unicore's bootstrap arc | This run against a prior run |
| Hoisting | Certifier + object | Unicore's hoisted chain walk; Weft Q3; Warp VP8 | Resolved statically against found at run time |

**Level 4**

| Composite | Built from | Absorbs | Distinction kept |
|---|---|---|---|
| Machine | `step` over `M` | Interpreter, debugger, checkpointing, serialization of running state | Format against realization |
| Governed self-modification | Dynamic store + certifier + barrier + complement | Moop's self-rewrite under the root; Weft's `Rebind` and checked patches | Inspect, transform, verify, patch and install stay separate |
| Tasks | Sectors + a scheduler as a handler | Threads and locks; Weft's spawn and send | Reproduced schedule against replayed execution |

Six unifications come from reading the sources against each other;
none is stated in any one of them.

1. **The object is the bridge at rest.** Moop's actor — a reversible
   body behind a table of irreversible messages — is Warp's handler
   layer plus state term: the bridge of F2 as a standing object rather
   than a single call. Moop's ladder (actor → system root → user roots
   → protos), Unicore's (`root_proto` → `Object` → user prototypes),
   Weft's (system root, user root) and Warp's (root handler → system
   sector → user sectors) are one ladder. The non-hereditary actor is
   its terminus: a layer that forwards nowhere.
2. **Freshness is the inward crossing.** A clean bit, a seal's salt, a
   nominal type's salt, a birth seed, a MAYBE draw and a world input
   are one act, and `hide` is its inverse. Moop seeds a child from its
   generator's dynamics; that is an inward crossing a certified handler
   answers, which is why the generator can step back to before the
   birth with nothing retained.
3. **Stage is store-sealing.** Weft's compile time, Moop's
   `RUNTIME_START`, Warp's two stores and Unicore's bootstrap arc are
   one distinction: before and after the system store is fixed. Compile
   time is a prior run whose output is the next system image. There is
   one evaluator, and a bootstrap is a chain of runs.
4. **Dispatch replaces meta records, and hoisting is one obligation.**
   Weft resolves operators by type, which the kernel rejects. A handler
   layer answers the operation instead, as a Moop proto answers a
   message, or the operations arrive as an explicit argument. Lowering a
   statically resolved handler to a direct call is then a single
   obligation with three names: Unicore's hoist, Weft's Q3, Warp's VP8.
5. **Hidden is declared inertness.** Moop detects causally inert cells
   by marks and zeroes them. Unicore and Warp require loss to be
   declared. `hide` declares what marks detect: a hidden term is inert
   to the forward run by definition. Declaration is the semantics, and
   detection is a tool for suggesting a `hide` or checking one. By
   Moop's own deletion test, marks cannot replace `hide`: a rule that
   prunes whatever is inert creates silence, because a cell that would
   have fired in a later epoch is lost without anyone discarding it —
   the caveat `docs/model.md` already records.
6. **`mirrors` is the clause.** Moop requires every `<->` form to be an
   involution so that "bijective" is a tested fact. Exclusivity on both
   sides gives that fact for any clause, and the involution moves from
   each form to `invert`. Deposit and exchange remain, as two clauses
   that happen to be their own inverses.

## 6. Three levels, one invariant

Moop meets the pairing at the bit, Weft at the format and Warp at the
term. Merged, these are not rival placements. They are Weft's sequence
grammar → format → realization, with the invariant held at every level.

| Level | What it is | From | The pairing there |
|---|---|---|---|
| Grammar | One chain grammar; words canonical and arrows as aliases; the article; the headless chain; one text per tree per projection | Moop, Weft | A text is a projection of a tree |
| Format | The term machine: `M`, `step`, code terms by hash | Warp, Weft | A clause over terms |
| Realization | CCNOT on a counter-rotating tape pair as the reference; native projections under Weft's profiles Hosted, Minimal and None | Moop, Weft | A gate over cells |

Adjacent levels are related by a codec, which is a `PartialIso`: print
and parse above, encode and decode below. The level structure therefore
costs no mechanism, and each round-trip law holds by construction where
the codec is certified.

**The wager moves.** Moop and Weft made opposite wagers in semantics:
whole-system guarantees at interpretive cost, against selected
guarantees inside bounded sectors. Merged, the guarantees are stated
once, at the format, and the cost is chosen per realization. A profile
restricts which programs can be realized and never changes what an
accepted program means. A realization may elide whatever no crossing can
observe, and must reproduce every crossing exactly. How much speed that
leaves is undemonstrated.

**Naturalism has an exact seat.** It governs the grammar level only.
Code identity excludes names and formatting, so the surface can change
on evidence about readers without touching the kernel. Moop's word and
arrow spellings and Weft's two projections (indentation, and explicit
terminators for screen readers) are the same device: a spelling is a
projection. Moop's derivations-away stand as grammar-level results:
`self` into the headless chain, `generate` into the article.

**Arrows.** All four agree on the principle Moop states: arrow shape is
information behavior. The two-way arrow stays inside; a one-way arrow
crosses. They disagree on what the one-way arrows are bound to. No
equivalence is inferred from a shared glyph; the last column rests on
semantics and is assumed until ruled (§10).

| Form | Moop, this repository | Moop, design records | Weft | Warp | Merged reading |
|---|---|---|---|---|---|
| `<->` `mirrors` | Bijection, as involutions | Bijection | One clause of an `iso` | Clause | Clause: nothing is left over |
| `->` `ask` | Message passing | Marks dissipation | Send to a task | Outward crossing | Outward crossing. A message, a task send and a `hide` are one act; the handler that answers decides what is lost |
| `<-` `inherits` | Lineage predicate | An ε = 0 operator | Field inheritance | Inward crossing | Inward crossing: the left receives from the right, and nothing is lost |
| `is` | Binds a name; teaches | — | — | — | Install in the dynamic store: an exchange through the barrier |
| `a` / `an` | Birth | — | Lineage constructor | `clone`, borrowed | Construction clause with a fresh seed |

`is` and `<-` keep separate jobs. `<-` fills a hole, which is linear and
local to a clause. `is` binds a name, which is rebindable and lives in
the dynamic store. The lineage predicate needs no form of its own: the
child retains its parent, so "who is my parent" is the construction
clause read backward.

## 7. The deletion ledger

What each source loses as an independent construct, and the uniform rule
that covers it. A row that depends on a ruling in §10 names it.

| Construct | Source | Covered by |
|---|---|---|
| Seven-mechanism kernel | Weft | Term (values, records, variants), clause (patterns), port (effects), rule (h) (strictness), certifier rules (rows), stage (comptime). A closure is a term; tail calls are a realization requirement |
| Reversibility as a bounded sector | Weft | Every step is a clause. Weft's sector is the system sector, and its ordinary code is the user sectors |
| `Dissipate`, ε_drop, the authorized receiver (Q13) | Weft | `hide` to the root, and ε. No handler can absorb a `hide`: linear use leaves it only retention or forwarding |
| Meta records | Weft | A handler layer, or an explicit operations argument |
| Reference counting on an acyclic heap | Weft | Linear holes: in-place reuse cannot be observed, and the kernel has no collection rule. Counting is a realization technique |
| Comptime as a second evaluator | Weft | Stage |
| `Rebind` slot; checked patch | Weft | Install as an exchange that keeps the previous version; a patch is a compare-exchange over definitions |
| Certified-primitive list | Weft, Warp | Clause sets over two atoms, plus a realization obligation (M3) |
| A design beside the others (R2); `clone` in the sketch (R4) | Warp | This merge (M2); the article (M5) |
| Irreversible logic layer | Moop | Function: a clause plus `hide` |
| Actor as a separate kind | Moop | An object whose layer forwards nowhere |
| Two memories | Moop | Two sides of a port: terms held linearly, and addressed memory behind a handler (candidate) |
| MAYBE as a logic operator | Moop | An inward crossing; logic stays two-valued |
| `<->` as involution only | Moop | Any certified clause; `invert` is the involution |
| Causal marks as a licence to prune | Moop | `hide` declares; marks detect (M6) |
| Lineage predicate | Moop | The construction clause read backward (M4) |
| `root_proto`, `Object`, the G♯ receiver | Unicore | The root handler, the user root, the root's `hide` |

The merge also answers or relocates open questions in this repository's
own notes:

| Open in `docs/model.md` or `docs/syntax.md` | Standing here |
|---|---|
| General invertible functions under `<->` | Answered in form by the clause: two templates, certified by exclusivity. Exact arithmetic needs the modular updates; floating-point rounding is not certified |
| Reflection: reading a taught chain back | Answered by F1: a taught chain is a code term, and matching it is a template read backward |
| MAYBE's final semantics | An inward crossing. Agent-resolved and measure-resolved are two handlers |
| How RAM and the surface exchange values with the system layer | Through ports; addressed memory as a handler is a candidate |
| How programs are encoded onto the loops | Relocated: a codec between format and realization. Still open |
| Whether pruned cells are reclaimed or zeroed | Two measurement events of the third stage; neither implies the other |
| Whether inheritance interacts with `<->` | Birth is a construction clause; inheritance is what the child retains |
| Logic words: keywords or messages | Messages. A function is not kernel |
| One gate or a ring of gates | A realization question; the format does not see it |

## 8. Orthogonality

Unification stops where a distinction carries its own guarantee.

| Mechanism | Its guarantee | How the other two preserve it |
|---|---|---|
| Term | Identity is content; no term changes | A clause builds new terms and never edits one. A port moves terms and never aliases one |
| Clause | The two readings are mutually inverse on the declared domain, and every hole is used once | A term has no hidden state, so matching is deterministic. A crossing has an inverse crossing or is a declared commit point |
| Port | Every crossing meets exactly one enclosing handler, and authority never exceeds the forwarder's | Holding a code term confers no port. A clause reaches nothing past its sector except through a crossing |

**Kept apart, on purpose.** Logical reversal and reversal by retention.
Hidden, pruned, and reclaimed or zeroed. Complement and witness. `Iso`
and `PartialIso`. Interpretation and authority: a seal, a clause and a
port identifier each confer none. Inspect, execute and install. System
store and dynamic store. Certification and meaning. Generation,
inheritance, reversibility and authority. Answering and forwarding. A
hole and a name. Format and realization.

**Rejected**, each because it would cost an admitted mechanism its
guarantee: implicit copy or drop in the core; shared mutable references;
a general undo log; installing over a system binding; laziness;
overlapping clauses resolved by order; multi-shot continuations;
raw-syntax macros; type-directed dispatch; subtyping; ambient ports;
re-parenting; pruning what was never hidden (M6). At the grammar level,
Moop's rejections stand: no receiver keyword and no creation word.

## 9. Guarantees and costs

Seven properties state what the kernel is meant to guarantee. Each
follows from the definitions above if `step` passes its own certifier.
None is proven. The last column records what `make test` checks today,
which is the realization level only.

| Property | Statement | Unicore's invariant | Tested in this repository |
|---|---|---|---|
| G1 Reversibility | `step` then its inverse is the identity on reachable, unpruned states. No global history is kept | `reversibility_guarantor` | Core round trip over a full cycle; every gate self-inverse; `<->` twice is the identity |
| G2 Totality of ε | Pruning is the only map that is not injective, and pruned bits never exceed ε | — | Pruned bits are counted. ε does not exist |
| G3 Closure | Every component of machine state is a term the root can match on | `homoiconicity_guarantor` | Both loops are written by execution. Names, taught chains and parent links sit outside any reversible state |
| G4 Attenuation | A sector's crossings are a subset of what its enclosing handler forwards; the root is the terminus | `attenuation_terminus` | Actor lookup is local; delegation never crosses into the system root |
| G5 Enforcement | A crossing the barrier rejects does not take effect: the speculative run is run back | `enforcement_binding` | Not implemented |
| G6 Neutrality | Erasing every certificate changes no run; removing a witness changes no visible result | — | Not implemented |
| G7 Fixed system store | No candidate installed during a run replaces a system binding | — | In part: `maybe` and `value` refuse redefinition |

Weft's twelve correspondence rows for Moop's invariants stand as Warp
assesses them: eight restored at machine scope, two more restored where
a witness layer sits (C05 provenance, C10 crossings), and two translated
(C07, admission at every crossing; C11, governed self-modification,
with scope equivalence unestablished).

**Costs.** Space: the complement grows with every hidden bit and every
world crossing until the root prunes it. Linear use: the core has no
implicit copy or drop, and each convenience the surface restores is a
counted crossing. Interpretation: terms are the ground truth and
compiled code is a projection of them. World effects: running back
restores the system, not the world, so an output that cannot be
compensated is a commit point. Concurrency: reversing concurrent sectors
needs their crossings ordered by cause, and atomicity is not derived.

## 10. For ruling

Each decision is the author's to make. Each is listed with what this
document assumes until ruled. M4, M6 and M7 contradict items that
`CLAUDE.md` records as decided; for those the implementation is
unchanged.

| Ref | Question | Assumed here |
|---|---|---|
| M1 | The name of the merged design | "moop": the repository and the reference realization already carry it. Warp's R1 lapses |
| M2 | Standing of Weft and Warp | They stop being designs beside Moop (Warp R2) and become its method and its kernel. Their documents remain the detailed records |
| M3 | Rule (e) | Vacated. The kernel is seven rules with one pending, which changes Warp's ruled count of eight |
| M4 | The one-way arrows | `->` is the outward crossing and `<-` the inward crossing. The lineage predicate dissolves into the construction clause read backward. Contradicts "`<-` is a lineage predicate" |
| M5 | The birth word | The article, as this repository decided. Warp's sketch keeps `clone` (R4), which Moop declined along with every other creation word |
| M6 | Pruning | Only the root prunes, and only what was hidden. Causal inertness is the policy's test, not a licence. Contradicts auto-pruning of unmarked cells in `moop_core_run` |
| M7 | Closure over the user medium | Names, taught chains and parent links are components of `M`. Rebinding and re-teaching are exchanges that keep the previous version, and discarding it is a counted `hide`. The two media stay as a realization choice. Contradicts "re-teaching replaces the chain" |
| M8 | Stage | Compile time is the run before `RUNTIME_START`, with one evaluator |
| M9 | Warp's remaining rulings | R6 to R10 carry over unchanged. Standing in the wider corpus is unchanged: a realization candidate, with RME-7 a model written in it and no mechanism an office |

## 11. Realization path in this repository

The repository already realizes the three mechanisms at the lowest
level: the gate layer and the core's step and step-back (clause),
symmetric wiring with no read-only program tape (term), and the bridge
shape in MAYBE, actors and delegation (port). It realizes lineage, and
the grammar's chain, words, article and headless chain. What is missing
is the format level. The order below builds each foundational synergy
before anything that depends on it. It is a proposed order, not a
commitment, and every step keeps `make test` passing.

1. **F1.** Make a chain a value the language can hold: quote one, and
   read a taught chain back. Let `mirrors` take two templates, with
   overlapping clause sets refused at definition and `invert` as an
   ordinary clause. This closes "number↔number bijections" and
   "reflection", which the REPL reports honestly as absent today.
2. **F2.** Add `hide` as the single outward loss, with an ε counter.
   Re-express the irreversible logic layer as clause plus `hide`, and
   MAYBE as an inward crossing. Results must not change; ε must count
   each `hide` once.
3. **F3.** Let a request carry a payload term, so messages take
   arguments. Make a handler a clause set over requests, and forward
   what no layer answers.
4. **F4.** Hold the session as one machine term — stores, focus,
   continuation, complement — and give the language `step` and its
   inverse. Apply M6 and M7 here, if ruled.
5. **Corollaries**, in level order: complement and barrier, then the
   certifier beyond exclusivity, stage, witness and hoisting, then
   addressed memory if admitted.

## 12. Status

Nothing beyond the Moop realization is implemented or tested.

**Established in the sources.** Weft: the selection rule and nine
constraints, the dossier, recursive unification, `Iso` and `PartialIso`
with their clause conditions, code identity, realization profiles.
Warp: the three mechanisms, the machine term, the fixed system store,
the separation of complement and witness, the three stages of loss.
Unicore: the two axes, and the root as guarantor and terminus. Moop:
the tape model, the bridge shape, generation against inheritance, the
surface, the deletion test.

**Pending admission, unchanged.** Role seals (Warp Dossier T) and
addressed memory as a handler (Dossier P). Contracts remain a Weft
candidate; they are one way to declare a `PartialIso` domain.

**Derived here.** These follow from reading the sources together and
are not shown in any realization:

- One mechanism carries one axiom, which fixes the count at three.
- The four foundational synergies are the three pairs and the triple.
- Certified primitives are clause sets over two atoms, so rule (e) is a
  realization obligation.
- The object is the bridge at rest, and the four ladders are one.
- Freshness is the inward crossing.
- Stage is store-sealing, and a bootstrap is a chain of runs.
- Dispatch replaces meta records, and hoisting is one obligation.
- Hidden is declared inertness.
- A level is a codec of the level above, and a spelling is a
  projection.
- The lineage predicate is the construction clause read backward.

**Open.** Warp's open items stand, chiefly: whether `step` can be
written as a certified clause set; inference for templates as types
under linear use; static exclusivity when templates apply other clauses;
iteration without history; garbage-minimal complements; the pruning
policy and where its authority sits; the causal order of crossings
between concurrent sectors; nearest enclosure against lexical
capability. The merge adds four:

- How `M` is encoded on the tape pair, and whether one gate suffices.
- Whether a handler layer or an operations argument keeps the coherence
  that Weft's meta records give by declaration.
- Whether word-level updates certify as structural recursions without
  a primitive, as §3 claims.
- Which grammar the merged arrows take once M4 is ruled, and how the
  word forms read for an inward crossing.

Prior art is recorded in Warp's §12 and Weft's kernel-provenance table.
Moop's own ancestors are in `docs/derivation.md`.
