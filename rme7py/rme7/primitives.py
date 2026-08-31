"""The seven RME-7 primitives as a class hierarchy.

Every subclassing step in this module is licensed by a property the format
RECORDS, and each class names that property in its ``WARRANT``. Nothing here
is nested by resemblance, by convenience, or by a dependency ordering.

That constraint is not decoration. A hierarchy over the seven slots is exactly
where an implementation convenience can become grammar: pick a nesting, and
you have silently asserted a dependency order. So the rule for this module is

    a class may subclass another only when a recorded property distinguishes
    the child from its siblings.

The seven are typed PLACEHOLDERS in a structural grammar, not operators whose
mathematics is settled. This module realizes the grammar's type distinctions;
it does not implement ASDG and does not claim to know what J# ultimately is.
The question a class answers is never "what is this operator?" but "what
recorded property distinguishes the thing in this position from the things in
the others?"

That distinction is what makes an unresolved placeholder acceptable. Where the
recorded properties do not separate two leaves, the two leaves stay
unseparated, and the module says so. Inventing a distinction to complete the
partition would be worse than carrying the collision.

THE STRUCTURAL SIGNATURE -- three properties, recorded in this repository's
carried source (``prompts/asdg-rme7.md`` section 2, S_v5):

    KIND      operator / admissibility / invariant
              -- an additive term, a gate, or something in no equation at all.

    POSITION  drift of X, diffusion of X, drift of theta
              -- the state equation has TWO positions, not one: the
                 metriplectic triple sits under dt and Sigma under dW.

    OPERAND   dH, dPhi, dW
              -- J#(dH) and G#(dH) consume the same one-form; G~#(dPhi) does
                 not. That is a relation among the drift operators written
                 into the equation itself.

Over the eight leaves those three yield SIX classes, not eight. Two pairs
collide, and both collisions are ACCEPTED rather than repaired:

    J# == G#          both operators, both drift of X, both consuming dH
    Sigma_ii == Sigma_ij   both operators, both diffusion of X, both on dW

PENDING REFINEMENTS -- properties that would separate them, each carried with
its source and status, and none of them structural:

    INDEX     diagonal / off-diagonal.  Source: S_C1.  Status: STIPULATED.
              Written in the count-aligned variant, ABSENT from S_v5. See
              section 2.1 of the spec: no property reads RECORDED against S_C1
              while its provenance stands.

    ALGEBRA   antisymmetric / positive semidefinite.  Status: DERIVED.
              Entailed by the recorded removal witnesses (Hdot = 0 for J#,
              Hdot < 0 for G#) because <v, Mv> = 0 for all v iff M is
              antisymmetric and >= 0 iff M is positive semidefinite. The
              witness is the ground; the algebraic form is what it entails.

Keeping the three apart from the two is the whole point: it is the difference
between a property the format states, one another source states, and one an
argument supplies. Collapsing them would let a derivation pass as a record.

What is deliberately absent: no leaf primitive subclasses another. J# is not
a parent of G#. The hierarchy branches on properties, never on one primitive
depending on another, because the dependency orderings on record disagree
with each other and none of them is grammar.
"""

from __future__ import annotations

from abc import ABC
from enum import Enum
from typing import ClassVar


class Kind(Enum):
    """The 5 + 1 + 1 partition. Recorded in the retrieved ontology."""

    OPERATOR = "appears as an additive term; produces tangent vectors"
    ADMISSIBILITY = "appears as a multiplicative gate; fail-only verdict"
    INVARIANT = "appears in no equation; computed from trajectories"


class Position(Enum):
    """Where in the canonical form a term stands."""

    DRIFT_X = "the dt term of dX"
    DIFFUSION_X = "the dW term of dX"
    DRIFT_THETA = "the dt term of dtheta"
    NO_TERM = "no term in either equation"


class Operand(Enum):
    """What the operator is applied to."""

    DH = "dH, the energy one-form"
    DPHI = "dPhi, the purpose one-form"
    DW = "a Wiener increment"
    NONE = "not applied to a one-form"


class Index(Enum):
    """Diagonal or off-diagonal. Recorded in the canonical form."""

    DIAGONAL = "Sigma_ii: i to i"
    OFF_DIAGONAL = "Sigma_ij: j to i"
    NOT_INDEXED = "carries no object index pair"


class Algebra(Enum):
    """The algebraic property that gives an operator its office.

    These are what make the removal witnesses checkable: an antisymmetric
    operator conserves what it is applied to, a positive-semidefinite one
    dissipates it. See ``rme7.witness``.
    """

    ANTISYMMETRIC = "M^T = -M; conserves its operand"
    POSITIVE_SEMIDEFINITE = "x^T M x >= 0; dissipates its operand"
    NONE = "no algebraic form declared"


