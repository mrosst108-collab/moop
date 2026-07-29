"""What kind of statement a result can support.

Every other refusal in this tree is an epistemic gate: the quantity cannot be
produced. ``COHERENCE_ONLY`` was the exception -- a label attached to a number
that remains perfectly quotable once the label is dropped. This module closes
that gap without refusing the underlying calculation, by making the evidentiary
status part of the result's *identity* rather than metadata beside it.

A measurement without validation provenance is not an empirical result with a
disclaimer. It is a different kind of result, and it is a different type here.

**Four claim levels, as a ladder.** Each names what becomes unavailable, which
is more useful than a confidence scalar: a scalar flattens "cannot be computed"
and "computed but not externally validated" into one number, and those are not
degrees of the same thing.

===============  =========================================================
computable       the quantity can be produced at all
inferential      a conclusion can be drawn from it
evidential       it can be cited as evidence about the architecture
generalisable    its absence extends beyond the region examined
===============  =========================================================

Withholding a level withholds everything above it: nothing is inferred from a
quantity that was never computed.

This generalises a distinction already in the tree. The gamma result separates
*endpoint change observed under stated conditions* from *supports gamma != 0 for
the tested pair* -- that is exactly the computable/inferential rung, and the
general operator arm is a measurement licensed at the first and withheld at the
second.

**What this does not do.** It cannot stop a reader copying a number out by hand.
What it removes is the *silent* path: the value cannot be obtained without
naming which claim is being made, and the rendered form carries its own status,
so quoting the figure quotes the status with it.
"""

from __future__ import annotations

COMPUTABLE = "computable"
INFERENTIAL = "inferential"
EVIDENTIAL = "evidential"
GENERALISABLE = "generalisable"

CLAIMS = (COMPUTABLE, INFERENTIAL, EVIDENTIAL, GENERALISABLE)

CLAIM_MEANING = {
    COMPUTABLE: "the quantity can be produced at all",
    INFERENTIAL: "a conclusion can be drawn from it",
    EVIDENTIAL: "it can be cited as evidence about the architecture",
    GENERALISABLE: "its absence extends beyond the region examined",
}

UNVALIDATED_CLASSIFIER = (
    "no classifier-validation record against an anchor external to the "
    "architecture; a classifier built on the architecture's own assumptions "
    "measures its priors"
)


class ClaimNotLicensed(Exception):
    """Raised when a result is asked for a claim it does not license."""


class Measurement:
    """A value together with the claims it licenses.

    Construct with the levels that are *withheld* and why. Everything not
    withheld is licensed, and withholding a level cascades upward.
    """

    __slots__ = ("quantity", "_value", "_withheld", "_licensed", "detail", "requires")

    def __init__(self, quantity: str, value=None, *, withheld=None, detail=None,
                 requires=()):
        held = dict(withheld or {})
        for key in held:
            if key not in CLAIMS:
                raise ValueError(f"unknown claim level {key!r}")
        for index, level in enumerate(CLAIMS):
            if level in held:
                for higher in CLAIMS[index + 1:]:
                    held.setdefault(higher, f"requires {level}, which is withheld: {held[level]}")
        self.quantity = quantity
        self._value = value
        self._withheld = held
        self._licensed = tuple(c for c in CLAIMS if c not in held)
        self.detail = detail
        self.requires = tuple(requires)

    # -- constructors ------------------------------------------------------

    @classmethod
    def refused(cls, quantity: str, reason: str, **kw) -> "Measurement":
        return cls(quantity, None, withheld={COMPUTABLE: reason}, **kw)

    # -- licensing ---------------------------------------------------------

    @property
    def licensed(self) -> tuple:
        return self._licensed

    @property
    def withheld(self) -> dict:
        return dict(self._withheld)

    @property
    def highest(self):
        return self._licensed[-1] if self._licensed else None

    def licenses(self, level: str) -> bool:
        return level in self._licensed

    def require(self, level: str):
        if level not in CLAIMS:
            raise ValueError(f"unknown claim level {level!r}")
        if level in self._withheld:
            raise ClaimNotLicensed(
                f"{self.quantity}: not {level} -- {self._withheld[level]}"
            )
        return self._value

    # -- access ------------------------------------------------------------

    @property
    def computed(self):
        """The raw computation. Available for development, composition and debugging."""
        return self.require(COMPUTABLE)

    def as_inference(self):
        return self.require(INFERENTIAL)

    def as_evidence(self):
        return self.require(EVIDENTIAL)

    def as_general(self):
        return self.require(GENERALISABLE)

    # -- rendering ---------------------------------------------------------

    def __float__(self):
        raise ClaimNotLicensed(
            f"{self.quantity}: a measurement does not silently become a number. "
            "Use .computed for the raw calculation, or .as_evidence() to assert "
            "it as evidence -- which will refuse if it is not licensed."
        )

    __int__ = __float__

    def __str__(self) -> str:
        if not self.licenses(COMPUTABLE):
            return f"{self.quantity}: REFUSED -- {self._withheld[COMPUTABLE]}"
        head = f"{self.quantity} = {self._value} [{self.highest}]"
        reasons = [f"not {level}: {why}" for level, why in self.explicit_withheld()]
        return "; ".join([head] + reasons)

    def __format__(self, spec: str) -> str:
        """Format specs are ignored on purpose.

        ``f"{m:.2f}"`` must not yield a bare number: a format spec is the
        commonest way a value gets lifted out of its context and into a
        sentence. The status travels with the value or the value does not travel.
        """
        return str(self)

    def explicit_withheld(self) -> list:
        """Withheld levels with their own reason, excluding ones inherited by cascade.

        The cascade reason is derivable from the level below it and repeating it
        buries the specific finding -- a passage result withheld for partial
        coverage should say so, not only that it is unvalidated.
        """
        return [(level, why) for level, why in self._withheld.items()
                if not why.startswith("requires ")]

    def first_withheld(self):
        for level in CLAIMS:
            if level in self._withheld:
                return level, self._withheld[level]
        return None

    def to_json(self) -> dict:
        return {
            "quantity": self.quantity,
            "value": self._value if self.licenses(COMPUTABLE) else None,
            "licensed": list(self._licensed),
            "withheld": self.withheld,
            "requires": list(self.requires),
            "detail": self.detail,
        }


def json_default(obj):
    """For ``json.dump(..., default=json_default)`` -- status survives serialisation."""
    if isinstance(obj, Measurement):
        return obj.to_json()
    return str(obj)
