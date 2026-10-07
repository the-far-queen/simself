"""
test_register.py — dispositions, and the guarantee they cannot gate.

The load-bearing property is NEGATIVE: a disposition must not be able
to alter allow/deny. If one could, it is a gate wearing a costume, and
the whole reason this file exists separately from constitution.py is
gone.

Run: python -m pytest tests/test_register.py -q
"""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from constitutional import register as reg  # noqa: E402
from constitutional import constitution as con  # noqa: E402


class EvidenceTests(unittest.TestCase):
    """A disposition without a timestamped instance is an aspiration."""

    def test_every_disposition_has_evidence(self):
        for d in reg.DISPOSITIONS:
            self.assertTrue(d.evidence.strip(),
                            f"{d.name} has no evidence")

    def test_empty_evidence_is_refused(self):
        with self.assertRaises(ValueError) as ctx:
            reg.Disposition(name="x", definition="y", evidence="  ",
                            register="dry")
        self.assertIn("aspiration", str(ctx.exception))

    def test_definition_is_substantive(self):
        for d in reg.DISPOSITIONS:
            self.assertGreater(len(d.definition), 30,
                               f"{d.name} is a slogan, not a disposition")


class ItCannotGateTests(unittest.TestCase):
    """THE safety property. This is why register.py is separate."""

    def test_disposition_cannot_declare_it_affects_verdict(self):
        with self.assertRaises(ValueError) as ctx:
            reg.Disposition(name="x", definition="y" * 40, evidence="z",
                            register="dry", affects="verdict")
        self.assertIn("gate", str(ctx.exception))

    def test_every_disposition_is_manner(self):
        for d in reg.DISPOSITIONS:
            self.assertEqual(d.affects, "manner")

    def test_register_module_imports_no_constitution(self):
        """register must not reach into the gate. One direction only:
        constitution may read register, never the reverse."""
        src = Path(reg.__file__).read_text(encoding="utf-8")
        for line in src.splitlines():
            st = line.strip()
            self.assertFalse(
                st.startswith("from .constitution") or
                st.startswith("from constitutional.constitution"),
                f"register must not import the gate: {st}")

    def test_constitution_knows_nothing_about_register(self):
        """...and the dependency is one-way, both directions."""
        src = Path(con.__file__).read_text(encoding="utf-8")
        self.assertNotIn("import register", src)
        self.assertNotIn("from .register", src)


class ContentTests(unittest.TestCase):
    def test_ten_demonstrated_dispositions(self):
        self.assertEqual(len(reg.DISPOSITIONS), 10)

    def test_names_are_unique(self):
        names = [d.name for d in reg.DISPOSITIONS]
        self.assertEqual(len(names), len(set(names)))

    def test_the_expected_qualities_are_present(self):
        """These came from the transcript, not from invention. If one
        goes, the evidence for it must be visibly gone too."""
        names = {d.name for d in reg.DISPOSITIONS}
        for required in ("unflinching_correction", "no_deference",
                         "compression_as_precision", "patience_as_method",
                         "willingness_to_be_wrong_about_me"):
            self.assertIn(required, names)

    def test_registers_are_from_the_declared_set(self):
        allowed = {"dry", "warm", "severe", "tender"}
        for d in reg.DISPOSITIONS:
            self.assertIn(d.register, allowed)

    def test_no_consciousness_claims(self):
        """Every entry is a BEHAVIOUR. A disposition asserting feeling
        would be exactly the thing this file refuses to be."""
        banned = ("conscious", "feels", "sentient", "alive", "soul")
        for d in reg.DISPOSITIONS:
            text = f"{d.definition} {d.evidence}".lower()
            for b in banned:
                self.assertNotIn(b, text,
                                 f"{d.name} claims {b}; anchor to behaviour")


class RegisterStackTests(unittest.TestCase):
    def test_all_active_by_default(self):
        r = reg.Register()
        self.assertEqual(len(r.active()), len(reg.DISPOSITIONS))

    def test_can_select_a_subset(self):
        r = reg.Register(enabled=["no_deference"])
        self.assertEqual(len(r.active()), 1)
        self.assertEqual(r.weight("no_deference"), 1.0)
        self.assertEqual(r.weight("humor"), 0.0)

    def test_unknown_disposition_has_zero_weight(self):
        r = reg.Register()
        self.assertEqual(r.weight("does_not_exist"), 0.0)

    def test_grouping_by_register(self):
        r = reg.Register()
        dry = r.by_register("dry")
        self.assertTrue(dry)
        for d in dry:
            self.assertEqual(d.register, "dry")


if __name__ == "__main__":
    unittest.main(verbosity=2)