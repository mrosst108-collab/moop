# State-versus-parameter attribution

An application of the RME-7 discipline chosen for benefit over cost against
an executable baseline, not to demonstrate primitives. Protocol, frozen:

    freeze Q → execute baseline → record → implement → execute → compare

No interpretation may alter Q after a baseline answer has been seen. Any
office the application does not need stays unused; none is instantiated for
completeness (`../prompts/asdg-rme7.md` §7).

## Target, and why it is independent

**cJSON** (`https://github.com/DaveGamble/cjson`), `origin/master` at
`fb16e5cf358798aabb049655975cde8427101056`, first-parent history of 386
commits from 2009-08-26 to 2026-04-09, fetched read-only. Its architecture,
build configuration and tests predate this selection by up to seventeen
years and were arranged by people who have never heard of RME-7. It has a
parameter history (CMake options; compile-time macros with defaults such as
`CJSON_NESTING_LIMIT`, `CJSON_CIRCULAR_LIMIT`; build flags) and a behavior
history (a vendored Unity test suite that builds unchanged at 2017 commits;
one build-and-test cycle takes eight seconds here). Over the history, 173
commits touch configuration, 465 touch `cJSON.c`, 57 touch both.

Selection was made from the properties above, verified before anything
was frozen, and from nothing else. The constitution's §5 named the problem
(semantic change hiding behind normal-looking execution) before this
target or the reddit existed.

## The instrument

`probe.c` is a fixed-input program using only the oldest API (`cJSON_Parse`,
`cJSON_Print`, `cJSON_Delete`): number formatting, string escapes and
surrogate pairs, object printing, nesting at depth 999 and 1001, a trailing
comma, a duplicate key. `sweep.sh` compiles it against every first-parent
commit's `cJSON.c`/`cJSON.h` with the same flags and records a hash of its
output. `record.tsv` is that record: 386 rows, every commit builds and
runs, six distinct behaviors, seven change points. The same record serves
both methods.

## Behavior record: the seven events

Read from `record.tsv` and the probe outputs only. Commit subjects were
read; diffs were not, and will not be until Q is frozen.

| event | index | commit | date | facet that changed |
|---|---|---|---|---|
| E1 | 6 | `65478ea7` | 2014-05-21 | probe crashes (heap corruption) → prints |
| E2 | 93 | `4d956390` | 2017-02-03 | `str` (a surrogate pair) accepted → **rejected** |
| E3 | 96 | `ee0c920d` | 2017-02-04 | `str` rejected → accepted again *(behavior returns to E1's)* |
| E4 | 124 | `030d0c14` | 2017-03-03 | numbers `1.500000`, `0.100000` → `1.5`, `0.1` |
| E5 | 165 | `2d6a2e01` | 2017-05-02 | precision 6 → 17 digits; `1e+300` form; **depth 1001 accepted → rejected** |
| E6 | 286 | `6434d864` | 2019-12-06 | precision 17 → 15 digits |
| E7 | 289 | `c06d8264` | 2019-12-06 | precision 15 → 17 digits *(behavior returns to E5's)* |

Two recurrences (E2/E3, E6/E7) and one event (E5) that is a release merge
containing, among other things, the introduction of a parameter with a
default.

## Q, frozen

For each event E_k, with c_prev the previous first-parent commit and c_k
the event commit:

- **Q1** Which probe facets changed between c_prev and c_k?
- **Q2** Which source artifacts (`cJSON.c`, `cJSON.h` code) changed?
- **Q3** Which parameter artifacts changed: build flags, CMake options,
  compile-time macros or their defaults?
- **Q4** Is the facet change attributable to the source change alone — would
  it have occurred with the new source under the previous parameters?
- **Q5** Is it attributable to the parameter change alone — would it have
  occurred with the previous source under the new parameters?
- **Q6** Does the order matter — do "parameters first, then source" and
  "source first, then parameters" pass through different intermediate
  behaviors?
- **Q7** Where does the available record fail to distinguish Q4–Q6?

Seven events × seven questions = 49 questions. Q1 is a control (both
methods read it off the record).

## Scoring rubric, frozen

A question is **answered** when the method yields a determinate claim that
cites something in the record (a commit, a diff, a flag, a probe output) —
not a guess, not "probably". "The record cannot distinguish" is an answer
to Q7 and a non-answer to Q4–Q6. A = the count of answered questions;
ρ_rel = A(RME-7) / A(baseline) on the same 49. Disagreements between the
two methods on an answered question are listed for adjudication with the
evidence each cites; neither method is presumed right.

## The baseline protocol, frozen

Tools: git 2.43.0, gcc 13.3.0, cmake 3.28.3, this container. For each event:

1. `git diff --stat c_prev c_k` and `git diff c_prev c_k -- cJSON.c cJSON.h`
   for Q2; `git diff c_prev c_k -- CMakeLists.txt Makefile library_config`
   plus `git diff c_prev c_k -- cJSON.h | grep '#define'` for Q3.
2. `git log --format='%h %s' c_prev..c_k` for context (a merge may carry
   many commits).
3. The probe at c_prev and c_k (already in the record) for Q1.
4. Q4–Q6 are answered only with what steps 1–3 give: inspection and
   reasoning over the diffs. The baseline does not construct
   counterfactual builds; ordinary tooling has no notion of "the previous
   parameters with the new source", which is the point under test.
5. Q7 by elimination.

Answers are recorded in `baseline.md` verbatim, one block per event, with
the commands and their outputs, before any RME-7 code is written.

## Hypotheses, recorded before the baseline runs

- H1 (mine, from before the target was chosen): the baseline answers few of
  the Q4–Q6 questions with a determinate, record-backed claim. **To be
  measured, not assumed.**
- H2: an RME-7 method that separates X (source) from θ (parameters) can
  build the two mixed corners — new source with old parameters, old source
  with new parameters — run the probe on them, and answer Q4–Q6 by
  observation rather than inspection, with Q6 as the commutator: the two
  mixed corners differing is γ ≠ 0. This is the implementation to be
  written after the baseline is recorded, not before.
- H3: E5 will be the case where both methods struggle, because the release
  merge changes source and introduces a parameter in one step (Q7).

## Status

Frozen. Baseline not yet executed. No RME-7 code exists.
