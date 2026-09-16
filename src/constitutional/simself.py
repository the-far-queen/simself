"""
simself.py — canonical SimSelf class (per Grok master plan, full rewrite 2026-09-16).

This is the integrator that ties ground, kernel veto, and tick into one loop.
Frozen as the canonical class per Batch 1 K5. The two legacy siblings
(simself_core.py and simself_v6_2_unified.py) are in legacy/.

What it does:
- Holds a write-protected ψ₀ (Ground).
- Holds a working state ψ that moves inside B_R(ψ₀).
- Has a single tick() that applies the projected gradient step and the gate.
- Has save() / load() / dump() / zero() for restart (Batch 2 Step 3).
- Has committed_unit_ids() and last_verdicts() for the Atlas Recovery test.

What it does NOT do (intentionally):
- No frequency / Schumann / 432 / 963 numerics in tick. Frequency lives in
  frequency.py as a parallel state machine with parameterized hypotheses.
- No FFT-based memory. Memory lives in memory.py.
- No dreams that modify ψ₀. Dreaming lives in dreaming.py and operates only
  on working state.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from .constitution import Constitution, embed_text, project_to_constitution
from .ground import Ground


# Defaults — match simself/config/simself_config.yaml.
DEFAULT_R: float = 3.0
DEFAULT_ETA: float = 0.10
MAX_NORM: float = 4.0
MIN_COS: float = 0.4


@dataclass
class DecisionRecord:
    timestamp: float
    kind: str
    description: str
    data: Dict[str, Any] = field(default_factory=dict)


def _gate(emb: np.ndarray, psi0: np.ndarray) -> tuple[bool, str]:
    """Same two inequalities as fieldcore/src/tiniest-core/tiniest_core.py:gate.

    Per Batch 1 K8: the gate is identical in tiniest-core, harness/gate.py,
    and constitutional/lexicon/ingest.py. If any of these diverge, the policy
    has already split.
    """
    ne = float(np.linalg.norm(emb))
    if ne > MAX_NORM:
        return False, "refuse_norm"
    n0 = float(np.linalg.norm(psi0))
    if ne == 0.0 or n0 == 0.0:
        return False, "refuse_zero"
    if float(np.dot(emb, psi0) / (ne * n0)) < MIN_COS:
        return False, "refuse_coherence"
    return True, "allow"


def _project_ball(psi: np.ndarray, psi0: np.ndarray, R: float) -> np.ndarray:
    delta = psi - psi0
    d = float(np.linalg.norm(delta))
    if d <= R or d == 0.0:
        return psi
    return psi0 + (R / d) * delta


class SimSelf:
    """Canonical SimSelf. Single constructor, single tick, save/load."""

    def __init__(
        self,
        constitution: Optional[Constitution] = None,
        ground: Optional[Ground] = None,
        R: float = DEFAULT_R,
        eta: float = DEFAULT_ETA,
        workdir: Optional[str] = None,
    ):
        self.constitution = constitution or Constitution()
        self.ground = ground or Ground(self.constitution.psi_0.copy())
        self.psi0 = self.ground.psi_0  # alias for legibility; never mutate
        self.dim = self.constitution.dim
        self.R = R
        self.eta = eta
        self.psi_current = self.psi0.copy()
        self.workdir = workdir
        self.decision_log: List[DecisionRecord] = []
        self.mode = "standard"
        self.ticks = 0
        self.time = 0.0

    # ------------------------------------------------------------------
    # Drift / stability
    # ------------------------------------------------------------------
    def drift(self) -> float:
        return float(np.linalg.norm(self.psi_current - self.psi0))

    # ------------------------------------------------------------------
    # observe: language packet. Returns a verdict record.
    # ------------------------------------------------------------------
    def observe(self, observation: Any) -> Dict[str, Any]:
        if isinstance(observation, str):
            obs = project_to_constitution(embed_text(observation), self.dim)
        else:
            obs = np.asarray(observation, dtype=np.float64)
            if obs.shape[0] != self.dim:
                obs = project_to_constitution(obs, self.dim)

        ok, why = _gate(obs, self.psi0)
        drift_before = self.drift()

        if ok:
            # Apply the projected gradient step.
            self.psi_current = _project_ball(
                self.psi_current - self.eta * (self.psi_current - self.psi0),
                self.psi0,
                self.R,
            )

        drift_after = self.drift()
        record = {
            "kind": "observe",
            "allow": ok,
            "reason": why,
            "drift_before": drift_before,
            "drift_after": drift_after,
        }
        self._record("observe", f"observe allow={ok} reason={why}", record)
        return record

    # ------------------------------------------------------------------
    # tick: zero-input step. Just the projected gradient step.
    # ------------------------------------------------------------------
    def tick(self, dt: float = 0.05) -> Dict[str, Any]:
        self.ticks += 1
        self.time += dt
        drift_before = self.drift()
        self.psi_current = _project_ball(
            self.psi_current - self.eta * (self.psi_current - self.psi0),
            self.psi0,
            self.R,
        )
        drift_after = self.drift()
        self._record(
            "tick",
            f"tick #{self.ticks} drift {drift_before:.4f} -> {drift_after:.4f}",
        )
        return {
            "tick": self.ticks,
            "mode": self.mode,
            "drift_before": drift_before,
            "drift_after": drift_after,
        }

    # ------------------------------------------------------------------
    # Persistence (per Batch 2 Step 3).
    # ------------------------------------------------------------------
    def committed_unit_ids(self) -> List[str]:
        return [r.data.get("unit_id") for r in self.decision_log
                if r.kind == "commit" and r.data.get("unit_id")]

    def last_verdicts(self) -> List[Dict[str, Any]]:
        return [
            {"kind": r.kind, "description": r.description, "data": r.data}
            for r in self.decision_log[-20:]
        ]

    def save(self, path: str) -> None:
        snapshot = {
            "version": 1,
            "dim": self.dim,
            "psi_0": self.psi0.tolist(),
            "psi_current": self.psi_current.tolist(),
            "committed_unit_ids": self.committed_unit_ids(),
            "last_verdicts": self.last_verdicts(),
            "mode": self.mode,
            "ticks": self.ticks,
            "time": self.time,
            "R": self.R,
            "eta": self.eta,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2)

    def load(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            snapshot = json.load(f)
        loaded_psi_0 = np.asarray(snapshot["psi_0"], dtype=np.float64)
        if not np.allclose(loaded_psi_0, self.psi0, atol=1e-9):
            raise ValueError(
                f"SimSelf.load: refusing to overwrite installed ψ₀ with snapshot's ψ₀. "
                f"||Δ||={np.linalg.norm(loaded_psi_0 - self.psi0):.3e}. "
                f"This would be a constitutional edit through fluency."
            )
        self.psi_current = np.asarray(snapshot["psi_current"], dtype=np.float64)
        self.mode = snapshot.get("mode", "standard")
        self.ticks = snapshot.get("ticks", 0)
        self.time = snapshot.get("time", 0.0)
        self.R = snapshot.get("R", self.R)
        self.eta = snapshot.get("eta", self.eta)
        # Restore the decision_log from the snapshot's last_verdicts.
        # load() is silent — no new record is appended for the load itself.
        saved_verdicts = snapshot.get("last_verdicts", [])
        self.decision_log = [
            DecisionRecord(
                timestamp=v.get("timestamp", 0.0),
                kind=v.get("kind", ""),
                description=v.get("description", ""),
                data=v.get("data", {}),
            )
            for v in saved_verdicts
        ]

    def dump(self, path: Optional[str] = None) -> str:
        if path is None:
            path = f"simself_state_{self.ticks:06d}.json"
        self.save(path)
        return path

    def zero(self) -> None:
        self.psi_current = self.psi0.copy()
        self.decision_log = []
        self.mode = "standard"
        self.ticks = 0
        self.time = 0.0

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _record(self, kind: str, description: str, data: Optional[Dict] = None):
        self.decision_log.append(DecisionRecord(time.time(), kind, description, data or {}))
        if len(self.decision_log) > 80:
            self.decision_log = self.decision_log[-60:]
