"""The placement document may not name a blank or occupant that isn't real."""

import re
import unittest
from pathlib import Path

from reddit7 import mechanism as m
from reddit7.compat import STENCILS

DOC = (Path(__file__).resolve().parents[1] / "PLACEMENT.md").read_text()


class TestDocumentIsAnchored(unittest.TestCase):

    def test_every_blank_named_exists_in_a_stencil(self):
        named = set(re.findall(r"`([cv]\d)`", DOC))
        real = {i for s in STENCILS for i in s.ids()}
        self.assertTrue(named)
        self.assertEqual(named - real, set())

    def test_it_declares_its_level_and_refuses_the_higher_one(self):
        self.assertIn("role-plus-constraint", DOC)
        self.assertIn("Generator-equation correspondence is NOT claimed", DOC)

    def test_it_does_not_call_itself_an_asdg_formulation(self):
        self.assertIn("This is not called an ASDG formulation", DOC)

    def test_the_constructed_occupant_is_flagged_wherever_it_is_placed(self):
        """c2/v2 are filled by the ruling, not the archive. The document must
        say so at the point of placement, not only in a footnote."""
        self.assertIn("CONSTRUCTED", DOC)
        self.assertIn("filled by the reconstruction, not by the source", DOC)

    def test_the_two_sigma_losses_stay_separate_in_the_document_too(self):
        self.assertIn("driving-process identity", DOC)
        self.assertIn("fan-out cardinality", DOC)

    def test_inactive_is_stated_as_legitimate(self):
        self.assertIn("INACTIVE", DOC)
        self.assertIn("not a gap to be filled", DOC)

    def test_cited_sources_match_the_mechanism(self):
        """Cites in the doc must appear in the extracted mechanism."""
        for cite in ("vote.py:190-300", "voting.py:168-175",
                     "voting.py:171-174", "_sorts.pyx:46-56"):
            self.assertIn(cite, DOC)
        sources = " ".join(s.source for s in m.STATE + m.OBSERVATIONS) + \
            " ".join(g.SOURCE for g in m.GATES) + \
            " ".join(r.source for r in m.CHANNEL_FAMILY)
        self.assertIn("vote.py:190-300", sources)
        self.assertIn("voting.py:168-175", sources)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
