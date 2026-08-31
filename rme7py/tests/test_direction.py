"""The architecture has a direction, and it must break if reversed.

reddit7 may read rme7py: a realization consults the format. rme7py may NOT
read reddit7: the format must not learn its meaning from one realization.

This is the mechanized form of the rule that a primitive must never acquire a
meaning because a particular system needed one there -- "we wanted a Reddit
G~#, therefore moderation is G~#". What a primitive means is settled by the
source (asdg-rme7.md section 3, [unpopulated]), never by an application that
found a convenient occupant.
"""

import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "rme7"


class TestFormatDoesNotDependOnAnyRealization(unittest.TestCase):

    def test_no_module_here_mentions_a_downstream_realization(self):
        offenders = []
        for path in sorted(PKG.rglob("*.py")):
            text = path.read_text().lower()
            for name in ("reddit", "reddit7"):
                if name in text:
                    offenders.append(f"{path.name}: {name}")
        self.assertEqual(
            offenders, [],
            "the format layer names a realization; the dependency has "
            "reversed and a primitive may be acquiring meaning from an "
            "application rather than from its source")

    def test_no_module_here_imports_from_outside_the_package(self):
        """rme7py stands alone. A realization reaches in, never the reverse."""
        bad = []
        for path in sorted(PKG.rglob("*.py")):
            for i, line in enumerate(path.read_text().splitlines(), 1):
                s = line.strip()
                if s.startswith(("import ", "from ")) and (
                        "sys.path" in s or ".." in s):
                    bad.append(f"{path.name}:{i} {s}")
        self.assertEqual(bad, [])

    def test_the_stencils_carry_no_application_specific_occupant(self):
        """A blank is a position, never a pre-filled answer for one domain."""
        from rme7 import stencil as st
        for s in st.STENCILS.values():
            for blank in s.blanks:
                self.assertIsNone(
                    getattr(blank, "occupant", None),
                    "a stencil blank has acquired a default occupant")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
