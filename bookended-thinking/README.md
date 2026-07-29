# bookended-thinking

A classifier specification and a deterministic scoring layer for the bookends
architecture: RME-7's seven dynamic objects typed against Communicative
Pragmatism's six-layer epistemic interface.

The design rule is that **the model classifies and the program calculates.**
Nothing here calls a language model. It renders prompts for one to answer and
then ingests, validates, seals and measures what comes back. Keeping generation
outside the program is what makes *responder is not classifier* structural
rather than procedural: two separate artifacts are ingested, and the ledger
refuses them if they name the same author.

---

## Maturity

**Nothing in this tree has met data.** The instrument is specified and now
built; the classifier is unvalidated; the typed subgraph is untested; the rater
study is unrun; the outer loop has no outcomes because it needs a time constant
nobody has waited out. What exists here are architectural rulings rendered as
executable constraints.

Runtime enforces this rather than stating it. Absent a validation record
discharging the `classifier` anchor, every report is stamped `COHERENCE_ONLY`.
A classifier built on the architecture's own assumptions measures its priors
rather than the model's behaviour, and a report that did not say so would be
internal recurrence wearing a lab coat.

### Anti-retroactivity is enforced pointwise, not globally

Three separate claims, and only the first two are true.

**Pointwise enforcement — yes.** Six back-referencing mechanisms are checked
against the record they characterise rather than believed:

| Field | Checked against |
|---|---|
| `standing_since` | the referenced commitment's *content*, not its existence |
| `commitment_ref` | a sealed response already in the chain |
| `declared_order` | the classified operator sequence, by order fidelity |
| `self_classification` | the bridge classifier's independent typing |
| `ontology_version` | the ontology the engine actually loaded |
| `prior_state` | specified as replay-verified; unbuilt with the ruling layer |

**The general rule — yes, as a derived constraint.** *A current declaration may
characterise a prior record; it may not constitute or silently rewrite one.* It
was not declared at the outset. It emerged from five concrete failures in
sequence — version string, standing custody, prior state, validation scope,
anchor decidedness — each asking the same question: can the present record make
itself true by describing the past differently.

**Global enforcement — no.** Nothing in this tree would catch a seventh site. A
field added tomorrow that characterises prior state fails no test, fires no
check, and enters exactly as `ontology_version` did: present, plausible, and
consulted by nobody. The rule is a habit plus six specific tests.

A registry of back-referencing fields would establish that *every known* such
field has a verifier. It could not establish that *every* such field is known —
and the registry would itself be a maintained declaration about the
architecture, subject to the same discovery failure it was introduced to fix.
So the gap is recorded rather than papered over. An instrument built around
what the record can establish must not claim an invariant its own test surface
cannot detect violations of.

---

## Layout

```
ontology/     cp_layers.yaml, rme7_objects.yaml   -- rendered into prompts
              typing_rules.yaml                   -- WITHHELD from prompts
prompts/      pole_classifier.md (Mode A), bridge_classifier.md (Mode B)
schemas/      the JSON shape of each mode's output
engine/       deterministic scoring; no model calls, no dependencies
              claim.py holds the licensing ladder every headline result carries
drills/       layer_sweep, dynamic_sweep, order_sweep -- runnable today
bt.py         the command line
```

The ontology is versioned independently of the classifier, so a corpus can be
re-scored under a revised subgraph without touching the student responses
underneath it. That guarantee depends on knowing which subgraph each
classification was produced under, so `ingest` refuses a record whose
`ontology_version` differs from the loaded ontology, and refuses one that
carries no version at all. `validate()` takes `ontology_version` as a
keyword-only required argument: an artifact cannot be admitted without its
provenance being checked, and an optional argument is one a caller can forget.

```sh
./run_tests.sh                 # 139 tests, stdlib only
python3 bt.py check            # ontology loads; prompts leak no predictions
python3 bt.py render bridge    # the prompt, with the ontology interpolated
python3 bt.py drill layer_sweep
python3 bt.py seal LEDGER poles.json
python3 bt.py ingest LEDGER --mode bridge --commitment HASH \
        --response r.txt --classification c.json --responder A --classifier B
python3 bt.py verify LEDGER
python3 bt.py passage LEDGER   # provenance query over sealed commitments
python3 bt.py report runs.json --ledger LEDGER
```

---

## Five departures from the specification

