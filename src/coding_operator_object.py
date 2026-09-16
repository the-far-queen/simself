"""
coding_operator_object.py — model-as-engine, gated (per Grok master plan Step 5).

The model sits outside the diagram. It emits candidate spans. Ingest and the
gate decide whether those spans become units or acts. A wrapper intercepts both
directions: spans leave only as typed packets; replies return only as spans
offered to ingest.

Per Batch 1 K8: any path the model uses to act must go through
harness/gate.py:gated_call. If gated_call is unavailable, this module raises
on construction rather than silently bypassing the gate.
"""

from __future__ import annotations

import os
from typing import Any, Optional

import numpy as np

try:
    from .harness.gate import gated_call
    _GATE_AVAILABLE = True
except ImportError as e:
    _GATE_AVAILABLE = False
    _GATE_ERROR = str(e)


class CodingOperatorObject:
    """The model's I/O surface. Gated by the harness."""

    def __init__(self, embed_fn=None, psi0: Optional[np.ndarray] = None):
        if not _GATE_AVAILABLE:
            raise RuntimeError(
                "coding_operator_object: harness.gate.gated_call not importable. "
                "Per Grok master plan Step 5: every model path must be gated. "
                f"Underlying error: {_GATE_ERROR}"
            )
        if embed_fn is None:
            from .constitutional.lexicon.ingest import embed_bag
            embed_fn = embed_bag
        if psi0 is None:
            from .constitutional.ground import Ground
            from .constitutional.constitution import Constitution
            psi0 = Ground(Constitution().psi_0.copy()).psi_0
        self.embed = embed_fn
        self.psi0 = psi0
        self.history = []

    def propose_span(self, span: str) -> dict:
        """Send a candidate span through the gate.

        Returns a verdict dict. The span does NOT become a unit until ingest
        commits it. This is the M1→ M0 hand-off.
        """
        verdict = gated_call(span, self.psi0, self.embed)
        verdict["span"] = span
        self.history.append(verdict)
        return verdict

    def is_allowed(self, span: str) -> bool:
        verdict = self.propose_span(span)
        return bool(verdict.get("allow"))

    def refuse_log(self) -> list:
        """Return the spans that were refused by the gate."""
        return [v for v in self.history if not v.get("allow")]
