"""Assembling a report -- and the things this program will not report.

The refusals are executable rather than documentary. Each one corresponds to a
ruling: an adequacy score would be the instrument selecting the criterion by
which the model's output is judged, which is closure custody, held by the
student. A retention *rate* incentivises keeping more or fewer bridges
regardless of quality. A composite bookending score has no unit.

The coherence gate is the other half. Absent a validation record from an anchor
external to the architecture, every interpretive line is stamped
COHERENCE_ONLY, because a classifier built on the architecture's own
assumptions measures its priors rather than the model's behaviour. Internal
recurrence wearing a lab coat is still internal recurrence.
"""

from __future__ import annotations

from . import ablation, dispersion, distance, divergence, typing_rules

REFUSALS = {
    "adequacy_score": (
        "Adequacy is a closure act. An automated adequacy score would be the "
        "instrument selecting the criterion by which the output it measures is "
        "judged. Longitudinal only."
    ),
    "retention_rate": (
        "Retention rate rewards keeping more or fewer bridges regardless of "
        "quality. The measurable quantity is retention calibration: do kept "
        "bridges outperform discarded ones against later, externally sourced "
        "outcomes."
    ),
    "composite_score": (
        "No composite. The quantities are not commensurable and their sum has "
        "no unit."
    ),
    "scalar_delta": (
        "Delta is not a scalar. See engine/distance.py."
    ),
    "middle_width": (
        "The middle-width gradient is interpretive and untested. It is not "
        "reported from this instrument at all until the classifier carries "
        "external validation, and it is withheld from the classifier meanwhile."
    ),
    "typing_adjudication": (
        "A cell landing where the subgraph predicts void is recorded, not "
        "adjudicated. Bad typing and bad classifier are not separable from "
        "inside the system."
    ),
}

COHERENCE_STAMP = (
    "COHERENCE_ONLY -- no classifier-validation record in this ledger. These "
    "figures describe what this classifier did. They are not evidence about "
    "the architecture, and may not be cited as corroboration."
)


def report(*, ontology, rules, ledger=None, input_cells=(), output_samples=(),
           null_samples=(), declared_objects=(), interaction_arms=None,
           ablation_arms=None, planted_rounds=None) -> dict:
    """Assemble everything that is currently well-founded, and nothing else."""
    validated = bool(ledger and ledger.has_validation())

    samples = [divergence.outcome(s) for s in output_samples]
    nulls = [divergence.outcome(s) for s in null_samples]

    observed_cells = [c for s in output_samples for c in s]
    audit = typing_rules.audit(observed_cells, ontology, rules)

    edge = distance.edge_summary(ontology, input_cells, _modal_cells(samples)) if input_cells else None

    measured = dispersion.dispersion(samples)
    predicted = dispersion.predicted_level(declared_objects, ontology)
    assessed = dispersion.assess(measured, predicted)

    out = {
        "validated": validated,
        "stamp": None if validated else COHERENCE_STAMP,
        "ontology_version": ontology.version,
        "typing_rules_version": rules.version,
        "predicted_blocks": typing_rules.predicted_blocks(ontology, rules),
        "typing_audit": {
            "counts": audit["counts"],
            "violations": [
                {"cell": str(v.cell), "rule": v.rule_id, "rule_status": v.rule_status,
                 "detail": v.detail}
                for v in audit["violations"]
            ],
            "note": audit["note"],
        },
        "edge": edge,
        "dispersion": assessed,
        "constraint_strength": divergence.constraint_strength(samples, nulls),
        "refusals": dict(REFUSALS),
    }

    if edge is not None:
        disp = "both" if edge["any_displacement"] else "none"
        out["quadrant"] = dispersion.quadrant(disp, assessed)

    if interaction_arms:
        out["interaction"] = divergence.interaction(
            [divergence.outcome(s) for s in interaction_arms["AB"]],
            [divergence.outcome(s) for s in interaction_arms["A"]],
            [divergence.outcome(s) for s in interaction_arms["B"]],
        )
    else:
        out["interaction"] = {
            "refused": True,
            "reason": (
                "Interaction needs three arms -- both poles, and each pole "
                "alone. Without the single-pole arms there is no way to tell a "
                "bridge from the model following one pole, and a large "
                "displacement is exactly what following one pole produces."
            ),
        }

    if ablation_arms:
        out["ablation"] = ablation.profile(
            samples,
            {k: [divergence.outcome(s) for s in v] for k, v in ablation_arms.get("single", {}).items()},
            {k: [divergence.outcome(s) for s in v] for k, v in ablation_arms.get("pairs", {}).items()} or None,
        )

    if planted_rounds is not None:
        from . import planted
        out["channel_2"] = planted.score(planted_rounds)
    else:
        out["channel_2"] = {
            "refused": True,
            "reason": (
                "No planted rounds. Channel 2 is the only mechanic that can "
                "observe adjudicative decay; without it a session of pure "
                "acceptance reads as excellent play."
            ),
        }

    return out


