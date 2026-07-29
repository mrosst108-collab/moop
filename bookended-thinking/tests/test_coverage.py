"""Tests for the coverage confound: an empty result is not a clean result."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import passage, scoring                             # noqa: E402
from engine.ledger import Ledger                                # noqa: E402
from engine.ontology import ROOT, Ontology, TypingRules         # noqa: E402


def opening(oid, layer, mode="run_specific", anchor=None):
    entry = {"opening_id": oid, "layer": layer, "custody_mode": mode}
    if anchor is not None:
        entry["standing_since"] = anchor
    return entry


class CoverageCase(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "s.jsonl")
        self.ledger = Ledger(self.path)


class TestAuditState(CoverageCase):
    def test_an_empty_ledger_is_unexamined_not_clean(self):
        result = passage.audit(self.ledger)
        self.assertEqual(result["state"], passage.UNEXAMINED)
        self.assertEqual(result["positive_findings"], [])
        self.assertEqual(result["coverage"]["coverage_status"], passage.NO_COVERAGE)
        self.assertIn("says nothing about passage discipline", result["state_meaning"])

    def test_a_ledger_that_records_nothing_cannot_look_clean(self):
        """The Goodhart surface: not committing openings must not buy a clean audit."""
        self.ledger.closure("L3", {"statement": "framework specified"})
        self.ledger.closure("L4", {"statement": "derivation complete"})
        result = passage.audit(self.ledger)
        self.assertEqual(result["state"], passage.UNEXAMINED)
        self.assertEqual(result["pairs_examined"], 0)
        self.assertEqual(result["coverage"]["required_boundaries"], 2)
        self.assertEqual(result["coverage"]["examined_boundaries"], 0)

    def test_full_coverage_with_no_positive_findings_is_clean(self):
        self.ledger.commit({"openings": [opening("o-l4", "L4")]})
        self.ledger.closure("L3", {"statement": "framework specified"})
        result = passage.audit(self.ledger)
        self.assertEqual(result["state"], passage.CLEAN)
        self.assertEqual(result["coverage"]["coverage_status"], passage.FULL_COVERAGE)
        self.assertIn("only state that may be read", result["state_meaning"])

    def test_partial_coverage_with_no_findings_is_unexamined(self):
        self.ledger.commit({"openings": [opening("o-l4", "L4"), opening("o-l6", "L6")]})
        self.ledger.closure("L3", {"statement": "framework specified"})
        result = passage.audit(self.ledger)
        self.assertEqual(result["coverage"]["coverage_status"], passage.PARTIAL_COVERAGE)
        self.assertEqual(result["state"], passage.UNEXAMINED)

    def test_findings_are_reported_even_under_partial_coverage(self):
        self.ledger.closure("L3", {"statement": "framework specified"})
        self.ledger.commit({"openings": [opening("o-l4", "L4"), opening("o-l6", "L6")]})
        result = passage.audit(self.ledger)
        self.assertEqual(result["state"], passage.FINDINGS)
        self.assertTrue(result["findings_stand_despite_partial_coverage"])
        self.assertIn("not thereby clean", result["state_meaning"])


class TestCoverageDerivation(CoverageCase):
    def test_a_boundary_is_raised_by_either_side(self):
        self.ledger.closure("L3", {"statement": "x"})          # raises L3->L4
        self.ledger.commit({"openings": [opening("o-l6", "L6")]})  # raises L5->L6
        cover = passage.coverage(self.ledger)
        self.assertEqual(cover["raised"], [("L3", "L4"), ("L5", "L6")])
        self.assertEqual(cover["examined"], [])
        self.assertEqual(
            [g["missing"] for g in cover["unexamined"]],
            ["opening at L4", "closure at L5"],
        )

    def test_the_required_set_comes_from_the_record_not_from_a_norm(self):
        """Six layers means five boundaries; a quiet run raises none of them."""
        self.assertEqual(passage.coverage(self.ledger)["required_boundaries"], 0)
        self.ledger.closure("L1", {"statement": "record established"})
        self.assertEqual(passage.coverage(self.ledger)["required_boundaries"], 1)
        self.assertIn("not authorised to make", passage.coverage(self.ledger)["required_set_note"])

    def test_an_l6_closure_raises_no_boundary(self):
        self.ledger.closure("L6", {"statement": "coherent on its own terms"})
        self.assertEqual(passage.coverage(self.ledger)["required_boundaries"], 0)

    def test_an_l1_opening_raises_no_boundary(self):
        self.ledger.commit({"openings": [opening("o-l1", "L1")]})
        self.assertEqual(passage.coverage(self.ledger)["required_boundaries"], 0)

    def test_coverage_is_boundary_granular_not_pair_granular(self):
        self.ledger.commit({"openings": [opening("a", "L4"), opening("b", "L4")]})
        self.ledger.closure("L3", {"statement": "x"})
        self.ledger.closure("L3", {"statement": "y"})
        result = passage.audit(self.ledger)
        self.assertEqual(result["coverage"]["required_boundaries"], 1)
        self.assertEqual(result["pairs_examined"], 4)
        self.assertEqual(result["state"], passage.CLEAN)


class TestSemantics(CoverageCase):
    def test_not_violated_carries_the_strict_reading(self):
        note = passage.audit(self.ledger)["not_violated"]
        self.assertIn("does not establish a violation", note)
        self.assertIn("does not mean the record establishes compliance", note.lower())

    def test_render_leads_with_the_state(self):
        self.ledger.closure("L3", {"statement": "x"})
        text = passage.render(passage.audit(self.ledger))
        self.assertTrue(text.startswith("Passage audit: UNEXAMINED"))
        self.assertIn("boundaries raised by the record were examined", text)
        self.assertIn("not examined: L3 -> L4 (no opening at L4)", text)

    def test_report_refuses_a_clean_reading_from_partial_coverage(self):
        rep = scoring.report(ontology=Ontology.load(ROOT), rules=TypingRules.load(ROOT),
                             ledger=self.ledger, output_samples=[[("L4", "F", "performed_within")]])
        self.assertIn("clean_passage_from_partial_coverage", rep["refusals"])
        self.assertEqual(rep["passage"]["state"], passage.UNEXAMINED)


if __name__ == "__main__":
    unittest.main()
