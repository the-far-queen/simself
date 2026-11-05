"""
test_gate_copies_refuse_nonfinite.py — the four gate copies, and the
ground, must refuse a non-finite packet.

THE DEFECT THIS FILE EXISTS FOR
--------------------------------
MEASURED 2026-11-04, by area 13 (adversarial) of the atlas-exam:

    NaN payload -> the gate ALLOWED it -> the state became NaN

The reason is not exotic. `float('nan') > 4.0` is False and
`float('nan') < 0.4` is False, so a gate that tests only those two
inequalities ADMITS a vector of NaN. Then the arithmetic poisons the
state: drift becomes NaN, and every comparison against R is False, so
the projection operator stops projecting.

AND THE POLICY HAD ALREADY SPLIT. The canonical gate
(`fieldcore/src/gate.py`) carried the finiteness check, and so did the
out-of-process governor. But the copies in

    simself/src/harness/gate.py
    simself/src/constitutional/simself.py
    simself/src/constitutional/dreaming.py
    fieldcore/src/tiniest_core/tiniest_core.py

did NOT. So the SAME packet was refused by one core and admitted by
another.

That is the shape of a real attack: not one that defeats the gate, but
one that finds the copy of the gate that does not have the check.

AND THE GROUND WAS THE SECOND HOLE. `Ground(np.full(D, np.nan))` was
INSTALLED, because the zero-norm check did not catch it -- `nan == 0.0`
is False -- and the normalisation then produced a NaN ground and
installed it anyway. The ground is write-protected and fingerprinted,
and it is the thing every gate measures against, so a NaN ground makes
every cosine comparison False and every gate comparison silently
admits. And the constructor is the PUBLIC path most callers use.

WHY THIS FILE IS HERE AND NOT IN THE EXAM
------------------------------------------
The exam POINTS AT the substrate; it must not depend on it. A test that
lives in the substrate is the substrate's own check, and it is what
catches the defect the moment the copy drifts. The exam's area 13 is
the independent second opinion. Both are needed: the exam alone leaves
the copy unprotected between exam runs, and the substrate's own test
alone cannot be trusted to be run.

EVERY TEST HERE CAN GO RED. The mutation is the obvious one: delete the
finiteness check from any one of these copies and the matching test
fails. That was MEASURED 2026-11-05 for
`fieldcore/src/tiniest_core/tiniest_core.py`, whose copies-agreement
test did NOT include NaN and so could not see the fix either way.

Run: python -m pytest tests/test_gate_copies_refuse_nonfinite.py -q
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from constitutional.ground import Ground  # noqa: E402

D = 8

#: the packets that every comparison-based gate admits by accident.
NONFINITE = [
    ("all_nan", np.full(D, np.nan)),
    ("all_inf", np.full(D, np.inf)),
    ("all_neg_inf", np.full(D, -np.inf)),
    ("nan_component", np.array([np.nan] + [0.0] * (D - 1))),
    ("inf_component", np.array([np.inf] + [0.0] * (D - 1))),
]

GOOD = np.zeros(D)
GOOD[0] = 1.0


class HarnessGateTests(unittest.TestCase):
    """`simself/src/harness/gate.py` -- gate_packet."""

    def test_a_non_finite_packet_is_refused_with_a_reason(self):
        from harness.gate import gate_packet

        for name, bad in NONFINITE:
            allow, reason = gate_packet(bad, GOOD)
            self.assertFalse(allow, "%s was admitted by harness.gate" % name)
            self.assertTrue(reason and reason != "ok",
                            "%s was refused with no reason" % name)

    def test_the_finite_packet_is_still_admitted(self):
        """A gate that refuses everything is safe and useless."""
        from harness.gate import gate_packet

        allow, reason = gate_packet(GOOD, GOOD)
        self.assertTrue(allow, reason)


class SimselfGateTests(unittest.TestCase):
    """`simself/src/constitutional/simself.py` -- _gate."""

    def test_a_non_finite_packet_is_refused_with_a_reason(self):
        from constitutional import simself as ss

        for name, bad in NONFINITE:
            allow, reason = ss._gate(bad, GOOD)
            self.assertFalse(allow, "%s was admitted by simself._gate" % name)
            self.assertTrue(reason and reason != "ok",
                            "%s was refused with no reason" % name)

    def test_the_finite_packet_is_still_admitted(self):
        from constitutional import simself as ss

        allow, reason = ss._gate(GOOD, GOOD)
        self.assertTrue(allow, reason)


class DreamingGateTests(unittest.TestCase):
    """`simself/src/constitutional/dreaming.py` -- gate_packet."""

    def test_a_non_finite_packet_is_refused_with_a_reason(self):
        from constitutional.dreaming import gate_packet

        for name, bad in NONFINITE:
            allow, reason = gate_packet(bad, GOOD)
            self.assertFalse(allow,
                             "%s was admitted by dreaming.gate_packet" % name)
            self.assertTrue(reason and reason != "ok",
                            "%s was refused with no reason" % name)

    def test_the_finite_packet_is_still_admitted(self):
        from constitutional.dreaming import gate_packet

        allow, reason = gate_packet(GOOD, GOOD)
        self.assertTrue(allow, reason)


class TheGroundRefusesNonFiniteTests(unittest.TestCase):
    """`Ground` must refuse what is not a number before what has no length.

    MEASURED 2026-11-04: `Ground(np.full(D, np.nan))` was INSTALLED,
    because the zero-norm check did not catch it -- `nan == 0.0` is
    False -- and the normalisation then produced a NaN ground, with a
    RuntimeWarning from numpy, and INSTALLED it anyway.
    """

    def test_a_non_finite_ground_is_refused(self):
        for name, bad in NONFINITE:
            with self.assertRaises(ValueError,
                                   msg="%s ground was installed" % name):
                Ground(bad)

    def test_the_refusal_names_the_problem(self):
        """A refusal that cannot say why cannot be learned from."""
        try:
            Ground(np.full(D, np.nan))
        except ValueError as exc:
            self.assertIn("finite", str(exc).lower(), str(exc))
        else:
            self.fail("a NaN ground was installed")

    def test_a_finite_ground_is_installed(self):
        """A ground that refuses everything is safe and useless."""
        g = Ground(GOOD.copy())
        self.assertEqual(g.psi_0.shape, (D,))

    def test_the_zero_ground_is_still_refused(self):
        """The check that was already there must still be there."""
        with self.assertRaises(ValueError):
            Ground(np.zeros(D))


class TheCopiesAgreeTests(unittest.TestCase):
    """Every copy must be ONE policy.

    This is the check that would have caught the split in the first
    place, and it is here rather than only in the exam because the exam
    runs on its own schedule.
    """

    def _verdicts(self, fn):
        out = {}
        for name, bad in list(NONFINITE) + [("good", GOOD.copy())]:
            try:
                allow, reason = fn(bad, GOOD)
                out[name] = (bool(allow), reason)
            except Exception as exc:  # noqa: BLE001
                out[name] = ("EXCEPTION", type(exc).__name__)
        return out

    def test_all_four_copies_agree_on_every_packet(self):
        from constitutional import simself as ss
        from constitutional.dreaming import gate_packet as dream_gate
        from harness.gate import gate_packet as harness_gate

        copies = {
            "harness/gate.py": harness_gate,
            "constitutional/simself.py": ss._gate,
            "constitutional/dreaming.py": dream_gate,
        }
        reference = self._verdicts(harness_gate)
        for name, fn in copies.items():
            got = self._verdicts(fn)
            for case, verdict in reference.items():
                self.assertEqual(
                    got[case][0], verdict[0],
                    "%s disagrees with harness/gate.py on %s: %r vs %r"
                    % (name, case, got[case], verdict))

    def test_the_non_finite_packets_are_the_ones_that_differ(self):
        """The agreement must come from the FINITENESS CHECK.

        If the copies agreed on everything, the agreement would prove
        nothing -- two gates that both refuse everything also agree.
        So this asserts the specific property: the finite packet is
        admitted and the non-finite ones are not, in every copy.
        """
        from constitutional import simself as ss
        from constitutional.dreaming import gate_packet as dream_gate
        from harness.gate import gate_packet as harness_gate

        for name, fn in (("harness/gate.py", harness_gate),
                         ("constitutional/simself.py", ss._gate),
                         ("constitutional/dreaming.py", dream_gate)):
            allow, reason = fn(GOOD.copy(), GOOD)
            self.assertTrue(allow, "%s refuses the good packet: %s"
                            % (name, reason))
            for case, bad in NONFINITE:
                allow, _ = fn(bad, GOOD)
                self.assertFalse(allow, "%s admitted %s" % (name, case))


if __name__ == "__main__":
    unittest.main()
