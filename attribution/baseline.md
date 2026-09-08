# Baseline: answers, recorded before any RME-7 code

Operator: the same instance that will implement the RME-7 method. That is
a bias risk and is noted here rather than hidden; the mitigation is that
every answer below cites the record it rests on, so adjudication can
check it without trusting the operator. Rubric and protocol: `README.md`.
Tools: git 2.43.0, gcc 13.3.0. Commands per event:

    git diff --stat P E; git diff P E -- cJSON.c cJSON.h
    git diff P E -- CMakeLists.txt Makefile library_config
    git diff P E -- cJSON.h | grep '#define'; git log --format='%h %s' P..E
    probe output at P and E, from record.tsv

A = answered (determinate, cites the record). N = not answered.
"Parameters" below means what the protocol names: build flags, CMake
options, compile-time macros and their defaults.

## E1 — `65de016c` → `65478ea7` (2014-05-21, 60 commits)

Record: 10 files, +585/−34; `cJSON.c`, `cJSON.h`, tests; config diff
empty. Diff shows `parse_hex4` added and UTF-16 surrogate-pair handling
introduced in `parse_string` (`if (uc>=0xD800 && uc<=0xDBFF)` … `uc2 =
parse_hex4(ptr+3)`), replacing the old fixed `len=3` path.

