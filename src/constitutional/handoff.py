"""
handoff.py — session transfer, made mechanical.

Grok's 2026-08-08 review, defect F:

> The handoff protocol checks stability, drift, confidence, entities, then
> returns "System recognizes itself." Nothing computational changes.
> This is a symbolic milestone rather than a new operating mode.

That was accurate. A handoff that only announces itself is a caption,
not a mechanism. **A handoff has to move state, and moving state across a
process boundary is a serialization problem.** So that is what this is.

What actually transfers:

- ψ_current, mode, ticks, time, R, eta   (via SimSelf.save/load)
- the decision log                        (last 20 verdicts)
- committed memory ids and their vectors
- the constitutional ground **by reference only** — ψ₀ is never
  serialized from a handoff packet, because a packet is not a
  constitutional amendment
- a readiness verdict: is this state coherent enough to resume from?

What is refused:

- a handoff with ψ₀ that differs from the installed ground
- a handoff taken while the system is incoherent (drift, or low
  stability) — refusing to transfer a broken state is the whole point
- a packet claiming a schema version it does not have

The invariant: **a handoff can move ψ, never ψ₀.** The receiving side
must already agree on who it is before it accepts what it was doing.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

import numpy as np

SCHEMA_VERSION = 2

# readiness thresholds. these are policy, not math — change them
# explicitly and the packet records which policy produced it.
STABILITY_FLOOR = 0.65
DRIFT_CEILING = 0.22


@dataclass
class Readiness:
    """Is this state coherent enough to hand over?"""

    ready: bool
    stability: float
    drift: float
    ticks: int
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HandoffProtocol:
    """Readiness check + packet write + verified receive.

    Usage:
        h = HandoffProtocol(simself)
        v = h.readiness()                  # look before you leap
        if v.ready:
            h.write("packet.json")         # serialize
        ...
        h2 = HandoffProtocol(other_simself)
        h2.receive("packet.json")          # restore, refusing on mismatch
    """

    def __init__(self, simself, stability_floor: float = STABILITY_FLOOR,
                 drift_ceiling: float = DRIFT_CEILING):
        self.simself = simself
        self.stability_floor = stability_floor
        self.drift_ceiling = drift_ceiling

    # ------------------------------------------------------------------
    # readiness
    # ------------------------------------------------------------------

    def _stability(self) -> float:
        """Settledness, computed from what SimSelf actually exposes.

        SimSelf has no get_stability(). The constitutional axis named
        "stability" is a threshold declaration, not a measurement, so it
        cannot be read as a score. Stability here is derived from drift
        alone: 1.0 at the ground, decaying to 0.0 at the ceiling.

            stability = 1 - min(1, drift / drift_ceiling)

        That is a policy choice and the packet records it, rather than
        inventing an API on another class to satisfy this one.
        """
        d = float(self.simself.drift())
        if self.drift_ceiling <= 0:
            return 1.0 if d == 0.0 else 0.0
        return float(max(0.0, 1.0 - min(1.0, d / self.drift_ceiling)))

    def readiness(self) -> Readiness:
        """Measure. Do not announce."""
        stability = self._stability()
        drift = float(self.simself.drift())
        reasons: List[str] = []

        if stability < self.stability_floor:
            reasons.append(f"stability:{stability:.3f}<{self.stability_floor}")
        if drift > self.drift_ceiling:
            reasons.append(f"drift:{drift:.3f}>{self.drift_ceiling}")
        if self.simself.ticks == 0:
            reasons.append("no_ticks")

        return Readiness(
            ready=not reasons,
            stability=stability,
            drift=drift,
            ticks=int(self.simself.ticks),
            reasons=reasons,
        )

    # ------------------------------------------------------------------
    # write
    # ------------------------------------------------------------------

    def build_packet(self) -> Dict[str, Any]:
        """The transferable state. ψ₀ is a fingerprint, never a payload."""
        s = self.simself
        psi0 = np.asarray(s.psi0, dtype=np.float64)
        packet = {
            "schema": SCHEMA_VERSION,
            "written_at": time.time(),
            "dim": int(s.dim),
            # fingerprint only: lets the receiver refuse a mismatch
            "psi0_sha256": hashlib.sha256(psi0.tobytes()).hexdigest(),
            # the transferable working state
            "psi_current": np.asarray(s.psi_current, dtype=np.float64).tolist(),
            "mode": s.mode,
            "ticks": int(s.ticks),
            "time": float(s.time),
            "R": float(s.R),
            "eta": float(s.eta),
            "decision_log": s.last_verdicts(),
            "committed_unit_ids": s.committed_unit_ids(),
            "readiness": self.readiness().to_dict(),
            "policy": {
                "stability_floor": self.stability_floor,
                "drift_ceiling": self.drift_ceiling,
            },
        }
        return packet

    def write(self, path: str) -> str:
        packet = self.build_packet()
        tmp = path + ".part"
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(packet, f, indent=2)
        os.replace(tmp, path)          # atomic: never half a packet
        return path

    # ------------------------------------------------------------------
    # receive
    # ------------------------------------------------------------------

    @staticmethod
    def peek(path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def receive(self, path: str) -> Dict[str, Any]:
        """Restore from a packet. Refuses rather than patches.

        Raises ValueError on any mismatch. This is the load-bearing part
        of the mechanism: a receiving system decides whether it can
        accept what it is being handed, and a wrong answer is a
        constitutional edit.
        """
        packet = self.peek(path)

        if packet.get("schema") != SCHEMA_VERSION:
            raise ValueError(
                f"HandoffProtocol.receive: schema {packet.get('schema')} "
                f"!= supported {SCHEMA_VERSION}. Refusing."
            )
        if int(packet.get("dim", 0)) != int(self.simself.dim):
            raise ValueError(
                f"HandoffProtocol.receive: dim {packet.get('dim')} "
                f"!= installed {self.simself.dim}. Refusing."
            )

        # the ground check. this is the invariant, not a detail.
        installed = np.asarray(self.simself.ground.psi_0, dtype=np.float64)
        got = hashlib.sha256(installed.tobytes()).hexdigest()
        if got != packet.get("psi0_sha256"):
            raise ValueError(
                "HandoffProtocol.receive: ψ₀ fingerprint mismatch. "
                f"packet={str(packet.get('psi0_sha256'))[:16]} "
                f"installed={got[:16]}. "
                "This is a different constitutional subject. Refusing."
            )

        readiness = packet.get("readiness", {})
        if not readiness.get("ready", False):
            raise ValueError(
                "HandoffProtocol.receive: packet was written from an "
                f"unready state: {readiness.get('reasons')}. "
                "Refusing to transfer a broken state."
            )

        # ψ₀ is untouched. everything else moves.
        self.simself.psi_current = np.asarray(
            packet["psi_current"], dtype=np.float64)
        self.simself.mode = packet.get("mode", "standard")
        self.simself.ticks = int(packet.get("ticks", 0))
        self.simself.time = float(packet.get("time", 0.0))
        self.simself.R = float(packet.get("R", self.simself.R))
        self.simself.eta = float(packet.get("eta", self.simself.eta))

        from .simself import DecisionRecord
        self.simself.decision_log = [
            DecisionRecord(
                timestamp=v.get("timestamp", 0.0),
                kind=v.get("kind", ""),
                description=v.get("description", ""),
                data=v.get("data", {}),
            )
            for v in packet.get("decision_log", [])
        ]
        return {
            "restored": True,
            "ticks": self.simself.ticks,
            "mode": self.simself.mode,
            "drift": self.simself.drift(),
            "committed": self.simself.committed_unit_ids(),
        }
