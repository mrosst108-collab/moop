# Phase 3 run: two events on `reddit-h3.txt`

Contract: `reddit.md` (`6abc1f9`), unrevised. Transcript: `reddit-h3.txt`,
24 lines, authored to hold one Σ → F → Σ → observation shape twice.
Derivation: `corners-reddit.sh` (classification and line removal only;
it executes nothing). Executor: `../reddit/build/reddit FILE` followed by
`show` for every track named in the interval. Artifacts: `h3-E13/`,
`h3-E19/` — each holds `source.txt`, `NM`, the four literal corner
transcripts and their observations.

## Artifact

| event | corner | meaning | sha256 | lines | exit |
|---|---|---|---|---|---|
| E13 `rules science 1 50 3.0 3600 1 1` (13, 18] | H00 | X_new, θ_new | `4bf8d84006a6` | 18 | 0 |
| | H01 | X_new, θ_old (minus F_13) | `71bc38a31d93` | 17 | 0 |
| | H10 | X_old, θ_new (minus Σ in (13,18]) | `80ffb1f4d14d` | 16 | 0 |
| | H11 | X_old, θ_old | `799521d94273` | 15 | 0 |
| E19 `lock science 1 0` (19, 24] | H00 | X_new, θ_new | `51cc90a2b96d` | 24 | 0 |
| | H01 | X_new, θ_old | `8b02a94f7a19` | 23 | 0 |
| | H10 | X_old, θ_new | `9ef42cfe1831` | 21 | 0 |
| | H11 | X_old, θ_old | `5d1877f2e311` | 20 | 0 |

Recorded: the source transcript's own `show` lines (in the history).
Reproduced: H00 is the source cut at *m*, replayed by the same binary; its
observation is the reference. Mixed: H01, H10. Conclusions: below.

## E13 — `min_hot` 0 → 3, then a comment, a vote, a sweep

Observations at *m* (`show science`, nodes only; θ line as printed):

| corner | θ shown | nodes present |
|---|---|---|
| H00 | min_hot=3.00 | #1 Ice caps (+8, 4.00), #0 Water (+7, 3.50) |
| H01 | min_hot=0.00 | #1 Ice caps (+8), #3 Cold reply under it (+1), #0 Water, #2 Source? under it |
| H10 | min_hot=3.00 | #0 Water (+7, 3.50) only |
| H11 | min_hot=0.00 | #0 Water, #2 Source?, #1 Ice caps (+3, 1.50) |

Facets that changed between *n* and *m* in H00, and the frozen mapping:

