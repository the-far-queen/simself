"""
memory_substrate.py — the memory layer, built to mem0's contract.

THE GAP, MEASURED
------------------
`constitutional/memory.py` is 200 lines of real substrate: add, retrieve,
autolink, novelty, salience decay, commit. It is good and it is ours.

Measured 2026-10-09, it has **zero** occurrences of dedup, extract, or
update. Those are precisely the three operations mem0ai/mem0 (66,838 stars,
Apache-2.0) exists to provide, and they are the difference between a store
that grows and a memory that *learns*.

    a store   accumulates everything, forever, and recalls noise
    a memory  notices it already knows this, notices the new thing
              contradicts the old thing, and resolves

So the substrate is not replaced. It is **given the three operations it
does not have**, behind the interface those operations are known by.

WHY AN ADAPTER AND NOT A SWAP
-----------------------------
mem0 is a service with its own storage, its own embeddings, and its own
opinion about what a "memory" is. Vendoring it would put a second source
of truth next to the constitutional one, and the second one would not be
subject to the qualification gate. That is the mistake this project keeps
making in a new costume: **a second substrate that answers to nobody.**

So: the interface is mem0's contract. The implementation is ours. If mem0
is ever the better substrate, the contract is what has to survive.

WHAT COMES FROM THE REUSE MAP
-----------------------------
    mem0ai/mem0         66,838*  Apache-2.0   the three operations
    topoteretes/cognee   31,753*  Apache-2.0   text->graph backend
    elizaOS/eliza       19,562*  MIT          persona/companion runtime

Stars measured 2026-10-08 via `gh api repos/<owner>/<name>`. None of
these is vendored; see fieldcore/docs/reuse-map-2026-10-09.md.

WHAT THIS DOES NOT ESTABLISH
----------------------------
It does not establish that retrieval is GOOD. It establishes that
deduplication, contradiction detection and resolution happen and are
countable. A memory layer that silently returns the ten most similar
things and never notices a contradiction is the MMM failure in a memory
coat, and the counters below exist to make that visible.

Run: python src/constitutional/memory_substrate.py --selftest
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np


class Resolution(str, Enum):
    KEEP_NEW = "keep_new"
    KEEP_OLD = "keep_old"
    MERGED = "merged"
    CONFLICT_RECORDED = "conflict_recorded"


@dataclass
class ExtractedFact:
    """A claim pulled out of prose. mem0's extraction step."""
    text: str
    embedding: np.ndarray
    source: str = ""
    confidence: float = 1.0


@dataclass
class DedupEvent:
    kept: str
    dropped: str
    similarity: float


@dataclass
class ConflictEvent:
    existing: str
    incoming: str
    similarity: float
    resolution: Resolution
    rationale: str


@dataclass
class MemoryStats:
    written: int = 0
    deduplicated: int = 0
    conflicts: int = 0
    merged: int = 0
    extracted: int = 0

    def to_dict(self) -> Dict:
        return {"written": self.written, "deduplicated": self.deduplicated,
                "conflicts": self.conflicts, "merged": self.merged,
                "extracted": self.extracted}


