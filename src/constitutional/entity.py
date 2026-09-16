"""
entity.py — LEGACY 20-axis entity recognition (per Grok master plan).

Per Grok (segment 02, applied 2026-09-16): "20 axes from Clifford +
octonions + Hodge dual + triple product" is dimension arithmetic, not a
theorem. The canonical axis set is now 8 default axes in
constitution.py:Constitution. The legacy 20-axis entity recognition is
preserved as a stub for historical diff.

If you want a working entity recognition, use the canonical harness
(simself/src/harness/) with the canonical constitution. This file is
preserved verbatim from the 2026-09-08 v8.0-grok SimSelf and is
intentionally not wired to the new gate.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

import numpy as np


class EntityRecognition:
    """LEGACY 20-axis entity recognition stub.

    Not wired to the canonical gate. Use simself/src/harness/ for the
    current API.
    """

    def __init__(self, constitution=None):
        self.constitution = constitution

    def recognize(self, observation: Any, is_text: bool = False) -> Dict[str, Any]:
        """Returns a placeholder dict. Real implementation moved to harness."""
        if is_text and isinstance(observation, str):
            return {"kind": "text", "is_entity": False, "score": 0.0, "note": "legacy"}
        return {"kind": "vector", "is_entity": False, "score": 0.0, "note": "legacy"}
