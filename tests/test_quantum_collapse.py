"""
test_quantum_collapse.py — Quantum Collapse Theorem tests for simself.

Adopted from jmikedupont2/meta-meme/THE-QUANTUM-COLLAPSE-THEOREM-OF-SECURITY.md (MIT).

Theorems tested:
    THEOREM 2: collapse IS security (Secured state <-> is_secure)
    THEOREM 3: superposition IS insecurity (Superposed -> not is_secure)
    Gate semantics: gate_passed witness -> Secured; forbidden witness -> Secured (with refused state)
    Witness composition: witness ∧ witness' composes under multiple observations
    Constitutional occupation: sacred axes pinned at amplitude 1.0 when witness holds
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src" / "constitutional"))

from quantum_collapse import (  # noqa: E402
    Superposed, Collapsed, Secured, is_secure, is_insecure,
    observe_with_witness, occupy_state_space, GATE_REASONS,
)


def test_q1_superposition_is_insecure():
    """THEOREM 3: a Superposed state is not secure."""
    s = Superposed(amplitudes=(("a", complex(0.5, 0)), ("b", complex(0.5, 0))))
    assert is_insecure(s)
    assert not is_secure(s)
    print("Q1: ok")


def test_q2_collapse_without_witness_insecure():
    """Collapsed without witness is not yet secure."""
    s = Collapsed(state="some_state")
    assert is_insecure(s)
    assert not is_secure(s)
    print("Q2: ok")


def test_q3_secured_after_witness():
    """Secured state = gate passed with witness."""
    s = Secured(state="normal", witness="gate_passed")
    assert is_secure(s)
    assert not is_insecure(s)
    print("Q3: ok")


def test_q4_gate_passed_collapses_to_secured():
    """observe_with_witness(Superposed) -> Secured."""
    s0 = Superposed(amplitudes=(
        ("normal", complex(0.99, 0)),
        ("shellcode", complex(0.01, 0)),
    ))
    s1 = observe_with_witness(s0, "gate_passed")
    assert isinstance(s1, Secured)
    assert s1.state == "normal"  # highest amplitude wins
    assert s1.witness == "gate_passed"
    print(f"Q4: ok (collapsed to {s1.state})")


def test_q5_gate_refused_also_secures():
    """observe_with_witness(refused_superposition) -> Secured with refused witness.

    Per the theorem: the gate either collapses-and-secures OR collapses-and-refuses.
    In both cases the system is Secured by the witness, but the witness says 'no'.
    """
    s0 = Superposed(amplitudes=(("attacker_path", complex(1.0, 0)),))
    s1 = observe_with_witness(s0, "forbidden_motif:blood")
    assert isinstance(s1, Secured)
    assert s1.witness == "forbidden_motif:blood"
    print(f"Q5: ok (refused path, but witness held)")


def test_q6_witness_composition():
    """Secured + Secured -> Secured with composed witness (w ∧ w')."""
    s0 = Secured(state="normal", witness="gate_passed")
    s1 = observe_with_witness(s0, "witness_held")
    assert isinstance(s1, Secured)
    assert s1.state == "normal"
    assert "gate_passed" in s1.witness
    assert "witness_held" in s1.witness
    print(f"Q6: ok (composed witness)")


def test_q7_occupy_state_space_pins_sacred():
    """When a sacred axis witness is present, its amplitude is 1.0."""
    amps = occupy_state_space(["boundaries", "coherence", "stability", "authenticity"])
    assert amps["boundaries"] == 1.0
    assert amps["coherence"] == 1.0
    assert amps["stability"] == 1.0
    assert amps["authenticity"] == 1.0
    # resilient axes are unoccupied by default
    assert amps["routing"] == 0.0
    assert amps["recovery"] == 0.0
    print(f"Q7: ok (4 sacred pinned)")


def test_q8_occupy_state_space_pin_specific_axis():
    """A specific witness can pin a specific axis."""
    amps = occupy_state_space(["commit_radius_occupied"])
    assert amps["commit_radius"] == 1.0
    assert amps["boundaries"] == 0.0  # not pinned
    print("Q8: ok")


def test_q9_gate_reasons_complete():
    """GATE_REASONS includes the canonical simself reason codes."""
    required = {
        "no_ground", "drift_exceeded", "mode_locked", "commit_forbidden",
        "forbidden_motif", "banned_term", "no_source_id", "royalty_mode_invalid",
        "ground_touch", "a11y_too_low", "naked_asset", "gate_passed", "witness_held",
    }
    missing = required - GATE_REASONS
    assert not missing, f"missing: {missing}"
    print(f"Q9: ok ({len(GATE_REASONS)} reason codes)")


def test_q10_full_gate_roundtrip():
    """A gate roundtrip: superposition -> secured -> refined with witness."""
    # initial: superposed
    s = Superposed(amplitudes=(("happy", 0.7), ("sad", 0.3)))
    # gate 1: pass
    s2 = observe_with_witness(s, "gate_passed:gate")
    assert is_secure(s2)
    assert s2.state == "happy"
    # gate 2: refine
    s3 = observe_with_witness(s2, "witness_held:constitutional_ground")
    assert is_secure(s3)
    assert s3.state == "happy"
    assert "gate_passed:gate" in s3.witness
    assert "witness_held:constitutional_ground" in s3.witness
    print(f"Q10: ok (full roundtrip)")


def main():
    test_q1_superposition_is_insecure()
    test_q2_collapse_without_witness_insecure()
    test_q3_secured_after_witness()
    test_q4_gate_passed_collapses_to_secured()
    test_q5_gate_refused_also_secures()
    test_q6_witness_composition()
    test_q7_occupy_state_space_pins_sacred()
    test_q8_occupy_state_space_pin_specific_axis()
    test_q9_gate_reasons_complete()
    test_q10_full_gate_roundtrip()
    print("\nALL QUANTUM_COLLAPSE TESTS PASS (Q1..Q10)")


if __name__ == "__main__":
    main()