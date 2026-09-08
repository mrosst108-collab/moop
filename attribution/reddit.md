# Phase 3: attribution on the reddit's own transcript — frozen before any corner

The cJSON experiment (`README.md`, `h2.md`) established a capability:
attribution recovered by executing X/θ combinations absent from history.
Phase 3 makes the reddit (`../reddit/`) able to run that method on its own
transcript. This file fixes, before any corner is built, what X and θ are
there, what an intervention is, and what an absent field means. Q and the
rubric are reused **verbatim** from `README.md`; nothing here alters them.

Scope, stated: the reddit's history is authored, not independent. This is
a capability demonstration on the reddit's own semantics and intra-domain
by construction. It is not evidence about an independent target.

## The transcript is the record

A session is a file of application commands (`../reddit/README.md`,
"Persistence is the transcript"); `reddit FILE` replays it exactly. Every
line is classified by what it does, and the classification is fixed:

| kind | lines | in a corner |
|---|---|---|
| **Σ** — produce X | `post`, `comment`, `vote`; and the port lines `cross`, `all`, `profile` (they produce X in the receiver from X elsewhere) | included or excluded per corner |
| **F** — set θ | `rules`, `lock`, `ban` | included or excluded per corner |
| **structural** | `sub` — a track comes to exist, with the binary's default θ and its founder as moderator | always kept: every corner needs the same tracks |
| **clock** | `tick` | always kept: time is the trajectory parameter, neither X nor θ |
| **operation** | `show`, `sweep`, `gamma` | always kept: `show` and `sweep` have effects (decay, sort, the verdict applied) that are part of the history; their output is not the observable |

Session control (`save`, `help`, `quit`) is never in a transcript.

*Correction after the freeze (delegation, README prediction 4):* commands
added later are classified by the same rule — `follow`, `unfollow`,
`pagerank` set θ and are **F**; `rank` produces X_u through ports and is
**Σ**. Later still (prediction 5): `cast` is **Σ**, `weigh` produces W
through ports and is **Σ**, `blend` sets θ and is **F**. `corners-reddit.sh` carries the same table. The contract's
definitions are otherwise unchanged.

## X and θ, operationally

**X_Reddit** — per track: the nodes (`posts[]`, `nposts`, `next_id`), i.e.
everything Σ lines produced, as decayed, sorted and swept by the kept
operation lines. Karma is a sum over X_u and is not separate state.

**θ_Reddit** — per track: `Rules` (`max_title`, `min_hot`,
`allow_crosspost`, `export_to_all`, `locked`, `banned`), `Ranking`
(`half_life`), and `mods[]`. Set at `sub` (defaults, founder) and changed
only by F lines through `f` under `kappa`. A refused F line (κ said no)
changes nothing and is still an F line in the record.

## Event, interval, observable

An **event** is one F line at transcript position *n* that was admitted
(κ said yes). Its **interval** runs from *n* to an observation point *m*
chosen so that (n, m] contains no other F line; an interval with two F
lines is two events, not one. The **observable** at *m* is the text of
`show TRACK` for every track the interval's lines name, emitted by a
fresh `show` appended after replay — the probe's analogue. Two corners
are equal on a facet iff those texts agree on it; `gamma TRACK` at *m*
is recorded alongside.

## The four corners

Let H = the transcript up to and including *m*. Each corner is a
transcript derived from H and replayed from the start by the same
binary; nothing is edited by hand inside a line.

    (X_old, θ_old)   H with F_n removed and every Σ line in (n, m] removed
    (X_new, θ_new)   H unchanged
    (X_new, θ_old)   H with F_n removed
    (X_old, θ_new)   H with every Σ line in (n, m] removed

"Old" and "new" refer to the interval only: X before *n* and θ before *n*
are in every corner, since the lines before *n* are never touched.
Structural, clock and operation lines are never removed.

Mapping to Q4–Q6 is `h2.md`'s, unchanged: Q4 yes iff `(X_new, θ_old)`
shows the facet's new value; Q5 yes iff `(X_old, θ_new)` does; Q6 yes iff
the two mixed corners differ on the facet — γ ≠ 0, observed.

## The absent-field case, resolved here and not in code

The cJSON identity rule was needed because a macro could be *absent* from
the older source. In the reddit, θ is a struct in the replaying binary and
has every field on every replay, so "absent" can only mean: the transcript
was recorded by an older binary that had no such field (`locked`,
`banned` were introduced at `15f23d0` and `25b1b80`). Five states are
distinguished and each has one meaning:

| state of a θ field at position *n* | meaning in θ_old |
|---|---|
| historical, explicitly set by an admitted F line before *n* | that value |
| historical, never set since `sub` | the binary's `sub` default |
| absent — the recording binary had no such field | **instantiated at the replaying binary's `sub` default**, and any Q4–Q6 answer that depends on it is marked **(default)** |
| present with default (−1 for `locked`, `banned`) | the mechanism's identity: no lock fires, no ban fires — here this is not an assumption, −1 is literally the value the code uses for "none" |
| explicitly changed by F_n | that is the event |

Omission is not an option: a struct field cannot be omitted. Any other
treatment (a synthetic value, a guess at what an older binary "would have
done") is refused.

## Baseline, for symmetry

The baseline is the transcript's own diff: read the lines in (n, m] and the
`show` at *n* and *m*, and answer Q by inspection, as `baseline.md` did
with git. It constructs no corner. Same rubric; same 49-per-seven-events
shape if seven events are authored, fewer if fewer.

## Preregistered outcomes

Corners recover the Q4–Q6 answers inspection cannot give, in particular
for intervals where an F line and Σ lines interleave under `tick`s so that
the mixed corners are histories that never happened; or they add nothing
because a reddit transcript is short enough to inspect; or an answer rests
on (default) and is scored only if the corner run produced a discriminant.
Separately reported: how many inspection answers the corners confirm.

## What is built when this runs

One script that, given a transcript and a position *n* and *m*, writes the
four derived transcripts and replays each with `reddit FILE` followed by
the `show` lines. No new command, no new storage, no change to the
kernel or the driver. The offices used are the X/θ separation, F, and γ.

## Status

Frozen. No transcript authored for it yet; no corner built.