class Primitive(ABC):
    """A typed format-level PLACEHOLDER in the grammar.

    Eight concrete leaves descend from here -- the seven slots, with Sigma
    carrying two instance forms -- and no leaf descends from another. A leaf
    names a position in the format; it does not claim settled semantics for
    what occupies that position.
    """

    SYMBOL: ClassVar[str] = "?"
    NAME: ClassVar[str] = "primitive"
    WARRANT: ClassVar[str] = "the seven typed format-level slots"
    KIND: ClassVar[Kind | None] = None
    POSITION: ClassVar[Position | None] = None
    OPERAND: ClassVar[Operand] = Operand.NONE
    INDEX: ClassVar[Index] = Index.NOT_INDEXED
    ALGEBRA: ClassVar[Algebra] = Algebra.NONE
    #: What the ALGEBRA is derived from. Empty when none is declared.
    ALGEBRA_FROM_WITNESS: ClassVar[str] = ""

    #: Non-structural properties, each with the source that carries it and
    #: its custody status. Neither may be read as RECORDED against S_v5.
    PENDING: ClassVar[dict[str, tuple[str, str]]] = {
        "INDEX":   ("S_C1", "STIPULATED"),
        "ALGEBRA": ("removal witnesses", "DERIVED"),
    }

    @classmethod
    def structural_signature(cls) -> tuple:
        """The three properties recorded in S_v5.

        This does NOT separate all eight leaves, and is not meant to. Two
        pairs collide; see ``Primitive.PENDING``.
        """
        return (cls.KIND, cls.POSITION, cls.OPERAND)

    @classmethod
    def discriminants(cls) -> tuple:
        """The structural signature with every pending refinement applied.

        Separates all eight -- but only by importing two properties this
        repository does not record. Use ``structural_signature`` for what the
        grammar actually distinguishes today.
        """
        return (cls.KIND, cls.POSITION, cls.OPERAND, cls.INDEX, cls.ALGEBRA)

    @classmethod
    def pending_refinements(cls) -> dict[str, tuple[object, str, str]]:
        """Property -> (value, source, status), for the non-structural two."""
        return {name: (getattr(cls, name), src, status)
                for name, (src, status) in Primitive.PENDING.items()}

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"{type(self).__name__}({self.SYMBOL})"

    @classmethod
    def lineage(cls) -> list[type[Primitive]]:
        """This class's chain up to Primitive, root first."""
        chain = [c for c in cls.__mro__ if isinstance(c, type)
                 and issubclass(c, Primitive)]
        return list(reversed(chain))

    @classmethod
    def warrants(cls) -> list[tuple[str, str]]:
        """Each step of the lineage with the property that licenses it.

        This is the point of the module: any class can be asked why it sits
        where it sits, and the answer is a recorded property rather than a
        design preference.
        """
        return [(c.__name__, c.WARRANT) for c in cls.lineage()]

    @classmethod
    def depth(cls) -> int:
        return len(cls.lineage())


# --------------------------------------------------------------------------
# KIND: the first branching. Three kinds, and the two non-operators can never
# be treated as terms because they are not Operators.
# --------------------------------------------------------------------------

class Operator(Primitive):
    WARRANT = "KIND: appears as an additive term in the equations"
    KIND = Kind.OPERATOR


class AdmissibilityStructure(Primitive):
    WARRANT = "KIND: a gate rather than a term; fail-only verdict"
    KIND = Kind.ADMISSIBILITY
    POSITION = Position.NO_TERM


class Invariant(Primitive):
    WARRANT = "KIND: in no equation; computed from trajectories"
    KIND = Kind.INVARIANT
    POSITION = Position.NO_TERM


# --------------------------------------------------------------------------
# POSITION: which equation, and where in it.
# --------------------------------------------------------------------------

class StateOperator(Operator):
    WARRANT = "POSITION: stands in dX"


class GeneratorOperator(Operator):
    WARRANT = "POSITION: stands in dtheta, never in dX"
    POSITION = Position.DRIFT_THETA


class DriftOperator(StateOperator):
    WARRANT = "POSITION: under dt -- the deterministic part of dX"
    POSITION = Position.DRIFT_X


class DiffusionOperator(StateOperator):
    WARRANT = "POSITION: under dW -- the stochastic part of dX"
    POSITION = Position.DIFFUSION_X
    OPERAND = Operand.DW


