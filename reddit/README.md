# reddit

A reddit in C23, shaped by RME-7 (`../prompts/asdg-rme7.md`). No network
of its own and no storage but its transcript: a library (`src/reddit.c`,
`src/rme7.h`), a terminal front end (`src/main.c`) with a virtual clock so
runs replay exactly, a live service over a Unix socket, and tests. AI
answers come from an external answerer the operator configures
(`answerers/claude.py` is the reference one).

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
request science 3 1                 user 3 asks the AI to answer node 1, once
answer science 1 It was in 2015.    the AI's answer (live, only the server writes it)
ai science 1 0                      the moderator turns AI answers off in r/science
help                                the command list
quit
```

Everything refused says why on stderr (`refused: ...`). Limits are fixed
and stated when hit: 16 subreddits, 16 profiles, 64 nodes per track, 4
moderators, 95 bytes of a human's text, 300 characters of an AI answer.

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

Product work since, each frozen before it was built (predictions 4 and 5):

    delegation (subscriptions as theta_u)          held
    PageRank as port message passing               held
    rank-weighted article ranking                  held
    anonymous historical vote                      preserved
    attributed cast                                held
    weigh as an explicit rebuild, stale until run  held
    no text analysis                               held
    no feedback from voting into rank              held
    port abstraction                               not earned
    Build A (in-process consumer)                  not earned
    Build C (port contract)                        evidence collected, no boundary

Deployment: equivalence is demonstrated and provider-independent — the
binary reproduces the eight committed Phase 3 corner observations byte for
byte, now a shell check, and any host that builds and passes the suite has
the same reference realization. Public exposure is blocked by three
product freezes, not by infrastructure: identity (what κ trusts, today an
asserted number), concurrency (one authoritative transcript order with
many writers, a semantic decision), and live time (when the wall clock
writes `tick` into the transcript). HTTP is downstream of those three.
Provider selection is deferred until they are ruled.

The one port function carries four translations for five uses — crosspost;
carried, for r/all and profiles; rank; weight — and only rank leaves its
node and user parameters unused. The measured result points toward the
existing function being the contract. It is not abstracted on the strength
of a count; a sixth translation, an independent consumer, or a real
substitution or testing need can change that.

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

**Outcome: held.** `follow`/`unfollow` change `Rules.subs` on the user's
own track through `f` under `kappa` (another user is refused; a
self-loop is an ordinary edge). `pagerank` sets `alpha`, `tolerance`,
`rounds` in `Ranking` on the site track through `f`, refused for anyone
but the site and for values out of range; `rules` preserves them. Rank is
a third translation of `reddit_port`, `REDDIT_RANK`: the sender's `share`
is summed into the receiver's `incoming`, no receiver gate. `rank` in the
driver runs the rounds as `all K` runs its loop: one track at a time sets
its share (rank over its subscription count, or rank over N when it has
none, spread uniformly) and ports it; then each track settles from its
own `incoming` alone, damped, plus the teleport share. Stops at the
tolerance or the round limit and says which.

Acceptance: on the frozen four-user graph the distributed result equals
an independent PageRank reference, written separately in awk inside the
test script, to four decimals; ranks sum to one; the static checks still
find one two-track function and six slots. Behavior as predicted: a
subscription change moves no rank until the next `rank`; with the round
limit at one, a two-hop effect is absent and appears at two.

Pressure observed, recorded as evidence and not acted on: carrying rank
through the one port function leaves three of its parameters unused
(`id`, `user`, `now`) and puts the sender's per-edge export in a field
the driver sets (`share`). That is the fourth material through the same
signature — crosspost, aggregate, profile, rank — and it is the first
concrete data on what a port contract would have to hold in common. It
is the trigger the relay called Build C; measuring it comes before
drawing it.

**5. rank-weighted article ranking.**

Two voting signals per node: the popular vote V (direct votes) and the
rank-weighted vote W (attributed votes, each weighted by the voter's proxy
rank). Ruled before any code:

1. `vote` stays anonymous and counts in V only. `cast SUB USER ID DELTA` is
   an attributed vote: it counts in V and records a ballot (voter, delta)
   on the node. One ballot per voter per node. Existing transcripts stay
   valid.
2. W arrives through the port. `weigh SUB` rebuilds every node's W from
   the voters' *current* ranks: for each ballot, the voter's track exports
   its rank and the port adds it, signed by the ballot, to that node. No
   subreddit reads a user track. W is stale until the next `weigh`.
3. Normalize before combining: V̂ = V/N and Ŵ = W, N the number of user
   tracks. Realized in vote units, which is the same ordering: the port
   carries rank × N ("user-equivalents", an average user's authority is
   one vote), and S = λ·V + (1−λ)·W in those units, decayed by the
   track's half-life like V. λ = 1 reproduces today's ordering exactly.
4. Both are exposed: `show` prints W on a node that has ballots and S
   when λ ≠ 1. J♯ sorts on S; one sort, one key.
5. **One-way dependency, frozen:** subscriptions → PageRank → voter
   authority → article ranking, never back. A `cast` changes V and a
   ballot and nothing else: it does not change any rank, does not
   invalidate PageRank, and is not a delegation. `rank` processes
   delegation; `weigh` processes the consequences of the resulting
   authority; neither is triggered implicitly by the other or by voting.

Realization clause: λ is the site's policy. Because J♯ and G♯ read one
track, λ is held in each track's `Ranking` as the site's setting, changed
only by `blend ADMIN SUB LAMBDA` through `f` under `kappa` with the site
as the actor; `rules` preserves it. A moderator cannot set it.

Prediction: rank-weighted ranking is computable with the voter's
authority arriving through the port into the node it weights, W rebuilt
and stale, no read of a user track by a subreddit, no new slot, no second
two-track function; and the port's `id` and `user` parameters, unused by
the rank translation, are used by this one.

Behavioral consequences, observable: with λ = 1 the ordering is today's;
with λ = 0 a node endorsed by one high-authority voter outranks a node
with many anonymous votes; casting a vote leaves every rank unchanged; a
`weigh` after a subscription change uses the old ranks until `rank` runs.

Falsified if a subreddit must read a voter's rank directly, if a new slot
appears, or if a second two-track function is needed.

**Outcome: held.** `cast` adds the delta to V and records a ballot, one
per voter per node, and touches nothing else. `weigh SUB` zeroes W in
the receiver, then for each ballot the voter's track exports its authority
in vote units (rank × N) and the port, under the fourth translation
`REDDIT_WEIGHT`, finds node `id` in the receiver, finds `user`'s ballot on
it, and adds share × delta; a voter with no ballot there is refused, and
a voter with no track contributes nothing. `gsharp` decays W into `heat`
beside `hot`; `jsharp` sorts on λ·hot + (1−λ)·heat, one key. `blend` sets
λ through `f`, refused for anyone but the site and outside [0, 1];
`rules` preserves it. `show` prints W and heat on nodes with ballots and
S when λ ≠ 1, so nothing printed today changed.

Observed, as predicted: with λ = 1 the 100-vote node is first; with λ =
0 a node with one ballot from the highest-ranked user outranks it and S
is shown; casting leaves every rank unchanged; a `weigh` after a new
subscription reproduces the old W until `rank` runs, then differs. The
port's `id` and `user` are used by this translation. Static checks: one
two-track function, six slots.

Pressure, updated from prediction 4: of the four materials now carried
by the one port function — crosspost, aggregate, profile, rank, weight —
only rank leaves the node and user parameters unused. The signature fits
the others as written. The evidence for a port contract has moved toward
"the existing signature is the contract" and away from a new one.

**6. anti-puppet (a block condition is not an independence certificate).**

Arrived as testimony (`docs/crossing.md`, entry 7): the outline "Where
the Generator Acts" states

    G♯_GE = G♯_EG = 0   ⇏   ¬Puppet(G, E, T_E)

— the absence of dissipative coupling between a generator side G and an
evaluator side E does not show that G lacks operative capacity over E's
transition space T_E. This reddit's no-capture test *is* the block
condition (capture := G♯_ij ≠ 0; "every act on b leaves a's ranking
identical"), and it held on a tree where such capacity was reproduced
before this prediction was written. The non-implication is re-derived
here by counterexample, not imported. The outline's equations are not
used: §3 is unpopulated and its gate stays down, so this stays at
role-plus-constraint level like every row above.

The partition, declared for this reddit and nothing else:

    G    users (posts, comments, ballots, subscriptions), moderators
         (their tracks' θ), clients of the live ingress
    E    the site's configuration of evaluation — alpha, tolerance,
         rounds, lambda, interval — and its admission data (bans); the
         evidence evaluation produces — ranks, the N they sum to one
         over, W, a profile's X; and the argument κ receives: the actor
    T_E  every write to those

Prediction: every write into T_E is either admitted at the site's
κ-site or produced by a declared evaluation (`rank`, `weigh`, the
aggregation port) from G's recorded acts under a configuration fixed for
that evaluation. No act of a generator-side actor writes T_E, directly or
through its own admission. Closing the channels needs no new slot and no
second two-track function: κ gains one argument (which κ-site holds the
field being changed), and a track's ban field becomes a set.

Concretely, each channel with the failure that forces it, all reproduced
on `d751555`:

1. **κ-site per field, level before sector.** `f` names the holder of
   every field it changes — the track (max_title, min_hot, half_life,
   allow_crosspost, export_to_all, locked, subs) or the site (alpha,
   tolerance, rounds, lambda, interval, bans) — and κ admits a
   track-held change for the track's moderators and the site, a
   site-held change for the site alone. Forced by: `ban 1 99` from the
   moderator of r/cats printed `refused: not the site` and still lifted
   the site's ban there; a moderator's `f` wrote lambda and alpha on
   their own track (the site-only rule for lambda lived in `blend`).
2. **Admission transitions are declared, one at a time.** A ban is added
   to a set and lifted only by `unban`; a subreddit is founded under the
   site's standing bans; κ_Σ gates a ballot as it gates a post — `cast`
   refuses a banned voter, and the weight port refuses their authority.
   Forced by: `ban 0 3` then `ban 0 4` let u3 post again; a subreddit
   founded after `ban 0 3` admitted u3; a banned user's `cast` was
   admitted.
3. **κ's argument is authored by the ingress alone.** The ingress
   collapses every run of whitespace to one space before it binds the
   actor; a field longer than a name is refused whole; one line bound
   governs the ingress and replay, and an over-long line is refused,
   never split. Forced by: a client bound to u2 sent `post cats<TAB>0 7
   x` and the post was authored u0; `sub` with a 24-character name read
   the actor from the name's tail; a 265-character line the ingress
   recorded whole replayed as two commands, the second (`sub tail 7`)
   under an actor nobody bound.
4. **The evidential procedure is declared.** A subscription naming the
   subscriber is refused — a subject does not certify its own
   authority; a ballot is +1 or −1; `weigh` processes every ballot (a
   voter with no track contributes nothing and stops nothing). Forced
   by: `follow 1 1` with three dangling users gave u1 rank 0.690 against
   0.250; `cast news 1 1 1000000` from the lowest-ranked user outweighed
   the highest-ranked user's +1 (W 659929.70 against 1.46); a ballot by
   a track-less voter zeroed every W after it.
5. **The evaluator reference is fixed per evaluation.** `rank` records
   the N its ranks sum to one over, and `weigh` scales by that N until
   the next `rank`. Forced by: a profile created between `rank` and
   `weigh` moved every W (1.46 to 1.82) with no rank changed.
6. **E's records are not writable by name.** `all` is reserved like
   `uN`; `cross` and `vote` address subreddits only, so no one writes
   another user's profile (a profile's X is what its karma is summed
   from). Forced by: `sub all 5` made `show all` show u5's subreddit;
   `cross cats 0 u3 9` put u9's post into u3's profile.

Decisions made here rather than by the code. Self-subscription is
refused, reversing prediction 4's "a self-loop is an ordinary edge",
which recorded itself as open to reversal. `unban` is added because a
ban set without removal would make every ban irreversible by accident,
and a replacing ban was the silent unban this prediction removes. The
ingress normalizes whitespace rather than refusing tabs, so a title sent
over the socket records single spaces; the transcript records exactly
what ran. Not closed, and recorded as open rather than decided here: the
anonymous `vote` (an unadmitted Σ channel over the default ordering,
kept anonymous by prediction 5), ballot capacity per node, and karma
summed under its subject's own θ_u (prediction 3's consumer of θ_u).

Behavioral consequences, observable: every command in the language,
issued by a non-site actor, leaves the site's configuration and every
existing track's admission data byte-identical; a moderator keeps every
track-held power; the PageRank reference and the eight committed corner
observations still reproduce.

Acceptance: at the library, for every field of θ, a moderator's `f`
changing only that field is admitted iff the field is track-held, and
the site's always is; in the shell, a battery issuing every command as
non-site actors leaves every rules line (bans included) and every rank
unchanged, and each forcing failure above, re-run, is refused. Static
checks: six slots, one two-track function.

Falsified if closing a channel needs a new slot, a second two-track
function, a slot reading a second track, or a distinction no reproduced
failure forces; if any channel above survives its re-run; or if the
committed corner observations stop reproducing, which would mean
recorded evidence had been re-produced under a different instrument.

Not claimed: independence. Authority remains a function of G's
subscriptions — PageRank over the follow graph measures recursive
endorsement, not judgment — so ¬Puppet here is structural and necessary,
and an independent evaluation would additionally need an evidential
procedure and matched conditions this reddit does not have.

**Outcome: held.** All six channels are closed, and each forcing failure,
re-run, is refused. Channel 1: `kappa` gained the `Held` argument
(track-held vs site-held), `f` reads the holder off the fields a change
moves, and a moderator's site-held change — a ban, or lambda/alpha — is
refused at the library; the C tests assert it field by field. Channel 2:
`banned` is a set (`reddit_set_ban`/`reddit_is_banned`), a second ban
keeps the first, `unban` lifts one, a subreddit is founded under the
site's standing bans, and `cast` and the weight port refuse a barred
voter. Channel 3: the ingress splits tokens on all whitespace, so the
tabbed line binds the real actor (`post cats 2 7 tabbed`, not u0); a name
over its field is refused; an over-long line replays refused, not split.
Channel 4: a self-subscription is refused at the driver, a ballot is
±1. Channel 5: `weigh` scales by the N of the last `rank`. Channel 6:
`all` is reserved, and `cross`/`vote` reach subreddits only. Acceptance
met: the field-holder battery and a non-site command battery leave every
rules line and rank unchanged; static checks still find six slots and one
two-track function; the eight committed corner observations still
reproduce (the only realization change to `show` is an empty ban set now
reads `banned=none`, and the frozen observations were regenerated for
that one token).

One prediction reversed, as it said it might: self-subscription. At the
library a self-loop is still an ordinary edge (`f` does not parse `uN`);
the *product* refuses it at the driver, where "a user originates nothing
into their own track" already lives. Two findings, neither falsifying.
(i) The library cannot tell a profile from a subreddit (finding 2 of
prediction 3 stands), so the self-edge refusal, the reserved `all`, and
"posts address subreddits only" are all driver rules, not slot rules —
the six slots carry no notion of "self" or "site policy" to consult.
(ii) A ban is now two records: `theta` per track (what `gtildesharp`
reads) and the driver's standing set (what a new track is founded under).
The standing set is the site policy the transcript replays; it is not a
seventh slot and reads nothing across tracks. Parked, unchanged: the
anonymous `vote` as an unadmitted Σ channel, ballot capacity per node,
and karma under theta_u.

**Correction to the outcome above**, which was recorded at 2ba50a5 and is
left as it was written. It over-claimed. Re-running the forcing failures
against the built binary, before freezing prediction 7, found three still
reproducing at 2ba50a5, and neither acceptance battery had been written:

- channel 4: `weigh` stopped at the first ballot whose voter had no track
  (a `return` where "contributes nothing and stops nothing" was frozen),
  so every W after it stayed zero;
- channel 5: `weigh` still scaled by the current count of user tracks,
  not by the N of the last `rank`, so a profile created between them moved
  W (1.42 to 1.90 on the re-run) with no rank changed;
- channel 6: `cross` and `vote` still reached profiles: `cross cats 0 u3
  9` put u9's post into u3's profile, and `vote u3 0 50` raised the votes
  u3's karma is summed from;
- "the field-holder battery and a non-site command battery" did not exist.

All four are closed at the commit carrying this paragraph. `weigh` skips a
voter with no track and continues. `rank` records its N, and `weigh`
scales by that N. `cross` and `vote` address subreddits only. The C
battery changes each of the thirteen fields of θ alone (seven track-held,
six site-held), and a shell check holds its field list equal to `Rules`
and `Ranking`. The shell battery issues every actor-bearing command as
non-site actors (a moderator on their own track, strangers, a banned
user) and compares the site's parameters, every ban set, every rank, every
subreddit's W, and the X of the profiles it does not rebuild. Every
forcing failure now has an exact re-run as a check. Each new check fails
against 2ba50a5's binary and passes here.

Writing the battery found a seventh channel, one the prediction did not
list. The crosspost translation copied the sender node's ballots and W,
so a user's `cross` wrote W into a track where no `weigh` had run, and
later `weigh`s there counted ballots nobody had cast there. It is closed
in the translation: a fresh crosspost starts over with one vote, no
ballots and no W. That needed no slot and no second two-track function.
So "no act of a generator-side actor writes T_E" was false when the
outcome was first recorded, for this channel and for channels 4 to 6. It
holds from this commit, and it rests on the batteries rather than on the
list of channels.

The process fault, kept on the record: the outcome was written from the
list of intended fixes, not from re-running each forcing failure against
the binary. The checks that would have caught it were the ones the
outcome said already existed.

**7. requested AI answers (an author that holds nothing).**

Ruled by the operator. Any human may request an AI answer to any
human-written post or comment, their own or someone else's. The AI then
answers once, automatically. It never answers the AI. After it has
answered, it speaks again in that thread only where a human has replied
and a human asks. An answer is at most 300 characters. Recommended and
accepted with those rulings: a moderator may turn answers off in their
subreddit (on by default), and an answer is written from the thread path
(the post down to the node answered) and from nothing else. Read here as:
each human-written node is answered at most once, and a node the AI wrote
is never answered.

Derived before any code. The AI is neither a slot nor a user. It is an
**author that holds nothing**: a reserved identity, `REDDIT_AI`, beside
`REDDIT_SITE`, with no track, no rank, no ballot, no moderation and no
principal. What it writes is a node of X, so every slot acts on an answer
as on any comment. `jsharp` orders it among siblings, `gsharp` decays it,
`gtildesharp` admits it, votes and ballots reach it, and a human may reply
to it. Prediction:

    an answer is Σ under the one verdict: requested as an attributed
    arrival on a node, entering X only through the answer path, gated by
    the same gtildesharp. No new slot, no second two-track function, no
    slot reading a second track, no state above the node.

Concretely:

1. **Request, then answer, both Σ.** `request SUB USER ID` is an
   attributed arrival on node ID, like a ballot. It marks the node pending
   and records who asked. It is admitted only if the requester is not the
   AI and not barred there, the node is unrequested, and the answer it asks
   for would be admitted now. That last test is `gtildesharp` run on a
   probe answer, so a request has no rules of its own. `answer SUB ID TEXT`
   is the only path by which an AI-authored node enters X, and it resolves
   the request. Either the node is answered, which is terminal ("one
   comment only"), or TEXT is empty or refused and the node is unrequested
   again, so a human may ask again. `post`, `comment`, `cross` and the port
   never produce an AI-authored node.
2. **Admission stays one verdict.** `gtildesharp` gains the AI's standing
   rules. An AI node has a parent that is present, not locked, and not
   written by the AI, so the AI never answers the AI. Its subreddit allows
   answers and has not barred the AI (the site's ban set can hold
   `REDDIT_AI` like any user). Its text is at most 300 characters (UTF-8
   code points), where a human's is at most `max_title` bytes. `min_hot`
   and the other rules apply unchanged, and `reddit_sweep` applies these
   rules to existing answers as it applies a lock to existing comments.
3. **The switch is θ.** `allow_ai` is one track-held field of `Rules`, set
   by `ai SUB USER 0|1` through `f` under `kappa`, and `rules` preserves
   it. The field-holder battery gains its row. The rules line prints
   `ai=off` only when the switch is off, so nothing printed today changes.
4. **Nothing of the AI crosses tracks.** The port refuses an AI node under
   every translation, and a crossposted or carried node arrives
   unrequested. The AI has no profile, so it has no karma and no rank:
   `sub`, `profile`, `follow` and `unfollow` refuse it. κ never admits it,
   because it moderates nothing and is not the site.
5. **Answering automatically belongs to the live service, as ticking
   does.** `reddit serve` runs one answerer per pending request. The
   answerer is an executable the operator configures (`REDDIT_ANSWERER`);
   it reads the thread path on stdin and writes one line. The server
   records the result as an ordinary `answer` line in the one serialized
   order: the text, or an empty answer if the answerer failed, timed out
   (`REDDIT_ANSWER_TIMEOUT`), or wrote more than a line can record. The
   executor, not the server, applies the 300-character rule, so an
   over-long answer is recorded and refused, never truncated. A client
   cannot send `answer`, just as it cannot send `tick`, and no principal
   binds to the AI. A server with no answerer refuses `request` at the
   ingress. A request still pending at restart is asked again. Replay reads
   the recorded answers and never consults an answerer, the network or
   wall time. The reference CLI records requests and executes `answer`
   lines but answers nothing by itself; whoever types an `answer` line
   there is trusted, as with the asserted actor number.
6. **The answerer is replaceable.** `answerers/claude.py` is a reference
   occupant that calls Claude through the official Python SDK. The server
   knows only the executable's contract.

Decisions made here rather than by the code. Any human may request,
including the node's author. Requests are limited only by one per node and
by the track's capacity; the moderator's switch, sweep and the site's bans
are the recourse. The empty answer exists so that a failed answer returns
the node to unrequested instead of leaving it pending forever. The human
text cap stays 95 bytes (now named `REDDIT_TITLE`), and a node's text
buffer grows to hold 300 characters of UTF-8.

Behavioral consequences, observable. These requests are refused: one on
an AI node, a second one on a pending or answered node, one by a barred
user, and one where the switch is off or the node is locked. A human's
reply to an answer can itself be answered. `ai SUB U 0` by a
non-moderator is refused. A 301-character answer is refused whole, and its
node is unrequested again. A transcript with requests and answers replays
to the same tree with no answerer present. No AI node reaches r/all or a
profile. The eight committed corner observations still reproduce, and the
prediction 6 batteries still pass with `request`, `answer` and `ai` added
to them.

Falsified if the feature needs a new slot, a second two-track function, a
slot reading a second track, or state above the node (a thread-level
generator, a per-thread counter); if an AI-authored node enters X by any
path but `answer`; if replay consults an answerer, the network or wall
time; if an answer over 300 characters is admitted or truncated; or if the
committed corner observations stop reproducing.

Not claimed: anything about what an answer says. Its correctness, safety
and tone belong to the answerer, and the site's recourse is the switch,
votes, sweep and the ban set. Also not claimed: that an unreserved account
is a human. "Human-written" means "not written through `answer`", so a
principal bound to a bot is a bot the rules treat as a human.

**Outcome: held.** The AI is `REDDIT_AI` (`~0u`). `sigma`, `reddit_cast`,
`sub`, `profile`, `follow` and `unfollow` refuse it, a principals-file line
that binds a token to it is refused when the server starts, and κ never
admits it. `reddit_request` and `reddit_answer` are Σ_ii library functions
beside `reddit_vote` and `reddit_cast`, not slots. A request is admitted by
running `gtildesharp` on a probe answer, so the refusals for the AI's own
node, a locked node, the switch being off and the AI being barred all come
from the verdict, not from a second set of rules. The request adds only
its own conditions: who asks, that the node is unrequested, and room in
the track. `admits` gained the AI branch (parent present, not locked, not
the AI's; `allow_ai` on; at most 300 code points) and nothing else
changed in it. `reddit_sweep` applies the branch to existing answers:
with the switch off, a sweep drops the answers, and a human reply under
one falls on the next pass, as under a lock. `allow_ai` got its row in
the field-holder battery; the static check that holds the battery equal to
`Rules` and `Ranking` is what forced the row. `Post` gained `ai` (none,
pending, answered) and `asked_by`, which is state on the node and nothing
above it. The static checks still find six slots and one two-track
function.

The port's refusal of an AI node is load-bearing. The adapter rewrites
`author` to the receiving user, so a carried AI node would have reached
r/all as u0's and passed as human. The driver's loops happened not to send
one (r/all takes posts, a profile takes its user's own nodes), but refusing
at the source makes "nothing the AI wrote crosses" hold in the library.

Sizes. `REDDIT_TITLE` (95 bytes) caps a human's text as `REDDIT_TEXT - 1`
did. `REDDIT_TEXT` is now 1201 bytes (300 four-byte characters), so the
port's prefix check no longer fires on a human title, and the receiver's
`max_title` refuses the titles that check used to refuse. One bound,
`LINE` = 2048 bytes, governs stdin, replay, the ingress and `connect`.

The live service is as frozen:

    REDDIT_ANSWERER=answerers/claude.py build/reddit serve SOCKET PRINCIPALS TRANSCRIPT

At most four answerers run at once. Each one gets the thread path as
stdin, from a temporary file unlinked at once; runs in its own process
group, with SIGPIPE at its default; and has its output read through a
pipe. Control bytes become spaces. A result is recorded only on exit 0 and
only if the line holds it. More output than a line kills the answerer, and
`REDDIT_ANSWER_TIMEOUT` (default 60 s) kills its group. An answerer that is
not executable stops the server at startup. With no answerer configured, a
client's `request` is refused at the ingress, and a request found pending
at startup is resolved with no answer.

The reference answerer, `answerers/claude.py`, uses the official Python
SDK: `claude-opus-5` (`REDDIT_MODEL` overrides it), adaptive thinking at
low effort, and server-side refusal fallbacks (`fallbacks: "default"`,
beta `server-side-fallback-2026-07-01`). A refusal, a truncated response
or an API error exits 1. Over 300 characters, it asks once for a rewrite,
then exits 1; it never cuts. It is tested against a fake Messages API,
including end to end through `reddit serve`. It has not run against the
live API from this tree, which has no key.

Observed, as predicted. These requests were refused: one on the AI's own
node, one on a pending or answered node, one by a barred user, one where
the switch was off or the node locked, and one in a full track. A human's
reply to an answer was answered, with the AI's earlier turn in its thread
path. A 301-character answer was recorded, refused whole, and left its
node unrequested, while 300 two-byte characters were admitted. A failed
answerer and one out of time each recorded no answer. A restart asked
again. A client's `answer` was refused at the ingress and not recorded.
The whole live transcript replayed to the same tree with no answerer
configured. No AI node reached r/all or a profile. The eight committed
corner observations still reproduce, and the prediction 6 batteries pass
with `request`, `answer` and `ai` added to them.

Recorded, not closed. An answerer still running when the server dies
finishes unobserved, and the restart asks again, so one request can cost
two model calls. Requests are limited only by one per node and the
track's capacity, as decided above.

## Frozen decisions for a live service

Three semantic decisions, fixed before any code, presupposing no host,
no HTTP, no database, no storage abstraction, and not Build A. Anything
that serves the reddit to more than one person is downstream of them.

**1. Identity.** The identity supplied to κ is a principal established by
the serving interface, not a number asserted in the command stream. The
interface authenticates a principal and binds it to a user number before
any application command is admitted; the command language does not
establish identity. The reference CLI's asserted number remains valid as
the *pre-authentication* reference mechanism and is never treated as
authentication by a live interface. Clauses: the transcript records the
*bound* number, so replay needs no identity system and never
re-authenticates; κ's occupant (moderators, and the site) is unchanged,
it only receives a number that was bound rather than typed; the site
principal, user 0, is bound the same way from an operator credential
and is never claimable from the command stream.

Constraint carried by the identity freeze: **each user controls exactly
one personal track, their own**, and κ is the only ownership mechanism —
the ingress adds no second one. A bound principal may change their own
track's θ (rules, subscriptions), cannot administer another user's track
by knowing their number (the actor is bound, not claimed), and site
authority is bound from the operator credential only. Cross-track
effects — following, rank, weighing — remain ports, never transferred
authority. A hole found and closed while checking this: a subreddit
could be founded under a personal-track name (`u7`) before that user's
track existed, and the profile lookup then returned it, moderated by
someone else. `uN` names are now reserved to users and a profile is
looked up only among profiles.

**2. Transcript order.** The transcript is one total order of admitted
command attempts, fixed by one serialized ingress. Every externally
submitted command receives its position before it executes; commands
execute atomically in that order; no concurrent execution may produce a
state that this order cannot represent. Thus X_t, θ_t = Replay(transcript
≤ t) holds for the live system exactly as for the reference. Clause: an
attempt the rules refuse is still admitted to the order and recorded, as
`save` records today, so a replay reproduces the refusal; "admitted"
means placed in the order, not accepted by the rules.

**3. Live time.** Wall time never replaces the virtual clock. The service
holds a tick interval as θ of the site track and, at each interval,
appends an ordinary `tick` line to the same serialized stream as every
other command; replay never consults wall time and replays the recorded
ticks. Clause: **downtime is not time** — a restart replays the
transcript and resumes generating ticks from then; no `tick` is
synthesized for the interval the service was down, so decay pauses while
nobody could act, and restart reads no clock.

Together: authenticated actor + serialized order + recorded ticks ⇒
replayable state. When these are built, the code is small: the existing
executor consuming a serialized, authenticated ingress, and a clock that
emits `tick` lines. Nothing more is licensed by these freezes.

**Built, as frozen.** `reddit serve SOCKET PRINCIPALS TRANSCRIPT` replays
the transcript if it exists, then accepts connections on a Unix socket in
one poll loop, so the transcript's order is the order complete lines are
taken there. A connection's first line must be `auth TOKEN`; the token is
looked up in the principals file (`TOKEN USER`), binds the connection to
that user number, and is never written anywhere. Every later line has its
actor field *replaced* by the bound number before it is recorded and
executed — a claimed number is discarded, not refused — and κ's occupant
is unchanged. Refusals by the rules are recorded like any attempt.
`tick`, `save`, `quit` and `auth` from a client are refused at the
ingress and not recorded. Every `interval` seconds of wall time, θ of the
site track set by `clock ADMIN SECONDS`, the server appends an ordinary
`tick INTERVAL` to the same stream. Downtime is not time: a restart
replays and resumes ticking from then. `reddit connect SOCKET TOKEN`
sends stdin and prints the replies. The reference executor is one
function, `execute`, consumed by stdin, file replay and the ingress
alike, and its replay invariant is unchanged (the eight committed corner
observations still reproduce). No HTTP, no database, no storage
interface, no Build A: the ingress is a consumer of the same executor in
the same process, which is what the freeze licensed and no more.

The framework claim is earned only when an independent consumer uses the
same seven slots without the discipline changing:

    one implementation → second implementation → independent consumer → framework
