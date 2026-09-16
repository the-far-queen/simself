"""
consolidation_filter.py — promote admitted units to committed (per Grok).

A consolidation is the promotion of an admitted unit to committed when its
distance to ψ₀ is within the commit radius. This filter is invoked by the
canonical SimSelf.observe; it does not modify ψ₀.
"""

from __future__ import annotations

import numpy as np


DEFAULT_COMMIT_RADIUS: float = 0.8


def should_consolidate(emb: np.ndarray, psi0: np.ndarray,
                       commit_radius: float = DEFAULT_COMMIT_RADIUS) -> bool:
    return float(np.linalg.norm(emb - psi0)) <= commit_radius
