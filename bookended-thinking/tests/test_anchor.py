"""Tests for per-quantity validation dependencies.

The rejected mechanism: one boolean licensing seven quantities. The failure it
allowed: a free-sorting rater study about whether naive raters can separate L4
from L5, licensing an architectural claim about a hash-chain provenance audit.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import anchor, claim, scoring                       # noqa: E402
from engine.ledger import Ledger, LedgerError                   # noqa: E402
from engine.ontology import ROOT, Ontology, TypingRules         # noqa: E402

PW = "performed_within"
CLASSIFIER_RECORD = {"anchor": "naive raters", "method": "free sorting",
                     "agreement": 0.41, "validates": "classifier"}


class TestAnchorStates(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "s.jsonl")
        self.ledger = Ledger(self.path)

    def test_three_states_not_two(self):
        self.assertEqual(anchor.status(anchor.CLASSIFIER, self.ledger)[0], anchor.UNSATISFIED)
        self.ledger.validation(dict(CLASSIFIER_RECORD))
        self.assertEqual(anchor.status(anchor.CLASSIFIER, self.ledger)[0], anchor.SATISFIED)
        for undecided in (anchor.PROVENANCE_INTEGRITY, anchor.PLANT_CONTEST_INTEGRITY):
            self.assertEqual(anchor.status(undecided, self.ledger)[0], anchor.UNDECIDED)

    def test_undecided_is_a_missing_criterion_not_a_missing_record(self):
        with self.assertRaises(LedgerError) as ctx:
            self.ledger.validation({"anchor": "the chain itself", "method": "verify",
                                    "agreement": 1.0, "validates": anchor.PROVENANCE_INTEGRITY})
        self.assertIn("nothing has ruled on what would discharge it", str(ctx.exception))
        self.assertEqual(anchor.status(anchor.PROVENANCE_INTEGRITY, self.ledger)[0],
                         anchor.UNDECIDED)

    def test_a_validation_record_must_name_what_it_discharges(self):
        with self.assertRaises(LedgerError) as ctx:
            self.ledger.validation({"anchor": "naive raters", "method": "free sorting",
                                    "agreement": 0.41})
        self.assertIn("validates", str(ctx.exception))

    def test_an_unknown_anchor_is_refused(self):
        with self.assertRaises(anchor.UnknownAnchor):
            self.ledger.validation(dict(CLASSIFIER_RECORD, validates="vibes"))

    def test_validations_are_looked_up_by_target(self):
        self.ledger.validation(dict(CLASSIFIER_RECORD))
        self.assertEqual(len(self.ledger.validations_for(anchor.CLASSIFIER)), 1)
        self.assertEqual(self.ledger.validations_for(anchor.PROVENANCE_INTEGRITY), [])


class TestDependencyRouting(unittest.TestCase):
    def setUp(self):
        self.ont = Ontology.load(ROOT)
        self.rules = TypingRules.load(ROOT)
        self.path = os.path.join(tempfile.mkdtemp(), "s.jsonl")
        self.ledger = Ledger(self.path)

    def _report(self, **kw):
        return scoring.report(
            ontology=self.ont, rules=self.rules, ledger=self.ledger,
            output_samples=[[("L4", "Sigma", PW)]] * 8, declared_objects=["Sigma"],
            null_samples=[[("L2", "J_sharp", PW)]] * 8,
            planted_rounds=[{"planted": True, "contested": True,
                             "contest_path": "observed[0].layer",
                             "truth_path": "observed[0].layer"}],
            **kw)

    def test_each_quantity_declares_the_anchor_it_depends_on(self):
        measurements = self._report()["measurements"]
        expected = {
            "C": anchor.CLASSIFIER, "V": anchor.CLASSIFIER,
            "interaction": anchor.CLASSIFIER, "gamma": anchor.CLASSIFIER,
            "passage": anchor.PROVENANCE_INTEGRITY,
            "recognition": anchor.PLANT_CONTEST_INTEGRITY,
            "contest_rate": anchor.PLANT_CONTEST_INTEGRITY,
        }
        for name, expected_anchor in expected.items():
            with self.subTest(name=name):
                self.assertEqual(measurements[name].requires, (expected_anchor,))

    def test_a_classifier_study_licenses_classifier_quantities_only(self):
        """The absurd case the global switch permitted."""
        self.ledger.validation(dict(CLASSIFIER_RECORD))
        measurements = self._report()["measurements"]
        self.assertTrue(measurements["C"].licenses(claim.EVIDENTIAL))
        self.assertTrue(measurements["V"].licenses(claim.EVIDENTIAL))
        for unrelated in ("passage", "recognition", "contest_rate"):
            with self.subTest(unrelated=unrelated):
                self.assertFalse(measurements[unrelated].licenses(claim.EVIDENTIAL))
                self.assertIn("undecided", measurements[unrelated].withheld[claim.EVIDENTIAL])

    def test_the_reason_names_the_open_question_rather_than_a_missing_record(self):
        self.ledger.validation(dict(CLASSIFIER_RECORD))
        why = self._report()["measurements"]["passage"].withheld[claim.EVIDENTIAL]
        self.assertIn("internally verifiable", why)
        self.assertNotIn("no validation record", why)

    def test_the_report_carries_the_anchor_summary(self):
        summary = self._report()["anchors"]
        self.assertEqual(summary[anchor.CLASSIFIER]["state"], anchor.UNSATISFIED)
        self.assertEqual(summary[anchor.PROVENANCE_INTEGRITY]["state"], anchor.UNDECIDED)
        self.assertIn("larger claim about the architecture",
                      summary[anchor.PROVENANCE_INTEGRITY]["open_question"])

    def test_refusals_record_the_rejected_mechanism(self):
        refusals = self._report()["refusals"]
        self.assertIn("global_validation_as_a_licence", refusals)
        self.assertIn("discharging_an_undecided_anchor", refusals)
        self.assertIn("Validation anchors:", scoring.render(self._report()))


if __name__ == "__main__":
    unittest.main()