def _modal_cells(samples):
    """The most frequent outcome across resamples, as a list of cells."""
    if not samples:
        return []
    dist = divergence.distribution(samples)
    best = max(dist.items(), key=lambda kv: (kv[1], sorted(str(c) for c in kv[0])))
    return list(best[0])


def render(rep: dict) -> str:
    lines = []
    if rep.get("stamp"):
        lines += ["=" * 72, rep["stamp"], "=" * 72, ""]
    lines.append(f"ontology {rep['ontology_version']}  typing-rules {rep['typing_rules_version']}")
    lines.append("")

    blocks = rep["predicted_blocks"]
    lines.append("Predicted subgraph (blocks are not summed):")
    for name in ("operator_block", "indicator_row", "invariant_row"):
        b = blocks[name]
        lines.append(f"  {name:16s} {b['cells']:>3} cells  relation={b['relation']:<17s} [{b['status']}]")
    lines.append(f"  total: refused -- {blocks['total_refused_because']}")
    lines.append("")

    audit = rep["typing_audit"]
    lines.append(f"Typing audit: {audit['counts']}")
    for v in audit["violations"]:
        lines.append(f"  ! {v['cell']} contradicts {v['rule']} [{v['rule_status']}]")
    if audit["violations"]:
        lines.append(f"  {audit['note']}")
    lines.append("")

    if rep.get("edge"):
        lines.append("Edge:")
        for d in rep["edge"]["pairs"]:
            lines.append(f"  {d}")
        lines.append(f"  {rep['edge']['caveat']}")
        lines.append("")

    c = rep["constraint_strength"]
    if c.get("refused"):
        lines.append(f"C:          REFUSED -- {c['reason']}")
    else:
        lines.append(f"C:          tv={c['tv']:.3f} p={c['p']:.4f} -- {c['reading']}")

    disp = rep["dispersion"]
    lines.append(f"Dispersion: {disp.get('verdict')} (band {disp.get('band')}, predicted {disp.get('predicted')})")
    if "quadrant" in rep:
        lines.append(f"Quadrant:   {rep['quadrant']['cell']} -- {rep['quadrant'].get('gloss','')}")
    lines.append("")

    inter = rep["interaction"]
    if inter.get("refused"):
        lines.append(f"Interaction: REFUSED -- {inter['reason']}")
    else:
        lines.append(f"Interaction: {inter['verdict']}"
                     + (f" (followed pole {inter['followed_pole']})" if inter["followed_pole"] else ""))
        lines.append(f"  {inter['sufficiency_note']}")
    lines.append("")

    ch2 = rep["channel_2"]
    if ch2.get("refused"):
        lines.append(f"Channel 2:  REFUSED -- {ch2['reason']}")
    else:
        lines.append(f"Channel 2:  recognition={ch2['recognition_accuracy']} "
                     f"false-acceptance={ch2['false_acceptance_rate']} contest-rate={ch2['contest_rate']}")
        for flag in ch2["flags"]:
            lines.append(f"  ! {flag}")
    lines.append("")

    lines.append("Not reported, by ruling:")
    for key, why in rep["refusals"].items():
        lines.append(f"  - {key}: {why}")
    return "\n".join(lines)
