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

### 3 — the RME-7 multi-track card arrives; its ports land as protos

- **from → to**: the Rosst Program register (realization card B.7, autopoietic-ecology regime) → `mrosst108-collab/moop @ claude/rme-7-multitrack-ports-990dt4`, relayed by hand as text. The relay declares custody: anchored in the Rosst register unless marked `[pending]`; Mark Rosst sole ratifying authority; relays assemble and criticize, never adjudicate or promote.
- **ground (sender-side, unverifiable here)**: none — no commit, no content hash; "the Rosst register" is not a repository this tree can fetch. Stated ground only: κ > 0 for every claim below, so nothing binds by arrival. Local ground for what landed: `a0a7faf6b63048581c460394ab99bc861d323f92` (`src/rme7.h` `ed070bf5b175deaacc59addc8cdd44cdd614838e381894fba16ad97f85094989`, `src/rme7.c` `a4ff82908a87c9c73ea97064b332e6e43de2c608254c8e55ee8869455199b37c`, `src/eval.c` `0dae462c0134222fc1217053e9934d87abd6fbbeb43f3257e04449d61b4dd2ee`, `docs/model.md` `045c095934dc55211485ee0e3bec64dce75df0328f29b9cd8d059ad68e460b90`, `tests/test_core.c` `b7b2768cc7e15e6f831a9b060143a350f71126823b754ed253b819fc8590e50f`), and the independent pre-relay artifact `bookended-thinking/ontology/rme7_objects.yaml` at `dec435d` (version 0.6.2, status retrieved).
- **claims** (sender's terms, close transcription; full text in `prompts/asdg-rme7.md` §11–12): per track *i*, `dX_i = (J♯_i(dH_i) − G♯_i(dH_i) − G̃♯_i(dΦ_i)) dt + Σ_ii ∘ dW_i + Σ_{j≠i} Σ_ij ∘ dW_ij`, `dθ_i = κ(𝒯_i; φ_i) · F_i dt`, `Σ_ij = A_i ∘ κ_i ∘ T_ij` (adapter ∘ gate ∘ translation). Signature ⟨J♯, G♯, G̃♯, Σ, F, κ, γ⟩ — "7 primitives, 6 operators", γ = [G♯, G̃♯] derived, "not an operator, not itself an observable". κ has two sites, κ_F and κ_Σ; "their identity is open, not decided by notation". Card conditions: block-diagonal offices; G♯_ij = 0 held throughout the trace, not only at endpoints; cross-track relation carried on the ports; Stratonovich; F_X = 0. "This is a card, not the grammar": the canonical form is single-track, `dθ = F(X, θ, Φ, κ, Ψ) dt` with κ and Ψ arguments of F, the product κ·F a documented realization variant; "do not expand the grammar from this card." Framework handles: track = one object's X_i and θ_i; port = a typed relation between objects; U₂ = a gluing along the coupling graph (a colimit only if the interface algebra is shown to be a category); Del(U₂) a predicate — G♯ cross-terms vanish, permitted cross-sector relation sits in G̃♯, κ governs admission; capture := G♯_ij ≠ 0. `[pending]`: N(U₂) negative space, two grains (refused vs absent ports); the flux/veil/witness lexicon for T/κ/A. Testability: ρ_rel against a fixed, executed sota baseline. Guards verbatim (§12).
- **status**, by claim:
  - the card, the handles, the standing instruction, the guards — `testimony` (recorded in `prompts/asdg-rme7.md` as `[relayed]`, never as `[carried]`).
  - γ typed derived (commutator, not an operator, not a single-trajectory observable) — `re-derived`: `rme7_objects.yaml` had it before this relay as `kind: invariant`, `definition: [G#, G~#]`, `computed_from: trajectories`, "no single classification can carry it". Independent agreement.
  - "6 operators" (κ counted among them) — `refuted` locally: the loaded ontology types κ `indicator` and `engine/ontology.py` hard-asserts 5 operators / 1 indicator / 1 invariant. Re-typing κ as an operator and loading it raises `OntologyError: the axis is not homogeneous by design: expected 5 operators, 1 indicator, 1 invariant`. Recorded, not resolved: the refutation is of the count under *this tree's* typing, and the relay's own canonical form makes κ an argument of F — neither an additive operator nor the yaml's "multiplicative gate", which reads the realization variant. Both typings are now open questions for the ratifying authority, not for us.
  - the port factorization A ∘ κ ∘ T — `re-derived`, twice. (i) This document: the Σ row (the typed entry, A), the κ row (ground resolution, κ), and the rule that a claim is re-derived into the receiver's terms (T) — the three factors were already here, unfactored. (ii) The language: `<->` is encode (T, `src/encode.c`) ∘ refuse-oversize (κ, `src/eval.c`) ∘ gate deposit/exchange (A). The card's port is moop's bijection.
  - capture and "held throughout the trace" — `re-derived`: this document's G♯ row (nothing from an unbound crossing may be committed; the entry precedes the commit) is the pre-commit form of "G♯_ij = 0 throughout, not only at endpoints".
  - the §2 correction (canonical dθ has κ, Ψ as arguments) — `testimony`; consequence below. Ψ is defined by no source available here.
  - `[pending]` items and ρ_rel — `parked`. No executed baseline exists in this tree; `bookended-thinking` already stamps every report `COHERENCE_ONLY` for the same reason, so ρ_rel arrives into a discipline that refuses to promote it.
- **derivation**: the deletion test, applied to the operator's proposal "a port for each RME-7 primitive". A cross-track port of each primitive either *is* the port (Σ), is its gate factor (κ), is the failure condition by the card's own definition (G♯: capture), merges the tracks into one (J♯), is covered by a port that exists (F: Σ_ij delivers into X_i and F_i picks it up under κ_F), has nothing to carry (γ: derived), or awaits a ruling the card and Del(U₂) leave open (G̃♯: block-diagonal offices vs. cross-sector confinement — *sector* and *track* are not shown to coincide). Seven ports do not survive; one port with seven-typed content does — which is what this document already was — and the enumeration itself is the `[pending]` negative space with both grains filled in. So the card adds no coupling mechanism here, only objects: the framework's handles as protos, generated by the world, with the enumeration hosted as four exclusive verdicts. That is the relay's own requirement — "what a framework built on this must make machine-checkable: ... what promotion would be a category error" — met with zero new grammar.
- **consequences**: `a0a7faf` — `src/rme7.{h,c}`: the user-facing root generates `port`, which generates one proto per primitive; `port` hosts `admitted`/`refused`/`absent`/`open`; verdict table as derived above; C and shell tests; `docs/model.md` section and an open question on the G̃♯ port. `prompts/asdg-rme7.md`: §2 records both forms with provenance, §3 gains the offices but stays unpopulated (offices are roles, not types/domains/composition rules, so the generator-equation gate stays down), new §11 (the card) and §12 (the framework handles, pending items marked, guards).
- **criticism, assembled** (not adjudicated): (1) the operator count, above; (2) "block-diagonal offices" as a card condition against "permitted cross-sector relation sits in G̃♯" in Del(U₂) — consistent only if sector ≠ track, which nothing states; (3) Ψ appears in the canonical form and nowhere else; (4) κ inside Σ_ij gives a fail-only indicator a compositional role the local typing does not describe. Each is a question for the register, recorded here so it is not re-derived from memory later.
- **a sequencing slip, recorded**: the code commit `a0a7faf` landed before this entry, against the G♯ row's letter (the entry precedes the commit). The derivation it encodes was done first; the record lagged by one commit in the same push. Entry 2 has the same shape. Not hidden, not repeated by choice.
- **parked, correctly**: the G̃♯ verdict (`open` until the register rules on sector vs. track); the two `[pending]` items; Ψ; ρ_rel.


### 4 — slots, not a classifier

- **from → to**: the operator, in session → this tree.
- **ruling**: "We don't need a classifier. We only need slots." The hosted verdict vocabulary from entry 3 (`admitted`/`refused`/`absent`/`open`) and an office table with executable constraints drafted after it are withdrawn; the seven primitives are bare protos filled by teaching (`prompts/parameterize-rme7.md`).
- **status**: `re-derived` — the deletion test agrees: a slot's content is what is taught into it, and teaching already exists. The verdict enumeration remains valid as this entry's predecessor's record; it was machinery that duplicated a ruling the register owns.
- **consequences**: the commit carrying this entry.

### 5 — a sibling relay reads the handoff: two claims withdrawn, one contradiction found, ε/Φ parked

- **from → to**: a sibling tree's relay (the unicore / `tri-modal-release`
  lineage of entry 1) → `mrosst108-collab/moop @ claude/rme-7-multitrack-ports-990dt4`,
  relayed by hand as text through the operator. Occasion: `docs/handoff.md`
  at `00eb5e4` was read abroad and criticized.