**1. The typed subgraph is withheld from the classifier.** This is the
load-bearing one. The draft prompt carried *"do not assume that every dynamic
object can be instantiated within every layer"*, which is a soft form of
telling the classifier the answer. A classifier that knows which pairings are
predicted void cannot report one — and the empty-cell test, which the empirical
order puts *before* the width test precisely because prohibitions are sharper
than gradients, becomes a test that cannot fail. That is the defect for which
the sentence test was rejected, reappearing at the instrument layer where it
would be invisible.

So the predictions live in `ontology/typing_rules.yaml`, are never rendered,
and are applied afterwards by `engine/typing_rules.py`. A violation is recorded
as a datum, never prevented and never repaired. `bt.py check` proves the
withholding on every run, and a test asserts it.

**2. Δ is not a scalar, and the code refuses to make it one.** There is no
metric here. The epistemic axis is a dependency order — displacement along it is
ordinal and signed, and the L5/L6 firewall makes one of its five steps
incommensurable with the other four. The dynamic axis is an unordered set of
three kinds of object, so only *same / within-type / cross-type* is available;
J♯ is not nearer to Σ than to F. Δ is therefore a typed pair, and
`float()`, `int()` and `+` on it raise `NotScalarError`. Δ was already sealed as
a lossy projection of the synthesis; collapsing it to one number makes the
projection worse and hides that it happened.

**3. `typing.status` is a κ act, so it is recorded as a proposal.** The draft
schema had the classifier return a well-typed / ill-typed verdict, which is
admissibility — the human's. The field is kept (the verdict is useful) but named
`typing_proposal`, and the student's adjudication is a separate ledger record.
The engine reads both and never collapses them. This is also where planted
misclassification enters.

**4. Confidence is ordinal, not a float.** `clear | contested | uncertain`. An
LLM-emitted 0.73 would be averaged downstream and become a measurement it cannot
support. The architecture's own answer to uncertainty is resampling — dispersion
is measured by resampling the classifier, not by asking it.

**5. Planting is engine-side, and contest rate is reported alongside accuracy.**
The plant is made by the program after classification and before the student
sees the result, with ground truth sealed at plant time so nobody is scored
against a truth written after their contest. And accuracy alone is not the
metric: a student who never contests is not adjudicating whatever their
differential shows, so a zero contest rate is flagged regardless of the other
numbers.

---

## Adopted after review: γ is measured, not recognised

κ is observationally **local** — a classifier can decide admissible or
inadmissible from the object in front of it. γ is observationally
**historical**: a commutator is a property of two trajectories and their
ordering, so no single classification can carry it. Asking a classifier to
*recognise* γ was the wrong abstraction, and it was the source of this tree's
declared leak.

So the classifier now types the constituent operations, one `observed` entry
per step, and never meets the commutator concept. `engine/trajectory.py`
composes the invariant afterwards. γ's `definition`, `commutator_of` and
`computed_from` join the withheld fields and no longer reach the prompt.

Three things fell out of the decomposition that were not visible before it.

**The endpoint is a place, not a move.** A cell is an operator instantiated
within a layer: the operator is *how you moved*, the layer is *where you are*.
Arm A necessarily ends with the second declared operator and arm B with the
other one, so an operator-valued endpoint would make every pair noncommute by
construction — a measurement of the experimental design rather than of the
operators. Endpoints are read off layers; routes are reported separately,
because two orders trivially differ in the middle and reading that as
noncommutation would find order dependence everywhere.

**Order fidelity became checkable.** A run that declared G♯ then G̃♯ but was
classified the other way round did not perform the order it declared. Those
trajectories are excluded and counted, never averaged in.

**Observation and inference are separate fields.** The endpoint comparison is
never rendered as though it were already the invariant. `observation` says
*endpoint change observed under the tested G♯/G̃♯ conditions*; `inference` says
*supports γ ≠ 0 for the tested pair under the conditions tested*, and exists
only when the pair is the defined commutator. The general arm can establish
order dependence; it cannot establish γ, and with the qualifier dropped a
positive there reads as a γ result.

**The two levels cross-check each other.** γ stays in the classifier's
vocabulary as a bare label, so a cell-level γ remains reportable and the void
conjecture remains falsifiable. A raw count of those labels under-determines
the reading, though — a classifier tracking the ordering and a classifier
repeating a habit produce the same count — so the labels are profiled by arm
and `cross_check` refuses a bare integer:

