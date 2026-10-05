"""
test_axis_reactivity.py — starbeam pattern (wycats) tests.

the pattern: only re-evaluate cells whose dependencies changed.
the 8-axis constitutional graph + dirty propagation.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src" / "constitutional"))

from axis_reactivity import (  # noqa: E402
    AxisReactive, DependencyEdge, ReactiveGraph, build_constitutional_graph,
)


def test_r1_eight_axes():
    """the constitutional graph has exactly 8 axes."""
    g = build_constitutional_graph()
    assert len(g.axes) == 8
    print(f"R1: ok (8 axes)")


def test_r2_leaves_have_no_deps():
    """the sacred tier (boundaries, coherence, stability, authenticity) has no deps."""
    g = build_constitutional_graph()
    for name in ["boundaries", "coherence", "stability", "authenticity"]:
        assert g.axes[name].depends_on == ()
    print("R2: ok (4 leaves)")


def test_r3_routing_depends_on_coherence():
    """routing reads coherence."""
    g = build_constitutional_graph()
    assert g.axes["routing"].depends_on == ("coherence",)
    print("R3: ok (routing → coherence)")


def test_r4_dirty_propagates_to_dependents():
    """set coherence → routing becomes dirty (depends on coherence)."""
    g = build_constitutional_graph()
    g.flush()
    assert not g.axes["routing"].dirty
    g.set("coherence", 0.5)
    assert g.axes["routing"].dirty
    # but boundaries, stability are not dirty (they don't depend on coherence)
    assert not g.axes["boundaries"].dirty
    assert not g.axes["stability"].dirty
    print("R4: ok (coherence → routing dirty, others not)")


def test_r5_flush_recomputes_dirty_only():
    """after flush, all axes are clean."""
    g = build_constitutional_graph()
    g.flush()
    dirty = sum(1 for a in g.axes.values() if a.dirty)
    assert dirty == 0
    print("R5: ok (0 dirty after flush)")


def test_r6_setting_one_axis_only_dirties_its_chain():
    """changing boundaries only dirties recovery (recovery depends on boundaries)."""
    g = build_constitutional_graph()
    g.flush()
    g.set("boundaries", -0.3)
    assert g.axes["recovery"].dirty
    assert not g.axes["routing"].dirty  # routing depends on coherence, not boundaries
    assert not g.axes["norm"].dirty
    print("R6: ok (boundaries → recovery only)")


def test_r7_efficiency():
    """demonstrates the reactivity savings."""
    g = build_constitutional_graph()
    g.flush()
    # setting 'coherence' recomputes: routing, norm (and via routing), norm → 2-3 axes
    g.set("coherence", 0.7)
    affected = [n for n, a in g.axes.items() if a.dirty]
    assert len(affected) < len(g.axes), f"should not affect all: {affected}"
    print(f"R7: ok (changing 'coherence' affects {len(affected)}/8 axes: {affected})")


def test_r8_computation_chain():
    """the compute functions actually compose — routing reads coherence."""
    g = build_constitutional_graph()
    g.set("coherence", 0.5)
    g.flush()
    # routing = 0.5 * coherence = 0.25
    assert abs(g.axes["routing"].value - 0.25) < 1e-9, f"routing={g.axes['routing'].value}"
    print(f"R8: ok (routing computed: {g.axes['routing'].value})")


def main():
    test_r1_eight_axes()
    test_r2_leaves_have_no_deps()
    test_r3_routing_depends_on_coherence()
    test_r4_dirty_propagates_to_dependents()
    test_r5_flush_recomputes_dirty_only()
    test_r6_setting_one_axis_only_dirties_its_chain()
    test_r7_efficiency()
    test_r8_computation_chain()
    print("\\nALL AXIS_REACTIVITY TESTS PASS (R1..R8)")


if __name__ == "__main__":
    main()