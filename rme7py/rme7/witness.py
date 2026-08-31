"""The removal witnesses, made executable.

Three rows of the seven-witness matrix are statements of linear algebra and
nothing more. They need no manifold, no operator semantics, and no primary
source:

    Hdot   = 0     under an antisymmetric J#
    Hdot  <= 0     under a positive-semidefinite G#
    Phidot = 0     under an antisymmetric G~#

Each says an operator cannot do the office of another: circulation is not
descent, and confinement is not descent either. Checking them is the
difference between a table that asserts the offices are distinct and a test
that shows it.

These are MATHEMATICAL WITNESSES, not an RME-7 realization. They establish
that the declared algebraic forms have the consequences claimed for them. They
establish nothing about what J# is.

Matrices are lists of rows. No numpy: these are small, and a dependency for a
3x3 determinant is not a trade worth making.
"""

from __future__ import annotations

from itertools import combinations

Matrix = list[list[float]]
Vector = list[float]

TOL = 1e-12


def transpose(m: Matrix) -> Matrix:
    return [list(col) for col in zip(*m)]


def matvec(m: Matrix, v: Vector) -> Vector:
    return [sum(row[j] * v[j] for j in range(len(v))) for row in m]


def dot(a: Vector, b: Vector) -> float:
    return sum(x * y for x, y in zip(a, b))


def quadratic_form(m: Matrix, v: Vector) -> float:
    """<v, M v>. The rate at which M changes what it is applied to."""
    return dot(v, matvec(m, v))


def is_square(m: Matrix) -> bool:
    return bool(m) and all(len(row) == len(m) for row in m)


def is_antisymmetric(m: Matrix, tol: float = TOL) -> bool:
    """M^T = -M."""
    if not is_square(m):
        return False
    n = len(m)
    return all(abs(m[i][j] + m[j][i]) <= tol for i in range(n) for j in range(n))


def is_symmetric(m: Matrix, tol: float = TOL) -> bool:
    if not is_square(m):
        return False
    n = len(m)
    return all(abs(m[i][j] - m[j][i]) <= tol for i in range(n) for j in range(n))


def _determinant(m: Matrix) -> float:
    n = len(m)
    if n == 0:
        return 1.0
    if n == 1:
        return m[0][0]
    total = 0.0
    for j in range(n):
        minor = [row[:j] + row[j + 1:] for row in m[1:]]
        total += ((-1.0) ** j) * m[0][j] * _determinant(minor)
    return total


def is_positive_semidefinite(m: Matrix, tol: float = TOL) -> bool:
    """Symmetric with every PRINCIPAL minor non-negative.

    Leading principal minors alone characterise positive DEFINITENESS, not
    semidefiniteness -- diag(0, -1) has both leading minors zero and is
    indefinite. So every principal minor is checked, which is exponential and
    entirely acceptable at the sizes a witness needs.
    """
    if not is_symmetric(m, tol):
        return False
    n = len(m)
    for k in range(1, n + 1):
        for idx in combinations(range(n), k):
            sub = [[m[i][j] for j in idx] for i in idx]
            if _determinant(sub) < -tol:
                return False
    return True


# --- the three witnesses -------------------------------------------------

def conserves(m: Matrix, v: Vector, tol: float = TOL) -> bool:
    """<v, M v> == 0: M does not change what it is applied to.

    True for every antisymmetric M and every v -- which is why J# circulates
    and G~# confines, rather than either of them descending.
    """
    return abs(quadratic_form(m, v)) <= tol


def descends(m: Matrix, v: Vector, tol: float = TOL) -> bool:
    """<v, M v> >= 0, so the -M term is non-increasing.

    The sign convention follows the canonical form, where G# enters as
    -G#(dH): a positive-semidefinite G# gives Hdot <= 0.
    """
    return quadratic_form(m, v) >= -tol


def witness_conservative(j: Matrix, dh: Vector) -> tuple[bool, float]:
    """J#: antisymmetric, and Hdot = 0."""
    return (is_antisymmetric(j) and conserves(j, dh)), quadratic_form(j, dh)


def witness_dissipative(g: Matrix, dh: Vector) -> tuple[bool, float]:
    """G#: positive semidefinite, and Hdot = -<dH, G dH> <= 0."""
    return (is_positive_semidefinite(g) and descends(g, dh)), -quadratic_form(g, dh)


def witness_confining(gt: Matrix, dphi: Vector) -> tuple[bool, float]:
    """G~#: antisymmetric, and Phidot = 0. Confines without converging."""
    return (is_antisymmetric(gt) and conserves(gt, dphi)), quadratic_form(gt, dphi)
