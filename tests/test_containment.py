"""
test_containment.py — the containment bound must be observable.

ADDED 2026-10-06 after a mutation audit.

`_project_ball` is the only thing keeping psi_current inside
B_R(psi_0). A mutation test removed the projection entirely — every
other I1-I5 check still passed, 144 green, because nothing asserted
the bound directly. The integration net protects the FIX but not the
CONSTRAINT that contains it.

These tests assert the bound itself, so removing or weakening the
projection turns them red.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from constitutional.simself import (  # noqa: E402
    SimSelf,
    _project_ball,
)
from constitutional.ground import Ground            # noqa: E402
from constitutional.constitution import Constitution  # noqa: E402


class ProjectionBoundTests(unittest.TestCase):
    """_project_ball must pull an out-of-bounds state back to the surface."""

    def test_outside_state_is_pulled_to_exactly_R(self):
        psi0 = np.zeros(8)
        psi = np.full(8, 10.0)          # norm ~28.3, far outside any sane R
        out = _project_ball(psi, psi0, 3.0)
        self.assertAlmostEqual(
            float(np.linalg.norm(out - psi0)), 3.0, places=9,
            msg="projection must land exactly on the ball boundary",
        )

    def test_direction_is_preserved(self):
        """Projection rescales, it does not rotate. A state must keep
        its bearing from the ground, or 'constrained to a ball' becomes
        'mapped somewhere unrelated'."""
        psi0 = np.zeros(8)
        psi = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
        out = _project_ball(psi, psi0, 2.0)
        cos = float(np.dot(out, psi)) / (
            float(np.linalg.norm(out)) * float(np.linalg.norm(psi))
        )
        self.assertAlmostEqual(cos, 1.0, places=9)

    def test_inside_state_is_untouched(self):
        psi0 = np.zeros(8)
        psi = np.array([0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0])
        out = _project_ball(psi, psi0, 3.0)
        np.testing.assert_allclose(out, psi)

    def test_zero_state_does_not_divide_by_zero(self):
        psi0 = np.zeros(8)
        out = _project_ball(np.zeros(8), psi0, 3.0)
        np.testing.assert_allclose(out, np.zeros(8))


class TangentProjectionTests(unittest.TestCase):
    """The step direction the code ACTUALLY used must be orthogonal to
    the state.

    Found 2026-10-06 by external analysis of the canonical dynamics.
    The code computed

        direction = obs - (obs . decayed) * decayed / ||decayed||

    which projects onto the UNIT vector in the decayed direction, not
    onto the state. Orthogonal projection onto v is

        x_perp = x - (x.v / |v||^2) v

    and the two coincide only when ||v|| == 1. ||psi_current|| is not
    preserved -- it passes through 0.93 and 1.02 over 32 accepted
    observations -- so the "tangent" direction was measured at up to
    cos = 0.68 aligned with the very state it claimed to be orthogonal
    to.

    IMPORTANT: these assert against ``record["step_direction"]``, the
    direction the production code actually moved along. An earlier
    version of this file recomputed the formula itself in the test
    body, and a mutation test proved that survives the bug being
    reintroduced -- a test that re-derives the thing under test
    verifies nothing.
    """

    def _sim(self):
        c = Constitution()
        g = Ground(c.psi_0.copy())
        return SimSelf(constitution=c, ground=g, R=3.0, eta=0.1)

    def _obs(self):
        x = np.zeros(16)
        x[0], x[1] = 0.8, 0.6
        return x

    def test_step_direction_is_exposed_and_unit(self):
        s = self._sim()
        rec = s.observe(self._obs())
        self.assertIsNotNone(rec["step_direction"],
                            "observe() must report the direction it used")
        d = np.asarray(rec["step_direction"])
        self.assertAlmostEqual(float(np.linalg.norm(d)), 1.0, places=9)

    def test_step_direction_is_orthogonal_to_state_every_iteration(self):
        s = self._sim()
        x = self._obs()
        worst = 0.0
        for _ in range(32):
            s.observe(x)
            rec = s.observe(x)
            d = np.asarray(rec["step_direction"])
            dec = np.asarray(rec["step_reference"])
            c = abs(float(np.dot(d, dec)) /
                    (np.linalg.norm(d) * np.linalg.norm(dec) + 1e-12))
            worst = max(worst, c)
        self.assertLess(
            worst, 1e-8,
            f"production step direction drifted to cos={worst} from orthogonality",
        )

    def test_orthogonality_survives_state_off_the_unit_sphere(self):
        """The condition under which the old formula breaks."""
        s = self._sim()
        s.psi_current = s.psi0 * 1.7
        self.assertNotAlmostEqual(float(np.linalg.norm(s.psi_current)), 1.0,
                                  places=2)
        rec = s.observe(self._obs())
        d = np.asarray(rec["step_direction"])
        dec = np.asarray(rec["step_reference"])
        cos = abs(float(np.dot(d, dec)) /
                  (np.linalg.norm(d) * np.linalg.norm(dec) + 1e-12))
        self.assertLess(cos, 1e-9)


class StateStaysInBoundsTests(unittest.TestCase):
    """End-to-end: after real observations, is the state still bounded?

    This is the assertion the whole suite was missing. Feeding
    observations and then checking drift != 0 proves motion; it does not
    prove the motion stayed inside the ball.
    """

    def _sim(self):
        c = Constitution()
        g = Ground(c.psi_0.copy())
        return SimSelf(constitution=c, ground=g, R=3.0)

    def test_drift_never_exceeds_R(self):
        s = self._sim()
        rng = np.random.default_rng(0)
        worst = 0.0
        for _ in range(200):
            v = rng.normal(size=s.dim)
            v = v / np.linalg.norm(v)
            s.observe(v * 2.0)
            worst = max(worst, s.drift())
        self.assertLessEqual(
            worst, 3.0 + 1e-9,
            f"state escaped the ball: drift {worst} > R {s.R}",
        )

    def test_norm_does_not_grow_without_bound(self):
        """The old bug was inert; the opposite failure is divergence.
        Bounded input must not produce a state that runs away."""
        s = self._sim()
        v = np.full(s.dim, 0.5)
        v = v / np.linalg.norm(v)
        for _ in range(300):
            s.observe(v * 3.0)
        self.assertLess(s.drift(), 3.0 + 1e-9)
        self.assertTrue(np.all(np.isfinite(s.psi_current)),
                        "state went non-finite")

    def test_projection_actively_bounds_accepted_observations(self):
        """Drive observations that ARE accepted and confirm the ball holds.

        Written after an earlier version of this test hand-assigned
        s.psi_current far outside the ball and expected the next
        observe() to pull it back. It does not, and should not: a
        refused observation never reaches the projection step. An
        out-of-bounds state is unreachable through the public path,
        because every state change goes through the gate first.

        So this asserts what the system actually guarantees — that the
        gate plus projection together keep accepted motion bounded —
        rather than a recovery behaviour that was never promised.
        """
        s = self._sim()
        rng = np.random.default_rng(0)
        accepted = 0
        worst = 0.0
        for _ in range(2000):
            v = rng.normal(size=s.dim)
            v /= np.linalg.norm(v)
            rec = s.observe(v * 2.0)
            if rec["allow"]:
                accepted += 1
            worst = max(worst, s.drift())
        self.assertGreater(accepted, 0, "no observations accepted; test is vacuous")
        self.assertLessEqual(worst, 3.0 + 1e-9)
        self.assertGreater(worst, 0.0, "state never moved; the ball test is vacuous")


if __name__ == "__main__":
    unittest.main(verbosity=2)