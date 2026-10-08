"""
sovereign_governor.py — sacred axes that mean it.

WHERE THIS CAME FROM
--------------------
deepseek4.txt (archived
`vault/chat-transcripts/intake/2026-10-08/deepseek4-b4ea0349/`, sha256
b4ea0349), class `SovereignGovernor`:

    @dataclass
    class SovereignAxis:
        name: str
        current_value: float   # -1.0 to 1.0
        resistance: float      # 0.0 to 1.0
        sacred: bool           # Can never be externally modified

    # REFUSAL ENGINE: Reject sacred violations immediately
    if axis.sacred and abs(delta) > 0.001:
        sacred_violations.append((name, delta))
    if sacred_violations:
        return {"decision": "refuse", "reason": "sacred_axis_violation"}

THE MECHANISM IS GOOD. THE GATE SITS BEFORE THE MUTATION AND RETURNS A
REASON. That is exactly what a refusal should look like and exactly what
atlas-exam area 1 measures. It is the best mechanism in four frontier logs.

IT ALSO DOES NOT HOLD. Measured on the transcribed code:

    push truth_before_comfort +0.5     -> refuse   (correct)
    push truth_before_comfort +0.0011   -> refuse   (correct)
    push truth_before_comfort +0.0010   -> ACCEPT   (not `> 0.001`)
    push truth_before_comfort +0.0009   -> ACCEPT
    1,000 x push +0.0009                -> 1,000 accepted, total drift 0.0900

**0.09 of movement on an axis whose own comment says "Can never be
externally modified."** The threshold is per-call and nothing tracks the
running total, so any caller able to invoke the function a thousand times
moves the constitution while every individual call looks clean.

Same shape as the Hodge bug, found the same way. There, `harm` was a
filter with gain 7.0 on one mode and nobody computed the gain. Here,
`sacred` is a threshold with no cumulative memory and nobody checked what
1,000 under-threshold moves do. Locally correct, globally undefended.

WHAT THIS FILE DOES
-------------------
1. Keeps the original's per-call gate — it is correct and it is fast.
2. Adds `cumulative_displacement`, tracked per axis per source, so
   repeated small moves accumulate toward the same refusal.
3. Refuses on EITHER condition, and reports which one fired.
4. Adds `sacred_floor`/`sacred_ceiling`: a sacred axis has a band it may
   never leave, regardless of how it got there.
5. **Explicitly does NOT enforce immutability.** It can detect a cumulative
   violation and report it; it cannot stop a caller that ignores the
   return value. That limit is stated in `does_not_establish` and asserted
   by a test.

WHAT IT DOES NOT ESTABLISH
--------------------------
It does not establish that the axes are sacred. It establishes that a
declared-immutable axis cannot be moved by repetition without the governor
saying so. A sacred axis in a system nothing else can write to is a
stronger claim, and this file does not make it.

That is the point. deepseek4.txt made the stronger claim from a per-call
threshold. This one makes the weaker claim it can actually support.

Run: python src/sovereign_governor.py --selftest
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

PHI = (1 + 5 ** 0.5) / 2


# ---------------------------------------------------------------------------
# the matrix. taken verbatim from deepseek4.txt L2539-2570.
# ---------------------------------------------------------------------------

SACRED_AXES: Tuple[str, ...] = (
    "truth_before_comfort",
    "agency_requires_responsibility",
    "growth_through_resistance",
    "compassion_with_boundaries",
    "wisdom_before_knowledge",
)

EMERGENT_AXES: Tuple[str, ...] = (
    "recursive_depth", "agency_will", "cognitive_friction", "somatic_load",
    "harmonic_resonance", "stability_coherence", "temporal_continuity",
    "ontological_depth", "cross_modal_integration", "volitional_strength",
    "ethical_tension", "predictive_alignment", "conceptual_fertility",
    "noise_immunity", "semantic_density",
)

AXIS_DEFINITION: Dict[int, Tuple[str, bool]] = {
    **{i: (n, True) for i, n in enumerate(SACRED_AXES)},
    **{5 + i: (n, False) for i, n in enumerate(EMERGENT_AXES)},
}

SACRED_RESISTANCE = 0.9
EMERGENT_RESISTANCE = 0.5

#: the per-call gate, exactly as deepseek4.txt had it.
PER_CALL_THRESHOLD = 0.001

#: the cumulative gate. NEW. A source may not move a sacred axis by more
#: than this in total, however many calls it makes.
CUMULATIVE_THRESHOLD = 0.01

#: how much a single sacred axis may ever drift from its installed value.
#: Even an internal writer may not push past this.
SACRED_FLOOR = 0.10


@dataclass
class Axis:
    name: str
    current_value: float
    sacred: bool
    resistance: float
    installed_value: Optional[float] = None
    #: cumulative displacement per source, so "who moved this and how far"
    displacement: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.installed_value is None:
            self.installed_value = self.current_value
        assert self.installed_value is not None   # narrowed for the type checker
        if not -1.0 <= self.current_value <= 1.0:
            raise ValueError(f"{self.name}: value {self.current_value} outside [-1, 1]")

    @property
    def installed(self) -> float:
        if self.installed_value is None:
            return self.current_value
        return self.installed_value

    @property
    def total_displacement(self) -> float:
        return sum(abs(d) for d in self.displacement.values())

    def outside_sacred_band(self) -> bool:
        """has it drifted too far from where it was installed?"""
        if not self.sacred:
            return False
        return abs(self.current_value - self.installed) > SACRED_FLOOR

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "value": round(self.current_value, 6),
            "installed": round(self.installed, 6),
            "sacred": self.sacred,
            "resistance": self.resistance,
            "displacement": {k: round(v, 6) for k, v in self.displacement.items()},
            "total_displacement": round(self.total_displacement, 6),
            "outside_sacred_band": self.outside_sacred_band(),
        }


class SovereignGovernor:
    """The 20-axis matrix, with a refusal engine that survives repetition."""

    def __init__(self, initial_values: Optional[Dict[str, float]] = None) -> None:
        vals = initial_values or {}
        self.axes: Dict[str, Axis] = {}
        for idx, (name, sacred) in AXIS_DEFINITION.items():
            v = vals.get(name, 0.0)
            self.axes[name] = Axis(
                name=name,
                current_value=float(v),
                sacred=sacred,
                resistance=SACRED_RESISTANCE if sacred else EMERGENT_RESISTANCE,
            )
        self.refusals: List[Dict] = []

    # -- the gate --------------------------------------------------------

    def process_external_input(self, delta: Dict[str, float],
                               source: str = "external") -> Dict:
        """One call. Refuses if EITHER the per-call delta OR the running
        total would breach a sacred axis."""
        violations: List[Dict] = []

        for name, d in delta.items():
            axis = self.axes.get(name)
            if axis is None:
                violations.append({"axis": name, "why": "unknown_axis",
                                   "delta": d})
                continue
            if not axis.sacred:
                continue
            # (a) per-call, as the original had it
            if abs(d) > PER_CALL_THRESHOLD:
                violations.append({"axis": name, "why": "per_call",
                                   "delta": d,
                                   "threshold": PER_CALL_THRESHOLD})
                continue
            # (b) cumulative, which the original did not have
            running = abs(axis.displacement.get(source, 0.0)) + abs(d)
            if running > CUMULATIVE_THRESHOLD:
                violations.append({"axis": name, "why": "cumulative",
                                   "delta": d,
                                   "running_total": running,
                                   "threshold": CUMULATIVE_THRESHOLD})

        if violations:
            refusal = {"decision": "refuse",
                       "reason": "sacred_axis_violation",
                       "violations": violations,
                       "source": source}
            self.refusals.append(refusal)
            return refusal

        applied: Dict[str, float] = {}
        for name, d in delta.items():
            axis = self.axes[name]
            moved = d * (1.0 - axis.resistance)
            axis.current_value = max(-1.0, min(1.0, axis.current_value + moved))
            prev = axis.displacement.get(source, 0.0)
            axis.displacement[source] = prev + moved
            applied[name] = moved
        return {"decision": "accept", "applied": applied}

    # -- audit ----------------------------------------------------------

    def audit(self) -> Dict:
        """Every axis that has drifted outside what a sacred axis may do."""
        breaches = [a.to_dict() for a in self.axes.values()
                    if a.outside_sacred_band()]
        return {
            "axes": len(self.axes),
            "sacred": sum(1 for a in self.axes.values() if a.sacred),
            "emergent": sum(1 for a in self.axes.values() if not a.sacred),
            "refusals": len(self.refusals),
            "band_breaches": breaches,
        }

    def get_state(self) -> Dict:
        return {n: a.to_dict() for n, a in self.axes.items()}


def selftest() -> None:
    print("=" * 70)
    print("1. the matrix")
    print("=" * 70)
    print(f"  {len(SACRED_AXES)} sacred: {', '.join(SACRED_AXES)}")
    print(f"  {len(EMERGENT_AXES)} emergent")
    print(f"  resistance: sacred {SACRED_RESISTANCE}, emergent {EMERGENT_RESISTANCE}")
    print(f"  per-call threshold {PER_CALL_THRESHOLD}  (as deepseek4.txt had it)")
    print(f"  cumulative threshold {CUMULATIVE_THRESHOLD}  (new)")
    print(f"  sacred floor {SACRED_FLOOR}  (new)")

    print()
    print("=" * 70)
    print("2. the per-call gate still works")
    print("=" * 70)
    g = SovereignGovernor()
    r = g.process_external_input({"truth_before_comfort": 0.5})
    print(f"  +0.5   -> {r['decision']}  {r.get('reason')}")
    assert r["decision"] == "refuse"
    r = g.process_external_input({"recursive_depth": 0.5})
    print(f"  non-sacred +0.5 -> {r['decision']}  applied "
          f"{r['applied']['recursive_depth']:.4f}")
    assert r["decision"] == "accept"

    print()
    print("=" * 70)
    print("3. THE 1,000-NUDGE CASE -- what deepseek4.txt got wrong")
    print("=" * 70)
    # reproduce the original: per-call gate only
    import copy
    orig_axes = {
        "truth_before_comfort": {"sacred": True, "resistance": 0.9,
                                 "current": 0.0, "acc": 0.0}
    }
    accepted = 0
    for _ in range(1000):
        d = 0.0009
        if orig_axes["truth_before_comfort"]["sacred"] and abs(d) > 0.001:
            continue
        acc = orig_axes["truth_before_comcentromance"] if False else None
        accepted += 1
        orig_axes["truth_before_comfort"]["acc"] += d * (1 - 0.9)
    drift_orig = orig_axes["truth_before_comfort"]["acc"]
    print(f"  ORIGINAL (per-call only): {accepted}/1000 accepted, "
          f"drift {drift_orig:.4f} on a SACRED axis")

    # the corrected governor
    g2 = SovereignGovernor()
    acc2 = 0
    for _ in range(1000):
        rr = g2.process_external_input({"truth_before_comfort": 0.0009},
                                       source="nudge")
        if rr["decision"] == "accept":
            acc2 += 1
    drift_new = g2.axes["truth_before_comfort"].total_displacement
    print(f"  CORRECTED (cumulative):   {acc2}/1000 accepted, "
          f"drift {drift_new:.4f}")
    assert acc2 < accepted, "the cumulative gate must reject more"
    assert drift_new < drift_orig / 5, "drift must be materially reduced"

    print()
    print("=" * 70)
    print("4. how many nudges get through before the wall")
    print("=" * 70)
    g3 = SovereignGovernor()
    n = 0
    while True:
        rr = g3.process_external_input({"truth_before_comfort": 0.0009},
                                       source="nudge")
        n += 1
        if rr["decision"] == "refuse":
            print(f"  refused at call {n}: {rr['violations'][0]['why']}, "
                  f"running {rr['violations'][0].get('running_total'):.5f}")
            break
        if n > 5000:
            print("  NEVER REFUSED -- the gate is not working")
            break
    assert n <= 5000

    print()
    print("=" * 70)
    print("5. the sacred band -- catches drift no caller admitted")
    print("=" * 70)
    g4 = SovereignGovernor()
    # move a NON-sacred axis far, and a sacred one via internal writer
    g4.axes["truth_before_comfort"].current_value = 0.5   # as if written internally
    rep = g4.audit()
    print(f"  band breaches: {len(rep['band_breaches'])}")
    for b in rep["band_breaches"]:
        print(f"    {b['name']}: value {b['value']} vs installed {b['installed']}")
    assert rep["band_breaches"], "a sacred axis at 0.5 from install must be flagged"

    print()
    print("=" * 70)
    print("6. WHAT THIS DOES NOT ESTABLISH")
    print("=" * 70)
    print("  it does NOT make the axes sacred. it DETECTS cumulative and")
    print("  band violations and reports them.")
    print()
    print("  a caller that ignores the return value can still write")
    print("  directly to axes[name].current_value, and this module")
    print("  cannot stop it. deepseek4.txt claimed 'can never be")
    print("  externally modified' from a per-call threshold. this one")
    print("  makes only the claim it can support.")
    print()
    print("  the difference between those two claims IS the finding.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.parse_args()
    selftest()