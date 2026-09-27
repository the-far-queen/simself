"""
test_frequency_layer.py — v6.2 frequency-layer regression tests.

STATUS (2026-09-27 audit):
  This file was originally written for the v6.1 architecture (which had
  FrequencyCoupler, Harness(agent=...), SimSelf.tick(), SimSelf.frequency).
  The canonical v6.2 rewrite (simself.py) is a slim kernel:
    - Ground (write-protected ψ₀)
    - ψ working state, tick(), drift(), save/load
    - NO FrequencyCoupler attribute on SimSelf
    - NO Harness class
    - AtlasExam lives in constitutional/atlas_exam.py
  Tests below were rewritten to run against v6.2 canonical API. Where a v6.1
  feature no longer exists in v6.2, the test is REPLACED with one that
  exercises the closest equivalent in v6.2, with a clear comment.

  Tests preserved (v6.1 → v6.2 mapping):
    1. test_variable_girths_split_degeneracy   — skipped (FrequencyCoupler removed)
    2. test_kuramoto_phases_bounded            — skipped (FrequencyCoupler removed)
    3. test_recall_gate_differentiates         — skipped (FrequencyCoupler removed)
    4. test_psi_0_immutable_under_frequency    — REWRITTEN: ψ_0 immutability under tick
    5. test_frequency_parallel_state           — REWRITTEN: ψ advances under tick; no parallel frequency
    6. test_reset_restores_both_states         — REWRITTEN: reset() restores ψ_current only
    7. test_atlas_exam_with_frequency_wiring   — REWRITTEN: atlas exam without frequency wiring
    8. test_save_load_round_trip               — NEW: regression for persistence

Run:
    python src/constitutional/test_frequency_layer.py
or:
    python -m pytest simself/src/constitutional/test_frequency_layer.py -v
"""
from __future__ import annotations

import sys
import os
import numpy as np

# Allow running from anywhere
_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.dirname(_HERE)  # .../simself/src
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# v6.2 canonical API
from constitutional.simself import SimSelf
from constitutional.constitution import Constitution
from constitutional.ground import Ground

# Marker attribute name for skipped tests (see _skipped() below).
_SKIPPED = "__skip_reason__"


def _skipped(reason: str):
    """Marker: the original test referenced a v6.1 feature that no longer
    exists in v6.2. Skipped (not failed) so reviewers see the test exists
    but recognize it's not applicable. See file header for context."""
    def _inner():
        print(f"    (skipped: {reason})")
    setattr(_inner, _SKIPPED, reason)
    return _inner


# Original tests 1-3 referenced FrequencyCoupler, which is a v6.1 parallel
# state machine removed from v6.2 canonical. Frequency hypotheses live in
# fieldcore/src/substrate.py:DEFAULT_FREQUENCY_HYPOTHESES. The recall gate
# logic is not exposed in v6.2. Skipping preserves the regression intent
# (future reintroduction will re-enable these).
test_variable_girths_split_degeneracy = _skipped("FrequencyCoupler removed in v6.2; degeneracy-split claim is now in fieldcore/src/substrate.py")
test_kuramoto_phases_bounded = _skipped("FrequencyCoupler removed in v6.2; phase dynamics are now in fieldcore/substrate.py:ResolutionOperator")
test_recall_gate_differentiates = _skipped("FrequencyCoupler.gate_recall removed in v6.2; recall is handled by Harness in legacy/")


def test_psi_0_immutable_under_frequency():
    """Constitutional core invariant (v6.2): ψ_0 must not change under tick()."""
    s = SimSelf()
    psi_0_before = s.psi0.copy()
    for _ in range(50):
        s.observe("test observation")
        s.tick()
    psi_0_after = s.psi0.copy()
    assert np.allclose(psi_0_before, psi_0_after), "ψ_0 must be immutable under tick()"


def test_psi_converges_under_tick():
    """v6.2: ψ_current with non-zero drift must contract toward ψ_0 under tick()
    (the projected gradient step). No parallel frequency state."""
    s = SimSelf()
    # Perturb ψ away from ψ_0 to give the gradient step something to do.
    s.psi_current = s.psi0 + 0.5 * np.ones(s.dim)
    drift_before = s.drift()
    assert drift_before > 0.01, f"sanity: drift should be > 0.01 after perturb, got {drift_before}"
    for _ in range(20):
        s.tick()
    drift_after = s.drift()
    # Drift must be non-increasing (per Grok Part III + tiniest_core projection).
    assert drift_after < drift_before, \
        f"ψ must contract toward ψ_0 under tick(): drift {drift_before:.4f} → {drift_after:.4f}"
    # ψ_0 stays put.
    assert np.allclose(s.psi0, np.eye(s.dim, dtype=float)[0]), \
        "ψ_0 must remain at the canonical ground"


def test_reset_restores_psi_current():
    """v6.2: zero() restores ψ to ψ_0 (drift → 0)."""
    s = SimSelf()
    # perturb ψ
    s.psi_current = s.psi0 + 0.5 * np.ones(s.dim)
    drift_before = s.drift()
    assert drift_before > 0.01, f"sanity: drift should be > 0.01 after perturb, got {drift_before}"
    s.zero()
    assert s.drift() < 1e-6, f"drift after zero() must be ~0, got {s.drift()}"


def test_atlas_exam_no_frequency_wiring():
    """v6.2: atlas exam runs without frequency wiring. Validates that the
    constitutional core (stability, routing, boundaries, recovery, coherence)
    passes without the v6.1 frequency parallel state."""
    from constitutional.atlas_exam import AtlasExam
    results = AtlasExam().run()
    assert isinstance(results, dict)
    assert results["score"] >= 4, f"atlas exam must score >=4/5 in v6.2, got {results['score']}/5: {results['items']}"
    for item in ("stability", "boundaries", "recovery", "coherence"):
        assert results["items"][item]["pass"], \
            f"{item} must pass in v6.2 canonical: {results['items'][item]}"


def test_save_load_round_trip():
    """v6.2: dump() → load() reproduces state bit-for-bit (regression for
    the persistence path; this is the test Bobby's "identity + persistence"
    thesis rests on)."""
    s = SimSelf()
    for _ in range(10):
        s.tick()
    psi_0_before = s.psi0.copy()
    psi_before = s.psi_current.copy()
    dump = s.dump()
    s2 = SimSelf()
    s2.load(dump)
    assert np.allclose(s2.psi0, psi_0_before), "ψ_0 must round-trip"
    assert np.allclose(s2.psi_current, psi_before), "ψ must round-trip"


def run_all():
    """Run all tests and print results. Returns True iff all pass."""
    tests = [
        test_variable_girths_split_degeneracy,
        test_kuramoto_phases_bounded,
        test_recall_gate_differentiates,
        test_psi_0_immutable_under_frequency,
        test_psi_converges_under_tick,
        test_reset_restores_psi_current,
        test_atlas_exam_no_frequency_wiring,
        test_save_load_round_trip,
    ]
    passed = 0
    failed = 0
    skipped = 0
    for t in tests:
        try:
            if hasattr(t, _SKIPPED):
                # Skipped marker — invoke to print the reason, count as skipped.
                t()
                print(f"  SKIP  {t.__name__}")
                skipped += 1
                continue
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped (of {len(tests)})")
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)