"""
test_reliability.py — the rate must be measurable, not asserted.

The number is the point, so the number has to be checkable. If a
future session can quietly improve it without saying so, it is
decoration -- the exact defect rule 7 names.

Run: python -m pytest tests/test_reliability.py -q
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from constitutional import reliability as rel  # noqa: E402


class RateTests(unittest.TestCase):
    def test_the_rate_is_recomputed_not_asserted(self):
        """If someone edits the count without editing the entries, this
        fails. A hand-written percentage is a claim; this is arithmetic."""
        expected = len(rel.CONFESSIONS) / float(rel.QUESTIONS_ASKED)
        self.assertAlmostEqual(rel.rate(), expected, places=12)

    def test_the_baseline_matches_the_observation(self):
        """DELIBERATELY RED RIGHT NOW.

        Hand-tallied 25, the module counts 26, so
        BASELINE_RATE (0.25) disagrees with rate() (0.26). This test is
        left failing rather than editing the baseline until it agrees,
        because the disagreement IS the honest record: I said 25 out
        loud and the code says 26.
        """
        self.assertTrue(
            abs(rel.rate() - rel.BASELINE_RATE) < 0.01,
            f"hand-counted baseline {rel.BASELINE_RATE} disagrees with "
            f"the observed {rel.rate():.4f}. Either the admissions list "
            f"or the stated number is wrong.")

    def test_rate_is_in_a_plausible_range(self):
        self.assertGreater(rel.rate(), 0.0)
        self.assertLess(rel.rate(), 1.0)


class DistributionTests(unittest.TestCase):
    def test_every_classification_is_known(self):
        for c in rel.CONFESSIONS:
            self.assertIn(c.cls, rel.CLASSES,
                          f"{c.summary!r} classified as {c.cls!r}")

    def test_counts_sum_to_the_total(self):
        b = rel.by_class()
        self.assertEqual(sum(b.values()), len(rel.CONFESSIONS))

    def test_framing_is_the_worst_class(self):
        """The finding, not a preference. If this ever changes, the
        document above it has to change too."""
        b = rel.by_class()
        worst = max(b, key=lambda k: b[k])
        self.assertEqual(worst, "framing")
        self.assertEqual(b["framing"], 8)

    def test_every_confession_has_a_detail(self):
        for c in rel.CONFESSIONS:
            self.assertGreater(len(c.detail), 15,
                               f"{c.summary!r} has no explanation")

    def test_false_findings_are_named_individually(self):
        """These are the ones that got closest to being believed."""
        texts = " ".join(c.summary.lower() for c in rel.CONFESSIONS
                        if c.cls == "false_finding")
        self.assertIn("filter", texts)
        self.assertIn("bandpass", texts)
        self.assertIn("bump", texts)


class MirrorAgreementTests(unittest.TestCase):
    """Two copies of a number WILL drift. This is the guard."""

    def test_atlas_mirror_matches(self):
        atlas = (Path(__file__).resolve().parent.parent.parent
                 / "atlas-exam" / "src" / "exam" / "reliability.py")
        if not atlas.is_file():
            self.skipTest("atlas-exam mirror not present on this machine")
        text = atlas.read_text(encoding="utf-8")
        self.assertIn(f'"confessions": {len(rel.CONFESSIONS)}', text,
                      "the atlas mirror disagrees with the canonical "
                      "count. simself is authoritative; update the mirror.")


if __name__ == "__main__":
    unittest.main(verbosity=2)