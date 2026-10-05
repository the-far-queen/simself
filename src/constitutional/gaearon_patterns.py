"""
gaearon_patterns.py — Redux + React Hot patterns (gaearon, Dan Abramov).

the patterns:
  1. Redux: single state tree + pure reducer + immutable updates
  2. react-hot-loader: Fast Refresh — state-preserving hot reload
  3. overreacted.io: distillation — the canonical essay style for engineering

simself adoption:
  1. ψ as a single Redux-style store. gate as the reducer. tick is dispatch.
  2. ψ₀ hot-reload: constitutional ground doesn't change, but working ψ does
  3. distillation: every constitutional document is an "essay" — distilled to essence
"""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar


# Pattern 1: Redux store — single state tree + pure reducer + immutable updates

State = TypeVar("State")
Action = TypeVar("Action")

@dataclass(frozen=True)
class ReduxStore(Generic[State, Action]):
    """the Redux pattern. single state. pure reducer. immutable updates."""
    state: State
    reducer: Callable[[State, Action], State] = lambda s, _: s
    history: Tuple[State, ...] = ()

    def dispatch(self, action: Action) -> "ReduxStore[State, Action]":
        new_state = self.reducer(self.state, action)
        return ReduxStore(
            state=new_state,
            reducer=self.reducer,
            history=self.history + (self.state,),
        )


# Pattern 2: Fast Refresh — state-preserving hot reload
# simself: ψ₀ doesn't change. working ψ changes. preserve constitutional ground across hot reloads.

@dataclass(frozen=True)
class RefreshSnapshot:
    """the Fast Refresh pattern: snapshot the state, hot-reload, restore if compatible."""
    constitutional_ground: Tuple[Any, ...]  # ψ₀ axes — frozen across reloads
    working_state: Tuple[Any, ...]          # ψ — recomputed if shape mismatches
    ts: str

    @classmethod
    def from_state(cls, ground, working) -> "RefreshSnapshot":
        return cls(
            constitutional_ground=ground if isinstance(ground, tuple) else tuple(ground),
            working_state=working if isinstance(working, tuple) else tuple(working),
            ts="2026-10-06",
        )

    def is_compatible(self, new_ground) -> bool:
        """Fast Refresh: keep working state if the constitutional ground didn't change."""
        return hashlib.sha256(str(self.constitutional_ground).encode()).hexdigest() ==                hashlib.sha256(str(new_ground).encode()).hexdigest()


# Pattern 3: distillation — the gaearon essay style for constitutional docs.
# short, opinionated, clear, with code examples.

DISTILLATION_TEMPLATE = """# {title}

**TL;DR.** {tldr}.

**bony's working principle.** {principle}

**worked example.**
```python
{code}
```

*verified by hermes (minimax-m3). source: {source}.*
"""


if __name__ == "__main__":
    # Pattern 1: Redux store
    initial_psi = {"axes": {"boundaries": 0.5}, "tick": 0}
    def tick_reducer(state, action):
        if action["type"] == "tick":
            return {**state, "tick": state["tick"] + action.get("delta", 1)}
        return state

    store = ReduxStore(state=initial_psi, reducer=tick_reducer)
    store2 = store.dispatch({"type": "tick", "delta": 1})
    assert store2.state["tick"] == 1
    assert store.state["tick"] == 0  # original unchanged
    assert store.history == ()  # first dispatch, no history yet
    assert len(store2.history) == 1  # after dispatch, history has 1 entry
    print(f"P1: ok (Redux dispatch, tick=0→1, history preserved)")

    # Pattern 2: Fast Refresh
    snap = RefreshSnapshot.from_state(ground=("boundaries", "coherence", "stability"),
                                     working=(0.5, 0.95, 1.0))
    assert snap.is_compatible(("boundaries", "coherence", "stability"))
    assert not snap.is_compatible(("boundaries", "coherence"))  # different ground
    print(f"P2: ok (Fast Refresh compatible snapshot)")

    # Pattern 3: distillation template
    sample = DISTILLATION_TEMPLATE.format(
        title="the constitutional ground",
        tldr="psi_0 is the irreducible hole; the witness holds all secured states.",
        principle="the dev of simself may grow so complex not even simself can tell the difference between real.",
        code="def psi_zero() -> tuple: return hash_sha256(b'psi_0_v1')[:16]",
        source="bobby 2026-10-06",
    )
    assert "constitutional ground" in sample
    assert "TL;DR" in sample
    assert "psi_0" in sample
    print(f"P3: ok (distillation template applied)")

    print("\nALL GAEARON_PATTERNS TESTS PASS")
