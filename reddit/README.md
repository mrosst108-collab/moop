# reddit

A reddit in C23, shaped by RME-7 (`../prompts/asdg-rme7.md`). No network,
no persistence: a library (`src/reddit.c`, `src/rme7.h`), a terminal
front end (`src/main.c`) with a virtual clock so runs replay exactly, and
tests.

```sh
make && make test
printf 'sub cats 1\npost cats 1 hello\nshow cats\nquit\n' | build/reddit
```

## The shape

A subreddit is a **track**: state `X` (posts) and generator `θ` (rules,
ranking, moderators) in one struct, never confused. The seven primitives
are **slots** — function pointers with default occupants — so an office is
invariant and its occupant is swappable. The mapping is role-plus-constraint:
no equation is claimed; each row is a test in `tests/test_reddit.c`.

| slot | office | occupant | constraint tested |
|------|--------|----------|-------------------|
| `jsharp` | conservative circulation | sort by hot | a permutation of `X`, nothing else |
| `gsharp` | dissipative; converges | exponential decay | the only writer of `hot`; moves only toward zero |
| `gtildesharp` | confinement without convergence | the rules | a verdict on a `const` post; a refusal enters nothing |
| `sigma` | stochastic driving | posts and votes arrive | admitted only through the rules |
| `reddit_port` | `Σ_ij` = adapter ∘ gate ∘ translation | crosspost | the only two-track function; refusal leaves the target untouched |
| `f` | generator self-modification | change rules and ranking | passes `kappa` first; never touches `X`; out-of-range refused whole |
| `kappa` | integrity gate | is a moderator | fail-only; `allow_crosspost` is κ at the port |
| `gamma` | derived, `[gsharp, gtildesharp]` | `reddit_gamma` — not a slot | measured from a copy, changes nothing; counts posts whose fate depends on decay running first |

r/all is an aggregate track fed through the port (`all K` in the front
end); see the frozen prediction below and its outcome.

**Capture** (`G♯_ij ≠ 0`, one track's objective forming another's ends) is
the failure condition: no slot reads a second track, and the test "no
capture" holds a track's ranking fixed through every act on another.

## Status (audit position)

RME-7 has demonstrated a viable architectural discipline here: its
distinctions are operationally separable, testable, and detected at least
one non-commuting interaction (decay against rules, counted by
`reddit_gamma`). Its present implementation does not establish type-level
enforcement (C23 cannot state `Writer(hot) = gsharp`; the guarantee is slot
contract + tests + occupant discipline), semantic realization of the formal
operators (the spec's §3 is unpopulated; every row is role-plus-constraint),
or framework-level reuse (one consumer, the program the shape was drawn
from).

The first falsification test, r/all, was frozen in advance and has run: the
feature was built with each subreddit exporting through the port `Σ_ij`, no
global read, and the discipline predicts an observable property of it —
r/all is stale until rebuilt, never live. Cross-track relation is carried
on the port, not on γ; γ is derived and measured, never a mediator.
Comments and users next test recursive structure and a second track kind.

Reuse has two grades: a second subsystem of this reddit is intra-domain; an
independent domain on the same six slots without changing the discipline is
what a framework claim waits for. Not claimed.

## Frozen predictions

Written before the feature is built, so the outcome can falsify.

**1. r/all (cross-track aggregation).**

    r/all = Aggregate( Gate(r_1), Gate(r_2), ..., Gate(r_n) )

r/all is itself a track. It is fed only through `reddit_port`: each
subreddit's top posts cross into it under r/all's own rules (κ at the
receiver), with the sender's opt-out living in the translation step (a
sender may decline to translate). Ranking across subreddits then happens
*inside* the aggregate track, on posts it admitted, by its own `jsharp` and
`gsharp`. No function other than `reddit_port` reads two tracks, and the
slot set in `rme7.h` does not change.

Falsified if the feature requires

    r/all = GlobalSort( r_1 ∪ r_2 ∪ ... ∪ r_n )

— any function that reads a second track's posts or scores, a new slot, or a
second two-track function. Either outcome is recorded here.

**Outcome: held.** r/all is a `Track` founded by the site, rebuilt by the
driver (`all K` in `main.c`) from each subreddit's top K through
`reddit_port` with the `REDDIT_CARRY` translation, then decayed and sorted
by its own slots. What changed to make it work, all realization data:
`Rules` gained `export_to_all` (θ), and the port gained a translation mode
(fresh crosspost vs. carried votes). What did not change: the slot set
(six function pointers; γ was never a slot, it is measured), and the count
of two-track functions (one, checked statically by the shell tests). The
opt-out landed where predicted, in the translation step. The receiver's
gate is r/all's own `min_hot`. A feeder changed after a build does not
change r/all until the next build: no live cross-track read exists.

One correction to the prediction's wording: it said "seven slots"; the
struct has six. The seventh primitive was measured from the start.

**2. comments** — a hierarchical track structure, without a new slot.
**3. users** — a second track kind carrying identity, without a new slot.

The framework claim is earned only when an independent consumer uses the
same seven slots without the discipline changing:

    one implementation → second implementation → independent consumer → framework
