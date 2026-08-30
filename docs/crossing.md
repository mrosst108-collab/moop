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
