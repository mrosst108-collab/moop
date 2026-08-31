"""The canonical equation as the workspace: blanks in situ.

``workspace`` emits a port namespace -- ``state.drift_X.dH`` and the rest --
which is already a translation of the equation. This module removes that
translation: the equation itself is the namespace, a blank sits where the
operator sits, and the relations the ports had to reconstruct are simply
still written down.

WHICH EQUATION IS THE STENCIL IS NOT SETTLED, AND THIS MODULE DOES NOT
SETTLE IT. Rendering one form as *the* workspace would make that form the
de facto source, which is precisely the inversion ``prompts/asdg-rme7.md``
section 2.1 records under G_prov. So both forms are here, each labelled with
its provenance, and they are not the same stencil: they differ in how many
blanks there are, where they are, and which primitives have a written home
at all. G_prov is exhibited rather than adjudicated.

A blank may stay blank. An unfilled blank means the grammar has the position
and this problem did not instantiate it -- not an error, and not silence.
"""

from __future__ import annotations

from dataclasses import dataclass

from .placement import Refused
from .primitives import Kind, Operand, Position

HOLE = "______"


@dataclass(frozen=True)
class Blank:
    """A position in the written equation, with its structural metadata.

    The metadata is what the port layer made user-facing; here it is exactly
    that -- metadata on a blank -- and the equation carries the relations.
    """

    id: str
    location: str
    kind: Kind
    position: Position
    operand: Operand
    index: str | None = None

    def describe(self) -> str:
        rows = [f"{self.id}", f"  location: {self.location}",
                f"  kind: {self.kind.name.lower()}",
                f"  operand: {self.operand.name.lower()}"]
        if self.index:
            rows.append(f"  instance: {self.index}")
        return "\n".join(rows)


@dataclass(frozen=True)
class Stencil:
    """One written form, its provenance, and the blanks it actually has."""

    name: str
    provenance: str
    status: str
    template: str
    blanks: tuple[Blank, ...]

    def ids(self) -> tuple[str, ...]:
        return tuple(b.id for b in self.blanks)

    def render(self, filled: dict[str, str] | None = None) -> str:
        f = dict(filled or {})
        unknown = set(f) - set(self.ids())
        if unknown:
            raise Refused(
                f"{self.name} has no blank {sorted(unknown)}. A primitive "
                "cannot be given a home the written form does not provide.")
        return self.template.format(
            **{b.id: f.get(b.id, HOLE) for b in self.blanks})

    def unfilled(self, filled: dict[str, str] | None = None) -> list[str]:
        return [i for i in self.ids() if i not in (filled or {})]

    def describe(self) -> str:
        head = (f"{self.name}\n  provenance: {self.provenance}\n"
                f"  status: {self.status}\n  blanks: {len(self.blanks)}")
        return head + "\n\n" + "\n".join(b.describe() for b in self.blanks)


# --------------------------------------------------------------------------
# S_v5 -- prompts/asdg-rme7.md section 2, carried from Rosst-CP v5.
# Seven blanks over TWO lines. F has a home in the state equation AND in the
# parameter equation; Sigma is one blank with no index.
# --------------------------------------------------------------------------

S_V5 = Stencil(
    name="S_v5",
    provenance="prompts/asdg-rme7.md section 2, carried from Rosst-CP v5",
    status="this section's carried source",
    template=(
        "dX_t = {v1}(dH) - {v2}(dH) - {v3}(dPhi) + {v4}.dW_t + {v5} dt\n"
        "dtheta = {v6}(theta, F) . {v7}(X, theta, Phi) dt"
    ),
    blanks=(
        Blank("v1", "dX.drift", Kind.OPERATOR, Position.DRIFT_X, Operand.DH),
        Blank("v2", "dX.drift", Kind.OPERATOR, Position.DRIFT_X, Operand.DH),
        Blank("v3", "dX.drift", Kind.OPERATOR, Position.DRIFT_X, Operand.DPHI),
        Blank("v4", "dX.diffusion", Kind.OPERATOR, Position.DIFFUSION_X,
              Operand.DW),
        Blank("v5", "dX.drift", Kind.OPERATOR, Position.DRIFT_X, Operand.NONE),
        Blank("v6", "dtheta.gate", Kind.ADMISSIBILITY, Position.DRIFT_THETA,
              Operand.NONE),
        Blank("v7", "dtheta.drift", Kind.OPERATOR, Position.DRIFT_THETA,
              Operand.NONE),
    ),
)

# --------------------------------------------------------------------------
# S_C1 -- the count-aligned variant, section 2.1. Provenance: chat-level
# continuity, conceded 2026-08-31. FIVE blanks over ONE line: no parameter
# equation is written, so neither kappa nor F has a home here at all.
# --------------------------------------------------------------------------

S_C1 = Stencil(
    name="S_C1",
    provenance="chat-level continuity; not a primary source (section 2.1)",
    status="STIPULATED -- recorded, not admitted",
    template=(
        "dX_i = ( {c1}(dH_i) - {c2}(dH_i) - {c3}(dPhi_i) ) dt\n"
        "       + {c4} o dW_i\n"
        "       + Sum_{{j!=i}} {c5}(X_j -> X_i) o dW_ij"
    ),
    blanks=(
        Blank("c1", "dX.drift", Kind.OPERATOR, Position.DRIFT_X, Operand.DH),
        Blank("c2", "dX.drift", Kind.OPERATOR, Position.DRIFT_X, Operand.DH),
        Blank("c3", "dX.drift", Kind.OPERATOR, Position.DRIFT_X, Operand.DPHI),
        Blank("c4", "dX.diffusion", Kind.OPERATOR, Position.DIFFUSION_X,
              Operand.DW, index="diagonal"),
        Blank("c5", "dX.diffusion", Kind.OPERATOR, Position.DIFFUSION_X,
              Operand.DW, index="off-diagonal"),
    ),
)

STENCILS = {s.name: s for s in (S_V5, S_C1)}

#: Primitives with no written blank in a given stencil. Neither form writes
#: gamma anywhere -- entry 28 -- so a "gamma = ___" line would be an equation
#: line no source carries, and is not drawn here.
HOMELESS = {
    "S_v5": ("gamma",),
    "S_C1": ("F", "kappa", "gamma"),
}
