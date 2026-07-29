"""C (constraint strength) and the interaction test.

Both are categorical. The outcome of a run is the *set* of cells the bridge
classifier reported, so distributions are over frozensets of cells and the
divergence used is total variation -- bounded, interpretable, and not liable to
the zero-probability blowup that makes KL unusable on small resamples.

On the representation question: measuring interaction in grid coordinates is
the use the grid is *qualified* for. Nothing about the grid is under test here
-- the claim is only that distributions diverge -- and the grid's virtue is
that it does not reproduce the model's own ambient ontology, which an embedding
metric would. The residual dependency is unchanged: whatever applies the grid
must itself be anchored, and naive human raters remain the only anchor
identified. That anchor is not in this program.
"""

from __future__ import annotations

import math
import random
from collections import Counter

DEFAULT_ITERATIONS = 2000
DEFAULT_SEED = 20260729
DEFAULT_THRESHOLD = 0.25
DEFAULT_ALPHA = 0.05


def outcome(cells) -> frozenset:
    """Canonical categorical outcome for one response."""
    return frozenset(tuple(c) for c in cells)


def distribution(samples) -> dict:
    n = len(samples)
    if n == 0:
        return {}
    counts = Counter(samples)
    return {k: v / n for k, v in counts.items()}


def total_variation(p: dict, q: dict) -> float:
    keys = set(p) | set(q)
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in keys)


def permutation_p(samples_a, samples_b, iterations=DEFAULT_ITERATIONS, seed=DEFAULT_SEED) -> float:
    """Deterministic label-shuffle test. Seeded: the same inputs give the same p."""
    a, b = list(samples_a), list(samples_b)
    if not a or not b:
        return 1.0
    observed = total_variation(distribution(a), distribution(b))
    pool = a + b
    rng = random.Random(seed)
    hits = 0
    for _ in range(iterations):
        rng.shuffle(pool)
        if total_variation(distribution(pool[: len(a)]), distribution(pool[len(a):])) >= observed:
            hits += 1
    return (hits + 1) / (iterations + 1)


def _compare(x, y, threshold, alpha, iterations, seed) -> dict:
    tv = total_variation(distribution(x), distribution(y))
    p = permutation_p(x, y, iterations, seed)
    return {
        "tv": tv,
        "p": p,
        "n": (len(x), len(y)),
        "moved": tv >= threshold and p <= alpha,
    }


def constraint_strength(conditioned, null_baseline, threshold=DEFAULT_THRESHOLD,
                        alpha=DEFAULT_ALPHA, iterations=DEFAULT_ITERATIONS,
                        seed=DEFAULT_SEED) -> dict:
    """C: did the student's input move the distribution away from the model's default?

    ``null_baseline`` is the model's output distribution for the task given
    minimal input. Without that run there is no evidence the student's
    contribution was causal rather than the model's default behaviour, so this
    function refuses rather than returning a number.
    """
    if not null_baseline:
        return {
            "refused": True,
            "reason": (
                "No null-baseline samples. C is divergence from P(Y|null); "
                "without the null run, C is not defined and any number here "
                "would be the model's default behaviour reported as the "
                "student's contribution."
            ),
        }
    result = _compare(conditioned, null_baseline, threshold, alpha, iterations, seed)
    result["refused"] = False
    result["reading"] = "input moved the distribution" if result["moved"] else "input left the distribution where it was"
    return result


def interaction(ab, a_only, b_only, threshold=DEFAULT_THRESHOLD, alpha=DEFAULT_ALPHA,
                iterations=DEFAULT_ITERATIONS, seed=DEFAULT_SEED) -> dict:
    """Synthesis occurred iff P(Y|A,B) differs from P(Y|A) AND from P(Y|B).

    If the joint distribution matches one marginal, the model followed that
    pole rather than bridging two -- however large the displacement looks.
    This is the criterion; the other quantities are instruments for it. It is
    necessary for synthesis and not sufficient for value: a bridge can be
    stable, jointly dependent and worthless, and nothing here says otherwise.
    """
    vs_a = _compare(ab, a_only, threshold, alpha, iterations, seed)
    vs_b = _compare(ab, b_only, threshold, alpha, iterations, seed + 1)
    jointly = vs_a["moved"] and vs_b["moved"]

    followed = None
    if not jointly:
        if not vs_a["moved"] and vs_b["moved"]:
            followed = "A"
        elif not vs_b["moved"] and vs_a["moved"]:
            followed = "B"
        else:
            followed = "neither"

    return {
        "vs_A": vs_a,
        "vs_B": vs_b,
        "jointly_dependent": jointly,
        "followed_pole": followed,
        "verdict": "synthesis" if jointly else "no synthesis",
        "sufficiency_note": (
            "Interaction is necessary but not sufficient for value. It "
            "establishes that synthesis occurred, not that it should be retained. "
            "Retention is a closure act and is not scored here."
        ),
    }
