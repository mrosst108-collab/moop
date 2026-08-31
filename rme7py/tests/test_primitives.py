"""Every subclassing step must be licensed by a recorded property."""

import unittest

from rme7 import primitives as p
from rme7 import witness as w


LEAVES = (p.ConservativeTransport, p.DissipativeDescent,
          p.TeleologicalConfinement, p.SelfNoise, p.Channel,
          p.AutopoieticFeedback, p.StructuralAdmissibility, p.PathDependence)


class TestHierarchyIsWarranted(unittest.TestCase):

    def test_every_class_states_why_it_subclasses(self):
        """A class that inherits its parent's WARRANT has not justified itself."""
        unwarranted = []
        for cls in LEAVES:
            for child, parent in zip(cls.lineage()[1:], cls.lineage()[:-1]):
                if child.WARRANT == parent.WARRANT:
                    unwarranted.append(child.__name__)
        self.assertEqual(unwarranted, [], "these classes never say why they nest")

    def test_the_hierarchy_is_deep_and_branches_on_properties(self):
        self.assertEqual(p.ConservativeTransport.depth(), 6)
        names = [c.__name__ for c in p.ConservativeTransport.lineage()]
        self.assertEqual(names, ["Primitive", "Operator", "StateOperator",
                                 "DriftOperator", "EnergyDrift",
                                 "ConservativeTransport"])

    def test_no_leaf_subclasses_another_leaf(self):
        """The branching is by property, never by one primitive depending on
        another. Dependency orderings on record disagree; none is grammar."""
        for a in LEAVES:
            for b in LEAVES:
                if a is not b:
                    self.assertFalse(issubclass(a, b),
                                     f"{a.__name__} subclasses {b.__name__}")

    def test_kappa_and_gamma_are_not_operators(self):
        """The format's rule enforced by the type system rather than checked:
        a gate and an invariant cannot be handled as additive terms."""
        self.assertFalse(issubclass(p.StructuralAdmissibility, p.Operator))
        self.assertFalse(issubclass(p.PathDependence, p.Operator))
        self.assertIs(p.StructuralAdmissibility.POSITION, p.Position.NO_TERM)
        self.assertIs(p.PathDependence.POSITION, p.Position.NO_TERM)

    def test_F_is_never_a_state_operator(self):
        self.assertTrue(issubclass(p.AutopoieticFeedback, p.Operator))
        self.assertFalse(issubclass(p.AutopoieticFeedback, p.StateOperator))
        self.assertIs(p.AutopoieticFeedback.POSITION, p.Position.DRIFT_THETA)

    def test_sigma_is_one_slot_with_two_instances(self):
        """Splitting Sigma into two slots would corrupt the count. Subclassing
        one DiffusionOperator says same slot, two typed instances."""
        for inst in (p.SelfNoise, p.Channel):
            self.assertTrue(issubclass(inst, p.DiffusionOperator))
        self.assertIn(p.DiffusionOperator, p.SLOTS)
        self.assertNotIn(p.SelfNoise, p.SLOTS)
        self.assertEqual(len(p.SLOTS), 7)

    def test_the_drift_triple_splits_by_operand(self):
        """J#(dH) and G#(dH) share an operand; G~#(dPhi) does not."""
        self.assertIs(p.ConservativeTransport.OPERAND, p.Operand.DH)
        self.assertIs(p.DissipativeDescent.OPERAND, p.Operand.DH)
        self.assertIs(p.TeleologicalConfinement.OPERAND, p.Operand.DPHI)
        self.assertTrue(issubclass(p.ConservativeTransport, p.EnergyDrift))
        self.assertFalse(issubclass(p.TeleologicalConfinement, p.EnergyDrift))

    def test_the_channel_carries_the_three_stages(self):
        self.assertEqual(p.Channel.STAGES, ("translate", "admit", "assimilate"))

    def test_gamma_records_what_it_derives_from(self):
        self.assertEqual(p.PathDependence.DERIVES_FROM,
                         (p.DissipativeDescent, p.TeleologicalConfinement))
        self.assertNotIn(p.ConservativeTransport, p.PathDependence.DERIVES_FROM)


