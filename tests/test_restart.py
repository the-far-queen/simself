"""
test_restart.py — Atlas Exam Recovery test (per Grok master plan).

The restart test is the second of the three artifacts. It exercises save/load on
the canonical SimSelf class. When it passes, ehole is a return address in the
runtime, not just a drawing.
"""

import os
import json
import sys
import tempfile

import numpy as np
import pytest


# Make canonical SimSelf importable.
HERE = os.path.dirname(os.path.abspath(__file__))
SIMSELF_SRC = os.path.abspath(os.path.join(HERE, "..", "src"))
sys.path.insert(0, SIMSELF_SRC)

try:
    from constitutional.simself import SimSelf
    from constitutional.constitution import Constitution
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


def _make_sim():
    constitution = Constitution()
    return SimSelf(constitution=constitution)


@pytest.mark.skipif(not IMPORTS_AVAILABLE,
                    reason=f"canonical SimSelf import pending: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
def test_restart_round_trip():
    """Construct → tick → save → reload → compare ψ0, ψ, committed unit ids, verdicts."""
    with tempfile.TemporaryDirectory() as td:
        sim = _make_sim()
        for _ in range(5):
            sim.tick()

        psi0_pre = sim.constitution.psi_0.copy()
        psi_pre = sim.psi_current.copy()
        units_pre = sorted(sim.committed_unit_ids())
        verdicts_pre = sim.last_verdicts()

        snap_path = os.path.join(td, "snapshot.json")
        sim.save(snap_path)

        # Simulate process boundary
        sim.zero()

        # Fresh object, load
        sim2 = _make_sim()
        sim2.load(snap_path)

        np.testing.assert_array_equal(sim2.constitution.psi_0, psi0_pre,
                                      err_msg="ψ0 changed across process boundary")
        np.testing.assert_allclose(sim2.psi_current, psi_pre, atol=1e-9,
                                   err_msg="ψ drifted across process boundary")
        assert sorted(sim2.committed_unit_ids()) == units_pre, \
            "committed unit ids changed across process boundary"
        assert sim2.last_verdicts() == verdicts_pre, \
            "last verdicts changed across process boundary"


@pytest.mark.skipif(not IMPORTS_AVAILABLE,
                    reason="canonical SimSelf import pending")
def test_ground_immutable_across_restart():
    """ψ0 must NOT change between save and load, regardless of tick count."""
    with tempfile.TemporaryDirectory() as td:
        sim = _make_sim()
        psi0_before = sim.constitution.psi_0.copy()
        for _ in range(10):
            sim.tick()
        snap_path = os.path.join(td, "snapshot.json")
        sim.save(snap_path)
        sim2 = _make_sim()
        sim2.load(snap_path)
        np.testing.assert_array_equal(sim2.constitution.psi_0, psi0_before,
                                      err_msg="ψ0 was modified by tick()")
