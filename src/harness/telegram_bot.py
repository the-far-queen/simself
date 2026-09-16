"""
telegram_bot.py — Telegram gateway, gated (per Grok master plan Step 5).

Per Batch 1 K8 + master plan Step 5: any path the model uses to act must go
through harness/gate.py:gated_call. This module wraps the Telegram message
surface so every incoming text is gated before it becomes a span.

The bot emits to the LLM only allowed spans (via gate.allow == True). Refused
spans produce a deny record but no LLM call.
"""

from __future__ import annotations

import logging
from typing import Optional

try:
    from .gate import gated_call
    _GATE_AVAILABLE = True
except ImportError:
    _GATE_AVAILABLE = False

log = logging.getLogger(__name__)


def gate_inbound(span: str, psi0, embed_fn) -> dict:
    """Gated wrapper for an inbound Telegram message.

    Returns the gated_call verdict. The caller decides whether to forward the
    span to the LLM.
    """
    if not _GATE_AVAILABLE:
        return {
            "allow": False,
            "reason": "gate_unavailable",
            "span": span,
            "embedding_norm": 0.0,
            "error": "harness.gate.gated_call not importable; refusing by default",
        }
    return gated_call(span, psi0, embed_fn)


def emit_verdict(verdict: dict) -> str:
    """Format a verdict as a user-visible Telegram message."""
    if verdict.get("allow"):
        return f"OK ({verdict.get('reason','ok')})"
    return f"REFUSED ({verdict.get('reason','?')})"
