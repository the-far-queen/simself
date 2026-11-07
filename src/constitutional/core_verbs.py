"""
core_verbs.py -- BOBBY'S OWN PRIMITIVE VERBS, RESTORED, IN THEIR OWN
REGISTRY.

**AND THIS IS A RESTORE, NOT AN INVENTION, AND THE GIT HISTORY IS THE
PROOF.**

Bobby, 2026-09-12, commit `b8e72bc` -- *"feat(constitutional): docs-as-code
implementations per Bobby directives"* -- added to
`src/constitutional/psb_primitives.py`:

    class PSBCategory(Enum):
        ACTION     = "action"      # do, go, make, work, build, conduct, transfer
        PERCEPTION = "perception"  # see, know
        RELATION   = "relation"    # care, love
        BEING      = "being"       # be, become
        QUALITY    = "quality"     # good, true, beautiful
        DIRECTION  = "direction"   # up, down, left, right, in, out
        CAUSAL     = "causal"      # cause, effect, because

    36 primitives, each with a gloss, a weight and a related-set
    class CompositePSB
    def compose(*primitives_or_composites, operator="sequence")
    def primitive_count() -> int
    def primitives_by_category(category)
    def find_composition_path(target, max_depth=3)

**AND ON 2026-09-16 THE FILE WAS REWRITTEN** -- commit `d3e890a`, the
Grok master plan rewrite -- and the rewrite's own docstring says why:

    "The previous version of this file carried 37 primitives and case
     slots and called it a hypothesis. Per Grok (segment 02, applied
     2026-09-16): coverage on real sentences is the test. This file
     exposes 6 primitives and a coverage() function that measures it
     against a fixed sentence list."

**AND MEASURED 2026-11-07, THE COST OF THAT REWRITE:**

```
bobby's 15 core verbs, through the CURRENT psb_primitives.classify_span:
    go, stop, move            -> admitted       (3 of 15)
    see, make, work, care, love, know, build, conduct, transfer,
    cause, up, left           -> REFUSED as other (12 of 15)

bobby's 15 core verbs in the MLTR register (416 terms):
    care, love, build, transfer  -> present      (4 of 15)
    the other eleven             -> ABSENT

THE UNION OF THE TWO CURRENT REGISTRIES COVERS 7 OF BOBBY'S 15.
**AND EIGHT OF BOBBY'S OWN CORE VERBS ARE IN NO VOCABULARY ANYWHERE IN
THE SUBSTRATE**: see, make, work, know, conduct, cause, up, left.
```

**AND `compose()` IS GONE, AND IT IS THE ENGINE.** Bobby's method 1644
was *"all words + meanings bounded by primitive set, not grammar"* -- and
`compose()` is the operator that did the bounding, and
`find_composition_path()` is what turned a primitive set into a
generative one.

**SO THE VERBS COME BACK HERE, IN THEIR OWN FILE, AND
`psb_primitives.py` IS NOT TOUCHED.** The reason is the current file's
own docstring, quoted from it:

    "The PSB registry below is a SEPARATE registry, exactly like
     LITERARY_FORMS, and for the same reason: putting new vocabulary
     into PRIMITIVES changed classify_span() and silently weakened the
     confabulation filter."

**AND A SECOND REASON, WHICH IS THE REAL ONE: THE REWRITE WAS RIGHT
ABOUT THE MEASUREMENT AND WRONG ABOUT WHAT IT REPLACED.** A coverage
number against a FIXED SENTENCE LIST is a measurement, and the sentence
list is small. The 36 primitives with their categories and their
composer are a STRUCTURE, and the structure is what makes 30,000 words
fall out of a few thousand patterns. **BOTH ARE NEEDED, AND THEY ARE
NEEDED IN SEPARATE FILES.**

Run:
    python src/constitutional/core_verbs.py --check
    python src/constitutional/core_verbs.py --coverage
"""

from __future__ import annotations
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

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Tuple
import sys


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


#: THE RESTORED TABLE, under the names the rest of this file and the
#: readers of it use. **AND THE OLD FILE'S OWN NAME IS KEPT**: the
#: table was called `BobbysPrimitives` from 2026-09-12, and a restore
#: that renames things is half an invention.
CORE_PRIMITIVES = BobbysPrimitives
PRIMITIVES = CORE_PRIMITIVES