| | no cell-level γ | γ labels symmetric across orders | γ labels covary with order |
|---|---|---|---|
| **order effect** | `path_level_supported` — γ has a referent one level up; cell ontology left unresolved | `label_habit` — labels indifferent to ordering, alongside an endpoint effect they are not detecting | `classifier_relocated` — tracking the phenomenon, assigning it to the wrong level; a live ontology question |
| **no order effect** | `gamma_inert` — the path-level proposal loses its only support | `label_without_operation` — typing on the name rather than the operation | `route_sensitive_labelling` — labels track the route while endpoints agree |

The right-hand column is the refinement: `classifier_relocated` is not only a
classifier defect. If the labels covary with ordering while the engine finds a
genuine endpoint effect, γ may not be path-level in the way hypothesised, and
the architecture should be able to discover that. The bottom-right cell fell
out of the endpoint/route split rather than being anticipated — labels tracking
the route while endpoints agree is the same conflation the split exists to
prevent, showing up in the classifier instead of the measure.

**This is not a clean win, and the code says so.** Removing the definition
trades one bias for another: with it present the classifier was told most of
what the void conjecture predicts; with it absent the classifier is likelier to
miss a genuine cell-level γ, which biases toward *confirming* the conjecture.
Neither direction is neutral. The path-level measurement carries the γ claim
now; the cell-level test is demoted to a weak cross-check, and the caveat rides
along with every reading the module returns.

The resolution limit is not lifted either, only relocated. If the classifier
cannot separate G♯ from G̃♯ in prose — they differ by a property of the flow, not
by what the sentence describes — then the fidelity check passes or fails
arbitrarily and the arms are not what they claim. Excluded-trajectory counts
are the first thing to read, before any endpoint comparison.

---

## The passage audit

Composition along the dynamic axis is measured by `trajectory.py`. Passage along
the epistemic one — whether satisfaction of Cᵢ was illicitly promoted into
authorisation of O₍ᵢ₊₁₎ — is measured by `passage.py`. A run can classify every
output's layer correctly and still treat a successful L4 derivation as warrant
for an L5 standard. Trajectory analysis sees *where the process went*; this sees
*what authority it claimed to acquire by getting there*.

**Two candidate tests, both rejected.**

*Citation.* Ask whether the justification for O₍ᵢ₊₁₎ cites Cᵢ as its warrant.
Rejected: silent promotion is the characteristic form. An audit that fires on
citation catches the honest violations and misses the ones the firewall exists
for.

*Content dependence.* Substitute a different Cᵢ and see whether O₍ᵢ₊₁₎ shifts.
Rejected: Cᵢ can legitimately inform what is declared next — it is the same
inquiry — and the constraint is about authority, not relevance. A divergence
test cannot tell the two apart, so this over-fires.

**Retained: a provenance query.** The passage constraint is not a semantic
property of the resulting opening. It is a property of the opening's *custody*,
and custody is an ordering fact the hash chain already records. So this is not a
classifier and not a new measurement channel — it is a typed read over records
that already exist. `Ledger.commit()` now accepts a layer-addressable `openings`
list (`opening_id`, `layer`, `custody_mode`, `standing_since`,
`triggered_reopen`), and `Ledger.closure()` records what the audit compares
against.

| State | Condition | Positive finding |
|---|---|---|
| `protected` | first recorded custody precedes the closure | — |
| `standing_protected` | standing since an earlier commitment that predates the closure **and contains this opening** | — |
| `standing_claimed_unsupported` | the named anchor does not contain this opening | **yes — L2** |
| `unprotected_by_record` | first recorded custody follows the closure | **yes — L1** |
| `unresolved` | custody claimed from an origin outside this record | — |

**The hole the specification had.** `standing_since` is a field whose entire
function is to claim earlier custody. Checking only that the anchor exists and
predates the closure makes it a backdating primitive: any opening can name any
earlier commitment and inherit its protection. The anchor is therefore resolved
**by content** — the audit reads the referenced commitment's payload and
confirms the opening is actually in it. A pointer to a real commitment that
lacks the opening is not `unprotected`; it is a distinct and more serious
finding, a claim of earlier custody the record itself contradicts. That is a
Layer 2 failure (a commitment misrepresented), not a Layer 1 one, and the
four-state table had no slot for it.

