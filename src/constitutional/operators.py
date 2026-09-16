"""
operators.py — identity operators (per Grok master plan, full rewrite 2026-09-16).

This module exposes the named operations of the identity layer:

- `project_ball(ψ, ψ₀, R)` — radial projection onto B_R(ψ₀).
- `step(ψ, ψ₀, η, R)` — projected gradient step on F(ψ)=½||ψ-ψ₀||².
- `commit_radius(ψ, ψ₀)` — distance from ψ to ψ₀; commit if within.

The previous version of this file implemented a "Hodge projection" via
projected gradient step. Per Grok (segment 01, applied 2026-09-16): that is a bounded MLP,
not Hodge projection. It is removed. The kernel's projected gradient step
is the only motion allowed.
"""

from __future__ import annotations

import numpy as np


DEFAULT_R: float = 3.0
DEFAULT_ETA: float = 0.10
DEFAULT_COMMIT_RADIUS: float = 0.8


def project_ball(psi: np.ndarray, psi0: np.ndarray, R: float = DEFAULT_R) -> np.ndarray:
    delta = psi - psi0
    d = float(np.linalg.norm(delta))
    if d <= R or d == 0.0:
        return psi
    return psi0 + (R / d) * delta


def step(psi: np.ndarray, psi0: np.ndarray,
         eta: float = DEFAULT_ETA, R: float = DEFAULT_R) -> np.ndarray:
    return project_ball(psi - eta * (psi - psi0), psi0, R)


def commit_radius(psi: np.ndarray, psi0: np.ndarray) -> float:
    return float(np.linalg.norm(psi - psi0))


def is_within_commit_radius(psi: np.ndarray, psi0: np.ndarray,
                            commit_radius: float = DEFAULT_COMMIT_RADIUS) -> bool:
    return commit_radius(psi, psi0) <= commit_radius
