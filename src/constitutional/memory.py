"""
memory.py — Relational memory with support / temporal / contradiction edges.

Replaces `HolographicMemory` from the v8.0-grok file. The original stored
memory as FFT-of-hash-projection and called it "holographic." That framing
borrowed prestige from physics-of-holography without the physics — FFT of a
hash bag is just FFT of a sparse random vector.

What we keep: the relational graph (support / temporal / contradiction
edges), exponential time-decay, salience tracking, access counts, FIFO
eviction by access count. These are real engineering.
"""
from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional

import numpy as np

from .constitution import cosine, embed_text


class RelationalMemory:
    """Bounded memory with relation graph, time decay, and salience tracking.

    Each entry is an (embedding, text, response, timestamp, access_count,
    salience, relations) record. Relations are categorized as:
    - support: cosine similarity > 0.72
    - temporal: adjacency in the store sequence
    - contradiction: cosine similarity < -0.15
    """

    def __init__(self, dim: int = 64, decay_rate: float = 0.008,
                 threshold: float = 0.28, max_entries: int = 220):
        self.dim = dim
        self.decay_rate = decay_rate
        self.threshold = threshold
        self.max_entries = max_entries
        self.entries: List[Dict[str, Any]] = []

    def store(self, text: str, response: str = "", context: Optional[str] = None,
              tags: Optional[List[str]] = None, vector: Optional[np.ndarray] = None) -> str:
        if vector is None:
            vector = embed_text(f"{text} {response} {context or ''}", self.dim)
        elif vector.shape[0] != self.dim:
            vector = np.resize(vector, self.dim)
        n = np.linalg.norm(vector)
        if n > 1e-9:
            vector = vector / n

        mid = f"m_{len(self.entries)}_{int(time.time()*1000)%100000}"

        relations = {"support": [], "temporal": [], "contradiction": []}
        for other in self.entries[-40:]:
            sim = cosine(vector, np.array(other["vector"]))
            if sim > 0.72:
                relations["support"].append(other["id"])
                other.setdefault("relations", {}).setdefault("support", []).append(mid)
            elif sim < -0.15:
                relations["contradiction"].append(other["id"])
                other.setdefault("relations", {}).setdefault("contradiction", []).append(mid)
        if self.entries:
            prev = self.entries[-1]
            relations["temporal"].append(prev["id"])
            prev.setdefault("relations", {}).setdefault("temporal", []).append(mid)

        # Duplicate detection by strong similarity
        for entry in self.entries:
            if cosine(vector, np.array(entry["vector"])) > 0.90:
                entry["access_count"] += 1
                entry["timestamp"] = time.time()
                return entry["id"]

        self.entries.append({
            "id": mid,
            "vector": vector.tolist(),
            "text": text[:220],
            "response": response[:220],
            "timestamp": time.time(),
            "access_count": 1,
            "tags": tags or [],
            "relations": relations,
            "salience": 0.5,
        })
        if len(self.entries) > self.max_entries:
            self.entries.sort(key=lambda x: x["access_count"])
            self.entries = self.entries[-self.max_entries:]
        return mid

    def retrieve(self, query: str, top_n: int = 5, hops: int = 1) -> List[Dict]:
        q_vec = embed_text(query, self.dim)
        n = np.linalg.norm(q_vec)
        if n > 1e-9:
            q_vec = q_vec / n
        now = time.time()
        scored = []
        for e in self.entries:
            sim = cosine(q_vec, np.array(e["vector"]))
            age = now - e["timestamp"]
            decay = math.exp(-age * self.decay_rate)
            score = 0.55 * sim * decay + 0.25 * e.get("salience", 0.5) + 0.20 * min(1.0, e["access_count"] / 5)
            if score > self.threshold:
                scored.append((score, e))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [e for _, e in scored[:top_n]]
        if hops > 0 and top:
            seen = {e["id"] for e in top}
            extra = []
            for e in top:
                for rel in ("support", "temporal"):
                    for rid in e.get("relations", {}).get(rel, [])[:3]:
                        if rid not in seen:
                            for cand in self.entries:
                                if cand["id"] == rid:
                                    extra.append(cand)
                                    seen.add(rid)
                                    break
            top.extend(extra[:top_n])
        return top[: top_n + 3]

    def decay_salience(self, rate: float = 0.015):
        """Apply salience decay across all entries. Called by SimSelf on periodic ticks."""
        for e in self.entries:
            e["salience"] = e.get("salience", 0.5) * (1.0 - rate)

    def clear(self):
        self.entries = []

    def stats(self) -> Dict:
        return {"total_entries": len(self.entries), "threshold": self.threshold, "type": "relational"}
