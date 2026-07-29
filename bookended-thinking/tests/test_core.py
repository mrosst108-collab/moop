"""Tests for the reader, the ontology, and the withholding guard."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import yamlish                                     # noqa: E402
from engine.ontology import (ROOT, Ontology, OntologyError,     # noqa: E402
                             TypingRules, WITHHELD_FIELDS)


class TestYamlish(unittest.TestCase):
    def test_mapping_list_and_block_scalar(self):
        data = yamlish.load(
            "version: \"1.0\"\n"
            "count: 7\n"
            "ratio: 0.5\n"
            "on: true\n"
            "missing: null\n"
            "flow: [a, b, \"c d\"]\n"
            "prose: |\n"
            "  first\n"
            "  second\n"
            "items:\n"
            "  - id: one\n"
            "    kind: operator\n"
            "  - id: two\n"
            "    kind: invariant\n"
            "bare:\n"
            "  - alpha\n"
            "  - beta\n"
        )
        self.assertEqual(data["version"], "1.0")
        self.assertEqual(data["count"], 7)
        self.assertEqual(data["ratio"], 0.5)
        self.assertIs(data["on"], True)
        self.assertIsNone(data["missing"])
        self.assertEqual(data["flow"], ["a", "b", "c d"])
        self.assertEqual(data["prose"], "first\nsecond\n")
        self.assertEqual([i["id"] for i in data["items"]], ["one", "two"])
        self.assertEqual(data["bare"], ["alpha", "beta"])

    def test_comments_stripped_but_not_inside_scalars(self):
        data = yamlish.load('display: "G~#"  # trailing comment\n# whole line\nname: plain\n')
        self.assertEqual(data["display"], "G~#")
        self.assertEqual(data["name"], "plain")

    def test_refuses_rather_than_guesses(self):
        for bad, needle in [
            ("a: {b: c}\n", "flow mappings"),
            ("a: >\n  folded\n", "folded"),
            ("a: &anchor\n", "anchors"),
            ("a: 1\na: 2\n", "duplicate"),
            ("\ta: 1\n", "tab"),
            ("a: \"unterminated\n", "unterminated"),
            ("  a: 1\n", "indent 0"),
        ]:
            with self.subTest(bad=bad):
                with self.assertRaises(yamlish.YamlishError) as ctx:
                    yamlish.load(bad)
                self.assertIn(needle, str(ctx.exception).lower())


class TestOntology(unittest.TestCase):
    def setUp(self):
        self.ont = Ontology.load(ROOT)
        self.rules = TypingRules.load(ROOT)

    def test_axes_are_not_homogeneous(self):
        kinds = {d.id: d.kind for d in self.ont.dynamics.values()}
        self.assertEqual(sum(1 for k in kinds.values() if k == "operator"), 5)
        self.assertEqual(kinds["kappa"], "indicator")
        self.assertEqual(kinds["gamma"], "invariant")

    def test_layers_are_an_order_with_a_firewall(self):
        self.assertEqual(list(self.ont.layers), ["L1", "L2", "L3", "L4", "L5", "L6"])
        self.assertEqual(self.ont.firewall, ("L5", "L6"))
        self.assertTrue(self.ont.crosses_firewall("L4", "L6"))
        self.assertFalse(self.ont.crosses_firewall("L1", "L5"))

    def test_rendered_prompt_carries_the_ontology(self):
        for name in ("pole_classifier.md", "bridge_classifier.md"):
            rendered = self.ont.render_prompt(os.path.join(ROOT, "prompts", name), ROOT)
            self.assertNotIn("{{CP_LAYERS}}", rendered)
            self.assertNotIn("{{RME7_OBJECTS}}", rendered)
            self.assertIn("Epistemic Validity", rendered)
            self.assertIn("G_tilde_sharp", rendered)

    def test_predictions_never_reach_the_prompt(self):
        """The load-bearing guard: a classifier that knows the subgraph cannot contradict it."""
        for name in ("pole_classifier.md", "bridge_classifier.md"):
            rendered = self.ont.render_prompt(os.path.join(ROOT, "prompts", name), ROOT)
            for pred in self.rules.predictions:
                self.assertNotIn(pred["id"], rendered, f"{pred['id']} leaked into {name}")
            self.assertNotIn("near_zero", rendered)
            self.assertNotIn("widest", rendered)
            self.assertNotIn("void conjecture", rendered)

    def test_withheld_fields_are_actually_withheld(self):
        rendered = self.ont._render_layers()
        for lid in self.ont.layers:
            self.assertNotIn(self.ont.layers[lid].middle_width, ("",))
        self.assertNotIn("middle_width", rendered)
        self.assertNotIn("forensic_zero", rendered)
        self.assertIn("middle_width", WITHHELD_FIELDS["cp_layers"])

    def test_render_refuses_a_prediction_placeholder(self):
        path = os.path.join(ROOT, "tests", "_tmp_prompt.md")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("{{CP_LAYERS}}\n{{TYPING_RULES}}\n")
        try:
            with self.assertRaises(OntologyError) as ctx:
                self.ont.render_prompt(path, ROOT)
            self.assertIn("cannot report one that is not", str(ctx.exception))
        finally:
            os.remove(path)

    def test_typing_rules_must_declare_themselves_withheld(self):
        with self.assertRaises(OntologyError):
            TypingRules({"version": "x", "predictions": [], "zeros": [],
                         "empirical_order": [], "withheld_from_classifier": False})


if __name__ == "__main__":
    unittest.main()
