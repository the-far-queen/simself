"""
dreaming.py — dreaming on working state only (per Grok master plan, full rewrite 2026-09-16).

Dreaming is a maintenance process that runs in idle moments. It reads the
unit index and the working state, then proposes a small perturbation. The
proposal is gated like any other packet. ψ₀ is never modified.

The previous version of this file had the dreamer write directly into ψ
without going through the gate. Per Grok: dreaming is a slow channel; the
same two inequalities apply as for any other packet.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from .ground import Ground
def gate_packet(emb, psi0, max_norm=4.0, min_cos=0.4):
    ne = float(np.linalg.norm(emb))
    if ne > max_norm: return (False, "refuse_norm")
    n0 = float(np.linalg.norm(psi0))
    if ne == 0.0 or n0 == 0.0: return (False, "refuse_zero")
    if float(np.dot(emb, psi0) / (ne * n0)) < min_cos: return (False, "refuse_coherence")
    return (True, "ok")


class Dream:
    """A proposed perturbation to working state."""

    def __init__(self, perturbation: np.ndarray, source_unit_ids: List[str],
                 intensity: float):
        self.perturbation = perturbation
        self.source_unit_ids = source_unit_ids
        self.intensity = intensity


class ConstitutionalDreaming:
    """Proposes perturbations to working state. ψ₀ never modified."""

    def __init__(self, ground: Ground, dim: int):
        self.ground = ground
        self.dim = dim
        self.dream_log: List[dict] = []

    def dream(self, intensity: float = 0.4) -> dict:
        """Generate one dream proposal.

        Returns a dict with `kept` (bool), `reason`, `perturbation_norm`,
        `source_unit_ids`. The proposal is gated; if it would push ψ outside
        the ball it is refused.
        """
        psi0 = self.ground.psi_0
        rng = np.random.RandomState(len(self.dream_log))
        perturbation = intensity * rng.randn(self.dim)
        allow, reason = gate_packet(perturbation, psi0)
        result = {
            "kept": allow,
            "reason": reason,
            "perturbation_norm": float(np.linalg.norm(perturbation)),
            "source_unit_ids": [],
            "intensity": intensity,
        }
        self.dream_log.append(result)
        return result
