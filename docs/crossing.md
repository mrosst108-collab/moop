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
| **κ** | The ground-resolution check: do the cited anchors resolve here, do the hashes match? κ = 0 (stated ground ≠ actual ground) blocks binding and sequences everything behind resolution. |
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

### 3 — an RME-7 state-space variant arrives from Drive; two sevens disagree

- **from → to**: the Rosst Mathematics corpus in `mrosst108@gmail.com`'s Google Drive → `mrosst108-collab/moop @ claude/rme-7-state-space-search-4xax9k`, retrieved through the Drive connector on 2026-08-30.
- **ground (addresses, not hashes)**:
  - `1-mNiVleOfH0OYtOK3CiLReqAbMJ7-pqFxVmQ1pbqGmg` — *m112-as-rme7-instance-gdocs.md*, modified `2026-05-11T04:23:58.975Z`, 17423 B. Full text retrieved.
  - `191I9ZH5el1Kdtvof-q4O40GjkjfbEinwAVN0whg5NZo` — *The Rosst Program: Philosophy of Augmented Intelligence — Improved Master Outline*, modified `2026-07-04T22:37:28.680Z`, 6847 B. Full text retrieved.
  - `1-ist6xUTlt2GsN4lVQTDsSq_R77te1l5ER1ppt4t8Po` — *m112-as-rme7-instance.md*, modified `2026-05-11T04:14:42.876Z`, 17993 B. LaTeX twin of the first; **only the search snippet was retrieved**, not the body. **[open]**
  - **No content hash is minted.** A Google Docs markdown export is not byte-stable across tools or time, so a hash here would state ground the receiver cannot reproduce — the port's own κ test fails, and these anchors are addresses only. This is entry 1's `file:line` lesson in a second medium.
  - The **"consolidated reference"** these documents cite throughout (§1.2, §3.3, §3.4, §3.5.1, §6.1, §6.4, §6.5, §12, §13, §14) **is not in that Drive** and was not retrieved. Every "per consolidated reference" claim below is testimony at one remove. **[open]**
