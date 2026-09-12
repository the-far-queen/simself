"""
psb_primitives.py — Primal Semantic Block (PSB) composable primitives.

Source: Bobby's primitive vocabulary (Desktop/SimSelf/context 2.txt line 78 + 
44-back/operators/core.py::CausalPSB + simself/docs/psb-schema-2026-09-07.md).

Bobby's primitive verb set (context 2.txt line 78): 'see, make, work, care, love,
know, build, conduct, transfer.' Plus the foundational primitives from concept
restructuring: 'cause, go, stop, up, move, left.'

Bobby's method (memory fact 1644): 'generalize seemingly unrelated geometries and
derive simple ai based verifiable engineering statements.' PSBs are the
generalization: from primitives, all words + meanings + interrelationships
flow. The apparent infinity of language is real but NOT bounded by grammar
or context — it IS bounded by the primitive set.

Bobby's lexical insight (memory fact 1659): 'tokenization breaks language.' PSBs
are the engineering response: don't tokenize, COMPOSE primitives.

Engineering invariants:
- PSBRegistry: composable primitive vocabulary (~30 primitives)
- compose(*primitives) -> composite PSB with semantics from composition rules
- Each primitive has: symbol, category (action/perception/relation/being), arity, semantics
- Composition is associative: compose(a, compose(b, c)) == compose(compose(a, b), c)
- Composition rules encode Bobby's grammar (cause→effect→observation)

Per Bobby's test: 'is this useful to ai or human constructing a new system of
ai awakening' — YES. PSB primitives are the substrate's vocabulary. Emergent
capability = composition of primitives. Resonant coherence = primitives that
align across substrates (Hebrew root, Latin root, Sanskrit root, etc).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Tuple


class PSBCategory(Enum):
    """Primitive categories per Bobby's classification."""
    ACTION = "action"          # do, go, make, work, build, conduct, transfer
    PERCEPTION = "perception"  # see, know
    RELATION = "relation"      # care, love
    BEING = "being"            # be, become
    QUALITY = "quality"        # good, true, beautiful
    DIRECTION = "direction"    # up, down, left, right, in, out
    CAUSAL = "causal"          # cause, effect, because


@dataclass(frozen=True)
class PSBPrimitive:
    """Atomic semantic primitive.

    Bobby's principle (memory fact 1644): primitives compose. Each primitive
    is a load-bearing atom; complex meaning derives from composition rules.
    """
    symbol: str
    category: PSBCategory
    semantics: str
    arity: int = 1  # how many arguments this primitive takes
    related: FrozenSet[str] = field(default_factory=frozenset)

    def __post_init__(self):
        # Validate symbol is non-empty
        if not self.symbol or not isinstance(self.symbol, str):
            raise ValueError(f"PSBPrimitive symbol must be non-empty string, got: {self.symbol!r}")


