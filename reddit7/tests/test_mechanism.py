"""The formulation says what the archive says, and admits what it added."""

import unittest

from reddit7 import mechanism as m
from reddit7.compat import STENCILS, Fit, assess, tally


class TestProvenanceOfEveryStructure(unittest.TestCase):

    def test_exactly_one_state_structure_is_constructed_not_extracted(self):
        """The ruling added one thing. Everything else was read."""
        constructed = [s for s in m.STATE if s.basis is m.Basis.CONSTRUCTED]
        self.assertEqual([s.name for s in constructed], ["thing.attention"])

    def test_every_extracted_structure_cites_a_file_and_line(self):
        for s in m.STATE + m.OBSERVATIONS:
            if s.basis is m.Basis.EXTRACTED:
                self.assertIn("r2/", s.source, s.name)
                self.assertRegex(s.source, r":\d+", s.name)

    def test_the_absences_are_recorded_rather_than_assumed_away(self):
        joined = " ".join(m.ABSENT_FROM_ARCHIVE)
        for missing in ("autonomous evolution", "intrinsic stochasticity",
                        "anonymous driving process"):
            self.assertIn(missing, joined)


class TestTheTwoGatesStayTwo(unittest.TestCase):

    def test_they_have_different_jurisdictions_and_different_inputs(self):
        a, b = m.GATES
        self.assertNotEqual(a.JURISDICTION, b.JURISDICTION)
        self.assertNotEqual(set(a.INPUTS), set(b.INPUTS))

    def test_only_the_second_gate_consults_spam_and_deleted(self):
        """The distinction that merging them would erase."""
        first, second = m.GATES
        self.assertTrue(any("spam" in i for i in second.INPUTS))
        self.assertFalse(any("spam" in i for i in first.INPUTS))

    def test_a_verdict_is_boolean_with_reasons_never_a_score(self):
        v = m.Verdict(False, ("KARMALESS_THING",))
        self.assertFalse(v)
        self.assertEqual(v.notes, ("KARMALESS_THING",))
        self.assertNotIsInstance(v.allowed, (int, float).__class__)
        self.assertIsInstance(v.allowed, bool)


class TestTheEventIsIdentified(unittest.TestCase):

    def test_identity_is_consumed_not_carried(self):
        """Self-vote and automatic-initial both read the actor field."""
        e = m.Event(actor="u1", target="t1", kind="link", direction=1, at=0.0)
        self.assertTrue(e.is_self_directed("u1"))
        self.assertTrue(e.is_automatic_initial("u1"))
        again = m.Event("u1", "t1", "link", 1, 1.0, prior=e)
        self.assertFalse(again.is_automatic_initial("u1"))

    def test_the_channel_is_a_family_of_four_routes_not_one(self):
        self.assertEqual(len(m.CHANNEL_FAMILY), 4)
        self.assertEqual(len({r.destination for r in m.CHANNEL_FAMILY}), 4)


class TestCompatibilityPass(unittest.TestCase):

    def test_the_only_element_placed_in_both_forms_is_the_constructed_one(self):
        """The finding. Every element EXTRACTED from Reddit is homeless or
        lossy in at least one form; the one that fits both is the one the
        ruling invented to fill the drift group."""
        placed = [{f.element for f in assess(s) if f.fit is Fit.PLACED}
                  for s in STENCILS]
        both = set.intersection(*placed)
        self.assertEqual(both, {"thing.attention (CONSTRUCTED by the ruling)"})

    def test_the_identified_event_is_lossy_never_placed(self):
        """The rule this pass exists for: identity is not discarded to fill
        a diffusion blank."""
        for s in STENCILS:
            hits = [f for f in assess(s)
                    if f.element == "identified event process"]
            self.assertEqual([f.fit for f in hits], [Fit.LOSSY])
            self.assertIn("ANONYMOUS", hits[0].reason)

    def test_the_second_gate_is_homeless_in_both_forms(self):
        for s in STENCILS:
            hits = [f for f in assess(s) if f.element.startswith("kappa_prop")]
            self.assertEqual([f.fit for f in hits], [Fit.NO_BLANK])

    def test_observations_are_deliberately_left_homeless(self):
        for s in STENCILS:
            hits = [f for f in assess(s) if f.element.startswith("observations")]
            self.assertEqual([f.fit for f in hits], [Fit.NO_BLANK])
            self.assertIn("correctly homeless", hits[0].reason)

    def test_no_finding_claims_a_blank_the_stencil_lacks(self):
        for s in STENCILS:
            ids = set(s.ids())
            for f in assess(s):
                if f.blank is not None:
                    self.assertIn(f.blank, ids)

    def test_the_tallies_are_what_they_are(self):
        v5, c1 = (tally(s) for s in STENCILS)
        self.assertEqual(v5, {"PLACED": 2, "NO_BLANK": 4, "LOSSY": 1})
        self.assertEqual(c1, {"PLACED": 1, "NO_BLANK": 4, "LOSSY": 2})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
