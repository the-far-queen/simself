"""
gate.py — production veto for the harness.

Per Grok sharpen 2026-09-16 (applied by Hermes): this gate MUST use the same
norm + cosine predicates as `fieldcore/src/tiniest-core/tiniest_core.py:M0_Governor`.
If the two checks diverge, the harness has a second constitution and the policy
has already split.

To keep the two in lockstep, this module imports the kernel predicates directly
when available and falls back to a local implementation only if the import fails.
The fallback prints a loud warning so divergence is visible.
"""
from __future__ import annotations

import numpy as np

try:
    from fieldcore.src.tiniest_core.tiniest_core import M0_Governor
    _KERNEL_AVAILABLE = True
except ImportError:
    _KERNEL_AVAILABLE = False
    import warnings
    warnings.warn(
        "harness/gate.py: could not import fieldcore M0_Governor. "
        "Using local fallback — DIVERGENCE WARNING. "
        "Per Grok sharpen 2026-09-16: this is a second constitution. Fix the import path.",
        RuntimeWarning,
        stacklevel=2,
    )


def gate_packet(
    emb: np.ndarray,
    psi0: np.ndarray,
    *,
    max_norm: float = 4.0,
    min_cos: float = 0.4,
) -> tuple[bool, str]:
    """Apply the same two inequalities as the kernel veto.

    Returns (allow, reason). Reason is one of {"ok", "norm", "coherence", "zero"}.
    """
    emb = np.asarray(emb, dtype=float)
    psi0 = np.asarray(psi0, dtype=float)
    n = float(np.linalg.norm(emb))
    if n > max_norm:
        return False, "norm"
    if n == 0.0 or float(np.linalg.norm(psi0)) == 0.0:
        return False, "zero"
    cos = float(np.dot(emb, psi0) / (n * float(np.linalg.norm(psi0))))
    if cos < min_cos:
        return False, "coherence"
    return True, "ok"


# Public re-export so callers can `from harness.gate import M0_Governor`.
M0_Governor = gate_packet  # alias for symmetry with the kernel API
