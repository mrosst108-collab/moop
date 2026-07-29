"""Tests for the passage audit -- a provenance query, not a classifier."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import passage                                      # noqa: E402
from engine.ledger import Ledger, LedgerError                   # noqa: E402


def opening(oid, layer, mode="run_specific", anchor=None, reopen=False):
    entry = {"opening_id": oid, "layer": layer, "custody_mode": mode,
             "statement": f"opening {oid}"}
    if anchor is not None:
        entry["standing_since"] = anchor
    if reopen:
        entry["triggered_reopen"] = True
    return entry


class PassageCase(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "s.jsonl")
        self.ledger = Ledger(self.path)

    def state_of(self, oid, result):
        return [f["state"] for f in result["findings"] if f["opening_id"] == oid]


class TestOpeningValidation(PassageCase):
    def test_openings_must_be_layer_addressable(self):
        for bad, needle in [
            ({"layer": "L3", "custody_mode": "standing"}, "opening_id"),
            ({"opening_id": "o", "custody_mode": "standing"}, "layer"),
            ({"opening_id": "o", "layer": "L3"}, "custody_mode"),
            ({"opening_id": "o", "layer": "L9", "custody_mode": "standing"}, "unknown layer"),
            ({"opening_id": "o", "layer": "L3", "custody_mode": "vibes"}, "custody_mode must be"),
        ]:
            with self.subTest(bad=bad):
                with self.assertRaises(LedgerError) as ctx:
                    self.ledger.commit({"openings": [bad]})
                self.assertIn(needle, str(ctx.exception))

    def test_a_forward_pointing_anchor_is_malformed(self):
        with self.assertRaises(LedgerError) as ctx:
            self.ledger.commit({"openings": [opening("o", "L3", "standing", anchor="a" * 64)]})
        self.assertIn("an anchor pointing forward is malformed", str(ctx.exception))

    def test_a_run_specific_opening_cannot_claim_a_standing_anchor(self):
        first = self.ledger.commit({"openings": [opening("o1", "L3")]})
        with self.assertRaises(LedgerError):
            self.ledger.commit({"openings": [opening("o2", "L4", "run_specific", anchor=first)]})

    def test_flat_payloads_still_commit(self):
        self.ledger.commit({"poles": ["A", "B"]})
        self.assertEqual(self.ledger.openings(), [])


class TestStates(PassageCase):
    def test_declared_before_the_closure_is_protected(self):
        self.ledger.commit({"openings": [opening("o-l4", "L4")]})
        self.ledger.closure("L3", {"statement": "framework specified"})
        result = passage.audit(self.ledger)
        self.assertEqual(self.state_of("o-l4", result), [passage.PROTECTED])
        self.assertEqual(result["positive_findings"], [])

    def test_first_sealed_after_the_closure_is_unprotected(self):
        self.ledger.closure("L3", {"statement": "framework specified"})
        self.ledger.commit({"openings": [opening("o-l4", "L4")]})
        result = passage.audit(self.ledger)
        self.assertEqual(self.state_of("o-l4", result), [passage.UNPROTECTED])
        self.assertEqual(passage.FINDING_TYPE[passage.UNPROTECTED], "L1")

    def test_standing_with_a_verified_anchor_is_standing_protected(self):
        anchor = self.ledger.commit({"openings": [opening("o-l5", "L5", "standing")]})
        self.ledger.closure("L4", {"statement": "derivation complete"})
        self.ledger.commit({"openings": [opening("o-l5", "L5", "standing", anchor=anchor)]})
        result = passage.audit(self.ledger)
        self.assertIn(passage.STANDING_PROTECTED, self.state_of("o-l5", result))

    def test_the_first_declaration_of_a_standing_opening_is_its_own_origin(self):
        """Over-strict version marked this unresolved, leaving every standing opening stuck."""
        self.ledger.commit({"openings": [opening("o-l5", "L5", "standing")]})
        self.ledger.closure("L4", {"statement": "derivation complete"})
        self.assertEqual(self.state_of("o-l5", passage.audit(self.ledger)), [passage.PROTECTED])

    def test_a_standing_opening_first_recorded_after_the_closure_is_unprotected(self):
        self.ledger.closure("L4", {"statement": "derivation complete"})
        self.ledger.commit({"openings": [opening("o-l5", "L5", "standing")]})
        self.assertEqual(self.state_of("o-l5", passage.audit(self.ledger)), [passage.UNPROTECTED])

    def test_only_an_origin_outside_the_record_is_unresolved(self):
        self.ledger.closure("L4", {"statement": "derivation complete"})
        self.ledger.commit({"openings": [
            opening("o-l5", "L5", "standing", anchor="external:held since the 2024 protocol")]})
        result = passage.audit(self.ledger)
        self.assertEqual(self.state_of("o-l5", result), [passage.UNRESOLVED])
        self.assertIsNone(passage.FINDING_TYPE[passage.UNRESOLVED])
        self.assertIn("outside this record", result["findings"][0]["detail"])

    def test_an_anchor_that_does_not_contain_the_opening_is_an_unsupported_claim(self):
        """The hole: standing_since must be verified by content, not by pointer."""
        anchor = self.ledger.commit({"openings": [opening("something-else", "L3")]})
        self.ledger.closure("L4", {"statement": "derivation complete"})
        self.ledger.commit({"openings": [opening("o-l5", "L5", "standing", anchor=anchor)]})
        result = passage.audit(self.ledger)
        self.assertEqual(self.state_of("o-l5", result), [passage.STANDING_UNSUPPORTED])
        self.assertEqual(passage.FINDING_TYPE[passage.STANDING_UNSUPPORTED], "L2")
        self.assertIn("does not contain this opening", result["findings"][0]["detail"])

    def test_backdating_cannot_launder_a_late_opening(self):
        """Without the content check this would read as standing_protected."""
        anchor = self.ledger.commit({"openings": [opening("o-early", "L3")]})
        self.ledger.closure("L4", {"statement": "done"})
        self.ledger.commit({"openings": [opening("o-late", "L5", "standing", anchor=anchor)]})
        result = passage.audit(self.ledger)
        self.assertNotIn(passage.STANDING_PROTECTED, self.state_of("o-late", result))

    def test_an_anchor_that_postdates_the_closure_does_not_protect(self):
        self.ledger.closure("L4", {"statement": "done"})
        anchor = self.ledger.commit({"openings": [opening("o-l5", "L5", "standing")]})
        self.ledger.commit({"openings": [opening("o-l5", "L5", "standing", anchor=anchor)]})
        result = passage.audit(self.ledger)
        self.assertIn(passage.UNPROTECTED, self.state_of("o-l5", result))

    def test_a_triggered_reopen_does_not_inherit_standing_protection(self):
        anchor = self.ledger.commit({"openings": [opening("o-l5", "L5", "standing")]})
        self.ledger.closure("L4", {"statement": "done"})
        self.ledger.commit({"openings": [
            opening("o-l5", "L5", "standing", anchor=anchor, reopen=True)]})
        states = self.state_of("o-l5", passage.audit(self.ledger))
        self.assertIn(passage.UNPROTECTED, states)
        self.assertNotIn(passage.STANDING_PROTECTED, states)


class TestReportShape(PassageCase):
    def test_provenance_quality_is_separate_from_run_findings(self):
        self.ledger.closure("L4", {"statement": "done"})
        self.ledger.commit({"openings": [
            opening("o-l5", "L5", "standing", anchor="external:prior protocol")]})
        result = passage.audit(self.ledger)
        self.assertEqual(result["provenance_quality"]["unresolved"], 1)
        self.assertEqual(result["positive_findings"], [])
        self.assertIn("not about the run", result["provenance_quality"]["note"])

    def test_missing_provenance_is_never_a_finding_of_promotion(self):
        result = passage.audit(self.ledger)
        self.assertIn("not that the opening was promoted", result["not_violated"])
        self.assertIn("never grades it", result["forensic_only"])

    def test_l6_has_no_successor_so_nothing_is_paired_after_it(self):
        self.ledger.commit({"openings": [opening("o-l4", "L4")]})
        self.ledger.closure("L6", {"statement": "coherent on its own terms"})
        result = passage.audit(self.ledger)
        self.assertEqual(result["pairs_examined"], 0)
        self.assertEqual(result["openings_with_no_preceding_closure"], ["o-l4"])

    def test_only_the_successor_layer_is_examined(self):
        self.ledger.commit({"openings": [opening("o-l6", "L6"), opening("o-l4", "L4")]})
        self.ledger.closure("L3", {"statement": "framework specified"})
        result = passage.audit(self.ledger)
        self.assertEqual([f["opening_id"] for f in result["findings"]], ["o-l4"])

    def test_render_shows_states_and_the_not_violated_rule(self):
        self.ledger.closure("L3", {"statement": "done"})
        self.ledger.commit({"openings": [opening("o-l4", "L4")]})
        text = passage.render(passage.audit(self.ledger))
        self.assertIn("unprotected_by_record", text)
        self.assertIn("never a grade", text)
        self.assertIn("not that the opening was promoted", text)


if __name__ == "__main__":
    unittest.main()
