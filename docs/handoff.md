# Handoff: the moop tree and the reddit in C23

For a fresh assistant session picking this work up. Everything below is
retrievable from the repository; read the files named here before
proposing anything, and treat this page as a map, not as the record.

    repository  mrosst108-collab/moop
    branch      claude/rme-7-multitrack-ports-990dt4
    head        c4ec69d
    build       make test                 (interpreter + C and shell tests)
                cd reddit && make test    (the reddit, its own suite)

Both suites are green at the head. The ratifying authority for anything
RME-7 is Mark Rosst (mrosst108); relays and assistants assemble, build,
and criticize; they do not adjudicate or promote.

## 1. What is in the tree

Two independent things share the repository.

**moop** is a small programming language in C23 (`src/`, `docs/`,
`tests/`). Its core is a CCNOT gate on two counter-rotating tape loops;
reversibility and homoiconicity are the load-bearing invariants; there
are two layers (reversible gates on the tapes, irreversible logic on RAM)
with exactly one bridge shape (reversible effect inside, irreversible
observation outside). The object ladder is actor → system root → user
root (`world`) → protos, with *generation* (who made you) and
*inheritance* (whom you defer to) kept strictly apart. Surface syntax:
`is`, `ask` (`->`), `inherits` (`<-`), `mirrors` (`<->`), and the
indefinite article for birth. `CLAUDE.md` is the authoritative summary;
`docs/derivation.md` is the methodology (the deletion test).

At startup moop generates a `port` proto and seven RME-7 slot protos
(`jsharp gsharp gtildesharp sigma f kappa gamma`, `src/rme7.{h,c}`). They
are bare slots: ordinary user-facing protos that host nothing, filled by
teaching from the surface language. `examples/rme7.moop` holds the seven
teachings; `prompts/parameterize-rme7.md` tells a coding assistant how to
fill them (teach, role-plus-constraint; no classifier, no office table —
that was tried and cut back on instruction).

**The reddit** (`reddit/`) is the thing to mention first when describing
this work: a reddit written in C23 on a framework inspired by RME-7's
structure and optimized for modularity. It is independent of the
interpreter (own Makefile, no dependency on `src/`).

## 2. The reddit, precisely

`reddit/README.md` is the full record. The shape:

- A subreddit is a **track**: one struct holding state `X` (a tree of
  nodes carried by ids: posts, comments, votes, ballots) and generator
  `θ` (rules, ranking parameters, moderators), never confused.
- The RME-7 primitives are **slots**: six function pointers on the track
  with default occupants (`jsharp` sort, `gsharp` decay, `gtildesharp`
  the rules as a verdict, `sigma` arrival, `f` change-of-θ, `kappa`
  is-a-moderator). γ is not a slot; `reddit_gamma` measures it from a
  copy as the count of nodes whose fate depends on decay running before
  the rules.
- `reddit_port` is the **only two-track function** (Σ_ij = adapter ∘ gate
  ∘ translation). It carries four translations for five uses: crosspost
  (FRESH), r/all and profiles (CARRY), PageRank message passing (RANK),
  rank-weighted votes (WEIGHT). The shell tests check statically that
  there is one two-track function and six slots.
- **Persistence is the transcript.** The clock is virtual; the command
  stream replays exactly; `save FILE` records, `reddit FILE` replays.
  There is no other storage.
- **Live boundary** (`reddit serve`, `reddit connect`): a Unix socket
  ingress that binds a token to a user number before any command is
  admitted, rewrites the actor field, serializes one transcript order,
  and writes wall time as generated `tick` lines. Downtime is not time.
  Tokens never enter the transcript. Each user owns exactly one personal
  track (`u<digits>` names are reserved).

**"Optimized for modularity" means this and only this:** modularity is an
implementation discipline here, not a claim that the program is seven
RME-7 modules. An office is invariant and its occupant is swappable; a
boundary is drawn only when a second occupant, a substitution, a testing
need, or persistence forces it. The port abstraction, an in-process
consumer library ("Build A"), and a storage boundary were each
considered and **not earned** on the evidence; do not add them in
anticipation of reuse. The mapping to RME-7 is role-plus-constraint: no
equation is claimed, every row is a test.

Frozen predictions, each written before the feature was built, all
recorded with outcome in the README: r/all (held: stale until rebuilt,
never live), comments (held, with a one-sentence revision: the port
refuses a comment only under the crosspost translation), users as a
second track kind (held, θ_u consumed through profile `min_hot`),
delegation as PageRank over ports (held, equals an awk reference to four
decimals), rank-weighted article ranking (held, one-way dependency
subscriptions → rank → weight → score).

