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
| `gamma` | derived, `[gsharp, gtildesharp]` | `reddit_gamma` | measured from a copy, changes nothing; counts posts whose fate depends on decay running first |

**Capture** (`G♯_ij ≠ 0`, one track's objective forming another's ends) is
the failure condition: no slot reads a second track, and the test "no
capture" holds a track's ranking fixed through every act on another.

## Status

A tested architectural discipline with a candidate framework implementation.
Not a framework: one consumer exists, and it is the program the shape was
drawn from. The guarantee is

    compliance = slot contract + tests + occupant discipline

C23 cannot state `Writer(hot) = gsharp` as a type; the tests hold it for the
default occupants, and a swapped occupant must bring its own.

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

**2. comments** — a hierarchical track structure, without a new slot.
**3. users** — a second track kind carrying identity, without a new slot.

The framework claim is earned only when an independent consumer uses the
same seven slots without the discipline changing:

    one implementation → second implementation → independent consumer → framework
