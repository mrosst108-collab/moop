"""A placement grammar: named ports with admission constraints.

The object here is not a classifier. Nothing in this module decides whether
a given operator "is" J# or G#. It answers the narrower and more achievable
question a labelled workspace needs to answer:

    given a term, which slot may it legitimately occupy, and can the
    placement be recovered afterwards?

PORTS ARE DERIVED, NOT ENUMERATED. A port is one structural signature from
``primitives`` -- (KIND, POSITION, OPERAND) -- together with the number of
leaves that carry it. Nothing is named here that the structural layer does not
already distinguish, which is why there are SIX ports for EIGHT leaves.

That is the consequence of the placeholder reframe, made operational. The two
drift-of-X operators consuming dH share one port of capacity two, because the
grammar genuinely cannot tell which of them a term belongs to; the two Sigma
instances share one port of capacity two for the same reason. Manufacturing
``drift_X.dH.0`` and ``drift_X.dH.1`` would invent an ordering the source does
not carry. Capacity is the honest encoding of a collision; enumeration is not.

The cost is stated rather than hidden: placement is total, recovery is exact
only up to structural class. See ``Grammar.recoverability``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .primitives import (Kind, Operand, Position, Primitive,
                         ConservativeTransport, DissipativeDescent,
                         TeleologicalConfinement, SelfNoise, Channel,
                         AutopoieticFeedback, StructuralAdmissibility,
                         PathDependence)

LEAVES: tuple[type[Primitive], ...] = (
    ConservativeTransport, DissipativeDescent, TeleologicalConfinement,
    SelfNoise, Channel, AutopoieticFeedback, StructuralAdmissibility,
    PathDependence,
)


class Refused(Exception):
    """A placement the grammar does not admit. Never silently coerced."""


@dataclass(frozen=True)
class Term:
    """Something to be placed. Carries a declared signature, not a name.

    A term does not say which primitive it is -- that is the classification
    question this module does not answer. It says what kind of thing it is,
    where it stands, and what it consumes.
    """

    label: str
    kind: Kind
    position: Position
    operand: Operand = Operand.NONE

    def signature(self) -> tuple:
        return (self.kind, self.position, self.operand)


@dataclass
class Port:
    """One structural class, with room for as many leaves as carry it."""

    path: str
    kind: Kind
    position: Position
    operand: Operand
    capacity: int
    held: list[Term] = field(default_factory=list)

    def signature(self) -> tuple:
        return (self.kind, self.position, self.operand)

    @property
    def free(self) -> int:
        return self.capacity - len(self.held)

    def constraint(self) -> str:
        return (f"{self.path}.kind = {self.kind.name}; "
                f"position = {self.position.name}; "
                f"consumes = {self.operand.name}; capacity = {self.capacity}")


#: Where each structural class sits in the namespace. The nesting is a slot
#: namespace -- these ports live within these contexts -- and asserts no
#: semantic dependency between the things placed in them.
_PATHS = {
    (Kind.OPERATOR, Position.DRIFT_X, Operand.DH):        "state.drift_X.dH",
    (Kind.OPERATOR, Position.DRIFT_X, Operand.DPHI):      "state.drift_X.dPhi",
    (Kind.OPERATOR, Position.DIFFUSION_X, Operand.DW):    "state.diffusion_X.dW",
    (Kind.OPERATOR, Position.DRIFT_THETA, Operand.NONE):  "generator.drift_theta",
    (Kind.ADMISSIBILITY, Position.NO_TERM, Operand.NONE): "governance",
    (Kind.INVARIANT, Position.NO_TERM, Operand.NONE):     "relation",
}


class Grammar:
    """The six ports, derived from the eight leaves' structural signatures."""

    def __init__(self) -> None:
        counts: dict[tuple, int] = {}
        for leaf in LEAVES:
            counts[leaf.structural_signature()] = \
                counts.get(leaf.structural_signature(), 0) + 1
        missing = set(counts) - set(_PATHS)
        if missing:  # pragma: no cover - guards a structural change
            raise Refused(f"structural class with no port path: {missing}")
        self.ports: list[Port] = [
            Port(_PATHS[sig], sig[0], sig[1], sig[2], n)
            for sig, n in counts.items()
        ]

    # -- placement ---------------------------------------------------------

    def port_for(self, term: Term) -> Port:
        for port in self.ports:
            if port.signature() == term.signature():
                return port
        raise Refused(
            f"{term.label}: no port admits {term.signature()}. "
            "The grammar refuses rather than guessing the nearest slot.")

    def place(self, term: Term) -> Port:
        port = self.port_for(term)
        if port.free == 0:
            raise Refused(f"{term.label}: {port.path} is full "
                          f"(capacity {port.capacity})")
        port.held.append(term)
        return port

    # -- recovery ----------------------------------------------------------

    def recover(self) -> dict[str, list[str]]:
        """What was placed, by port. Order within a port is not meaningful."""
        return {p.path: sorted(t.label for t in p.held)
                for p in self.ports if p.held}

    def recoverability(self) -> tuple[int, int]:
        """(distinguishable classes, leaves). The cost of the collisions.

        A term placed in a capacity-2 port cannot be told from its
        port-mate on recovery. This is what the pending refinements would
        buy, priced in the only currency that matters for a workspace.
        """
        return (len(self.ports), len(LEAVES))

    def constraints(self) -> list[str]:
        return [p.constraint() for p in self.ports]


