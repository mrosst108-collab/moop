# Reddit placement into RME-7 — **role-plus-constraint level**

**Level declared, per `prompts/asdg-rme7.md` §5:** this is **role-plus-constraint**
correspondence. Operations are matched to operator offices and the carried
constraints are named. **Generator-equation correspondence is NOT claimed and
is not attempted** — §3 (operator semantics) is `[unpopulated]`, and §2's gate
states that while it is, the canonical form "may be read and cited; it may not
be asserted as satisfied."

**This is not called an ASDG formulation.** §4 — the grammar, its primitives,
its well-formedness conditions, and the relation by which RME-7 is a format
within it — is `[unpopulated]`. Naming this an ASDG artifact would claim
conformance to a grammar this repository does not hold.

**Source:** `reddit-archive/reddit @ 753b1740`, extracted in `mechanism.py`.
**Stencils:** `rme7py/rme7/stencil.py`, both forms, neither privileged (§2.1).

Each blank is asked four questions. A blank with no warranted occupant is left
**INACTIVE**, which is a legitimate answer and not a gap to be filled.

---

## S_C1 — five blanks

### `c1` — drift of X, operand `dH`, conservative office
- **occupant:** none.
- **why:** no circulating, non-converging transport was found in the archive.
  Every `_incr` site is monotone in one direction per event; nothing restores
  what another removes.
- **warrant:** —
- **status: INACTIVE.** Not a defect. The reconstruction is not required to
  exhibit a conservative office.

### `c2` — drift of X, operand `dH`, dissipative office
- **occupant:** attention decay on `thing.attention`.
- **why:** the office is convergent descent — a term that reduces a quantity
  monotonically absent input. Decay of a post's visibility is that office.
- **warrant:** **none from the archive.** This occupant is `CONSTRUCTED`
  (`mechanism.py:STATE`), added by the architectural ruling that moved time
  from observation into state. The archive has `dX/dt = 0` between events and
  puts all time dependence in `hot` (`_sorts.pyx:46-56`).
- **carried constraint:** the quantity is non-increasing between events.
- **status: PLACED, on a constructed occupant.** The distinction matters: this
  blank is filled by the reconstruction, not by the source.

### `c3` — drift of X, operand `dΦ`, confinement office
- **occupant:** none placed. **Candidate:** subreddit rules and moderation —
  they confine where a post may go without dissipating it.
- **why not placed:** the office requires confinement *without* convergence,
  and the archive implements moderation as discrete removal (`_spam`,
  `_deleted`), which is a state jump, not a confining term. The candidate is
  named so it is not lost, and refused so it is not asserted.
- **status: INACTIVE, candidate recorded.**

### `c4` — diffusion of X, diagonal, intrinsic noise
- **occupant:** none.
- **why:** no intrinsic stochasticity exists in the archive
  (`mechanism.ABSENT_FROM_ARCHIVE`). The only nondeterminism is scheduling —
  async queues, the grace period, lock contention, `% 10` sharding — which is
  infrastructure, not model.
- **the temptation, refused:** vote arrival is the nearest available occupant.
  Placing it here is **LOSSY**: `∘ dW` is an anonymous increment and the
  archive's event is identified, with the identity *consumed* by the mechanism
  (previous-vote lookup on `(actor, target)`, self-vote detection, karma routed
  to the target's author).
- **status: INACTIVE.**

### `c5` — diffusion of X, off-diagonal, coupling
- **occupant:** the channel family — one admitted event routed to author,
  subreddit and domain through one gate (`voting.py:171-174`).
- **why partial:** the routing half of `Σ_ij(X_j → X_i)` fits. Two things do
  not, and they are independent losses:
  1. **driving-process identity** — as `c4` above.
  2. **fan-out cardinality** — `Σ_ij` names one destination; the mechanism
     addresses three through a shared gate.
- **status: LOSSY.** Recorded as a placement that discards warranted
  distinctions, not as a placement made.

---

## S_v5 — seven blanks

`v1`, `v2`, `v3`, `v4` take the same verdicts as `c1`, `c2`, `c3`, `c4`.
S_v5 writes no index, so the channel family has **no blank at all** here
(`NO_BLANK` rather than `LOSSY`) — the coupling is unwritable in this form.

### `v5` — drift of X, no operand
- **occupant:** none.
- **why:** this is S_v5's `F`-in-the-state-equation position, which S_C1 does
  not write and which both implementations refuse (entry 27). Filling it would
  take a side in G_prov.
- **status: INACTIVE, contested.** Left empty because the position itself is
  disputed, not because no occupant exists.

### `v6` — dθ gate, admissibility
- **occupant:** `κ_change` (`vote.py:190-300`).
- **why:** the office is a verdict that admits or refuses a proposed change.
  `VoteEffects` is exactly that — boolean, never a scalar, carrying refusal
  reasons (`AUTOMATIC_INITIAL_VOTE`, `KARMALESS_THING`, `COMMENT_STICKIED`).
- **carried constraints:** the verdict is a verdict, not a score; it is
  **path-dependent**, consulting the *stored* verdict of the prior event.
- **what is lost:** `κ_propagate` (`voting.py:168-175`) has different inputs
  and a different jurisdiction and there is only one gate position. Whether one
  κ may compose two offices is **Q7**, open.
- **status: PLACED, with a named loss.**

### `v7` — dθ drift, generator evolution
- **occupant:** the swappable vote validator, injected via
  `hooks.get_hook("vote.get_validator")` (`vote.py:207-208`).
- **why:** the office is what evolves the generator. The archive's gate is
  replaceable at runtime, so what changes is the rule rather than the state.
- **carried constraint:** the change is to the gate, never to the state
  directly.
- **status: CANDIDATE.** The hook is a configuration seam, and whether a
  configuration seam is generator evolution or merely deployment is not
  decided here.

---

## Summary

| | S_v5 | S_C1 |
|---|---|---|
| placed on an **extracted** occupant | 1 (`v6`) | 0 |
| placed on a **constructed** occupant | 1 (`v2`) | 1 (`c2`) |
| lossy | 0 | 1 (`c5`) |
| candidate, not placed | 2 (`v3`, `v7`) | 1 (`c3`) |
| inactive | 3 | 2 |

**The standing result of entry 43 survives the blank-by-blank pass:** the drift
group is filled by the occupant the ruling constructed, and of everything
*extracted* from the archive exactly one element — the state-change gate —
takes a blank cleanly, in one form only.

**What generator-equation level would require and this does not have:** what
`H` and `Φ` *are* for Reddit, which one-form each operator consumes, and
whether the equations are satisfied. All three wait on §3.
