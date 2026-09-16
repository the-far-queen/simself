"""
telegram_text_bot.py — text-only Telegram gateway, gated (per Grok master plan Step 5).

Same gate contract as telegram_bot.py. This is the text-only variant; the
multimodal bot handles voice and attachments in a sibling module.
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


def gate_text(span: str, psi0, embed_fn) -> dict:
    """Gated wrapper for text-only inbound messages."""
    if not _GATE_AVAILABLE:
        return {
            "allow": False,
            "reason": "gate_unavailable",
            "span": span,
            "embedding_norm": 0.0,
        }
    return gated_call(span, psi0, embed_fn)
