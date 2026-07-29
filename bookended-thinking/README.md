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

Runtime enforces this rather than stating it. Absent a validation record from
an anchor external to the architecture, every report is stamped
`COHERENCE_ONLY`. A classifier built on the architecture's own assumptions
measures its priors rather than the model's behaviour, and a report that did
not say so would be internal recurrence wearing a lab coat.

---

## Layout

```
ontology/     cp_layers.yaml, rme7_objects.yaml   -- rendered into prompts
              typing_rules.yaml                   -- WITHHELD from prompts
prompts/      pole_classifier.md (Mode A), bridge_classifier.md (Mode B)
schemas/      the JSON shape of each mode's output
engine/       deterministic scoring; no model calls, no dependencies
drills/       layer_sweep, dynamic_sweep, order_sweep -- runnable today
bt.py         the command line
```

The ontology is versioned independently of the classifier, so a corpus can be
re-scored under a revised subgraph without touching the student responses
underneath it.

```sh
./run_tests.sh                 # 96 tests, stdlib only
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
| `standing_since` resolved by content, not pointer | Enforced — otherwise the field is a backdating primitive |
| Passage findings vs provenance quality | Reported separately |
| Classifier validation | **Absent.** Every report is stamped `COHERENCE_ONLY`. |
| Middle-width gradient | Withheld and unreported |
| Grid count (28 vs 42) | Still blocked. Nothing here needs it: the blocks are reported separately and never summed |
| Retention calibration | Records exist (`outcome`); no data, and none for months by construction |
