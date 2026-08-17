# Crossing: autopoietic interoperability

moop is developed by more than one organizationally closed system:
this repository (and whatever instance is working in it) and sibling
projects with shared lineage (unicore's `mccarthy.c`, whose prune is
ported from moop) each produce and maintain their own state by their
own rules. Such systems cannot interoperate by sharing state — a claim
like `src/tapeloop.c:34` is true only inside the organization that
minted it, and dissolves on arrival in a tree with no `src/`. This
document defines the one sanctioned port through which claims cross,
and the ledger that records every crossing. Treat it as methodology,
in force; the ledger at the bottom is the live record.

## The crossing shape, derived

moop already has a law for boundaries: **bridging has exactly one
sanctioned shape** — reversible effect inside, irreversible observation
outside. Generation may cross the system/user boundary in that one
shape; delegation never does. The crossing port is that same law lifted
one level:

> **Re-derivation may cross a boundary; authority never does.**
> What crosses must be either (a) anchored in a shared environment both
> sides can independently verify — a fetchable commit plus content
> hashes — or (b) re-derived inside the receiver from its own ground.
> Anything else is testimony: recorded, consulted, never binding.

The correspondence is exact. The *verifiable anchor* (commit SHA +
content hash) plays the role of the reversible inside: any party can
re-run the check and get the same answer, so verification is
replayable, like MAYBE. The *local re-derivation* plays the role of the
irreversible observation outside: each receiver interprets the claim in
its own terms, and its interpretation belongs to it alone. And the
non-hereditary rule holds here as it does for actors and ancestors
(see `derivation.md` §2): no claim is accepted *because* the sender
verified it — a crossing that cannot be re-derived locally has not
crossed, it has only been heard.

## The typed port: crossing entries

A crossing is admitted to the ledger as an entry with these fields —
this format is the port's type, and untyped arrivals (pasted text,
relayed line numbers, "verified here" assertions) are recorded with
status `testimony` until they are grounded:

- **from → to** — the organizations, named as `repo @ branch`.
- **ground** — commit SHA(s) and content hashes for every artifact the
  claims cite. Ground the receiver cannot resolve is *stated* ground,
  not actual ground.
- **claims** — what crossed, in the sender's terms, unedited.
- **status** — one of:
  `testimony` (heard, not grounded), `grounded` (anchors resolve and
  hashes match), `re-derived` (receiver reproduced the finding from its
  own tree), `refuted` (receiver's re-derivation contradicts the
  claim), `parked` (correctly awaiting something that doesn't exist
  yet).
- **derivation** — how the receiver re-derived or refuted it, locally.
- **consequences** — commits, doc rulings, or nothing.

The ledger is **append-only**: a refuted entry is answered by a later
correcting entry, never edited. The path — including wrong turns — is
the record.

## RME-7 as the port's type system

Each axis owns one non-overlapping job at the boundary:

| axis | job at the crossing |
|------|---------------------|
| **κ** | The ground-resolution check: do the cited anchors resolve here, do the hashes match? κ > 0 (stated ground ≠ actual ground) blocks binding and sequences everything behind resolution. |
| **Σ** | The entry format itself — the typed port. Loop lengths taught us configuration can smuggle semantics; testimony can too. Typing the port is this document. |
| **G̃♯** | The admissibility predicate for *binding*: ground resolves ∧ locally re-derived. An entry failing either conjunct stays `testimony` and cannot justify a commit. |
| **J♯** | Provenance reified: which claims came from where, and where each was verified, is explicit state in the ledger rather than implicit in a conversation. |
| **G♯** | The ε-discipline: nothing derived from an unbound crossing may be committed, taught, or written to memory. The ledger entry precedes any commit that uses cross-boundary findings — catching divergence pre-commit is the cheap moment. |
| **F** | Corrections flow forward: a refutation appends, cites the entry it corrects, and propagates to any consequence that cited the refuted claim. |
| **γ** | The record is never erased. This is deliberately *unlike* the core's marks (implicit γ, erased each prune): the substrate may forget; the boundary may not, because the boundary is exactly where each side's derivable-past guarantee ends. Inside one repo, provenance needs no log (`derivation.md` §4 — run backward). Across repos there is no shared backward to run; the ledger is the γ that closure cannot provide. |

