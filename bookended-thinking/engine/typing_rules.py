"""Applying the typed subgraph AFTER classification.

This module is the whole reason the predictions are kept out of the prompt. It
takes classifications produced by an instrument that did not know the
predictions and checks them against the predictions afterwards, so that a
prediction can actually be contradicted.

A contradiction is recorded, never repaired, and never adjudicated: when an
output lands in a cell the architecture types as void, the two hypotheses --
the typing is wrong, or the classifier is wrong -- are not separable from
inside the system. Separating them needs the external anchor, which this
program does not have.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import NamedTuple


class Cell(NamedTuple):
    layer: str | None
    object: str
    relation: str

    def __str__(self) -> str:
        where = self.layer if self.layer else "no-address"
        return f"{self.object}/{self.relation}@{where}"


CONSISTENT = "consistent"
VIOLATION = "violation"
UNPREDICTED = "unpredicted"

COLLISION_NOTE = (
    "A violation is a collision, not a refutation. Bad typing and bad "
    "classifier are not separable without the external anchor."
)


@dataclass(frozen=True)
class Verdict:
    cell: Cell
    status: str
    rule_id: str | None
    rule_status: str | None
    expect: str | None
    detail: str

    @property
    def is_violation(self) -> bool:
        return self.status == VIOLATION


def _relations_of(pred: dict) -> tuple:
    rel = pred.get("relation")
    if rel is None:
        return ()
    return tuple(rel) if isinstance(rel, list) else (rel,)


def _matches_object(pred: dict, obj_id: str, kind: str) -> bool:
    if "applies_to_id" in pred and pred["applies_to_id"] is not None:
        return pred["applies_to_id"] == obj_id
    if "applies_to_kind" in pred and pred["applies_to_kind"] is not None:
        return pred["applies_to_kind"] == kind
    return False


def _matches_layer(pred: dict, layer: str | None) -> bool:
    layers = pred.get("layers")
    if layers == "all":
        return layer is not None
    if layers == "none":
        return layer is None
    if isinstance(layers, list):
        return layer in layers
    return False


def as_cell(value) -> Cell:
    """Coerce a (layer, object, relation) triple -- e.g. straight from JSON."""
    if isinstance(value, Cell):
        return value
    layer, obj, relation = tuple(value)[:3]
    return Cell(layer if layer not in ("", "none") else None, obj, relation)


def audit_cell(cell, ontology, rules) -> Verdict:
    cell = as_cell(cell)
    dyn = ontology.dynamics.get(cell.object)
    if dyn is None:
        return Verdict(cell, UNPREDICTED, None, None, None,
                       f"{cell.object!r} is not an RME-7 object")

    for pred in rules.predictions:
        if not _matches_object(pred, dyn.id, dyn.kind):
            continue
        if cell.relation not in _relations_of(pred):
            continue
        if not _matches_layer(pred, cell.layer):
            continue
        expect = pred["expect"]
        if expect == "ill_typed":
            return Verdict(
                cell, VIOLATION, pred["id"], pred.get("status"), expect,
                f"classifier reported a pairing predicted ill-typed by {pred['id']} "
                f"(status: {pred.get('status')}). {COLLISION_NOTE}",
            )
        return Verdict(cell, CONSISTENT, pred["id"], pred.get("status"), expect,
                       f"consistent with {pred['id']}")

    return Verdict(
        cell, UNPREDICTED, None, None, None,
        "no prediction covers this pairing -- a gap in the subgraph spec, "
        "not evidence for or against it",
    )


def audit(cells, ontology, rules) -> dict:
    verdicts = [audit_cell(c, ontology, rules) for c in cells]
    counts = Counter(v.status for v in verdicts)
    violations = [v for v in verdicts if v.is_violation]
    by_rule = Counter(v.rule_id for v in violations)
    return {
        "typing_rules_version": rules.version,
        "verdicts": verdicts,
        "counts": dict(counts),
        "violations": violations,
        "violations_by_rule": dict(by_rule),
        "note": COLLISION_NOTE,
    }


def predicted_blocks(ontology, rules) -> dict:
    """The shape the subgraph is predicted to have, counted honestly.

    The three blocks are not summed. They are not the same kind of object and
    a total would assert a commensurability that does not hold.
    """
    n_layers = len(ontology.layers)
    operators = ontology.operators()
    return {
        "operator_block": {
            "relation": "performed_within",
            "members": operators,
            "cells": len(operators) * n_layers,
            "status": "draft",
        },
        "indicator_row": {
            "relation": "evaluated_under",
            "members": [d.id for d in ontology.dynamics.values() if d.kind == "indicator"],
            "cells": n_layers,
            "status": "draft",
            "note": "Not cells of the same kind as the operator block.",
        },
        "invariant_row": {
            "relation": "path_level",
            "members": [d.id for d in ontology.dynamics.values() if d.kind == "invariant"],
            "cells": 0,
            "status": "conjecture",
            "note": "Void at cell level; referent is one level up, on paths.",
        },
        "total": None,
        "total_refused_because": (
            "The blocks hold different relations. Adding them would produce a "
            "number whose referent is undetermined -- which is the state the "
            "grid count was blocked in."
        ),
    }
