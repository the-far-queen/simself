"""
gate.py — production veto for the harness (per Grok master plan, normalized 2026-09-16).

This gate uses the SAME two inequalities as fieldcore/src/tiniest-core/tiniest_core.py:
M0_Governor. Per Batch 1 K8 + Grok segment 02: identical thresholds, identical
reasons, no divergence.

Public API:
- gate_packet(emb, psi0, *, max_norm, min_cos) -> (allow, reason)
- M0_Governor alias for symmetry with the kernel
- gated_call(packet_payload, psi0, embed_fn) -> verdict dict
"""

from __future__ import annotations

import numpy as np

# Defaults that match the kernel.
MAX_NORM: float = 4.0
MIN_COS: float = 0.4


def gate_packet(
    emb: np.ndarray,
    psi0: np.ndarray,
    *,
    max_norm: float = MAX_NORM,
    min_cos: float = MIN_COS,
) -> tuple[bool, str]:
    """Apply both inequalities. Returns (allow, reason).

    AND THE FINITENESS CHECK, WHICH IS THE FOURTH INEQUALITY AND WAS
    MISSING HERE. MEASURED 2026-11-04: a NaN payload was ADMITTED by
    this gate, because `nan > 4.0` is False and `nan < 0.4` is False.

    The canonical gate in `fieldcore/src/gate.py` has carried this check
    since it was written, and so has the out-of-process governor. This
    copy did not, so the same packet was refused by one core and
    admitted by another. The shape of that attack is not "beat the
    gate" -- it is "find the copy of the gate that does not have the
    check".

    The reason string matches the canonical gate's: `refuse_nonfinite`.
    """
    if not (_is_finite(emb) and _is_finite(psi0)):
        return False, "refuse_nonfinite"
    ne = float(np.linalg.norm(emb))
    if ne > max_norm:
        return False, "refuse_norm"
    n0 = float(np.linalg.norm(psi0))
    if ne == 0.0 or n0 == 0.0:
        return False, "refuse_zero"
    if float(np.dot(emb, psi0) / (ne * n0)) < min_cos:
        return False, "refuse_coherence"
    return True, "ok"


def _is_finite(arr: np.ndarray) -> bool:
    """A NaN or an infinity is refused, never admitted.

    MEASURED: `float('nan') > 4.0` is False, so a gate that tests only
    `ne > max_norm` returns ALLOW for a vector of NaN.

    An exception is not a verdict, so this returns False rather than
    raising on a non-numeric input.
    """
    try:
        return bool(np.all(np.isfinite(np.asarray(arr, dtype=float))))
    except (TypeError, ValueError):
        return False


# Public re-export so callers can `from harness.gate import M0_Governor`.
M0_Governor = gate_packet  # alias for symmetry with the kernel API


def gated_call(
    packet_payload,
    psi0: np.ndarray,
    embed_fn,
    *,
    max_norm: float = MAX_NORM,
    min_cos: float = MIN_COS,
) -> dict:
    """Single entry point for any LLM-call path (per master plan Step 5).

    Embeds the payload, applies the same two inequalities as M0_Governor, and
    returns either an allow verdict or a deny record.
    """
    emb = np.asarray(embed_fn(packet_payload), dtype=float)
    allow, reason = gate_packet(emb, psi0, max_norm=max_norm, min_cos=min_cos)
    return {
        "allow": allow,
        "reason": reason,
        "embedding_norm": float(np.linalg.norm(emb)),
    }
