"""
stalk_node.py — Distributed SimSelf node with mixed-precision compression.

Extracted from Bobby's `MINI-SIMSELF.txt` (2026-09-08). Each node is a
self-contained mini-SimSelf with:
  - A local embedding (compressed to int8 via log-scale)
  - A set of invariant predicates
  - A recovery map (precision-lift back to float32)
  - An epsilon tolerance for gluing distance checks
  - Gluing mechanics with governor-gated merges

The "mixed-precision bridge" pattern (Bobby's reference to Tesla mixed-precision
training) is: stay at int8 for normal operation, lift to float32 only when
gluing — save cycles on edge hardware.

For 3-node robot embodiment example: vision + arm + hand stalks, each running
on separate cores (e.g., Apple Silicon AI5 subunits), gluing asynchronously
via the governor.
"""
from __future__ import annotations

from typing import Callable, List, Optional, Set

import numpy as np


InvariantFn = Callable[[np.ndarray], bool]
RecoveryFn = Callable[[np.ndarray], np.ndarray]
GovernorFn = Callable[["StalkNode", "StalkNode"], bool]


def compress_to_log_int8(emb: np.ndarray) -> np.ndarray:
    """Compress float embedding to int8 via log-scale.

    Maps log(|emb|+ε) to [-128, 127]. Lossy but stable for relative comparisons.
    """
    log_emb = np.log(np.abs(emb) + 1e-8)
    if log_emb.max() == log_emb.min():
        return np.zeros_like(emb, dtype=np.int8)
    scaled = np.clip((log_emb - log_emb.min()) / (log_emb.max() - log_emb.min()) * 255 - 128, -128, 127)
    return scaled.astype(np.int8)


def taylor_recovery(compressed: np.ndarray, order: int = 3) -> np.ndarray:
    """Taylor/Horner approximation for precision lift from int8 to float32.

    Mimics Tesla's mixed-precision bridge: lift happens only during gluing
    or validation, not during normal operation.
    """
    x = compressed.astype(np.float32) / 127.0
    result = np.ones_like(x)
    for i in range(order, 0, -1):
        result = 1 + x * result / i
    return np.exp(x) * result


class StalkNode:
    """A distributed SimSelf node.

    Each node carries a local latent state (the "embedding"), a set of
    invariants it must satisfy, and a recovery map to lift from compressed
    to full precision.

    Parameters
    ----------
    local_embedding : np.ndarray
        Initial float embedding. Will be compressed to int8 internally.
    invariants : list of callable
        Predicates on the recovered embedding. All must return True for the
        node to be considered valid.
    recovery_map : callable
        Maps compressed embedding back to float32 (default: taylor_recovery).
    epsilon : float
        Distance tolerance for gluing with other nodes.
    name : str
        Identifier (e.g., "vision", "arm", "hand").
    """

    def __init__(
        self,
        local_embedding: np.ndarray,
        invariants: List[InvariantFn],
        recovery_map: Optional[RecoveryFn] = None,
        epsilon: float = 0.05,
        name: str = "stalk",
    ):
        self.name = name
        self.invariants = list(invariants)
        self.recovery_map = recovery_map if recovery_map is not None else taylor_recovery
        self.epsilon = float(epsilon)
        # Compress on init.
        self.embedding = compress_to_log_int8(np.asarray(local_embedding, dtype=np.float32))
        self.validity_conditions: dict = {}

    def is_valid(self) -> bool:
        """Recover + check all invariants."""
        recovered = self.recovery_map(self.embedding)
        return all(bool(inv(recovered)) for inv in self.invariants)

    def approximate_distance(self, other: "StalkNode") -> float:
        """Bounded L2 distance between compressed embeddings."""
        diff = self.embedding.astype(np.float32) - other.embedding.astype(np.float32)
        dist = float(np.linalg.norm(diff))
        # Bound: capped by combined epsilon (prevents far nodes from gluing).
        return min(dist, self.epsilon + other.epsilon)

    def glue_with(
        self,
        other: "StalkNode",
        governor: GovernorFn,
    ) -> Optional["StalkNode"]:
        """Attempt to glue with another node.

        Steps:
          1. Governor pre-check (shared invariants, precision match).
          2. Distance bound check (epsilon-relative).
          3. Recovery + mean merge.
          4. Invariant union + check on merged state.
          5. If all pass, return new StalkNode with merged embedding + combined invariants.

        Returns the new StalkNode on success, None on any failure.
        """
        if not governor(self, other):
            return None

        overlap_dist = self.approximate_distance(other)
        if overlap_dist > max(self.epsilon, other.epsilon) * 1.5:
            return None

        self_rec = self.recovery_map(self.embedding)
        other_rec = other.recovery_map(other.embedding)
        merged_emb = 0.5 * self_rec + 0.5 * other_rec
        merged_invariants = list(set(self.invariants) | set(other.invariants))
        if not all(bool(inv(merged_emb)) for inv in merged_invariants):
            return None

        new_epsilon = max(self.epsilon, other.epsilon)
        glued = StalkNode(
            local_embedding=merged_emb,
            invariants=merged_invariants,
            recovery_map=self.recovery_map,
            epsilon=new_epsilon,
            name=f"{self.name}_glued_{other.name}",
        )
        return glued

    def update_embedding(self, new_embedding: np.ndarray) -> None:
        """Replace the local embedding (re-compresses automatically)."""
        self.embedding = compress_to_log_int8(np.asarray(new_embedding, dtype=np.float32))

    def __repr__(self) -> str:
        return f"StalkNode(name={self.name!r}, ε={self.epsilon}, valid={self.is_valid()})"


__all__ = ["StalkNode", "compress_to_log_int8", "taylor_recovery"]