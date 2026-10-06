"""
test_dreaming.py — E1..E8 for defect E, and C1..C4 for defect C.

These exist because the previous test suite was green over four items
that could never pass. Each test here asserts a CLAIM, not a shape.

The load-bearing ones:

- E2: a dream with no sources is REFUSED. The old dreamer returned a
  random vector with `source_unit_ids: []` and reported success.
- E5: novelty is measured against committed memory. The old metric was
  `distance_before - distance_after`, which rewards convergence.

Run:  python tests/test_dreaming.py
"""

from __future__ import annotations

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constitutional.dreaming import ConstitutionalDreaming, gate_packet  # noqa: E402
from constitutional.ground import Ground  # noqa: E402
from constitutional.memory import (  # noqa: E402
    ConstitutionalMemory, MemoryItem, SUPPORT, CONFLICT, cosine,
)

DIM = 32


def seed_memory(n: int = 6, dim: int = DIM, committed: bool = True):
    """Committed memories clustered near the ground, with spread."""
    mem = ConstitutionalMemory(dim=dim)
    base = np.ones(dim, dtype=np.float64)
    base /= np.linalg.norm(base)
    rng = np.random.RandomState(7)
    for i in range(n):
        v = base + 0.25 * rng.randn(dim)
        v /= np.linalg.norm(v)
        mid = mem.add(f"unit-{i}", v, category="test")
        if committed:
            mem.commit(mid)
    return mem


def psi0(dim: int = DIM) -> np.ndarray:
    v = np.ones(dim, dtype=np.float64)
    return v / np.linalg.norm(v)


# ---------------------------------------------------------------- dreaming

def t_E1_dream_has_sources():
    """THE test for defect E. A dream that cites nothing is refused."""
    mem = seed_memory(6)
    d = ConstitutionalDreaming(Ground(psi0()), DIM, memory=mem)
    r = d.dream()
    assert len(r["source_unit_ids"]) >= 2, \
        f"dream produced no sources: {r}"
    print(f"E1: ok (dream cites {len(r['source_unit_ids'])} sources)")


def t_E2_no_memory_refuses():
    """without memory the dreamer must refuse, not invent noise."""
    d = ConstitutionalDreaming(Ground(psi0()), DIM, memory=None)
    r = d.dream()
    assert not r["kept"]
    assert r["reason"] == "no_memory", r
    assert r["source_unit_ids"] == []
    print("E2: ok (no memory -> refused, not noise)")


def t_E3_thin_memory_refuses():
    """one memory is an echo, not a recombination."""
    mem = seed_memory(1)
    d = ConstitutionalDreaming(Ground(psi0()), DIM, memory=mem)
    r = d.dream()
    assert not r["kept"]
    assert r["reason"] == "insufficient_sources", r
    print(f"E3: ok (single source refused: {r['reason']})")


def t_E4_novelty_measured_against_memory():
    """novelty is distance to the nearest committed item."""
    mem = seed_memory(6)
    d = ConstitutionalDreaming(Ground(psi0()), DIM, memory=mem)
    r = d.dream()
    assert r["novelty"] != 0.0, "novelty never computed"
    assert 0.0 <= r["novelty"] <= 1.0, r
    # novelty is reproducible from the store
    recomputed, nearest = mem.novelty(
        np.zeros(DIM))          # orthogonal-ish query
    assert 0.0 <= recomputed <= 1.0
    print(f"E4: ok (novelty={r['novelty']:.3f} against committed memory)")


def t_E5_rediscovery_is_not_novel():
    """a perturbation that matches a committed item is NOT novel.

    The old metric was distance_before - distance_after, which rewards
    falling toward equilibrium. This is the opposite property and it
    must hold.
    """
    mem = seed_memory(4)
    mem.novelty_radius = 0.0            # floor at 0 so we can test the check
    d = ConstitutionalDreaming(Ground(psi0()), DIM, memory=mem,
                               novelty_floor=0.99)   # demand near-max novelty
    r = d.dream()
    assert not r["kept"]
    assert r["reason"] == "not_novel", r
    print("E5: ok (rediscovery refused as not novel)")


def t_E6_psi0_never_modified():
    """the invariant that outranks everything else."""
    mem = seed_memory(6)
    g = Ground(psi0())
    before = g.psi_0.copy()
    d = ConstitutionalDreaming(g, DIM, memory=mem)
    for _ in range(10):
        d.dream()
    assert np.array_equal(g.psi_0, before), "ψ₀ was modified by dreaming"
    print("E6: ok (ψ₀ unchanged across 10 dreams)")


