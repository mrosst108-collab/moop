# reddit

A reddit in C23, shaped by RME-7 (`../prompts/asdg-rme7.md`). No network,
no persistence: a library (`src/reddit.c`, `src/rme7.h`), a terminal
front end (`src/main.c`) with a virtual clock so runs replay exactly, and
tests.

```sh
make && make test
build/reddit          # then type commands; `help` lists them, `quit` leaves
```

## Using it

Commands are one per line on stdin. A user is a number; the site is user 0
and moderates everything. The clock is virtual, starts at 0, and only
`tick` advances it — so **the command stream is the session's transcript,
and feeding the same stream again reproduces the session exactly.**

```
sub science 1                       user 1 founds r/science and moderates it
post science 1 Water on Mars        a post arrives (node 0) if the rules admit it
comment science 2 0 Source?         a comment under node 0 (node 1)
vote science 0 4                    four upvotes on node 0
tick 3600                           an hour passes; hot halves everywhere
show science                        the rules in force, then the tree by hot
rules science 1 50 0.5 3600 1 1     the moderator sets max_title, min_hot,
                                    half_life, allow_crosspost, export_to_all
lock science 1 0                    no more comments under node 0
sweep science                       drop what the rules no longer admit
sub cats 3                          a second subreddit
cross science 0 cats 3              user 3 crossposts node 0 into r/cats
all 2                               r/all, rebuilt from every subreddit's top 2
profile 1 5                         u1, rebuilt from user 1's nodes everywhere
ban 0 2                             the site bans user 2 from every subreddit
gamma science                       nodes whose fate depends on decay running first
help                                the command list
quit
```

Everything refused says why on stderr (`refused: ...`). Limits are fixed
and stated when hit: 16 subreddits, 16 profiles, 64 nodes per track, 4
moderators, 95 characters of text.

**Persistence is the transcript.** `save FILE` records every application
command to FILE from then on, before it runs; `build/reddit FILE` replays
FILE silently and then reads stdin, which is a restart. Session control
(`save`, `help`, `quit`) is not application history and is never recorded.
There is no other storage: because runs replay exactly, the input history
*is* the state, and any earlier state is the same file cut short.

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
kept on the record). Users ran and held (79ca7bd → the commit carrying
this text), with θ_u consumed and the comments outcome revised in one
sentence. The independent-domain consumer is what remains.

Reuse has two grades: a second subsystem of this reddit is intra-domain; an
independent domain on the same six slots without changing the discipline is
what a framework claim waits for. Not claimed.

The reddit side is closed. It demonstrated cross-track aggregation, recursive
state without a new primitive, a second track kind determined by its feeding
relation rather than by a new primitive, receiver-governed admission, derived
γ, one port serving distinct aggregations, and the six-slot kernel unchanged
throughout. Nothing further is to be added here in anticipation of reuse.

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
while existing ones stay. The port refuses a comment under the crosspost
translation — it would have no parent in another subreddit — but admits
one into an aggregate under the carried translation, flattened and
marked with its origin *(revised at 25b1b80; the original read "the port
refuses comments", which users showed was compressed too far)*.
`reddit_gamma` counts over the tree unchanged.

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

**Outcome: held, with two findings.** A profile is a `Track` named
`uN`, founded by N (so `kappa` makes the user their own moderator),
rebuilt by the driver from every subreddit's nodes by N through
`reddit_port` with the carried translation, ranked by its own slots;
`reddit_karma` sums votes inside X_u after the ports. θ_u got a consumer
without one being invented for it: the profile's own `min_hot` is
consulted by the port's gate, so a user who sets it hides their cold
nodes and lowers their own karma; another user's attempt to set it is
refused by `kappa`. A profile is stale until rebuilt. A ban is
`Rules.banned`, one field of each subreddit's θ, set through `f` by the
site (`kappa` admits `REDDIT_SITE` everywhere); it refuses the banned
user's new arrivals, leaves already-ported profile content alone, and
`reddit_sweep` applies it to what they already wrote. No subreddit slot
reads a user track; six slots; one two-track function (both checked
statically).

Finding 1, a revision of the comments outcome. It said "the port
refuses comments". A profile shows what a user said, comments included,
so the *aggregation* translation now carries a comment flattened — it
arrives as a top-level node marked with its origin — while the
*crosspost* translation still refuses one (it would have no parent).
Comments still do not cross between subreddits; they do cross into
aggregates. The second consumer forced the port's translation to say
which, and the comments falsifiers are all still intact.

Finding 2. The library cannot tell a profile from a subreddit: the
second kind differs only in how it is fed. "A user originates nothing
into their own track" is enforced by the driver (posts and comments
address subreddits only), not by a slot — there is nothing in θ or X
that a slot could consult to refuse it. And one export flag,
`export_to_all`, governs both aggregates: a subreddit that opts out of
r/all is absent from its authors' profiles too. Whether that is one
decision or two is a θ design question, left open.

**4. delegation (transitive proxy rank).**

A subscription u → v means u authorizes v to carry u's ranking influence,
transitively. Rank is PageRank over the subscription graph, with no
content analysis of any kind. Prediction:

    rank is computable with each user track exporting its rank through
    the port and summing what arrives — power iteration as message
    passing — with no global read of independent tracks' contents, no
    new slot, and no second two-track function

Concretely: a subscription is a field of θ_u, changed only through `f`
under `kappa` with the user as their own moderator (so following is an F
act, not a Σ act). Rank is a new material the port carries, a fourth
translation of `reddit_port`; the receiver sums what arrives, applies
damping and the teleport share itself, and the driver runs the rounds
exactly as it runs `all K`. α, the tolerance and the round limit are θ of
the site track (`all`), set through `f` by the site. The iteration
converges, which is G♯'s office; nothing is added for it.

Decisions made here rather than by the code: self-subscription is
permitted (a self-loop is an ordinary edge; nothing is added to refuse
it). A delegate cannot refuse being delegated to — rank has no
receiver-side gate — because a subscription is the subscriber's act on
their own θ; recorded as a political choice, open to reversal by a later
ruling. A user with no subscriptions (dangling) spreads their rank
uniformly, through ports, as standard PageRank does. Rank is state (X_u),
produced only by ports, and never touches a subreddit's ordering in this
step: content ranking by author rank is a separate later prediction.

Behavioral consequences, observable: rank is stale between runs of the
iteration; a subscription change propagates only through subsequent
rounds, one hop per round; with the round limit at one, a two-hop effect
does not appear.

Acceptance: for a small frozen graph, the distributed result equals an
independently computed PageRank reference to four decimals; the static
checks still find one two-track function and six slots.

Falsified if a correct rank requires a matrix or any read of a second
track's contents outside the port; if a new slot appears; or if the
port cannot carry rank without a second two-track function.

The framework claim is earned only when an independent consumer uses the
same seven slots without the discipline changing:

    one implementation → second implementation → independent consumer → framework