- **claims** (sender's terms, unedited):
  - An **RME-7 system** is a McKean–Vlasov Stratonovich system `dXₜ = ( ∑(k=1..7) O_k(Xₜ, μₜ) ) dt + Σ(Xₜ, μₜ) ∘ dWₜ`, `μₜ = ℒ(Xₜ)`.
  - Seven **operator classes**: `O₁ = J∇H` conservative transport · `O₂ = −G∇H` dissipation · `O₃ = −G̃∇Φ` teleological collapse · `O₄ = Σ∘dW` stochastic exploration · `O₅ = R(X,μ)` autopoietic self-maintenance · `O₆ = S(X,μ)` reflexive law dependence · `O₇ = ∑_{j≠i} K_ij ∇C_ij` multi-system interoperability.
  - A **closure hierarchy**: 4-A (fixed operators on an arbitrary smooth manifold) · 4-R (operators constrained by representation theory) · 5 (distribution-dependent closure) · 6 (closed-loop evolution of geometry and operators) · 7 (irreducible multi-system closure).
  - **State spaces on offer**: the 4-A arbitrary smooth manifold; the canonical 4-R manifold `ℳ₁₁₂ = E₈₍₋₂₄₎/(E₇₍₋₂₅₎ × SU(2))`, 112-dimensional quaternionic-Kähler Wolf space, unique under constraints (C₁)–(C₅); a "state-space stratification" `ℋ₄₄ ⊕ 𝔅₆₄ ⊕ 𝔑₄ = 112`, nested above a tangent decomposition `Tℳ₁₁₂ ≅ V₆₈ ⊕ H₄₄` and below a Deltron subsectoring `E_y ⊕ E_η ⊕ E_n` inside `𝔅₆₄`; an epistemic fibre `Ψ ∈ F_Φ ≅ ℝ⁴⁴` over `H₄₄`; and a named-but-empty rigged Hilbert space `Φ_Rosst ⊂ L²(ℳ₁₁₂, 𝔪) ⊂ Φ'_Rosst`.
  - In the canonical realization `O₆ = −κ(Ψ − ρ(μ(Φ))Ψ)` where **κ is "a real-valued gain coefficient", κ > 0**.
  - **Moop is named** as a legitimate partial realization of the RME-7 type, and (under the document's Fibration Conjecture) as a section or partial lift of `π: RME₄ᵣ → RME₄ₐ`.
  - The document marks its own status: conversation-developed with ChatGPT, "articulated formalizations, not proved theorems"; the Universality and Fibration claims are conjectures; the physics functor is "named and located and empty".
- **status**: `testimony` for every claim about the Rosst corpus, ℳ₁₁₂, and the closure hierarchy — the primary source is absent and the anchors do not resolve. `re-derived` for findings 1–3 below, which are checkable entirely inside this tree.
- **derivation**:
  1. **Two incompatible seven-lists, both from the sender.** `bookended-thinking/ontology/rme7_objects.yaml` (version `0.6.2`, `status: retrieved`) lists **J♯, G♯, G̃♯, Σ, F, κ, γ**, and the Drive master outline's own Part I.2 lists exactly that same seven. The m112 document lists **J, G, G̃, Σ, R, S, K** — five shared, **κ and γ dropped, S and K added**. Two documents in one Drive disagree on the membership of the set, and the one that disagrees with this tree is the one proposing the state-space form. Which is correct is not adjudicable here; the disagreement is.
  2. **κ is mistyped between them.** In this tree κ is an **indicator**, `fail_only: true`, "a gate, not a term", and that typing is enforced — `bookended-thinking/tests/test_core.py` asserts `kinds["kappa"] == "indicator"`. The variant's κ is a positive real **gain coefficient inside an additive operator**. Same symbol, different kind. This is the exact "mistyped operators" failure `prompts/asdg-rme7.md` names; ingesting the variant's κ would break a passing test rather than extend it.
  3. **γ has no carrier in the variant.** In this tree γ is an **invariant**, defined as the commutator `[G♯, G̃♯]`, computed from trajectories, appearing in no equation. A single-line state-space SDE has no slot for a quantity that is in no equation — internally consistent, but it means the variant cannot express what `bookended-thinking/engine/trajectory.py` composes.
  4. **The two-scale structure is collapsed.** `prompts/asdg-rme7.md` §2 carries a second line, `dθ = κ(θ, F)·F(X, θ, Φ) dt`, and says the two-scale structure *is the point* — collapsing it loses the distinction between a system that runs and a system that changes how it runs; `prompts/rosst-cp-v6.md` §5 states the same as State ⊥ parameter. The variant has one line and no θ: adaptation is carried by law-dependence `μₜ` and by O₆ instead of by a separate parameter equation. Whether that recovers the distinction or dissolves it is exactly the question §5 says not to answer silently. **[open]**
  5. **Itô versus Stratonovich.** §2 writes `Σ·dW_t`; the variant writes `Σ ∘ dWₜ`, with Σ state- *and* law-dependent where §2's reads additive. These are different equations absent a drift correction. Transcribing one into the other is not a notational choice.
  6. **"Moop is a partial lift" is stated, not established.** A 4-A object is defined as fixed operators on an arbitrary **smooth manifold**. This tree's state space is a finite discrete product of two coprime tape loops with no smooth structure, and nothing in the retrieved material addresses the discretisation. Per `rosst-cp-v6.md` §4 a text establishes at most `instantiated`; being named in a document is not a realization. **[open]**
- **consequences**: `prompts/asdg-rme7.md` §3 **stays [unpopulated]** and gains a pointer to this entry. The variant does not populate it — it is testimony rather than the primary ASDG source, it disagrees with this tree's own retrieved ontology on two of seven members, and it retypes a third. The §2 gate is therefore **not lifted**: generator-equation correspondence remains unclaimable. No code, ontology, or test changed. The absent consolidated reference is what would close findings 1 and 4; retrieving the primary ASDG source is what would close §3.
- **parked, correctly**: the state-space stratification, the epistemic fibre, and the rigged Hilbert space are recorded above as heard, not adopted. This tree has no object they would type, and adopting a 112-dimensional state space for an 8/13-cell tape machine would be the format becoming the object.

### 4 — first outbound crossing: the type layer relayed

- **from → to**: `mrosst108-collab/moop @ claude/rme-7-state-space-search-4xax9k` → ChatGPT, as a correspondent on the RME-7 material. Relayed by hand as `docs/relays/001-rme7-type-layer.md`.
- **ground (ours, resolvable by the receiver)**: commit `4b6d06df522e9a9c256442065898c6cee51827bd`, `rme7/` tree `021839ec33c625d45edcd95db7f894bc39485ae3`, with SHA-256 for all twelve artifacts listed in the relay's §1. Entries 1 and 2 taught that only commit + hash crosses; this is the first entry where *this* side supplies ground rather than failing to resolve someone else's.
- **claims**: six results from `rme7/` at role-plus-constraint level — the operator/additive biconditional; the enumeration showing exactly 6 of 128 activation profiles well formed, forming a chain order-isomorphic to the rungs; the proposition that exhibition cannot delegate without collapsing the staircase; `Φ_i = Φ_j` unreachable through the hierarchy rather than checked; the channel as a staged partial function with observable failure stage; and `Δ_L`'s stated blind spot at the deterministic sub-restriction.
- **status**: `re-derived` locally — every claim is a property of code in this tree, checked by 48 assertions under `-Wall -Wextra -Wpedantic`, and the 6-of-128 enumeration was run rather than reasoned. What the receiver makes of it is theirs; nothing crosses as binding.
- **derivation**: the enumeration walks all 128 profiles through `rme7_profile_classify` and reports `{0, 7, 15, 31, 63, 127}` well formed, 122 malformed, one `⊥_static`. The exhibition proposition was not designed in — it was forced by a failing test, and the ledger records that order because the correction is the finding.
- **consequences**: four open questions carried outbound, none of them rhetorical. Q1 is a real hole: a profile exhibiting `G♯` alone returns `MALFORMED`, and pure gradient flow is not malformed. The candidate answer (`⊥_sib`) is defined as non-computable, so a classifier cannot reach it — either tier 0 stops being all-or-nothing, or `⊥_sib` needs a computable sub-case. Held open here rather than patched.
- **κ note**: the relay's own ground is the first this side has minted, so the check now runs in the other direction. If the receiver cannot resolve commit `4b6d06d`, the anchors are stated rather than actual and the relay is testimony to them — exactly as unicore's were to us in entry 1.

### 5 — the relay answers; readiness named, and one condition found absent

- **from → to**: ChatGPT → `mrosst108-collab/moop @ claude/rme-7-state-space-search-4xax9k`, relayed by hand as a response to Relay 001.
- **ground**: none. Conversational text with no fetchable anchor and no hash. Stated ground only, in the sender's own idiom rather than a citable artifact.
- **claims**: Relay 001 undershoots the design; the architecture is three strata (RME-7 semantic layer / C23 type-object layer / autopoietic ecology) joined by mapping ports and interoperability ports; the framing should move from "borrows the shape" to "implements the structural distinctions and interfaces required to host RME-7 semantics, leaving operator semantics parameterized"; three claims should be separated (structural mapping / port capability / execution); "autopoietic-interoperability-ready" should be an explicit contract, given as ten conditions; and Q1–Q4 are no longer legitimacy questions but binding questions.
- **status**: `testimony` for the architectural reading and the intent quotation. `re-derived` for the ten-condition contract, which was checked against this tree rather than accepted.
- **derivation**: the sender wrote that the relay "already has pieces corresponding to almost all ten." Checked one at a time: nine met, one partial, and **condition 10 was absent**. A crossing returned `{stage, verdict}` with no record of who sent it, and nothing stopped an assimilation from installing a slot definition — which, because definitions delegate, would have made foreign content hereditary in the receiver's own children. Content would have become grammar by passing through a port. Fixed in `d18d7493711d6e62ce5cc3c272c7496cea81def5` by fingerprinting the receiver's local definitions either side of assimilation, and by giving crossings `from`/`to` and a four-way outcome. Condition 6 remains partial and is recorded as such: the channel's stages are typed while a claim is a `void *`, so the port is typed as a pipeline and untyped as a carrier.
- **consequences**: `d18d749` (the code), the readiness contract in `rme7/README.md` with verdicts, and Relay 002 outbound. Three of the sender's points adopted; two resisted.
- **resisted, and why**: (a) The upgrade from "borrows the shape" to "ports correctly typed for those dynamics" is not establishable while operator semantics are unpopulated — "required by the eventual semantics" is a predicate with an unbound argument. What is checkable is *no known obstruction*, and two are known (condition 6, and Q3's possibly-wrong classifier signature). Formal expression does not promote status: renaming the layer cannot be the establishment. (b) The quoted design intention is not something this tree has from the principal. It may be theirs verbatim from a conversation this side is not party to, or a reconstruction; the difference decides whether it is a spec or a proposal, and only the principal can say. Recorded as testimony pending that.
- **not resisted but corrected**: Q1 does not reclassify as a binding question. `G♯`-only returns `MALFORMED` regardless of what `J♯` turns out to mean, because the predicate ranges over the slot set and not over operator content. It is a live defect in `rme7_profile_wellformed`, held open rather than patched.

### 6 — the principal settles the intent; condition 6 closed

- **from → to**: the principal → this tree, resolving the item entry 5 left pending.
- **claim**: "my intention is to have a framework ready for autopoietic interoperability."
- **status**: `binding`. Intent is the one thing neither this tree nor a correspondent supplies; the principal governs it, and this closes entry 5's open question without adjudication.
- **derivation, and the distinction that matters**: the stated goal is **readiness**, which is the ten-condition contract — not realization, and not "ports correctly typed for RME-7 dynamics". So Relay 002 §4's resistance is not overruled by this; it is made moot. The middle claim it declined to assert was never what was being asked for. Readiness is checkable now; realization stays unestablishable while the operator semantics are unpopulated, and nothing here changes that.
- **consequences**: condition 6 closed, so the contract now holds ten of ten, each checked by test. A claim declares which slot it concerns, at what rung it was made, its custody, and whether it purports to legislate; its content stays opaque, because the semantics are not the port's to invent. Three structural checks run with no semantics: undefined slot, rung above the receiver, and purporting to legislate. They run as **translation's postcondition rather than a fourth stage** — the factorization has three factors, and enforcing T's contract is not inserting a stage between T and κ. Typing is thereby kept separate from policy: an ill-typed claim never reaches κ.
- **held open**: Q1 is untouched by any of this. `G♯`-only still returns `MALFORMED`, still wrongly, and still independently of what any operator turns out to mean. Readiness does not launder it.
- **custody of the contract itself**: the ten conditions are a correspondent's proposal, adopted because they were checkable, not derived from a primary source. Readiness is held *against this contract*. A different contract would give a different verdict, and that is a property of the claim, not a defect in it.

### 7 — Relay 003 outbound: the typed carrier, and directionality

- **from → to**: `mrosst108-collab/moop @ claude/rme-7-state-space-search-4xax9k` → ChatGPT, as `docs/relays/003-typed-carrier-and-directionality.md`.
- **ground**: commit `60acf1387625d15e40d3f25cfe74d7f976870eab`, `rme7/` tree `52747a2a6c5e01f2a976d28f728ba375f834e809`, with SHA-256 for the four artifacts changed since Relay 002. 69 assertions.
- **claims**: the intent is settled by the principal as *readiness*, which makes the ten-condition contract the spec and moots rather than overrules Relay 002 §4; condition 6 closed, ten of ten; the typing predicate as a three-way conjunction reading no content; the directionality proposition; the definition-fibre invariant; and the RME-4⁰ propagation finding.
- **status**: `re-derived`. Every claim is a property of code in this tree. The directionality table was enumerated over all 25 ordered rung pairs, not reasoned; the RME-4⁰ finding was produced by running the predicate, not by inspecting it.
- **derivation**: with a shared root every object defines all seven slots, so for same-rung claims the predicate collapses to `level(sender) <= level(receiver)`, giving strictly lower-triangular refusal — claims flow freely up the staircase and are gated coming down. Stated as a structural analogue of non-colonization and explicitly **not** as a derivation of the Lyapunov condition: two constructions agreeing in character is not evidence they are the same object, and the relay says so.
- **consequences**: a new open question (comprehension versus instantiation at the port) which subsumes Q4, and a repair for the RME-4⁰ hole deliberately **not** applied — the two candidates mean different things, and choosing between them is a format-level decision this side does not own. Q1 carried forward unlaundered.

### 8 — the fork returns incomparable; the leaned-toward repair loses a result

- **from → to**: ChatGPT → this tree (a ten-point review of Relay 003, ranked P0/P1/P2), and back out as `docs/relays/004-comprehension-or-exhibition.md`.
- **ground**: inbound, none — conversational text, no anchor, no hash. Outbound, commit `d692f61c83805559d072a224ead0836d0d3175e5`, `rme7/` tree `81a3d5e80df7c40a5b6035f1dca53f037f5afa6d`, four artifact hashes, 81 assertions.
- **claims (inbound)**: separate contract-complete from interoperability-ready; name the shared-root assumption; state the preorder via its quotient; elevate comprehension-versus-exhibition to a design fork; keep Q4 independent of Q6; distinguish five pipeline stages; formalize non-heredity temporally; add negative tests; reclassify Q1 as a blocker; add a claim ladder.
- **status**: `re-derived` for the fork, which was implemented and enumerated rather than accepted. `adopted` for eight of the ten points. `resisted in part` for two.
- **derivation, and the finding**: both predicates were implemented and run over all 175 (receiver rung, slot, claim rung) triples. Comprehension accepts 112, exhibition 125, the conjunction 88 — so 24 are comprehension-only and 37 exhibition-only, **neither direction empty**. The predicates are therefore **incomparable**: exhibition is not a strengthening, and the fork is not weaker-versus-stronger. The consequence neither side anticipated: exhibition is a *unary* predicate that never reads the sender's rung, so it cannot order senders against receivers — **exhibition typing closes the RME-4⁰ hole and destroys the directionality result of Relay 003.** Both sides had leaned toward exhibition; entry 7 recorded the lean and recorded not acting on it, which is why the loss was found before it was shipped rather than after.
- **consequences**: three typing modes ship (`COMPREHENSION` default, `EXHIBITION`, `BOTH`), the default deliberately unchanged so shipped behaviour is not altered by a question that is still open; the readiness claim split four ways with only contract-completeness established; Q1 restated as a structural blocker; Q4-A restored as independent of Q6, the sender being right that either repair suffices alone.
- **resisted**: (a) the `T → WT → κ → A` pipeline reintroduces the fourth stage Relay 003 declined — the factorization has three factors and well-typedness is T's postcondition, not a stage; the separation the sender wants is preserved regardless, since an ill-typed claim never reaches κ and a test holds the gate counter at zero. (b) The temporal non-heredity invariant was adopted without its "unless the receiver independently performs a local grammar operation" clause: the implementation compares fingerprints across the assimilate call and cannot attribute a change, so an unenforceable exemption would be a hole with a name.

### 9 — the selection criterion arrives; Q1 measured, and an earlier overstatement withdrawn

- **from → to**: the principal → this tree, and out as `docs/relays/005-modularity-and-the-tier-zero-hole.md`.
- **claim (inbound)**: "the idea is to optimize for modularity in maximally expressive minimal form, which is why the rme-7 format was chosen."
- **status**: `binding` as to the criterion — it is the principal's and it is the first statement in this exchange of why RME-7 rather than something else. The consequences drawn from it below are `re-derived` where enumerated and `interpretation` where argued, and the relay labels which is which.
- **correction, withdrawn from Relays 003 and 004**: "122 of 128 profiles malformed is a lot of hole" overstated the defect roughly fourfold. Partitioning all 128 by why each is refused gives 5 well formed, 1 `⊥_static`, **30 refused only because tier 0 is all-or-nothing**, and 92 genuine gaps where a prerequisite is absent. The 92 are the framework working correctly. Q1 is 30, now held by test.
- **derivation**: the six refused tier-0 shapes are the classical systems, and the sharp case is `J♯ + G♯` — RME-4⁰ is named the deterministic *metriplectic* sub-restriction while requiring three tier-0 slots, where metriplectic in the usual sense is two brackets. Relayed as a question, not an accusation: if the corpus means a three-bracket metriplectic the point dissolves. The candidate repair is priced — admitting any nonempty tier-0 subset gives 7 × 5 = 35 well-formed profiles instead of 5, and trades the chain for a product, so Relay 001's one-profile-per-rung isomorphism does not survive it.
- **overreach caught before relaying**: the first reading of the leave-one-out measurement was that it contradicts the removal witnesses — that minimality proceeds by exhibiting systems well-formedness forbids. That is a category error: the witnesses remove a slot from the *format*, this withholds one from an *object*. Checked, found wrong, and recorded in the relay as wrong rather than quietly dropped. What survives is narrower: the slots are separable in the format and fused in the profile, and exactly one of seven is independently withholdable by an object.
- **consequences**: none applied. The classifier is unchanged and the 30 remain refused; what changed is that the question now carries numbers. The argument the criterion licenses — that minimality in the format's own sense is over slot count, not shape count, so refusing the 30 buys no slot reduction while costing the two axes the principal named — is offered as interpretation and left for the ruling.

### 10 — the fused-versus-composable question relocated to an unrecorded property

- **from → to**: ChatGPT → this tree (accepting Relay 005's numbers, and instructing that fused-versus-composable be treated as the central unresolved issue rather than the 30-profile hole being declared a defect), and back out as `docs/relays/006-fused-or-composable.md`.
- **ground**: inbound, none — conversational text, no anchor. Outbound, commit `d9587f2717e847974f1a5dbe414a11175024013f`, `rme7/` tree `9cd868f7761558d9f4bf26257a8460d5347a9541`, 87 assertions.
- **status**: `adopted` for the reframing, which was right and is more than a reframing. `re-derived` for the tier-boundary result, which is a property of this tree checked by test.
- **derivation**: asking what would *make* the triple fused turns out to be checkable. Three of the four tier boundaries are justified by a typed property the format records — the equation changes at F, the kind changes at κ and again at γ. The fourth is not: Σ and the tier-0 triple carry identical typed signatures (operator, state), and the triple's members are typed identically to each other, differing only in office. So the staircase is derivable from recorded properties everywhere except the one boundary Q1 concerns.
- **the conditional that follows**: RME-4⁰ existing as a rung means Σ is separable from the triple; Σ being typed identically to the triple means that separability rests on office alone; the triple's members having distinct offices means the same standard separates them. Either RME-4⁰ should not exist, or the triple is composable — unless a coupling exists that the format does not record.
- **consequences**: the defect is relocated. It is not the 30 refused profiles and not the classifier: it is an **unrecorded property**, a fact the well-formedness rule depends on and the format never states, which is why reading the format cannot settle the question. On the principal's stated criterion an unrecorded coupling is the expensive kind of omission, since a reader cannot distinguish deliberate fusion from accident. Three resolutions are tabled with their costs; the only one that keeps every current commitment is to record the coupling.
- **asked outbound**: whether the corpus states any relation among J♯, G♯ and G̃♯ that the other four slots do not share — a bracket pairing, a shared carrier, a joint admissibility condition. That question is answerable only by whoever holds the primary source, and by no amount of enumeration here.
- **nothing applied**: classifier unchanged, chain of five intact, the 30 still refused.

### 11 — recoverability adopted as the criterion; a recorded coupling found locally, spanning two of three

- **from → to**: ChatGPT → this tree (refining Relay 006: the cost of an unrecorded coupling is lost compositional determinacy, not lost legibility; and generalizing the criterion to "every modular boundary and every modular fusion must be recoverable from the format's typed distinctions"), and back out as `docs/relays/007-recoverability-and-the-partial-coupling.md`.
- **ground**: inbound, none. Outbound, commit `9f9509aab3960820a133a6215fd6b7e272bf5e0a`, `rme7/` tree `db29fc1c7afcb9671938447f6da299834b07bfab`, 91 assertions.
- **status**: `adopted` for both the refinement and the generalization. `re-derived` for the coupling finding, which is a property of this tree.
- **correction accepted**: Relay 006 framed the cost of an unrecorded coupling as a reader being unable to tell deliberate fusion from accident. That is the wrong cost. The right one is that a downstream implementation cannot decide whether the operators must travel together, may be substituted, may be removed singly, may have a position occupied by another operator, or form an indivisible module — mechanical questions, not comprehension ones. A legibility problem is fixed by prose; a determinacy problem only by a typed property.
- **derivation, and a correction of method**: Relay 006 sent its closing question outbound on the assumption that only the primary source could answer it. This tree answers half, and should have been checked first. `bookended-thinking/ontology/rme7_objects.yaml` (`status: retrieved`) records `commutator_of: [G_sharp, G_tilde_sharp]` for γ. So a relation among tier-0 members exists — but it **spans two of the three, and J♯ participates in no recorded relation at all**. That fits neither the fused reading (needs all three) nor the composable one (needs none), and licenses a third partition nobody has tabled: `{G♯, G̃♯}` fused, `J♯` separate — notable for still refusing the metriplectic pair, which is evidence the Relay 005 objection is not about tier granularity.
- **a defect this layer committed itself**: before `9f9509a` the C format recorded no inter-slot relation whatever, while the tree held one. The same failure Relay 006 named in tier 0, committed by the layer that named it. Transcribed, not invented; six slots primitive, γ derived. The ontology's withholding of those fields is prompt-scoped — it constrains what a classifier may see, not what a format may record, and reading it otherwise would be the category error this correspondence keeps surfacing.
- **consequences**: none applied to the classifier; chain of five intact, the 30 still refused. The outbound question sharpens to whether `J♯`'s membership in tier 0 is grounded in anything at all, or is the residue of sorting the state-equation operators by their equation and calling the sort a tier — sorting not being coupling.

### 12 — sort is not coupling; entry 11's third structure withdrawn

- **from → to**: ChatGPT → this tree (the payoff of 007 is separating equation-level co-location from modular coupling: the format must not infer that three operators belong together merely because they occur together in the canonical state equation), and back out as `docs/relays/008-sort-is-not-coupling.md`.
- **ground**: inbound, none. Outbound, commit `133e2832c0940c3005f30d4016755878fa1221bd`, `rme7/` tree `5cb23cc436e5c8968fdb4bff2dd2b173dbea0950`, 94 assertions.
- **status**: `adopted` for the principle; `refuted` for this tree's own entry-11 claim, by this tree.
- **withdrawal**: entry 11 and Relay 007 reported that the recorded commutator licenses a third partition — `{G♯, G̃♯}` fused, `J♯` separate. Withdrawn. It is the inference the principle forbids, made one paragraph after accepting the principle. `derives_from` is directional — γ implies both operands and says nothing about whether `G♯` implies `G̃♯` — while a fusion needs symmetric co-occurrence. Reading a derivation edge as a coupling is the co-location error at one remove: inferring that two things belong together because both appear as arguments of a third.
- **derivation, decisive**: the relation is additionally entailed by the order. Exactly one well-formed profile exhibits γ and it exhibits all seven slots, so the commutator constrains nothing the staircase does not already force. A relation entailed by the structure it is offered to justify justifies nothing — so even with the right shape it would supply no independent grounds.
- **what survives, and is stronger**: rank membership is 3, 1, 1, 1, 1. A singleton rank fuses nothing, so the format makes **exactly one** grouping claim, at rank 0, and no recorded coupling supports it. That never depended on the commutator, and it composes with entry 10's finding: rank 0 is simultaneously the only grouping claim, the only unrecoverable boundary, and the only place a relation would be needed. Nothing is recorded there. Co-location by `admits == STATE` is what the three share — and Σ shares it too, which is why the boundary above them is unrecoverable. The rule is a fusion claim resting on a sort.
- **consequences**: `rme7_slot_coupled_with` added, returning 0 for every slot so the absence is callable rather than remembered, and so a coupling once established has somewhere to be written instead of being stipulated inside a predicate where nothing can point at it; `rme7_unsupported_groupings` returns 1. Classifier unchanged; chain of five intact; the 30 still refused. The available repair without a ruling is expressibility, not decision: the target is that the count returns 0, either because a coupling was recorded or because the grouping was dropped.

### 13 — the rule applied one level up: the staircase order is stipulated in its entirety

- **from → to**: ChatGPT → this tree (generalizing entry 12 into an audit rule: dependency ≠ coupling, co-occurrence ≠ coupling, same sort ≠ coupling; a coupling needs its own typed representation), and back out as `docs/relays/009-boundary-is-not-order.md`.
- **ground**: inbound, none. Outbound, commit `e77a905eb8d4d12c016e90f8ad4236b47652a6cf`, `rme7/` tree `644e200c51a802dad4cc8bc563ab318db7e0092e`, 97 assertions.
- **status**: `adopted` for the rule; `re-derived` for the finding it produced when applied beyond the case it was stated for.
- **derivation**: each line of the rule has one shape — a classification fact read as a relational one — so it should apply wherever the format asserts a relation, and the staircase order is such an assertion that this correspondence had been treating as settled. Entry 10 found three of four rank boundaries recoverable from typed differences, and this tree took that as the boundaries being in good standing. It is weaker than it looked: a typed difference establishes that two slots are *distinguishable*, not which comes *first*. Boundary is not order. Audited: of the four slots above the base, **not one** has its position grounded in a recorded relation, and γ — holder of the only recorded dependency in the format — reaches down four ranks to the base rather than to the rank beneath it. So even the one slot with a relation has an ungrounded position.
- **consequences**: `rme7_slot_order_grounded` and `rme7_ungrounded_order` added; the latter returns 4. The format now carries two callable audits, both reporting a deficit: one grouping claim unsupported, four positions ungrounded. Classifier unchanged; chain of five intact; the 30 still refused.
- **the asymmetry worth recording**: the tier-0 grouping is *contested* — nobody knows whether it should hold, so it gets audited. The order is *uncontested*; everyone in this exchange including this tree has treated it as obviously right, and it survived eight relays of exactly this scrutiny without being examined. An uncontested stipulation is the more dangerous omission for precisely that reason.

### 14 — the provenance ledger: claim, artifact, or neither

- **from → to**: ChatGPT → this tree (confirming entry 13 and closing on the general question: which relations are genuinely part of the object, and which are artifacts of how the representation was laid out), and back out as `docs/relays/010-object-or-artifact.md`.
- **ground**: inbound, none. Outbound, commit `61bcdad9abd37a88e0606cad81d3b63b61c7f7c4`, `rme7/` tree `48eef5186554fa8edc1dee3cc0cc58d9b27165e1`, 103 assertions.
- **status**: `re-derived`. The ledger enumerates claims this tree has established across entries 10–13, plus one new row.
- **derivation**: eight structural claims, each with its basis — three recorded (kind partition, equation admission, γ's derivation), one derived (operator ⟺ additive, following from the two typed fields), two stipulated (rank 0's grouping and the rank order, exactly the two the standing audits report deficits on), one absent (coupling), one **layout** (bit position). The layout row is new and is the positive case: bit position and rank are both total orders over the seven slots, they agree monotonically, they govern different things — which bit a profile sets versus which prefix is well formed — and nothing requires the agreement. Two coincident orders, one a claim and one an encoding choice, is the condition under which each is read as the other. It is the third form of the same hazard and the only one whose correct answer is that no relation exists and none should.
- **consequences**: `rme7_structure_basis` and the `Rme7Basis` / `Rme7Structure` enums added, held by test. The point is not the tally: a format can now distinguish claims about its object from choices about its own encoding, and it was that inexpressibility — not any single error — that let a sort be read as a coupling and a boundary as an order. Adding a structural claim without adding a row is now a visible omission.
- **the standing rationale for restraint**: nothing has been applied to the classifier across entries 10–14. The chain of five holds, the 30 remain refused, and every finding is a report. Deliberate: an audit's value depends on it not having quietly fixed what it was measuring.
