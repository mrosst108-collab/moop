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
Comments ran and held (d5ee04a → 15f23d0 → 0d983d2, with a process fault
kept on the record). Users is frozen next.

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

**2. comments (recursive structure).**

A comment thread has no generator of its own: it inherits the subreddit's
rules, ranking and moderators. So a thread is not a track. Prediction:

    comments ⊂ X — the state becomes a tree (post → comments → replies)
    and the same six slots act on the tree, per node, unchanged in kind

Concretely: `jsharp` permutes siblings at every depth with one occupant
(it may read depth, it may not be a second slot); `gsharp` is the sole
writer of `hot` for comments too, under the subreddit's one half-life;
`gtildesharp` is a verdict per node, never a tree rewrite; `sigma` is a
comment arriving under a parent; `f` and `kappa` are untouched, and a
thread lock is a change of θ (a rule about one post), not a thread-level
generator; `reddit_gamma` counts over the tree with no new mechanism.
There is no port for comments, because comments do not cross tracks.

Behavioral consequences, observable: a comment obeys the same `min_hot`
as a post, and there is no separate comment-ranking parameter in θ.

Falsified if comments require a θ of their own (a thread-level generator
that is not the subreddit's), a second sort slot for the comment level, a
tree-rewriting G̃♯, or a second two-track function. Either outcome is
recorded here.

**Outcome: held.** Comments are nodes of X with a stable id and a parent;
the tree is carried by ids, so `jsharp`'s one permutation of the flat
array orders siblings at every depth and the driver walks it. `gsharp` is
unchanged and decays comments under the track's one half-life (a comment
halves exactly as a post does). `gtildesharp` stayed a verdict on a
`const` node — a comment additionally needs its parent present and not
locked — and `reddit_sweep` cascades only by repeating that verdict: a
hot reply under a refused comment falls on the next pass. `sigma` gained
a parent argument, the same slot admitting a post (-1) or a comment. A
lock is `Rules.locked`, one field of θ changed through `f` under `kappa`,
so a non-moderator cannot lock and a locked post refuses new comments
while existing ones stay. The port refuses comments. `reddit_gamma`
counts over the tree unchanged.

Falsifiers, checked: no thread-level θ (θ gained one integer, no
comment-ranking parameter — the shell tests grep the field names); no
second sort slot (six pointers, checked statically); no tree-rewriting
G̃♯ (its signature is unchanged and `const`); no second two-track
function (checked statically). The behavioral prediction held: a fresh
comment clears the same `min_hot` as a fresh post, and a stale one falls
to the same sweep.

**3. users (a second track kind).**

Derived, not assumed. A thread was not a track because nothing that
governs it lives outside the subreddit's θ. For a user, the forcing
feature is the profile: what they did, and their karma, across
subreddits. That is a cross-track aggregate — r/all's problem at the
level of one identity — and the discipline allows it exactly one shape:

    profile(u) = Aggregate( Port(r_1 → u), Port(r_2 → u), ... )

So the prediction is that a user **is** a track, of a second kind:
its X is only ever fed through the port (a user originates nothing into
their own track; every node they wrote was admitted by a subreddit's
`sigma` and carries the author as a datum), and karma is a sum inside
X_u after the ports, never a read across subreddits. Its θ_u is the
profile's own rules, changed through `f` under `kappa` where the user is
their own moderator. Nothing a subreddit does reads the user track: a
site-wide ban is `f` applied to each subreddit's θ by an admin, not a
consultation of θ_u. The six slots and the one port suffice.

Behavioral consequences, observable: a profile and its karma are stale
until rebuilt, exactly as r/all is; a ban takes effect at each subreddit
through its θ and leaves already-ported profile content untouched until
the next build.

**The question this is allowed to fail on.** Whether θ_u is a generator
at all. The prediction requires that at least one profile behavior
depends on θ_u — the profile's own admission (its `min_hot`, its
`allow_crosspost` as "what may appear on me", a per-subreddit opt-out
held by the user). If the only sensible occupant of every θ_u field is a
constant that nothing consults, then "what a user may do" was never a
generator, users are identities referenced from tracks' X and θ, and
the profile is r/all again with a filter — a track with no generator,
which the typing does not have. Either result is recorded here.

Falsified if the feature requires: any subreddit slot reading the user
track (a permission or ban check that reaches into θ_u or X_u); a user
originating content into their own X without a subreddit's admission;
a new slot; a second two-track function; or θ_u with no consumer.

The framework claim is earned only when an independent consumer uses the
same seven slots without the discipline changing:

    one implementation → second implementation → independent consumer → framework
