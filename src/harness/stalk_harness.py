"""
stalk_harness.py — runtime that loads stalk topologies, drives them, and
                    reports status to the SimSelf agent.

The harness is the middle layer:
  - substrate (fieldcore/src/modal_field_core.py)   — dynamics
  - topology  (fieldcore/src/stalk_topology.py)    — geometry / braids
  - harness   (this file)                          — runtime + gate interface

Responsibilities:
  1. Instantiate stalk topologies from config.
  2. Tick them in lockstep with the substrate.
  3. Surface topology status to the agent's status endpoint.
  4. Gate topology mutations through the existing Gate so the Governor
     can veto unsafe changes (e.g. mutations of the immutable inner core).

Design:
  The harness owns the topology. Mutations (braid, resonate, extend,
  detach) are proposals; they go through `gate_propose()`. The Gate's
  Governor decides. Mutations are applied only on ALLOW. The harness
  logs every proposal + decision for the ledger.

Status:
  Every tick, the harness returns a `StalkHarnessStatus` dataclass with
  the topology snapshot, the substrate coherence, the gate decision log,
  and a count of pending mutations.

Usage:
    from harness.stalk_harness import StalkHarness
    h = StalkHarness(substrate=substrate_obj, gate=gate_obj)
    h.load_stalks([stalk1, stalk2, ...])
    for _ in range(N):
        status = h.tick()
        # expose status to agent / UI
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Topology lives in fieldcore/src/stalk_topology.py
# Path: simself/src/harness/stalk_harness.py -> fieldcore/src/stalk_topology.py
import sys
import os

_FIELDCORE_SRC = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "fieldcore", "src")
)
if _FIELDCORE_SRC not in sys.path:
    sys.path.insert(0, _FIELDCORE_SRC)

from stalk_topology import (  # noqa: E402
    Stalk,
    StalkTopology,
    StalkState,
    braid,
    unbraid,
    nest,
    add_cross_member,
    resonate,
    detach,
    attach,
    extend,
)


# ---------------------------------------------------------------------------
# Status types
# ---------------------------------------------------------------------------

@dataclass
class GateDecision:
    """One gate decision log entry."""
    action: str
    decision: str           # ALLOW / REFUSE / DEFER
    reason: str
    timestamp: float


@dataclass
class StalkHarnessStatus:
    """Status snapshot returned after each tick."""
    tick: int
    topology: Dict[str, Any]
    substrate_coherence: float
    pending_mutations: int
    gate_log_tail: List[GateDecision] = field(default_factory=list)
    uptime_s: float = 0.0


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------

class StalkHarness:
    """Runtime for stalk topologies on a substrate, gated by the agent."""

    def __init__(self, substrate=None, gate=None, log_capacity: int = 256) -> None:
        self.substrate = substrate        # any object with .coherence() -> float
        self.gate = gate                  # the Gate instance from gate.py
        self.topology = StalkTopology()
        self.log: List[GateDecision] = []
        self.log_capacity = log_capacity
        self.pending: List[Dict[str, Any]] = []
        self._started = time.time()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def load_stalks(self, stalks: List[Stalk]) -> int:
        """Bulk-load stalks. Returns the count loaded."""
        before = len(self.topology.stalks)
        for s in stalks:
            self.topology.add(s)
        return len(self.topology.stalks) - before

    def add_stalk(self, s: Stalk) -> None:
        """Single-stalk add. Goes through gate."""
        self.propose({
            "op": "add",
            "stalk": s,
            "apply": lambda: self.topology.add(s),
            "label": f"add:{s.id}",
        })

    # ------------------------------------------------------------------
    # Mutation proposals (gated)
    # ------------------------------------------------------------------
    def propose(self, mutation: Dict[str, Any]) -> str:
        """Submit a topology mutation for Governor approval.

        `mutation` must contain:
          - op:    str (description of operation)
          - apply: callable that performs the mutation
          - label: str for logging
        The Gate is consulted. On ALLOW, `apply()` is run and the
        decision is logged. On REFUSE / DEFER, nothing happens.
        """
        if self.gate is None:
            # No gate -> apply directly. Useful for tests.
            mutation["apply"]()
            self._log(mutation["op"], "ALLOW", "no-gate")
            return "ALLOW"

        # Coherence comes from the substrate if available.
        coherence = (
            self.substrate.coherence()
            if self.substrate is not None and hasattr(self.substrate, "coherence")
            else 1.0
        )
        try:
            decision = self.gate.check(
                action=mutation["op"],
                context={"label": mutation["label"]},
                coherence=coherence,
            )
        except Exception as exc:
            decision = "DEFER"
            self._log(mutation["op"], decision, f"gate-error:{exc}")
            self.pending.append(mutation)
            return decision

        if decision == "ALLOW":
            try:
                mutation["apply"]()
                self._log(mutation["op"], decision, "ok")
            except Exception as exc:
                self._log(mutation["op"], "REFUSE", f"apply-error:{exc}")
                return "REFUSE"
        else:
            self.pending.append(mutation)
            self._log(mutation["op"], decision, "queued")
        return decision

    def propose_braid(self, a_id: str, b_id: str) -> str:
        """Gated braid."""
        a = self.topology.stalks.get(a_id)
        b = self.topology.stalks.get(b_id)
        if a is None or b is None:
            return "REFUSE"
        return self.propose({
            "op": "braid",
            "label": f"braid:{a_id}<->{b_id}",
            "apply": lambda: braid(a, b),
        })

    def propose_resonate(self, a_id: str, b_id: str) -> str:
        a = self.topology.stalks.get(a_id)
        b = self.topology.stalks.get(b_id)
        if a is None or b is None:
            return "REFUSE"
        return self.propose({
            "op": "resonate",
            "label": f"resonate:{a_id}<->{b_id}",
            "apply": lambda: resonate(a, b),
        })

    def propose_detach(self, stalk_id: str) -> str:
        s = self.topology.stalks.get(stalk_id)
        if s is None:
            return "REFUSE"
        return self.propose({
            "op": "detach",
            "label": f"detach:{stalk_id}",
            "apply": lambda: detach(s),
        })

    def propose_extend(self, stalk_id: str,
                       new_length: float, new_girth: float) -> str:
        s = self.topology.stalks.get(stalk_id)
        if s is None:
            return "REFUSE"
        return self.propose({
            "op": "extend",
            "label": f"extend:{stalk_id}",
            "apply": lambda: extend(s, new_length, new_girth),
        })

    # ------------------------------------------------------------------
    # Tick
    # ------------------------------------------------------------------
    def tick(self) -> StalkHarnessStatus:
        """One harness tick: advance topology, refresh contacts, snapshot."""
        self.topology.tick()
        coherence = (
            self.substrate.coherence()
            if self.substrate is not None and hasattr(self.substrate, "coherence")
            else 1.0
        )
        return StalkHarnessStatus(
            tick=self.topology.tick_count,
            topology=self.topology.status(),
            substrate_coherence=coherence,
            pending_mutations=len(self.pending),
            gate_log_tail=self.log[-self.log_capacity:],
            uptime_s=time.time() - self._started,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _log(self, action: str, decision: str, reason: str) -> None:
        entry = GateDecision(
            action=action, decision=decision, reason=reason,
            timestamp=time.time(),
        )
        self.log.append(entry)
        if len(self.log) > self.log_capacity:
            self.log = self.log[-self.log_capacity:]

    def flush_pending(self) -> int:
        """Re-submit all pending mutations. Returns how many were retried."""
        retry, self.pending = self.pending, []
        for mut in retry:
            self.propose(mut)
        return len(retry)


# ---------------------------------------------------------------------------
# Minimal gate stub for tests / standalone use
# ---------------------------------------------------------------------------

class _AllowAllGate:
    """Stand-in for the Gate when running outside an agent."""
    def check(self, action: str, context: Dict, coherence: float) -> str:
        return "ALLOW"


def default_harness(substrate=None) -> StalkHarness:
    """A harness with an allow-all gate (useful for tests + demos)."""
    return StalkHarness(substrate=substrate, gate=_AllowAllGate())


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    import math
    from stalk_topology import (
        Stalk, StalkAttachment, StalkGeometry, AttachmentSide,
    )

    h = default_harness()
    s1 = Stalk(
        id="alpha",
        inner=StalkAttachment(AttachmentSide.INNER, 0.0, 0.0),
        outer=StalkAttachment(AttachmentSide.OUTER, math.pi / 2, 0.0),
        geometry=StalkGeometry(
            length=1.0, girth=0.05, winding=0,
            control_points=[(0.0, 0.0), (math.pi / 2, 0.0)],
        ),
    )
    s2 = Stalk(
        id="beta",
        inner=StalkAttachment(AttachmentSide.INNER, 0.0, 0.0),
        outer=StalkAttachment(AttachmentSide.OUTER, math.pi / 2, 0.0),
        geometry=StalkGeometry(
            length=1.0, girth=0.05, winding=1,
            control_points=[(0.0, 0.0), (math.pi / 2, 0.0)],
        ),
    )
    h.load_stalks([s1, s2])

    print("Braid:", h.propose_braid("alpha", "beta"))
    print("Tick 1:", h.tick())
    print("Detach alpha:", h.propose_detach("alpha"))
    print("Tick 2:", h.tick())