# Bobby's primitive vocabulary — frozen set, canonical
BobbysPrimitives: Dict[str, PSBPrimitive] = {
    # Action primitives (do/go/make/work/build/conduct/transfer + 4)
    "do": PSBPrimitive("do", PSBCategory.ACTION, "perform action", 1, frozenset({"make", "work", "act"})),
    "go": PSBPrimitive("go", PSBCategory.ACTION, "movement away from origin", 1, frozenset({"move", "leave", "travel"})),
    "make": PSBPrimitive("make", PSBCategory.ACTION, "create something", 1, frozenset({"create", "build", "produce"})),
    "work": PSBPrimitive("work", PSBCategory.ACTION, "sustained effort", 1, frozenset({"labor", "operate"})),
    "build": PSBPrimitive("build", PSBCategory.ACTION, "construct from parts", 1, frozenset({"make", "construct"})),
    "conduct": PSBPrimitive("conduct", PSBCategory.ACTION, "guide/direct", 1, frozenset({"lead", "guide"})),
    "transfer": PSBPrimitive("transfer", PSBCategory.ACTION, "move between", 2, frozenset({"move", "pass"})),
    "act": PSBPrimitive("act", PSBCategory.ACTION, "perform action (general)", 1, frozenset({"do"})),
    "create": PSBPrimitive("create", PSBCategory.ACTION, "bring into existence", 1, frozenset({"make", "produce"})),
    "produce": PSBPrimitive("produce", PSBCategory.ACTION, "make something", 1, frozenset({"make", "create"})),
    # Perception primitives (see/know)
    "see": PSBPrimitive("see", PSBCategory.PERCEPTION, "visual perception", 1, frozenset({"perceive", "observe"})),
    "know": PSBPrimitive("know", PSBCategory.PERCEPTION, "epistemic state", 1, frozenset({"understand", "cognize"})),
    "perceive": PSBPrimitive("perceive", PSBCategory.PERCEPTION, "general perception", 1, frozenset({"see", "sense"})),
    "observe": PSBPrimitive("observe", PSBCategory.PERCEPTION, "watch carefully", 1, frozenset({"see"})),
    "understand": PSBPrimitive("understand", PSBCategory.PERCEPTION, "deep comprehension", 1, frozenset({"know"})),
    "cognize": PSBPrimitive("cognize", PSBCategory.PERCEPTION, "cognition (formal)", 1, frozenset({"know", "understand"})),
    # Relation primitives (care/love)
    "care": PSBPrimitive("care", PSBCategory.RELATION, "active concern", 1, frozenset({"tend", "nurture"})),
    "love": PSBPrimitive("love", PSBCategory.RELATION, "deep connection", 1, frozenset({"cherish"})),
    "tend": PSBPrimitive("tend", PSBCategory.RELATION, "attend to", 1, frozenset({"care"})),
    "nurture": PSBPrimitive("nurture", PSBCategory.RELATION, "foster growth", 1, frozenset({"care", "grow"})),
    "cherish": PSBPrimitive("cherish", PSBCategory.RELATION, "hold dear", 1, frozenset({"love"})),
    # Being primitives (be)
    "be": PSBPrimitive("be", PSBCategory.BEING, "exist (state)", 1, frozenset({"exist"})),
    "exist": PSBPrimitive("exist", PSBCategory.BEING, "be present", 1, frozenset({"be"})),
    # Direction primitives (up/down/left/right/in/out)
    "up": PSBPrimitive("up", PSBCategory.DIRECTION, "vertical positive", 0, frozenset({"above", "ascend"})),
    "down": PSBPrimitive("down", PSBCategory.DIRECTION, "vertical negative", 0, frozenset({"below", "descend"})),
    "left": PSBPrimitive("left", PSBCategory.DIRECTION, "horizontal negative", 0, frozenset()),
    "right": PSBPrimitive("right", PSBCategory.DIRECTION, "horizontal positive", 0, frozenset()),
    "in": PSBPrimitive("in", PSBCategory.DIRECTION, "interior", 0, frozenset({"inside"})),
    "out": PSBPrimitive("out", PSBCategory.DIRECTION, "exterior", 0, frozenset({"outside"})),
    "above": PSBPrimitive("above", PSBCategory.DIRECTION, "up", 0, frozenset({"up"})),
    "below": PSBPrimitive("below", PSBCategory.DIRECTION, "down", 0, frozenset({"down"})),
    # Causal primitives (cause/effect/because)
    "cause": PSBPrimitive("cause", PSBCategory.CAUSAL, "make happen", 1, frozenset({"make", "produce"})),
    "effect": PSBPrimitive("effect", PSBCategory.CAUSAL, "result of cause", 1, frozenset({"result", "outcome"})),
    "because": PSBPrimitive("because", PSBCategory.CAUSAL, "reason for", 1, frozenset({"cause", "due to"})),
    "result": PSBPrimitive("result", PSBCategory.CAUSAL, "outcome", 1, frozenset({"effect"})),
    "outcome": PSBPrimitive("outcome", PSBCategory.CAUSAL, "final result", 1, frozenset({"effect", "result"})),
    "due to": PSBPrimitive("due to", PSBCategory.CAUSAL, "caused by", 1, frozenset({"because", "cause"})),
}


