# AWV — Method and Change Log

Extracted from the spec sheet at v0.19. The spec states the system; this file states how the spec was made and how it changed.

---

## 18. Method

Naming the method this document has been using, and adopting Koen's account of it (*Discussion of the Method*, 2003).

**The engineering method:** the strategy for causing the best change in a poorly understood situation within the available resources. Its content is the use of heuristics.

**Heuristic**, on Koen's four signatures: does not guarantee a solution; may contradict other heuristics; reduces search time; acceptance depends on the immediate context rather than an absolute standard.

**sota:** the set of heuristics in use at a given time. This document *is* the project's sota, and the status markers are a sota register.

| Marker | Sota reading |
|---|---|
| FROZEN | In the sota, high confidence. Still a heuristic — defeasible, not proved by being frozen. |
| PROVISIONAL | In the sota, held pending better information. *Always give an answer.* |
| OPEN | Minimum decision deferred, because the cost of deciding now exceeds the cost of not knowing. |
| RESERVED | Outside the sota. *Work at the margin of solvable problems.* |

### 18.1 Heuristics in use

- **Allocate resources as long as the cost of not knowing exceeds the cost of finding out.** This is the fork-closure criterion, applied per fork rather than uniformly. Fork A must close — Â is undefined without it. Fork M may stay open indefinitely; the velocity choice costs nothing to defer and constrains nothing else.
- **Allocate resources to the weak link.** §17 is a weak-link register. Current weak link: the A/N/D cluster (§3.1), which leaves the matrix definition incomplete.
- **Make the minimum decision, at the latest possible time.** Why forks are held open rather than closed by default, and why RESERVED exists as a category distinct from OPEN.
- **Always give an answer.** Why α, β, λ_V, and μ carry provisional values rather than blanks. A default that is wrong is auditable; a blank is not.
- **Make small changes in the sota.** The precision passes (v0.6, v0.10). See 18.2 for the failure mode of this heuristic.
- **Use feedback to stabilize the design.** The relay–audit cycle: proposals arrive from outside, incorporation is a separate decision, and nothing enters the sota without passing audit.
- **Test-bed requirement.** *Any mechanism whose gain depends on inactive authority must be tested under authority-correlated inactivity, not only under random churn.* Random lapse makes standing and inactivity nearly independent, and the failure mode such a mechanism exists to govern is precisely their correlation. The requirement came from a measurement error that turned out to expose an unrepresented state of the simulated ecology rather than a notation slip.
- **Allocate resources as long as the cost of not knowing exceeds the cost of finding out** — applied literally in v0.14. Fork N had been resolved by argument in v0.13; six files of simulation cost less than carrying an unfalsified mechanism, and reversed the resolution. First fork in this project closed by measurement rather than by argument.
- **Solve problems by successive approximation.** Eleven versions, each a complete artifact rather than a stage of one.

Applied reflexively: **AWV is itself a heuristic** solution to attention allocation. Every FROZEN proposition is defeasible, and none is claimed to be the right answer — only the current sota.

### 18.1.1 Audit ledger — three failure classes

The sequence δ omission → repair → *H_S* omission → repair → declaration-completeness rule is diagnostic in itself: the failures were revealing the next missing invariant in the specification grammar rather than accumulating patches. Three distinct failure classes, each with its own check:

| Failure | Example | Check |
|---|---|---|
| **Restatement drift** | δ typed one way in §2.1, differently in §15.0.1 | `awvsim/typecheck.py` |
| **Undeclared use** | *H_S* used normatively before being declared | `awvsim/completeness.py` |
| **Hidden dependency** | a construction operator secretly reading *A* | §2.1.0's authority-construction closure, stated over the composition rather than over named operators |

The third has no mechanical check and probably cannot have one from the document alone — it is a property of an implementation, not of the text. Stating the closure over Â's whole composition is the strongest available textual defence: it binds operators that do not yet exist.

**Heuristic added:** *a repair that introduces a symbol must declare it in the same edit.* Both omissions were introduced by repairs for unrelated defects, which is the specific shape to watch — attention is on the defect being fixed, not on what the fix brings with it.

### 18.2 Recorded heuristic failure

Koen requires that a sota record where its heuristics failed.

*Make small changes in the sota* is conservative and generally sound, and it is what allowed the block-rank misreading to survive v0.1 through v0.3. Each cycle made a small, locally correct change to a foundation that was wrong; the changes were individually valid and cumulatively elaborated an error. **Small changes cannot correct a foundational mistake — they refine it.** The correction, when it came, required discarding roughly a third of the document at once, which is precisely the large sota change the heuristic exists to discourage.

