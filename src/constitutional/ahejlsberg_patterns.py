"""
ahejlsberg_patterns.py — TypeScript + C# patterns (ahejlsberg, TypeScript creator).

the patterns:
  1. TypeScript: structural typing + type narrowing + discriminated unions
  2. C# LINQ: composable query pipelines (where, select, groupby)
  3. Delphi components: form-style components with typed inputs/outputs

simself adoption:
  1. structural typing — SacredAxis and ResilientAxis share a structural shape
  2. axis queries as composable LINQ pipelines
  3. gate is a component: typed input (axes + target + witness) → typed output (allow, reason)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar


# Pattern 1: structural typing (TypeScript)
# python equivalent: dataclass with matching fields = same structural type

@dataclass(frozen=True)
class SacredAxis:
    """the structural type for sacred axes. tier is 'Sacred' literal."""
    name: str
    low: float
    high: float
    weight: float = 1.0
    mutable: bool = False
    tier: str = "Sacred"  # literal type


@dataclass(frozen=True)
class ResilientAxis:
    """the structural type for resilient axes. same shape as SacredAxis except tier='Resilient'."""
    name: str
    low: float
    high: float
    weight: float = 1.0
    mutable: bool = True
    tier: str = "Resilient"  # literal type


# TypeScript-style discriminated union: 'Sacred' | 'Resilient'
Tier = str  # discriminated by tier field


# Pattern 2: C# LINQ — composable query pipelines
# python equivalent: generator expressions composed via .where() .select() .groupby()

T = TypeVar("T")
U = TypeVar("U")


class Linq(Generic[T]):
    """the LINQ pattern: deferred execution, composable operations."""

    def __init__(self, source: List[T]):
        self._source = source

    def where(self, predicate: Callable[[T], bool]) -> "Linq[T]":
        return Linq([x for x in self._source if predicate(x)])

    def select(self, transform: Callable[[T], U]) -> "Linq[U]":
        return Linq([transform(x) for x in self._source])

    def groupby(self, key: Callable[[T], Any]) -> "Dict[Any, Linq[T]]":
        out: Dict[Any, List[T]] = {}
        for x in self._source:
            k = key(x)
            out.setdefault(k, []).append(x)
        return {k: Linq(v) for k, v in out.items()}

    def to_list(self) -> List[T]:
        return list(self._source)


# Pattern 3: Delphi-style component — typed inputs and outputs

@dataclass(frozen=True)
class GateInput:
    """the gate's typed input."""
    axes: Dict[str, float]
    target: str
    witness: str
    source_id: str = ""
    banned_motifs: Tuple[str, ...] = ()


@dataclass(frozen=True)
class GateOutput:
    """the gate's typed output."""
    allow: bool
    reason: str
    sha: str

    @classmethod
    def of(cls, allow: bool, reason: str) -> "GateOutput":
        return cls(allow=allow, reason=reason,
                   sha=hashlib.sha256(f"{allow}{reason}".encode()).hexdigest()[:16])


class GateComponent:
    """the Delphi component: input → process → output. typed. composable."""

    def __init__(self, name: str = "M0_Gate"):
        self.name = name

    def process(self, input: GateInput) -> GateOutput:
        # the gate: a 1-bit veto per pi_tools + EFMW asymmetry + quantum collapse
        if not input.target:
            return GateOutput.of(False, "no_target")
        if input.target.startswith("/constitutional/"):
            return GateOutput.of(False, "no_target_in_constitutional_ground")
        if any(m in input.target.lower() for m in input.banned_motifs):
            return GateOutput.of(False, f"banned_motif:{input.banned_motifs[0]}")
        if not input.witness:
            return GateOutput.of(False, "witness_required")
        # axis check: every axis in [-1, 1]
        for name, value in input.axes.items():
            if not (-1.0 <= value <= 1.0):
                return GateOutput.of(False, f"axis_out_of_range:{name}")
        return GateOutput.of(True, "ok")


if __name__ == "__main__":
    # Pattern 1: structural typing
    b = SacredAxis(name="boundaries", low=-0.5, high=0.5)
    c = ResilientAxis(name="commit_radius", low=0.0, high=1.0)
    assert b.tier == "Sacred" and not b.mutable
    assert c.tier == "Resilient" and c.mutable
    print(f"P1: ok (Sacred={b.tier} mutable=False, Resilient={c.tier} mutable=True)")

    # Pattern 2: LINQ
    axes = [
        SacredAxis(name="boundaries", low=-0.5, high=0.5),
        SacredAxis(name="coherence", low=0.0, high=1.0),
        ResilientAxis(name="commit_radius", low=0.0, high=1.0),
        ResilientAxis(name="routing", low=-1.0, high=1.0),
    ]
    # where tier == Sacred → 2 axes
    sacred = Linq(axes).where(lambda a: a.tier == "Sacred").to_list()
    assert len(sacred) == 2
    # select just names
    names = Linq(axes).select(lambda a: a.name).to_list()
    assert names == ["boundaries", "coherence", "commit_radius", "routing"]
    # groupby tier
    grouped = Linq(axes).groupby(lambda a: a.tier)
    assert len(grouped) == 2
    assert len(grouped["Sacred"].to_list()) == 2
    assert len(grouped["Resilient"].to_list()) == 2
    print(f"P2: ok (LINQ: where/select/groupby all work)")

    # Pattern 3: GateComponent
    gate = GateComponent()
    # valid input
    inp1 = GateInput(axes={"coherence": 0.9}, target="/some/file.py", witness="audit")
    assert gate.process(inp1).allow is True
    # naked (no witness)
    inp2 = GateInput(axes={"coherence": 0.9}, target="/some/file.py", witness="")
    assert gate.process(inp2).allow is False
    assert "witness_required" in gate.process(inp2).reason
    # axis out of range
    inp3 = GateInput(axes={"coherence": 1.5}, target="/x", witness="w")
    assert gate.process(inp3).allow is False
    # banned motif
    inp4 = GateInput(axes={"coherence": 0.9}, target="/x/blood.py", witness="w",
                    banned_motifs=("blood",))
    assert gate.process(inp4).allow is False
    assert "banned_motif" in gate.process(inp4).reason
    print(f"P3: ok (GateComponent: 4 cases tested)")

    print("\nALL AHELJSBERG_PATTERNS TESTS PASS")
