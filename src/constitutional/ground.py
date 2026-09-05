"""
ground.py — Ground integration and readiness check.

Renamed from `VoidIntegration` and `HandoffProtocol` in the v8.0-grok file.
The original names are consciousness-flavored. The code is just math:
- `GroundIntegration` is a leaky integrator that pulls psi_current back
  toward psi_0 (a controlled relaxation).
- `ReadinessCheck` is a precondition test (stability > 0.65 and drift < 0.22)
  that decides whether psi_current is close enough to ground to "hand off."

The math is real. The names now describe what the math does.
"""
from __future__ import annotations

from typing import Any, Dict

import numpy as np

from .simself import SimSelf  # for type hint only; runtime uses duck typing


class GroundIntegration:
    """Pull psi_current toward psi_0 via a leaky integrator.

    The relaxation rate (default 0.08) is a free parameter. The result is
    a controlled ground pull that does not snap psi_current to psi_0 in
    one step.
    """

    def __init__(self, simself: "SimSelf", relaxation_rate: float = 0.08):
        self.simself = simself
        self.relaxation_rate = relaxation_rate
        self.cycles = 0

    def integrate(self) -> Dict[str, Any]:
        before = self.simself.drift()
        self.simself.psi_current = (
            (1.0 - self.relaxation_rate) * self.simself.psi_current
            + self.relaxation_rate * self.simself.constitution.psi_0
        )
        n = np.linalg.norm(self.simself.psi_current)
        self.simself.psi_current = self.simself.psi_current / n if n > 1e-9 else self.simself.psi_current
        after = self.simself.drift()
        self.cycles += 1
        return {"cycles": self.cycles, "drift_before": before, "drift_after": after}


class ReadinessCheck:
    """Check whether psi_current is close enough to ground for a clean transition.

    Default gates: stability > 0.65 AND drift < 0.22.
    """

    def __init__(self, simself: "SimSelf",
                 stability_threshold: float = 0.65,
                 drift_threshold: float = 0.22):
        self.simself = simself
        self.stability_threshold = stability_threshold
        self.drift_threshold = drift_threshold
        self.acknowledged = False
        self.complete = False

    def is_ready(self) -> Dict[str, Any]:
        stability = self.simself.get_stability()
        drift = self.simself.drift()
        ready = stability > self.stability_threshold and drift < self.drift_threshold
        return {"ready": ready, "stability": stability, "drift": drift}

    def acknowledge(self) -> Dict[str, Any]:
        readiness = self.is_ready()
        if not readiness["ready"]:
            return {"status": "not_ready", "readiness": readiness}
        if self.acknowledged:
            return {"status": "already_acknowledged"}
        self.acknowledged = True
        return {
            "status": "acknowledged",
            "message": "System recognizes itself as ground.",
            "readiness": readiness,
        }
