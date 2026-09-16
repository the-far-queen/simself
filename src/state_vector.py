"""
state_vector.py — ψ with the projected gradient step (per Grok master plan).

ψ is a point in ℝ^n that moves in B_R(ψ₀) under the projected gradient step.
The class below is a thin wrapper that owns ψ, exposes drift, and steps under
the kernel's tick contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


DEFAULT_R: float = 3.0
DEFAULT_ETA: float = 0.10
MAX_NORM: float = 4.0
MIN_COS: float = 0.4


def _project_ball(psi: np.ndarray, psi0: np.ndarray, R: float) -> np.ndarray:
    delta = psi - psi0
    d = float(np.linalg.norm(delta))
    if d <= R or d == 0.0:
        return psi
    return psi0 + (R / d) * delta


def gate(emb: np.ndarray, psi0: np.ndarray) -> tuple[bool, str]:
    ne = float(np.linalg.norm(emb))
    if ne > MAX_NORM:
        return False, "refuse_norm"
    n0 = float(np.linalg.norm(psi0))
    if ne == 0.0 or n0 == 0.0:
        return False, "refuse_zero"
    if float(np.dot(emb, psi0) / (ne * n0)) < MIN_COS:
        return False, "refuse_coherence"
    return True, "ok"


@dataclass
class StateVector:
    psi0: np.ndarray
    psi: np.ndarray
    R: float = DEFAULT_R
    eta: float = DEFAULT_ETA

    def drift(self) -> float:
        return float(np.linalg.norm(self.psi - self.psi0))

    def step(self) -> float:
        """One projected gradient step. Returns drift_after."""
        self.psi = _project_ball(
            self.psi - self.eta * (self.psi - self.psi0),
            self.psi0,
            self.R,
        )
        return self.drift()

    def propose(self, packet_emb: np.ndarray) -> dict:
        """Apply the gate to a candidate packet embedding.

        Returns the gate verdict; caller decides whether to step the state.
        """
        return {
            "allow": gate(packet_emb, self.psi0)[0],
            "reason": gate(packet_emb, self.psi0)[1],
            "drift_before": self.drift(),
        }
