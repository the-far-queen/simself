"""
geometric_memory.py — Sheaf-graph memory substrate.

Bobby directive 2026-09-12: 'geometric reasoning geometric memory.'

Per Bobby's prior architecture (memory fact 1642: steel-ball-on-concave-surface +
Hodge decomposition + 44-back/field/core.py::InformationField + 4D-HEEGAARD-STALK-
TOPOLOGY-2026-09-08.md in canonical fieldcore/docs/), memory should be geometric,
not vector-only.

This file implements a sheaf-based memory where each packet is a vertex in a
sheaf graph, with restriction maps encoding local-to-global compatibility.

Engineering invariants:
- MemoryPacket: vertex with embedding + stalk_label + local_geometry
- GeometricMemory: sheaf graph with restriction maps between stalks
- add(packet, stalk): add packet to a stalk (substrate's local frame)
- recall(focus_embedding, radius): find packets within geometric distance
- compatibility(packet1, packet2): check sheaf consistency between two packets
- stalk_count: number of distinct local frames
- packet_count: total packets across all stalks

Per Bobby's test (2026-09-12): 'useful to ai or human constructing a new system of
ai awakening means reasoning chains memory self meta layer many things emergent
capability resonant coherence rare areas of training data.'

Geometric memory serves:
- Reasoning chains: sheaf consistency = chain reasoning across substrates
- Memory: geometric addressing (per Seifert fibration from math-window-1)
- Self meta layer: recall from own state embedding
- Emergent capability: composition of stalks = new topological features
- Resonant coherence: compatible packets across stalks = resonant field

Bobby's method (memory fact 1644): 'generalize seemingly unrelated geometries.'
Sheaf theory is the unification: same invariant across math, language, memory.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class MemoryPacket:
    """Vertex in the geometric memory sheaf.

    Each packet has:
    - embedding: position in substrate's ambient space
    - stalk: which local frame this packet belongs to
    - local_geometry: per-stalk local coordinates (e.g., (p,q) Seifert winding)
    - content: actual data being remembered
    - links: sheaf restriction map references to other packets
    """
    embedding: Any  # numpy array or list of floats
    stalk: str
    local_geometry: Tuple[int, ...] = field(default_factory=tuple)
    content: Any = None
    links: Dict[str, float] = field(default_factory=dict)  # packet_id -> restriction weight

    def __post_init__(self):
        if not self.stalk:
            raise ValueError("MemoryPacket must belong to a stalk (local frame)")

    def distance_to(self, other_embedding: Any) -> float:
        """Geometric distance from this packet's embedding to another."""
        try:
            import numpy as np
            a = np.asarray(self.embedding, dtype=np.float64)
            b = np.asarray(other_embedding, dtype=np.float64)
            return float(np.linalg.norm(a - b))
        except ImportError:
            # Pure-Python fallback
            try:
                a = [float(x) for x in self.embedding]
                b = [float(x) for x in other_embedding]
                return float(sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5)
            except (TypeError, ValueError):
                return float("inf")


