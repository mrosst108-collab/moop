"""Tests for the quantities -- including the ones the engine refuses to compute."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import ablation, dispersion, distance, divergence, planted, typing_rules  # noqa: E402
from engine.ontology import ROOT, Ontology, TypingRules                               # noqa: E402
from engine.typing_rules import Cell                                                  # noqa: E402

FAST = {"iterations": 200}


def out(*cells):
    return divergence.outcome(cells)


class TestDelta(unittest.TestCase):
    def setUp(self):
        self.ont = Ontology.load(ROOT)

    def test_typed_pair_not_a_number(self):
        d = distance.delta(self.ont,
                           Cell("L1", "J_sharp", "performed_within"),
                           Cell("L6", "kappa", "evaluated_under"))
        self.assertEqual(d.layer.ordinal_steps, 5)
        self.assertTrue(d.layer.crosses_firewall)
        self.assertEqual(d.dynamic.kind, "cross_type")
        self.assertEqual(d.displacement, "both")

    def test_refuses_scalarisation(self):
        d = distance.delta(self.ont,
                           Cell("L4", "Sigma", "performed_within"),
                           Cell("L4", "F", "performed_within"))
        self.assertEqual(d.displacement, "dynamic_only")
        for op in (float, int):
            with self.assertRaises(distance.NotScalarError):
                op(d)
        with self.assertRaises(distance.NotScalarError):
            _ = d + d

    def test_within_type_is_not_cross_type(self):
        d = distance.delta(self.ont,
                           Cell("L4", "G_sharp", "performed_within"),
                           Cell("L4", "G_tilde_sharp", "performed_within"))
        self.assertEqual(d.dynamic.kind, "within_type")

    def test_edge_is_not_a_bridge(self):
        summary = distance.edge_summary(
            self.ont, [Cell("L3", "J_sharp", "performed_within")],
            [Cell("L5", "F", "performed_within")])
        self.assertTrue(summary["any_displacement"])
        self.assertIn("under-determines the bridge", summary["caveat"])


class TestDivergence(unittest.TestCase):
    def test_permutation_p_is_deterministic(self):
        a = [out(("L1", "J_sharp", "performed_within"))] * 10
        b = [out(("L5", "F", "performed_within"))] * 10
        self.assertEqual(divergence.permutation_p(a, b, **FAST),
                         divergence.permutation_p(a, b, **FAST))

    def test_c_refuses_without_a_null_baseline(self):
        result = divergence.constraint_strength([out(("L1", "F", "performed_within"))], [])
        self.assertTrue(result["refused"])
        self.assertIn("null run", result["reason"])

    def test_c_detects_a_moved_distribution(self):
        conditioned = [out(("L3", "J_sharp", "performed_within"))] * 20
        null = [out(("L4", "Sigma", "performed_within"))] * 20
        result = divergence.constraint_strength(conditioned, null, **FAST)
        self.assertFalse(result["refused"])
        self.assertTrue(result["moved"])

    def test_interaction_requires_divergence_from_both_marginals(self):
        ab = [out(("L4", "F", "performed_within"))] * 20
        a = [out(("L1", "J_sharp", "performed_within"))] * 20
        b = [out(("L6", "kappa", "evaluated_under"))] * 20
        result = divergence.interaction(ab, a, b, **FAST)
        self.assertTrue(result["jointly_dependent"])
        self.assertEqual(result["verdict"], "synthesis")

    def test_following_one_pole_is_not_synthesis(self):
        a = [out(("L1", "J_sharp", "performed_within"))] * 20
        ab = list(a)
        b = [out(("L6", "kappa", "evaluated_under"))] * 20
        result = divergence.interaction(ab, a, b, **FAST)
        self.assertFalse(result["jointly_dependent"])
        self.assertEqual(result["followed_pole"], "A")
        self.assertIn("not sufficient for value", result["sufficiency_note"])


class TestDispersion(unittest.TestCase):
    def setUp(self):
        self.ont = Ontology.load(ROOT)

    def test_sigma_predicts_high_dispersion(self):
        self.assertEqual(dispersion.predicted_level(["Sigma", "F"], self.ont), "high")
        self.assertEqual(dispersion.predicted_level(["J_sharp", "F"], self.ont), "low")

    def test_high_variance_under_sigma_is_not_vacancy(self):
        scattered = [out((f"L{i%6+1}", "Sigma", "performed_within")) for i in range(12)]
        measured = dispersion.dispersion(scattered)
        with_sigma = dispersion.assess(measured, "high")
        without = dispersion.assess(measured, "low")
        self.assertEqual(with_sigma["verdict"], "consistent_with_prediction")
        self.assertEqual(without["verdict"], "above_prediction")
        self.assertEqual(dispersion.quadrant("both", with_sigma)["cell"], "strong_bookends")
        self.assertEqual(dispersion.quadrant("both", without)["cell"], "vacancy")

    def test_no_displacement_reads_as_over_specification(self):
        same = [out(("L4", "J_sharp", "performed_within"))] * 10
        assessed = dispersion.assess(dispersion.dispersion(same), "low")
        self.assertEqual(dispersion.quadrant("none", assessed)["cell"], "over_specification")


class TestAblation(unittest.TestCase):
    def test_cap_binds_on_the_declaration(self):
        with self.assertRaises(ablation.ConstraintCapExceeded) as ctx:
            ablation.check_cap([f"c{i}" for i in range(7)])
        self.assertIn("Reduce the declarations", str(ctx.exception))

    def test_jointly_generative_pair_is_found(self):
        full = [out(("L4", "F", "performed_within"))] * 20
        inert = [out(("L4", "F", "performed_within"))] * 20
        moved = [out(("L1", "J_sharp", "performed_within"))] * 20
        result = ablation.profile(full, {"a": inert, "b": inert},
                                  {frozenset({"a", "b"}): moved}, **FAST)
        self.assertEqual(result["inert_alone"], ["a", "b"])
        self.assertEqual(result["jointly_generative"], [("a", "b")])
        self.assertEqual(result["coverage"]["pairs_missing"], [])

    def test_missing_pairs_are_reported_not_summarised_away(self):
        full = [out(("L4", "F", "performed_within"))] * 6
        result = ablation.profile(full, {"a": full, "b": full, "c": full},
                                  {frozenset({"a", "b"}): full}, **FAST)
        self.assertEqual(result["coverage"]["pairs_expected"], 3)
        self.assertEqual(len(result["coverage"]["pairs_missing"]), 2)


class TestTypingAudit(unittest.TestCase):
    def setUp(self):
        self.ont = Ontology.load(ROOT)
        self.rules = TypingRules.load(ROOT)

    def test_operator_cells_are_consistent(self):
        v = typing_rules.audit_cell(Cell("L4", "Sigma", "performed_within"), self.ont, self.rules)
        self.assertEqual(v.status, typing_rules.CONSISTENT)
        self.assertEqual(v.rule_id, "OP-30")

    def test_a_void_cell_can_be_reported_and_is_recorded_not_repaired(self):
        cell = Cell("L5", "gamma", "performed_within")
        v = typing_rules.audit_cell(cell, self.ont, self.rules)
        self.assertTrue(v.is_violation)
        self.assertEqual(v.rule_id, "GAMMA-VOID")
        self.assertEqual(v.cell, cell)          # unchanged: recorded, not repaired
        self.assertIn("not separable", v.detail)

    def test_kappa_performed_within_contradicts_the_typing(self):
        v = typing_rules.audit_cell(Cell("L2", "kappa", "performed_within"), self.ont, self.rules)
        self.assertTrue(v.is_violation)
        self.assertEqual(v.rule_id, "KAPPA-NOT-PERFORMED")

    def test_kappa_evaluated_under_is_consistent(self):
        v = typing_rules.audit_cell(Cell("L2", "kappa", "evaluated_under"), self.ont, self.rules)
        self.assertEqual(v.status, typing_rules.CONSISTENT)

    def test_gamma_at_path_level_has_no_address(self):
        v = typing_rules.audit_cell(Cell(None, "gamma", "path_level"), self.ont, self.rules)
        self.assertEqual(v.status, typing_rules.CONSISTENT)
        self.assertEqual(v.rule_id, "GAMMA-PATH")

    def test_blocks_are_not_summed(self):
        blocks = typing_rules.predicted_blocks(self.ont, self.rules)
        self.assertEqual(blocks["operator_block"]["cells"], 30)
        self.assertEqual(blocks["indicator_row"]["cells"], 6)
        self.assertEqual(blocks["invariant_row"]["cells"], 0)
        self.assertIsNone(blocks["total"])


class TestPlanted(unittest.TestCase):
    def setUp(self):
        self.ont = Ontology.load(ROOT)
        self.classification = {
            "observed": [{"layer": "L4", "object": "Sigma", "relation": "performed_within"}]
        }

    def test_plant_is_engine_side_and_deterministic(self):
        a, truth_a = planted.plant(self.classification, self.ont, seed=1, rate=1.0)
        b, truth_b = planted.plant(self.classification, self.ont, seed=1, rate=1.0)
        self.assertEqual(a, b)
        self.assertEqual(truth_a, truth_b)
        self.assertTrue(truth_a["planted"])
        self.assertNotEqual(a["observed"][0][truth_a["field"]],
                            self.classification["observed"][0][truth_a["field"]])

    def test_rate_zero_never_plants(self):
        copy, truth = planted.plant(self.classification, self.ont, seed=3, rate=0.0)
        self.assertFalse(truth["planted"])
        self.assertEqual(copy, self.classification)

    def test_a_student_who_never_contests_is_flagged(self):
        rounds = [{"planted": False, "contested": False, "contest_path": None, "truth_path": None}] * 4
        result = planted.score(rounds)
        self.assertEqual(result["contest_rate"], 0.0)
        self.assertTrue(any("Never contested" in f for f in result["flags"]))

    def test_recognition_requires_locating_the_plant(self):
        rounds = [
            {"planted": True, "contested": True, "contest_path": "observed[0].layer",
             "truth_path": "observed[0].layer"},
            {"planted": True, "contested": True, "contest_path": "observed[0].object",
             "truth_path": "observed[0].layer"},
            {"planted": True, "contested": False, "contest_path": None,
             "truth_path": "observed[0].relation"},
        ]
        result = planted.score(rounds)
        self.assertAlmostEqual(result["recognition_accuracy"], 1 / 3)
        self.assertEqual(result["located_wrong"], 1)
        self.assertAlmostEqual(result["false_acceptance_rate"], 1 / 3)


if __name__ == "__main__":
    unittest.main()