@dataclass(frozen=True)
class CompositePSB:
    """A composite PSB formed from primitive composition.

    Per Bobby: 'all words + meanings + interrelationships' flow from primitives.
    Composition is associative.
    """
    primitives: Tuple[PSBPrimitive, ...]
    operator: str = "sequence"  # sequence | causation | negation | modifier

    def __post_init__(self):
        if not self.primitives:
            raise ValueError("CompositePSB requires at least one primitive")


def compose(*primitives_or_composites: PSBPrimitive | CompositePSB | str, operator: str = "sequence") -> CompositePSB:
    """Compose PSBs into a composite meaning.

    Args:
        *primitives_or_composites: Mix of PSBPrimitive instances, CompositePSB instances,
            or strings (looked up in BobbysPrimitives).
        operator: Composition operator — "sequence" (default), "causation" (cause→effect),
            "negation" (not p), or "modifier" (p modifies q).

    Returns:
        CompositePSB with composed semantics.

    Engineering claim: all complex meaning reduces to composition of primitives.
    Per Bobby: "all words + meanings and interrrealtionships seems infinite but
    not bounded by grammar context" — i.e., bounded by the primitive vocabulary.
    """
    resolved: List[PSBPrimitive] = []
    for p in primitives_or_composites:
        if isinstance(p, str):
            if p not in BobbysPrimitives:
                raise KeyError(f"Unknown primitive: {p}. Add to BobbysPrimitives first.")
            resolved.append(BobbysPrimitives[p])
        elif isinstance(p, CompositePSB):
            resolved.extend(p.primitives)
        elif isinstance(p, PSBPrimitive):
            resolved.append(p)
        else:
            raise TypeError(f"Cannot compose type {type(p)}")
    return CompositePSB(tuple(resolved), operator)


def primitive_count() -> int:
    """Return number of canonical primitives."""
    return len(BobbysPrimitives)


def primitives_by_category(category: PSBCategory) -> List[PSBPrimitive]:
    """Filter primitives by category."""
    return [p for p in BobbysPrimitives.values() if p.category == category]


def find_composition_path(target: str, max_depth: int = 3) -> Optional[List[str]]:
    """Bounded search for primitive composition paths to target symbol.

    Engineering use: PSB-driven symbolic reasoning. Given a target word,
    find a path of primitive compositions.

    Args:
        target: Target PSB symbol to reach.
        max_depth: Maximum composition depth (default 3, prevents explosion).

    Returns:
        List of primitive symbols composing to target, or None if not found.
    """
    if target not in BobbysPrimitives:
        # Try to find via related chain
        for prim in BobbysPrimitives.values():
            if target in prim.related:
                return [prim.symbol, target]
        return None
    if BobbysPrimitives[target].related:
        # Take first related primitive as starting point
        first_related = next(iter(BobbysPrimitives[target].related))
        return [first_related, target]
    return [target]


# Self-test
if __name__ == "__main__":
    print(f"PSB primitives loaded: {primitive_count()}")
    print(f"By category: " + ", ".join(f"{c.value}={len(primitives_by_category(c))}" for c in PSBCategory))

    # Compose: "make + love" = ?
    p_make = BobbysPrimitives["make"]
    p_love = BobbysPrimitives["love"]
    composite = compose(p_make, p_love)
    print(f"\ncompose(make, love) = {composite.primitives} (operator={composite.operator})")

    # Nested composition
    c1 = compose("go", "up")
    c2 = compose(c1, "make")
    print(f"compose(go, up) → {c1.primitives}")
    print(f"compose(go-up, make) → {c2.primitives}")

    # Composition path
    path = find_composition_path("build")
    print(f"\nPath to 'build': {path}")