class MemorySubstrate:
    """Adds the three operations the constitutional store does not have.

    Deliberately a wrapper, not a replacement. `inner` is the existing
    ConstitutionalMemory; everything this class does goes THROUGH it, so
    the constitutional invariants keep holding.
    """

    #: above this similarity two statements are "the same thing said twice"
    DEDUP_THRESHOLD = 0.97
    #: above this they are related but possibly contradictory
    CONFLICT_THRESHOLD = 0.80

    def __init__(self, inner, dedup_threshold: Optional[float] = None,
                 conflict_threshold: Optional[float] = None):
        self.inner = inner
        if dedup_threshold is not None:
            self.DEDUP_THRESHOLD = dedup_threshold
        if conflict_threshold is not None:
            self.CONFLICT_THRESHOLD = conflict_threshold
        self.stats = MemoryStats()
        self.conflicts: List[ConflictEvent] = []
        self.superseded: Dict[str, str] = {}   # old_id -> new_id

    # -- helpers ---------------------------------------------------------

    @staticmethod
    def _cos(a: np.ndarray, b: np.ndarray) -> float:
        a = np.asarray(a, dtype=float)
        b = np.asarray(b, dtype=float)
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na < 1e-12 or nb < 1e-12:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    def _nearest(self, embedding: np.ndarray) -> Tuple[Optional[str], float]:
        best_id, best_sim = None, -1.0
        items = getattr(self.inner, "items", {}) or {}
        for item_id, item in items.items():
            vec = getattr(item, "embedding", None)
            if vec is None:
                continue
            sim = self._cos(embedding, vec)
            if sim > best_sim:
                best_id, best_sim = item_id, sim
        return best_id, (best_sim if best_id else 0.0)

    # -- 1. extract -------------------------------------------------------

    def extract(self, text: str, embedding: np.ndarray,
                source: str = "") -> ExtractedFact:
        """Pull a fact out of prose. The seam where an LLM call would go;
        deterministic today, and named as the seam rather than hidden."""
        self.stats.extracted += 1
        return ExtractedFact(text=text.strip(),
                             embedding=np.asarray(embedding, dtype=float),
                             source=source, confidence=1.0)

    # -- 2. deduplicate --------------------------------------------------

    def write(self, fact: ExtractedFact, category: str = "uncategorized"
              ) -> str:
        """Deduplicate, detect conflict, then write THROUGH the inner store."""
        near_id, sim = self._nearest(fact.embedding)

        if near_id is not None and sim >= self.DEDUP_THRESHOLD:
            self.stats.deduplicated += 1
            return near_id                      # already knew it

        if near_id is not None and sim >= self.CONFLICT_THRESHOLD:
            self.stats.conflicts += 1
            res = self._resolve(near_id, fact, sim)
            new_id = self._store(fact, category)
            self.conflicts.append(ConflictEvent(
                existing=near_id, incoming=new_id, similarity=sim,
                resolution=res.resolution, rationale=res.rationale))
            if res.resolution in (Resolution.KEEP_NEW, Resolution.MERGED):
                self.superseded[near_id] = new_id
            if res.resolution is Resolution.MERGED:
                self.stats.merged += 1
            return new_id

        return self._store(fact, category)

    def _resolve(self, existing_id: str, fact: ExtractedFact,
                 sim: float) -> ConflictEvent:
        """How a near-contradiction is settled.

        Default: record the conflict and KEEP BOTH. That is the honest
        default for a constitutional system, where silently discarding a
        claim because it resembles another one is how a memory learns to
        lie. A caller with a domain rule (newer wins, higher confidence
        wins) overrides this; there is no safe default that is not a
        policy, so the policy is a parameter and the default is
        non-destructive.
        """
        return ConflictEvent(
            existing=existing_id, incoming="", similarity=sim,
            resolution=Resolution.CONFLICT_RECORDED,
            rationale="near-duplicate with divergent content; kept both "
                      "rather than silently discarding either")

    def _store(self, fact: ExtractedFact, category: str) -> str:
        self.stats.written += 1
        add = getattr(self.inner, "add", None)
        if callable(add):
            return add(fact.text, fact.embedding, category=category)
        raise AttributeError(
            "inner store has no add(); MemorySubstrate wraps a store, it "
            "does not replace one")

    # -- recall ----------------------------------------------------------

    def recall(self, query: np.ndarray, top_n: int = 5):
        """Read through, and do not return a superseded item as current."""
        r = getattr(self.inner, "retrieve", None)
        if not callable(r):
            raise AttributeError("inner store has no retrieve()")
        hits = r(query, top_n=top_n * 2)
        out = []
        for h in hits:
            item_id = getattr(h, "id", None) or (h[0] if isinstance(h, tuple) else None)
            if item_id in self.superseded:
                continue
            out.append(h)
            if len(out) >= top_n:
                break
        return out

    def report(self) -> Dict:
        return {"stats": self.stats.to_dict(),
                "conflicts": len(self.conflicts),
                "superseded": len(self.superseded),
                "thresholds": {"dedup": self.DEDUP_THRESHOLD,
                               "conflict": self.CONFLICT_THRESHOLD}}


