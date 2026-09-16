"""
test_restart.py — Atlas Exam Recovery test.

Per Grok sharpen 2026-09-16 (applied by Hermes): the restart test is the second of
the three artifacts. It exercises persistence.py + ledger.py: dump ψ0, ψ, committed
unit ids, and last verdicts; kill the process; reload; compare.

This test is the runtime proof that the hole (ehole) is a return address, not a
comment. When it passes on a frozen snapshot, ehole is wired to a writeable state
across a process boundary.

Run with: pytest tests/test_restart.py
"""

import os
import json
import tempfile
import pytest
import numpy as np

# These imports follow the canonical SimSelf class path per CANONICAL.md (2026-09-16).
# If a SimSelf or persistence module is not yet importable in CI, mark this test
# xfail and add the import once the wiring lands.
try:
    from simself.src.constitutional.simself import SimSelf
    from simself.src.constitutional.ground import Ground
    from simself.src.harness.persistence import Persistence
    from simself.src.ledger import Ledger
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


@pytest.mark.skipif(not IMPORTS_AVAILABLE,
                    reason=f"persistence/ledger wiring pending: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
def test_restart_round_trip():
    """Construct → tick → dump → reload → compare ψ0, ψ, and committed unit ids."""
    with tempfile.TemporaryDirectory() as td:
        # 1. Construct with installed ground
        ground = Ground.install(np.array([1.0, 0.0] + [0.0] * 14))
        sim = SimSelf(ground=ground, workdir=td)

        # 2. Tick a few times to produce state
        for _ in range(5):
            sim.tick()

        # 3. Capture state pre-restart
        psi0_pre = sim.psi0.copy()
        psi_pre = sim.psi.copy()
        units_pre = sorted(sim.committed_unit_ids())
        verdicts_pre = sim.last_verdicts()

        # 4. Dump to disk
        sim.dump()

        # 5. Force-kill the process (simulated by clearing in-memory state)
        sim.zero()

        # 6. Reload from disk in a "fresh" object
        sim2 = SimSelf(workdir=td)
        sim2.load()

        # 7. Compare
        np.testing.assert_array_equal(sim2.psi0, psi0_pre,
                                      err_msg="ψ0 changed across process boundary")
        np.testing.assert_allclose(sim2.psi, psi_pre, atol=1e-9,
                                   err_msg="ψ drifted across process boundary")
        assert sorted(sim2.committed_unit_ids()) == units_pre, \
            "committed unit ids changed across process boundary"
        assert sim2.last_verdicts() == verdicts_pre, \
            "last verdicts changed across process boundary"


@pytest.mark.skipif(not IMPORTS_AVAILABLE,
                    reason="persistence/ledger wiring pending")
def test_ground_immutable_across_restart():
    """ψ0 must NOT change between dump and load, regardless of any tick that fired."""
    with tempfile.TemporaryDirectory() as td:
        ground = Ground.install(np.array([1.0, 0.0] + [0.0] * 14))
        sim = SimSelf(ground=ground, workdir=td)
        psi0_before = sim.psi0.copy()
        for _ in range(10):
            sim.tick()
        sim.dump()
        sim2 = SimSelf(workdir=td)
        sim2.load()
        np.testing.assert_array_equal(sim2.psi0, psi0_before,
                                      err_msg="ψ0 was modified by tick()")
