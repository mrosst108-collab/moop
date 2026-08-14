"""Tests for gamma as a measured path-level invariant rather than a label."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import scoring, trajectory                          # noqa: E402
from engine.ontology import ROOT, Ontology, TypingRules         # noqa: E402

FAST = {"iterations": 200}
PW = "performed_within"


def traj(order, *step_objects, layer="L4"):
    return {
        "declared_order": list(order),
        "steps": [[(layer, obj, PW)] for obj in step_objects],
    }


def arm(order, *step_objects, n=16, layer="L4"):
    return [traj(order, *step_objects, layer=layer) for _ in range(n)]


class TestOrderFidelity(unittest.TestCase):
    def test_a_faithful_run_passes(self):
        v = trajectory.order_fidelity(traj(["G_sharp", "G_tilde_sharp"], "G_sharp", "G_tilde_sharp"))
        self.assertTrue(v["faithful"])

    def test_a_run_that_did_not_do_what_it_said_is_caught(self):
        v = trajectory.order_fidelity(traj(["G_sharp", "G_tilde_sharp"], "G_tilde_sharp", "G_sharp"))
        self.assertFalse(v["faithful"])
        self.assertEqual(len(v["mismatches"]), 2)
        self.assertIn("did not perform the order it declared", v["reason"])

    def test_step_count_mismatch_is_caught(self):
        v = trajectory.order_fidelity(traj(["G_sharp", "G_tilde_sharp"], "G_sharp"))
        self.assertFalse(v["faithful"])

    def test_unfaithful_trajectories_are_excluded_not_averaged_in(self):
        good = arm(["G_sharp", "G_tilde_sharp"], "G_sharp", "G_tilde_sharp", n=8)
        bad = arm(["G_sharp", "G_tilde_sharp"], "Sigma", "F", n=4)
        result = trajectory.noncommutation(
            good + bad, arm(["G_tilde_sharp", "G_sharp"], "G_tilde_sharp", "G_sharp", n=8), **FAST)
        self.assertEqual(result["excluded"], 4)
        self.assertEqual(result["n_faithful"], (8, 8))


def commuting_arms(end_a="L4", end_b="L4", mid_a="L4", mid_b="L4", n=16):
    a = [dict(declared_order=["G_sharp", "G_tilde_sharp"],
              steps=[[(mid_a, "G_sharp", PW)], [(end_a, "G_tilde_sharp", PW)]]) for _ in range(n)]
    b = [dict(declared_order=["G_tilde_sharp", "G_sharp"],
              steps=[[(mid_b, "G_tilde_sharp", PW)], [(end_b, "G_sharp", PW)]]) for _ in range(n)]
    return a, b


class TestNoncommutation(unittest.TestCase):
    def test_the_operator_label_cannot_discriminate_the_arms(self):
        """Endpoints are places, not moves -- otherwise every pair noncommutes trivially."""
        a, b = commuting_arms()
        self.assertEqual(trajectory.endpoint(a[0]), trajectory.endpoint(b[0]))
        self.assertNotEqual(trajectory.observed_order(a[0]), trajectory.observed_order(b[0]))

    def test_same_endpoint_different_route_is_not_noncommutation(self):
        a, b = commuting_arms(mid_a="L3", mid_b="L5")
        result = trajectory.noncommutation(a, b, **FAST)
        self.assertFalse(result["noncommutes"])
        self.assertTrue(result["routes"]["moved"])
        self.assertEqual(result["reading"], "order changed the route but not the endpoint")

    def test_different_endpoints_noncommute(self):
        a, b = commuting_arms(end_a="L4", end_b="L2")
        result = trajectory.noncommutation(a, b, **FAST)
        self.assertTrue(result["noncommutes"])
        self.assertEqual(result["reading"], "order changed where the trajectory landed")

    def test_no_faithful_trajectories_refuses(self):
        bad = arm(["G_sharp", "G_tilde_sharp"], "Sigma", "F", n=4)
        result = trajectory.noncommutation(bad, bad, **FAST)
        self.assertTrue(result["refused"])
        self.assertIn("cannot measure the effect", result["reason"])


class TestGammaLabel(unittest.TestCase):
    def setUp(self):
        self.ont = Ontology.load(ROOT)

    def test_the_defined_commutator_earns_the_label(self):
        a = arm(["G_sharp", "G_tilde_sharp"], "G_sharp", "G_tilde_sharp")
        b = arm(["G_tilde_sharp", "G_sharp"], "G_tilde_sharp", "G_sharp")
        result = trajectory.gamma(a, b, self.ont, **FAST)
        self.assertTrue(result["is_gamma"])
        self.assertEqual(result["pair"]["defined_commutator"], ("G_sharp", "G_tilde_sharp"))

    def test_a_general_pair_measures_order_dependence_not_gamma(self):
        a = arm(["J_sharp", "G_sharp"], "J_sharp", "G_sharp")
        b = arm(["G_sharp", "J_sharp"], "G_sharp", "J_sharp")
        result = trajectory.gamma(a, b, self.ont, **FAST)
        self.assertFalse(result["is_gamma"])
        self.assertIn("not the defined commutator", result["inference_refused_because"])
        self.assertIsNone(result["inference"])
        self.assertIn("endpoint change observed", result["observation"])
        self.assertIn("refused", result)

    def test_two_arms_of_the_same_order_reverse_nothing(self):
        a = arm(["G_sharp", "G_tilde_sharp"], "G_sharp", "G_tilde_sharp")
        result = trajectory.gamma(a, list(a), self.ont, **FAST)
        self.assertFalse(result["is_gamma"])
        self.assertIn("nothing is being reversed", result["inference_refused_because"])

    def test_gamma_zero_is_a_result_not_a_failure(self):
        a, b = commuting_arms()
        result = trajectory.gamma(a, b, self.ont, **FAST)
        self.assertTrue(result["is_gamma"])
        self.assertIn("no endpoint change observed under the tested", result["observation"])
        self.assertIn("supports gamma = 0 for the tested pair", result["inference"])
        self.assertEqual(result["reading"], "order changed nothing observable")


def with_gamma(arm, count, layer="L4"):
    """Mark the first ``count`` trajectories with a cell-level gamma label."""
    out = []
    for i, t in enumerate(arm):
        t = {"declared_order": list(t["declared_order"]),
             "steps": [list(step) for step in t["steps"]]}
        if i < count:
            t["steps"][0] = t["steps"][0] + [(layer, "gamma", PW)]
        out.append(t)
    return out


class TestRelocationProfile(unittest.TestCase):
    def test_no_labels(self):
        a, b = commuting_arms()
        self.assertEqual(trajectory.relocation_profile(a, b, **FAST)["verdict"], "no_labels")

    def test_labels_at_the_same_rate_in_both_orders_are_symmetric(self):
        a, b = commuting_arms()
        profile = trajectory.relocation_profile(with_gamma(a, 8), with_gamma(b, 8), **FAST)
        self.assertEqual(profile["verdict"], "symmetric")
        self.assertEqual(profile["rate"], (0.5, 0.5))
        self.assertEqual(profile["total"], 16)

    def test_labels_that_covary_with_order_are_asymmetric(self):
        a, b = commuting_arms()
        profile = trajectory.relocation_profile(with_gamma(a, 16), with_gamma(b, 0), **FAST)
        self.assertEqual(profile["verdict"], "asymmetric")
        self.assertEqual(profile["rate"], (1.0, 0.0))

    def test_marking_a_trajectory_does_not_break_its_order_fidelity(self):
        a, _ = commuting_arms()
        self.assertTrue(trajectory.order_fidelity(with_gamma(a, 1)[0])["faithful"])


class TestCrossCheck(unittest.TestCase):
    def setUp(self):
        self.moved = {"refused": False, "noncommutes": True}
        self.still = {"refused": False, "noncommutes": False}
        a, b = commuting_arms()
        self.none = trajectory.relocation_profile(a, b, **FAST)
        self.sym = trajectory.relocation_profile(with_gamma(a, 8), with_gamma(b, 8), **FAST)
        self.asym = trajectory.relocation_profile(with_gamma(a, 16), with_gamma(b, 0), **FAST)

    def test_the_six_readings(self):
        cases = [
            (self.moved, self.none, "path_level_supported"),
            (self.still, self.none, "gamma_inert"),
            (self.moved, self.asym, "classifier_relocated"),
            (self.moved, self.sym, "label_habit"),
            (self.still, self.asym, "route_sensitive_labelling"),
            (self.still, self.sym, "label_without_operation"),
        ]
        for path_result, relocation, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(trajectory.cross_check(path_result, relocation)["reading"], expected)

    def test_a_raw_count_is_refused_because_it_under_determines_the_reading(self):
        with self.assertRaises(TypeError) as ctx:
            trajectory.cross_check(self.moved, 3)
        self.assertIn("cannot separate classifier_relocated from label_habit", str(ctx.exception))

    def test_path_level_supported_leaves_the_cell_ontology_unresolved(self):
        cc = trajectory.cross_check(self.moved, self.none)
        self.assertIn("leaves the cell ontology unresolved", cc["detail"])

    def test_relocation_is_a_live_ontology_question_not_only_a_classifier_defect(self):
        cc = trajectory.cross_check(self.moved, self.asym)
        self.assertIn("may not be path-level in the way hypothesised", cc["detail"])

    def test_the_trade_is_carried_with_every_reading(self):
        cc = trajectory.cross_check(self.moved, self.none)
        self.assertIn("trades one bias for another", cc["caveat"])

    def test_a_refused_measurement_does_not_produce_a_reading(self):
        cc = trajectory.cross_check({"refused": True, "reason": "no faithful arms"}, self.none)
        self.assertEqual(cc["reading"], "undetermined")


class TestWithholding(unittest.TestCase):
    def setUp(self):
        self.ont = Ontology.load(ROOT)
        self.rules = TypingRules.load(ROOT)

    def test_the_commutator_never_reaches_the_prompt(self):
        for name in ("pole_classifier.md", "bridge_classifier.md"):
            rendered = self.ont.render_prompt(os.path.join(ROOT, "prompts", name), ROOT)
            self.assertNotIn("[G#, G~#]", rendered)
            self.assertNotIn("commutator", rendered.lower())
            self.assertNotIn("computed from trajectories", rendered)
            self.assertIn("gamma", rendered)      # the bare label survives

    def test_gamma_remains_reportable_so_the_void_conjecture_stays_falsifiable(self):
        schema_enum = None
        import json
        with open(os.path.join(ROOT, "schemas", "bridge_classification.json"), encoding="utf-8") as fh:
            schema_enum = json.load(fh)["$defs"]["object"]["enum"]
        self.assertIn("gamma", schema_enum)

    def test_report_refuses_to_promote_a_cell_level_gamma(self):
        rep = scoring.report(
            ontology=self.ont, rules=self.rules,
            output_samples=[[("L5", "gamma", PW)]] * 4,
            declared_objects=["J_sharp"],
        )
        self.assertTrue(rep["raw"]["path_level"]["refused"])
        self.assertEqual(rep["raw"]["path_level"]["cell_level_gamma_observations"], 4)
        self.assertIn("gamma_from_classification", rep["refusals"])

    def test_report_composes_gamma_when_arms_are_present(self):
        rep = scoring.report(
            ontology=self.ont, rules=self.rules,
            output_samples=[[("L4", "F", PW)]] * 4,
            declared_objects=["J_sharp"],
            trajectory_arms=dict(zip(("A", "B"), commuting_arms(end_a="L4", end_b="L2"))),
        )
        self.assertTrue(rep["raw"]["path_level"]["measurement"]["is_gamma"])
        self.assertEqual(rep["raw"]["path_level"]["cross_check"]["reading"], "path_level_supported")
        rendered = scoring.render(rep)
        self.assertIn("Observed:   endpoint change observed under the tested", rendered)
        self.assertIn("Inference:  supports gamma != 0 for the tested pair", rendered)
        self.assertNotIn("Path level: gamma != 0", rendered)


if __name__ == "__main__":
    unittest.main()
