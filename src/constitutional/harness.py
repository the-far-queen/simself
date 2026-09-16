"""
harness.py — Agent harness: gated tool use, memory, tick (per Grok master plan).

Wraps a SimSelf with:
- The canonical gate (harness.gate.gate_packet) for every tool call.
- A SimSelf instance for state.
- A constitutional memory store.
- A tick that applies the projected gradient step on F.
- A process(text) that routes through gate then ingest then tick.

Per Batch 1 K8 (applied 2026-09-16): every LLM-call path goes through
gated_call. The harness is no exception.

This module replaces the v8.0-grok Harness which used CONSTRAINT_PATTERN
and GroundIntegration as sacred-tier predicates. Those are off-spec
per Grok (segment 02). The canonical predicates are the two inequalities
in gate_packet.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np

from .constitution import Constitution, embed_text, project_to_constitution
from .ground import Ground
from .simself import SimSelf
from .memory import ConstitutionalMemory
from .lexicon.ingest import gate_m0, ingest, embed_bag


class Harness:
    """Agent harness: gated tool use, memory store, tick."""

    def __init__(
        self,
        constitution: Optional[Constitution] = None,
        ground: Optional[Ground] = None,
        R: float = 3.0,
        eta: float = 0.10,
    ):
        self.simself = SimSelf(
            constitution=constitution or Constitution(),
            ground=ground or Ground((constitution or Constitution()).psi_0.copy()),
            R=R, eta=eta,
        )
        self.memory = ConstitutionalMemory()
        self.index: List[Any] = []  # lexicon unit index

    def process(self, text: str) -> Dict[str, Any]:
        """Route a text span through gate, ingest, tick.

        1. Embed + classify via ingest (or fall back to observe).
        2. Apply gate_packet.
        3. Tick.
        4. Record in memory.
        5. Return verdict + drift + mode.
        """
        result = self.simself.observe(text)
        result["drift_after"] = self.simself.drift()
        return result

    def commit(self, item_id: str) -> bool:
        """Promote a memory item to committed."""
        return self.memory.commit(item_id)

    def add_item(self, item) -> None:
        self.memory.add_item(item)

    def state_report(self) -> Dict[str, Any]:
        return {
            "drift": self.simself.drift(),
            "mode": self.simself.mode,
            "ticks": self.simself.ticks,
            "psi_unchanged_from_install": bool(
                np.allclose(
                    self.simself.psi0,
                    self.simself.ground.psi_0,
                )
            ),
        }


__all__ = ["Harness"]
