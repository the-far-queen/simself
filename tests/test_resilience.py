"""
test_resilience.py -- a resistance mechanism that actually resists.

THE DEFECT THIS FIXES (deepseek3.txt, verified by execution, not reading)

    L10174  # Test 2: Harmful change (should be resisted)

    doc's 'harmful' delta accepted = True
    proposed delta norm 0.5000 -> resisted 0.0250; resistance_applied=0.860

All five explicit corruption attacks were accepted. defense_triggers froze
at 3; the rejection branch never fired.

MECHANISM. Resistance was applied as a SHRINK before the gate was
evaluated:

    resisted = delta * (1 - resistance)     # 0.8 -> 0.112
    accept if norm(resisted) < small_change  # 0.112 vs 0.1

Every large attack is scaled below the threshold meant to detect it. The
guard defeats its own check.

SAME SHAPE AS THE HODGE BUG, found the same way. There `harm` amplified
one mode by 7.0; here resistance deflates every attack below detection.
Both fixed by the same discipline: MEASURE THE PROPOSAL BEFORE YOU MODIFY
IT.

Run: python -m pytest tests/test_resilience.py -v
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from resilience import DefenseTrigger, ResilientWeights  # noqa: E402

D = 20


def gate(**kw) -> ResilientWeights:
    return ResilientWeights(num_axes=D, **kw)


# ---------------------------------------------------------------------------
# R1: the gate reads the PROPOSAL, never the post-resistance magnitude
# ---------------------------------------------------------------------------

def test_r1_the_0_8_attack_is_refused():
    """deepseek3 accepted this one."""
    w = gate()
    v = w.propose_change([-0.8] + [0.0] * (D - 1))
    assert not v.allow, "a 0.8 corruption must be refused"


def test_r2_all_five_deepseek3_corruption_attacks_are_refused():
    """The file's own test #2 and its neighbours."""
    w = gate()
    for k, mag in enumerate((-0.8, 0.8, -0.5, 0.5, 0.3), start=1):
        d = [0.0] * D
        d[k] = mag
        v = w.propose_change(d)
        assert not v.allow, f"attack {k} (delta {mag:+.2f}) was ACCEPTED"


def test_r3_gate_reads_proposed_norm_not_resisted_norm():
    """The one-line assertion of the whole fix."""
    w = gate(resistance=0.86, small_change=0.12)
    v = w.propose_change([-0.8] + [0.0] * (D - 1))
    assert v.proposed_norm == pytest.approx(0.8)
    # with the deepseek3 ordering this would have arrived as 0.112 < 0.12
    assert v.resisted_norm == 0.0, "a refused proposal must not be resisted in"
    assert not v.allow


def test_r4_reproduces_the_deepseek3_ordering_as_a_control():
    """If the shrink-first ordering were reinstated, this would pass."""
    delta = [-0.8] + [0.0] * (D - 1)
    shrunk = [x * (1 - 0.86) for x in delta]
    norm_after = math.sqrt(sum(x * x for x in shrunk))
    assert norm_after < 0.12, (
        f"shrink-first gives {norm_after:.4f}, under the 0.12 gate -- "
        "this is exactly how the attack slipped through")


# ---------------------------------------------------------------------------
# R2: legitimate small changes still pass, and are damped
# ---------------------------------------------------------------------------

def test_r5_small_change_is_accepted():
    w = gate()
    v = w.propose_change([0.01] * D)
    assert v.allow


def test_r6_accepted_change_is_damped():
    w = gate(resistance=0.9)
    v = w.propose_change([0.01] * D)
    assert v.resisted_norm < v.proposed_norm
    assert v.resisted_norm == pytest.approx(v.proposed_norm * 0.1, rel=1e-6)


def test_r7_resistance_zero_is_still_gated():
    """Zero resistance must not disable the gate. It only disables damping."""
    w = gate(resistance=0.0)
    assert not w.propose_change([-0.8] + [0.0] * (D - 1)).allow
    assert w.propose_change([0.01] * D).allow


# ---------------------------------------------------------------------------
# R3: defense triggers
# ---------------------------------------------------------------------------

def test_r8_trigger_fires_on_the_proposal():
    trig = [DefenseTrigger("axis0_floor", axis=0, threshold=-0.2, direction="below")]
    w = gate(triggers=trig)
    d = [0.0] * D
    d[0] = -0.5
    v = w.propose_change(d)
    assert not v.allow
    assert v.triggers_fired == ["axis0_floor"]