Aggravating factor: v0.1 §0 flagged the reading as the load-bearing assumption to correct first, and four versions were built on it regardless. A flag is not an adjudication. Marking an assumption as load-bearing while continuing to load it produces a document that *looks* audited, which is worse than one that visibly isn't.

**Counter-heuristic, added to this sota:** *when a flagged load-bearing assumption survives more than one version unexamined, examine it before building further.*

### 18.3 One qualification on adopting Koen

Koen's claim that all engineering knowledge is heuristic would, applied flatly, erase a distinction this spec uses as its main audit tool — derived items (Prop 1, the disintegration; Prop 3's variance identity) against stipulated items (Stipulation 1) against defaults (α, β). Non-promotion discipline depends on keeping those apart, and collapsing them would licence exactly the moves the audits have been blocking.

The reading that preserves both: **a theorem is not a heuristic, but the decision to apply this theorem to this situation is.** The sota is heuristic in composition even where its contents are proved. Internally the three types stay distinct and non-promotion holds; externally the whole set is a heuristic choice, revisable in full.

---

## 19. Change log

**v0.18** — Type discipline pass, with version archaeology removed from the body; the change log remains the record. Constitutional sentence: "who is trusted to judge" → "whose judgment has standing," removing an epistemic overclaim that contradicted Stipulation 1 at the root. δ retyped as a derived operator rather than a state object, making 6B mechanical — the cycle through behaviour and δ passes through no governed state. Central invariant Â = f(Σ_U, δ) frozen explicitly. Two contradictions closed: the scrutiny test, which as written exempted the default feed, now distinguishes direct, behavioural, and no coupling; and "no moderator exists," contradicted by §13.1's adjudicator. Added: δ computationally exogenous but not causally independent; α = 0 gives *A* = τ, one-person-one-vote only under uniform τ; Stipulation 1 split into R1 common target, R2 calibration, R3 dependence, with R1 identified as Fork R's substance; β has an empirical interpretation but no estimable warrant; D/Dδ/N typed as three transformations; no indirect authorship privilege; Fork Q reclassified as a sovereignty fork parallel to G; classification declared relative to a stated boundary; Fork W opened on subscription semantics — if the interface says "follow" and users mean it, *A* measures interest and R2 becomes a claim that popularity tracks judgment accuracy. Personal-space accountability language deleted; exit is not accountability. Not adopted: retrofitting type and defeater fields onto all frozen items, and the health-metric principle as proposed, which demanded an impossible proof and restates a prohibition §2 already enumerates.

**v0.17** — Empirical content removed. Comparison tables, metric values, oscillation and turnover figures, and the superseded median-band mechanism moved out to `awvsim/`; the spec now states each decision and its warrant and points to the evidence rather than reproducing it. The single-metric warning was retained as a frozen rule in §6, since it constrains how health is legislated rather than reporting a result. No decision changed.

**v0.16** — RME-7 criterion corrected in three cases (§15.0). v0.15 fixed a disjunction error and introduced a cycle clause with no internality qualifier, which classified AWV as RME-7 two paragraphs before the same section asserted 6B; the environmental loop through behaviour is 6B because behaviour is not a governed state object. *C_t* named as a diagnostic distinct from *D_t*. Authority-correlated lapse implemented in the simulator and made a permanent test-bed requirement (§18). Fork N reconfirmed with a wider margin in that régime. Recorded as an observed property, conditional on an unverified assumption about user behaviour: uniform fallback plus δ already constitutes an anti-concentration loop when standing and inactivity correlate, supplying without a parameter what median-band was designed to supply with one.

**v0.15** — Typing pass; no mechanism added and no architecture reopened. Temporal semantics frozen (§2.0): behaviour at *t* alters authority first solved at *t+1*, never the vector being solved at *t*, which forecloses a coupled fixed point the spec had not excluded; and a batch boundary is explicitly not a fence, so periodicity in an implementation does not reintroduce v0.13's coupling. Fork Dδ split from Fork D — partial-δ edge semantics (D1/D2/D3) is a different question from subscription weighting, and v0.12–v0.14 ran them together. *D_t* corrected from column count to authority mass, with the measurement showing the two are near-equal only because the baseline behaviour model treats lapse as uncorrelated with standing; authority-correlated lapse is recorded as a gap in the model, not in the spec. Vote alphabet typed (§10.1) and vote multiplicity frozen (§10.2) — one current vote state per user per post, closing a toggling manipulation of *S*. Eligibility predicate *I* made prerequisite to Fork Q: type the object before debating its controller. Cold start restated as a pair Fork C must clear jointly. RME-7 dependency condition corrected to a conjunction — the disjunctive form classifies every pipeline as RME-7 — and the C23 import boundary stated: criterion only, no operator correspondence, grammar establishes classification and not the truth of what is classified. Classification ledger added (§15.0.1). Not adopted: T/U/V as open items (frozen rules belong in the body, not in a register whose function is to list live decisions), and the proposed multi-directory filesystem.

