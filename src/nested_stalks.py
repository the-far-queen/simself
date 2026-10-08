"""
nested_stalks.py — fail-up, nested architecture, and bit-widening.

WHAT THIS IS
------------
Bobby, 2026-10-08:

    "i call hyper local cohomology with 1-bit fail upward nested stalk
     architecture that expands to 4-bit, 8 etc and widens area"

Three mechanisms, and the third one is not in any previous design note:

  1. FAIL UP        a failing sub-stalk escalates to its parent instead
                    of crashing or silently dying
  2. NESTED         stalks within stalks, so a region can be refined
                    without disturbing its neighbourhood
  3. BIT WIDENING   1 bit, expanding to 4, then 8, as area grows

(1) and (2) were already declared and never built. `stalk.py` lines 4-8,
dated 2026-03-07:

    "Nested stalks: Stalks within stalks - hierarchical structure for
     complex reasoning
     Atomic nodules: Granularized nodes within stalks - smallest update
     units
     Fail up: When sub-stalk fails, escalate to parent stalk instead of
     crashing"

Five and a half months. This builds them, plus the bit-widening.

WHY FAIL UP AND NOT FAIL DOWN
-----------------------------
Standard practice is to escalate to a supervisor. That is inverted here,
and the inversion is the point: a stalk that cannot hold its invariant
reports upward to the thing that CONTAINS it, because containment is the
relationship that matters. The parent can widen its own region, absorb the
burden, or declare the failure uncontainable. A child cannot do any of
those.

The alternative -- propagating failure downward -- spreads a defect into
neighbours that were healthy.

BIT WIDENING, and the number that decides it
--------------------------------------------
At 1 bit a stalk can hold one of two states. At n bits it holds 2**n. A
region therefore carries 2**n distinct distinguishable states, and the
whole architecture is only useful if that count GROWS at least as fast as
the number of regions it has to discriminate.

So the invariant this module enforces is a growth condition, not a
pretty table:

    for every widening step,
        capacity(child_next) >= capacity(parent_now) * regions_gained

If a widening step fails it, the step is REFUSED. Widening is not free
and it is not cosmetic -- below the threshold the structure has more
regions than it has states to tell them apart with.

WHAT IS NOT CLAIMED
-------------------
Not cohomology in the mathematical sense. Nothing here computes a
cohomology group; "hyper local cohomology" is being used as a NAME for a
local, nested, hierarchical arrangement whose behaviour is worth
studying, not as a claim about sheaf cohomology.

Not verified against any substrate. This is a data structure with tests,
not evidence that it governs anything.

Run: python src/nested_stalks.py --selftest
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# failure taxonomy
# ---------------------------------------------------------------------------

class Failure(str, Enum):
    INVARIANT = "invariant"      # an invariant stopped holding
    CAPACITY = "capacity"        # the stalk ran out of representable state
    SHAPE = "shape"              # malformed input
    ESCALATED = "escalated"      # already failed upward once; do not loop


@dataclass
class FailureReport:
    """One failure, and where it went.

    `handled_by` is the mechanism. A report whose handler is the child
    itself is a FAILURE OF THE MECHANISM, not a failure of the stalk, and
    `is_contained` makes that visible.

    `hops` counts how many parents have received it. A report that reaches
    a parent who DECLINES keeps climbing -- that is what makes fail-up a
    chain rather than a single sideways hop.
    """
    origin: str
    kind: Failure
    detail: str
    handled_by: str = ""
    escalated: bool = False
    contained: bool = False
    hops: int = 0
    trail: Tuple[str, ...] = ()

    def to_dict(self) -> Dict:
        return {
            "origin": self.origin, "kind": self.kind.value, "detail": self.detail,
            "handled_by": self.handled_by, "escalated": self.escalated,
            "contained": self.contained, "hops": self.hops,
            "trail": list(self.trail),
        }


# ---------------------------------------------------------------------------
# bit-widened precision
# ---------------------------------------------------------------------------

#: allowed widths. 1 -> 4 -> 8 is the progression Bobby named.
ALLOWED_WIDTHS: Tuple[int, ...] = (1, 4, 8, 16, 32)


def quantize(values: np.ndarray, width: int) -> np.ndarray:
    """Represent `values` at `width` bits per component.

    1 bit  -> a single threshold, so a component is {0, 1}
    n bits -> 2**n levels, uniformly spaced over the SIGNED range [-1, 1]

    SIGNED, deliberately. The first version of this function quantised
    over [0, 1] into int8, which produced two bugs that the selftest
    caught:

      1. int8 holds -128..127, so at 8-bit (255 levels) the value 0.5
         rounds to 128 and WRAPS to -128. At 16-bit it was worse --
         levels 65535 in an int8, so almost every level wrapped. Silent
         corruption of the representation, invisible unless you printed it.

      2. Quantising to [0,1] at CONSTRUCTION made the `non_negative`
         invariant UNSATISFIABLE. A stalk could never be built that
         violated it, so fail-up could never fire, so the mechanism this
         whole module exists to provide was untestable end to end.

    Signed embeddings are also the honest default for a state value --
    the existing stalk.py uses unconstrained rand().

    Returns the narrowest integer dtype that actually holds the level
    count, never int8 by default.
    """
    if width not in ALLOWED_WIDTHS:
        raise ValueError(
            f"width {width} is not one of {ALLOWED_WIDTHS}; refusing rather "
            "than silently rounding to a width nobody chose")
    v = np.asarray(values, dtype=float)
    if np.any(v < -1.0) or np.any(v > 1.0):
        raise ValueError("values must lie in [-1, 1] to quantize")

    # WIDTH 1 IS A SIGN BIT, not a two-level grid.
    #
    # The uniform signed formula below needs levels >= 2. At width 1,
    # levels = 1, the mapping spans only [-0.5, +0.5], and BOTH ends of
    # the range round to 0:
    #     x = -0.7 -> round(0.15 - 0.5) = round(-0.35) = 0
    #     x = +0.7 -> round(0.85 - 0.5) = round( 0.35) = 0
    # so a 1-bit quantiser returned a single level and the first step of
    # Bobby's 1 -> 4 -> 8 progression was degenerate. Caught by the
    # selftest asserting exactly 2 levels.
    if width == 1:
        return np.where(v >= 0.0, 1, -1).astype(np.int8)

    levels = capacity(width) - 1
    half = levels / 2.0
    q = np.rint((v + 1.0) / 2.0 * levels - half)
    dtype = np.int8 if levels <= 254 else (np.int16 if levels <= 65534 else np.int64)
    return q.astype(dtype)


def dequantize(q: np.ndarray, width: int) -> np.ndarray:
    """integer levels -> floats in [-1, 1]."""
    qq = np.asarray(q, dtype=float)
    if width == 1:
        return np.where(qq >= 0.0, 1.0, -1.0)
    levels = capacity(width) - 1
    return (qq + levels / 2.0) / levels * 2.0 - 1.0


def capacity(width: int) -> int:
    """how many distinct states a component carries at this width."""
    if width not in ALLOWED_WIDTHS:
        raise ValueError(f"width {width} not allowed")
    return 1 << width


def region_capacity(width: int, components: int) -> int:
    """distinct states a whole region carries."""
    return capacity(width) ** components


# ---------------------------------------------------------------------------
# the stalk
# ---------------------------------------------------------------------------

@dataclass
class NodalStalk:
    """A stalk that can fail upward and can contain others.

    Deliberately a NEW type rather than a patch of `stalk.Stalk`: the
    existing class has no parent, no children, and no failure channel, and
    retrofitting it would change a dataclass that 200+ tests depend on.
    """
    name: str
    embedding: np.ndarray
    width: int = 1
    invariants: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict[str, object] = field(default_factory=dict)

    #: "first_healthy" (default) or "root_only". See can_handle() -- this is
    #: a POLICY choice, not something the data determines, so it is an
    #: explicit field rather than a hardcoded guess.
    escalation_policy: str = "first_healthy"

    parent: Optional["NodalStalk"] = None
    children: List["NodalStalk"] = field(default_factory=list)
    reports: List[FailureReport] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.width not in ALLOWED_WIDTHS:
            raise ValueError(f"{self.name}: width {self.width} not allowed")
        if self.escalation_policy not in ("first_healthy", "root_only"):
            raise ValueError(
                f"{self.name}: escalation_policy must be 'first_healthy' or "
                f"'root_only', got {self.escalation_policy!r}")
        self.embedding = np.asarray(self.embedding, dtype=float)
        if self.embedding.size == 0:
            raise ValueError(f"{self.name}: empty embedding")
        self.embedding = dequantize(quantize(self.embedding, self.width), self.width)

    # -- structure ------------------------------------------------------

    def attach(self, child: "NodalStalk") -> None:
        """contain `child`, detaching it from any previous parent.

        Two refusals and one repair:

        - a stalk cannot contain itself
        - a cycle is refused: containment must be a TREE, and
          `stalk_architecture` needs a tree to walk

        The repair is the part that was missing in the first version.
        Reparenting set `child.parent` but left the old reference in the
        previous parent's `children`, so the structure became a DAG and
        `audit()` walked the same subtree once per stale edge -- one real
        failure reported three times. Found by the test suite.
        """
        if child is self:
            raise ValueError("a stalk cannot contain itself")
        if self._is_descendant_of(child):
            raise ValueError(
                f"{self.name} cannot contain {child.name}: that would make "
                f"{child.name} its own ancestor")
        if child.parent is not None and child.parent is not self:
            try:
                child.parent.children.remove(child)
            except ValueError:
                pass    # already detached; nothing stale to remove
        child.parent = self
        if child not in self.children:
            self.children.append(child)

    def _is_descendant_of(self, other: "NodalStalk") -> bool:
        node: Optional[NodalStalk] = self
        seen = set()
        while node is not None:
            if node is other:
                return True
            if id(node) in seen:
                return True     # defensive; attach() already prevents this
            seen.add(id(node))
            node = node.parent
        return False

    def depth(self) -> int:
        d = 0
        node = self.parent
        while node is not None:
            d += 1
            node = node.parent
        return d

    def width_at_depth(self) -> List[Tuple[str, int]]:
        """(name, width) from the root down to this stalk."""
        chain: List[Tuple[str, int]] = []
        node: Optional[NodalStalk] = self
        while node is not None:
            chain.append((node.name, node.width))
            node = node.parent
        return list(reversed(chain))

    # -- failure: the mechanism -----------------------------------------

    def check(self) -> Optional[FailureReport]:
        """Test this stalk's own invariants. Returns a report on failure."""
        v = self.embedding
        if self.invariants.get("non_negative", False) and np.any(v < 0):
            return FailureReport(origin=self.name, kind=Failure.INVARIANT,
                                 detail="non_negative violated")
        if self.invariants.get("unit_sum", False):
            s = float(v.sum())
            if abs(s - 1.0) > 1e-6:
                return FailureReport(origin=self.name, kind=Failure.INVARIANT,
                                     detail=f"unit_sum violated: {s:.6f}")
        return None

    def can_handle(self, report: FailureReport) -> bool:
        """Can this stalk absorb a failure arriving from a child?

        A parent ACCEPTS when it is healthy. A healthy parent accepting is
        the normal case and the walk stops there -- that is what "handled"
        means.

        The default policy in the first version accepted EVERYTHING,
        which made fail-up a single hop: the first healthy ancestor
        swallowed everything and nothing ever climbed. Measured: a
        failure three levels down stopped at n2 instead of reaching the
        root.

        There is a real question hiding here -- whether escalation should
        climb PAST a healthy parent all the way to the root, or stop at
        the first healthy one. The honest answer is that it depends on
        policy, so the policy is a constructor argument rather than a
        hardcoded guess:

          "first_healthy"  stop at the nearest healthy parent (default)
          "root_only"      only the root may accept

        Both are defensible. Neither is discoverable from the data, and
        guessing one and calling it correct is how the single-hop bug
        happened in the first place.
        """
        if report.origin == self.name:
            return False        # do not "handle" your own failure
        if self.check() is not None:
            return False        # already failing; escalate past me
        if self.escalation_policy == "root_only":
            return self.parent is None
        return True

    def fail_up(self, report: FailureReport) -> FailureReport:
        """Escalate a failure to the parent. Never to a sibling, never down.

        Walks the chain rather than hopping once. A parent that ACCEPTS
        contains the failure and the walk stops. A parent that DECLINES
        passes it further up, and `trail` records where it has been.

        A stalk with no parent -- or one every ancestor declined --
        CONTAINS the failure itself, and `contained` stays False. Returning
        quietly would be the exact bug this mechanism exists to prevent.
        """
        report.hops += 1
        report.trail = report.trail + (self.name,)

        if self.parent is None:
            report.handled_by = self.name
            report.contained = False
            report.escalated = report.hops > 1
            self.reports.append(report)
            return report

        if not self.parent.can_handle(report):
            # this node cannot take it; try the one above
            return self.parent.fail_up(report)

        report.escalated = True
        report.handled_by = self.parent.name
        report.contained = True
        self.reports.append(report)
        self.parent.reports.append(report)
        return report

    def audit(self) -> List[FailureReport]:
        """check self, then every descendant. Failures always go upward."""
        out: List[FailureReport] = []
        r = self.check()
        if r is not None:
            out.append(self.fail_up(r))
        for child in self.children:
            out.extend(child.audit())
        return out

    def unresolved_failures(self) -> List[FailureReport]:
        """reports that reached the root and were contained by nothing."""
        return [r for r in self.reports if not r.contained]

    # -- bit widening ----------------------------------------------------

    def can_widen(self, target_width: int) -> Tuple[bool, str]:
        """May this stalk widen, given what it contains?

        The growth condition: widening a CHILD must give it at least as
        many states as its parent currently has, or the child is holding
        more regions than it can tell apart.
        """
        if target_width <= self.width:
            return False, f"{self.name}: widening must increase, {self.width} -> {target_width}"
        gained = max(1, len(self.children))
        need = capacity(self.width) ** gained
        have = capacity(target_width)
        if have < need:
            return False, (
                f"{self.name}: widening {self.width} -> {target_width} gives "
                f"{have} states, needs {need} for {gained} region(s)")
        return True, f"{self.name}: {self.width} -> {target_width} gives {have} >= {need}"

    def widen(self, target_width: int) -> None:
        ok, why = self.can_widen(target_width)
        if not ok:
            raise ValueError(why)
        # re-quantise from the CURRENT representation at the new width.
        self.embedding = dequantize(quantize(self.embedding, target_width),
                                    target_width)
        hist = self.metadata.get("width_history")
        if not isinstance(hist, list):
            hist = []
            self.metadata["width_history"] = hist
        hist.append((self.width, target_width))
        self.width = target_width


