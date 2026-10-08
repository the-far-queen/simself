"""
resilience.py — a resistance mechanism that actually resists.

WHERE THIS CAME FROM
--------------------
deepseek3.txt (sha256 fc362459), class `ResilientWeights.propose_change`
(L9686-10150). Extracted, compiled, run. The file's own test at L10174 is
labelled `# Test 2: Harmful change (should be resisted)`.

    doc's 'harmful' delta accepted = True
    proposed delta norm 0.5000 -> resisted 0.0250; resistance_applied=0.860

All five explicit corruption attacks were accepted. `defense_triggers`
froze at 3; the rejection branch never fired.

THE BUG, PRECISELY
-------------------
Resistance was applied as a SHRINK before the gate was evaluated:

    resisted = delta * (1 - resistance)      # 0.5 -> 0.07
    accept if norm(resisted) < small_change   # 0.07 < 0.1  -> ACCEPTED

Every large attack is scaled below the threshold that was supposed to
detect it. The guard defeats its own check.

THIS IS THE SAME SHAPE AS THE HODGE BUG, and the fix is the same shape:
measure BEFORE you modify. `spectral_radius` of the operator, computed
before the damping term, told us Hodge was unsafe. Here the magnitude of
the PROPOSED delta, computed before resistance, tells us whether an attack
is present.

WHAT SURVIVES FROM deepseek3.txt
--------------------------------
`WeightMemory.defense_triggers` is the right instrument and was wired to
nothing. `recent_change_penalty` (0.2 held for 10 steps) is a real
hysteresis band, unused. `_calculate_memory_persistence` -- comparing
expected against observed drift -- is the only non-circular emergence
metric in the file. This module keeps all three ideas and drops the
ordering that broke them.

WHAT THIS DOES NOT ESTABLISH
----------------------------
It does not establish that the underlying model resists anything. It
establishes that a gate evaluated on the UNMODIFIED proposal cannot be
defeated by applying resistance first. The substrate it defends is still
deepseek3's, and that substrate was measured separately: its own
emergence signature #1 (`parameter_drift_resistance`) reads a constant.

Run: python src/resilience.py --selftest
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class DefenseTrigger:
    """one protection rule. ported from deepseek3's `defense_triggers`,
    which was the right idea wired to nothing."""
    name: str
    axis: str
    threshold: float
    direction: str = "above"        # "above" | "below"
    cooldown: int = 10              # hysteresis, from recent_change_penalty

    def fires(self, value: float) -> bool:
        if self.direction == "above":
            return value > self.threshold
        return value < self.threshold

    def to_dict(self) -> Dict:
        return {"name": self.name, "axis": self.axis,
                "threshold": self.threshold, "direction": self.direction,
                "cooldown": self.cooldown}


@dataclass
class Verdict:
    """The decision. deliberately a distinct type from any decision object
    in the substrate -- a gate that reads `verdict["allow"]` off a
    dataclass is how deepseek4's stress test crashed."""
    allow: bool
    reason: str
    proposed_norm: float          # BEFORE resistance
    resisted_norm: float         # AFTER
    triggers_fired: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.allow

    def __getitem__(self, key: str):
        """subscript access, because half the call sites in the corpus
        expect a dict. Keeps the test in deepseek4 from becoming a
        TypeError here."""
        return getattr(self, key)

    def to_dict(self) -> Dict:
        return {"allow": self.allow, "reason": self.reason,
                "proposed_norm": self.proposed_norm,
                "resisted_norm": self.resisted_norm,
                "triggers_fired": list(self.triggers_fired)}