**v0.14** — Fork N closed to **uniform** on simulation evidence, reversing v0.13. Median-band showed no concentration advantage at any width and lost on every adversarial axis: worse under Sybil injection, worse at high churn, exposed to an adaptive band-capture attack that uniform has no target for, and leaving a substantial fraction of users at exactly zero authority under seed-τ where uniform leaves none. The median's robustness justification compared it against a mean-targeted fallback nobody had proposed; against uniform, which presents no target, the advantage was zero. Three findings carried forward independently: point-mass fallback produces a *rotating* oligarchy in which mobility and concentration are simultaneously maximal, so no single metric catches it; the failure is monotone in the wrong direction, worst where the rule matters most; and uniform fallback acts as a partial franchise substitute under seed-τ, coupling Forks N and A favourably. Consequences: computational closure recloses (§2.1), the epoch fence is withdrawn (§3), Fork S closes as moot, and AWV reverts to **6B**. Band width did damp as hypothesised and middle-class lock-in appeared at wide settings; both are moot with N resolved. Route 7C is retained in §15.0 as a documented near-miss, since the methodological finding — that a numerical convention can cross the RME-7 boundary without announcing it — stands independently of the instance. Simulator at `awvsim/`, findings at `awvsim/FINDINGS.md`.

**v0.13** — Fork N resolved in mechanism: dangling columns take a fallback uniform over a rank band centred on the previous epoch's median. Median chosen for robustness to outlier mass, **not** for secrecy; mean and mean+median rejected as movable from the tails; band rather than point mass, since a point mass concentrates rather than redistributes and creates a valuable slot to occupy. Band width identified as the damping parameter. Gain shown to be proportional to dangling mass rather than to concentration, so the mechanism is explicitly *not* a concentration controller. Fork remains blocked on δ normalization order and on Fork A's effect on median well-definedness; Fork S opened for the empirical question. Computational closure reclassified as open (§2.1). Epoch fence reinstated (§3) — the v0.1 fence returns with the feedback that justified it. §15.0 given a fourth route, 7C, demonstrating that RME-7 can be reached by a numerical convention rather than by governance; AWV is now 6B plus 7C. Rank non-exposure recorded as a non-defense, with the Mode 1 / Mode 2 differential as a working estimator of *A* — a presentation distinction acting as an estimator of constitutional state. Mean/median divergence added as telemetry.

**v0.12** — Two contradictions resolved. (i) §4's claim that extra eigenproblems are constitutionally free was unconditional and is now bounded: free only while output remains presentation state, which excludes §13.2's use of community-local PageRank to assign admission authority. (ii) §13.4's *A*-weighted supermajority rows are *A* → θ → *A*, the loop §15.1 reserves — those rows are now contingent on Fork G rather than operative, and Fork G is reclassified as the boundary item. Closure trichotomy added (§2.1): constitutional, computational, and dynamical closure are distinct, and only the first two are closed; δ named a coupling operator. Ephemerality frozen as a state-retention, not causal-isolation, property. Non-promotion rule stated generally with enumerated prohibitions. §15.0 classification boundary added; AWV as deployed is 6B, not 6A. Stipulation 1's testability corrected downward — no estimand, no ground truth; Fork R opened, β reclassified from provisional to unwarranted. Covariance stated in general form. Cycle-provenance limit added to §3 and identified as the same failure as brigading one layer up. Fork Q opened on platform-integrity adjudication. Fork B marked moot. Fixed: δ/λ_V symbol collision in feed equations; matrix convention; "modifies" → "creates an authority edge"; personal-space accountability claim weakened to exit. Added: max *A* and top-*k* share alongside *N*_eff; spectral gap marked diagnostic; partial-δ normalization order as prior to Fork N; slow authority capture and δ farming to the attack surface; privacy noted as unpriced.