# --------------------------------------------------------------------------
# Partial realization. A problem need not exercise every port.
# --------------------------------------------------------------------------

#: The seven format-level slots, in the order the format names them, paired
#: with the port each one lands in. J# and G# share a port: that is the
#: entry-29 collision, and it is what makes the fibre below larger than one.
SLOT_TO_PORT: tuple[tuple[str, str], ...] = (
    ("J#",    "state.drift_X.dH"),
    ("G#",    "state.drift_X.dH"),
    ("G~#",   "state.drift_X.dPhi"),
    ("Sigma", "state.diffusion_X.dW"),
    ("F",     "generator.drift_theta"),
    ("kappa", "governance"),
    ("gamma", "relation"),
)


class Realization:
    """One problem's placement. Unused ports are INACTIVE, never filled.

    A problem may exercise any subset of the format. The correct output for
    an unexercised port is that it is inactive -- not a plausible occupant
    invented to complete the picture. ``occupy`` is the only way a port
    becomes active, and it requires an actual term.
    """

    def __init__(self, name: str = "realization") -> None:
        self.name = name
        self.grammar = Grammar()

    def occupy(self, term: Term) -> Port:
        return self.grammar.place(term)

    def profile(self) -> tuple[bool, ...]:
        """Port activation, in the grammar's port order."""
        return tuple(bool(p.held) for p in self.grammar.ports)

    def inactive(self) -> list[str]:
        return [p.path for p in self.grammar.ports if not p.held]

    def report(self) -> dict[str, object]:
        """Occupied ports with their occupants; inactive ports named as such.

        Silence is not an option: every port appears, and an unexercised one
        says ``inactive`` rather than being omitted and later mistaken for an
        oversight.
        """
        out: dict[str, object] = {}
        for p in self.grammar.ports:
            out[p.path] = sorted(t.label for t in p.held) if p.held \
                else "inactive"
        return out


def port_profile(active_slots: frozenset[str]) -> tuple[str, ...]:
    """Map a seven-slot activation onto the ports it lights up.

    Not injective. ``{J#}``, ``{G#}`` and ``{J#, G#}`` all light exactly
    ``state.drift_X.dH`` and are the same object at this layer.
    """
    unknown = active_slots - {s for s, _ in SLOT_TO_PORT}
    if unknown:
        raise Refused(f"not format-level slots: {sorted(unknown)}")
    return tuple(sorted({path for slot, path in SLOT_TO_PORT
                         if slot in active_slots}))


def profile_fibres() -> dict[tuple[str, ...], int]:
    """How many of the 128 slot activations each port profile cannot tell
    apart. The measurement Q1 would have to be decided somewhere other than
    here: a layer that cannot separate J# from G# cannot rule on whether a
    G#-only profile is well formed."""
    from itertools import combinations
    slots = [s for s, _ in SLOT_TO_PORT]
    fibres: dict[tuple[str, ...], int] = {}
    for r in range(len(slots) + 1):
        for combo in combinations(slots, r):
            key = port_profile(frozenset(combo))
            fibres[key] = fibres.get(key, 0) + 1
    return fibres
