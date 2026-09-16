"""
resolution.py — the projected gradient step on F (per Grok master plan, full rewrite 2026-09-16).

The previous version of this file implemented a two-layer tanh map plus a clip
and called it "Hodge projection." Per Grok (segment 01, applied 2026-09-16):
"a two-layer tanh map plus a clip is a bounded MLP, not Hodge projection."

This rewrite is the projected gradient step on F(ψ) = (1/2)||ψ-ψ₀||². That is
the resolution operator: the discrete flow that returns ψ toward ψ₀ inside
the ball B_R(ψ₀). The previous projected gradient step operator is deleted.
"""

from __future__ import annotations

import numpy as np


DEFAULT_R: float = 3.0
DEFAULT_ETA: float = 0.10


def project_ball(psi: np.ndarray, psi0: np.ndarray, R: float = DEFAULT_R) -> np.ndarray:
    delta = psi - psi0
    d = float(np.linalg.norm(delta))
    if d <= R or d == 0.0:
        return psi
    return psi0 + (R / d) * delta


def step(psi: np.ndarray, psi0: np.ndarray, eta: float = DEFAULT_ETA,
         R: float = DEFAULT_R) -> np.ndarray:
    """One projected gradient step on F(ψ) = (1/2)||ψ-ψ₀||²."""
    return project_ball(psi - eta * (psi - psi0), psi0, R)


def resolve(psi: np.ndarray, psi0: np.ndarray, n_steps: int = 1,
            eta: float = DEFAULT_ETA, R: float = DEFAULT_R) -> np.ndarray:
    """Apply n_steps of the projected gradient step. Returns the new ψ."""
    out = psi.copy()
    for _ in range(n_steps):
        out = step(out, psi0, eta=eta, R=R)
    return out
