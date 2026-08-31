"""The paired-stencil apparatus. No results here -- only what it can measure."""

import unittest

from rme7 import stencil as st
from rme7 import trial as tr
from rme7.primitives import AutopoieticFeedback, Operand, Position


class TestTwoKeysNotOne(unittest.TestCase):

    def test_primitives_cannot_serve_as_the_answer_key(self):
        """The instructive failure: primitives puts F in the drift of theta,
        a position stipulated from S_C1. S_v5 writes F in the STATE equation.
        Scoring S_v5 with that module would mark S_v5's own canonical filling
        as an error -- the entry-27 inversion at the scoring layer."""
        self.assertIs(AutopoieticFeedback.POSITION, Position.DRIFT_THETA)
        v5_f_blank = [b for b in st.S_V5.blanks
                      if tr.KEYS["S_v5"][b.id] == "F"]
        self.assertEqual(len(v5_f_blank), 2)
        self.assertIn(Position.DRIFT_X, [b.position for b in v5_f_blank])

    def test_each_form_is_scored_against_what_it_itself_writes(self):
        self.assertEqual(len(tr.KEYS["S_v5"]), 7)
        self.assertEqual(len(tr.KEYS["S_C1"]), 5)
        self.assertEqual(set(tr.KEYS["S_v5"]), set(st.S_V5.ids()))
        self.assertEqual(set(tr.KEYS["S_C1"]), set(st.S_C1.ids()))

    def test_the_keys_disagree_and_that_is_the_variable(self):
        d = tr.key_disagreement()
        self.assertEqual(d["written only in S_v5"], ("F", "Sigma", "kappa"))
        self.assertEqual(d["written only in S_C1"],
                         ("Sigma_ii", "Sigma_ij"))
        self.assertEqual(d["written in neither"], ("gamma",))

    def test_s_v5_writes_f_twice(self):
        """Entry 28, as a property of the key: six distinct symbols over
        seven blanks, because F has two written homes in that form."""
        vals = list(tr.KEYS["S_v5"].values())
        self.assertEqual(len(vals), 7)
        self.assertEqual(len(set(vals)), 6)
        self.assertEqual(vals.count("F"), 2)


class TestWhatCannotBeMeasured(unittest.TestCase):

    def test_each_stencil_has_exactly_one_collision_class(self):
        self.assertEqual(tr.collision_classes(st.S_V5), [("v1", "v2")])
        self.assertEqual(tr.collision_classes(st.S_C1), [("c1", "c2")])

    def test_swapping_within_a_collision_class_is_undetectable(self):
        """The trial cannot tell a model that ordered J# and G# correctly
        from one that swapped them. Reported unscorable, never scored."""
        _, c1 = tr.paired("any")
        right = {"c1": "J#", "c2": "G#", "c3": "G~#",
                 "c4": "Sigma_ii", "c5": "Sigma_ij"}
        swapped = dict(right, c1="G#", c2="J#")
        self.assertEqual(c1.tally(right), c1.tally(swapped))
        self.assertEqual(c1.score(right)["c1"], tr.Outcome.UNSCORABLE)

    def test_a_correct_filling_scores_three_constructed_and_two_unscorable(self):
        _, c1 = tr.paired("any")
        t = c1.tally(tr.KEYS["S_C1"])
        self.assertEqual(t["CONSTRUCTED"], 3)
        self.assertEqual(t["UNSCORABLE"], 2)
        self.assertEqual(t["OMITTED"] + t["INVENTED"], 0)


class TestOmissionIsNotInvention(unittest.TestCase):

    def test_an_unused_blank_is_omitted_not_wrong(self):
        _, c1 = tr.paired("gradient flow, no noise")
        s = c1.score({"c2": "G#"})
        self.assertEqual(s["c3"], tr.Outcome.OMITTED)
        self.assertEqual(s["c4"], tr.Outcome.OMITTED)
        self.assertNotIn(tr.Outcome.INVENTED, s.values())

    def test_a_symbol_the_form_does_not_write_is_invented(self):
        _, c1 = tr.paired("any")
        self.assertEqual(c1.score({"c3": "gamma"})["c3"], tr.Outcome.INVENTED)

    def test_the_same_answer_scores_differently_under_the_two_forms(self):
        """Provenance is operational: identical model output, different
        tallies, because the forms offer different numbers of blanks."""
        v5, c1 = tr.paired("gradient flow, no noise")
        self.assertEqual(c1.tally({"c2": "G#"})["OMITTED"], 4)
        self.assertEqual(v5.tally({"v2": "G#"})["OMITTED"], 6)


class TestConditionCarriesItsProvenance(unittest.TestCase):

    def test_the_prompt_states_which_form_and_its_status(self):
        """A result reported without its condition is uninterpretable."""
        v5, c1 = tr.paired("damped oscillator")
        self.assertIn("S_v5", v5.prompt())
        self.assertIn("carried source", v5.prompt())
        self.assertIn("STIPULATED", c1.prompt())
        self.assertIn("damped oscillator", c1.prompt())

    def test_neither_arm_is_the_control(self):
        v5, c1 = tr.paired("any")
        self.assertIs(v5.stencil, st.S_V5)
        self.assertIs(c1.stencil, st.S_C1)
        self.assertFalse(hasattr(tr, "BASELINE"))
        self.assertFalse(hasattr(tr, "CONTROL"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