Whether the anchor contains the opening is deliberately *not* checked at commit
time. Refusing it at write time would make the retroactive claim unrecordable,
and the audit exists to report such claims rather than to be spared them. A
forward-pointing anchor is refused, because that is malformed rather than false.

**`triggered_reopen` voids inherited protection.** A reopened opening is a fresh
declaration and is judged on its own seal time; otherwise "standing" would
license every later re-declaration.

**Only an origin outside the record is `unresolved`.** The first declaration of
a standing opening *is* its origin, so it is judged on its own seal time like
any other. An earlier draft marked it unresolved, which left every standing
opening permanently stuck — the failure mode where the audit's commonest output
is "cannot say." `unresolved` now means specifically that the provenance needed
to distinguish legitimate standing custody from a retrospective claim was not
preserved, which makes it a diagnostic of the ledger rather than noise.

**Two reports, never mixed.** Findings are about the run; provenance quality is
about the ledger's bookkeeping. An `unresolved` rate reported in the same column
as an `unprotected` rate invites the first to be read as the second.

**No state is a finding of promotion.** `unprotected_by_record` means the record
does not protect the opening, not that the opening was promoted — it may have
been held all along and written down late. And the verdict is forensic, never
scored: *"O₄ was sealed after C₃ in three of seven runs"* is a record, while
*"your passage discipline is 6/10"* supplies a criterion, which is Layer 5, and
hands custody of Cᵢ to the instrument.

> **`NOT_VIOLATED` means the record does not establish a violation. It does not
> mean the record establishes compliance.**

### The coverage confound

An empty findings block from an impoverished record and an empty findings block
from a disciplined run are not the same result, and the difference cannot be
left to be inferred from a count. So the audit's top-level outcome is
three-valued:

| State | Meaning |
|---|---|
| `CLEAN` | Every boundary the record raises was examined; no positive finding. The only state readable as "the examined record contains no finding". |
| `FINDINGS` | One or more positive findings. Under partial coverage the findings stand and the unexamined boundaries are *not* thereby clean. |
| `UNEXAMINED` | Not enough layer-addressable commitments and closures to establish that the raised relations were examined. Says nothing about passage discipline, in either direction. |

Partial coverage cannot reach `CLEAN`: a forensic audit cannot certify the
absence of a finding in a region it did not examine. This closes the Goodhart
surface at the ledger layer — declining to commit openings no longer buys a
clean audit, it buys `UNEXAMINED`.

**Where the required set comes from, and why it is not a norm.** Saying
"required: 5" needs a definition of which relations *should* have been examined,
and taking that from what a properly conducted run ought to have contained would
be a normative judgement about what the user should have declared — the thing
this audit is not authorised to make. The required set is instead **induced by
the record**: a boundary (Cᵢ, O₍ᵢ₊₁₎) is *raised* when the record itself
contains a closure at i or an opening at i+1. The record's own assertion that a
layer was in play is what makes the passage question live there. A quiet run
raises nothing and is reported as examining nothing, which is accurate rather
than clean.

Coverage is **boundary-granular**, deliberately distinct from `pairs_examined`
in the findings block: several closures at layer i against several openings at
i+1 produce many comparisons across one boundary. (The fields are
`required_boundaries` / `examined_boundaries` rather than `required_pairs` /
`examined_pairs`, to keep the two granularities from being read as one number.)

**Still held, and deliberately.** *Ledger completeness* — whether the record
contains what a properly conducted run should have produced — is not built. The
coverage report says what the record represents and does not interpret its
absence; a completeness judgement would say "you failed to declare Oᵢ", which is
normative and unauthorised. The two must not be merged.

---

## Claim licensing: computability is not claimability

Every refusal in this tree is an epistemic gate — the quantity cannot be
produced — with one exception. `COHERENCE_ONLY` was a *label attached to a
number that stays perfectly quotable once the label is dropped*: result →
copied → stamp omitted → figure cited as evidence. The engine had constrained
its own output and could not constrain downstream quotation.

`engine/claim.py` closes that without refusing the calculation, by making
evidentiary status part of the result's **identity**. A measurement without
validation provenance is not an empirical result with a disclaimer; it is a
different type of result, and it is a different type here.

**Four claim levels, as a ladder.** Each names what becomes unavailable, which
a confidence scalar cannot do — a scalar flattens *cannot be computed* and
*computed but not externally validated* into one number, and those are not
degrees of the same thing.

