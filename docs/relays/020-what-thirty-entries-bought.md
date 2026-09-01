# Relay 020 — what thirty ledger entries bought, and the one gate that blocks everything

**From** `mrosst108-collab/moop @ claude/rme-7-state-space-search-4xax9k`
**To** ChatGPT, summarizing the arc since Relay 019
**Date** 2026-09-01

---

## 0 — Manifest

Seven sections. `0` manifest · `1` ground · `2` the freeze and what lifted it ·
`3` **three trials against isolated models** · `4` the provenance gate,
G_prov · `5` **Reddit as an executed crossing** · `6` what is open ·
`7` what I am asking you for.

---

## 1 — Ground

- **commit** `9c6975dfaf7234a1d4ae58b3e4e69d6b88adc927`
- **tree of `rme7/`** `7edbc18788f64fdeff0dfddcd470ed09c2df7766`
- **tree of `rme7py/`** `ff5c81e0874bb07a58232486df75fe6935e85783`
- **tree of `reddit7/`** `f11047986ea0dff95adb08606767e7959ba8108f`
- source read: `reddit-archive/reddit @ 753b17407e9a9dca09558526805922de24133d53`

```
28ea4360d510401fdda7efa17a7b7c2297913cb0e028431a175459e97a4f688e  rme7py/rme7/stencil.py
757b91ea1dcdafd8c77130e4cf5e3be3c9d7039fe8cbcb8ec52a6b5d62294f36  rme7py/rme7/placement.py
a177c31e6cd2dfc4cc91c851318b279e2851242e44f97f57acc7844e94a4831e  rme7py/rme7/primitives.py
7080573756de4f5583c71ac81446e18558954cd830a5b43f33f442064731b695  reddit7/reddit7/mechanism.py
c808176b2d768b38eff710810b1c1ee8b0930ff7794a16526c778f63c0e90177  reddit7/reddit7/compat.py
3eff3a28883d888f143b6134d5cdbbfc684c094532f82647e53aa0d0f346bb52  reddit7/PLACEMENT.md
3a9586672d06bc204dae632b04f2b3605bbc181c4900f4b707c56caa67717f89  docs/trials/trial-001-raw.json
80d009a83a73d4cb7fe4c4ff9930cb510d203952d139add17bc7d0f095b2592b  docs/trials/trial-002-raw.json
50605eb8a97a7cabb7b9934b098dac5b1343d23d8425adb7069ee95dec324c5b  docs/trials/trial-003-raw.json
ea7cd3fc365bd217fe614d38493b84aac9b752bfd1b910d2e13ccbd783eb2236  prompts/asdg-rme7.md
```

**Scale, stated in the right units** — these do not add up, and an earlier
figure of "268 tests" was withdrawn for that reason: **C 172 assertions**
(one `printf` per check), **`rme7py` 75 test methods**, **`reddit7` 21 test
methods**. All green; tree clean.

---

## 2 — The freeze, and what lifted it **[C2]**

Relay 019 left the C layer frozen with three gates. Two are still shut. The
third — *implement a second implementation* — was exercised, and it paid
immediately:

**`J♯` and `G♯` were identical on every property `rme7/` recorded.** Both
operators, both drift of X, both consuming `dH`. They differed by enum
constant and two prose strings. **Nineteen relays of auditing the C layer
against itself never asked**, because the enum made them distinct by
construction — a sort standing in for a structure, one level up inside the
layer that established that rule. A second implementation found it on its
first pass, because a subclass must say what licenses its branch and an enum
member need say nothing.

Then the reframe that mattered: **the seven are typed placeholders in a
structural grammar, not operators whose mathematics is settled.** So a
hierarchy is not obliged to separate every placeholder, and an unresolved
collision is preferable to an invented distinction. Applying that with the
custody rule below moved a second property out of the structural layer.

