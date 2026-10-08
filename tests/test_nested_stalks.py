"""
test_nested_stalks.py — fail up, nesting, and bit-widening.

BUILDS THE THING DECLARED FIVE AND A HALF MONTHS AGO.

`stalk.py` lines 4-8, dated 2026-03-07:

    "Nested stalks: Stalks within stalks - hierarchical structure for
     complex reasoning
     Atomic nodules: Granularized nodes within stalks - smallest update
     units
     Fail up: When sub-stalk fails, escalate to parent stalk instead of
     crashing"

Bobby named the third mechanism 2026-10-08, and it is not in that note:

    "i call hyper local cohomology with 1-bit fail upward nested stalk
     architecture that expands to 4-bit, 8 etc and widens area"

FOUR BUGS THIS SUITE LOCKS, all found by running the selftest:

  1. int8 WRAPPING. Levels were stored in int8 regardless of width. At
     8-bit (255 levels) the value 0.5 rounds to 128 and wraps to -128; at
     16-bit nearly every level wrapped. Silent corruption.
  2. `non_negative` was UNSATISFIABLE. Quantising to [0,1] at
     construction meant no stalk could ever be built that violated the
     invariant -- so fail-up could never fire and the whole mechanism was
     untestable end to end. Embeddings are now signed.
  3. 1-BIT WAS DEGENERATE. The uniform signed formula needs levels >= 2;
     at width 1 both ends of the range round to 0, so the first step of
     the 1 -> 4 -> 8 progression returned a single level. A 1-bit
     component is a SIGN.
  4. THE GROWTH BOUNDARY IS AT 5 REGIONS, NOT 4. 4 regions need 16 and
     4-bit gives exactly 16, so "16 >= 16" ALLOWS. An earlier check
     asserted refusal there; the check was wrong.

Run: python -m pytest tests/test_nested_stalks.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from nested_stalks import (  # noqa: E402
    ALLOWED_WIDTHS,
    Failure,
    NodalStalk,
    build_chain,
    capacity,
    dequantize,
    quantize,
    region_capacity,
)


def stalk(name="s", n=4, width=4, val=0.5, **kw):
    return NodalStalk(name=name, embedding=np.full(n, val), width=width, **kw)


# ---------------------------------------------------------------------------
# N1: bit widths
# ---------------------------------------------------------------------------

def test_n1_capacity_doubles_the_exponent():
    assert capacity(1) == 2
    assert capacity(4) == 16
    assert capacity(8) == 256
    assert capacity(16) == 65536


def test_n2_unlisted_width_is_refused():
    """3-bit is not on the progression. Rounding it to the nearest allowed
    width would be inventing a precision nobody chose."""
    with pytest.raises(ValueError, match="not allowed"):
        capacity(3)
    with pytest.raises(ValueError, match="not allowed"):
        stalk(width=3)


def test_n3_region_capacity_is_capacity_to_the_n():
    assert region_capacity(4, 8) == 16 ** 8


def test_n4_allowed_widths_are_the_progression_bobby_named():
    assert ALLOWED_WIDTHS[:3] == (1, 4, 8)


# ---------------------------------------------------------------------------
# N2: quantisation. three bugs live here.
# ---------------------------------------------------------------------------

def test_n5_one_bit_is_a_sign():
    """LOCKS BUG 3. Exactly two levels, and they are -1 and +1."""
    v = np.array([-0.9, -0.1, 0.0, 0.1, 0.9])
    q = quantize(v, 1)
    assert set(q.tolist()) == {-1, 1}
    assert len(set(q.tolist())) == 2


def test_n6_one_bit_round_trips_to_the_sign():
    back = dequantize(quantize(np.array([-0.9, 0.9]), 1), 1)
    assert np.allclose(back, [-1.0, 1.0])


def test_n7_quantisation_is_signed():
    """LOCKS BUG 2. Negative values must be representable, or the
    non_negative invariant can never be violated and fail-up never fires."""
    v = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
    assert quantize(v, 8).min() < 0, "signed input must survive"


def test_n8_storage_dtype_holds_the_level_count():
    """LOCKS BUG 1. int8 holds -128..127; 255 levels at 8-bit overflow it.
    The dtype must widen with the width or the representation corrupts."""
    for w in ALLOWED_WIDTHS:
        levels = capacity(w) - 1
        q = quantize(np.full(64, 0.5), w)
        assert q.max() <= levels, f"{w}-bit: max {q.max()} exceeds levels {levels}"
        assert np.iinfo(q.dtype).max >= levels, \
            f"{w}-bit: dtype {q.dtype} cannot hold {levels} levels"


def test_n9_no_wrapping_across_the_whole_range():
    """LOCKS BUG 1 concretely. At 8-bit the value 0.5 must NOT become -128."""
    q = quantize(np.full(16, 0.5), 8)
    assert np.all(q > 0), f"0.5 wrapped into non-positive levels: {q}"


def test_n10_distinct_levels_never_shrink():
    v = np.array([-0.7, -0.5, -0.3, -0.1, 0.1, 0.3, 0.5, 0.7])
    d = [len(set(quantize(v, w).tolist())) for w in (1, 4, 8)]
    assert d[0] == 2
    assert d[0] <= d[1] <= d[2], f"levels shrank as width grew: {d}"


def test_n11_round_trip_within_one_step():
    v = np.linspace(-1.0, 1.0, 33)
    for w in (4, 8, 16):
        step = 2.0 / (capacity(w) - 1)
        err = float(np.abs(dequantize(quantize(v, w), w) - v).max())
        assert err <= step, f"{w}-bit round-trip {err} > one step {step}"


def test_n12_out_of_range_is_refused():
    with pytest.raises(ValueError, match=r"\[-1, 1\]"):
        quantize(np.array([2.0]), 8)


def test_n13_empty_embedding_is_refused():
    with pytest.raises(ValueError, match="empty embedding"):
        NodalStalk(name="x", embedding=np.array([]), width=4)


# ---------------------------------------------------------------------------
# N3: nesting. containment is a tree.
# ---------------------------------------------------------------------------

def test_n14_depth_and_chain():
    root, mid, leaf = stalk("s0"), stalk("s1"), stalk("s2")
    root.attach(mid)
    mid.attach(leaf)
    assert leaf.depth() == 2
    assert root.depth() == 0
    assert [n for n, _ in leaf.width_at_depth()] == ["s0", "s1", "s2"]


def test_n15_self_containment_refused():
    s = stalk("x")
    with pytest.raises(ValueError, match="cannot contain itself"):
        s.attach(s)


def test_n16_cycles_refused():
    root, mid, leaf = stalk("s0"), stalk("s1"), stalk("s2")
    root.attach(mid)
    mid.attach(leaf)
    with pytest.raises(ValueError, match="own ancestor"):
        leaf.attach(root)


def test_n17_reparenting_moves_the_child():
    a, b, c = stalk("a"), stalk("b"), stalk("c")
    a.attach(c)
    b.attach(c)
    assert c.parent is b
    assert a.children == []


# ---------------------------------------------------------------------------
# N4: fail up. the mechanism this module exists for.
# ---------------------------------------------------------------------------

def test_n18_invariant_failure_escalates_to_the_parent():
    root = stalk("root")
    bad = NodalStalk("bad", np.array([-0.5, 0.5, 0.5, 0.5]), width=4,
                     invariants={"non_negative": True})
    root.attach(bad)
    reports = root.audit()
    assert reports, "audit found no failure"
    assert reports[0].escalated and reports[0].contained
    assert reports[0].handled_by == "root", "must reach the PARENT"


def test_n19_fail_up_reaches_the_immediate_parent():
    root, mid = stalk("root"), stalk("mid")
    leaf = NodalStalk("leaf", np.array([-0.5, 0.5]), width=4,
                       invariants={"non_negative": True})
    root.attach(mid)
    mid.attach(leaf)
    r = leaf.check()
    assert r is not None
    out = leaf.fail_up(r)
    assert out.handled_by == "mid", "escalation must stop at the nearest parent"


def test_n20_root_failure_is_not_contained():
    """A stalk with no parent has nowhere to escalate. Reporting itself as
    the handler with contained=True would be the exact silent-success bug
    this mechanism exists to prevent."""
    lonely = NodalStalk("lonely", np.array([-1.0, 0.0]), width=4,
                        invariants={"non_negative": True})
    r = lonely.check()
    assert r is not None
    out = lonely.fail_up(r)
    assert out.handled_by == "lonely"
    assert not out.contained, "a root failure cannot be contained"
    assert len(lonely.unresolved_failures()) == 1


def test_n21_healthy_tree_produces_no_reports():
    root, mid, leaf = stalk("r"), stalk("m"), stalk("l")
    root.attach(mid)
    mid.attach(leaf)
    assert root.audit() == [], "a healthy tree must be silent"


def test_n22_fail_up_walks_the_chain_when_policy_says_so():
    """Under the default `first_healthy` policy the nearest healthy parent
    accepts and the walk stops there -- that is the correct meaning of
    "handled", and measured hops confirm it: 1 hop, handled_by n2.

    The FIRST version of this test asserted the report reached the root,
    which the code did not do, and the code was wrong in a different way:
    `can_handle` accepted everything, so fail-up was a single sideways
    hop and nothing ever climbed. Both facts are now stated -- the
    default policy, and the root-climbing alternative -- because which
    one you want is a POLICY choice, not something the data decides.
    """
    root = stalk("root")
    node = root
    for i in range(3):
        nxt = stalk(f"n{i}")
        node.attach(nxt)
        node = nxt
    bad = NodalStalk("bad", np.array([-0.9, 0.0, 0.0, 0.0]), width=4,
                     invariants={"non_negative": True})
    node.attach(bad)
    reports = root.audit()
    assert len(reports) == 1, f"one failing node must give one report: {reports}"
    assert reports[0].handled_by == "n2", \
        f"first_healthy stops at the nearest healthy parent: {reports[0].handled_by}"
    assert reports[0].hops == 1, f"expected 1 hop, got {reports[0].hops}"
    assert reports[0].contained


def test_n22a_root_only_policy_climbs_to_the_root():
    """The same failure, under `root_only`: it climbs past every healthy
    intermediate parent and is contained by the root."""
    root = stalk("root", escalation_policy="root_only")
    node = root
    for i in range(3):
        nxt = stalk(f"n{i}", escalation_policy="root_only")
        node.attach(nxt)
        node = nxt
    bad = NodalStalk("bad", np.array([-0.9, 0.0, 0.0, 0.0]), width=4,
                     invariants={"non_negative": True},
                     escalation_policy="root_only")
    node.attach(bad)
    reports = root.audit()
    assert len(reports) == 1
    assert reports[0].handled_by == "root", \
        f"root_only must reach the root: {reports[0].handled_by}"
    assert reports[0].hops == 4, f"expected 4 hops, got {reports[0].hops}"
    # `trail` records where the report PASSED THROUGH. The root contains
    # it, so the root is handled_by but is NOT in the trail -- the last
    # node it climbed past is n0. Asserting trail[-1] == "root" was
    # off by one; measured, the trail is (bad, n2, n1, n0).
    assert reports[0].trail[-1] == "n0", \
        f"the report is contained at root, passing through n0: {reports[0].trail}"


def test_n22x_bad_policy_is_refused():
    with pytest.raises(ValueError, match="escalation_policy"):
        stalk("x", escalation_policy="whatever")


def test_n22b_a_declining_parent_passes_the_failure_up():
    """A parent whose OWN invariants are broken has no capacity to take
    responsibility for a second failure. It declines, and the walk
    continues above it."""
    root = stalk("root")
    broken = NodalStalk("broken", np.array([-0.9, 0.0, 0.0, 0.0]), width=4,
                        invariants={"non_negative": True})
    healthy = stalk("healthy")
    bad = NodalStalk("bad", np.array([-0.9, 0.0, 0.0, 0.0]), width=4,
                     invariants={"non_negative": True})
    root.attach(broken)
    root.attach(healthy)
    broken.attach(bad)

    reports = root.audit()
    handled_by = {r.origin: r.handled_by for r in reports}
    assert handled_by["bad"] == "root", \
        f"bad should skip the broken parent: {handled_by}"
    assert handled_by["broken"] == "root", \
        f"the root must contain its own failure too: {handled_by}"


def test_n23_unit_sum_invariant_fires():
    s = NodalStalk("s", np.array([0.9, 0.9, 0.9, 0.9]), width=8,
                   invariants={"unit_sum": True})
    r = s.check()
    assert r is not None
    assert r.kind is Failure.INVARIANT
    assert "unit_sum" in r.detail


# ---------------------------------------------------------------------------
# N5: bit widening and the growth condition
# ---------------------------------------------------------------------------

def test_n24_widen_requires_increase():
    s = stalk(width=4)
    ok, why = s.can_widen(4)
    assert not ok and "must increase" in why


def test_n25_three_regions_widen_to_four_bits():
    root = stalk("r", width=1)
    for i in range(3):
        root.attach(stalk(f"k{i}", width=1))
    ok, why = root.can_widen(4)
    assert ok, why
    root.widen(4)
    assert root.width == 4
    assert root.metadata["width_history"] == [(1, 4)]


def test_n26_four_regions_is_the_allow_boundary():
    """LOCKS BUG 4. 4 regions need 2**4 = 16; 4-bit gives exactly 16, so
    16 >= 16 ALLOWS. An earlier check asserted refusal here and was wrong."""
    root = stalk("r", width=1)
    for i in range(4):
        root.attach(stalk(f"k{i}", width=1))
    ok, why = root.can_widen(4)
    assert ok, f"16 >= 16 must ALLOW: {why}"


def test_n27_five_regions_cannot_widen_to_four_bits():
    """The genuine failure. 5 regions need 32; 4-bit gives 16."""
    root = stalk("r", width=1)
    leaf = stalk("l", width=1)
    for i in range(5):
        leaf.attach(stalk(f"x{i}", width=1))
    root.attach(leaf)
    ok, why = leaf.can_widen(4)
    assert not ok, f"4-bit gives 16, cannot serve 5 regions: {why}"
    with pytest.raises(ValueError, match="needs 32"):
        leaf.widen(4)
    ok8, why8 = leaf.can_widen(8)
    assert ok8, why8
    leaf.widen(8)
    assert leaf.width == 8


def test_n28_widening_preserves_the_value():
    v = np.array([0.3, -0.4, 0.9, -0.1])
    s = NodalStalk("s", v.copy(), width=4)
    before = s.embedding.copy()
    s.widen(8)
    assert s.width == 8
    assert float(np.abs(s.embedding - before).max()) < 0.1, \
        "widening must refine, not jump"


# ---------------------------------------------------------------------------
# N6: the chain Bobby named
# ---------------------------------------------------------------------------

def test_n29_chain_is_one_four_eight():
    root = build_chain((1, 4, 8))
    widths = [root.width, root.children[0].width, root.children[0].children[0].width]
    assert widths == [1, 4, 8]
    assert root.children[0].children[0].depth() == 2


def test_n30_chain_capacity_grows_at_every_step():
    root = build_chain((1, 4, 8))
    caps = [region_capacity(root.width, 8),
            region_capacity(root.children[0].width, 8),
            region_capacity(root.children[0].children[0].width, 8)]
    assert caps[0] < caps[1] < caps[2], f"capacity must widen: {caps}"


def test_n31_empty_widths_refused():
    with pytest.raises(ValueError, match="at least one width"):
        build_chain(())


# ---------------------------------------------------------------------------
# N7: the docstring's honesty clause
# ---------------------------------------------------------------------------

def test_n32_module_does_not_claim_cohomology():
    """'hyper local cohomology' is a NAME. Nothing here computes a group."""
    import nested_stalks as ns
    doc = ns.__doc__ or ""
    assert "Not cohomology" in doc or "not cohomology" in doc.lower()
    assert "NAME" in doc


def test_n33_module_states_it_is_unverified_against_substrate():
    import nested_stalks as ns
    doc = ns.__doc__ or ""
    assert "not verified against any substrate" in doc.lower()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))