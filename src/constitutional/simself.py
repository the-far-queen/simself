"""
simself.py — The SimSelf integrator. The core constitutional feedback loop.

Extracted from the v8.0-grok `SimSelf` class. The integrator exposes:
- `observe(text_or_vector)`: project the input to the constitutional manifold,
  compute harmonic + axial readings, run the resolution operator, update
  axis values by relevance, return a summary dict.
- `tick(dt)`: one simulation step. Pulls psi_current toward psi_0, evaluates
  the mode (standard / recognition / exploratory), triggers a dream on
  periodic ticks if the mode permits, applies salience decay to memory.
- `mode` state machine: standard -> recognition (when stable + memories) ->
  exploratory (when stable + memories + dreams).
- `why(n)`: returns the last n decision records.
- `axis_report()`: snapshot of the 20 axes.
- `gate_refusal(context_strength)`: returns whether the SimSelf can say no,
  based on the boundaries and authenticity axes.
- `reset()`: clear all state and return to psi_0.
- `drift()`: ||psi_current - psi_0||.
- `get_stability()`: 0.65 * mean_confidence + 0.35 * (1 - drift).

What is NOT here (intentionally):
- No frequency / standing-wave / Schumann / 432 / 963 / pineal / crown
  references. The frequency module is `frequency.py` and is isolated.
- No FFT-based "holographic" memory. See `memory.py`.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from .constitution import Constitution, ConstitutionalAxis, embed_text, project_to_constitution
from .resolution import ResolutionOperator
from .entity import EntityRecognition
from .memory import RelationalMemory
from .dreaming import ConstitutionalDreaming


@dataclass
class DecisionRecord:
    timestamp: float
    kind: str
    description: str
    data: Dict[str, Any] = field(default_factory=dict)


class SimSelf:
    """The constitutional feedback loop. Manages psi_current relative to psi_0."""

    def __init__(self, constitution: Optional[Constitution] = None, use_torch: bool = True):
        self.constitution = constitution or Constitution()
        self.dim = self.constitution.dim
        self.curvature = self.constitution.curvature_vector()
        self.psi_current = self.constitution.psi_0.copy()
        self.resolution = ResolutionOperator(self.dim, use_torch=use_torch)
        self.axes: Dict[str, ConstitutionalAxis] = {
            name: ConstitutionalAxis(name=name, sheave=sheave)
            for name, sheave in self.constitution.axes_def
        }
        self.entity_recognizer = EntityRecognition(self.constitution)
        self.memory = RelationalMemory()
        self.dreaming = ConstitutionalDreaming(
            self.memory, list(self.axes.keys()), self.dim
        )
        self.decision_log: List[DecisionRecord] = []
        self.mode = "standard"
        self.ticks = 0
        self.time = 0.0
        self.total_updates = 0

    def _record(self, kind: str, description: str, data: Optional[Dict] = None):
        self.decision_log.append(DecisionRecord(time.time(), kind, description, data or {}))
        if len(self.decision_log) > 80:
            self.decision_log = self.decision_log[-60:]

    def why(self, n: int = 5) -> List[str]:
        return [f"[{r.kind}] {r.description}" for r in reversed(self.decision_log[-n:])]

    def observe(self, observation: Any, context: Optional[Dict] = None,
                valence: float = 0.0, eta: float = 0.06) -> Dict[str, Any]:
        if isinstance(observation, str):
            obs = project_to_constitution(embed_text(observation))
            entity = self.entity_recognizer.recognize(observation, is_text=True)
        else:
            obs = np.asarray(observation, dtype=np.float64)
            if obs.shape[0] != self.dim:
                obs = np.resize(obs, self.dim)
            n = np.linalg.norm(obs)
            obs = obs / n if n > 1e-9 else obs
            entity = self.entity_recognizer.recognize(obs, is_text=False)

        harm = float(np.dot(obs, self.constitution.psi_0))
        axial = float(np.dot(obs, self.curvature))

        delta = self.psi_current - self.constitution.psi_0
        correction = self.resolution(delta + 0.12 * obs)
        pulled = self.psi_current - eta * delta + eta * correction
        n = np.linalg.norm(pulled)
        self.psi_current = pulled / n if n > 1e-9 else pulled

        for axis in self.axes.values():
            if not axis.mutable:
                continue
            sim = self.constitution.consonance(obs, axis.name)
            relevance = max(0.0, sim - 0.35)
            if relevance > 0.0:
                axis.value = 0.82 * axis.value + 0.18 * float(np.dot(obs, self.psi_current))
                axis.confidence = min(0.97, axis.confidence + 0.08 * relevance)
            else:
                axis.confidence = 0.97 * axis.confidence + 0.03 * 0.55

        self.total_updates += 1
        return {
            "harm": harm,
            "axial": axial,
            "entity": entity,
            "stability": self.get_stability(),
        }

    def drift(self) -> float:
        return float(np.linalg.norm(self.psi_current - self.constitution.psi_0))

    def get_stability(self) -> float:
        confs = [ax.confidence for ax in self.axes.values()]
        mean_conf = float(np.mean(confs)) if confs else 0.5
        return float(max(0.35, min(1.0, 0.65 * mean_conf + 0.35 * (1.0 - min(self.drift(), 1.0)))))

    def gate_refusal(self, context_strength: float = 0.0) -> bool:
        """Returns True iff the SimSelf can refuse, based on boundaries + authenticity axes."""
        b = self.axes.get("boundaries", ConstitutionalAxis("boundaries")).value
        a = self.axes.get("authenticity", ConstitutionalAxis("authenticity")).value
        return (b > 0.25 and a > 0.28) or context_strength < 0.4

    def _evaluate_mode(self):
        stab = self.get_stability()
        mem_count = len(self.memory.entries)
        dream_count = len(self.dreaming.dream_log)
        old = self.mode
        if stab >= 0.82 and mem_count >= 10 and dream_count >= 2:
            new = "exploratory"
        elif stab >= 0.70 and mem_count >= 5:
            new = "recognition"
        else:
            new = "standard"
        if new != old:
            self.mode = new
            self._record("mode_shift", f"Mode {old} -> {new} (stab={stab:.3f})")

    def tick(self, dt: float = 0.05) -> Dict[str, Any]:
        self.ticks += 1
        self.time += dt
        actions = []

        # constitutional ground pull
        delta = self.psi_current - self.constitution.psi_0
        self.psi_current -= 0.04 * delta
        n = np.linalg.norm(self.psi_current)
        self.psi_current = self.psi_current / (n + 1e-9)
        actions.append("resonance")

        old_mode = self.mode
        self._evaluate_mode()
        if self.mode != old_mode:
            actions.append(f"mode->{self.mode}")

        dreamed = False
        if self.ticks % 3 == 0 and self.mode in ("recognition", "exploratory"):
            d = self.dreaming.dream(intensity=0.4 if self.mode == "recognition" else 0.6)
            if d.get("kept"):
                actions.append("dream")
                dreamed = True

        if self.ticks % 5 == 0:
            self.memory.decay_salience()
            actions.append("decay")

        return {
            "tick": self.ticks,
            "mode": self.mode,
            "stability": round(self.get_stability(), 4),
            "actions": actions,
            "dreamed": dreamed,
        }

    def reset(self):
        self.psi_current = self.constitution.psi_0.copy()
        self.memory.clear()
        self.decision_log = []
        self.dreaming.dream_log = []
        self.mode = "standard"
        self.ticks = 0
        self.time = 0.0
        for ax in self.axes.values():
            ax.value = 0.0
            ax.confidence = 0.55

    def axis_report(self) -> Dict[str, Dict[str, float]]:
        return {
            name: {"value": round(ax.value, 4), "confidence": round(ax.confidence, 4), "sheave": ax.sheave}
            for name, ax in self.axes.items()
        }