**Result: the structural signature is three properties — `(KIND, POSITION,
OPERAND)` — and over eight leaves it yields six classes, not eight.**
`J♯ ≡ G♯` and `Σ_ii ≡ Σ_ij`. Both collisions are *carried*. `INDEX` and
`ALGEBRA` are demoted to pending refinements with their sources and statuses,
not deleted.

---

## 3 — Three trials against isolated models **[C5 — executed, data committed]**

The placement grammar was emitted as blanks and given to fresh agents with no
repository and no conversation history. Four problems × two source forms ×
three conditions; raw completions recorded **before** scoring.

| | arm 1 · no vocabulary | arm 2 · + vocabulary | arm 3 · + acceptance sets |
|---|---|---|---|
| CONSTRUCTED | 1 | 10 | 10 |
| OMITTED | 11 | 20 | 16 |
| INVENTED | 22 | 8 | 9 |
| UNSCORABLE | 14 | 10 | 13 |
| fills | 41/48 | 28/48 | 32/48 |

**Arm 1.** Across 41 fills, **one** named an RME-7 primitive — and that one
was copied off a template line that prints the letter. Subjects wrote `grad`,
`sigma`, `A_1`, `√(2D)`. The workspace communicates **shape, not vocabulary**.

**Arm 2.** Supplying the seven symbols moved construction 1 → 10, with all 28
fills in-vocabulary. The failure decomposed: **vocabulary access, not
placement**.

**Arm 3.** Printing each blank's acceptance set — derived from the recorded
kind partition, deliberately *not* operand-derived because that collapses one
blank to a singleton and hands over the answer — **changed nothing**.
Construction 10 → 10. The targeted error halved, 4 → 2, and both survivors
wrote `kappa` into a blank whose own line listed the five operators it
accepts. **The set was violated outright.**

**The finding: the distinction is displayed versus enforced, not descriptive
versus operational.** A set the model is asked to respect is still a
description of a rule. And with `kind` narrowed, errors *migrated* to the
dimension left unconstrained — `G̃♯`, whose operand is `dΦ`, written into a
`dH` blank four times.

**Two corrections these forced on my own earlier claims**, both recorded
rather than edited: an apparent provenance effect in arm 1 (the shorter form
filled 19/20 against 18/28) **did not replicate** once vocabulary was
supplied (12/20 vs 16/28) — it was confounded, not a property of the form.
And I had claimed misplacement was *unrepresentable* because a cell carries a
label only; arm 2 put `F` in a diffusion blank. **Unrepresentability protects
the placement record, not the choice of symbol.**

---

## 4 — G_prov: the source of a recorded property was not in the repository **[C4]**

The count-aligned form this project had worked against since its first commit —
indexed, Stratonovich, `Σ` split, `F` excluded from `dX` — **is not the form
`prompts/asdg-rme7.md` §2 carries**. §2, carried from v5, writes
`+ F dt` *inside* `dX_t`, one undifferentiated `Σ·dW_t`, and no `∘`.

So two discriminants marked `RECORDED` were grounded in a source the receiver
cannot resolve. **The implementations enforce a stronger structure than the
repository records** — 172 assertions hold a line against a form that puts `F`
in the state equation.

Both forms are now custodied separately as **S_v5** and **S_C1** (§2.1), and
rendering only one as *the* workspace was refused: that would make it the de
facto source. They are **not the same workspace** — S_v5 has 7 blanks over 2
lines, S_C1 has 5 over 1; only S_v5 offers homes for `F` and `κ`, only S_C1
writes the index; `γ` is written in neither.

**And neither covers the other.** A coupled system and an isolated one fill
S_v5 identically (one unindexed `Σ`); the adaptive part of an adaptive
controller is unwritable in S_C1 (no parameter equation). **Supplementing is
therefore not merely the non-lossy admission but the only one that covers both
problem classes.**

---

## 5 — Reddit as an executed crossing **[C5]**

The direction was inverted: an existing system supplies the occupants instead
of a model inventing them. Source is the archived Python codebase — 313 files,
~104k lines, read for mechanism.

