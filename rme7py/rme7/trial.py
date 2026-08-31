"""Paired-stencil trials: the same problem under two custodied sources.

Provenance changes the workspace, so it changes the construction problem.
This module builds the two conditions and scores a returned filling. It makes
no model call and contains no results -- it is the apparatus, not the finding.

WHY THERE IS NO SINGLE ANSWER KEY. The obvious scorer would check a filling
against ``primitives`` -- does the symbol written here have this blank's
recorded position? That scorer is wrong, and wrong in an instructive way:
``primitives`` places F in the drift of theta, a position stipulated from
S_C1 (section 2.1). Scoring S_v5 with it would mark S_v5's OWN canonical
filling -- F in the state equation, which S_v5 writes -- as an error. The
entry-27 inversion, arriving at the scoring layer.

So each stencil is scored against the filling ITS OWN form writes, and the
two answer keys disagree. That disagreement is the experimental variable,
not a defect in either key.

WHAT THE TRIAL CANNOT MEASURE. Blanks with identical metadata are
interchangeable: a filling that swaps them is indistinguishable from one that
does not. Those positions are reported UNSCORABLE rather than scored, which
bounds the experiment honestly -- entries 29 through 31, arriving here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .stencil import HOLE, Stencil, S_C1, S_V5, STENCILS


class Outcome(Enum):
    CONSTRUCTED = "matches the filling this form writes"
    OMITTED = "left blank; the form has the position, the answer did not use it"
    INVENTED = "a symbol this form gives no home"
    UNSCORABLE = "in a collision class; swapping is undetectable"


#: The filling each form itself writes. Not interchangeable: S_v5 writes F
#: TWICE (state equation and generator) and has no index; S_C1 writes the
#: index and writes F nowhere.
KEYS: dict[str, dict[str, str]] = {
    "S_v5": {"v1": "J#", "v2": "G#", "v3": "G~#", "v4": "Sigma",
             "v5": "F", "v6": "kappa", "v7": "F"},
    "S_C1": {"c1": "J#", "c2": "G#", "c3": "G~#",
             "c4": "Sigma_ii", "c5": "Sigma_ij"},
}


def collision_classes(stencil: Stencil) -> list[tuple[str, ...]]:
    """Blank ids that share a structural signature, hence are unscorable."""
    groups: dict[tuple, list[str]] = {}
    for b in stencil.blanks:
        groups.setdefault((b.kind, b.position, b.operand, b.index),
                          []).append(b.id)
    return [tuple(v) for v in groups.values() if len(v) > 1]


@dataclass(frozen=True)
class Condition:
    """One arm of the trial. The stencil is part of the record, not context.

    A result reported without its condition is uninterpretable, so the
    condition carries the stencil name and provenance with it.
    """

    problem: str
    stencil: Stencil

    def prompt(self) -> str:
        return (f"problem: {self.problem}\n"
                f"form: {self.stencil.name} "
                f"({self.stencil.status})\n\n"
                f"{self.stencil.render()}\n\n"
                + "\n".join(b.describe() for b in self.stencil.blanks))

    def score(self, filling: dict[str, str]) -> dict[str, Outcome]:
        key = KEYS[self.stencil.name]
        unscorable = {i for cls in collision_classes(self.stencil) for i in cls}
        out: dict[str, Outcome] = {}
        for b in self.stencil.blanks:
            written = filling.get(b.id)
            if b.id in unscorable and written not in (None, HOLE):
                out[b.id] = Outcome.UNSCORABLE
            elif written in (None, HOLE, ""):
                out[b.id] = Outcome.OMITTED
            elif written == key[b.id]:
                out[b.id] = Outcome.CONSTRUCTED
            else:
                out[b.id] = Outcome.INVENTED
        return out

    def tally(self, filling: dict[str, str]) -> dict[str, int]:
        counts = {o.name: 0 for o in Outcome}
        for v in self.score(filling).values():
            counts[v.name] += 1
        return counts


def paired(problem: str) -> tuple[Condition, Condition]:
    """The same problem under both custodied forms. Neither is the control."""
    return (Condition(problem, S_V5), Condition(problem, S_C1))


def key_disagreement() -> dict[str, tuple[str, ...]]:
    """Where the two answer keys differ, which is the experimental variable."""
    v5, c1 = set(KEYS["S_v5"].values()), set(KEYS["S_C1"].values())
    return {
        "written only in S_v5": tuple(sorted(v5 - c1)),
        "written only in S_C1": tuple(sorted(c1 - v5)),
        "written in neither": ("gamma",),
    }
