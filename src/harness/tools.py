"""
tools.py — tool registry, gated (per Grok master plan Step 5).

Per Batch 1 K8: every tool invocation goes through harness/gate.py. If the
gate refuses, the tool is not called. This module is the tool surface; it does
not own the gate.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

try:
    from .gate import gated_call
    _GATE_AVAILABLE = True
except ImportError:
    _GATE_AVAILABLE = False


class ToolRegistry:
    """A small registry of tool callables, gated."""

    def __init__(self):
        self._tools: Dict[str, Callable] = {}

    def register(self, name: str, fn: Callable):
        self._tools[name] = fn

    def call(self, name: str, payload: Any, psi0, embed_fn) -> dict:
        """Invoke a tool, but only if the gate allows."""
        if not _GATE_AVAILABLE:
            return {"allow": False, "reason": "gate_unavailable", "tool": name}
        verdict = gated_call(payload, psi0, embed_fn)
        if not verdict.get("allow"):
            return {**verdict, "tool": name, "ran": False}
        if name not in self._tools:
            return {"allow": False, "reason": "no_such_tool", "tool": name, "ran": False}
        try:
            result = self._tools[name](payload)
            return {**verdict, "tool": name, "ran": True, "result": result}
        except Exception as e:
            return {"allow": False, "reason": "tool_exception", "tool": name,
                    "ran": False, "error": str(e)}
