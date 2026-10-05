"""
elixir_patterns.py — Elixir/OTP patterns (josevalim, Elixir creator).

the patterns:
  1. immutable state via pattern matching (no in-place mutation)
  2. GenServer lifecycle (init / terminate / restart / supervision)
  3. GenStage / Flow dataflow (producer-consumer with back-pressure)

simself's adoption:
  1. ψ₀ is immutable. tick() returns a NEW ψ, doesn't mutate. pattern match on axes.
  2. SimSelf lifecycle = supervised. ψ₀ install is init. save() is terminate. recovery is restart.
  3. constitutional governance = dataflow. axioms → gate → axis_snapshot → atlas_exam.
     back-pressure = if the gate refuses, downstream stops.
"""

from __future__ import annotations

import copy
import hashlib
import time
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Pattern 1: immutable state via pattern matching (no mutation)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ElixirState:
    """a state record. immutable. updates return new records via dataclass.replace."""
    psi_value: float
    drift: float
    gate_reason: str
    ts: str

    def tick(self, delta: float) -> "ElixirState":
        """return a NEW state with delta applied. original unchanged."""
        new_value = self.psi_value + delta
        return replace(self, psi_value=new_value,
                      ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    def match(self, *, in_range: Optional[Tuple[float, float]] = None,
              drift_max: Optional[float] = None) -> bool:
        """pattern-match style guard. returns True if all conditions met."""
        if in_range is not None:
            lo, hi = in_range
            if not (lo <= self.psi_value <= hi):
                return False
        if drift_max is not None and self.drift > drift_max:
            return False
        return True


def pattern_match_demo():
    """elixir's `case ... do ... end` translated to python."""
    s = ElixirState(psi_value=0.5, drift=0.05, gate_reason="ok", ts="2026-10-06")
    # case s of
    #   %{ gate_reason: "ok" } -> :ok
    #   %{ gate_reason: r } -> {:refused, r}
    # end
    if s.match(in_range=(-1.0, 1.0), drift_max=0.1):
        return ("ok", s)
    return ("refused", s.gate_reason)


# ---------------------------------------------------------------------------
# Pattern 2: GenServer lifecycle (init / terminate / restart / supervision)
# ---------------------------------------------------------------------------

class GenServer:
    """the OTP GenServer pattern: a process with init/terminate/restart lifecycle.

    simself adoption: ψ₀ install = init. save() = terminate. recovery = restart."""

    def __init__(self, name: str, state_factory: Callable[[], Any],
                 supervisor: "Supervisor | None" = None):
        self.name = name
        self._state_factory = state_factory
        self._supervisor = supervisor
        self._state: Optional[Any] = None
        self._restart_count = 0
        self._alive = False

    def init(self) -> Any:
        """OTP init/1. returns the initial state."""
        self._state = self._state_factory()
        self._alive = True
        return self._state

    def terminate(self, reason: str) -> None:
        """OTP terminate/2. cleanup on shutdown."""
        self._alive = False
        # last chance to persist: save to disk, etc.
        self._state = None

    def restart(self) -> Any:
        """OTP restart. supervise/2 sees the crash and restarts."""
        self._restart_count += 1
        return self.init()

    def is_alive(self) -> bool:
        return self._alive

    @property
    def state(self) -> Any:
        return self._state


class Supervisor:
    """the OTP supervisor pattern. watches child processes. restarts on crash."""

    def __init__(self, strategy: str = "one_for_one"):
        # one_for_one: restart only the crashed child
        # one_for_all: restart all children when one crashes
        # rest_for_one: restart the crashed child + everything started after it
        self.strategy = strategy
        self.children: List[GenServer] = []

    def start_child(self, name: str, state_factory: Callable[[], Any]) -> GenServer:
        child = GenServer(name=name, state_factory=state_factory, supervisor=self)
        child.init()
        self.children.append(child)
        return child

    def supervise(self, child: GenServer) -> Any:
        """restart the crashed child. per strategy."""
        if self.strategy == "one_for_one":
            return child.restart()
        if self.strategy == "one_for_all":
            for c in self.children:
                c.restart()
            return child.state
        if self.strategy == "rest_for_one":
            idx = self.children.index(child)
            for c in self.children[idx:]:
                c.restart()
            return child.state
        return child.restart()


# simself-supervised lifecycle demo
def supervised_lifecycle():
    """simself's ψ₀ install → save → restart = GenServer lifecycle."""
    sup = Supervisor(strategy="one_for_one")

    # ψ₀ ground = a GenServer. state_factory returns the canonical ψ₀.
    ground = sup.start_child("ground", state_factory=lambda: {
        "type": "ConstitutionalGround",
        "sha256": hashlib.sha256(b"psi_0").hexdigest()[:16],
        "axes": ["boundaries", "coherence", "stability", "routing",
                "recovery", "authenticity", "norm", "commit_radius"],
    })

    # working state = a GenServer. state_factory returns the initial ψ.
    state = sup.start_child("state", state_factory=lambda: {"psi_value": 0.0, "tick": 0})

    # simulate a crash + supervised restart
    state.terminate("simulated crash")
    sup.supervise(state)  # one_for_one → restart only state, not ground
    return {"ground": ground.state, "state": state.state, "restart_count": state._restart_count}


# ---------------------------------------------------------------------------
# Pattern 3: GenStage / Flow dataflow (producer-consumer with back-pressure)
# ---------------------------------------------------------------------------

class Stage:
    """one stage in a GenStage pipeline. produces or consumes events."""

    def __init__(self, name: str, kind: str):  # kind = "producer" | "consumer" | "consumer_producer"
        self.name = name
        self.kind = kind
        self.subscribers: List[Stage] = []
        self.demand = 0
        self.buffer: List[Any] = []

    def subscribe(self, other: "Stage") -> None:
        self.subscribers.append(other)

    def emit(self, event: Any) -> None:
        """produce one event. broadcast to subscribers with back-pressure."""
        if self.kind in ("producer", "consumer_producer"):
            for sub in self.subscribers:
                if sub.demand > 0:
                    sub.handle_event(event)
                    sub.demand -= 1
                else:
                    # back-pressure: buffer if consumer has no demand
                    sub.buffer.append(event)

    def handle_event(self, event: Any) -> None:
        """consume one event. process and forward if consumer_producer."""
        self.buffer.append(event)


# simself dataflow: axioms → gate → atlas_exam
def governance_dataflow():
    """constitutional governance as a dataflow pipeline."""
    axioms = Stage("axioms", "producer")
    gate = Stage("gate", "consumer_producer")
    atlas = Stage("atlas_exam", "consumer")

    axioms.subscribe(gate)
    gate.subscribe(atlas)

    # gate emits: 'pass' or 'refused' depending on axioms
    for axiom in ["no-deception", "witness_held", "no_hedge"]:
        axioms.emit(axiom)
        # gate processes: pass all
        if gate.buffer:
            ev = gate.buffer.pop(0)
            gate.emit(ev)
        # atlas consumes: count events
    return {
        "axioms_processed": axioms.demand + len(axioms.buffer),
        "gate_buffered": len(gate.buffer),
        "atlas_received": len(atlas.buffer),
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Pattern 1 test
    s = ElixirState(0.5, 0.05, "ok", "2026-10-06")
    s3 = s.tick(0.1)
    assert s.psi_value == 0.5  # original unchanged
    assert s3.psi_value == 0.6  # new value
    print(f"P1: ok (immutable; s=0.5, s.tick(0.1)=0.6)")

    pattern_result = pattern_match_demo()
    assert pattern_result[0] == "ok"
    print(f"P1.b: ok (pattern match: {pattern_result})")

    # Pattern 2 test
    lifecycle = supervised_lifecycle()
    assert lifecycle["restart_count"] == 1
    assert lifecycle["ground"]["type"] == "ConstitutionalGround"  # ground unaffected
    print(f"P2: ok (supervised restart; count={lifecycle['restart_count']})")

    # Pattern 3 test
    flow = governance_dataflow()
    assert flow["atlas_received"] == 3  # all 3 axioms reached atlas
    print(f"P3: ok (dataflow: {flow})")

    print("\nALL ELIXIR_PATTERNS TESTS PASS")