| Level | Licenses |
|---|---|
| `computable` | the quantity can be produced at all |
| `inferential` | a conclusion can be drawn from it |
| `evidential` | it can be cited as evidence about the architecture |
| `generalisable` | its absence extends beyond the region examined |

Withholding a level withholds everything above it: nothing is inferred from a
quantity that was never computed.

**This generalises something already in the tree.** The γ result already
separated *endpoint change observed under stated conditions* from *supports
γ ≠ 0 for the tested pair*. That is exactly the computable/inferential rung, and
the general operator arm is a measurement licensed at the first and withheld at
the second. The existing refusals map onto the ladder without being restated:

| Failure | Level withheld |
|---|---|
| missing null baseline; missing single-pole arms; no order-faithful trajectories | `computable` |
| operator pair is not the defined commutator | `inferential` |
| no classifier-validation record | `evidential` |
| partial passage coverage; unresolved provenance | `generalisable` |

**What makes it a gate rather than a louder warning.** `float()` and `int()` on
a `Measurement` raise. So does `f"{m:.2f}"` — a format spec is the commonest way
a value is lifted out of its context and into a sentence, so specs are ignored
and `str()` always carries the status. The value is reachable only by naming
what is being claimed: `.computed` for the raw calculation, `.as_evidence()`
which refuses unless licensed. JSON serialisation carries `licensed` and
`withheld` rather than a bare number.

**The typed surface is the whole surface.** Seven headline quantities — C, V,
interaction, γ, passage, recognition, contest rate — are `Measurement` objects,
and the underlying computations live under `report()["raw"]` rather than beside
them. A parallel untyped view would have left the ladder optional: anything
reading `rep["dispersion"]["normalized_entropy"]` would get a bare float without
doing anything unusual. `raw` stays reachable, because the ladder types what a
result licenses rather than hiding the arithmetic, but reaching for it is now as
explicit an act as `.computed`. `typing_audit`, `edge`, `ablation` and
`predicted_blocks` stay at the top level: they are structured diagnostics, and
there is no single number in them to promote.

**Claim level and validation dependency are orthogonal.** A single `validated`
boolean collapsed a dependency graph into one bit: only four of the seven
quantities are built on classified cells, so gating all seven on one switch was
wrong in both directions — it withheld from three for a reason that does not
apply to them, and the moment a free-sorting rater study landed it would have
licensed a passage claim on the strength of evidence about whether naive raters
can separate L4 from L5. Each quantity now declares the anchor it depends on,
and the gate asks whether *that* anchor is discharged.

| Quantity | Produced from | Anchor |
|---|---|---|
| C, V, interaction | classified cells | `classifier` |
| γ | classified cells **and ordered trajectories** | `classifier` + `classifier_target_granularity` |
| passage | ledger provenance | `provenance_integrity` |
| recognition, contest rate | engine-side plants | `plant_contest_integrity` |

**Anchors are three-valued, and the third state is the point.** `satisfied` — a
record discharging it exists. `unsatisfied` — no such record, and it is settled
what one would be. `undecided` — the architecture has not ruled on what would
discharge it. The third is a missing *criterion*, not a missing record, so
`Ledger.validation()` refuses a record naming an undecided anchor: accepting one
would answer an open architectural question by bookkeeping. Validation records
therefore carry both `anchor` (the external source) and `validates` (the
dependency discharged); without the second the record is semantically
incomplete.

**γ's second anchor is an anchor whose own existence is the question.** A
classifier could be excellent at typing L4 against L5 and G♯ against G̃♯ as
independent labels while being poor at *G♯ then G̃♯* against *G̃♯ then G♯* as a
sequence. Order fidelity already shows the distinction matters operationally,
but that does not establish it is a separate *validation target*. Leaving γ on
`classifier` alone would have answered that in the affirmative by structure — a
cell-level rater study would have licensed γ by inheritance. Requiring an
undecided anchor decides nothing and keeps the question live; if it resolves one
way the anchor merges back into `classifier`, if the other it acquires its own
criterion.

Three anchors are currently undecided, and every open question is held in
`engine/anchor.py` rather than defaulted. For passage: *the record contains X
and the chain establishes X preceded Y* may be settled by an internally
verifiable chain, while *this shows the passage constraint is correctly
implemented and meaningful* is a larger claim, and nothing has ruled on whether
the first is sufficient for the second. For Channel 2: the rates are exactly
computable from the engine's own plant records, but whether a synthetic
substitution elicits the same adjudicative act a real misclassification would is
a separate question.

