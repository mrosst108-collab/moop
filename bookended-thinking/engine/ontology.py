"""Loading the ontology, and the guard that keeps the predictions out of it.

Two files describe the axes (``cp_layers.yaml``, ``rme7_objects.yaml``) and one
file holds the predictions (``typing_rules.yaml``). Only the first two are ever
rendered into a prompt, and ``render_prompt`` fails loudly rather than quietly
leaking a prediction into the classifier's context.

Some descriptive fields are predictions wearing descriptive clothes and are
withheld too -- see ``WITHHELD_FIELDS``. Telling the classifier that L1 has
near-zero admissible width would bias it away from ever reporting an L1
synthesis, which is precisely the fabrication the layer exists to catch.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from . import yamlish

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LAYER_IDS = ("L1", "L2", "L3", "L4", "L5", "L6")
RELATIONS = ("performed_within", "evaluated_under", "path_level", "none", "uncertain")
KINDS = ("operator", "indicator", "invariant")
SUPPORT = ("clear", "contested", "uncertain")

#: Fields excluded from anything rendered into a classifier prompt.
#:
#: ``definition`` / ``commutator_of`` / ``computed_from`` are withheld because
#: gamma is measured rather than recognised: the engine composes it from the
#: constituent operator labels, so the classifier never needs the commutator
#: and giving it the commutator would hand it most of the void conjecture.
WITHHELD_FIELDS = {
    "cp_layers": ("middle_width", "zero"),
    "rme7_objects": ("predicts_high_dispersion", "note", "definition",
                     "commutator_of", "computed_from"),
}


class OntologyError(ValueError):
    pass


@dataclass(frozen=True)
class Layer:
    id: str
    name: str
    question: str
    objects: tuple
    opening: str
    closure: str
    middle_width: str
    zero: str
    failure_mode: str

    @property
    def index(self) -> int:
        return LAYER_IDS.index(self.id)


@dataclass(frozen=True)
class Dynamic:
    id: str
    display: str
    unicode: str
    name: str
    kind: str
    fail_only: bool = False
    definition: str | None = None
    commutator_of: tuple = ()
    computed_from: str | None = None
    predicts_high_dispersion: bool = False
    note: str | None = None


@dataclass
class Ontology:
    version: str
    layers: dict = field(default_factory=dict)
    dynamics: dict = field(default_factory=dict)
    firewall: tuple = ()
    _raw: dict = field(default_factory=dict)

    # -- construction ------------------------------------------------------

    @classmethod
    def load(cls, root: str = ROOT) -> "Ontology":
        cp = yamlish.load_file(os.path.join(root, "ontology", "cp_layers.yaml"))
        rme = yamlish.load_file(os.path.join(root, "ontology", "rme7_objects.yaml"))

        layers = {}
        for entry in cp["layers"]:
            layer = Layer(
                id=entry["id"],
                name=entry["name"],
                question=entry["question"],
                objects=tuple(entry.get("objects") or ()),
                opening=entry["opening"],
                closure=entry["closure"],
                middle_width=entry.get("middle_width", "unknown"),
                zero=entry.get("zero", "none"),
                failure_mode=entry.get("failure_mode", ""),
            )
            if layer.id in layers:
                raise OntologyError(f"duplicate layer {layer.id}")
            layers[layer.id] = layer
        if tuple(layers) != LAYER_IDS:
            raise OntologyError(
                f"layers must be exactly {LAYER_IDS} in dependency order, got {tuple(layers)}"
            )

        dynamics = {}
        for entry in rme["objects"]:
            dyn = Dynamic(
                id=entry["id"],
                display=entry["display"],
                unicode=entry["unicode"],
                name=entry["name"],
                kind=entry["kind"],
                fail_only=bool(entry.get("fail_only", False)),
                definition=entry.get("definition"),
                commutator_of=tuple(entry.get("commutator_of") or ()),
                computed_from=entry.get("computed_from"),
                predicts_high_dispersion=bool(entry.get("predicts_high_dispersion", False)),
                note=entry.get("note"),
            )
            if dyn.kind not in KINDS:
                raise OntologyError(f"{dyn.id}: unknown kind {dyn.kind!r}")
            if dyn.id in dynamics:
                raise OntologyError(f"duplicate dynamic object {dyn.id}")
            dynamics[dyn.id] = dyn
        if len(dynamics) != 7:
            raise OntologyError(f"RME-7 must have seven objects, got {len(dynamics)}")

        by_kind = {k: [d.id for d in dynamics.values() if d.kind == k] for k in KINDS}
        if len(by_kind["operator"]) != 5 or len(by_kind["indicator"]) != 1 or len(by_kind["invariant"]) != 1:
            raise OntologyError(
                "the axis is not homogeneous by design: expected 5 operators, "
                f"1 indicator, 1 invariant; got {by_kind}"
            )

        for dyn in dynamics.values():
            for member in dyn.commutator_of:
                if member not in dynamics:
                    raise OntologyError(f"{dyn.id}: commutator_of names unknown object {member!r}")
                if dynamics[member].kind != "operator":
                    raise OntologyError(f"{dyn.id}: commutator_of must name operators, {member} is {dynamics[member].kind}")

        fw = cp["axis"]["firewall"]["between"]
        return cls(
            version=cp["version"],
            layers=layers,
            dynamics=dynamics,
            firewall=(fw[0], fw[1]),
            _raw={"cp_layers": cp, "rme7_objects": rme},
        )

    # -- queries -----------------------------------------------------------

    def operators(self) -> tuple:
        return tuple(d.id for d in self.dynamics.values() if d.kind == "operator")

    def crosses_firewall(self, a: str, b: str) -> bool:
        lo, hi = LAYER_IDS.index(self.firewall[0]), LAYER_IDS.index(self.firewall[1])
        i, j = LAYER_IDS.index(a), LAYER_IDS.index(b)
        return min(i, j) <= min(lo, hi) < max(lo, hi) <= max(i, j)

    # -- rendering ---------------------------------------------------------

    def _render_layers(self) -> str:
        drop = WITHHELD_FIELDS["cp_layers"]
        lines = ["### CP layers (dependency order; positions are not permutable)", ""]
        for lid in LAYER_IDS:
            layer = self.layers[lid]
            lines.append(f"**{layer.id} {layer.name}**")
            lines.append(f"- Question: {layer.question}")
            lines.append(f"- Objects: {', '.join(layer.objects)}")
            lines.append(f"- Opening: {layer.opening}")
            lines.append(f"- Closure: {layer.closure}")
            if "failure_mode" not in drop and layer.failure_mode:
                lines.append(f"- Characteristic failure: {layer.failure_mode}")
            lines.append("")
        lines.append(
            f"A firewall separates {self.firewall[0]} from {self.firewall[1]}: "
            "epistemic validity is not ontological standing, and the two must not be merged."
        )
        return "\n".join(lines)

    def _render_dynamics(self) -> str:
        drop = WITHHELD_FIELDS["rme7_objects"]
        lines = ["### RME-7 dynamic objects (a typed set: three kinds, not seven of one kind)", ""]
        for kind in KINDS:
            members = [d for d in self.dynamics.values() if d.kind == kind]
            lines.append(f"**{kind}**")
            for dyn in members:
                bits = [f"`{dyn.id}` ({dyn.unicode}) -- {dyn.name}"]
                if dyn.fail_only:
                    bits.append("fail-only verdict")
                if dyn.definition and "definition" not in drop:
                    bits.append(f"defined as {dyn.definition}")
                if dyn.computed_from and "computed_from" not in drop:
                    bits.append(f"computed from {dyn.computed_from}")
                lines.append("- " + "; ".join(bits))
            lines.append("")
        lines.append(
            "Do not treat all seven as interchangeable operators, and do not assume "
            "any particular pairing with a layer is or is not available -- that is "
            "not yours to decide and you have not been told."
        )
        return "\n".join(lines)

    def render_prompt(self, prompt_path: str, root: str = ROOT) -> str:
        with open(prompt_path, "r", encoding="utf-8") as handle:
            text = handle.read()

        for forbidden in ("{{TYPING_RULES}}", "{{PREDICTIONS}}", "{{SUBGRAPH}}"):
            if forbidden in text:
                raise OntologyError(
                    f"{prompt_path}: refuses to interpolate {forbidden}. The typed "
                    "subgraph is withheld from the classifier; a classifier that "
                    "knows which pairings are admissible cannot report one that is not, "
                    "and the empty-cell test becomes a test that cannot fail."
                )

        rendered = text.replace("{{CP_LAYERS}}", self._render_layers())
        rendered = rendered.replace("{{RME7_OBJECTS}}", self._render_dynamics())

        leaks = self._leak_check(rendered, root)
        if leaks:
            raise OntologyError(
                f"{prompt_path}: prediction content leaked into the prompt: {leaks}"
            )
        return rendered

    @staticmethod
    def _leak_check(rendered: str, root: str) -> list:
        """Fail if any prediction id or note text reached the prompt."""
        rules = yamlish.load_file(os.path.join(root, "ontology", "typing_rules.yaml"))
        leaks = []
        for pred in rules["predictions"]:
            if pred["id"] in rendered:
                leaks.append(pred["id"])
            note = (pred.get("note") or "").strip()
            if note:
                probe = note.split("\n")[0].strip()
                if len(probe) > 24 and probe in rendered:
                    leaks.append(f"{pred['id']}:note")
        return leaks


class TypingRules:
    """The withheld predictions, loaded separately and never rendered."""

    def __init__(self, data: dict) -> None:
        self.version = data["version"]
        self.predictions = data["predictions"]
        self.zeros = {z["id"]: z for z in data["zeros"]}
        self.empirical_order = tuple(data["empirical_order"])
        if not data.get("withheld_from_classifier"):
            raise OntologyError(
                "typing_rules.yaml must declare withheld_from_classifier: true"
            )

    @classmethod
    def load(cls, root: str = ROOT) -> "TypingRules":
        return cls(yamlish.load_file(os.path.join(root, "ontology", "typing_rules.yaml")))