Status: the reddit side is **closed**. The independent-domain consumer
(a second domain on the same six slots, unchanged) is what a framework
claim still waits for. Not claimed.

## 3. The attribution experiment (`attribution/`)

A separate, frozen-protocol test of whether the state-versus-parameter
distinction (X vs θ) recovers attribution answers on an executable
baseline. Target: cJSON's git history, read-only. `README.md` there is
the protocol: the question set Q (49 items) is frozen and must never be
altered after a baseline answer is seen.

- Baseline (SOTA reading of diffs): 45/49 (`baseline.md`).
- H2, four counterfactual corners (X_old/new × θ_old/new) plus an
  identity rule: 49/49, ρ_rel ≈ 1.089, which is the ceiling (`h2.md`).
- Phase 3, the same method on the reddit's own transcript
  (`reddit.md`, `reddit-h3.md`, `corners-reddit.sh`): 14/14, γ observed
  at E13, an inert event at E19. Two **method defects are open and
  deliberately unrepaired**: the arrival-facet Q5 degeneracy, and the
  presumption that an F line is a cause. Three adjudication questions
  await a ruling; positions are recorded there.

The committed corner artifacts are also the deployment-equivalence
check: the reddit binary reproduces the eight Phase 3 observations byte
for byte, as a shell test, so any host that builds and passes the suite
is the same reference realization.

## 4. The discipline (what governs the next move)

These rules were stated by the ratifying authority during the work and
are the reason the record looks the way it does. Keep them.

1. **Freeze → build → test → record.** Write the prediction and its
   falsifiers before code. Record the outcome in place, held or
   falsified, with the commit that carries it. Corrections are recorded
   in place with a commit reference, never silently rewritten.
2. **Retrieve, never reconstruct.** The RME-7 spec as this tree holds it
   is `prompts/asdg-rme7.md`, with provenance markers `[carried]`,
   `[relayed]`, `[unpopulated]`, `[ruled]`. A `[ruled]` sentence is
   never promoted to `[carried]`. Its §3 (operator semantics) is
   unpopulated and stays down until a primary source arrives. Relays
   have repeatedly reconstructed office tables wrongly (γ as decay, Σ as
   state, G̃♯ as a map): check every office against the retrieved text.
   The offices: J♯ conservative circulation; G♯ dissipative and the
   only office that converges; G̃♯ confinement without convergence (a
   verdict, not a map); Σ stochastic driving (Σ_ii, Σ_ij port); F
   generator-level self-modification (θ ↦ θ′); κ integrity gate (sites
   κ_F and κ_Σ); γ = [G♯, G̃♯], derived, never a slot or an observable.
3. **Minimalism, ruled:** introduce a distinction only where it carries
   information the problem requires. Unused offices are expected; no
   office is instantiated for completeness. Only the "only if"
   direction is ruled; "iff" is not.
4. **Let the second consumer force the abstraction.** Counts are not
   evidence for a boundary; a substitution, testing, or persistence
   need is.
5. **Cross-repo claims** go in `docs/crossing.md`, append-only, graded
   testimony / grounded / re-derived / refuted / parked. Nothing from a
   sibling project binds unless anchored in a fetchable commit plus a
   content hash and re-derived locally.
6. **Honesty in the implementation:** the REPL and the reddit report
   what they cannot do instead of stubbing it. Never make something look
   functional that is not.
7. Do not expand the RME-7 grammar from the realization card; pending
   items (N(U₂), flux/veil/witness) stay pending.

## 5. Open items, none of them tasks

- The two Phase 3 method defects and the three adjudication questions
  in `attribution/reddit-h3.md`: awaiting rulings.
- An independent-domain consumer for the six-slot kernel: the only thing
  that would earn a framework claim. Nothing in the reddit should be
  reshaped to prepare for it.
- Live-service decisions that are reversible by ruling: "downtime is not
  time"; a delegate cannot refuse being delegated to; whether one export
  flag governing both r/all and profiles is one decision or two.
- Not implemented in moop, and honestly erroring: number↔number
  bijections, running files, reflection, nested definitions in blocks.

## 6. How to get oriented in ten minutes

    cat CLAUDE.md                       the tree's rules
    cat reddit/README.md                the reddit: shape, predictions, freezes
    sed -n 1,80p reddit/src/rme7.h      Track, the slots, the port signature
    cat attribution/README.md           the frozen protocol
    cat prompts/asdg-rme7.md            the spec as held, with provenance marks
    tail -n 60 docs/crossing.md         the latest cross-repo ledger entries
    git log --oneline | head -40        the freeze/build/record rhythm

Work on the named branch only; push with `git push -u origin <branch>`;
open no pull request unless asked.