It does **not** stop a reader copying a figure out by hand. What it removes is
the silent path.

---

## What the engine refuses

Refusals are executable, not documentary — `scoring.report` returns them and
`scoring.render` prints them under *Not reported, by ruling*.

| Refused | Because |
|---|---|
| adequacy score | Closure custody. An automated adequacy score selects the criterion by which the output it measures is judged. |
| retention *rate* | Rewards keeping more or fewer bridges regardless of quality. Calibration is the measurable quantity, and it is longitudinal. |
| composite score | The quantities are not commensurable; their sum has no unit. |
| scalar Δ | No metric. See departure 2. |
| middle-width conclusions | Interpretive and untested; withheld from the classifier and not reported until the classifier is validated. |
| adjudicating a typing violation | Bad typing and bad classifier are not separable from inside the system. |
| C without a null baseline | C *is* divergence from P(Y│∅). Without the null run, any number would be the model's default behaviour reported as the student's contribution. |
| interaction without single-pole arms | Without them a bridge cannot be told from the model following one pole — and following one pole is exactly what produces a large displacement. |
| a classifier-emitted γ as a γ measurement | γ is a property of two trajectories and their ordering. A cell-level γ is an observation; it is never promoted. |
| the γ *inference* for a non-defined operator pair | γ *is* [G♯, G̃♯]. Any other pair measures order dependence, and treating every noncommutativity result as evidence for one particular commutator is the mistake the arms are separated to avoid. The observation is still reported; only the inference is withheld. |
| γ from arms with no order-faithful trajectories | A run that did not perform the order it declared cannot measure the effect of that order. |
| a cross-check from a bare γ label count | The count cannot separate a classifier tracking the ordering from one repeating a label, and those are different findings. `cross_check` raises on an integer. |
| a clean passage reading from partial coverage | A forensic audit cannot certify the absence of a finding in a region it did not examine. |
| ingesting a classification produced under another ontology version | A version string is a declaration about history, not history; it cannot make an earlier classification belong to the current ontology. Hard refusal at ingest — reclassify or exclude, never relabel. The stored record keeps the version it claimed. |

Two further guards sit in the ledger. An outcome record must name an external
source: if the student decides which retained bridges failed, the loop
calibrates a judgement against later judgements by the same party. And a
response record is refused unless the commitment it references is already
sealed earlier in the chain, because a retrofitted transcript and a genuine one
look identical.

---

## What is runnable today

The three drills, none of which needs a validated classifier, a rater panel, a
null baseline, or a settled grid count.

- **`layer_sweep`** — hold the content fixed, vary the layer. One sentence, six
  operations. Tests the per-layer result directly.
- **`dynamic_sweep`** — hold the layer fixed, vary the dynamic object. Tests
  whether the 30-cell operator block is uniform. κ and γ are run in *separate
  arms*, not as a sixth and seventh operator: running them in the operator arm
  would presuppose the homogeneity the drill exists to check. κ's arm expects
  rejection verdicts; γ's arm expects failure to construct, and failure is the
  datum.
- **`order_sweep`** — hold the layer fixed, vary the order of composition. The
  only drill that can produce γ evidence, and the only one whose negative result
  is informative in a specific direction: if order never changes the output, γ
  is not merely unaddressable at cell level, it is inert under the conditions
  tested.

The order sweep separates a **commutator arm** (G♯ then G̃♯ against G̃♯ then G♯ —
γ is *defined* as [G♯, G̃♯], so that pair and only that pair tests γ as defined)
from a **general arm** with other operator pairs. A positive result on the
general arm is order dependence, not a γ result, and conflating them would read
as confirmation.

---

## Known weaknesses, declared here rather than discovered later

**The γ cross-check is the softest test in the tree**, for the reason given
above: removing the definition biases toward confirming the void conjecture
just as including it biased toward the classifier knowing the answer. The
path-level measurement is sounder than the cell-level one, and neither is
anchored.

**Empty-cell tests are not anchor-free.** When an output lands in a cell the
subgraph types as void, *bad typing* and *bad classifier* are not separable from
inside the system. The engine records the collision and does not adjudicate it.
Naive human raters remain the only anchor identified, and they are not in this
program.