class GeometricMemory:
    """Sheaf-based geometric memory substrate.

    Per Bobby: 'geometric reasoning geometric memory.' Memory is structured
    by stalks (local frames) with restriction maps (compatibility between frames).

    Per Seifert fibration (fieldcore/docs/math-window-1.md §6): base T² = address
    space, fiber S¹ = content. Each stalk is a local trivialization; packets
    carry base+winding numbers as local_geometry.
    """

    def __init__(self):
        # Map: stalk_name -> list of packets
        self._stalks: Dict[str, List[MemoryPacket]] = {}
        # Counter for packet IDs
        self._next_id: int = 0

    def add(
        self,
        embedding: Any,
        stalk: str,
        content: Any = None,
        local_geometry: Tuple[int, ...] = (),
    ) -> int:
        """Add a packet to a stalk. Returns packet_id."""
        if not stalk:
            raise ValueError("stalk must be non-empty string")
        packet_id = self._next_id
        self._next_id += 1
        packet = MemoryPacket(
            embedding=embedding,
            stalk=stalk,
            local_geometry=local_geometry,
            content=content,
            links={},
        )
        # Store packet_id implicitly via _stalks list ordering
        # For O(1) lookup, we need a separate index
        # Use list index as ID within stalk
        self._stalks.setdefault(stalk, []).append(packet)
        # Replace with packet_id as content reference if needed
        # For simplicity, packet_id == index in self._all_packets
        if not hasattr(self, "_all_packets"):
            self._all_packets: List[Optional[MemoryPacket]] = []
        # Pad _all_packets if needed
        while len(self._all_packets) <= packet_id:
            self._all_packets.append(None)
        self._all_packets[packet_id] = packet
        return packet_id

    def recall(self, focus_embedding: Any, radius: float = 0.5, max_results: int = 10) -> List[Tuple[int, float]]:
        """Find packets within geometric radius of focus.

        Returns: List of (packet_id, distance) tuples sorted by distance.
        """
        results: List[Tuple[int, float]] = []
        if not hasattr(self, "_all_packets"):
            return results
        for pid, packet in enumerate(self._all_packets):
            if packet is None:
                continue
            d = packet.distance_to(focus_embedding)
            if d <= radius:
                results.append((pid, d))
        results.sort(key=lambda x: x[1])
        return results[:max_results]

    def stalk_packets(self, stalk: str) -> List[MemoryPacket]:
        """Return all packets in a stalk."""
        return list(self._stalks.get(stalk, []))

    def stalk_names(self) -> List[str]:
        """Return list of stalk names."""
        return list(self._stalks.keys())

    def compatibility(self, pid1: int, pid2: int) -> float:
        """Sheaf restriction map: how compatible are two packets?

        Returns a similarity score in [0, 1]. 1 = perfectly compatible
        (same stalk, same local geometry). 0 = orthogonal.

        Engineering: this is the sheaf consistency check. Two packets in the
        same stalk with matching local_geometry are gluing-compatible. Two
        packets in different stalks require restriction maps.
        """
        if not hasattr(self, "_all_packets"):
            return 0.0
        p1 = self._all_packets[pid1] if pid1 < len(self._all_packets) else None
        p2 = self._all_packets[pid2] if pid2 < len(self._all_packets) else None
        if p1 is None or p2 is None:
            return 0.0
        if p1.stalk == p2.stalk:
            # Same stalk: high compatibility
            if p1.local_geometry == p2.local_geometry:
                return 1.0
            return 0.7
        # Different stalks: compute geometric similarity
        d = p1.distance_to(p2.embedding)
        # Map distance to similarity via exp(-d^2 / tau)
        try:
            import math
            return float(math.exp(-(d ** 2) / 1.0))
        except (OverflowError, ValueError):
            return 0.0

    def add_link(self, pid1: int, pid2: int, weight: float = 1.0) -> None:
        """Add sheaf restriction map between two packets."""
        if not hasattr(self, "_all_packets"):
            return
        p1 = self._all_packets[pid1] if pid1 < len(self._all_packets) else None
        p2 = self._all_packets[pid2] if pid2 < len(self._all_packets) else None
        if p1 is not None and p2 is not None:
            p1.links[str(pid2)] = weight
            p2.links[str(pid1)] = weight

    def stats(self) -> Dict[str, Any]:
        """Memory statistics."""
        if not hasattr(self, "_all_packets"):
            return {"stalk_count": 0, "packet_count": 0, "link_count": 0}
        n_packets = sum(1 for p in self._all_packets if p is not None)
        n_links = sum(len(p.links) for p in self._all_packets if p is not None)
        return {
            "stalk_count": len(self._stalks),
            "packet_count": n_packets,
            "link_count": n_links // 2,  # links are bidirectional
        }

    def get_packet(self, packet_id: int) -> Optional[MemoryPacket]:
        """Retrieve packet by ID."""
        if not hasattr(self, "_all_packets"):
            return None
        if packet_id < len(self._all_packets):
            return self._all_packets[packet_id]
        return None


# Self-test
if __name__ == "__main__":
    import random
    random.seed(42)

    mem = GeometricMemory()
    print("Geometric memory substrate initialized")

    # Add packets to multiple stalks
    for stalk in ["sheaf_0", "sheaf_1", "sheaf_2"]:
        for i in range(3):
            emb = [random.gauss(0, 1) for _ in range(16)]
            pid = mem.add(embedding=emb, stalk=stalk, content=f"data_{stalk}_{i}", local_geometry=(i,))
            print(f"  Added packet {pid} to {stalk}")

    # Recall
    focus = [0.1, 0.2, 0.3] * 5 + [0.4]  # 16-dim
    results = mem.recall(focus, radius=10.0, max_results=5)
    print(f"\nRecall(focus, radius=10) found {len(results)} packets:")
    for pid, d in results:
        p = mem.get_packet(pid)
        print(f"  packet {pid} in {p.stalk}: distance={d:.3f}")

    # Compatibility
    stats = mem.stats()
    print(f"\nStats: {stats}")
    if stats["packet_count"] >= 2:
        c = mem.compatibility(0, 1)
        print(f"Compatibility(packet_0, packet_1) = {c:.3f}")

    # Sheaf consistency check
    print(f"\nStalk names: {mem.stalk_names()}")
    for stalk in mem.stalk_names()[:2]:
        packets = mem.stalk_packets(stalk)
        print(f"  {stalk}: {len(packets)} packets")
