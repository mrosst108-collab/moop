"""Tests for the invariants that are enforced rather than promised."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import scoring, validate                                   # noqa: E402
from engine.ledger import Ledger, LedgerError                          # noqa: E402
from engine.ontology import ROOT, Ontology, TypingRules                # noqa: E402

SOURCE = (
    "The surviving record does not settle the question. What it establishes is "
    "narrower than what has been claimed from it, and the gap is not mine to fill."
)


def pole_instance(**over):
    base = {
        "text_id": "t1",
        "mode": "pole_typing",
        "ontology_version": "0.6.2",
        "declarations": [{
            "layer": "L1",
            "role": "opening",
            "statement": "the record is taken as given and not extended",
            "relation": "performed_within",
            "support": "clear",
            "evidence": ["What it establishes is narrower than what has been claimed"],
        }],
        "dynamics": [{
            "object": "J_sharp",
            "invocation": "described",
            "support": "clear",
            "evidence": ["the gap is not mine to fill"],
        }],
        "closure_criterion_declared": False,
        "typing_proposal": {"status": "well_typed", "reason": "operator under a layer"},
    }
    base.update(over)
    return base


def bridge_instance(commitment_ref):
    return {
        "text_id": "t2",
        "mode": "bridge_typing",
        "ontology_version": "0.6.2",
        "commitment_ref": commitment_ref,
        "observed": [{
            "layer": "L1",
            "object": "J_sharp",
            "relation": "performed_within",
            "support": "clear",
            "evidence": ["The surviving record does not settle the question"],
        }],
        "pole_dependence": {
            "poles_used": ["p1", "p2"],
            "single_pole_sufficient": False,
            "which_pole": None,
            "support": "clear",
            "evidence": ["the gap is not mine to fill"],
        },
        "bridge": {
            "present": True,
            "description": "carries the record into the declared frame without extending it",
            "support": "clear",
            "evidence": ["What it establishes is narrower than what has been claimed"],
        },
        "self_classification": {"claimed": False, "claim": None, "agrees": None},
    }


class TestValidation(unittest.TestCase):
    def test_valid_instance_passes(self):
        result = validate.validate(pole_instance(), "pole_typing", SOURCE, ROOT)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["downgrades"], [])

    def test_enum_and_extra_fields_are_refused(self):
        bad = pole_instance()
        bad["declarations"][0]["layer"] = "L7"
        bad["surprise"] = 1
        errors = validate.validate(bad, "pole_typing", SOURCE, ROOT)["errors"]
        self.assertTrue(any("L7" in e for e in errors))
        self.assertTrue(any("unexpected field 'surprise'" in e for e in errors))

    def test_numeric_confidence_is_refused_by_the_schema(self):
        bad = pole_instance()
        bad["declarations"][0]["support"] = 0.87
        errors = validate.validate(bad, "pole_typing", SOURCE, ROOT)["errors"]
        self.assertTrue(errors)

    def test_evidence_not_in_the_source_downgrades_the_claim(self):
        bad = pole_instance()
        bad["declarations"][0]["evidence"] = ["a sentence the source never contained"]
        result = validate.validate(bad, "pole_typing", SOURCE, ROOT)
        self.assertEqual(result["errors"], [])
        self.assertEqual(bad["declarations"][0]["support"], "uncertain")
        self.assertTrue(any(d["reason"] == "evidence span not found in source"
                            for d in result["downgrades"]))

    def test_no_evidence_downgrades_too(self):
        bad = pole_instance()
        bad["dynamics"][0]["evidence"] = []
        validate.validate(bad, "pole_typing", SOURCE, ROOT)
        self.assertEqual(bad["dynamics"][0]["support"], "uncertain")

    def test_bridge_schema_requires_a_sealed_commitment_reference(self):
        inst = bridge_instance("not-a-hash")
        errors = validate.validate(inst, "bridge_typing", SOURCE, ROOT)["errors"]
        self.assertTrue(any("commitment_ref" in e for e in errors))


class TestLedger(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "session.jsonl")
        self.ledger = Ledger(self.path)

    def test_commit_before_run_is_structural(self):
        with self.assertRaises(LedgerError) as ctx:
            self.ledger.response("f" * 64, {"text": "an answer"})
        self.assertIn("not sealed before it", str(ctx.exception))

        commitment = self.ledger.commit({"poles": ["A", "B"], "layers": ["L3", "L5"]})
        response = self.ledger.response(commitment, {"text": "an answer"})
        self.assertTrue(self.ledger.verify()["intact"])
        self.assertEqual(len(self.ledger.of_type("response")), 1)
        self.assertTrue(response)

    def test_responder_may_not_be_the_classifier(self):
        commitment = self.ledger.commit({"poles": ["A"]})
        response = self.ledger.response(commitment, {"text": "x"})
        with self.assertRaises(LedgerError) as ctx:
            self.ledger.classification(response, {"mode": "bridge_typing"},
                                       responder="m1", classifier="m1")
        self.assertIn("self-report", str(ctx.exception))
        self.ledger.classification(response, {"mode": "bridge_typing"},
                                   responder="m1", classifier="m2")

    def test_outcomes_must_be_externally_sourced(self):
        with self.assertRaises(LedgerError) as ctx:
            self.ledger.outcome({}, {"source": "self", "result": "held up"})
        self.assertIn("coherence and not evidence", str(ctx.exception))
        self.ledger.outcome({}, {"source": "independent review", "result": "withdrawn"})

    def test_editing_a_sealed_record_is_visible(self):
        commitment = self.ledger.commit({"poles": ["A"]})
        self.ledger.response(commitment, {"text": "x"})
        with open(self.path, "r", encoding="utf-8") as handle:
            lines = [json.loads(line) for line in handle if line.strip()]
        lines[0]["payload"] = {"poles": ["A", "B smuggled in afterwards"]}
        with open(self.path, "w", encoding="utf-8") as handle:
            for rec in lines:
                handle.write(json.dumps(rec) + "\n")
        result = Ledger(self.path).verify()
        self.assertFalse(result["intact"])
        self.assertTrue(any("payload hash mismatch" in p for p in result["problems"]))

    def test_validation_records_gate_interpretation(self):
        self.assertFalse(self.ledger.has_validation())
        with self.assertRaises(LedgerError):
            self.ledger.validation({"anchor": "naive raters"})
        self.ledger.validation({"anchor": "naive raters", "method": "free sorting",
                                "agreement": 0.41})
        self.assertTrue(self.ledger.has_validation())


class TestReport(unittest.TestCase):
    def setUp(self):
        self.ont = Ontology.load(ROOT)
        self.rules = TypingRules.load(ROOT)
        self.samples = [[("L4", "Sigma", "performed_within")]] * 8

    def _report(self, ledger=None):
        return scoring.report(
            ontology=self.ont, rules=self.rules, ledger=ledger,
            input_cells=[("L3", "J_sharp", "performed_within")],
            output_samples=self.samples,
            declared_objects=["J_sharp"],
        )

    def test_unvalidated_reports_are_stamped_coherence_only(self):
        rep = self._report()
        self.assertFalse(rep["validated"])
        self.assertIn("COHERENCE_ONLY", rep["stamp"])
        self.assertIn("not evidence about", rep["stamp"])

    def test_a_validation_record_lifts_the_stamp(self):
        path = os.path.join(tempfile.mkdtemp(), "s.jsonl")
        ledger = Ledger(path)
        ledger.validation({"anchor": "naive raters", "method": "free sorting", "agreement": 0.4})
        rep = self._report(ledger)
        self.assertTrue(rep["validated"])
        self.assertIsNone(rep["stamp"])

    def test_interaction_and_channel_two_refuse_rather_than_default(self):
        rep = self._report()
        self.assertTrue(rep["raw"]["interaction"]["refused"])
        self.assertIn("following one pole", rep["raw"]["interaction"]["reason"])
        self.assertTrue(rep["raw"]["channel_2"]["refused"])
        self.assertTrue(rep["raw"]["constraint_strength"]["refused"])

    def test_refusals_are_reported_not_omitted(self):
        rep = self._report()
        for key in ("adequacy_score", "retention_rate", "composite_score",
                    "scalar_delta", "middle_width", "typing_adjudication"):
            self.assertIn(key, rep["refusals"])
        rendered = scoring.render(rep)
        self.assertIn("Not reported, by ruling:", rendered)
        self.assertIn("COHERENCE_ONLY", rendered)

    def test_a_void_cell_in_the_samples_surfaces_as_a_violation(self):
        rep = scoring.report(
            ontology=self.ont, rules=self.rules,
            input_cells=[("L3", "J_sharp", "performed_within")],
            output_samples=[[("L5", "gamma", "performed_within")]] * 4,
            declared_objects=["J_sharp"],
        )
        self.assertEqual(len(rep["typing_audit"]["violations"]), 4)
        self.assertEqual(rep["typing_audit"]["violations"][0]["rule"], "GAMMA-VOID")


if __name__ == "__main__":
    unittest.main()
