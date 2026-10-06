"""
memory.py — constitutional memory with vectors and a real graph.

Grok's 2026-08-08 review named this as defect C: "Memory stores first
200 chars of response. No semantic compression. No graph. No episodic
hierarchy. Memory will become flat." It also blocked defect E, because
dreaming cannot retrieve what has no representation.

This module's docstring claimed a "typed graph (support, conflict,
time, reference)". There was no graph. There are now four relation
types, which is what the docstring always described.

What changed:

- every item carries a real vector, so "nearest" means something
- four typed relations, established at write time
- retrieval by cosine
- `novelty()` — distance to the nearest committed item. This is the
  metric the old dreamer did not have, and the reason defect E was
  unfixable.

Memory is a store, not a flow. It does not modify ψ₀.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

DEFAULT_DIM = 64

# the four relations the docstring always claimed
SUPPORT = "support"
CONFLICT = "conflict"
TEMPORAL = "temporal"
REFERENCE = "reference"


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


@dataclass
class MemoryItem:
    id: str
    embedding: np.ndarray = field(
        default_factory=lambda: np.zeros(DEFAULT_DIM, dtype=np.float64))
    category: str = "uncategorized"
    committed: bool = False
    metadata: Dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    salience: float = 1.0
    # legacy field name, kept so existing callers do not break
    embedding_dim: int = DEFAULT_DIM


class ConstitutionalMemory:
    """Items, categories, and a typed graph. Does not touch ψ₀."""

    def __init__(self, dim: int = DEFAULT_DIM):
        self.dim = dim
        self.items: Dict[str, MemoryItem] = {}
        self.categories: Dict[str, List[str]] = {}
        # {(a, b, relation)} with a < b for undirected types
        self.edges: Set[Tuple[str, str, str]] = set()

    # ------------------------------------------------------------------
    # write
    # ------------------------------------------------------------------

    @staticmethod
    def make_id(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def link(self, a: str, b: str, relation: str = SUPPORT) -> bool:
        """Record a typed relation. Self-links are refused."""
        if a == b or a not in self.items or b not in self.items:
            return False
        lo, hi = sorted((a, b))
        self.edges.add((lo, hi, relation))
        return True

    def _autolink(self, item: MemoryItem, threshold: float) -> None:
        """Relate a new item to what it resembles. Similarity is support;
        opposition is conflict. Established at insert time so a later
        reader never has to reconstruct the relation."""
        for other_id, other in self.items.items():
            if other_id == item.id:
                continue
            c = cosine(item.embedding, other.embedding)
            if c >= threshold:
                self.link(item.id, other_id, SUPPORT)
            elif c <= -threshold:
                self.link(item.id, other_id, CONFLICT)

    def add_item(self, item: MemoryItem,
                 link_threshold: float = 0.6) -> str:
        if item.embedding.shape[0] != self.dim:
            raise ValueError(
                f"Memory: embedding dim {item.embedding.shape[0]} "
                f"!= store dim {self.dim}")
        self.items[item.id] = item
        self.categories.setdefault(item.category, []).append(item.id)
        self._autolink(item, link_threshold)
        return item.id

    def add(self, text: str, embedding, category: str = "uncategorized",
            **meta) -> str:
        return self.add_item(MemoryItem(
            id=self.make_id(text + category),
            embedding=np.asarray(embedding, dtype=np.float64),
            category=category,
            metadata=dict(meta, text=text),
        ))

    def commit(self, item_id: str) -> bool:
        """Mark durable. Only committed items count as prior art for
        novelty — uncommitted items are a dream's own output."""
        if item_id not in self.items:
            return False
        self.items[item_id].committed = True
        return True

    # ------------------------------------------------------------------
    # read
    # ------------------------------------------------------------------

    def get(self, item_id: str) -> Optional[MemoryItem]:
        return self.items.get(item_id)

    def by_category(self, category: str) -> List[str]:
        return list(self.categories.get(category, []))

    def retrieve(self, query, top_n: int = 5,
                 committed_only: bool = True) -> List[Tuple[str, float]]:
        """Nearest neighbours by cosine. Returns [(id, similarity)]."""
        q = np.asarray(query, dtype=np.float64)
        scored = []
        for iid, item in self.items.items():
            if committed_only and not item.committed:
                continue
            scored.append((iid, cosine(q, item.embedding)))
        scored.sort(key=lambda t: -t[1])
        return scored[:top_n]

    def relations(self, item_id: str,
                  relation: Optional[str] = None) -> List[Tuple[str, str]]:
        """[(other_id, relation)] for anything linked to item_id."""
        out = []
        for a, b, rel in self.edges:
            if relation is not None and rel != relation:
                continue
            if a == item_id:
                out.append((b, rel))
            elif b == item_id:
                out.append((a, rel))
        return out

    def novelty(self, vector) -> Tuple[float, Optional[str]]:
        """Distance to the nearest committed item.

        Returns (novelty, nearest_id). novelty == 0.0 means this has
        been seen before. 1.0 means nothing committed resembles it.
        **This is the metric the old flat memory could not supply, and
        the reason defect E was unfixable.**
        """
        v = np.asarray(vector, dtype=np.float64)
        best, best_id = -1.0, None
        for iid, item in self.items.items():
            if not item.committed:
                continue
            c = cosine(v, item.embedding)
            if c > best:
                best, best_id = c, iid
        if best_id is None:
            return (1.0, None)
        return (float(max(0.0, 1.0 - best)), best_id)

    def committed_count(self) -> int:
        return sum(1 for i in self.items.values() if i.committed)

    # ------------------------------------------------------------------
    # maintenance
    # ------------------------------------------------------------------

    def decay_salience(self, half_life_s: float = 86400.0) -> None:
        """Exponential decay by age. Does not modify ψ₀."""
        now = time.time()
        for item in self.items.values():
            age = max(0.0, now - item.timestamp)
            item.salience = float(0.5 ** (age / half_life_s))