def primitive_count() -> int:
    """HOW MANY PRIMITIVES, and it is MEASURED and not asserted."""
    return len(CORE_PRIMITIVES)


def primitives_by_category(category):
    """The primitives of one category."""
    return [p for p in CORE_PRIMITIVES.values() if p.category == category]


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


def resolve_primitive(word: str) -> PSBPrimitive:
    """RESOLVE A WORD TO ITS PRIMITIVE, and the resolution goes through
    the RELATED SETS.

    **AND THIS IS THE FIX, AND IT IS MEASURED.** The restored table has
    37 primitives and each carries a `related` set of the words that
    mean it -- `go` carries {"travel", "leave", "move"}, and `up` carries
    {"ascend", "above"}. The old `compose()` looked ONLY in the table, so
    `compose("see", "cause", "move")` raised `KeyError('Unknown
    primitive: move')` -- **because "move" was never a primitive, it was
    only ever a RELATED word of "go".**

    **AND THAT IS WRONG, AND BOBBY'S OWN METHOD SAYS WHY.** Method 1644:
    *"all words + meanings bounded by primitive set, not grammar"* -- so
    a word is bounded by the primitive set THROUGH ITS RELATIONS, and a
    composer that cannot use a related word is not bounding the words,
    it is bounding the table.

    **SO THE RESOLUTION IS TWO DEEP: the table first, then the related
    sets.** And the related word resolves to the primitive that means
    it, so `compose("move")` composes the MEANING of movement, which is
    what a composition of words is for.
    """
    if word in BobbysPrimitives:
        return BobbysPrimitives[word]
    # THE RELATED SETS, and they are searched in a DETERMINISTIC order
    # so the resolution is reproducible -- the table's own insertion
    # order, which is the order bobby wrote them in.
    for prim in BobbysPrimitives.values():
        if word in prim.related:
            return prim
    raise KeyError("Unknown primitive: %s. It is in neither the table nor "
                   "any related set." % word)


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
            # THE RESOLVER, and not a table lookup -- and the reason is
            # the resolver's docstring: a related word IS bound by the
            # primitive set, and that is the whole point of the method.
            resolved.append(resolve_primitive(p))
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


# THE OLD SELF-TEST, and it is KEPT because it is a real measurement of
# the restore, and it is CALLED BY --check rather than by the import --
# because a module that prints when it is imported is a module nobody
# can import quietly.
def _old_self_test() -> None:
    print(f"the core primitives loaded: {primitive_count()}")
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


#: BOBBY'S FIFTEEN CORE PRIMITIVE VERBS, and the record of where they
#: come from is the vault's own: "see, make, work, care, love, know,
#: build, conduct, transfer" (from context 2.txt line 78) plus "cause,
#: go, stop, up, move, left" (Bobby's statement on 2026-09-12).
BOBBY_CORE_VERBS: Tuple[str, ...] = (
    "see", "make", "work", "care", "love", "know", "build", "conduct",
    "transfer", "cause", "go", "stop", "up", "move", "left",
)


def primitive_count() -> int:
    """HOW MANY PRIMITIVES, and it is MEASURED and not asserted."""
    return len(CORE_PRIMITIVES)


#: THE PATH, and it is walked up until `src/` is found -- AND THE PSB IS
#: IMPORTED AS A PACKAGE MEMBER, because `psb_primitives.py` has
#: `from .lexicon.ingest import embed_bag` at its line 204 and a bare
#: `import psb_primitives` raises ImportError: attempted relative
#: import with no known parent package.
#:
#: **AND THE SAME DEFECT AND THE SAME TWO-FORM FIX ARE DESCRIBED IN
#: `coding_operator_object.py`'s OWN DOCSTRING**, so this is a known
#: shape in this codebase and not a new one.
import os as _os
import sys as _sys

_SRC = None
for _up in range(1, 6):
    _cand = _os.path.abspath(_os.path.join(
        _os.path.dirname(_os.path.abspath(__file__)), *([".."] * _up)))
    if _os.path.isfile(_os.path.join(_cand, "constitutional",
                                     "psb_primitives.py")):
        _SRC = _cand
        break
if _SRC is not None and _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