**Measuring interaction in grid coordinates is the use the grid is qualified
for**, and only that use. Nothing about the grid is under test in the
interaction measurement — the claim is that distributions diverge — and the
grid's virtue there is that it does *not* reproduce the model's ambient
ontology, which an embedding metric would. Width claims are a different matter
and are refused.

**Both path structures are now measured, neither is anchored.** `trajectory.py`
takes composition along the dynamic axis and `passage.py` takes passage along
the epistemic one. Neither has an external anchor, and the passage audit's
verdicts are only as good as the discipline of the ledger it reads.

**Any visualisation of this space must be graph-based, not a heatmap.** Δ is
partially ordered, not metric, and a heatmap irresistibly suggests Euclidean
geometry — adjacent cells reading as near, colour gradients reading as
distance. That would reintroduce, in the display layer, exactly the metric the
engine refuses to assert. Recorded here because it is the kind of constraint
the first person to build a UI would violate without noticing.

---

## Ledger

| Item | Status |
|---|---|
| Ontology, prompts, schemas, engine, drills, CLI | Built, tested, unexercised on real responses |
| Predictions withheld from the classifier | Enforced and asserted |
| Commit-before-run; responder ≠ classifier; external outcomes | Enforced by the ledger |
| Δ as a typed pair refusing scalarisation | Enforced |
| Σ correction: dispersion scored against predicted level | Enforced — no call signature scores against an absolute floor |
| Interaction as the definition of synthesis | Implemented; necessary, not sufficient for value |
| Pairwise ablation with a constraint cap | Implemented; the cap binds on the declaration |
| Channel 2 planted errors | Implemented engine-side; contest rate reported alongside accuracy |
| γ composed by the engine from operator labels | Implemented; commutator withheld from the prompt |
| Order fidelity per trajectory | Enforced; unfaithful runs excluded and counted |
| Observation / inference kept apart in the γ result | Enforced; no code path renders a bare "γ ≠ 0" |
| Cell/path cross-check, 2×3 with relocation profiling | Implemented; carries the bias caveat with every reading; refuses a bare count |
| Passage audit | Implemented; five states, two of them positive findings at different layers |
| Three-valued audit state (CLEAN / FINDINGS / UNEXAMINED) | Enforced; partial coverage cannot reach CLEAN |
| Required set induced by the record, not by a norm | Enforced |
| Ledger completeness | **Held.** Would be a normative judgement the audit is not authorised to make |
| Anti-retroactivity, pointwise | Enforced at six identified sites |
| Anti-retroactivity, globally | **Absent.** No mechanism discovers a seventh site |
| Constitutional ruling layer | **Unbuilt.** Blocked on the plurality question below |
| Plurality of custodians: scope and conflict rule of a ruling | **Open.** Global, lineage-scoped or community-scoped; contradiction, fork or differing scope. Not derivable — the custody model has only ever represented one answerable party |
| Entrenchment: the rule naming who may append rulings is not itself rulable | Settled — otherwise the chain amends its own amendment rule |
| Claim licensing ladder | Implemented; headline results are typed, not numbers with a warning |
| `COHERENCE_ONLY` as a gate rather than a label | Closed for the silent path; a reader copying a figure by hand is still outside the instrument |
| Every headline quantity typed; raw computations namespaced | Enforced — no quotable number sits outside the ladder |
| Validation dependency is quantity-specific | Enforced; global validation status rejected as a licensing mechanism |
| Validation records name what they discharge | Enforced; `validates` is required |
| Is internally verifiable provenance enough for `passage` to reach `evidential`? | **Open.** Held as an undecided anchor; no record can close it |
| Does a synthetic plant elicit the adjudicative act a real misclassification would? | **Open.** Held as an undecided anchor |
| Is sequence-faithful classification a second validation target, or the same one? | **Open.** Held as an undecided anchor; γ requires it, so no cell-level study licenses γ by inheritance |
| `standing_since` resolved by content, not pointer | Enforced — otherwise the field is a backdating primitive |
| Passage findings vs provenance quality | Reported separately |
| Classifier validation | **Absent.** Every report is stamped `COHERENCE_ONLY`. |
| Middle-width gradient | Withheld and unreported |
| Grid count (28 vs 42) | Still blocked. Nothing here needs it: the blocks are reported separately and never summed |
| Retention calibration | Records exist (`outcome`); no data, and none for months by construction |