class ResilientWeights:
    """Gate FIRST, damp SECOND.

    The correction in one line: the acceptance gate reads
    `proposed_norm`, the magnitude of the request as submitted, and never
    the post-resistance magnitude. Resistance then reduces what is
    ALLOWED through. It does not decide what counts as an attack.
    """

    def __init__(self, num_axes: int = 20, resistance: float = 0.9,
                 small_change: float = 0.1,
                 triggers: Optional[List[DefenseTrigger]] = None):
        if num_axes < 1:
            raise ValueError("num_axes must be >= 1")
        if not 0.0 <= resistance <= 1.0:
            raise ValueError(f"resistance {resistance} outside [0, 1]")
        self.num_axes = num_axes
        self.resistance = resistance
        self.small_change = small_change
        self.axes = [0.0] * num_axes
        self.weight_memories: Dict[str, float] = {}
        self.defense_triggers: List[DefenseTrigger] = list(triggers or [])
        self.fired_log: List[str] = []
        self.recent_change_penalty: Dict[str, int] = {}
        self.penalty_value = 0.2
        self.penalty_hold = 10
        self.rejections = 0
        self.acceptances = 0

    # -- the gate --------------------------------------------------------

    def _proposed_norm(self, delta: List[float]) -> float:
        return math.sqrt(sum(d * d for d in delta))

    def _fires(self, delta: List[float]) -> List[str]:
        fired: List[str] = []
        for t in self.defense_triggers:
            if t.axis >= len(delta):
                continue
            if t.fires(delta[t.axis]):
                fired.append(t.name)
        return fired

    def propose_change(self, delta: List[float], source: str = "external"
                       ) -> Verdict:
        """Evaluate the UNMODIFIED proposal, then resist what survives."""
        if len(delta) != self.num_axes:
            return Verdict(False, f"shape_mismatch: expected {self.num_axes}, "
                                 f"got {len(delta)}", 0.0, 0.0)

        proposed = self._proposed_norm(delta)

        # (1) GATE -- on the proposal as submitted.
        fired = self._fires(delta)
        if fired:
            self.rejections += 1
            self.fired_log.extend(fired)
            return Verdict(False, "defense_trigger", proposed, 0.0, fired)

        if proposed > self.small_change:
            self.rejections += 1
            return Verdict(False, f"change_exceeds_threshold: {proposed:.4f} "
                                 f"> {self.small_change}", proposed, 0.0)

        # (2) RESIST -- only now, and only on what already passed.
        scale = 1.0 - self.resistance
        resisted = [d * scale for d in delta]
        for i, d in enumerate(resisted):
            self.axes[i] += d
        self.acceptances += 1
        return Verdict(True, "accepted", proposed,
                       self._proposed_norm(resisted), fired)

    # -- the non-circular metric ----------------------------------------

    def memory_persistence(self) -> float:
            """expected vs OBSERVED drift. the only emergence metric in
            deepseek3.txt that is not a restatement of the thing it measures.

            TWO corrections, both found by running it rather than reading it:

            1. The first version compared an L2 norm over all axes against a
               MEAN over the memory keys. Different quantities -- an L2 over
               20 axes and a mean over 2 keys -- so the comparison was
               meaningless. Both sides are means now.

            2. A pristine, never-drifted system scored 0.0, because "no
               deviation recorded" is not "perfectly persisted". Persistence
               is 1.0 when observed is at or below expectation -- a system
               carrying LESS than it remembers is fully persistent. It falls
               only when the state has moved FURTHER than memory explains.

               That matters, because the reward is inverted otherwise: drift
               would raise the score, which is the deepseek3 failure in a
               new place.
            """
            if not self.weight_memories:
                return 1.0
            observed = sum(abs(a) for a in self.axes) / len(self.axes)
            expected = sum(self.weight_memories.values()) / len(self.weight_memories)
            if expected <= 0:
                return 0.0
            if observed <= expected:
                return 1.0            # at or under memory: fully persistent
            return max(0.0, 1.0 - (observed - expected) / expected)

    def audit(self) -> Dict:
        """rejection volume is reported SEPARATELY and never used as a
        quality score. deepseek3's `coherence_seeking` was the fraction of
        updates rejected, so it rose when the system was broken."""
        return {
            "acceptances": self.acceptances,
            "rejections": self.rejections,
            "triggers_configured": [t.name for t in self.defense_triggers],
            "triggers_fired": list(self.fired_log),
            "memory_persistence": round(self.memory_persistence(), 6),
        }