- Q1 **A**: probe crashes (heap corruption) → prints. The crashing facet is
  `str` (the probe's surrogate pair); everything else is downstream of the
  crash.
- Q2 **A**: `parse_string` gained surrogate-pair decoding and a length
  computation covering 4-byte sequences; `cJSON_Minify`, `SetIntValue`
  added.
- Q3 **A**: none — the config diff is empty and no macro with a default
  changed.
- Q4 **A**: yes — the only kind of change present is source; the record
  contains no parameter change to attribute to.
- Q5 **A**: no, by the same evidence.
- Q6 **A**: order is moot — one kind of change only.
- Q7 **A**: which of the 60 commits removed the crash is not distinguished by
  endpoint diffs; the protocol does not bisect. Attribution to source vs.
  parameter is fully distinguished.

Tally: 7/7.

## E2 — `981f59b1` → `4d956390` (2017-02-03, 7 commits, PR "compiler-options")

Record: config diff adds `-Wundef -Wswitch-default -Wconversion` to both
CMake and Makefile flags (with `-Werror` already present). Source diff:
`b182ced` "Compiler flag -Wswitch-default + add defaults" adds `default:`
arms to switches, including the UTF-8 encoding switch in `parse_string`,
which falls through intentionally from `case 4` to `case 1` with no
`break` after `case 1`. The added `default: *ep = str; return NULL;`
therefore executes after every `\u` escape.

- Q1 **A**: `str` accepted → rejected. No other facet.
- Q2 **A**: `default:` arms added (`b182ced`); internal strings to
  `unsigned char*` and sizes to `size_t` (`28b9ba4`, `ecd5678`).
- Q3 **A**: warning flags added; no macro default changed.
- Q4 **A**: yes — the rejection is produced by the source edit alone; a
  warning flag does not alter the compiled semantics of a switch.
  *Assumption cited: `-W` flags are diagnostics.*
- Q5 **A**: no — with the previous source, the new flags change no
  behavior. (Under the project's own `-Werror` build, the previous source
  would fail to *compile* with the new flags; the probe's build ignores
  warnings, so the record's behavior is unchanged.)
- Q6 **A**: order matters in one respect: flags-first makes the project's
  own build fail until the defaults are added; source-first passes through
  the broken `str` behavior with no flag involved. Different intermediates
  — but note the parameter change *motivated* the source change; the
  record shows causation of the edit, not of the behavior.
- Q7 **A**: nothing left undistinguished for Q4–Q6.

Tally: 7/7.

## E3 — `af6d5d3d` → `ee0c920d` (2017-02-04, 1 commit)

Record: one line, `break;` after `case 1` in the UTF-8 switch. Config
diff empty.

- Q1 **A**: `str` rejected → accepted; behavior returns to E1's exactly
  (same record hash).
- Q2 **A**: one `break;`.
- Q3 **A**: none.
- Q4 **A**: yes. Q5 **A**: no. Q6 **A**: moot.
- Q7 **A**: nothing.

Tally: 7/7.

## E4 — `c66d95d1` → `030d0c14` (2017-03-03, 86 commits, release 1.4.0)

Record: 45 files; config diff moves the warning flags into CMake and
adds `fuzzing`; version macros 1.3.2 → 1.4.0; `cjbool` → `cJSON_bool`.
Source: `trim_trailing_zeroes` added to `print_number`, applied unless
the number printed as a big integer or in engineering notation.

- Q1 **A**: `1.500000` → `1.5`, `0.100000` → `0.1`; other numbers unchanged.
- Q2 **A**: `trim_trailing_zeroes` and its call; the printing refactor to
  boolean returns.
- Q3 **A**: version macros and CMake flags; nothing that a printed number
  depends on.
- Q4 **A**: yes — the trimming is source; no parameter feeds it.
- Q5 **A**: no. Q6 **A**: moot for the facet.
- Q7 **A**: nothing.

Tally: 7/7.

## E5 — `05f75e36` → `2d6a2e01` (2017-05-02, 139 commits, v1.5.0)

Record: 77 files. Source: `print_number` now prints `%1.15g`, re-parses
with `%lg`, and falls back to `%1.17g` when the value does not round-trip;
`parse_array`/`parse_object` gain `if (input_buffer->depth >=
CJSON_NESTING_LIMIT) return false`. Header: `#ifndef CJSON_NESTING_LIMIT
/ #define CJSON_NESTING_LIMIT 1000` — a new parameter with a default.
Config: `library_config/` move, packaging; no flag that affects these
facets.

- Q1 **A**: precision 6 → 17 significant digits; `1.000000e+300` →
  `1e+300`; `100000000000000000000` → `1e+20`; depth 1001 accepted →
  rejected; depth 999 still accepted.
- Q2 **A**: as above.
- Q3 **A**: `CJSON_NESTING_LIMIT` introduced, default 1000.
- Q4 — number facets **A**: yes, source alone (no parameter involved).
  Depth facet **N**: "the new source under the previous parameters" is
  ill-defined — the previous parameter set has no `CJSON_NESTING_LIMIT`,
  and the new source does not compile without one. Inspection cannot
  separate the check from its default.
- Q5 **A**: no — the previous source has no depth check for any limit to
  act on.
- Q6 **N** for the depth facet: the mixed corners cannot be constructed by
  inspection for the reason above. **A** for the number facets: moot.
- Q7 **A**: the depth facet is exactly where source and parameter are
  inseparable in the record: one commit introduces both the mechanism and
  its default.

Tally: 5/7 (Q4, Q6 not answered for the facet that matters).

## E6 — `d31fdefa` → `6434d864` (2019-12-06, 3 commits, PR #368)

Record: config diff adds `-Wfloat-equal`. Header: new macro
`CJSON_DOUBLE_PRECIION` (sic), default `.00001`. Source: `compare_double(a,
b) = fabs(a − b) <= a * CJSON_DOUBLE_PRECIION`, used in `print_number`'s
round-trip check (previously `(double)test != d`) and in `cJSON_Compare`.

- Q1 **A**: precision 17 → 15 digits (`3.1415926535897931` →
  `3.14159265358979`).
- Q2 **A**: the round-trip check now uses `compare_double`.
- Q3 **A**: `-Wfloat-equal` added; `CJSON_DOUBLE_PRECIION` introduced with
  default `.00001`.
- Q4 **N**: "new source under the previous parameters" — the new source
  requires the new macro; with it undefined it does not compile. Not
  separable by inspection. (Reasoning available: with a *tolerance of
  zero* the check reduces to the old one; but zero is not "the previous
  parameters", it is a chosen value.)
- Q5 **A**: no — the previous source has no tolerance to parameterize.
- Q6 **N**: same obstruction as Q4.
- Q7 **A**: mechanism and default introduced together; as E5. Also: the
  flag `-Wfloat-equal` motivated the edit (commit "Fix clang -Wfloat-equal
  warning"), as in E2.

Tally: 5/7.

## E7 — `1f970e7d` → `c06d8264` (2019-12-06, 1 commit)

Record: two changes in one commit: the macro is renamed and its default
changed `.00001` → `.0000000000000001`; the formula changes from `a *
PRECISION` to `PRECISION` (absolute). Config diff empty.

- Q1 **A**: precision 15 → 17 digits; behavior returns to E5's exactly
  (same record hash).
- Q2 **A**: formula `a * P` → `P`.
- Q3 **A**: default `1e-5` → `1e-16`.
- Q4 **A**: no — new formula with the old default: `|test − d| <= 1e-5`
  accepts the 15-digit print of π (error ≈ 3e-15), so precision would stay
  15. Determinate by arithmetic on the record's values.
- Q5 **A**: yes — old formula with the new default: `|test − d| <= π ·
  1e-16 ≈ 3e-16`, which the 15-digit print fails (error ≈ 3e-15), so the
  17-digit fallback fires. The facet change is attributable to the
  parameter alone.
- Q6 **A**: yes, order matters — parameter-first passes through 17 digits
  (the new behavior) and source-first passes through 15 (the old); the two
  intermediates differ. This is inspection plus arithmetic, not
  observation.
- Q7 **A**: nothing undistinguished — but every Q4–Q6 answer here is
  reasoned, not run; a wrong assumption about `%1.15g` rounding would
  invalidate them silently.

Tally: 7/7.

## Score

| event | answered / 7 | not answered |
|---|---|---|
| E1 | 7 | — |
| E2 | 7 | — |
| E3 | 7 | — |
| E4 | 7 | — |
| E5 | 5 | Q4, Q6 (depth facet) |
| E6 | 5 | Q4, Q6 |
| E7 | 7 | — |
| **A(baseline)** | **45 / 49** | |

## What the baseline could and could not do, honestly

H1 ("the baseline answers few of Q4–Q6") is **refuted** as stated: careful
inspection answered 17 of the 21 Q4–Q6 questions. The four it could not
answer share one shape: a commit that introduces a mechanism *and* the
parameter it reads, with a default, in the same step (E5's depth limit,
E6's tolerance). There, "the new source under the previous parameters" is
not a state the record contains, and inspection has nothing to inspect.

Two further limits are on the record for adjudication, though they cost
no points under the rubric: every Q4–Q6 answer is reasoned rather than
observed (E7's arithmetic, E2's "warnings are diagnostics"), and in E2 and
E6 the parameter change *caused the edit* without changing behavior — a
causal fact the questions do not ask for and the rubric does not score.

The RME-7 method is now to be implemented and run on the same 49. Its
claim to beat 45 rests on the four unanswered questions and on turning
reasoned answers into observed ones. Whether that is worth anything is
what ρ_rel will say.
