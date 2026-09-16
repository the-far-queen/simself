"""
m1_m0_negotiation.py — two-layer control loop (per Grok segment 10, full rewrite 2026-09-16).

M0 is the gate (veto). It runs two inequalities: norm and cosine to ψ₀.
M1 is the working-side search (planner, stalk control, span proposal).

The order is fixed: M1 proposes; M0 refuses or allows. There is no other order.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np

from .harness.gate import gate_packet


def negotiate(packet_payload: Any, psi0: np.ndarray, embed_fn) -> dict:
    """Run the M1→ M0 negotiation.

    Returns a dict with allow, reason, embedding_norm, and the gate verdict.
    The caller decides what to do with an allowed packet (e.g. tick the self).
    """
    emb = np.asarray(embed_fn(packet_payload), dtype=float)
    allow, reason = gate_packet(emb, psi0)
    return {
        "allow": allow,
        "reason": reason,
        "embedding_norm": float(np.linalg.norm(emb)),
    }