def psb_admits(word: str) -> bool:
    """Does the CURRENT psb_primitives admit this word as a span?

    AND IT CALLS THE CURRENT MODULE, so this answer tracks the PSB
    rather than a copy of it.
    """
    try:
        from constitutional.psb_primitives import classify_span
    except Exception:                               # noqa: BLE001
        try:
            from .psb_primitives import classify_span   # type: ignore
        except Exception:                           # noqa: BLE001
            return False
    try:
        return classify_span(word).value != "other"
    except Exception:                               # noqa: BLE001
        return False


def core_verb_coverage() -> Dict[str, Dict[str, bool]]:
    """WHERE EACH OF BOBBY'S FIFTEEN LIVES, and the answer is measured
    against the live modules -- the current PSB and this registry.

    **AND THE THREE COLUMNS ARE: IN THE PSB'S SPAN CLASSIFIER, IN THIS
    REGISTRY, AND IN THE MLTR'S REGISTER.** And the union is what
    matters, because a word that is in one of the three IS bound.
    """
    out: Dict[str, Dict[str, bool]] = {}
    mltr_words = set()
    _reg = None
    for _mod in ("constitutional.mltr_register", "mltr_register"):
        try:
            _reg = __import__(_mod, fromlist=["REGISTER"])
            break
        except Exception:                           # noqa: BLE001
            continue
    if _reg is not None:
        for t in getattr(_reg, "REGISTER", ()):     # noqa: B007
            w = getattr(t, "word", None)
            if w:
                mltr_words.add(str(w).lower())
    for v in BOBBY_CORE_VERBS:
        out[v] = {
            "in_psb": psb_admits(v),
            "in_core": v in CORE_PRIMITIVES,
            "in_mltr": v in mltr_words,
        }
    return out


def coverage() -> Dict[str, object]:
    """THE COVERAGE, and it is a NUMBER and not a position."""
    cov = core_verb_coverage()
    bound = [v for v, c in cov.items() if c["in_psb"] or c["in_core"]
             or c["in_mltr"]]
    unbound = [v for v in cov if v not in bound]
    return {
        "the_total": len(cov),
        "the_bound": len(bound),
        "the_unbound": unbound,
        "the_detail": cov,
    }


def check() -> int:
    """Every one of bobby's fifteen must be bound by SOMETHING, and the
    composer must bind."""
    problems: List[str] = []
    cov = core_verb_coverage()
    for v, c in cov.items():
        if not (c["in_psb"] or c["in_core"] or c["in_mltr"]):
            problems.append("%s is in NO vocabulary" % v)
    # AND THE COMPOSER, because it is the engine and it was lost.
    try:
        composed = compose("see", "cause", "move")
        if composed is None:
            problems.append("compose() returned nothing")
    except Exception as exc:                        # noqa: BLE001
        problems.append("compose() raised: %r" % (exc,))
    # AND THE COMPOSITION PATH, because it is the generative half.
    try:
        path = find_composition_path("transfer")
        if path is None:
            problems.append("find_composition_path() found no path")
    except Exception as exc:                        # noqa: BLE001
        problems.append("find_composition_path() raised: %r" % (exc,))
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("   - %s" % p)
        return 1
    print("CLEAN -- %d primitives, %d of bobby's %d core verbs bound, "
          "the composer binds and the path is found"
          % (primitive_count(), len(cov), len(cov)))
    return 0


def main(argv: List[str]) -> int:
    if "--coverage" in argv:
        cov = coverage()
        print("BOBBY'S FIFTEEN CORE VERBS")
        print("=" * 74)
        print("  %-12s %-8s %-10s %-10s" % ("the verb", "in the PSB",
                                           "in the core", "in the MLTR"))
        for v, c in cov["the_detail"].items():
            print("  %-12s %-8s %-10s %-10s"
                  % (v, "yes" if c["in_psb"] else "no",
                     "yes" if c["in_core"] else "no",
                     "yes" if c["in_mltr"] else "no"))
        print("")
        print("  the bound:   %d of %d" % (cov["the_bound"], cov["the_total"]))
        print("  the unbound: %s" % (", ".join(cov["the_unbound"]) or "none"))
        return 0
    if "--check" in argv:
        return check()
    print("THE CORE VERBS -- %d primitives, %d categories"
          % (primitive_count(), len(PSBCategory)))
    for cat in PSBCategory:
        names = [str(getattr(p, 'symbol', None) or getattr(p, 'word', ''))
                 for p in CORE_PRIMITIVES.values() if p.category == cat]
        print("  %-12s %s" % (cat.value, ", ".join(names)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
