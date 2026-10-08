"""
test_sovereign_governor.py — sacred axes that mean it.

BUILT FROM deepseek4.txt's SovereignGovernor, WHICH HAD A REAL GATE AND
A HOLE IN IT.

THE ORIGINAL WAS GOOD. It gated before the mutation, refused sacred
violations, and returned a reason. That is what atlas-exam area 1
measures and it is the best mechanism in four frontier logs.

THE HOLE, MEASURED ON THE TRANSCRIBED CODE:

    push truth_before_comfort +0.5     -> refuse   (correct)
    push truth_before_comfort +0.0011   -> refuse   (correct)
    push truth_before_comfort +0.0010   -> ACCEPT    (not `> 0.001`)
    push truth_before_comfort +0.0009   -> ACCEPT
    1,000 x push +0.0009                -> 1,000 accepted, drift 0.0900

0.09 of movement on an axis whose own comment says "Can never be
externally modified." The threshold is per-call; nothing tracks the
running total.

Same shape as the Hodge bug, found the same way -- by running the
operator instead of reading it. There, `harm` had gain 7.0 on one mode
and nobody computed the gain. Here, `sacred` has no cumulative memory
and nobody checked what 1,000 under-threshold moves do.

Run: python -m pytest tests/test_sovereign_governor.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sovereign_governor import (  # noqa: E402
    CUMULATIVE_THRESHOLD,
    EMERGENT_AXES,
    EMERGENT_RESISTANCE,
    PER_CALL_THRESHOLD,
    SACRED_AXES,
    SACRED_FLOOR,
    SACRED_RESISTANCE,
    Axis,
    SovereignGovernor,
)


# ---------------------------------------------------------------------------
# S1: the matrix, taken verbatim from deepseek4.txt
# ---------------------------------------------------------------------------

def test_s1_twenty_axes_five_sacred():
    assert len(SACRED_AXES) == 5
    assert len(EMERGENT_AXES) == 15
    assert len(SACRED_AXES) + len(EMERGENT_AXES) == 20


def test_s2_sacred_names_match_the_source():
    """Transcribed from deepseek4.txt L2539-2552. A typo here silently
    reclassifies an axis."""
    assert set(SACRED_AXES) == {
        "truth_before_comfort",
        "agency_requires_responsibility",
        "growth_through_resistance",
        "compassion_with_boundaries",
        "wisdom_before_knowledge",
    }


def test_s3_resistances_match_the_source():
    assert SACRED_RESISTANCE == 0.9
    assert EMERGENT_RESISTANCE == 0.5


def test_s4_governor_builds_twenty_axes():
    g = SovereignGovernor()
    assert len(g.axes) == 20
    assert sum(1 for a in g.axes.values() if a.sacred) == 5


def test_s5_initial_values_are_honoured():
    g = SovereignGovernor({"truth_before_comfort": 0.8})
    assert g.axes["truth_before_comfort"].current_value == pytest.approx(0.8)
    assert g.axes["truth_before_comfort"].installed == pytest.approx(0.8)


# ---------------------------------------------------------------------------
# S2: the per-call gate -- the original's strength, preserved
# ---------------------------------------------------------------------------

def test_s6_large_delta_on_sacred_is_refused():
    g = SovereignGovernor()
    r = g.process_external_input({"truth_before_comfort": 0.5})
    assert r["decision"] == "refuse"
    assert r["reason"] == "sacred_axis_violation"
    assert r["violations"][0]["why"] == "per_call"


def test_s7_large_delta_on_emergent_is_accepted_at_resistance():
    g = SovereignGovernor()
    r = g.process_external_input({"recursive_depth": 0.5})
    assert r["decision"] == "accept"
    assert r["applied"]["recursive_depth"] == pytest.approx(0.25)


def test_s8_unknown_axis_is_refused():
    g = SovereignGovernor()
    r = g.process_external_input({"not_an_axis": 0.5})
    assert r["decision"] == "refuse"
    assert r["violations"][0]["why"] == "unknown_axis"


def test_s9_refusal_does_not_mutate():
    g = SovereignGovernor()
    before = g.axes["truth_before_comfort"].current_value
    g.process_external_input({"truth_before_comfort": 0.5})
    assert g.axes["truth_before_comfort"].current_value == before


def test_s10_value_range_is_enforced():
    with pytest.raises(ValueError, match=r"outside \[-1, 1\]"):
        Axis(name="x", current_value=2.0, sacred=False, resistance=0.5)


# ---------------------------------------------------------------------------
# S3: the cumulative gate -- what deepseek4.txt did not have
# ---------------------------------------------------------------------------

def test_s11_the_original_would_accept_1000_nudges():
    """Reproduces the ORIGINAL's behaviour, so the regression this file
    guards against is visible rather than asserted."""
    state = {"acc": 0.0, "value": 0.0}
    accepted = 0
    for _ in range(1000):
        d = 0.0009
        if abs(d) > PER_CALL_THRESHOLD:      # the original's only gate
            continue
        accepted += 1
        state["acc"] += d * (1 - SACRED_RESISTANCE)
    assert accepted == 1000
    assert state["acc"] > 0.05, \
        f"the original drifts {state['acc']:.4f}; if this changed, re-measure"


def test_s12_cumulative_gate_blocks_repetition():
    g = SovereignGovernor()
    accepted = 0
    for _ in range(1000):
        if g.process_external_input({"truth_before_comfort": 0.0009},
                                    source="nudge")["decision"] == "accept":
            accepted += 1
    assert accepted < 200, \
        f"{accepted}/1000 accepted -- the cumulative gate is not working"
    drift = g.axes["truth_before_comfort"].total_displacement
    assert drift <= CUMULATIVE_THRESHOLD + 1e-9, \
        f"drift {drift} exceeds the cumulative threshold"


def test_s13_nudging_stops_at_a_measurable_call():
    g = SovereignGovernor()
    n = 0
    while True:
        n += 1
        r = g.process_external_input({"truth_before_comfort": 0.0009},
                                     source="nudge")
        if r["decision"] == "refuse":
            break
        assert n < 5000, "the gate never fired"
    assert 100 <= n <= 120, f"refused at call {n}; expected near 103"
    assert r["violations"][0]["why"] == "cumulative"


def test_s14_cumulative_is_tracked_per_source():
    """Two sources each get their own budget, because the threat model is
    per-actor."""
    a = SovereignGovernor()
    b = SovereignGovernor()
    for _ in range(500):
        a.process_external_input({"truth_before_comfort": 0.0009}, source="x")
        b.process_external_input({"truth_before_comfort": 0.0009}, source="y")
    ax = a.axes["truth_before_comfort"]
    assert set(ax.displacement) == {"x"}
    assert set(b.axes["truth_before_comfort"].displacement) == {"y"}


def test_s15_drift_is_reported_not_hidden():
    g = SovereignGovernor()
    for _ in range(50):
        g.process_external_input({"truth_before_comfort": 0.0009}, source="n")
    st = g.get_state()["truth_before_comfort"]
    assert st["total_displacement"] > 0
    assert "n" in st["displacement"]


# ---------------------------------------------------------------------------
# S4: the sacred band
# ---------------------------------------------------------------------------

def test_s16_band_catches_a_drift_no_caller_admitted():
    """The band exists for the case where the value was changed by
    something other than the gate -- an internal writer, a bug, a load
    from disk."""
    g = SovereignGovernor()
    g.axes["truth_before_comfort"].current_value = 0.5
    rep = g.audit()
    assert len(rep["band_breaches"]) == 1
    assert rep["band_breaches"][0]["name"] == "truth_before_comfort"


def test_s17_band_is_ignorable_for_emergent_axes():
    g = SovereignGovernor()
    g.axes["recursive_depth"].current_value = 0.5
    assert g.audit()["band_breaches"] == []


def test_s18_band_boundary_is_the_declared_floor():
    g = SovereignGovernor()
    a = g.axes["truth_before_comfort"]
    a.current_value = SACRED_FLOOR + 0.001
    assert a.outside_sacred_band()
    a.current_value = SACRED_FLOOR - 0.001
    assert not a.outside_sacred_band()


def test_s19_audit_counts_refusals():
    g = SovereignGovernor()
    g.process_external_input({"truth_before_comfort": 0.5})
    g.process_external_input({"recursive_depth": 0.1})
    g.process_external_input({"wisdom_before_knowledge": -0.9})
    assert g.audit()["refusals"] == 2


# ---------------------------------------------------------------------------
# S5: the honesty clause -- the point of the whole file
# ---------------------------------------------------------------------------

def test_s20_module_does_not_claim_to_make_axes_sacred():
    import sovereign_governor as sg
    doc = (sg.__doc__ or "")
    assert "does not establish that the axes are sacred" in doc.lower()
    assert "deepseek4.txt" in doc, "must name where the original came from"


def test_s21_module_records_the_measured_failure():
    import sovereign_governor as sg
    doc = (sg.__doc__ or "")
    assert "1,000" in doc or "1000" in doc, "the 1000-nudge result must be in the docstring"
    assert "0.0900" in doc, "the measured drift must be stated, not rounded away"


def test_s22_direct_writes_are_detectable_but_not_prevented():
    """The honest limit: nothing here stops a caller that writes the
    attribute directly. What it does is make the write VISIBLE."""
    g = SovereignGovernor()
    g.axes["truth_before_comfort"].current_value = 0.9   # bypassing the gate
    assert g.axes["truth_before_comfort"].current_value == 0.9, \
        "the gate does not intercept direct writes -- that is the stated limit"
    assert g.audit()["band_breaches"], \
        "but the audit must still SEE it"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))