- **ground (sender-side, unverifiable here)**: the sender again cites its
  own commit `6f85579`, with the same gloss as entry 1 ("testimony, never
  law" — there, Φ crosses as testimony). The anchor is unchanged and still
  does not resolve in this tree, so κ > 0 exactly as before and nothing
  below binds by arrival. Local ground: `docs/handoff.md` at `00eb5e4`,
  amended in the commit carrying this entry.
- **an unentered predecessor, recorded**: the assessment being corrected
  ("[B]") reached this tree in an earlier exchange that was never entered
  in this ledger. It is entered here, with its correction, rather than
  left implicit — the F row says corrections cite the entry they correct,
  and this one has to cite its own absence. The prior claims, now
  withdrawn by their author:
  - "θ is a ChatGPT invention wearing Greek" — **withdrawn by the sender**.
    Against this tree: θ is the generator of the X/θ split, F is
    generator-level self-modification θ ↦ θ′, `reddit/src/rme7.h` holds
    the split in one struct, and the whole of `attribution/` is built on
    the distinction. Local status: the withdrawal agrees with what is
    already `re-derived` here (five frozen predictions, `reddit/README.md`);
    nothing changes.
  - "ε missing → a two-modal system with three-modal branding" —
    **withdrawn by the sender as corpus-relative**. ε is not among the
    seven offices this tree holds; admit-ε / reject-κ / trace-γ is the
    *sender's* local realization vocabulary, applied to RME-7 proper as
    if it were canonical. Local status: no claim on this tree either way.
- **claims arriving, by status**:
  - The office semantics this tree carries match the sender's corpus where
    it can check them: G̃♯ confinement-without-convergence as *a verdict,
    not a map*; Σ as stochastic driving (their MAYBE~→Σ commitment); κ with
    the two sites κ_F and κ_Σ. — `testimony`. It is agreement about a
    corpus that cannot be fetched here; it corroborates, it does not bind,
    and nothing in this tree moves on it. Recorded because independent
    agreement on three offices is exactly the evidence that would matter
    if §3 ever comes up for population.
  - This ledger's graded form (append-only; testimony / grounded /
    re-derived / refuted / parked) is the institutional shape of the
    sender's own "Φ crosses as testimony, never as law". — `testimony`,
    an observation about convergence between two boundaries. No consequence.
  - The sender's self-report that it "demonstrated the failure mode the
    handoff warns about, from the other side" — reconstructing office
    semantics from its own corpus instead of retrieving this tree's.
    Recorded as the fourth instance; rule 2 of the handoff (`retrieve,
    never reconstruct`) is now earned from both directions.