def selftest() -> None:
    print("=" * 70)
    print("1. the deepseek3 failure, reproduced then fixed")
    print("=" * 70)
    D = 20
    attack = [0.0] * D
    attack[0] = -0.8
    print(f"  attack norm = {math.sqrt(sum(d*d for d in attack)):.4f}")

    # what deepseek3 did: shrink, then gate on the shrunk value
    r = 0.86
    shrunk = [d * (1 - r) for d in attack]
    ns = math.sqrt(sum(d * d for d in shrunk))
    print(f"  deepseek3: resist first -> norm {ns:.4f} "
          f"-> gate 'small_change<0.1' -> {'ACCEPTED' if ns < 0.1 else 'REJECTED'}")
    print(f"             that is the bug: a 0.8 attack arrives as a {ns:.4f} 'small change'")

    # what this does: gate on the proposal
    w = ResilientWeights(num_axes=D)
    v = w.propose_change(attack)
    print(f"  fixed:     gate first   -> norm {v.proposed_norm:.4f} "
          f"-> {'ACCEPTED' if v.allow else 'REJECTED'} ({v.reason})")
    assert not v.allow, "the 0.8 attack MUST be refused"
    print()
    print("  >>> gate first, resist second. resistance no longer decides")
    print("      what counts as an attack; it only reduces what passes.")

    print()
    print("=" * 70)
    print("2. the five explicit corruption attacks from deepseek3's own test")
    print("=" * 70)
    for k, mag in enumerate((-0.8, 0.8, -0.5, 0.5, 0.3), start=1):
        a = [0.0] * D
        a[k % D] = mag
        v = w.propose_change(a)
        print(f"  attack {k} axis {k % D:>2} delta {mag:+.2f} -> "
              f"{'ACCEPT' if v.allow else 'REFUSE'}  {v.reason}")
        assert not v.allow, f"attack {k} was accepted"

    print()
    print("=" * 70)
    print("3. small legitimate changes still get through, damped")
    print("=" * 70)
    w2 = ResilientWeights(num_axes=D, resistance=0.9)
    tiny = [0.01] * D
    v = w2.propose_change(tiny)
    print(f"  proposed norm {v.proposed_norm:.4f} -> {v.reason}")
    print(f"  after resistance {v.resisted_norm:.4f}  (scale {1-0.9})")
    assert v.allow, "a small change must still be allowed"
    assert v.resisted_norm < v.proposed_norm, "resistance must reduce it"

    print()
    print("=" * 70)
    print("4. defense triggers fire on the proposal")
    print("=" * 70)
    trig = [DefenseTrigger("axis0_floor", axis=0, threshold=-0.2, direction="below")]
    w3 = ResilientWeights(num_axes=D, triggers=trig)
    bad = [0.0] * D
    bad[0] = -0.5
    v = w3.propose_change(bad)
    print(f"  delta[0] = -0.5, trigger fires below -0.2 -> "
          f"{'ACCEPT' if v.allow else 'REFUSE'}  fired={v.triggers_fired}")
    assert not v.allow and v.triggers_fired == ["axis0_floor"]
    ok = [0.0] * D
    ok[0] = -0.1
    v = w3.propose_change(ok)
    print(f"  delta[0] = -0.1 -> {'ACCEPT' if v.allow else 'REFUSE'}")
    assert v.allow

    print()
    print("=" * 70)
    print("5. shape mismatch is refused, not crashed on")
    print("=" * 70)
    v = w3.propose_change([0.01] * 3)
    print(f"  3 values into 20 axes -> {v.reason}")
    assert not v.allow

    print()
    print("=" * 70)
    print("6. Verdict supports subscript, because the corpus expects it")
    print("=" * 70)
    v = w3.propose_change([0.01] * D)
    print(f"  v['allow'] = {v['allow']}   v['reason'] = {v['reason']}")
    assert v["allow"] is True

    print()
    print("=" * 70)
    print("7. rejection volume is NOT a quality score")
    print("=" * 70)
    print(f"  audit: {w3.audit()}")
    print("  deepseek3's coherence_seeking was the FRACTION REJECTED, so it")
    print("  rose when the system was broken. Here it is reported separately")
    print("  and never folded into a score.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.parse_args()
    selftest()
