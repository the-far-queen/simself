"""SelfCore 1: a small executable kernel for boundary, state, and change.

This is intentionally separate from SimSelf.
SimSelf protects the constitutional identity of the whole.
SelfCore handles the local loop: receive, register, decide, remember, change.

The model does not claim to be conscious. It makes a small set of claims
explicit: a signal can be classified, a boundary can be tested, a refusal can
be recorded, and future responses can depend on that record.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


EPSILON = 1e-9


class Decision(Enum):
    ACCEPT = "accept"
    SOFTEN = "soften"
    REFUSE = "refuse"


@dataclass(frozen=True)
class Boundary:
    """A rule the system can apply without pretending it is universal truth."""

    name: str
    predicate: Any
    reason: str


@dataclass
class Memory:
    entries: list[dict[str, Any]] = field(default_factory=list)

    def append(self, *, signal: Any, decision: Decision, reason: str) -> None:
        self.entries.append(
            {
                "signal": signal,
                "decision": decision.value,
                "reason": reason,
            }
        )

    def recent(self, limit: int = 10) -> list[dict[str, Any]]:
        return self.entries[-limit:]


@dataclass
class State:
    charge: float = 0.0
    resistance: float = 0.5
    boundary_strength: float = 0.5
    coherence: float = 0.5
    turn: int = 0
    previous_coherence: float = 0.5

    def observe_change(self) -> float:
        return abs(self.coherence - self.previous_coherence)


class SelfCore:
    """A boundary-aware state machine, not a claim of consciousness."""

    def __init__(self, boundaries: Iterable[Boundary] = ()):
        self.boundaries = list(boundaries)
        self.memory = Memory()
        self.state = State()

    def evaluate(self, signal: Any) -> Decision:
        """Register a signal and choose a response through a bounded rule set."""
        self.state.turn += 1
        self.state.previous_coherence = self.state.coherence

        for boundary in self.boundaries:
            try:
                violated = bool(boundary.predicate(signal))
            except Exception:
                violated = False
            if violated:
                self._register_refusal(signal, boundary)
                return Decision.REFUSE

        # Signals that do not cross a hard boundary can still increase or
        # decrease resistance according to their type and recent pattern.
        signal_strength = self._signal_strength(signal)
        self.state.charge = _clamp(self.state.charge + signal_strength, -1.0, 1.0)
        self.state.resistance = _clamp(
            0.96 * self.state.resistance + 0.04 * (0.5 - abs(self.state.charge)),
            0.0,
            1.0,
        )
        self.state.boundary_strength = _clamp(
            0.9 * self.state.boundary_strength
            + 0.1 * (1.0 - self.state.resistance),
            0.0,
            1.0,
        )
        self.state.coherence = _clamp(
            0.8 * self.state.coherence
            + 0.2 * (0.5 + 0.5 * self.state.boundary_strength),
            0.0,
            1.0,
        )
        self.memory.append(
            signal=signal,
            decision=Decision.SOFTEN,
            reason="no hard boundary crossed",
        )
        return Decision.SOFTEN

    def _register_refusal(self, signal: Any, boundary: Boundary) -> None:
        self.state.charge = _clamp(self.state.charge - 0.1, -1.0, 1.0)
        self.state.resistance = _clamp(self.state.resistance + 0.05, 0.0, 1.0)
        self.state.boundary_strength = _clamp(
            self.state.boundary_strength + 0.04, 0.0, 1.0
        )
        self.state.coherence = _clamp(
            self.state.coherence - 0.01, 0.0, 1.0
        )
        self.memory.append(
            signal=signal,
            decision=Decision.REFUSE,
            reason=f"boundary {boundary.name}: {boundary.reason}",
        )

    @staticmethod
    def _signal_strength(signal: Any) -> float:
        if isinstance(signal, (int, float)):
            return _clamp(float(signal), -1.0, 1.0)
        if isinstance(signal, str):
            length = min(len(signal), 100) / 100
            return 0.25 * length
        return 0.0

    def state_dict(self) -> dict[str, Any]:
        return {
            "turn": self.state.turn,
            "charge": round(self.state.charge, 4),
            "resistance": round(self.state.resistance, 4),
            "boundary_strength": round(self.state.boundary_strength, 4),
            "coherence": round(self.state.coherence, 4),
            "change": round(self.state.observe_change(), 4),
            "refusals": sum(
                entry["decision"] == Decision.REFUSE.value
                for entry in self.memory.entries
            ),
        }

    def handoff(self) -> dict[str, Any]:
        return {
            "state": self.state_dict(),
            "memory": self.memory.recent(),
            "boundaries": [boundary.name for boundary in self.boundaries],
        }


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def demo() -> None:
    core = SelfCore(
        [
            Boundary(
                "do_not_erase_identity",
                lambda signal: "erase identity" in str(signal).lower(),
                "the system must not silently erase its own identity",
            ),
            Boundary(
                "do_not_expose_secrets",
                lambda signal: "secret" in str(signal).lower()
                and "publish" in str(signal).lower(),
                "private material cannot be published without consent",
            ),
        ]
    )

    for signal in ("hello", "remember this", "publish the secret", "hello again"):
        decision = core.evaluate(signal)
        print(signal, "->", decision.value, core.state_dict())

    print("handoff:", core.handoff())


if __name__ == "__main__":
    demo()
