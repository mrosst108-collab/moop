"""Path-level measurement: gamma computed, not recognised.

kappa is observationally local -- a classifier can decide admissible or
inadmissible from the object in front of it. gamma is observationally
historical: a commutator is a property of two trajectories and their ordering,
so no single classification can carry it. Asking a classifier to *recognise*
gamma was the wrong abstraction. Recognition belongs to operators; measurement
belongs to trajectory analysis.

So the classifier types the constituent operations and never meets the
commutator concept, and this module composes what it returned:

    classifier -> operator labels per step -> engine -> gamma

Three things the decomposition buys, in descending order of importance:

1. The classifier no longer needs gamma's definition, so the definition can
   leave the rendered prompt. That was the leak declared as this tree's softest
   spot.
2. Order fidelity becomes checkable. A run that declared G# then G~# but was
   typed the other way round did not do what it said, and its trajectory is
   excluded and counted rather than silently averaged in.
3. The cell-level and path-level results become a cross-check on each other
   (see ``cross_check``), which neither gives alone.

What it does not buy: a clean test. See ``NOTE_ON_THE_TRADE`` below.
"""

from __future__ import annotations

from .divergence import (DEFAULT_ALPHA, DEFAULT_ITERATIONS, DEFAULT_SEED,
                         DEFAULT_THRESHOLD, _compare, outcome)

NOTE_ON_THE_TRADE = (
    "Removing gamma's definition from the prompt does not make the cell-level "
    "test clean; it trades one bias for another. With the definition present "
    "the classifier was told most of what the void conjecture predicts. With it "
    "absent the classifier is likelier to miss a genuine cell-level gamma, "
    "which biases toward confirming the conjecture. Neither direction is "
    "neutral. The path-level measurement is what carries the gamma claim now; "
    "the cell-level test is demoted to a weak cross-check."
)


def steps_of(trajectory) -> list:
    return trajectory.get("steps") or []


def location(step) -> frozenset:
    """Where a step is, as distinct from how it got there.

    A cell is an operator instantiated within a layer: the operator is the
    *move* and the layer is the *place*. The endpoint of a trajectory must
    therefore be read off the layers alone. Including the operator would make
    the arms differ by construction -- arm A necessarily ends with the second
    declared operator and arm B with the other one -- and every pair would
    noncommute trivially, which is a measurement of the experimental design
    rather than of the operators.
    """
    return frozenset(c[0] for c in step if c[0])


def endpoint(trajectory):
    steps = steps_of(trajectory)
    return location(steps[-1]) if steps else frozenset()


def route(trajectory):
    """The ordered sequence of places visited."""
    return tuple(location(step) for step in steps_of(trajectory))


def observed_order(trajectory) -> tuple:
    """The operator labels the classifier assigned, one step at a time."""
    order = []
    for step in steps_of(trajectory):
        objects = [c[1] for c in step if c[1] not in ("none", "uncertain")]
        order.append(tuple(sorted(set(objects))))
    return tuple(order)


def order_fidelity(trajectory) -> dict:
    """Did the run perform the order it declared?"""
    declared = tuple(trajectory.get("declared_order") or ())
    observed = observed_order(trajectory)
    if not declared:
        return {"checked": False, "faithful": None,
                "reason": "no declared order to check against"}
    if len(observed) != len(declared):
        return {"checked": True, "faithful": False, "declared": declared,
                "observed": observed,
                "reason": f"{len(declared)} operations declared, {len(observed)} steps classified"}
    mismatches = [
        {"step": i, "declared": d, "observed": o}
        for i, (d, o) in enumerate(zip(declared, observed)) if d not in o
    ]
    return {
        "checked": True,
        "faithful": not mismatches,
        "declared": declared,
        "observed": observed,
        "mismatches": mismatches,
        "reason": "" if not mismatches else "the run did not perform the order it declared",
    }


def partition(arm) -> dict:
    faithful, unfaithful = [], []
    for traj in arm:
        verdict = order_fidelity(traj)
        (faithful if verdict.get("faithful") is not False else unfaithful).append(
            {"trajectory": traj, "fidelity": verdict}
        )
    return {"faithful": faithful, "excluded": unfaithful}


