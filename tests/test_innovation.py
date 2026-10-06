"""
test_innovation.py — the observer, and the inertness it was built to catch.

Run: python -m pytest tests/test_innovation.py
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from constitutional.innovation import (  # noqa: E402
    PlantModel,
    InnovationMonitor,
    observe_simself,
    detect_inertness,
)


class RefusalTests(unittest.TestCase):
    def test_unfitted_observer_refuses_to_step(self):
        m = InnovationMonitor()
        with self.assertRaises(RuntimeError):
            m.step(1.0, 1.0)

    def test_fit_needs_two_samples(self):
        m = InnovationMonitor()
        with self.assertRaises(ValueError):
            m.fit([(1.0, 1.0)])

    def test_no_threshold_means_no_verdict(self):
        """A threshold in native units is not portable. Guessing one is
        how 23 exam items scored themselves."""
        m = InnovationMonitor(plant=PlantModel())
        m.fit([(1.0, 1.0), (0.9, 1.0)])
        for _ in range(5):
            m.step(0.9, 1.0)
        v = m.verdict()
        self.assertFalse(v["verdict_available"])
        self.assertIn("UNAVAILABLE", v["state"])


class VerdictTests(unittest.TestCase):
    def _fitted(self, threshold):
        m = InnovationMonitor(plant=PlantModel(A=0.9, B=1.0, C=1.0),
                              threshold=threshold)
        m.fit([(1.0, 1.0), (0.9, 1.0)])
        return m

    def test_no_input_and_small_residual_is_quiet(self):
        m = self._fitted(1e-6)
        m.step(0.0, u=0.0)        # a step with NO input applied
        self.assertEqual(m.verdict()["state"], "QUIET")

    def test_no_input_and_large_residual_is_uncontrolled(self):
        """the state moved with nothing driving it -- no input applied.
        inputs_seen counts APPLIED inputs, so a step with u=0 does not
        count as the system being alive."""
        m = self._fitted(1e-6)
        for _ in range(5):
            m.step(5.0, u=0.0)
        v = m.verdict()
        self.assertEqual(v["inputs_seen"], 0)
        self.assertEqual(v["state"], "UNCONTROLLED_DRIFT")

    def test_input_with_zero_residual_is_INERT(self):
        """THE THREE-STATE READING. Input is arriving and nothing
        changes. Drift reads 0 here, exactly like the oct-6 bug."""
        m = self._fitted(1e-6)
        for _ in range(20):
            m.step(0.0, 1.0)
        v = m.verdict()
        self.assertEqual(v["state"], "INERT")
        self.assertLess(v["rms_residual"], 1e-12)

    def test_input_with_residual_is_alive(self):
        m = self._fitted(1e-6)
        for _ in range(20):
            m.step(0.5, 1.0)
        self.assertEqual(m.verdict()["state"], "ALIVE")


class InertnessDetectionTests(unittest.TestCase):
    """The regression this whole module exists for."""

    def test_detects_an_inert_system(self):
        d = detect_inertness(40)
        self.assertTrue(d["detected_inert"])
        self.assertLess(d["rms_residual"], 1e-9)
        self.assertGreaterEqual(d["inputs_seen"], 40)

    def test_inert_and_alive_are_distinguishable(self):
        inert = detect_inertness(40)
        alive = observe_simself(40)
        self.assertGreater(
            alive["rms_residual"], inert["rms_residual"],
            "an alive system must produce a larger residual than an "
            "inert one; if not, the observer distinguishes nothing")


class LiveSubstrateTests(unittest.TestCase):
    def test_observer_sees_the_real_system(self):
        d = observe_simself(40)
        self.assertTrue(d["verdict"]["fitted"])
        self.assertEqual(len(d["fit"]["fingerprint"]), 16)
        self.assertGreater(d["rms_residual"], 0.0)

    def test_plant_is_fingerprinted(self):
        """A model is a claim; the fingerprint says which."""
        a = PlantModel(A=0.9, B=1.0, C=1.0, label="x")
        b = PlantModel(A=0.8, B=1.0, C=1.0, label="x")
        self.assertNotEqual(a.fingerprint(), b.fingerprint())

    def test_plant_predicts_its_dynamics(self):
        p = PlantModel(A=0.5, B=1.0, C=1.0)
        self.assertAlmostEqual(p.predict(2.0, 0.0), 1.0)
        self.assertAlmostEqual(p.predict(0.0, 4.0), 4.0)

    def test_observer_converges_on_a_steady_plant(self):
        """x_hat should climb toward the signal and the residual should
        fall. That is what a working observer looks like."""
        m = InnovationMonitor(plant=PlantModel(A=0.5, B=1.0, C=1.0),
                              gain=0.4)
        m.fit([(1.0, 1.0), (0.5, 1.0)])
        early = [m.step(1.0, 1.0) for _ in range(5)]
        late = [m.step(1.0, 1.0) for _ in range(40)]
        self.assertGreater(abs(early[0]), abs(late[-1]),
                           "residual should shrink as the observer fits")


if __name__ == "__main__":
    unittest.main(verbosity=2)