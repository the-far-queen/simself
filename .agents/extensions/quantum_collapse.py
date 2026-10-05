"""
quantum_collapse.py — the Quantum Collapse Theorem of Security applied
to simself's gate. adopted from jmikedupont2/meta-meme (MIT).

the theorem (per mike's THE-QUANTUM-COLLAPSE-THEOREM-OF-SECURITY.md):

    A system in computational superposition (multiple paths) is insecure.
    Witness occupation of state space forces a definite state = security.

applied to simself:

    ψ ∈ Superposed(ψ)           : before the gate fires
    ψ ∈ Collapsed(ψ)            : after the gate commits
    ψ ∈ Secured(ψ, w)           : after the gate passes with witness w
    is_secure(ψ)                 : gate returns allow=True

    THEOREM 2:  ∃ s w, ψ = Secured s w  ↔  is_secure ψ
    THEOREM 3:  ∃ s a, ψ = Superposed s a  →  ¬(is_secure ψ)

ψ₀ (constitutional ground) is the irreducible witness. the system
cannot derive ψ₀ from inside; ψ₀ is observed only by witness — hence
ψ₀ is write-protected by ConstitutionalGuard.

the gate doesn't prove ψ₀. the gate proves ψ is Secured by ψ₀.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# ComputationalState — the three-state encoding
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Superposed:
    """ψ in computational superposition. insecure by definition."""
    amplitudes: Tuple[Tuple[str, complex], ...]  # (state_name, complex amplitude)


@dataclass(frozen=True)
class Collapsed:
    """ψ collapsed to a definite state. awaiting witness."""
    state: str


@dataclass(frozen=True)
class Secured:
    """ψ is Secured by witness. this is what the gate produces."""
    state: str
    witness: str  # the reason code, e.g. "gate_passed:commit_asset=gate"


# ComputationalState is the sum type
State = Superposed | Collapsed | Secured


# ---------------------------------------------------------------------------
# is_secure — the gate predicate, formalized
# ---------------------------------------------------------------------------

def is_secure(s: State) -> bool:
    """THEOREM 2: ψ is Secured iff ψ is in Secured state."""
    return isinstance(s, Secured)


def is_insecure(s: State) -> bool:
    """THEOREM 3: superposition implies ¬is_secure."""
    if isinstance(s, Superposed):
        return True
    if isinstance(s, Collapsed):
        # collapsed but not witnessed — not yet secure
        return True
    return False


# ---------------------------------------------------------------------------
# observe_with_witness — the gate operation
# ---------------------------------------------------------------------------

def observe_with_witness(s: State, witness: str) -> State:
    """Collapse the state and add the witness.

    per mike's theorem:
    - Superposed → Secured (collapse + witness)
    - Collapsed  → Secured (witness the collapse)
    - Secured    → Secured (witness composes: w ∧ w')
    """
    if isinstance(s, Superposed):
        # collapse to the highest-amplitude state
        if not s.amplitudes:
            return Secured(state="undefined", witness=witness)
        best = max(s.amplitudes, key=lambda kv: abs(kv[1]))
        return Secured(state=best[0], witness=witness)
    if isinstance(s, Collapsed):
        return Secured(state=s.state, witness=witness)
    if isinstance(s, Secured):
        return Secured(state=s.state, witness=f"{s.witness} ∧ {witness}")
    raise TypeError(f"unknown state type: {type(s)}")


# ---------------------------------------------------------------------------
# occupy_state_space — pin all behavior to constitutional axes
# ---------------------------------------------------------------------------

def occupy_state_space(witnesses: List[str]) -> Dict[str, float]:
    """For each constitutional axis, force amplitude = 1.0 if a witness holds.

    Returns a dict {axis_name: amplitude}. All amplitudes are 1.0 if the
    corresponding witness holds; 0.0 otherwise. this is the constitutional
    guard pinning behavior to the sacred axes.
    """
    sacred = ["boundaries", "coherence", "stability", "authenticity"]
    resilient = ["routing", "recovery", "norm", "commit_radius"]
    result: Dict[str, float] = {}
    for axis in sacred + resilient:
        # a witness holds for an axis if any of the witness strings contains
        # the axis name. this is a simple heuristic; the real check uses
        # simself/src/constitutional/constitution.py
        result[axis] = 1.0 if any(axis in w.lower() for w in witnesses) else 0.0
    return result


# ---------------------------------------------------------------------------
# GateReason — the witness that the gate holds
# ---------------------------------------------------------------------------

GATE_REASONS = frozenset({
    "no_ground",            # ψ₀ not installed
    "drift_exceeded",        # ‖ψ - ψ₀‖ > threshold
    "mode_locked",           # M0 won't allow M1
    "commit_forbidden",      # commit_asset="forbid"
    "forbidden_motif",       # asset text matched a banned term
    "banned_term",           # lyric/voice check failed
    "no_source_id",          # film/track/mechanic missing pd source
    "royalty_mode_invalid",  # non-pd source
    "ground_touch",          # still/3d/comic touched ground
    "a11y_too_low",           # image sheet below WCAG
    "naked_asset",           # no_sheet / no_shot / no_track / no_mechanic
    "no_app_id",             # app missing app_id
    "no_voice_id",           # voice missing voice_id
    "gate_passed",           # success — gate allowed the asset through
    "witness_held",          # ψ is Secured by the constitutional ground
})


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # start in superposition — insecure
    s0 = Superposed(amplitudes=(("normal", complex(0.99, 0)), ("shellcode", complex(0.01, 0))))
    print(f"initial state: {s0}")
    assert is_insecure(s0), "superposition must be insecure"
    print(f"  insecure? {is_insecure(s0)} ✓")

    # gate fires — gate_passed witness
    s1 = observe_with_witness(s0, "gate_passed")
    print(f"\nafter gate: {s1}")
    assert is_secure(s1), "after gate with witness, must be secure"
    assert isinstance(s1, Secured), "must be Secured"
    print(f"  secure? {is_secure(s1)} ✓")
    print(f"  state: {s1.state}")
    print(f"  witness: {s1.witness}")

    # gate refused — gate stays refused
    s0_again = Superposed(amplitudes=(("attacker_path", complex(1.0, 0)),))
    s2 = observe_with_witness(s0_again, "forbidden_motif:blood")
    print(f"\nrefused gate: {s2}")
    assert is_secure(s2), "refusal witness also secures (but refused)"
    print(f"  secure? {is_secure(s2)} ✓ (witness held, but state is the refused one)")

    # collapse without witness — still insecure
    s3 = Collapsed(state="undefined")
    print(f"\ncollapsed without witness: {s3}")
    assert is_insecure(s3), "Collapsed without witness is insecure"
    print("  insecure? yes ✓")

    # occupy state_space
    amps = occupy_state_space(["boundaries", "coherence", "stability", "authenticity"])
    print(f"\noccupied amplitudes: {amps}")
    assert amps["boundaries"] == 1.0
    assert amps["routing"] == 0.0
    print("  sacred axes pinned, resilient axes unoccupied ✓")

    print("\nALL QUANTUM_COLLAPSE TESTS PASS")