def noncommutation(arm_a, arm_b, threshold=DEFAULT_THRESHOLD, alpha=DEFAULT_ALPHA,
                   iterations=DEFAULT_ITERATIONS, seed=DEFAULT_SEED) -> dict:
    """Does order change where the trajectory ends up?

    Endpoints carry the commutator: [A,B] is the difference between where
    A-then-B lands and where B-then-A lands. Route divergence is reported
    separately because two orders can trivially differ in the middle -- that is
    what ordering *is* -- and reading that as noncommutation would find order
    dependence everywhere.
    """
    part_a, part_b = partition(arm_a), partition(arm_b)
    ends_a = [endpoint(e["trajectory"]) for e in part_a["faithful"]]
    ends_b = [endpoint(e["trajectory"]) for e in part_b["faithful"]]
    paths_a = [route(e["trajectory"]) for e in part_a["faithful"]]
    paths_b = [route(e["trajectory"]) for e in part_b["faithful"]]

    excluded = len(part_a["excluded"]) + len(part_b["excluded"])
    if not ends_a or not ends_b:
        return {
            "refused": True,
            "reason": (
                "no order-faithful trajectories in one or both arms. A run that "
                "did not perform the order it declared cannot measure the effect "
                "of that order."
            ),
            "excluded": excluded,
        }

    endpoints = _compare(ends_a, ends_b, threshold, alpha, iterations, seed)
    interiors = _compare(paths_a, paths_b, threshold, alpha, iterations, seed + 7)

    return {
        "refused": False,
        "endpoints": endpoints,
        "routes": interiors,
        "noncommutes": endpoints["moved"],
        "excluded": excluded,
        "n_faithful": (len(ends_a), len(ends_b)),
        "reading": (
            "order changed where the trajectory landed" if endpoints["moved"]
            else ("order changed the route but not the endpoint"
                  if interiors["moved"] else "order changed nothing observable")
        ),
    }


def gamma(arm_a, arm_b, ontology, **kw) -> dict:
    """Measure gamma -- and refuse the label for any pair that is not the defined one.

    gamma is defined as a specific commutator. Any other operator pair measures
    order dependence in general, which may or may not be gamma; treating every
    noncommutativity result as evidence for one particular commutator is the
    mistake the arms are separated to avoid.
    """
    defined = tuple(ontology.dynamics["gamma"].commutator_of or ())
    pair_a = _pair_of(arm_a)
    pair_b = _pair_of(arm_b)

    result = noncommutation(arm_a, arm_b, **kw)
    result["pair"] = {"arm_a": pair_a, "arm_b": pair_b, "defined_commutator": defined}

    if pair_a is None or pair_b is None:
        result["is_gamma"] = False
        result["label_refused_because"] = "an arm declares no operator order"
        return result
    if set(pair_a) != set(pair_b):
        result["is_gamma"] = False
        result["label_refused_because"] = "the two arms are not the same pair in two orders"
        return result
    if set(pair_a) != set(defined):
        result["is_gamma"] = False
        result["label_refused_because"] = (
            f"{tuple(sorted(pair_a))} is not the defined commutator {defined}. "
            "This measures order dependence, not gamma."
        )
        return result
    if pair_a == pair_b:
        result["is_gamma"] = False
        result["label_refused_because"] = "both arms declare the same order; nothing is being reversed"
        return result

    result["is_gamma"] = True
    result["verdict"] = "gamma != 0" if result.get("noncommutes") else "gamma = 0 under the conditions tested"
    return result


def _pair_of(arm):
    orders = {tuple(t.get("declared_order") or ()) for t in arm}
    if len(orders) != 1:
        return None
    only = orders.pop()
    return only if len(only) == 2 else None


CROSS_CHECK = {
    (True, False): (
        "path_level_supported",
        "Order changes the endpoint and no cell was typed gamma: gamma has a "
        "referent one level up, which is what the path-level proposal predicts.",
    ),
    (False, False): (
        "gamma_inert",
        "No order effect and no cell-level gamma. gamma is not merely "
        "unaddressable at cell level -- it is inert under the conditions tested, "
        "and the path-level proposal loses its only current support.",
    ),
    (True, True): (
        "classifier_relocated",
        "Order dependence is real, and the classifier also put gamma at cell "
        "level. That is a typing question about the classifier, not evidence "
        "for or against the void conjecture.",
    ),
    (False, True): (
        "label_without_operation",
        "Cells typed gamma while no order effect exists. The classifier is "
        "typing on the name rather than the operation -- the Goodhart signature "
        "the design exists to detect, here caught in the instrument itself.",
    ),
}


def cross_check(path_result: dict, cell_level_gamma_count: int) -> dict:
    """The 2x2 that neither instrument gives alone."""
    if path_result.get("refused"):
        return {"reading": "undetermined", "detail": path_result.get("reason", "")}
    key = (bool(path_result.get("noncommutes")), cell_level_gamma_count > 0)
    reading, detail = CROSS_CHECK[key]
    return {
        "reading": reading,
        "detail": detail,
        "noncommutes": key[0],
        "cell_level_gamma": cell_level_gamma_count,
        "caveat": NOTE_ON_THE_TRADE,
    }
