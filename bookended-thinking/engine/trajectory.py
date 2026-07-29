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
    """Measure the endpoint comparison, and separate observation from inference.

    Two things are kept apart on every return path.

    ``observation`` is what was measured: an endpoint change under stated
    conditions. ``inference`` is what the architecture may conclude from it,
    and it exists only when the tested pair is the defined commutator. The
    endpoint comparison is never rendered as though it were already the
    invariant -- the general arm can establish order dependence, and it cannot
    establish gamma.
    """
    defined = tuple(ontology.dynamics["gamma"].commutator_of or ())
    pair_a, pair_b = _pair_of(arm_a), _pair_of(arm_b)

    result = noncommutation(arm_a, arm_b, **kw)
    result["pair"] = {"arm_a": pair_a, "arm_b": pair_b, "defined_commutator": defined}
    result["observation"] = _observation(result, pair_a)
    result["inference"] = None

    refusal = None
    if pair_a is None or pair_b is None:
        refusal = "an arm declares no operator order"
    elif set(pair_a) != set(pair_b):
        refusal = "the two arms are not the same pair in two orders"
    elif set(pair_a) != set(defined):
        refusal = (
            f"{tuple(sorted(pair_a))} is not the defined commutator {defined}. "
            "This measures order dependence; it cannot establish gamma."
        )
    elif pair_a == pair_b:
        refusal = "both arms declare the same order; nothing is being reversed"
    elif result.get("refused"):
        refusal = "no measurement to infer from"

    if refusal is not None:
        result["is_gamma"] = False
        result["inference_refused_because"] = refusal
        return result

    result["is_gamma"] = True
    result["inference"] = _inference(result, pair_a)
    return result


def _observation(result, pair_a) -> str:
    if result.get("refused"):
        return "no measurement"
    names = "/".join(sorted(pair_a)) if pair_a else "an unstated pair"
    return (
        f"endpoint change observed under the tested {names} conditions"
        if result.get("noncommutes")
        else f"no endpoint change observed under the tested {names} conditions"
    )


def _inference(result, pair_a) -> str:
    names = "/".join(sorted(pair_a))
    return (
        f"supports gamma != 0 for the tested pair ({names}) under the conditions tested"
        if result.get("noncommutes")
        else f"supports gamma = 0 for the tested pair ({names}) under the conditions tested"
    )


def gamma_labels(arm) -> list:
    """Per trajectory: did the classifier type any cell as gamma?"""
    return [
        any(c[1] == "gamma" for step in steps_of(t) for c in step)
        for t in arm
    ]


def relocation_profile(arm_a, arm_b, threshold=DEFAULT_THRESHOLD, alpha=DEFAULT_ALPHA,
                       iterations=DEFAULT_ITERATIONS, seed=DEFAULT_SEED) -> dict:
    """Do the classifier's cell-level gamma labels covary with the ordering?

    A label that appears at the same rate in both orders is not tracking order
    -- it is a habit, or ontology leaking in from somewhere. A label that
    appears preferentially in one order is tracking something real about the
    composition and assigning it to the wrong level. The two look identical in
    a raw count, which is why the count alone under-determines the
    ``classifier_relocated`` reading.
    """
    labels_a, labels_b = gamma_labels(arm_a), gamma_labels(arm_b)
    total = sum(labels_a) + sum(labels_b)
    profile = {
        "total": total,
        "n": (len(labels_a), len(labels_b)),
        "rate": (
            (sum(labels_a) / len(labels_a)) if labels_a else None,
            (sum(labels_b) / len(labels_b)) if labels_b else None,
        ),
    }
    if total == 0:
        profile["verdict"] = "no_labels"
        return profile
    if not labels_a or not labels_b:
        profile["verdict"] = "undetermined"
        profile["reason"] = "one arm is empty; symmetry is not assessable"
        return profile

    comparison = _compare(labels_a, labels_b, threshold, alpha, iterations, seed + 13)
    profile["comparison"] = comparison
    profile["verdict"] = "asymmetric" if comparison["moved"] else "symmetric"
    return profile


def _pair_of(arm):
    orders = {tuple(t.get("declared_order") or ()) for t in arm}
    if len(orders) != 1:
        return None
    only = orders.pop()
    return only if len(only) == 2 else None


#: Endpoint change x how the classifier's cell-level gamma labels are distributed.
#: A raw label count cannot separate the middle column from the right one, which
#: is what left the original ``classifier_relocated`` reading under-determined.
CROSS_CHECK = {
    (True, "no_labels"): (
        "path_level_supported",
        "Order changes the endpoint and no cell was typed gamma: gamma has a "
        "referent one level up. This supports the path-level interpretation and "
        "leaves the cell ontology unresolved -- absence of a label is not proof "
        "that the cell is void.",
    ),
    (False, "no_labels"): (
        "gamma_inert",
        "No order effect and no cell-level gamma. gamma is not merely "
        "unaddressable at cell level -- it is inert under the conditions tested, "
        "and the path-level proposal loses its only current support.",
    ),
    (True, "asymmetric"): (
        "classifier_relocated",
        "Order dependence is real and the classifier's gamma labels covary with "
        "the ordering: it is tracking the phenomenon and assigning it to the "
        "wrong level. This is a live ontology question -- gamma may not be "
        "path-level in the way hypothesised -- not a classifier defect alone.",
    ),
    (True, "symmetric"): (
        "label_habit",
        "Order dependence is real, but the classifier's gamma labels appear at "
        "the same rate in both orders, so they are not tracking order. Label "
        "habit or ontology leaking in from somewhere, alongside a genuine "
        "endpoint effect it is not detecting.",
    ),
    (False, "asymmetric"): (
        "route_sensitive_labelling",
        "No endpoint effect, yet the gamma labels covary with the ordering. "
        "Consistent with the classifier tracking the route rather than the "
        "endpoint -- the conflation the endpoint/route split exists to prevent, "
        "here visible in the classifier instead of the measure.",
    ),
    (False, "symmetric"): (
        "label_without_operation",
        "Cells typed gamma while no order effect exists and the labels are "
        "indifferent to ordering. The classifier is typing on the name rather "
        "than the operation -- the Goodhart signature the design exists to "
        "detect, here caught in the instrument itself.",
    ),
}


def cross_check(path_result: dict, relocation: dict) -> dict:
    """The cell-level and path-level results read against each other.

    ``relocation`` is a ``relocation_profile``. Passing a bare count is refused:
    the count cannot distinguish a classifier tracking the ordering from one
    repeating a label, and those are different findings.
    """
    if not isinstance(relocation, dict):
        raise TypeError(
            "cross_check needs a relocation_profile, not a count. A raw count "
            "cannot separate classifier_relocated from label_habit."
        )
    if path_result.get("refused"):
        return {"reading": "undetermined", "detail": path_result.get("reason", ""),
                "relocation": relocation}

    moved = bool(path_result.get("noncommutes"))
    verdict = relocation.get("verdict", "no_labels")
    if verdict == "undetermined":
        return {
            "reading": "undetermined",
            "detail": "cell-level gamma labels present but their distribution is not assessable: "
                      + relocation.get("reason", ""),
            "relocation": relocation,
            "caveat": NOTE_ON_THE_TRADE,
        }

    reading, detail = CROSS_CHECK[(moved, verdict)]
    return {
        "reading": reading,
        "detail": detail,
        "noncommutes": moved,
        "relocation": relocation,
        "caveat": NOTE_ON_THE_TRADE,
    }
