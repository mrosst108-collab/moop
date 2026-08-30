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