# --------------------------------------------------------------------------
# OPERAND: which one-form a drift operator consumes. This is the split the
# canonical form writes and an earlier transcription of it dropped.
# --------------------------------------------------------------------------

class EnergyDrift(DriftOperator):
    WARRANT = "OPERAND: applied to dH, the energy one-form"
    OPERAND = Operand.DH


class PurposeDrift(DriftOperator):
    WARRANT = "OPERAND: applied to dPhi, the purpose one-form"
    OPERAND = Operand.DPHI


# --------------------------------------------------------------------------
# The seven leaves.
# --------------------------------------------------------------------------

class ConservativeTransport(EnergyDrift):
    """J#. Circulates without converging."""

    WARRANT = "ALGEBRA (pending, derived): antisymmetric, so Hdot = 0 -- it\n        conserves H. Not structural: J# and G# are one class under the\n        recorded signature, and that collision is carried, not repaired."
    ALGEBRA_FROM_WITNESS = "Hdot = 0: conservative structure loses its office"
    SYMBOL = "J#"
    NAME = "conservative transport"
    ALGEBRA = Algebra.ANTISYMMETRIC


class DissipativeDescent(EnergyDrift):
    """G#. The only slot whose office is convergence."""

    WARRANT = "ALGEBRA (pending, derived): positive semidefinite, so Hdot <= 0.\n        Not structural: see ConservativeTransport."
    ALGEBRA_FROM_WITNESS = "Hdot < 0: no dedicated convergent office"
    SYMBOL = "G#"
    NAME = "dissipative descent"
    ALGEBRA = Algebra.POSITIVE_SEMIDEFINITE


class TeleologicalConfinement(PurposeDrift):
    """G~#. Confines without converging; never a gradient descent."""

    WARRANT = "ALGEBRA (pending, derived): antisymmetric, so Phidot = 0 --\n        confines. Separated from the J#/G# pair structurally, by OPERAND."
    ALGEBRA_FROM_WITNESS = "Phidot = 0: confinement collapses into descent"
    SYMBOL = "G~#"
    NAME = "teleological confinement"
    ALGEBRA = Algebra.ANTISYMMETRIC


class SelfNoise(DiffusionOperator):
    """Sigma_ii. Intrinsic stochastic exploration."""

    WARRANT = "INDEX (pending, stipulated): the diagonal instance, i to i.\n        Written in S_C1, absent from S_v5, so this is an instance placeholder\n        whose distinguishing property this repository does not record."
    INDEX = Index.DIAGONAL
    SYMBOL = "Sigma_ii"
    NAME = "stochastic injection"


class Channel(DiffusionOperator):
    """Sigma_ij = A_i . kappa_i . T_ij. The one route between objects.

    Sigma_ii and Sigma_ij are INSTANCES of one slot, not two slots. Splitting
    Sigma into two primitives would corrupt the 5 + 1 + 1 count; subclassing
    one DiffusionOperator says exactly what is meant -- same slot, two typed
    instances -- which a flat enumeration cannot.
    """

    WARRANT = "INDEX (pending, stipulated): the off-diagonal instance, j to i.\n        Same custody as SelfNoise."
    INDEX = Index.OFF_DIAGONAL
    SYMBOL = "Sigma_ij"
    NAME = "typed coupling"

    STAGES: ClassVar[tuple[str, str, str]] = ("translate", "admit", "assimilate")


class AutopoieticFeedback(GeneratorOperator):
    """F. Evolves the generator. Never a term in the state equation."""

    WARRANT = "the sole generator-equation term"
    SYMBOL = "F"
    NAME = "autopoietic feedback"


class StructuralAdmissibility(AdmissibilityStructure):
    """kappa. Admits or refuses a proposed generator change."""

    WARRANT = "the sole admissibility structure; a verdict, never a score"
    SYMBOL = "kappa"
    NAME = "structural admissibility"


class PathDependence(Invariant):
    """gamma = [G#, G~#]. Measured from trajectories, never applied."""

    WARRANT = "the sole invariant; the commutator of the two narrowing operators"
    SYMBOL = "gamma"
    NAME = "path dependence"
    DERIVES_FROM: ClassVar[tuple[type[Primitive], type[Primitive]]] = (
        DissipativeDescent,
        TeleologicalConfinement,
    )


#: The seven slots. Sigma appears once, as its two instance classes.
SLOTS: tuple[type[Primitive], ...] = (
    ConservativeTransport,
    DissipativeDescent,
    TeleologicalConfinement,
    DiffusionOperator,          # Sigma, as one slot
    AutopoieticFeedback,
    StructuralAdmissibility,
    PathDependence,
)