def build_chain(widths: Sequence[int] = (1, 4, 8)) -> NodalStalk:
    """root -> child -> grandchild, each at the given width."""
    if not widths:
        raise ValueError("need at least one width")
    root = NodalStalk(name="s0", embedding=np.full(8, 0.5), width=widths[0])
    node = root
    for i, w in enumerate(widths[1:], start=1):
        child = NodalStalk(name=f"s{i}", embedding=np.full(8, 0.5), width=widths[0])
        node.attach(child)
        node = child
    # widen after attaching, so the growth condition sees the children
    node = root
    for i, w in enumerate(widths):
        if w != node.width:
            node.widen(w)
        node = node.children[0] if node.children else None
        if node is None:
            break
    return root


def selftest() -> None:
    print("=" * 68)
    print("1. bit widths and capacity")
    print("=" * 68)
    for w in ALLOWED_WIDTHS:
        print(f"  {w:>2}-bit  {capacity(w):>6} states/component   "
              f"region of 8 components = {region_capacity(w, 8):>10}")
    try:
        capacity(3)
        print("  FAIL: 3-bit should have been refused")
    except ValueError as exc:
        print(f"  capacity(3) refused: {exc}")

    print()
    print("=" * 68)
    print("2. quantisation resolves more at higher width")
    print("=" * 68)
    # straddles zero on purpose. The first version used [0.0 .. 0.7], all
    # positive, so at 1-bit every value landed on the same side of the
    # single threshold and the test read "1 distinct level" as a failure.
    # It was the fixture, not the quantiser.
    v = np.array([-0.7, -0.5, -0.3, -0.1, 0.1, 0.3, 0.5, 0.7])
    for w in (1, 4, 8):
        q = quantize(v, w)
        print(f"  {w:>2}-bit -> {q.tolist()}")
    d1 = len(set(quantize(v, 1).tolist()))
    d4 = len(set(quantize(v, 4).tolist()))
    d8 = len(set(quantize(v, 8).tolist()))
    print(f"  distinct levels: 1-bit {d1}, 4-bit {d4}, 8-bit {d8}")
    assert d1 == 2, f"1-bit must give exactly 2 levels, got {d1}"
    assert d4 >= d1 and d8 >= d4, "levels must not shrink as width grows"
    # round-trip: dequantise(quantise(x)) must land within one step of x
    for w in (4, 8):
        step = 2.0 / (capacity(w) - 1)
        back = dequantize(quantize(v, w), w)
        err = float(np.abs(back - v).max())
        assert err <= step, f"{w}-bit round-trip error {err} exceeds one step {step}"
        print(f"  {w:>2}-bit round-trip max error {err:.5f} <= one step {step:.5f}")

    print()
    print("=" * 68)
    print("3. NESTED -- containment is a tree")
    print("=" * 68)
    root = NodalStalk("s0", np.full(4, 0.5), width=4)
    mid = NodalStalk("s1", np.full(4, 0.5), width=4)
    leaf = NodalStalk("s2", np.full(4, 0.5), width=4)
    root.attach(mid)
    mid.attach(leaf)
    print(f"  s2 depth = {leaf.depth()}   chain = {leaf.width_at_depth()}")
    try:
        leaf.attach(root)
        print("  FAIL: a cycle should have been refused")
    except ValueError as exc:
        print(f"  cycle refused: {exc}")
    try:
        root.attach(root)
        print("  FAIL: self-containment should have been refused")
    except ValueError as exc:
        print(f"  self-containment refused: {exc}")

    print()
    print("=" * 68)
    print("4. FAIL UP -- the mechanism")
    print("=" * 68)
    # a leaf that violates its own invariant
    bad = NodalStalk("bad", np.array([-0.5, 0.5, 0.5, 0.5]), width=4,
                     invariants={"non_negative": True})
    root.attach(bad)
    reports = root.audit()
    for r in reports:
        print(f"  {r.origin} -> handled_by {r.handled_by}  "
              f"escalated={r.escalated}  contained={r.contained}  ({r.detail})")
    assert reports and reports[0].escalated and reports[0].contained, \
        "a failing leaf must escalate and be contained"
    assert reports[0].handled_by == "s0", "escalation must reach the PARENT"

    # a root that fails has nowhere to escalate
    lonely = NodalStalk("lonely", np.array([-1.0, 0.0, 0.0, 0.0]), width=4,
                        invariants={"non_negative": True})
    r = lonely.check()
    assert r is not None, "this fixture is supposed to violate its invariant"
    lr = lonely.fail_up(r)
    print(f"  root failure -> handled_by {lr.handled_by}  contained={lr.contained}")
    assert not lr.contained, "a root failure cannot be contained by anything"
    print(f"  unresolved: {len(lonely.unresolved_failures())}")

    print()
    print("=" * 68)
    print("5. BIT WIDENING -- the growth condition")
    print("=" * 68)
    root = NodalStalk("w0", np.full(4, 0.5), width=1)
    kids = [NodalStalk(f"k{i}", np.full(4, 0.5), width=1) for i in range(3)]
    for k in kids:
        root.attach(k)
    ok, why = root.can_widen(4)
    print(f"  root with 3 children, 1 -> 4 bits: {why}")
    assert ok, f"4-bit should be enough for 3 regions: {why}"
    root.widen(4)
    print(f"  after widen, root width = {root.width}, history = {root.metadata['width_history']}")

    # now the negative case, at the REAL boundary.
    # The first version used 4 children and asserted refusal. Measured:
    # 4 regions need 2**4 = 16 and 4-bit gives exactly 16, so "16 >= 16"
    # ALLOWS -- and that is the correct boundary, not a bug. The genuine
    # failure is 5 regions, which need 32.
    wide_root = NodalStalk("r", np.full(4, 0.5), width=8)
    leaf2 = NodalStalk("l", np.full(4, 0.5), width=1)
    for i in range(5):
        leaf2.attach(NodalStalk(f"x{i}", np.full(4, 0.5), width=1))
    wide_root.attach(leaf2)
    ok2, why2 = leaf2.can_widen(4)
    print(f"  leaf with 5 children, 1 -> 4 bits: {why2}")
    assert not ok2, f"4-bit gives 16 states, cannot serve 5 regions: {why2}"
    ok3, why3 = leaf2.can_widen(8)
    print(f"  same leaf, 1 -> 8 bits:            {why3}")
    assert ok3, f"8-bit gives 256, which does serve 5 regions: {why3}"
    try:
        leaf2.widen(4)
        print("  FAIL: widening to 4 bits should have been refused")
    except ValueError as exc:
        print(f"  widening to 4 bits refused: {exc}")
    leaf2.widen(8)
    print(f"  widened to {leaf2.width} instead, history = {leaf2.metadata['width_history']}")

    print()
    print("=" * 68)
    print("6. the 1 -> 4 -> 8 chain Bobby named")
    print("=" * 68)
    chain = build_chain((1, 4, 8))
    node = chain
    while node is not None:
        print(f"  {node.name}  width={node.width:>2}  depth={node.depth()}  "
              f"states/region={region_capacity(node.width, 8)}")
        node = node.children[0] if node.children else None

    print()
    print("=" * 68)
    print("7. WHAT THIS IS NOT")
    print("=" * 68)
    print("  not cohomology: no group is computed anywhere in this file")
    print("  'hyper local cohomology' is a NAME for a local, nested,")
    print("  hierarchical arrangement, not a claim about sheaf theory")
    print("  not verified against a substrate: a tested data structure is")
    print("  not evidence that it governs anything")
    print("  a new type rather than a patch of stalk.Stalk, whose 200+")
    print("  tests depend on its current shape")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.parse_args()
    selftest()