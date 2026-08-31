"""Can terms be placed and recovered using only the labelled structure?"""

import unittest

from rme7 import placement as pl
from rme7.primitives import Kind, Operand, Position


class TestPortsAreDerived(unittest.TestCase):

    def test_one_port_per_structural_class_not_one_per_leaf(self):
        """Six ports for eight leaves. The grammar names exactly what the
        structural signature distinguishes and nothing more."""
        g = pl.Grammar()
        self.assertEqual(g.recoverability(), (6, 8))
        self.assertEqual(len(g.ports), 6)

    def test_capacity_accounts_for_every_leaf(self):
        """Nothing is dropped by collapsing leaves into classes: the
        capacities sum to the leaf count."""
        g = pl.Grammar()
        self.assertEqual(sum(p.capacity for p in g.ports), 8)

    def test_the_two_collisions_appear_as_capacity_not_as_names(self):
        """A collision is encoded as room for two, never as two named ports.
        Naming them would invent an ordering the source does not carry."""
        g = pl.Grammar()
        wide = {p.path: p.capacity for p in g.ports if p.capacity > 1}
        self.assertEqual(wide, {"state.drift_X.dH": 2,
                                "state.diffusion_X.dW": 2})

    def test_every_port_states_its_admission_constraint(self):
        """The point of the workspace: a port says what may go in it, so a
        model does not have to infer it from prose."""
        g = pl.Grammar()
        c = [s for s in g.constraints() if s.startswith("state.drift_X.dH")]
        self.assertEqual(len(c), 1)
        self.assertIn("consumes = DH", c[0])


class TestPlacementRefuses(unittest.TestCase):

    def test_forcing_is_refused_from_the_state_equation(self):
        """The format's most-emphasized rule, as an admission refusal rather
        than a comment: F stands in the generator equation, and a term
        claiming F's kind at a state position has no port."""
        g = pl.Grammar()
        f_misplaced = pl.Term("F", Kind.OPERATOR, Position.DRIFT_X,
                              Operand.NONE)
        with self.assertRaises(pl.Refused):
            g.place(f_misplaced)
        ok = pl.Term("F", Kind.OPERATOR, Position.DRIFT_THETA, Operand.NONE)
        self.assertEqual(g.place(ok).path, "generator.drift_theta")

    def test_an_unmatched_signature_is_refused_not_coerced(self):
        """No nearest-slot guessing. A drift operator consuming dW is not a
        diffusion operator, and the grammar says so rather than filing it."""
        g = pl.Grammar()
        odd = pl.Term("?", Kind.OPERATOR, Position.DRIFT_X, Operand.DW)
        with self.assertRaises(pl.Refused) as cm:
            g.place(odd)
        self.assertIn("no port admits", str(cm.exception))

    def test_a_full_port_refuses_a_third_term(self):
        g = pl.Grammar()
        for n in ("a", "b"):
            g.place(pl.Term(n, Kind.OPERATOR, Position.DRIFT_X, Operand.DH))
        with self.assertRaises(pl.Refused) as cm:
            g.place(pl.Term("c", Kind.OPERATOR, Position.DRIFT_X, Operand.DH))
        self.assertIn("full", str(cm.exception))

    def test_governance_and_relation_admit_no_state_term(self):
        """kappa is a gate and gamma is measured over trajectories. Neither
        port accepts something that declares itself a term of an equation."""
        g = pl.Grammar()
        for pos in (Position.DRIFT_X, Position.DIFFUSION_X):
            with self.assertRaises(pl.Refused):
                g.place(pl.Term("x", Kind.ADMISSIBILITY, pos, Operand.NONE))
            with self.assertRaises(pl.Refused):
                g.place(pl.Term("y", Kind.INVARIANT, pos, Operand.NONE))


class TestRecovery(unittest.TestCase):
    """The criterion the project is to be judged by, executed."""

    CANONICAL = (
        ("J#",       Kind.OPERATOR,      Position.DRIFT_X,     Operand.DH),
        ("G#",       Kind.OPERATOR,      Position.DRIFT_X,     Operand.DH),
        ("G~#",      Kind.OPERATOR,      Position.DRIFT_X,     Operand.DPHI),
        ("Sigma_ii", Kind.OPERATOR,      Position.DIFFUSION_X, Operand.DW),
        ("Sigma_ij", Kind.OPERATOR,      Position.DIFFUSION_X, Operand.DW),
        ("F",        Kind.OPERATOR,      Position.DRIFT_THETA, Operand.NONE),
        ("kappa",    Kind.ADMISSIBILITY, Position.NO_TERM,     Operand.NONE),
        ("gamma",    Kind.INVARIANT,     Position.NO_TERM,     Operand.NONE),
    )

    def _placed(self):
        g = pl.Grammar()
        for row in self.CANONICAL:
            g.place(pl.Term(*row))
        return g

    def test_all_eight_primitives_place_without_refusal(self):
        """Placement is total over the canonical set: every primitive has a
        port, and the six-class grammar loses none of them."""
        g = self._placed()
        self.assertEqual(sum(len(p.held) for p in g.ports), 8)
        self.assertEqual(sum(p.free for p in g.ports), 0)

    def test_recovery_is_exact_up_to_structural_class_and_no_further(self):
        """The honest answer to 'can terms be recovered?' -- yes, to the
        class; no, to the term, for the two colliding pairs. Every port is
        recovered, and the two wide ports return their pair as a set."""
        g = self._placed()
        self.assertEqual(g.recover(), {
            "state.drift_X.dH":     ["G#", "J#"],
            "state.drift_X.dPhi":   ["G~#"],
            "state.diffusion_X.dW": ["Sigma_ii", "Sigma_ij"],
            "generator.drift_theta": ["F"],
            "governance":           ["kappa"],
            "relation":             ["gamma"],
        })

    def test_swapping_a_colliding_pair_is_undetectable(self):
        """The cost, stated as a property rather than a caveat: placing the
        pair in either order yields the same recovery. That is precisely
        what a promoted pending refinement would buy."""
        a, b = pl.Grammar(), pl.Grammar()
        for row in self.CANONICAL:
            a.place(pl.Term(*row))
        for row in tuple(reversed(self.CANONICAL)):
            b.place(pl.Term(*row))
        self.assertEqual(a.recover(), b.recover())

    def test_four_of_the_six_ports_recover_a_term_exactly(self):
        """Not everything collides. Four ports hold one leaf each, so a term
        placed there is recovered as itself."""
        g = self._placed()
        exact = [p.path for p in g.ports if p.capacity == 1]
        self.assertEqual(len(exact), 4)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
