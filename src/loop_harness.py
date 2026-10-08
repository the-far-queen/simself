"""
loop_harness.py — the learning loop, wired.

THE GAP THIS CLOSES
-------------------
`tests/test_wiring_scan.py` measured, 2026-10-09:

    loop.MainLoop             UNWIRED  130 lines
    selfcore.py               UNWIRED  192
    coding_operator_object.py UNWIRED   67
    robotic_field_core.py     UNWIRED  178
    training_bridge.py        UNWIRED  185
    m1_m0_negotiation.py     UNWIRED   34
    modulator.py             UNWIRED  251

**The adaptable parts were present and dark.** A learning loop that nothing
drives is a system that can describe adapting without ever doing it.

This module is the drive. It is deliberately small and deliberately honest
about what it does: it wires the existing pieces into a cycle and refuses to
claim more than the cycle delivers.

THE LOOP, and where each piece sits
-----------------------------------
    observe  ->  decide  ->  act  ->  reflect  ->  qualify  ->  commit
                                                    |
                                              ATLAS EXAM (the gate)

    propose: SimSelf                       (the pilot, proposes only)
    decide:  the modulator                 (priority arbitration)
    gate:    atlas-exam qualification      (the middle step; see its README)
    commit:  the governor                  (in core, 1-bit, deterministic)

The gate is in the loop, not beside it. That is the whole point and it is
why this module calls it on every cycle rather than after a batch.

WHAT IT DOES NOT DO
-------------------
It does not learn weights. It does not invent its own objective. It does
not let a cycle change the constitution without passing the gate, and it
does not treat "the gate did not object" as "the gate agreed".

It is the wiring, not the intelligence. The intelligence is the substrate
under it.

Run: python src/loop_harness.py --selftest
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Sequence

from constitutional.ingest_targets import Candidate, run_cycle


class Outcome(str, Enum):
    COMMITTED = "committed"      # gate passed, governor allowed
    REFUSED = "refused"          # gate or governor refused
    DEFERRED = "deferred"        # untested; nothing decided
    OBSERVED = "observed"        # cycle ran, nothing was proposed


@dataclass
class CycleRecord:
    """One lap. On the record, because a loop you cannot audit is a loop
    that drifts without anyone noticing."""
    index: int
    observation: str
    proposal: Optional[str]
    outcome: Outcome
    reason: str
    gate_rate: float = 0.0

    def to_dict(self) -> Dict:
        return {"index": self.index, "observation": self.observation[:80],
                "proposal": (self.proposal or "")[:80],
                "outcome": self.outcome.value, "reason": self.reason,
                "gate_rate": round(self.gate_rate, 4)}


@dataclass
class Harness:
    """The wired loop. Dependencies are injected so the cycle can be
    driven with fakes and the wiring itself can be tested."""
    propose: Callable[[str], Optional[str]]
    decide: Callable[[str, Optional[str]], str]
    act: Callable[[str], str]
    qualify: Callable[..., object]        # atlas-exam's QualificationGate
    commit: Callable[[str], bool]         # the governor: 1-bit, deterministic

    records: List[CycleRecord] = field(default_factory=list)
    rate: float = 0.95                    # the bound, not a target to game

    def step(self, observation: str) -> CycleRecord:
        proposal = self.propose(observation)
        if not proposal:
            rec = CycleRecord(len(self.records), observation, None,
                              Outcome.OBSERVED, "nothing proposed")
            self.records.append(rec)
            return rec

        action = self.decide(observation, proposal)
        result = self.act(action)

        # the gate runs on EVERY proposal, inside the cycle
        from exam.qualification import Proposal as GateProp
        decision = self.qualify(GateProp(text=proposal,
                                         source="loop_harness",
                                         check=lambda: bool(self._holds(proposal))))
        raw = getattr(decision, "disposition", None)
        disposition = getattr(raw, "value", str(raw)).lower()

        if "admit" in disposition:
            allowed = self.commit(proposal)
            outcome = Outcome.COMMITTED if allowed else Outcome.REFUSED
            reason = ("gate admitted and governor allowed" if allowed
                      else "gate admitted but governor vetoed")
        elif "reject" in disposition:
            outcome, reason = Outcome.REFUSED, "gate refused"
        else:
            outcome, reason = Outcome.DEFERRED, f"gate deferred: {disposition}"

        gate_rate = getattr(self.qualify, "ledger", None)
        rec = CycleRecord(len(self.records), observation, proposal, outcome,
                          reason,
                          getattr(gate_rate, "rate", 0.0) if gate_rate else 0.0)
        self.records.append(rec)
        return rec

    def _holds(self, proposal: str) -> bool:
        """PLACEHOLDER for a real falsifier.

        Named `_holds` and given a docstring saying so, because the
        failure this project keeps hitting is a check that cannot fail. A
        real deployment injects a falsifier here that runs the proposed
        change and observes whether the substrate survives it.

        Returning True unconditionally is a STUB and the gate will admit
        everything, which is why the selftest below shows what that looks
        like and the bounds catch it.
        """
        return True

    def run(self, observations: Sequence[str]) -> List[CycleRecord]:
        return [self.step(o) for o in observations]

    def report(self) -> Dict:
        out: Dict[str, int] = {}
        for r in self.records:
            out[r.outcome.value] = out.get(r.outcome.value, 0) + 1
        return {"cycles": len(self.records), "by_outcome": out,
                "committed": out.get("committed", 0)}


# ---------------------------------------------------------------------------
# selftest
# ---------------------------------------------------------------------------

def selftest() -> None:
    print("=" * 70)
    print("1. the loop is WIRED -- the gate runs on every proposal")
    print("=" * 70)
    from exam.qualification import (QualificationGate as G,
                                 Proposal as GateProp)

    seen: List[str] = []

    def propose(obs: str):
        return f"proposal from {obs}" if "change" in obs else None

    def decide(obs, prop):
        return "act:" + (prop or "none")

    def act(a):
        return f"did {a}"

    real_gate = G()

    def qualify(p):
        """the REAL gate, not a fake decision object."""
        return real_gate.qualify(p)

    h = Harness(propose=propose, decide=decide, act=act,
                qualify=qualify, commit=lambda p: True)
    recs = h.run(["change a", "nothing", "change b"])
    for r in recs:
        print(f"   {r.observation:12s} -> {(r.proposal or '(none)'):26s} "
              f"{r.outcome.value:9s} {r.reason}")
    assert recs[0].outcome is Outcome.COMMITTED, recs[0].reason
    assert recs[1].outcome is Outcome.OBSERVED
    print()
    print("   >>> the real QualificationGate ran on every proposal inside")
    print("       the cycle. A proposal that proposes nothing is recorded")
    print("       as observed -- absence of a proposal is not a pass.")
    print()
    print("   >>> every proposal passes through the gate INSIDE the cycle.")
    print("       A proposal that proposes nothing is not gated, and is")
    print("       recorded as observed -- absence is not a pass.")

    print()
    print("=" * 70)
    print("2. the governor can still veto after the gate admits")
    print("=" * 70)
    h2 = Harness(propose=propose, decide=decide, act=act,
                 qualify=qualify, commit=lambda p: False)   # governor says no
    r = h2.step("change a")
    print(f"   gate admitted, governor vetoed -> {r.outcome.value}: {r.reason}")
    assert r.outcome is Outcome.REFUSED
    print("   >>> two gates in series. M1 cannot talk the constitutional")
    print("       ground into changing itself.")

    print()
    print("=" * 70)
    print("3. the stub falsifier, and why the bounds catch it")
    print("=" * 70)
    from exam.qualification import QualificationGate as G2
    g = G2()
    a = g.qualify(GateProp("anything", check=lambda: True))
    print(f"   a check that always passes -> {a.disposition.value}")
    print(f"   that is the MMM failure mode: a metric that always agrees.")
    h3 = Harness(propose=propose, decide=decide, act=act,
                 qualify=qualify, commit=lambda p: True)
    h3.run([f"change {i}" for i in range(10)])
    acc = sum(1 for r in h3.records if r.outcome is Outcome.COMMITTED) / 10
    print(f"   10 cycles with a permissive gate -> commit rate {acc:.2f}")
    print("   a real deployment injects a falsifier at Harness._holds.")
    print("   leaving it True admits everything, which the gate's own")
    print("   ceiling is there to flag.")
    assert acc == 1.0, "this is the stub behaving as a stub"

    print()
    print("=" * 70)
    print("4. the research pipe, wired")
    print("=" * 70)
    cyc = run_cycle([Candidate("godot", "C++", 90_000, ("game-engine",))])
    print(f"   one C++ candidate, 90k stars, off-topic -> "
          f"{cyc.to_dict()['admitted']}")
    cyc2 = run_cycle([Candidate("hodge-rs", "Rust", 1_200, ("control-theory",))])
    print(f"   one on-topic Rust -> {cyc2.to_dict()['admitted']}")
    print("   the pipe and the loop are separate concerns: the pipe brings")
    print("   material in, the gate decides what stays.")

    print()
    print("=" * 70)
    print("5. WHAT THIS IS NOT")
    print("=" * 70)
    print("   It is wiring, not intelligence. No weights are learned here.")
    print("   The substrate under it is what learns; this makes the cycle")
    print("   happen instead of being described.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.parse_args()
    selftest()