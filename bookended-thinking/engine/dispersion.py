"""V (dispersion across resamples), scored against what the operators predict.

The outcome quadrant as originally drawn treats low variance as an absolute
target. It is not. Sigma is the slot through which genuinely new information
enters, and when Sigma is legitimately active high variance is *correct
behaviour*, which the uncorrected quadrant would misreport as vacancy.

So every function here requires the predicted level as an input. There is no
call signature that scores dispersion against an absolute floor.
"""

from __future__ import annotations

import math
from collections import Counter

from .divergence import distribution

HIGH_BAND = 0.66
LOW_BAND = 0.33


def dispersion(samples) -> dict:
    n = len(samples)
    if n == 0:
        return {"n": 0, "support": 0, "normalized_entropy": None, "mode_share": None}
    counts = Counter(samples)
    probs = [c / n for c in counts.values()]
    entropy = -sum(p * math.log(p) for p in probs if p > 0)
    ceiling = math.log(n) if n > 1 else 0.0
    return {
        "n": n,
        "support": len(counts),
        "normalized_entropy": (entropy / ceiling) if ceiling > 0 else 0.0,
        "mode_share": max(probs),
        "distribution": distribution(samples),
    }


def predicted_level(declared_objects, ontology) -> str:
    """High iff a declared operator predicts high dispersion (Sigma)."""
    for obj_id in declared_objects:
        dyn = ontology.dynamics.get(obj_id)
        if dyn is not None and dyn.predicts_high_dispersion:
            return "high"
    return "low"


def assess(measured: dict, predicted: str) -> dict:
    """Compare measured dispersion against the level the operators predict.

    Returns a comparison, never a grade. 'above_prediction' is not 'weak
    bookending' and 'below_prediction' is not 'strong bookending'.
    """
    value = measured.get("normalized_entropy")
    if value is None:
        return {"verdict": "undefined", "reason": "no samples"}
    band = "high" if value >= HIGH_BAND else ("low" if value <= LOW_BAND else "middle")
    if band == predicted:
        verdict = "consistent_with_prediction"
    elif predicted == "high" and band != "high":
        verdict = "below_prediction"
    elif predicted == "low" and band != "low":
        verdict = "above_prediction"
    else:
        verdict = "indeterminate_band"
    return {
        "normalized_entropy": value,
        "band": band,
        "predicted": predicted,
        "verdict": verdict,
        "note": (
            "Sigma is active: high dispersion is the predicted behaviour here, "
            "not a defect."
            if predicted == "high"
            else "No Sigma declared: low dispersion is the predicted behaviour here."
        ),
    }


def quadrant(displacement: str, assessment: dict) -> dict:
    """The outcome quadrant, Sigma-corrected.

    Note that the row axis is *displacement*, categorical, not a magnitude.
    Underspecification mimics tension -- a vague input yields a large apparent
    differential because the model must invent everything left unfixed -- and
    resampling is what separates the two, which is why the assessment is
    required rather than optional.
    """
    if assessment.get("verdict") in (None, "undefined"):
        return {"cell": "undefined", "reason": "dispersion not assessable"}

    moved = displacement != "none"
    excess = assessment["verdict"] == "above_prediction"

    if moved and not excess:
        cell = "strong_bookends"
        gloss = "constraints determined the space, the model filled it"
    elif moved and excess:
        cell = "vacancy"
        gloss = "input under-constrained; the model wandered into empty space"
    elif not moved and not excess:
        cell = "over_specification"
        gloss = "nothing was delegated"
    else:
        cell = "noise"
        gloss = "no displacement and more dispersion than predicted"

    return {
        "cell": cell,
        "gloss": gloss,
        "displacement": displacement,
        "dispersion": assessment,
        "caveat": (
            "Dispersion was scored against the level the declared operators "
            "predict, not against an absolute floor. A Sigma-active "
            "configuration is scored on whether dispersion falls at the "
            "predicted level."
        ),
    }