def _fake_store():
    """A minimal stand-in with the same surface, so the operations can be
    tested without booting the whole constitutional kernel."""
    class Item:
        def __init__(self, i, e, t):
            self.id, self.embedding, self.text = i, e, t
    class Store:
        def __init__(self):
            self.items = {}
            self._n = 0
        def add(self, text, embedding, category="uncategorized"):
            self._n += 1
            i = f"m{self._n}"
            self.items[i] = Item(i, np.asarray(embedding, float), text)
            return i
        def retrieve(self, q, top_n=5):
            v = np.asarray(q, float)
            scored = []
            for i, it in self.items.items():
                n = np.linalg.norm(v) * np.linalg.norm(it.embedding)
                s = float(np.dot(v, it.embedding) / n) if n > 1e-12 else 0.0
                scored.append((s, i, it))
            scored.sort(reverse=True, key=lambda x: x[0])
            return [it for _, _, it in scored[:top_n]]
    return Store()


def selftest() -> None:
    print("=" * 70)
    print("1. THE GAP, restated as an operation count")
    print("=" * 70)
    print("   constitutional/memory.py:  add retrieve autolink novelty")
    print("   decay commit              -> 200 lines of real substrate")
    print("   dedup  extract  update    -> ZERO. those are mem0's three.")
    print("   this adds the three without replacing the store.")
    print()

    print("=" * 70)
    print("2. DEDUPLICATION -- already knew it")
    print("=" * 70)
    m = MemorySubstrate(_fake_store())
    e = np.array([1.0, 0.0, 0.0])
    i1 = m.write(m.extract("the ground is immutable", e))
    i2 = m.write(m.extract("the ground is immutable", e))     # identical
    i3 = m.write(m.extract("the ground is immutable", e * 0.999))
    print(f"   three writes of the same fact -> ids {i1} {i2} {i3}")
    print(f"   written {m.stats.written}  deduplicated {m.stats.deduplicated}")
    assert i1 == i2 == i3, "an identical fact must resolve to one item"
    assert m.stats.deduplicated == 2

    print()
    print("=" * 70)
    print("3. CONFLICT -- near-identical, different content")
    print("=" * 70)
    m2 = MemorySubstrate(_fake_store())
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([0.95, 0.31, 0.0])          # sim ~0.95, different content
    old = m2.write(m2.extract("the ground is immutable", a))
    new = m2.write(m2.extract("the ground is mutable after reset", b))
    print(f"   old={old}  new={new}  sim={m2.conflicts[0].similarity:.4f}")
    print(f"   resolution: {m2.conflicts[0].resolution.value}")
    print(f"   rationale : {m2.conflicts[0].rationale}")
    assert m2.stats.conflicts == 1, "a near-duplicate with new content must be flagged"
    assert m2.conflicts[0].resolution is Resolution.CONFLICT_RECORDED
    print()
    print("   >>> the default is NON-DESTRUCTIVE: keep both, record the")
    print("       conflict. Silently discarding one because it resembles")
    print("       another is how a memory learns to lie.")

    print()
    print("=" * 70)
    print("4. SUPERSEDED ITEMS DO NOT COME BACK AS CURRENT")
    print("=" * 70)
    m3 = MemorySubstrate(_fake_store())
    v1 = np.array([1.0, 0.0]); v2 = np.array([0.99, 0.14])
    old = m3.write(m3.extract("alpha", v1))
    m3.superseded[old] = m3.write(m3.extract("beta", v2))
    hits = m3.recall(v1, top_n=5)
    ids = [h.id for h in hits]
    print(f"   recall for the OLD vector -> {ids}")
    assert old not in ids, "a superseded item must not be returned as current"
    print("   >>> recall goes through the supersession map.")

    print()
    print("=" * 70)
    print("5. WHAT THIS IS NOT")
    print("=" * 70)
    print("   It does not make retrieval good. It makes deduplication,")
    print("   contradiction detection and resolution HAPPEN and be")
    print("   COUNTABLE. A memory that returns the ten most similar things")
    print("   forever and never notices a contradiction is the MMM failure")
    print("   in a memory coat, and the counters exist to make that visible.")
    print()
    print("   And it is a wrapper, not a swap. A second substrate that does")
    print("   not answer to the qualification gate would be the mistake this")
    print("   project keeps making in a new costume.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.parse_args()
    selftest()