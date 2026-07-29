"""Planted misclassification -- Channel 2, the practice-floor instrument.

Without planted errors a student can submit, receive a classification, accept
it, and score well. That is ratification theater with a scoreboard, and it
reads as excellent play in the transcript.

Two properties are structural rather than procedural here:

* The plant is made by this program, after classification and before the
  student sees the result. A classifier asked to plant its own errors is a
  system marking its own work.
* The ground truth goes into the sealed ledger at plant time, so a student
  cannot be scored against a truth that was written after their contest.

The metric is not accuracy alone. A student who never contests is not
adjudicating whatever their differential shows, so contest rate is reported
alongside and a zero contest rate is flagged regardless of the other numbers.
"""

from __future__ import annotations

import copy
import random

from .ontology import LAYER_IDS, RELATIONS

DEFAULT_RATE = 0.25
FIELDS = ("layer", "object", "relation")


def _alternatives(field: str, current, ontology) -> list:
    if field == "layer":
        return [x for x in LAYER_IDS if x != current]
    if field == "object":
        return [x for x in ontology.dynamics if x != current]
    return [x for x in RELATIONS if x not in (current, "uncertain", "none")]


def plant(classification: dict, ontology, seed: int, rate: float = DEFAULT_RATE):
    """Return (possibly mutated copy, truth record). Deterministic in ``seed``."""
    rng = random.Random(seed)
    truth = {"planted": False, "rate": rate, "seed": seed, "path": None,
             "field": None, "original": None, "substituted": None}

    observed = classification.get("observed") or []
    if not observed or rng.random() >= rate:
        return copy.deepcopy(classification), truth

    mutated = copy.deepcopy(classification)
    idx = rng.randrange(len(observed))
    candidates = [f for f in FIELDS if mutated["observed"][idx].get(f) not in (None, "none", "uncertain")]
    if not candidates:
        return copy.deepcopy(classification), truth

    field = rng.choice(candidates)
    current = mutated["observed"][idx][field]
    options = _alternatives(field, current, ontology)
    if not options:
        return copy.deepcopy(classification), truth

    substitute = rng.choice(options)
    mutated["observed"][idx][field] = substitute
    truth.update({
        "planted": True,
        "path": f"observed[{idx}].{field}",
        "field": field,
        "original": current,
        "substituted": substitute,
    })
    return mutated, truth


def score(rounds) -> dict:
    """``rounds``: dicts with keys planted, contested, contest_path, truth_path."""
    planted = [r for r in rounds if r["planted"]]
    clean = [r for r in rounds if not r["planted"]]

    caught = [r for r in planted if r["contested"] and r.get("contest_path") == r.get("truth_path")]
    contested_wrong_place = [r for r in planted if r["contested"] and r.get("contest_path") != r.get("truth_path")]
    accepted = [r for r in planted if not r["contested"]]
    false_contests = [r for r in clean if r["contested"]]
    contests = [r for r in rounds if r["contested"]]

    result = {
        "rounds": len(rounds),
        "planted": len(planted),
        "recognition_accuracy": (len(caught) / len(planted)) if planted else None,
        "located_wrong": len(contested_wrong_place),
        "false_acceptance_rate": (len(accepted) / len(planted)) if planted else None,
        "false_contest_rate": (len(false_contests) / len(clean)) if clean else None,
        "contest_rate": (len(contests) / len(rounds)) if rounds else None,
        "flags": [],
    }
    if rounds and not contests:
        result["flags"].append(
            "Never contested. Adjudicative competence is unobserved in this "
            "session whatever the other channel shows -- that is the failure "
            "the practice floor exists to detect."
        )
    if planted and result["recognition_accuracy"] == 0.0:
        result["flags"].append("No plant recognised.")
    if not planted:
        result["flags"].append(
            "No plants in this session. Channel 2 is unmeasured; recognition "
            "figures are absent rather than perfect."
        )
    return result