- **Source? (#2) dropped.** H01 present, H10 dropped. Q4 no, Q5 **yes**, Q6
  yes (mixed corners differ). Attributable to θ alone; γ ≠ 0 on this facet.
- **Ice caps (#1) survives the sweep, at +8.** Before *n* it had +3. H01
  present (+8), H10 **dropped** (+3 → hot 1.50 < 3). Q4 yes, Q5 no, Q6 yes.
  The survival is joint: the vote (Σ) arriving before the sweep is what
  keeps it under the new rule; had the sweep run first it would be gone.
  That order dependence is γ observed, and it is a fact about this history
  that neither the F line nor the Σ line states.
- **Cold reply (#3) absent.** H01 present (admitted at hot 1.00 under
  min_hot 0), H10 absent. Q4 no. Q5 by the frozen mapping reads H10 —
  but H10 *removed the arrival itself*, so its absence there is by
  construction, not by verdict. See finding 1. The discriminant that does
  answer it is H00 versus H01: the same arrival, refused under θ_new and
  admitted under θ_old — θ alone, observed.

Baseline by inspection (the transcript's own diff, lines 14–18 read):
gives the same three attributions with reasoning about hot values; the
corners turn each into an observation, and the second facet's order
dependence is the one inspection has to compute rather than see.

## E19 — `lock science 1 0`, then two comments, a vote, a tick

All four corners show the **same nodes**: #1 Ice caps (+8, 3.36), #0
Water (+7, 2.94). Only θ differs (locked=0 versus −1, the `[locked]`
marker). Both interval comments are absent in every corner — H01 too,
where there is no lock — because `min_hot=3.00`, standing since E13,
refuses any fresh comment (hot 1.00 at arrival). The vote on #2 is refused
in every corner because #2 was swept at E13.

Frozen mapping, facet "Late comment absent": Q4 yes (H01 absent), Q5 —
finding 1 again, Q6 **no**: H01 and H10 agree on every node. γ = 0.
Conclusion: the event at 19 is **causally inert in its interval**. The
facet changes are attributable to the *standing* θ from E13, not to F_19.
Inspection could reach this too; the corners establish it by
observation in one comparison, H00 = H01 on X.

## Findings, both about the method, recorded and not repaired

1. **Arrival facets are degenerate under the Q5 mapping.** When the facet
   is the presence of a node that *arrived inside the interval*, the
   corner `(X_old, θ_new)` removes the arrival line, so the facet's
   absence there is by construction. The discriminating pair for such a
   facet is `(X_new, θ_new)` against `(X_new, θ_old)` — H00 against H01.
   The frozen mapping (`h2.md`) was written for cJSON, where every facet
   was a fixed probe input present in all corners; on a transcript,
   facets can be arrivals. A revision to the mapping for arrival facets
   is a candidate correction, to be frozen before any further run, not
   applied here.
2. **An event can be masked by standing θ.** Q presumes the F line at *n*
   is the candidate cause; E19 shows an admitted F line with no effect on
   X in its interval because an earlier θ already refused everything it
   would have. The corners detect this as H00 = H01 on X. Q7 for such an
   event should name the masking θ; the current Q7 asks only where the
   record fails to distinguish. Candidate correction, same rule.

Neither finding was designed in; the second was an accident of authoring
`min_hot=3` before the lock and is kept as such.

## Score, under the frozen rubric

Two events, seven questions each: 14. Inspection answers 14 (the
transcript is 24 lines). Corners answer 14 and, for Q5 on the two arrival
facets, only via the H00/H01 pair the mapping does not name — scored
answered, with the pair cited, flagged by finding 1. ρ_rel = 1.0. The
gain here is not count: it is that two of the answers (Ice caps' order
dependence; E19's inertness) are observations rather than computations,
and the method found two defects in its own mapping on its first
transcript.

## Status

    Phase 3 execution: CLOSED     Score: FROZEN (14/14, ρ_rel = 1.0)
    Findings: OPEN                Method defects: OPEN
    Rerun: NO                     New freeze: NOT YET

The defects are adjudicated as questions before any Phase 3b is written,
and a Phase 3b may not be warranted. The three questions, with the
operator's positions stated for the adjudication to accept or refuse —
positions, not rulings:

1. **Does an arrival event require a different intervention geometry?**
   Position: yes, and a smaller one. For a facet that pre-exists *n* the
   2×2 grid stands. For an arrival facet, "X_old" has no referent — the
   node does not exist before *n* — so the grid collapses to 1×2: keep
   the arrival line and vary θ (H00 against H01). This narrows the
   mapping's domain; it does not change what is asked.
2. **Should event selection distinguish admitted F events from
   effective ones?** Position: no change to selection, because
   effectiveness cannot be known before the corners run and selecting on
   it would be selecting on the outcome. Keep selecting admitted F lines
   — the record's own notion — and add *inert* as a verdict the run can
   return (H00 = H01 on X), reported under Q7 with the standing θ named.
   Inertness is a result, not a filter.
3. **Does either correction change the purpose or identity of the
   original experiment?** Position: no. Correction 2 adds an outcome
   category; correction 1 restricts an instrument's domain and supplies
   a reduced grid for the cases outside it. Neither touches Q, the
   rubric, or the cJSON result, which had no arrival facets and no inert
   events. Both would be recorded as corrections to `h2.md`'s mapping
   with the run that forced them cited, never as edits to it.

The stronger result stands as stated above it: the reddit is now a test
bed that can find limitations in the attribution protocol while the
frozen result it was found on stays untouched.
