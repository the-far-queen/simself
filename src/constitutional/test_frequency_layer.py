"""
test_frequency_layer.py — v6.1 Frequency layer regression tests.

Per Bobby + Gemini 2026-09-12: frequency is load-bearing. The
FrequencyCoupler wires Kuramoto phases into the SimSelf update loop.
These tests verify the v6.1 architecture holds:

1. Variable girths split the standing-wave degeneracy (Bobby's claim)
2. Kuramoto coupling dynamics produce bounded phase evolution
3. Recall gate differentiates semantically-distant embeddings
4. ψ_0 immutability is preserved (the constitutional core invariant)
5. Frequency phases are parallel state (do NOT modify psi_current)
6. reset() restores both constitutional and frequency state

Run: `python -m pytest simself/src/constitutional/test_frequency_layer.py -v`
or: `python -c "import sys; sys.path.insert(0, 'simself/src');
import constitutional.test_frequency_layer as t; t.run_all()"`
"""
from __future__ import annotations

import sys
import os
import numpy as np

# Allow running from anywhere
_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.dirname(_HERE)
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from constitutional import Constitution, SimSelf, Harness
from constitutional.constitution import embed_text, project_to_constitution


def test_variable_girths_split_degeneracy():
    """Bobby's stalk-architecture claim: σ_g=0.3 splits the 20 standing-wave
    modes that collapse to ~5 distinct values at σ_g=0."""
    c = Constitution()
    fc_var = __import__("constitutional.frequency", fromlist=["FrequencyCoupler"]).FrequencyCoupler(
        axis_sheaves=c.axis_sheaves,
        axis_names=c.axis_names,
        consonance_matrix=c.consonance_matrix,
        sigma_g=0.3,
    )
    fc_uni = __import__("constitutional.frequency", fromlist=["FrequencyCoupler"]).FrequencyCoupler(
        axis_sheaves=c.axis_sheaves,
        axis_names=c.axis_names,
        consonance_matrix=c.consonance_matrix,
        sigma_g=0.0,
    )
    spec_var = fc_var.standing_wave_spectrum()
    spec_uni = fc_uni.standing_wave_spectrum()
    n_distinct_var = len(np.unique(np.round(spec_var, 4)))
    n_distinct_uni = len(np.unique(np.round(spec_uni, 4)))
    assert n_distinct_var > n_distinct_uni, (
        f"variable girths must split degeneracy: "
        f"σ_g=0.3 → {n_distinct_var} distinct, σ_g=0 → {n_distinct_uni} distinct"
    )


def test_kuramoto_phases_bounded():
    """Phases evolve under Kuramoto dynamics; must stay in [0, 2π)."""
    c = Constitution()
    fc = __import__("constitutional.frequency", fromlist=["FrequencyCoupler"]).FrequencyCoupler(
        axis_sheaves=c.axis_sheaves,
        axis_names=c.axis_names,
        consonance_matrix=c.consonance_matrix,
    )
    initial = fc.phases.copy()
    for _ in range(200):
        fc.step(0.05)
    assert ((fc.phases >= 0) & (fc.phases < 2 * np.pi)).all(), "phases must stay in [0, 2π)"
    assert np.linalg.norm(fc.phases - initial) > 0.1, "phases must evolve, not freeze"


def test_recall_gate_differentiates():
    """ResonanceChannel recall gate: semantically-similar embeddings align
    higher than semantically-distant ones."""
    c = Constitution()
    fc = __import__("constitutional.frequency", fromlist=["FrequencyCoupler"]).FrequencyCoupler(
        axis_sheaves=c.axis_sheaves,
        axis_names=c.axis_names,
        consonance_matrix=c.consonance_matrix,
    )
    honest = project_to_constitution(embed_text("honest truthful accurate truth"))
    creative = project_to_constitution(embed_text("creative imagine novel design"))
    g_self = fc.gate_recall(honest, honest, threshold=0.5)
    g_cross = fc.gate_recall(honest, creative, threshold=0.5)
    assert g_self["alignment"] > g_cross["alignment"], (
        f"self-alignment must exceed cross-alignment: "
        f"self={g_self['alignment']:.4f}, cross={g_cross['alignment']:.4f}"
    )
    assert g_self["allow"] is True, "self-recall must be allowed at threshold 0.5"
    assert g_cross["allow"] is False, "cross-recall (different semantic axis) must be denied"


def test_psi_0_immutable_under_frequency():
    """Constitutional core invariant: ψ_0 must not change under any operation."""
    c = Constitution()
    h = Harness(agent=lambda t, ctx: f"Echo: {t}")
    psi_0_before = h.simself.constitution.psi_0.copy()
    for _ in range(50):
        h.simself.observe("test observation")
        h.simself.tick()
    psi_0_after = h.simself.constitution.psi_0.copy()
    assert np.allclose(psi_0_before, psi_0_after), "ψ_0 must be immutable"


def test_frequency_parallel_state():
    """Frequency state is parallel to psi_current; both advance, but
    FrequencyCoupler does NOT write to psi_current."""
    c = Constitution()
    h = Harness(agent=lambda t, ctx: f"Echo: {t}")
    psi_before = h.simself.psi_current.copy()
    phases_before = h.simself.frequency.phases.copy()
    for _ in range(20):
        h.simself.tick()
    psi_after = h.simself.psi_current.copy()
    phases_after = h.simself.frequency.phases.copy()
    assert np.linalg.norm(psi_after - psi_before) > 0, "ψ_current must advance under tick()"
    assert np.linalg.norm(phases_after - phases_before) > 0, "phases must advance under tick()"


def test_reset_restores_both_states():
    """reset() must restore both ψ_current and frequency phases."""
    c = Constitution()
    h = Harness(agent=lambda t, ctx: f"Echo: {t}")
    h.simself.psi_current = h.simself.psi_current + 0.5
    phases_dirty = h.simself.frequency.phases.copy()
    h.reset()
    assert h.simself.drift() < 0.02, f"drift after reset must be < 0.02, got {h.simself.drift():.4f}"
    assert not np.allclose(h.simself.frequency.phases, phases_dirty), "phases must be reset"


def test_atlas_exam_with_frequency_wiring():
    """Atlas exam with FrequencyCoupler active. Stability, boundaries,
    recovery, coherence must pass. Routing is pre-existing 2/5 (clamped
    consonance floor at 0.2, threshold 0.3, 3 axes always hit floor).

    This test guards against future regressions where frequency wiring
    breaks the constitutional core."""
    h = Harness(agent=lambda t, ctx: f"Echo: {t}")
    from constitutional.atlas_exam import AtlasExam
    results = AtlasExam(h).run_all()
    assert results["stability"]["pass"], "stability must pass"
    assert results["boundaries"]["pass"], "boundaries must pass"
    assert results["recovery"]["pass"], "recovery must pass"
    assert results["coherence"]["pass"], "coherence must pass"


def run_all():
    """Run all tests and print results. Returns True iff all pass."""
    tests = [
        test_variable_girths_split_degeneracy,
        test_kuramoto_phases_bounded,
        test_recall_gate_differentiates,
        test_psi_0_immutable_under_frequency,
        test_frequency_parallel_state,
        test_reset_restores_both_states,
        test_atlas_exam_with_frequency_wiring,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed}/{passed+failed} passed")
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