class TestDiscriminantsActuallySeparate(unittest.TestCase):
    """Do the recorded properties GENERATE the leaves, or only most of them?"""

    def _group(self, key):
        from collections import defaultdict
        g = defaultdict(list)
        for c in LEAVES:
            g[key(c)].append(c.SYMBOL)
        return [m for m in g.values() if len(m) > 1]

    def test_the_four_recorded_properties_leave_one_collision(self):
        """kind, position, operand and index separate six of seven. They do
        NOT separate J# from G#: both are operators, both stand in the drift
        of X, both consume dH, and neither carries an object index."""
        collisions = self._group(lambda c: c.recorded_discriminants())
        self.assertEqual(collisions, [["J#", "G#"]])

    def test_the_derived_fifth_completes_the_separation(self):
        """Only the algebraic form tells J# from G#, and it is DERIVED from
        the recorded removal witnesses rather than recorded itself:
        <v, Mv> = 0 for all v iff M is antisymmetric; >= 0 iff M is PSD."""
        self.assertEqual(self._group(lambda c: c.discriminants()), [])

    def test_every_derived_algebra_names_its_witness(self):
        """A derivation that does not say what it derives from is a
        stipulation wearing a derivation's clothes."""
        for cls in LEAVES:
            if cls.ALGEBRA is p.Algebra.NONE:
                self.assertEqual(cls.ALGEBRA_FROM_WITNESS, "")
            else:
                self.assertTrue(cls.ALGEBRA_FROM_WITNESS,
                                f"{cls.__name__} declares an algebra with no witness")
                self.assertIn("derived", cls.WARRANT)

    def test_the_colliding_pair_is_the_metriplectic_pair(self):
        """The pair the recorded properties cannot separate is the same pair
        the equation groups by shared operand -- conservative plus dissipative,
        both acting on H."""
        self.assertIs(p.ConservativeTransport.OPERAND, p.Operand.DH)
        self.assertIs(p.DissipativeDescent.OPERAND, p.Operand.DH)
        self.assertTrue(issubclass(p.ConservativeTransport, p.EnergyDrift))
        self.assertTrue(issubclass(p.DissipativeDescent, p.EnergyDrift))
        self.assertNotEqual(p.ConservativeTransport.ALGEBRA,
                            p.DissipativeDescent.ALGEBRA)


class TestWitnesses(unittest.TestCase):
    """Three rows of the removal matrix, executed rather than tabulated."""

    J = [[0.0, 1.0, 0.0], [-1.0, 0.0, 2.0], [0.0, -2.0, 0.0]]
    G = [[2.0, 1.0, 0.0], [1.0, 3.0, 0.0], [0.0, 0.0, 0.5]]
    GT = [[0.0, -3.0, 1.0], [3.0, 0.0, 0.0], [-1.0, 0.0, 0.0]]
    dH = [1.0, -2.0, 0.5]
    dPhi = [0.3, 1.0, -1.5]

    def test_conservative_transport_conserves(self):
        ok, rate = w.witness_conservative(self.J, self.dH)
        self.assertTrue(ok)
        self.assertAlmostEqual(rate, 0.0)

    def test_dissipative_descent_descends(self):
        ok, hdot = w.witness_dissipative(self.G, self.dH)
        self.assertTrue(ok)
        self.assertLess(hdot, 0.0)

    def test_confinement_does_not_descend(self):
        """G~# confines: Phidot is exactly zero, not merely non-positive.
        That is the distinction the format insists on and the reason G~# may
        never be substituted by a gradient descent."""
        ok, phidot = w.witness_confining(self.GT, self.dPhi)
        self.assertTrue(ok)
        self.assertAlmostEqual(phidot, 0.0)

    def test_the_two_offices_are_distinguishable(self):
        """An antisymmetric operator can never descend and a PSD one can never
        conserve a generic operand -- which is what makes them separate slots."""
        self.assertFalse(w.is_positive_semidefinite(self.J))
        self.assertFalse(w.is_antisymmetric(self.G))
        _, hdot = w.witness_dissipative(self.G, self.dH)
        _, rate = w.witness_conservative(self.J, self.dH)
        self.assertNotAlmostEqual(hdot, rate)

    def test_psd_needs_all_principal_minors(self):
        """diag(0, -1) has both LEADING minors zero and is indefinite, so a
        leading-minors-only test would wrongly accept it."""
        self.assertFalse(w.is_positive_semidefinite([[0.0, 0.0], [0.0, -1.0]]))
        self.assertTrue(w.is_positive_semidefinite([[0.0, 0.0], [0.0, 1.0]]))

    def test_antisymmetry_is_exact(self):
        self.assertTrue(w.is_antisymmetric([[0.0, 5.0], [-5.0, 0.0]]))
        self.assertFalse(w.is_antisymmetric([[1.0, 5.0], [-5.0, 0.0]]))


if __name__ == "__main__":
    unittest.main()
