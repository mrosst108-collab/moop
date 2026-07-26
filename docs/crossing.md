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