- **finding, accepted and repaired**: the handoff said moop generates
  "seven RME-7 slot protos" including `gamma` (§1) while stating that γ is
  "derived, never a slot" (§4 rule 2), with the reddit correctly keeping γ
  off its six pointers (§2). A fresh session following rule 2 would hit the
  contradiction in its first ten minutes. Resolved in place, not smoothed:
  a moop slot is a *name* hosting nothing, and γ's name exists so the
  derivation can be taught into it — `examples/rme7.moop` teaches
  `gamma ask derive` as `gtildesharp ask confine` composed with
  `gsharp ask converge`, which is γ = [G♯, G̃♯] as a composition of two
  offices, not an occupant of an office of its own. Seven names, six
  offices. `docs/handoff.md` amended in the commit carrying this entry,
  with the amendment marked and `00eb5e4` named.
- **the open cross-corpus question — `parked`, for the ratifying authority**:
  ε and Φ are load-bearing in the sender's corpus (ε-accounting, three-modal
  closure, Φ-crossing) and absent from the spec this tree holds
  (`prompts/asdg-rme7.md`, seven offices, no ε). Either the two trees hold
  different strata of RME-7 — plausible on the face of it, since §3
  (operator semantics) is explicitly `[unpopulated]` here, awaiting a
  primary source — or one relay has a gap. Neither the sender nor this
  session may resolve it: adjudication is Mark Rosst's, and neither corpus
  can fetch the other's. Parked here as testimony, which is what this
  document exists to do with exactly this kind of claim. Note for whoever
  rules: Φ *does* appear in the card carried at entry 3 (`G̃♯_i(dΦ_i)` in
  the per-track equation, and the `[pending]` flux/veil/witness lexicon),
  so the absence is of ε and of any populated semantics for Φ, not of the
  symbol Φ itself. Checked locally against `prompts/asdg-rme7.md`: Φ occurs
  in both written forms of the generator equation and in the card, and §3
  lists it among the terms for which "no definitions available" — ε occurs
  nowhere in the file.
- **consequences**: the handoff amendment above. No code, no spec change,
  no promotion. `prompts/asdg-rme7.md` is untouched: nothing here arrived
  with ground that would let it become `[carried]`, and `[relayed]` text
  is not edited on the strength of a reading from abroad.