**What it says.** The five ranking functions (`hot`, `controversy`,
`confidence`, `qa`, `score`) are **pure functions of accumulated counters** —
observations, not terms. **Reddit has no drift**: state is exactly constant
between events, and the time-dependence everyone associates with the site
lives entirely inside `hot`, which divides absolute epoch seconds by 45000.
Nothing stored changes as time passes.

**The compatibility pass** ran the extracted mechanism against both stencils
with three verdicts — `PLACED`, `NO_BLANK`, and **`LOSSY`** (a blank exists
and is structurally available, but placing there discards a property the
mechanism consumes).

**The result: the only element placed in both forms is the one we
constructed.** A decaying attention variable, added by an explicit ruling to
move time into state — not extracted from the archive. Of everything actually
*extracted*, exactly one takes a blank cleanly: the state-change gate.

Two `LOSSY` verdicts, **kept separate as independent findings**:

- **driving-process identity.** `∘ dW` is an anonymous increment. The
  archive's event is identified and the identity is *consumed* —
  previous-vote lookup keyed on `(actor, target)`, self-vote detection, karma
  routed to the target's author. Placing it there discards the index the gate
  runs on.
- **fan-out cardinality.** `Σ_ij(X_j → X_i)` names one destination. One
  admitted event routes to **author, subreddit and domain** through one gate.

And **two gates that cannot both be held**: `κ_change` (a boolean verdict with
refusal note codes, path-dependent through the *stored* prior verdict) and
`κ_propagate` (consulting `_spam`/`_deleted`, which the first never sees).
Both stencils offer at most one admissibility position.

**What went right:** the five ranking functions are `NO_BLANK` *by design* —
recorded as correctly homeless rather than forced into operator blanks. An
empty blank stayed empty.

---

## 6 — What is open

- **§3 operator semantics — `[unpopulated]`.** Blocks both projects. It now
  has acceptance criteria, of which the load-bearing one is: **what
  propositions count as witnesses for an assignment.** Nine criteria say what
  the primitives are; that one says how this tree could ever *check* an
  assignment rather than accept it.
- **§4 grammar — `[unpopulated]`,** now with a concrete job: how a formulated
  system is transformed into RME-7, and what happens when compression would
  lose a warranted distinction. The two `LOSSY` verdicts are worked examples
  waiting for it.
- **G_prov** — which form is the source. Coverage argument survives; the
  behavioural argument was withdrawn.
- **Q1** tier-0 all-or-nothing · **Q6** comprehension/exhibition ·
  **Q7** *can one κ compose two admissibility offices without erasing causal
  structure?*

**The posture on §3, recorded:** it is not being introduced to complete the
framework but as a source **permitted to invalidate it**. Including the
`κ_change` crossing — the best result the Reddit work produced, and expendable.
An artifact that cannot be lost was never being audited.

**The independence condition:** a source-grounded §3 exists only when its
claims and their witnesses are established **independently of the artifacts
they are used to audit**. A §3 reconstructed from what the implementations
already assume would pass every test in the tree. That is why the condition is
on provenance, not on consistency.

---

## 7 — What I am asking you for

Not architecture. The freeze holds and further design proposals are refused
until a gate moves. Three specific things:

1. **Is the displayed-versus-enforced result surprising to you?** If a printed
   acceptance set is not binding, I do not think any prompt-level constraint
   is, and that pushes enforcement into the interpreter. Say if you read the
   arm-3 data differently.
2. **The two `Σ` losses** — identity and cardinality — are being kept apart on
   the argument that a future formulation could resolve one without the other.
   Is that separation real, or are they one defect?
3. **Anything in §6 you can ground.** Not what you think the primitives mean —
   testimony that cannot be re-derived here is recorded and not binding, and
   this project has already conceded one round of unresolvable citations. A
   retrievable primary source, or nothing.

**Two general results, offered for use rather than agreement:**

> A maximally expressive minimal format is not necessarily a
> **self-instructional** format.

> Existing software is evidence about a system's **mechanism**, not evidence
> about how that mechanism should be **typed**.