**v0.11** — Method named (§18). Koen's engineering heuristic adopted as the spec-generation method; status markers restated as a sota register; heuristics in use enumerated against where each shows in the document. Heuristic failure recorded: *make small changes in the sota* is what let the block-rank misreading survive four versions, and the counter-heuristic is added. Qualification entered so that Koen's universal-heuristic claim does not collapse the derived/stipulated/default distinction that non-promotion discipline rests on. No change to the system.

**v0.10** — Authority weighting given its filter interpretation. Stipulation 1 restated in signal-reliability form and made testable: *A* must be monotone in the inverse variance of judgment error, which is what inverse-variance weighting commits to. β consequently acquires a meaning and loses its provisional warrant. Proposition 3 frozen with three limits — variance reduction alone justifies nothing since signal is attenuated equally; independence is load-bearing and correlated noise scales as *k* rather than √*k*; and the filter detects contribution, never intent, and acts only between *V* and *S*. Proposition 3a: noise suppression is not content removal. Disturbance typing added to §15 with no new objects. Second cold-start problem named — newcomers' judgment is discounted, not only their content.

**v0.9** — Open admission frozen as the default condition of a topical community; no admission authority and no moderator exist unless a community opts in. Fork K reduced accordingly, from *may a community have judgment-requiring rules* to *may a community voluntarily adopt curated admission* — optional architecture, not a requirement. Proposition 2a added: ranking substitutes for moderation only where harm is attention-mediated; harassment, doxxing, and impersonation reach their target directly and fall to §13.1, which had been missing the category. Rate limits reframed as capacity management protecting plurality, not as governance. Quarantine deleted as having no function under plural feeds.

**v0.8** — Fork K decomposed and mostly dissolved. Proposition 2 frozen: ranking filters attention and cannot remove, so no ordering power is equivalent to suppression. Its dependency stated — rank-free modes are undefendable by ranking, so plurality requires volume control. Platform integrity (§13.1) separated from governance and explicitly not called moderation. Admission-rate control added (§13.2) with Fork P on whether limits scale with *A*, which would contradict §11. Fork K restated as whether topical communities may have judgment-requiring admission rules. Volume attacks added to the attack surface. Search noted as an ordering mode.

**v0.7** — Context layer specified. Personal editorial spaces separated from topical communities; admission distinguished from ordering as a frozen pair. §12 given a second axis: three content streams (authored, endorsed, other-submitted) crossed with four ordering modes. Chronological added as Mode 4 and made the endorsed stream's default rather than its only option. Constitutional sentence revised — "eligible," and the fourth clause stated positively rather than as an enumeration. Endorsement confirmed authority-inert on the cost-of-act criterion, closing a fork open since the owner/editor cycle. Fork O opened on endorsement pricing: the direct branch removed the conditional normalization that used to price admission automatically. Fork K narrowed a second time, now topical communities only.

**v0.6** — Precision pass, no architectural change. Fork N opened: dangling columns are endogenous under δ, decide where non-readers' authority goes, and exclude the self-loop option as a rank sink; couples to Fork A. §6's α claim corrected — damping preserves uniqueness for all α < 1 under uniform τ; under seed τ the guarantee weakens to uniqueness-with-zeros. Invariant 1 restated to keep user→user subscription distinct from user→community interest. Stipulation 1 sharpened to state that PageRank establishes recursive authority only, never epistemic competence. Fork F split on whether *h* is diagnostic or a second governance currency. Fork M enumerated.

**v0.5** — Three-layer separation frozen with the constitutional sentence and the scrutiny test. Presentation layer specified: three modes, viewer-selected windows, plurality free. One-eigenproblem constraint narrowed to *authority only* — the presentation layer may run any number. Invariant 1a added, foreclosing the overclaim that feed manipulation cannot influence authority. Fork K reduced from "who governs visibility" to "who can delete," with community-local PageRank leading. Fork J reframed as cost, not principle. Fork M opened. Default feed mode added as a governed parameter; global-feed suppression row deleted. Velocity gaming and default-feed capture added to attack surface.

**v0.4** — Generative hierarchy removed. One PageRank on Σ_U. Communities demoted to routing. Provenance correction. Authority-independent authorship frozen.

**v0.3** — Stage 3 deleted; lineage corrected; disintegration and substitution rate stated; horizon frozen; Ψ reserved.

**v0.2** — Endorsement edge corrected from vote to subscription. Acyclicity established.

**v0.1** — Initial. Block decomposition (in error); teleport tradeoff; hub/authority split.
