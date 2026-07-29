"""Tests for claim licensing: a result's evidentiary status is part of its type."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import anchor, claim, passage, scoring              # noqa: E402
from engine.claim import ClaimNotLicensed, Measurement          # noqa: E402
from engine.ledger import Ledger                                # noqa: E402
from engine.ontology import ROOT, Ontology, TypingRules         # noqa: E402

PW = "performed_within"


class TestLadder(unittest.TestCase):
    def test_a_fully_licensed_measurement_answers_every_claim(self):
        m = Measurement("C", 0.42)
        self.assertEqual(m.licensed, claim.CLAIMS)
        self.assertEqual(m.computed, 0.42)
        self.assertEqual(m.as_evidence(), 0.42)
        self.assertEqual(m.highest, claim.GENERALISABLE)

    def test_withholding_a_level_withholds_everything_above_it(self):
        m = Measurement("C", 0.42, withheld={claim.INFERENTIAL: "no single-pole arms"})
        self.assertEqual(m.computed, 0.42)
        self.assertFalse(m.licenses(claim.EVIDENTIAL))
        self.assertFalse(m.licenses(claim.GENERALISABLE))
        self.assertIn("requires inferential", m.withheld[claim.EVIDENTIAL])

    def test_nothing_is_inferred_from_what_was_never_computed(self):
        m = Measurement.refused("C", "no null-baseline samples")
        self.assertEqual(m.licensed, ())
        for accessor in ("computed",):
            with self.assertRaises(ClaimNotLicensed):
                getattr(m, accessor)
        for accessor in (m.as_inference, m.as_evidence, m.as_general):
            with self.assertRaises(ClaimNotLicensed):
                accessor()

    def test_the_reason_travels_with_the_refusal(self):
        m = Measurement("V", 0.3, withheld={claim.EVIDENTIAL: claim.UNVALIDATED_CLASSIFIER})
        with self.assertRaises(ClaimNotLicensed) as ctx:
            m.as_evidence()
        self.assertIn("measures its priors", str(ctx.exception))

    def test_an_unknown_claim_level_is_refused(self):
        with self.assertRaises(ValueError):
            Measurement("C", 1.0, withheld={"vibes": "nope"})
        with self.assertRaises(ValueError):
            Measurement("C", 1.0).require("vibes")


class TestSilentPromotion(unittest.TestCase):
    def test_a_measurement_does_not_silently_become_a_number(self):
        m = Measurement("C", 0.42)
        for op in (float, int):
            with self.assertRaises(ClaimNotLicensed) as ctx:
                op(m)
            self.assertIn("does not silently become a number", str(ctx.exception))

    def test_the_status_travels_with_the_rendered_value(self):
        m = Measurement("C", 0.42, withheld={claim.EVIDENTIAL: claim.UNVALIDATED_CLASSIFIER})
        for text in (str(m), f"{m}", format(m, ".2f")):
            self.assertIn("0.42", text)
            self.assertIn("not evidential", text)
        self.assertIn("REFUSED", str(Measurement.refused("C", "no baseline")))

    def test_status_survives_json_serialisation(self):
        m = Measurement("C", 0.42, withheld={claim.EVIDENTIAL: claim.UNVALIDATED_CLASSIFIER})
        blob = json.loads(json.dumps({"C": m}, default=claim.json_default))
        self.assertEqual(blob["C"]["value"], 0.42)
        self.assertNotIn(claim.EVIDENTIAL, blob["C"]["licensed"])
        self.assertIn(claim.EVIDENTIAL, blob["C"]["withheld"])


class TestReportIntegration(unittest.TestCase):
    def setUp(self):
        self.ont = Ontology.load(ROOT)
        self.rules = TypingRules.load(ROOT)
        self.samples = [[("L4", "Sigma", PW)]] * 8

    def _report(self, ledger=None, **kw):
        return scoring.report(ontology=self.ont, rules=self.rules, ledger=ledger,
                              output_samples=self.samples, declared_objects=["Sigma"], **kw)

    def test_without_validation_nothing_reaches_evidential(self):
        rep = self._report()
        for key in ("C", "V", "interaction", "gamma", "passage"):
            with self.subTest(key=key):
                self.assertFalse(rep["measurements"][key].licenses(claim.EVIDENTIAL))

    def test_a_validation_record_licenses_the_computable_ones(self):
        path = os.path.join(tempfile.mkdtemp(), "s.jsonl")
        ledger = Ledger(path)
        ledger.validation({"anchor": "naive raters", "method": "free sorting", "agreement": 0.4,
                            "validates": "classifier"})
        rep = self._report(ledger)
        self.assertTrue(rep["measurements"]["V"].licenses(claim.EVIDENTIAL))
        self.assertEqual(rep["measurements"]["V"].as_evidence(),
                         rep["raw"]["dispersion"]["normalized_entropy"])

    def test_uncomputable_quantities_stay_refused_even_when_validated(self):
        path = os.path.join(tempfile.mkdtemp(), "s.jsonl")
        ledger = Ledger(path)
        ledger.validation({"anchor": "naive raters", "method": "free sorting", "agreement": 0.4,
                            "validates": "classifier"})
        rep = self._report(ledger)
        self.assertFalse(rep["measurements"]["C"].licenses(claim.COMPUTABLE))
        self.assertIn("null run", rep["measurements"]["C"].withheld[claim.COMPUTABLE])

    def test_a_general_operator_pair_is_computable_but_not_inferential(self):
        """The observation/inference split is one rung of this ladder."""
        arms = {
            "A": [dict(declared_order=["J_sharp", "G_sharp"],
                       steps=[[("L3", "J_sharp", PW)], [("L4", "G_sharp", PW)]]) for _ in range(16)],
            "B": [dict(declared_order=["G_sharp", "J_sharp"],
                       steps=[[("L5", "G_sharp", PW)], [("L2", "J_sharp", PW)]]) for _ in range(16)],
        }
        gamma = self._report(trajectory_arms=arms)["measurements"]["gamma"]
        self.assertTrue(gamma.licenses(claim.COMPUTABLE))
        self.assertFalse(gamma.licenses(claim.INFERENTIAL))
        self.assertIn("not the defined commutator", gamma.withheld[claim.INFERENTIAL])
        self.assertIn("endpoint change observed", gamma.computed)

    def test_partial_passage_coverage_withholds_generalisation_specifically(self):
        path = os.path.join(tempfile.mkdtemp(), "s.jsonl")
        ledger = Ledger(path)
        ledger.validation({"anchor": "naive raters", "method": "free sorting", "agreement": 0.4,
                            "validates": "classifier"})
        ledger.commit({"openings": [{"opening_id": "o", "layer": "L4",
                                     "custody_mode": "run_specific"}]})
        ledger.closure("L3", {"statement": "x"})
        ledger.closure("L5", {"statement": "y"})
        m = self._report(ledger)["measurements"]["passage"]
        # A classifier rater study says nothing about a provenance query, so it
        # does not license one -- the anchor passage depends on is undecided.
        self.assertFalse(m.licenses(claim.EVIDENTIAL))
        self.assertIn("undecided", m.withheld[claim.EVIDENTIAL])
        self.assertEqual(m.requires, (anchor.PROVENANCE_INTEGRITY,))
        # and the coverage reason survives underneath rather than being
        # overwritten by the inherited one
        self.assertFalse(m.licenses(claim.GENERALISABLE))
        self.assertIn("does not extend to the rest", m.withheld[claim.GENERALISABLE])
        self.assertEqual(m.computed, passage.UNEXAMINED)

    def test_every_headline_quantity_is_typed(self):
        """The invariant: no quotable number sits outside the ladder."""
        rep = self._report()
        self.assertEqual(sorted(rep["measurements"]),
                         ["C", "V", "contest_rate", "gamma", "interaction",
                          "passage", "recognition"])
        for key, value in rep["measurements"].items():
            with self.subTest(key=key):
                self.assertIsInstance(value, Measurement)

    def test_raw_is_reachable_but_named(self):
        rep = self._report()
        self.assertIn("raw", rep)
        for key in ("constraint_strength", "dispersion", "interaction",
                    "path_level", "passage", "channel_2"):
            self.assertIn(key, rep["raw"])
            self.assertNotIn(key, rep)
        self.assertIn("bypasses it", rep["raw_note"])

    def test_unmeasured_recognition_is_refused_not_zero(self):
        rep = self._report()
        recognition = rep["measurements"]["recognition"]
        self.assertFalse(recognition.licenses(claim.COMPUTABLE))
        self.assertIn("Channel 2", recognition.withheld[claim.COMPUTABLE])

    def test_render_prints_the_licensing_block(self):
        text = scoring.render(self._report())
        self.assertIn("Claim licensing (the status travels with the value)", text)
        self.assertIn("not evidential", text)


if __name__ == "__main__":
    unittest.main()
