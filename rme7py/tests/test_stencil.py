"""The equation as the workspace, and the two forms it could be."""

import unittest

from rme7 import stencil as st
from rme7.placement import Refused
from rme7.primitives import Kind, Operand, Position


class TestBothFormsAreRendered(unittest.TestCase):
    """Rendering one form as THE workspace would make it the source."""

    def test_neither_stencil_is_privileged_and_both_carry_provenance(self):
        self.assertEqual(set(st.STENCILS), {"S_v5", "S_C1"})
        self.assertIn("carried from Rosst-CP v5", st.S_V5.provenance)
        self.assertIn("chat-level continuity", st.S_C1.provenance)
        self.assertIn("STIPULATED", st.S_C1.status)

    def test_the_two_forms_do_not_have_the_same_blanks(self):
        """G_prov made concrete: the dispute is not stylistic. S_v5 has seven
        blanks over two lines; S_C1 has five over one."""
        self.assertEqual(len(st.S_V5.blanks), 7)
        self.assertEqual(len(st.S_C1.blanks), 5)
        self.assertEqual(len(st.S_V5.template.splitlines()), 2)
        self.assertEqual(len(st.S_C1.template.splitlines()), 1 + 2)

    def test_f_has_a_state_equation_blank_in_v5_and_none_in_c1(self):
        """The F disagreement, as a difference between two workspaces: S_v5
        offers a drift-of-X blank consuming nothing, and S_C1 does not."""
        v5_drift = [b for b in st.S_V5.blanks
                    if b.position is Position.DRIFT_X
                    and b.operand is Operand.NONE]
        self.assertEqual(len(v5_drift), 1)
        c1_drift = [b for b in st.S_C1.blanks
                    if b.position is Position.DRIFT_X
                    and b.operand is Operand.NONE]
        self.assertEqual(c1_drift, [])

    def test_only_c1_writes_the_index_and_only_v5_writes_the_gate(self):
        self.assertEqual([b.index for b in st.S_C1.blanks if b.index],
                         ["diagonal", "off-diagonal"])
        self.assertTrue(all(b.index is None for b in st.S_V5.blanks))
        self.assertEqual(
            [b.id for b in st.S_V5.blanks if b.kind is Kind.ADMISSIBILITY],
            ["v6"])
        self.assertEqual(
            [b.id for b in st.S_C1.blanks if b.kind is Kind.ADMISSIBILITY], [])


class TestHomelessPrimitives(unittest.TestCase):
    """What a form does not write, it does not get a blank for."""

    def test_gamma_is_written_in_neither_form(self):
        """A 'gamma = ___' line would be an equation line no source carries.
        Entry 28: gamma appears in neither written form."""
        self.assertIn("gamma", st.HOMELESS["S_v5"])
        self.assertIn("gamma", st.HOMELESS["S_C1"])
        for s in st.STENCILS.values():
            self.assertNotIn("gamma", s.template)

    def test_c1_leaves_f_and_kappa_homeless_because_it_writes_no_theta_line(self):
        self.assertEqual(set(st.HOMELESS["S_C1"]), {"F", "kappa", "gamma"})
        self.assertNotIn("theta", st.S_C1.template)
        self.assertIn("theta", st.S_V5.template)

    def test_a_primitive_cannot_be_given_a_blank_that_does_not_exist(self):
        with self.assertRaises(Refused) as cm:
            st.S_C1.render({"c9": "gamma"})
        self.assertIn("no blank", str(cm.exception))


class TestBlanksMayStayBlank(unittest.TestCase):

    def test_an_empty_stencil_renders_every_position_as_a_hole(self):
        self.assertEqual(st.S_C1.render().count(st.HOLE), 5)
        self.assertEqual(st.S_V5.render().count(st.HOLE), 7)

    def test_a_partial_realization_renders_without_error(self):
        """The disputed Q1 case, written out: a pure gradient flow occupies
        one blank and leaves the rest holes. The stencil renders it and says
        nothing about whether it is a well-formed RME-7 realization."""
        text = st.S_C1.render({"c2": "G#"})
        self.assertIn("G#(dH_i)", text)
        self.assertEqual(text.count(st.HOLE), 4)
        self.assertEqual(st.S_C1.unfilled({"c2": "G#"}),
                         ["c1", "c3", "c4", "c5"])
        self.assertFalse(hasattr(st.Stencil, "well_formed"))

    def test_a_fully_filled_c1_reproduces_the_written_form(self):
        text = st.S_C1.render({"c1": "J#", "c2": "G#", "c3": "G~#",
                               "c4": "Sigma_ii", "c5": "Sigma_ij"})
        self.assertNotIn(st.HOLE, text)
        self.assertIn("Sigma_ii o dW_i", text)
        self.assertIn("Sigma_ij(X_j -> X_i)", text)


class TestBlanksCarryStructuralMetadata(unittest.TestCase):

    def test_each_blank_names_location_kind_and_operand(self):
        b = [x for x in st.S_C1.blanks if x.id == "c4"][0]
        d = b.describe()
        for expected in ("location: dX.diffusion", "kind: operator",
                         "operand: dw", "instance: diagonal"):
            self.assertIn(expected, d)

    def test_the_two_dH_blanks_are_distinct_positions_without_ordinal_names(self):
        """The entry-30 collision, handled by the equation instead of by
        invented port ordinals: two blanks, same metadata, different places
        in one written line."""
        a, b = st.S_C1.blanks[0], st.S_C1.blanks[1]
        self.assertNotEqual(a.id, b.id)
        self.assertEqual((a.kind, a.position, a.operand),
                         (b.kind, b.position, b.operand))
        self.assertNotIn(".0", st.S_C1.template)
        self.assertNotIn(".1", st.S_C1.template)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