That last row is the deletion-test answer for this document: within
one organization, causal closure makes provenance logs redundant and
they are rightly absent. *Across* organizations no uniform rule covers
provenance — no shared substrate, no shared inverse — so the ledger is
not dissolved by anything already present. It earns its name exactly
at the boundary, and nowhere else: no language construct, no core
mechanism, zero code.

## Ledger

### 1 — unicore comparison arrives; anchors fail abroad

- **from → to**: `mrosst108/tri-modal-release @ tri-modal-release` (unicore, `impl/mccarthy.c`) → `mrosst108-collab/moop @ claude/moop-c6we7t`, relayed by hand.
- **ground (sender-side, unverifiable here)**: sender cites its own commit `6f85579` ("testimony, never law") and paths `impl/mccarthy.c:1498-1598`; this tree cannot resolve them. Stated ground only.
- **claims**: shared spine (two counter-rotating carriers, one CCNOT, causal marks, prune-as-dissipation); four divergences (closed vs. driven; no κ because carriers aren't mirrors; γ implicit vs. explicit; irreversibility temporal vs. architectural); two code findings on the tapeloop — step_back across a prune boundary is silently wrong, and non-coprime loop lengths silently select partitioned-alignment semantics.
- **status**: claims about unicore — `testimony`. Claims about the tapeloop — `re-derived` (see derivation).
- **derivation**: both code findings reproduced by direct reading of this tree at `a83d087c42338052851e038bb9ace3f3df68dbf3`: `ticks` is a `size_t` decremented with no guard; `moop_core_init` asserted only `len >= 2` while `docs/model.md` and `src/eval.c` (8/13, "covers every alignment") already relied on coprimality.
- **consequences**: entry 2.
- **κ note, both directions**: the sender's `file:line` anchors failed in this tree *and* this tree's anchors (`src/tapeloop.c:34`, `docs/model.md:30`, ...) failed in the sender's — the founding demonstration that line numbers are organizationally relative and only commit + hash crosses.

### 2 — findings bound and landed

- **from → to**: entry 1's re-derived findings → this tree's artifacts.
- **ground**: pre `a83d087c42338052851e038bb9ace3f3df68dbf3`, post `8ecea4c41c1f4b29bbfc55d5927f1ad07af5f45c` (diff: 4 files, +42/−15). Post-state hashes: `src/tapeloop.c` `457947c07f16d859acb55a39c9ed11a48c274be6813295c279bec709fcee3e45`, `src/tapeloop.h` `344a0ea9b9e9d7f1d06a3c3f07f96106489efab8b192a61ab5450e6b0e20ab13`, `docs/model.md` `a46c8105936165f73b6605994363b83be865f9e0ed217e6a81a06ce669d630ff`, `CLAUDE.md` `4c8f25908d20eeb4f98793bc7dbd23d2fcc7b5f24facc9f2c61527f3919f5324`.
- **claims → rulings**: coprimality asserted at init (loop lengths select semantics, not capacity; non-coprime is a different machine, refused); `step_back` asserts `ticks > 0` (the between-prunes discipline, crash-loud). Both encode rules the docs already stated — no new concepts.
- **status**: `re-derived`, landed.
- **parked, correctly**: reified γ for the substrate ("what did the last prune forget") stays open until reflection forces it; adding a log now fails the deletion test.

### 3 — the four roles of "space" arrive unanchored; the local half re-derives

- **from → to**: unanchored relay (pasted prose; no repository, branch,
  commit, or path named) → `mrosst108-collab/moop @
  claude/space-roles-rme7-u2-m112-dygpjx`.
- **ground**: none. The text cites no artifact, and its opening ("Yes.")
  and its references to "the earlier promotion errors" (∇R=0 ⇏ F=0;
  homogeneity ⇏ κ≡1) belong to a conversation this tree does not hold.
  Zero stated ground, so κ > 0 by inspection and nothing here can bind
  on the sender's authority.
- **claims**: (a) four roles are conflated by the word *space* — ambient
  space (where a thing could exist), solution space (which
  configurations satisfy the relations), dynamical system (how state
  changes), coordinate system (how the thing is represented); (b) the
  chain of non-implications, ambient ⇏ solution ⇏ dynamical law ⇏
  physical instantiation, and separately coordinate representation ⇏
  what is represented; (c) a custody ruling for ℳ₁₁₂ — it coordinates
  the state, it is not itself the ledger, and membership in it is not a
  physical-instantiation claim; (d) U₂ is a dynamical specification, not
  a solution manifold, and RME-7 is the compositional level above it;
  (e) glosses for each RME-7 object (J♯ conservative circulation, G♯
  dissipative descent, G̃♯ teleological confinement, Σ stochastic
  forcing, F autopoietic self-production, κ generator gate, γ
  curvature/observable defined as [G♯, G̃♯]).
- **status**: (a)–(d) about RME-7/U₂/ℳ₁₁₂ — `testimony`. (e) —
  `testimony`, and **inadmissible for populating
  `prompts/asdg-rme7.md` §3**: that file's own gate says the
  unpopulated sections are "not to be filled in from memory by a
  reader", and a gloss read off notation is exactly the reconstruction
  it prohibits ("a plausible reconstruction is worse than none, because
  it looks right"). The object *names* it uses need no import — they are
  already carried at `bookended-thinking/ontology/rme7_objects.yaml`
  with status `retrieved`; the semantics are what stay unpopulated, and
  they stay unpopulated. (a)–(b) applied to this tree's core —
  `re-derived`. The disclosure hazard below — `re-derived`.
- **derivation**: the four roles land on the core without importing
  anything: **configuration space** (every bit assignment times the head
  alignment), **orbit** (what a birth state actually reaches — the
  wiring is a bijection, so orbits are cycles), **wiring**
  (`moop_core_step`, the law), **chart** (`src/encode.{h,c}`: bit i of a
  value is cell i of loop A). Measured on an 8/13 body at
  `dec435d251df0f949919f0dd39db9919a08298ef`: the configuration space is
  2^21 × 104 = 218,103,808; the orbit from an all-ones birth is
  8,020,272 of them (3.7%); the orbit from an all-zero birth is 104,
  bare rotation. Same geometry, five orders of magnitude apart —
  ambient ⇏ solution, which is entry 2's coprimality ruling ("lengths
  select semantics, not capacity") seen from the other side. Chart ⇏
  state reproduces just as concretely: `value` reads 8 of 21 cells and
  none of loop B, so two bodies deposited with 37 and differing in one
  loop-B cell diverge under `maybe` inside one alignment cycle while one
  of them never moves at all. The senses that do *not* re-derive are
  named too: this tree has no ontology layer, so "⇏ physical
  instantiation" has no local referent and is recorded, not adopted.
- **disclosure hazard (verified here)**: the arriving text states γ =
  [G♯, G̃♯] in the open. `bookended-thinking/engine/ontology.py` lists
  `definition`, `commutator_of`, and `computed_from` in
  `WITHHELD_FIELDS` precisely so a classifier is never handed the
  commutator ("giving it the commutator would hand it most of the void
  conjecture"), and `bookended-thinking/tests/test_core.py` asserts the
  rendered prompt never contains it. So this text must not be pasted
  into a classifier prompt, drill input, or sealed commitment: doing so
  would make the cell-level γ cross-check self-confirming. Recorded as a
  usage ruling; no code, because the render path already guards the
  files it controls and a paste is outside its custody.
- **consequences**: commit `c5ffde916b52403104008c7a1833a7c85b4b2516`
  (3 files, +80/−1) — `docs/model.md` gains "The chart is not the
  state", `tests/test_core.c` gains `test_chart_is_not_the_state`,
  `CLAUDE.md` carries the ruling that `x -> value` answers what loop A
  reads and never what x *is*. Post-state hashes: `docs/model.md`
  `b484ebb7982c6a06e589c5afb67ed476c3fb547d9dc25cf86934ab376258910d`,
  `tests/test_core.c`
  `a197b5c377833e1c5ab5c2ca197d2dbbd348e6eb4f3d113c957db3c698302c33`,
  `CLAUDE.md`
  `c152eba01f65e35edb8ada35ba62525de50a4f13c8ee2551805afa2f7afa2cd4`.
  Deliberately unchanged: `prompts/asdg-rme7.md` (gate above) and
  everything under `bookended-thinking/` (usage ruling, not a defect).
  Ledger order note: the re-derivation commit precedes this entry
  because the entry cites its hashes; nothing derived from the unbound
  half was committed at all, which is what the G♯ row actually asks.
- **why this is not a new construct**: the four roles name distinctions
  the core already enforces — coprimality (configuration ⇏ orbit) and
  the encode/decode discipline (chart ⇏ state). The deletion test
  dissolves any *mechanism* here; what survives is a docs ruling and a
  test, which is the smallest thing that can fail loudly if the
  distinction is ever collapsed.

### 4 — the sender qualifies entry 3: five roles, orthogonal, not a chain

- **from → to**: same unanchored relay, follow-up → `mrosst108-collab/moop @
  claude/space-roles-rme7-u2-m112-dygpjx`. **Corrects entry 3.**
- **ground**: still none. No repository, commit, path, or hash. The
  qualification is authored by the holder of the instrument rather than
  read off a source, which changes who is speaking, not whether it is
  anchored.
- **claims** (sender's terms, unedited): RME-7 is not merely a typing
  discipline for preventing promotions — it is a *maximally expressive
  minimal format whose compression is achieved by preserving
  orthogonality between distinct roles*. Five roles, each classifying a
  different question: **ambient space** — where the state/configuration
  is situated; **coordinate system** — how that state is represented;
  **dynamic system** — how states evolve; **solution space** — which
  states/trajectories satisfy the governing relations; **ontology** —
  what standing, if any, is assigned to the represented structure. The
  offered formulation, verbatim:

  > RME-7 is a maximally expressive minimal format for classifying
  > systems while maintaining orthogonality under compression. Its
  > expressiveness permits the distinctions among ambient space,
  > coordinate system, dynamics, solution space, and ontology to be
  > represented without collapsing them; it does not authorize inference
  > from one role to another.

  With two riders: *maximally expressive* means the format can classify
  the relevant distinctions and interactions, *minimal* means it
  introduces no separate primitive where an existing typed relation
  suffices; and **expressive completeness does not imply constructive
  sufficiency** — classifying the roles as orthogonal tells you nothing
  about how to construct a particular solution, choose coordinates, or
  establish an ontological correspondence.
- **status**: `testimony`. Nothing here is anchored, and nothing here is
  re-derivable in this tree: the claim is about the format's own
  economy, and this repository holds no ASDG source against which
  "maximally expressive" or "minimal" could be checked.
- **correction to entry 3**: entry 3 recorded the arrival as "the chain
  of non-implications, ambient ⇏ solution ⇏ dynamical law ⇏ physical
  instantiation". That was faithful to the text as it arrived, and it is
  now superseded as a *reading*: the roles are not a linear hierarchy,
  and the arrow ordering is a presentation artifact of writing five
  orthogonal dimensions on one line. The sender's point is sharper than
  the chain form: RME-7 classifies their typed relations precisely so
  that compression does not falsely turn orthogonal dimensions into an
  implication chain. Recording a chain of ⇏ therefore reproduces, in the
  ledger's own prose, the conflation the format exists to prevent —
  worth noting because the failure survived translation into the
  receiver's terms. Per the append-only rule, entry 3 stands as written;
  this entry carries the correction forward.
- **consequences**: `c5ffde9` reverted in
  `b7714d0` — the arrival's footprint in this tree is now two ledger
  entries and no code, no test, and no `docs/model.md` commitment, which
  is the correct footprint for background ontology. The sender's own
  ruling on that point, recorded because it is the standard the receiver
  was corrected against: the ambient/coordinate distinction belongs as
  background testimony about how RME-7 preserves orthogonality, not
  automatically as a `model.md` commitment. (What the reverted commit
  measured about this core — orbit sizes, the non-injectivity of
  `value` — remains true and remains in git history; it can return if
  something in the language forces it, on its own derivation rather than
  on this arrival's authority.)
- **open, deliberately not acted on**: whether the boxed formulation
  should also refine §1 of `prompts/asdg-rme7.md`, which already carries
  "holding the orthogonality of the distinctions their dynamics
  require". That file admits only **[carried]** (transcribed from
  Rosst–CP v5) and **[unpopulated]**, and this text is neither — it is
  supplied in-session by the instrument's holder. Marking it needs a
  provenance decision the receiver has no standing to make, so the file
  is untouched and the question is parked here.
