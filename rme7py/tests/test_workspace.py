"""The blanks a model actually sees, and what they make impossible."""

import unittest

from rme7 import placement as pl
from rme7 import workspace as ws
from rme7.primitives import Kind, Operand, Position


FULL = """
state.drift_X.dH [x] : J# , G#
state.drift_X.dPhi [x] : G~#
state.diffusion_X.dW [x] : Sigma_ii , Sigma_ij
generator.drift_theta [x] : F
governance [x] : kappa
relation [x] : gamma
"""

PARTIAL = """
state.drift_X.dH [x] : J# , G#
state.drift_X.dPhi [x] : ____
state.diffusion_X.dW [x] : ____ , ____
generator.drift_theta [x] : ____
governance [x] : ____
relation [x] : ____
"""


class TestEmission(unittest.TestCase):

    def test_every_port_is_emitted_with_its_constraint(self):
        """The model is told what may go in a blank rather than left to infer
        it: kind, position, operand and capacity travel with the port."""
        text = ws.emit()
        self.assertEqual(len(text.splitlines()), 6)
        self.assertIn("consumes=dh capacity=2", text)
        self.assertIn("consumes=dphi capacity=1", text)
        self.assertEqual(text.count(ws.BLANK), 8)

    def test_an_unfilled_port_shows_blanks_rather_than_disappearing(self):
        """Entry 31's rule at the interface: inactive is a state, not an
        omission, so a partly-used workspace still emits all six ports."""
        r = pl.Realization()
        r.occupy(pl.Term("J#", Kind.OPERATOR, Position.DRIFT_X, Operand.DH))
        text = ws.emit(r)
        self.assertEqual(len(text.splitlines()), 6)
        self.assertIn("J# , ____", text)


class TestMisplacementIsUnrepresentable(unittest.TestCase):
    """Stronger than refusal: the mistake cannot be written down."""

    def test_a_filled_blank_cannot_declare_a_signature(self):
        """A cell carries a label only. The signature comes from the port, so
        writing 'F' into the drift-of-X blank does not produce a misplaced F
        -- it produces a drift-of-X operator someone named F."""
        r = ws.parse(PARTIAL.replace("J# , G#", "F , ____"))
        placed = [t for p in r.grammar.ports for t in p.held]
        self.assertEqual(len(placed), 1)
        self.assertEqual(placed[0].label, "F")
        self.assertEqual(placed[0].position, Position.DRIFT_X)
        self.assertEqual(placed[0].operand, Operand.DH)

    def test_the_port_set_is_fixed_and_cannot_be_extended_by_writing_one(self):
        bad = PARTIAL + "state.drift_X.dPsi [x] : Q\n"
        with self.assertRaises(pl.Refused) as cm:
            ws.parse(bad)
        self.assertIn("unknown port", str(cm.exception))

    def test_dropping_a_port_is_refused_not_treated_as_inactive(self):
        """An omitted port is a malformed workspace, because omission and
        inactivity are exactly what this layer keeps apart."""
        lines = [l for l in PARTIAL.strip().splitlines()
                 if not l.startswith("relation")]
        with self.assertRaises(pl.Refused) as cm:
            ws.parse("\n".join(lines))
        self.assertIn("ports dropped", str(cm.exception))

    def test_a_port_written_twice_is_refused(self):
        with self.assertRaises(pl.Refused):
            ws.parse(PARTIAL + PARTIAL.strip().splitlines()[1] + "\n")

    def test_overfilling_a_blank_row_is_refused_by_capacity(self):
        with self.assertRaises(pl.Refused) as cm:
            ws.parse(FULL.replace("J# , G#", "J# , G# , X"))
        self.assertIn("full", str(cm.exception))


class TestRoundTrip(unittest.TestCase):

    def test_a_full_workspace_survives_emit_then_parse(self):
        r = ws.parse(FULL)
        self.assertEqual(ws.round_trip(r).report(), r.report())
        self.assertEqual(r.profile(), (True,) * 6)

    def test_a_partial_workspace_survives_with_its_inactive_ports_intact(self):
        r = ws.parse(PARTIAL)
        again = ws.round_trip(r)
        self.assertEqual(again.report(), r.report())
        self.assertEqual(len(again.inactive()), 5)
        self.assertEqual(again.report()["relation"], "inactive")

    def test_the_collision_cost_survives_the_round_trip_unchanged(self):
        """Entry 30's price is not papered over by serialization: filling a
        capacity-2 row in either order parses to the same realization."""
        a = ws.parse(FULL)
        b = ws.parse(FULL.replace("J# , G#", "G# , J#"))
        self.assertEqual(a.report(), b.report())
        self.assertEqual(ws.emit(a), ws.emit(b))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