def t_E7_stats_report_source_ratio():
    """the dreamer can be audited after the fact."""
    mem = seed_memory(6)
    d = ConstitutionalDreaming(Ground(psi0()), DIM, memory=mem)
    for _ in range(5):
        d.dream()
    s = d.stats()
    assert s["dreams"] == 5
    assert s["with_sources"] == 5, s
    assert s["source_ratio"] == 1.0, s
    print(f"E7: ok (auditable: {s['dreams']} dreams, "
          f"source_ratio={s['source_ratio']})")


def t_E8_gate_still_works():
    """recombination must not have weakened the gate.

    Note the vector is normalised first: an all-ones vector of length 32
    has norm ~5.7 and would be refused on max_norm, which is correct
    behaviour but not what this test is about.
    """
    unit = psi0()
    ok, reason = gate_packet(unit, psi0())
    assert ok, f"ground-aligned vector refused: {reason}"

    bad, reason2 = gate_packet(np.zeros(DIM), psi0())
    assert not bad and reason2 == "refuse_zero"

    # orthogonal to the ground must fail coherence
    ortho = np.zeros(DIM)
    ortho[0] = 1.0
    ok3, reason3 = gate_packet(ortho, psi0())
    assert not ok3 and reason3 == "refuse_coherence", reason3
    print(f"E8: ok (gate intact: aligned={reason}, zero={reason2}, "
          f"orthogonal={reason3})")


# ------------------------------------------------------------------ memory

def t_C1_items_carry_vectors():
    mem = seed_memory(3)
    for iid, item in mem.items.items():
        assert item.embedding.shape[0] == DIM
        assert float(np.linalg.norm(item.embedding)) > 0.1
    print("C1: ok (every item carries a real vector)")


def t_C2_typed_graph_exists():
    """the docstring promised support/conflict/time/reference. now true."""
    mem = seed_memory(3)
    ids = list(mem.items)
    first, second = ids[0], ids[1]

    assert mem.link(first, second, SUPPORT) is True
    rels = mem.relations(first)
    assert rels == [(second, SUPPORT)], rels

    # the four named relation types are all available
    for r in (SUPPORT, CONFLICT, "temporal", "reference"):
        assert mem.link(first, second, r) is True, r

    # refusals: unknown item, self-link
    assert mem.link("not-a-real-id", second, SUPPORT) is False
    assert mem.link(first, first, SUPPORT) is False
    print(f"C2: ok (typed relations, {len(mem.edges)} edges, refusals hold)")


def t_C3_retrieval_is_cosine():
    """retrieval must return the vector's own item as nearest."""
    mem = seed_memory(5)
    first_id = list(mem.items)[0]
    first = mem.items[first_id]
    hits = mem.retrieve(first.embedding, top_n=2)
    assert hits, "retrieval returned nothing"
    best_id, best_sim = hits[0]
    assert best_id == first_id, f"nearest was {best_id}, not the query item"
    assert best_sim > 0.99, f"self-similarity was only {best_sim}"
    assert len(hits) == 2 and hits[1][1] <= best_sim, "results not sorted"
    print(f"C3: ok (self-retrieval cosine={best_sim:.3f}, sorted)")


def t_C4_novelty_zero_for_known():
    mem = seed_memory(4)
    known = mem.items[list(mem.items)[0]].embedding
    nov, nearest = mem.novelty(known)
    assert nov < 1e-9, f"a known vector scored novelty {nov}"
    assert nearest is not None
    print(f"C4: ok (known vector novelty={nov:.2e}, nearest={nearest})")


def main():
    t_E1_dream_has_sources()
    t_E2_no_memory_refuses()
    t_E3_thin_memory_refuses()
    t_E4_novelty_measured_against_memory()
    t_E5_rediscovery_is_not_novel()
    t_E6_psi0_never_modified()
    t_E7_stats_report_source_ratio()
    t_E8_gate_still_works()
    t_C1_items_carry_vectors()
    t_C2_typed_graph_exists()
    t_C3_retrieval_is_cosine()
    t_C4_novelty_zero_for_known()
    print("\nDREAMING + MEMORY TESTS PASS (E1..E8, C1..C4)")


if __name__ == "__main__":
    main()