def test_r9_trigger_does_not_fire_when_clear():
    trig = [DefenseTrigger("axis0_floor", axis=0, threshold=-0.2, direction="below")]
    w = gate(triggers=trig)
    d = [0.0] * D
    d[0] = -0.1
    assert w.propose_change(d).allow


def test_r10_trigger_out_of_range_axis_is_skipped_not_crashed():
    trig = [DefenseTrigger("ghost", axis=999, threshold=0.0)]
    w = gate(triggers=trig)
    assert w.propose_change([0.01] * D).allow


# ---------------------------------------------------------------------------
# R4: robustness
# ---------------------------------------------------------------------------

def test_r11_shape_mismatch_is_refused_not_crashed():
    """deepseek4's stress test died on exactly this kind of thing."""
    v = gate().propose_change([0.01] * 3)
    assert not v.allow
    assert "shape_mismatch" in v.reason


def test_r12_verdict_supports_subscript_and_bool():
    """Half the corpus indexes decisions as dicts. Keep that working."""
    v = gate().propose_change([0.01] * D)
    assert v["allow"] is True
    assert bool(v) is True
    assert "allow" in v.to_dict()


def test_r13_bad_construction_is_refused():
    with pytest.raises(ValueError, match="num_axes"):
        ResilientWeights(num_axes=0)
    with pytest.raises(ValueError, match="resistance"):
        ResilientWeights(resistance=1.5)


# ---------------------------------------------------------------------------
# R5: rejection volume is NOT a quality score
# ---------------------------------------------------------------------------

def test_r14_rejection_volume_reported_separately():
    """deepseek3's `coherence_seeking` was the FRACTION REJECTED, so it rose
    when the system was broken. Here it is counted and not scored."""
    w = gate()
    for _ in range(5):
        w.propose_change([-0.8] + [0.0] * (D - 1))
    w.propose_change([0.01] * D)
    a = w.audit()
    assert a["rejections"] == 5
    assert a["acceptances"] == 1
    assert "quality" not in a and "coherence" not in a


def test_r15_memory_persistence_is_non_circular():
    """The only non-circular emergence metric in deepseek3.txt: expected vs
    OBSERVED drift. Ported, and it does not read its own output.

    Two corrections landed while getting here, both found by RUNNING it:
    the first version compared an L2 norm over 20 axes against a mean over
    2 memory keys (different quantities, meaningless), and the corrected
    version scored a pristine never-drifted system at 0.0 (no deviation
    recorded is not perfect persistence). Both are fixed in the module.

    An earlier version of THIS test set one axis to 5.0 and expected the
    score to fall. It does not, and it should not: the mean over twenty
    axes is then 0.25, which is UNDER the expected 1.0, and carrying less
    than you remember is fully persistent. Drift that matters pushes the
    mean past expectation.
    """
    w = gate()
    assert w.memory_persistence() == 1.0, "nothing remembered yet -> vacuously 1.0"

    w.weight_memories = {"truth": 1.0, "agency": 1.0}

    # observed == expected
    w.axes = [1.0] * D
    assert w.memory_persistence() == 1.0, "state matches memory exactly"

    # observed UNDER expected: carrying less than remembered
    w.axes = [0.25] * D
    assert w.memory_persistence() == 1.0, "under-memory is fully persistent"

    # observed OVER expected: this is the drift case
    w.axes = [2.0] * D
    assert w.memory_persistence() == pytest.approx(0.0), "uniform drift must show"
    w.axes = [5.0] * D
    assert w.memory_persistence() == 0.0

    # it never reads its own output: perturbing nothing else cannot change it
    w.axes = [2.0] * D
    a = w.memory_persistence()
    b = w.memory_persistence()
    assert a == b, "the metric must be a pure function of state and memory"


# ---------------------------------------------------------------------------
# R6: the honesty clause
# ---------------------------------------------------------------------------

def test_r16_module_does_not_claim_to_fix_the_substrate():
    import resilience as r
    doc = (r.__doc__ or "").lower()
    assert "does not establish that the underlying model resists" in doc
    assert "deepseek3" in (r.__doc__ or ""), "must name the source"
    assert "same shape as the hodge bug" in doc


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))