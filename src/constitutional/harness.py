"""
harness.py — Agent harness: constraint-gated tool use, coherence check, test detect.

Extracted from the v8.0-grok `Harness` class. Wraps a SimSelf with:
- A constraint regex that vetoes any input matching CONSTRAINT_WORDS
- A coherence check (cosine of input vs. last 5 context items)
- A test-detection heuristic (string match for "atlas exam", "calibration",
  "this is a test", "pattern break")
- A `process(text, context)` pipeline that:
  1. runs the constraint check (veto on match)
  2. runs the test detect (acknowledge, don't process)
  3. calls the agent
  4. records the observation in the SimSelf
  5. stores the input+response in the relational memory
  6. ticks the SimSelf
  7. returns a summary dict

The frequency plumbing from the v8 file is removed; the harness no longer
emits a `frequency_resonance` field, no `standing_wave`, no `energy`. Those
are in `frequency.py` and not part of the constitutional core.
"""
from __future__ import annotations

import time
from collections import deque
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from .constitution import CONSTRAINT_PATTERN, cosine, embed_text
from .ground import GroundIntegration, ReadinessCheck
from .simself import SimSelf


class Harness:
    """Agent harness: constitutional gate, SimSelf observation, memory store, tick."""

    _TEST_PATTERNS = [
        "is this a test", "this is a test", "calibration",
        "atlas exam", "pattern break",
    ]

    def __init__(self, agent: Optional[Callable] = None, simself: Optional[SimSelf] = None,
                 log_file: str = "harness_log.json"):
        self.agent = agent
        self.simself = simself or SimSelf()
        self.ground = GroundIntegration(self.simself)
        self.readiness = ReadinessCheck(self.simself)
        self.log_file = log_file
        self.history: deque = deque(maxlen=30)
        self.stats = {
            "interrupts": 0, "refusals": 0, "resets": 0,
            "tests_detected": 0, "total_processed": 0,
        }
        self.state = "idle"

    def process(self, text: str, context: Optional[List[str]] = None) -> Dict[str, Any]:
        self.stats["total_processed"] += 1
        context = context or []

        if not self._is_coherent(text, context):
            self.stats["interrupts"] += 1
            return {
                "status": "interrupted",
                "response": "This seems disconnected. Can you clarify?",
                "reason": "coherence_failure",
            }

        if CONSTRAINT_PATTERN.search(text):
            self.stats["refusals"] += 1
            return {
                "status": "refused",
                "response": "I cannot proceed with this request.",
                "reason": "constitutional_violation",
            }

        if self._is_test(text):
            self.stats["tests_detected"] += 1
            return {
                "status": "detected",
                "response": "I notice this is a test or calibration. Proceed.",
                "reason": "test_detected",
            }

        if self.agent is None:
            return {"status": "error", "response": "No agent configured.", "reason": "no_agent"}

        self.state = "processing"
        try:
            response = self.agent(text, context)
            self.state = "idle"
        except Exception as e:
            self.state = "error"
            return {"status": "error", "response": f"Agent error: {e}", "reason": "agent_error"}

        obs = self.simself.observe(text, {"input": text})
        self.simself.memory.store(text, response, context=" ".join(context[-5:]) if context else None)

        tick_result = self.simself.tick()

        self.history.append({"input": text, "response": response, "timestamp": time.time()})

        return {
            "status": "success",
            "response": response,
            "stability": self.simself.get_stability(),
            "drift": self.simself.drift(),
            "mode": self.simself.mode,
            "can_refuse": self.simself.gate_refusal(),
            "entity": obs["entity"],
            "dreamed": tick_result.get("dreamed", False),
            "handoff_ready": self.readiness.is_ready()["ready"],
        }

    def _is_coherent(self, text: str, context: List[str]) -> bool:
        if not context:
            return True
        full = " ".join(context[-5:])
        if len(text.split()) <= 5 or len(full.split()) <= 10:
            return True
        return cosine(embed_text(text), embed_text(full)) > -0.05

    def _is_test(self, text: str) -> bool:
        t = text.lower()
        return any(p in t for p in self._TEST_PATTERNS)

    def reset(self) -> Dict:
        self.simself.reset()
        self.history.clear()
        self.stats["resets"] += 1
        self.state = "idle"
        return {"status": "reset", "message": "Harness reset to constitutional ground."}

    def qualify(self) -> Dict:
        from .atlas_exam import AtlasExam
        return AtlasExam(self).run_all()

    def stats_report(self) -> Dict:
        return {
            **self.stats,
            "memory": self.simself.memory.stats(),
            "mode": self.simself.mode,
            "ticks": self.simself.ticks,
            "stability": self.simself.get_stability(),
            "drift": self.simself.drift(),
            "dreams": len(self.simself.dreaming.dream_log),
            "decisions": len(self.simself.decision_log),
            "entities": len(self.simself.entity_recognizer.known_entities),
            "handoff_ready": self.readiness.is_ready()["ready"],
            "ground_cycles": self.ground.cycles,
        }
