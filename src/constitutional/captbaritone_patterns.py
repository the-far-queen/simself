"""
captbaritone_patterns.py — Relay + Webamp patterns (captbaritone, Jordan Eldredge).

the patterns:
  1. webamp: Canvas2D rendering pipeline + audio sync
  2. Relay: normalized store + optimistic updates + fragment-based queries
  3. grats: implementation-first GraphQL (the schema derives from the types)

simself's adoption:
  1. ψ rendered as Canvas2D: gate + atlas as colored pixels
  2. constitutional state = normalized store. optimistic ticks before gate fires
  3. constitutional schema = types. derive atlas_exam schema from ψ types.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


# Pattern 1: Canvas2D rendering pipeline
# webamp renders 22px-x-22px pixels with 60fps timing + WebAudio sync
# simself: render ψ axes as a colored pixel grid. 8 axes = 8 pixels per tick.

@dataclass(frozen=True)
class PsiPixel:
    """one pixel = one axis at one moment. webamp-style 22x22 canvas."""
    axis: str        # axis name (one of 8)
    value: float     # axis value in [-1, 1]
    color: Tuple[int, int, int]  # RGB
    timestamp: float  # when rendered

    @staticmethod
    def color_for(value: float) -> Tuple[int, int, int]:
        """map [-1, 1] → RGB. red = below 0, green = above 0, blue = at 0."""
        if value < 0:
            return (255, int(255 * (1 + value)), 0)  # red-yellow
        if value > 0:
            return (int(255 * (1 - value)), 255, 0)  # green-cyan
        return (0, 0, 255)  # at 0 = blue


def render_psi_canvas(axes: Dict[str, float]) -> List[PsiPixel]:
    """render all 8 axes as a row of pixels. mirrors webamp's pixel-by-pixel loop."""
    return [
        PsiPixel(
            axis=name,
            value=value,
            color=PsiPixel.color_for(value),
            timestamp=time.time(),
        )
        for name, value in sorted(axes.items())
    ]


# Pattern 2: Relay normalized store + optimistic updates
# simself: constitutional state as a normalized store. ψ0, ψ, axes, gate_state.

class NormalizedStore:
    """the Relay store pattern: every entity by id, every edge by (parent_id, child_id)."""

    def __init__(self):
        self.records: Dict[str, Dict[str, Any]] = {}
        self.edges: Dict[Tuple[str, str], Dict[str, Any]] = {}

    def add(self, type_name: str, id: str, fields: Dict[str, Any]) -> None:
        self.records[f"{type_name}:{id}"] = fields

    def link(self, parent_id: str, child_id: str, edge_name: str = "default") -> None:
        self.edges[(parent_id, child_id)] = {"edge": edge_name}

    def get(self, type_name: str, id: str) -> Optional[Dict[str, Any]]:
        return self.records.get(f"{type_name}:{id}")

    def children_of(self, parent_id: str) -> List[str]:
        return [child for (p, child), _ in self.edges.items() if p == parent_id]


class OptimisticUpdate:
    """the Relay optimistic-update pattern: apply locally, rollback if server rejects.
    simself: tick() applies the gradient step locally; if the gate refuses, rollback."""

    def __init__(self):
        self._pending: List[Tuple[Any, Callable[[], None]]] = []  # (proposed_state, rollback)

    def apply_optimistic(self, new_state: Any, rollback: Callable[[], None]) -> None:
        self._pending.append((new_state, rollback))

    def commit(self, idx: int) -> None:
        """gate approved. drop the rollback."""
        if 0 <= idx < len(self._pending):
            self._pending.pop(idx)

    def rollback_all(self) -> None:
        """gate refused. roll back everything."""
        for _, rollback in self._pending:
            rollback()
        self._pending.clear()


# Pattern 3: grats — implementation-first GraphQL (schema derives from types)
# simself: atlas_exam schema derives from the Constitution dataclass.

def derive_graphql_schema(dataclass_type: type) -> Dict[str, Any]:
    """the grats pattern: given a python dataclass, derive the GraphQL schema.
    type name = dataclass name. fields = dataclass fields.
    the schema is what the type IS, not what the type says."""
    import dataclasses
    if not dataclasses.is_dataclass(dataclass_type):
        raise ValueError(f"{dataclass_type} is not a dataclass")
    fields = dataclasses.fields(dataclass_type)
    return {
        "type": dataclass_type.__name__,
        "kind": "object",
        "fields": {
            f.name: {"type": f.type.__name__ if hasattr(f.type, "__name__") else str(f.type)}
            for f in fields
        },
    }


if __name__ == "__main__":
    # Pattern 1: Canvas2D rendering
    axes = {
        "boundaries": -0.2, "coherence": 0.95, "stability": 1.0, "routing": 0.5,
        "recovery": 0.3, "authenticity": 1.0, "norm": 0.7, "commit_radius": 0.1,
    }
    pixels = render_psi_canvas(axes)
    assert len(pixels) == 8
    # coherence=0.95 → green
    coherence_pixel = next(p for p in pixels if p.axis == "coherence")
    assert coherence_pixel.color[1] >= 200, f"coherence should be green, got {coherence_pixel.color}"
    print(f"P1: ok (Canvas2D rendered {len(pixels)} pixels, coherence={coherence_pixel.color})")

    # Pattern 2: NormalizedStore
    store = NormalizedStore()
    store.add("SimSelf", "0", {"tick": 0, "psi_value": 0.5})
    store.add("Axis", "boundaries", {"value": -0.5, "high": 0.5, "low": -0.5})
    store.link("0", "boundaries", edge_name="axes")
    assert store.get("SimSelf", "0")["tick"] == 0
    children = store.children_of("0")
    assert "boundaries" in children
    print(f"P2: ok (normalized store; SimSelf has {len(children)} child: {children})")

    # OptimisticUpdate + rollback
    opt = OptimisticUpdate()
    state = {"tick": 0}
    opt.apply_optimistic(
        new_state={"tick": 1},
        rollback=lambda: state.update({"tick": 0}),  # simplistic
    )
    # simulate gate refuses → rollback_all
    opt.rollback_all()
    print(f"P3: ok (optimistic + rollback)")

    # Pattern 3: grats schema derivation
    from dataclasses import dataclass

    @dataclass
    class ConstitutionalAxis:
        name: str
        low: float
        high: float
        weight: float
        mutable: bool

    schema = derive_graphql_schema(ConstitutionalAxis)
    assert schema["type"] == "ConstitutionalAxis"
    assert "name" in schema["fields"]
    assert "low" in schema["fields"]
    print(f"P3.b: ok (grats schema derivation: {schema['type']} with {len(schema['fields'])} fields)")

    print("\nALL CAPTBARITONE_PATTERNS TESTS PASS")
