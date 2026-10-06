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
from .dreaming import ConstitutionalDreaming
from .handoff import HandoffProtocol
from .void import VoidIntegration


class Harness:
    """Agent harness: gated tool use, memory store, tick.

    The dreamer is wired in here (2026-10-06). It was not: the module
    existed, imported cleanly, passed its own tests, and nothing in the
    repository ever constructed it. `process()` also claimed in its
    docstring to "record in memory" and never called `add_item`.

    Both are the same defect — a component documented as part of the
    system with no operating mode that reaches it. `tests/test_wiring.py`
    now fails if any core module loses its last caller.
    """

    #: dream on every Nth process() call. 0 disables.
    DREAM_EVERY: int = 8

    #: commit the oldest uncommitted observation every Nth call. Kept
    #: smaller than DREAM_EVERY so a dream always has at least
    #: min_sources committed memories to recombine from; otherwise it
    #: refuses correctly and forever.
    COMMIT_AFTER: int = 2

    #: dt for the zero-input maintenance step that follows each observe.
    TICK_DT: float = 0.05

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
        self.memory = ConstitutionalMemory(dim=self.simself.dim)
        self.index: List[Any] = []  # lexicon unit index
        self.dreamer = ConstitutionalDreaming(self.simself.ground,
                                              self.simself.dim,
                                              memory=self.memory)
        # handoff + void wired in 2026-10-06. Both had been advertised in
        # this repo's docs since August and neither existed as code.
        self.handoff = HandoffProtocol(self.simself)
        self.void = VoidIntegration(self.simself.dim)
        self._calls = 0

    def process(self, text: str) -> Dict[str, Any]:
        """Route a text span through gate, ingest, tick.

        1. Embed + classify via ingest (or fall back to observe).
        2. Apply gate_packet.
        3. Tick.
        4. Record in memory.
        5. Return verdict + drift + mode.

        Observations are committed once they are no longer the newest
        thing. Committing is what makes an item count as prior art for
        `novelty()`; without it the dreamer refuses forever with
        `insufficient_memory` and never runs. That was found by running
        the loop, not by reading it.
        """
        result = self.simself.observe(text)
        # the zero-input maintenance step. observe() only moves psi on
        # input; without a tick the system accumulates observations and
        # never integrates them, and readiness stays at no_ticks forever.
        tick = self.simself.tick(dt=self.TICK_DT)
        result["tick"] = tick["tick"]
        result["drift_after"] = tick["drift_after"]

        # step 4, actually: record what was observed. The docstring
        # claimed this and no line did it.
        item_id = self.memory.add(text, self.simself.psi_current,
                                  category="observation")
        result["memory_id"] = item_id
        self._calls += 1

        if self._calls % self.COMMIT_AFTER == 0:
            result["committed"] = self._commit_oldest()

        # idle dreaming. maintenance work, gated like anything else.
        if self.DREAM_EVERY and self._calls % self.DREAM_EVERY == 0:
            result["dream"] = self.dreamer.dream()
        return result

    def _commit_oldest(self):
        """Commit the oldest uncommitted observation. Returns its id."""
        pending = [i for i, it in self.memory.items.items()
                   if not it.committed]
        if not pending:
            return None
        oldest = min(pending,
                     key=lambda i: self.memory.items[i].timestamp)
        self.memory.commit(oldest)
        return oldest

    def dream(self) -> Dict[str, Any]:
        """Run a dream on demand. Never modifies ψ₀."""
        return self.dreamer.dream()

    def commit(self, item_id: str) -> bool:
        """Promote a memory item to committed.

        Committed items are what `novelty()` measures against, so an
        uncommitted observation never suppresses a future dream.
        """
        return self.memory.commit(item_id)

    def add_item(self, item) -> None:
        self.memory.add_item(item)

    def state_report(self) -> Dict[str, Any]:
        return {
            "ready_for_handoff": self.handoff.readiness().ready,
            "void_distance": self.void.distance_to_void(
                self.simself.psi_current),
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
