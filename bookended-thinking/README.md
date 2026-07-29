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
./run_tests.sh                 # 51 tests, stdlib only
python3 bt.py check            # ontology loads; prompts leak no predictions
python3 bt.py render bridge    # the prompt, with the ontology interpolated
python3 bt.py drill layer_sweep
python3 bt.py seal LEDGER poles.json
python3 bt.py ingest LEDGER --mode bridge --commitment HASH \
        --response r.txt --classification c.json --responder A --classifier B
python3 bt.py verify LEDGER
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

**The γ arm is the softest test in the tree.** γ's definition — computed from
trajectories — is given to the classifier, because withholding it would leave
the classifier unable to recognise γ at all. That definition is already close to
the prediction under test, so the γ result is weaker evidence than the κ result,
where the withholding is clean.

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

**No drill measures a path structure.** A cell-level classifier is blind to
both passage along the epistemic axis and composition along the dynamic one.
The order sweep is a first approach to the second; nothing here touches the
first.

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
| Classifier validation | **Absent.** Every report is stamped `COHERENCE_ONLY`. |
| Middle-width gradient | Withheld and unreported |
| Grid count (28 vs 42) | Still blocked. Nothing here needs it: the blocks are reported separately and never summed |
| Retention calibration | Records exist (`outcome`); no data, and none for months by construction |
