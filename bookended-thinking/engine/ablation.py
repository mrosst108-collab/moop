"""The ablation profile: which declarations were load-bearing.

Drop each declared constraint individually and resample. Constraints whose
removal leaves the distribution unmoved were inert. This is the null baseline
at finer grain -- C is the ablate-everything case -- and it identifies *which*
declarations did work rather than scoring their volume.

Pairwise ablation is the primary measurement, not an anomaly check, because
the individually-inert-but-jointly-generative case is the target rather than a
blind spot. It costs O(n^2) runs, which forces a cap on constraint count. The
cap is enforced here as an exception rather than a recommendation: it is the
structural version of the parsimony the rejected synthesis-per-specification
ratio tried to score.
"""

from __future__ import annotations

from itertools import combinations

from .divergence import (DEFAULT_ALPHA, DEFAULT_ITERATIONS, DEFAULT_SEED,
                         DEFAULT_THRESHOLD, _compare)

MAX_CONSTRAINTS = 6


class ConstraintCapExceeded(ValueError):
    pass


def _runs(n: int) -> int:
    return n + n * (n - 1) // 2


def check_cap(constraint_ids, cap: int = MAX_CONSTRAINTS) -> None:
    n = len(constraint_ids)
    if n > cap:
        raise ConstraintCapExceeded(
            f"{n} declared constraints require {_runs(n)} ablation runs "
            f"(cap {cap} -> {_runs(cap)}). Pairwise ablation is the primary "
            "measurement, so the cap binds on the declaration rather than on "
            "the measurement. Reduce the declarations."
        )


def single_profile(full, dropped: dict, threshold=DEFAULT_THRESHOLD, alpha=DEFAULT_ALPHA,
                   iterations=DEFAULT_ITERATIONS, seed=DEFAULT_SEED) -> dict:
    """``dropped`` maps constraint id -> samples generated with it removed."""
    check_cap(list(dropped))
    out = {}
    for offset, (cid, samples) in enumerate(sorted(dropped.items())):
        cmp = _compare(full, samples, threshold, alpha, iterations, seed + offset)
        out[cid] = {**cmp, "inert": not cmp["moved"]}
    return out


def pairwise_profile(full, dropped_pairs: dict, threshold=DEFAULT_THRESHOLD,
                     alpha=DEFAULT_ALPHA, iterations=DEFAULT_ITERATIONS,
                     seed=DEFAULT_SEED) -> dict:
    """``dropped_pairs`` maps frozenset({a, b}) -> samples with both removed."""
    out = {}
    for offset, (pair, samples) in enumerate(sorted(dropped_pairs.items(), key=lambda kv: sorted(kv[0]))):
        cmp = _compare(full, samples, threshold, alpha, iterations, seed + 1000 + offset)
        out[tuple(sorted(pair))] = {**cmp, "inert": not cmp["moved"]}
    return out


def required_pairs(constraint_ids) -> list:
    check_cap(constraint_ids)
    return [frozenset(p) for p in combinations(sorted(constraint_ids), 2)]


def profile(full, dropped: dict, dropped_pairs: dict | None = None, **kw) -> dict:
    singles = single_profile(full, dropped, **kw)
    pairs = pairwise_profile(full, dropped_pairs, **kw) if dropped_pairs else {}

    inert_alone = {cid for cid, r in singles.items() if r["inert"]}
    jointly_generative = [
        pair for pair, r in pairs.items()
        if not r["inert"] and set(pair) <= inert_alone
    ]

    missing = []
    if dropped_pairs is not None:
        have = {frozenset(p) for p in pairs}
        missing = [tuple(sorted(p)) for p in required_pairs(list(dropped)) if p not in have]

    return {
        "singles": singles,
        "pairs": pairs,
        "inert_alone": sorted(inert_alone),
        "jointly_generative": [tuple(p) for p in jointly_generative],
        "coverage": {
            "pairs_expected": len(required_pairs(list(dropped))) if dropped else 0,
            "pairs_measured": len(pairs),
            "pairs_missing": missing,
        },
        "note": (
            "Constraints individually inert but jointly generative are the "
            "target, not an anomaly. A profile with missing pairs is a partial "
            "measurement and is reported as such rather than summarised as if "
            "it were complete."
        ),
    }
