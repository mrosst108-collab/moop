"""Compatibility pass: what can RME-7 legitimately hold of the mechanism?

Three verdicts, and the third is the one this pass exists for:

    PLACED   a blank exists whose recorded properties match, and placing the
             element there discards nothing the mechanism consumes.
    NO_BLANK the stencil offers no position of this shape. An informative
             outcome, not a failure -- an empty blank stays empty.
    LOSSY    a blank exists and is structurally available, but placing the
             element there DISCARDS a property the mechanism requires. Named,
             because this is the failure mode a stencil invites: the nearest
             available slot is not the same as the right one.

The rule this pass enforces, stated once: an identified process is not turned
into an anonymous one to occupy a blank.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "rme7py"))

from rme7.stencil import S_C1, S_V5, Stencil  # noqa: E402

from .mechanism import (CHANNEL_FAMILY, GATES, OBSERVATIONS,  # noqa: E402
                        STATE, Basis)


class Fit(Enum):
    PLACED = "a matching blank, nothing lost"
    NO_BLANK = "no position of this shape in the stencil"
    LOSSY = "a blank exists, but placing here discards a required property"


@dataclass(frozen=True)
class Finding:
    element: str
    fit: Fit
    blank: str | None
    reason: str


def assess(stencil: Stencil) -> list[Finding]:
    """Run the mechanism against one stencil. No element is forced."""
    ids = set(stencil.ids())
    out: list[Finding] = []

    # -- the identified event process ------------------------------------
    diffusion = [b.id for b in stencil.blanks
                 if b.position.name == "DIFFUSION_X"]
    out.append(Finding(
        "identified event process",
        Fit.LOSSY if diffusion else Fit.NO_BLANK,
        diffusion[0] if diffusion else None,
        "the diffusion blanks are driven by `o dW`, an ANONYMOUS increment. "
        "The mechanism's event carries an actor identity that the gates and "
        "routing consume -- previous-vote lookup keyed on (actor, target), "
        "self-vote detection, karma attributed to the target's author. "
        "Placing the event here would discard the index the gate runs on."
        if diffusion else "no diffusion position in this form"))

    # -- the channel family ----------------------------------------------
    off = [b.id for b in stencil.blanks if b.index == "off-diagonal"]
    out.append(Finding(
        "channel family (one event -> author, subreddit, domain)",
        Fit.LOSSY if off else Fit.NO_BLANK,
        off[0] if off else None,
        "Sigma_ij(X_j -> X_i) names ONE destination. The mechanism routes one "
        "admitted event to three, through one gate, each keyed differently. "
        "Collapsing the family into a single occurrence loses the arity and "
        "the shared gate."
        if off else "this form writes no indexed channel at all"))

    # -- the two gates ---------------------------------------------------
    gate_blanks = [b.id for b in stencil.blanks
                   if b.kind.name == "ADMISSIBILITY"]
    if not gate_blanks:
        for g in GATES:
            out.append(Finding(f"{g.NAME} ({g.JURISDICTION})", Fit.NO_BLANK,
                               None, "this form writes no admissibility "
                               "position; kappa is homeless here"))
    else:
        out.append(Finding(GATES[0].NAME, Fit.PLACED, gate_blanks[0],
                           "a verdict position exists and the mechanism's "
                           "gate is a boolean verdict with reasons"))
        out.append(Finding(
            GATES[1].NAME, Fit.NO_BLANK, None,
            "the stencil offers ONE admissibility position. The mechanism has "
            "two gates with different inputs and different jurisdictions "
            "(the second consults spam/deleted, which the first never sees). "
            "The second gate has nowhere to go without merging them."))

    # -- autonomous evolution: the ruling's target ------------------------
    drift = [b.id for b in stencil.blanks
             if b.position.name == "DRIFT_X" and b.operand.name == "DH"]
    constructed = [s for s in STATE if s.basis is Basis.CONSTRUCTED]
    for s in constructed:
        out.append(Finding(
            f"{s.name} (CONSTRUCTED by the ruling)",
            Fit.PLACED if drift else Fit.NO_BLANK,
            drift[0] if drift else None,
            "the drift group is exactly the position a decaying temporal "
            "state occupies. Note this element is NOT extracted from the "
            "archive -- the blank is filled by the reconstruction, not by "
            "the source."))

    # -- observations: deliberately not placed ---------------------------
    out.append(Finding(
        f"observations ({len(OBSERVATIONS)}: hot, top, controversy, ...)",
        Fit.NO_BLANK, None,
        "correctly homeless. These are functions OF the state, not terms in "
        "its evolution. The stencil has no observation position and should "
        "not: forcing them into operator blanks was the error this pass "
        "exists to prevent."))

    # -- extracted state that is not a term ------------------------------
    out.append(Finding(
        "account.karma[subreddit, kind]",
        Fit.NO_BLANK, None,
        "a state VARIABLE, not an operator. The stencil's blanks are "
        "operator positions; X itself has no blank in either form."))

    assert all(f.blank is None or f.blank in ids for f in out)
    return out


def report(stencil: Stencil) -> str:
    rows = [f"{stencil.name}  ({stencil.status})", ""]
    for f in assess(stencil):
        at = f" -> {f.blank}" if f.blank else ""
        rows.append(f"  [{f.fit.name}]{at}  {f.element}")
        rows.append(f"      {f.reason}")
    return "\n".join(rows)


def tally(stencil: Stencil) -> dict[str, int]:
    counts = {f.name: 0 for f in Fit}
    for f in assess(stencil):
        counts[f.fit.name] += 1
    return counts


STENCILS = (S_V5, S_C1)
