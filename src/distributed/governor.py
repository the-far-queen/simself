"""
governor.py — Gluelgating predicates for distributed SimSelf nodes.

Extracted from Bobby's MINI-SIMSELF.txt (2026-09-08). The governor is the
"asynchronous attention" mechanism — decides whether two StalkNodes should
be allowed to glue based on shared invariants and precision compatibility.

`basic_governor`: requires (a) similar epsilon (precision match), and
(b) at least one shared invariant. Reject otherwise.

Future governors may include:
  - constitutional_governor: check shared invariants against constitutional axes
  - temporal_governor: require recent gluing history match
  - m0_m1_governor: route through kernel gate (per simself/src/harness/gate.py)
"""
from __future__ import annotations

from typing import Set


def basic_governor(s1, s2, epsilon_tolerance: float = 0.1) -> bool:
    """Bobby's basic governor from MINI-SIMSELF.

    Args:
        s1, s2: StalkNode instances (duck-typed; we only access .epsilon and .invariants).
        epsilon_tolerance: max |Δε| allowed.

    Returns True iff:
        - |s1.epsilon - s2.epsilon| ≤ epsilon_tolerance (precision match)
        - len(set(s1.invariants) & set(s2.invariants)) > 0 (shared invariants)
    """
    if abs(s1.epsilon - s2.epsilon) > epsilon_tolerance:
        return False
    s1_invs: Set = set(s1.invariants)
    s2_invs: Set = set(s2.invariants)
    return len(s1_invs & s2_invs) > 0


# Common invariants (placeholder). Use these with StalkNode.

def norm_invariant(emb, threshold: float = 10.0) -> bool:
    """Embeddings with norm below threshold are valid."""
    import numpy as np
    return float(np.linalg.norm(emb)) < threshold


def energy_invariant(emb, threshold: float = 50.0) -> bool:
    """Embeddings with sum-of-squares below threshold are valid."""
    import numpy as np
    return float(np.sum(emb ** 2)) < threshold


def balance_invariant(emb, threshold: float = 0.5) -> bool:
    """Centroid within bounds — for robot embodiment use case."""
    import numpy as np
    if len(emb) == 0:
        return True
    return abs(float(np.mean(emb))) < threshold


__all__ = ["basic_governor", "norm_invariant", "energy_invariant", "balance_invariant"]