"""Validation anchors: what each quantity's evidential claim actually depends on.

A single ``validated`` boolean collapsed a dependency graph into one bit. Only
four of the seven headline quantities are built on classified cells; the passage
audit is a provenance query over the student's own commitments, and the Channel
2 rates come from engine-side plants. Gating all seven on one switch is wrong in
both directions -- it withholds from three quantities for a reason that does not
apply to them, and the moment a free-sorting rater study lands it would license a
passage claim on the strength of evidence about whether naive raters can separate
L4 from L5. Those are unrelated propositions.

So each quantity declares the anchor its evidential claim depends on, and the
gate asks whether *that* anchor is discharged rather than whether anything
anywhere has been validated.

**Anchors are three-valued, and the third state is the point.**

satisfied    a validation record discharging this anchor exists
unsatisfied  no such record exists, and it is settled what one would be
undecided    the architecture has not ruled on what would discharge it

``undecided`` is not a missing record. It is a missing *criterion*, and no
record can remedy it -- which is why ``Ledger.validation`` refuses a record
naming an undecided anchor. Defaulting such an anchor either way would answer
the open question by implementation, which is precisely the smuggling the
instrument exists to detect.
"""

from __future__ import annotations

from dataclasses import dataclass

from .claim import EVIDENTIAL

SATISFIED = "satisfied"
UNSATISFIED = "unsatisfied"
UNDECIDED = "undecided"

CLASSIFIER = "classifier"
PROVENANCE_INTEGRITY = "provenance_integrity"
PLANT_CONTEST_INTEGRITY = "plant_contest_integrity"


@dataclass(frozen=True)
class Anchor:
    id: str
    depends_on: str
    decided: bool
    discharged_by: str | None = None
    open_question: str | None = None


ANCHORS = {
    CLASSIFIER: Anchor(
        id=CLASSIFIER,
        depends_on="quantities computed from classified cells",
        decided=True,
        discharged_by=(
            "a validation record naming validates: classifier -- inter-rater "
            "agreement with judges naive to the architecture, or performance on "
            "held-out data typed independently, including adversarial examples "
            "built to expose keyword and stylistic shortcuts"
        ),
    ),
    PROVENANCE_INTEGRITY: Anchor(
        id=PROVENANCE_INTEGRITY,
        depends_on="the passage audit, a query over the student's own sealed record",
        decided=False,
        open_question=(
            "Two propositions have to be kept apart. 'The record contains X and "
            "the chain establishes X was committed before Y' may be settled by "
            "the record itself, since the hash chain is internally verifiable. "
            "'This shows the passage constraint is correctly implemented and "
            "meaningful' is a larger claim about the architecture. Whether an "
            "intact, internally verifiable ledger is sufficient for the first to "
            "count as evidence about the second is unruled, and the instrument "
            "may not settle it by defaulting."
        ),
    ),
    PLANT_CONTEST_INTEGRITY: Anchor(
        id=PLANT_CONTEST_INTEGRITY,
        depends_on="recognition and contest rate, computed from engine-side plants",
        decided=False,
        open_question=(
            "The engine knows what it planted, so the rates are computable "
            "exactly from its own records without any classifier. Whether the "
            "plant mechanism faithfully represents the intended substitution "
            "experiment -- that a synthetic swap elicits the same adjudicative "
            "act a real misclassification would -- is a separate question, and "
            "nothing has ruled on what would answer it."
        ),
    ),
}


class UnknownAnchor(ValueError):
    pass


def get(anchor_id: str) -> Anchor:
    try:
        return ANCHORS[anchor_id]
    except KeyError:
        raise UnknownAnchor(
            f"unknown validation anchor {anchor_id!r}; known: {sorted(ANCHORS)}"
        ) from None


def status(anchor_id: str, ledger) -> tuple:
    """Return (state, reason) for one anchor against a ledger."""
    entry = get(anchor_id)
    if not entry.decided:
        return UNDECIDED, (
            f"anchor {entry.id!r} is undecided: {entry.open_question}"
        )
    if ledger is not None and ledger.validations_for(anchor_id):
        return SATISFIED, f"discharged by a validation record naming {anchor_id!r}"
    return UNSATISFIED, (
        f"no validation record discharging {anchor_id!r}. Discharged by: "
        f"{entry.discharged_by}"
    )


def withholding(requires, ledger) -> dict:
    """The evidential withholding implied by a quantity's declared anchors."""
    blocked = []
    for anchor_id in requires:
        state, reason = status(anchor_id, ledger)
        if state != SATISFIED:
            blocked.append(f"{state}: {reason}")
    return {EVIDENTIAL: " | ".join(blocked)} if blocked else {}


def summary(ledger) -> dict:
    return {
        anchor_id: {
            "state": status(anchor_id, ledger)[0],
            "depends_on": entry.depends_on,
            "decided": entry.decided,
            "open_question": entry.open_question,
        }
        for anchor_id, entry in ANCHORS.items()
    }
