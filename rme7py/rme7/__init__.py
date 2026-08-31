"""RME-7 primitives as a warranted class hierarchy, with executable witnesses."""

from rme7.primitives import (  # noqa: F401
    Algebra, Kind, Operand, Position, Primitive,
    Operator, AdmissibilityStructure, Invariant,
    StateOperator, GeneratorOperator, DriftOperator, DiffusionOperator,
    EnergyDrift, PurposeDrift,
    ConservativeTransport, DissipativeDescent, TeleologicalConfinement,
    SelfNoise, Channel, AutopoieticFeedback,
    StructuralAdmissibility, PathDependence, SLOTS,
)
from rme7 import witness  # noqa: F401

__all__ = ["Algebra", "Kind", "Operand", "Position", "Primitive", "SLOTS", "witness"]
