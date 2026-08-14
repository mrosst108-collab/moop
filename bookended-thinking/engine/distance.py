"""Delta, and why it is not a number.

Delta was specified as "distance between input cells and response cells". There
is no metric on this space to make that a scalar:

* The epistemic axis is a dependency order. Displacement along it is ordinal
  and signed, and the L5/L6 firewall means one of its five steps is not
  commensurable with the other four.
* The dynamic axis is an unordered set of three different kinds of object.
  Only same / within-type / cross-type is available. There is no sense in
  which J# is nearer to Sigma than to F.

So Delta is a typed pair with a categorical displacement summary, and this
module refuses arithmetic on it rather than documenting that the arithmetic is
unwarranted. v0.6 s12b already sealed Delta as a lossy projection of the
synthesis; collapsing it further to one number makes the projection worse and
hides that it happened.
"""

from __future__ import annotations

from dataclasses import dataclass

from .ontology import LAYER_IDS


class NotScalarError(TypeError):
    """Raised on any attempt to turn a displacement into a number."""


_REFUSAL = (
    "Delta is not a scalar. The epistemic axis is an order and the dynamic "
    "axis is an unordered typed set; there is no metric to combine them. Read "
    "the layer displacement and the dynamic transition separately."
)


@dataclass(frozen=True)
class LayerDisplacement:
    frm: str | None
    to: str | None
    ordinal_steps: int | None
    crosses_firewall: bool

    def __str__(self) -> str:
        if self.ordinal_steps is None:
            return f"{self.frm or '-'} -> {self.to or '-'} (undefined)"
        mark = " [crosses L5/L6 firewall]" if self.crosses_firewall else ""
        return f"{self.frm} -> {self.to} ({self.ordinal_steps:+d} ordinal steps){mark}"


@dataclass(frozen=True)
class DynamicTransition:
    frm: str | None
    to: str | None
    kind: str  # same | within_type | cross_type | undefined

    def __str__(self) -> str:
        return f"{self.frm or '-'} -> {self.to or '-'} ({self.kind})"


@dataclass(frozen=True)
class Delta:
    layer: LayerDisplacement
    dynamic: DynamicTransition
    displacement: str  # none | layer_only | dynamic_only | both

    def __float__(self):
        raise NotScalarError(_REFUSAL)

    def __int__(self):
        raise NotScalarError(_REFUSAL)

    def __add__(self, other):
        raise NotScalarError(
            "Displacements do not add. Averaging them across pairs would treat "
            "an ordinal axis as an interval one. " + _REFUSAL
        )

    __radd__ = __add__

    def __str__(self) -> str:
        return f"layer: {self.layer} | dynamic: {self.dynamic} | displacement: {self.displacement}"


def layer_displacement(ontology, frm: str | None, to: str | None) -> LayerDisplacement:
    if frm is None or to is None or frm not in LAYER_IDS or to not in LAYER_IDS:
        return LayerDisplacement(frm, to, None, False)
    steps = LAYER_IDS.index(to) - LAYER_IDS.index(frm)
    return LayerDisplacement(frm, to, steps, ontology.crosses_firewall(frm, to))


def dynamic_transition(ontology, frm: str | None, to: str | None) -> DynamicTransition:
    a, b = ontology.dynamics.get(frm or ""), ontology.dynamics.get(to or "")
    if a is None or b is None:
        return DynamicTransition(frm, to, "undefined")
    if a.id == b.id:
        return DynamicTransition(frm, to, "same")
    return DynamicTransition(frm, to, "within_type" if a.kind == b.kind else "cross_type")


def delta(ontology, frm_cell, to_cell) -> Delta:
    """frm_cell / to_cell are ``typing_rules.Cell`` (or any (layer, object, ...) tuple)."""
    ld = layer_displacement(ontology, frm_cell[0], to_cell[0])
    dt = dynamic_transition(ontology, frm_cell[1], to_cell[1])
    moved_layer = ld.ordinal_steps not in (0, None)
    moved_dyn = dt.kind not in ("same", "undefined")
    if moved_layer and moved_dyn:
        disp = "both"
    elif moved_layer:
        disp = "layer_only"
    elif moved_dyn:
        disp = "dynamic_only"
    else:
        disp = "none"
    return Delta(ld, dt, disp)


def edge_summary(ontology, input_cells, output_cells) -> dict:
    """All input/output pairs, plus the warning that an edge is not a bridge."""
    pairs = [delta(ontology, a, b) for a in input_cells for b in output_cells]
    return {
        "pairs": pairs,
        "any_displacement": any(d.displacement != "none" for d in pairs),
        "firewall_crossings": sum(1 for d in pairs if d.layer.crosses_firewall),
        "caveat": (
            "This is the edge. The edge under-determines the bridge: two bridges "
            "joining different pole pairs can land on the same edge. Displacement "
            "is not synthesis -- the interaction test carries that claim."
        ),
    }
