"""
coherence.py — multi-vector coherence check across constitutional axes.

Per Bobby 2026-09-16 ("feature rich and you approve grab and use"):
ported the coherence check pattern from the v6.1 monolith (grok3.txt),
extended for the canonical SimSelf axis set (8 default axes per
constitution.py:DEFAULT_AXES).

A coherence check verifies that multiple input vectors (e.g. axis values,
proposed mutations, memory embeddings) do not contradict each other.
Returns a CoherenceScore with a value in [0.0, 1.0]:
- 1.0 = full agreement
- 0.0 = full contradiction
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CoherenceScore:
    """Result of a multi-vector coherence check."""

    value: float  # [0.0, 1.0]
    n_vectors: int
    pairs_compared: int
    contradictions: List[str] = field(default_factory=list)


def _cosine(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two equal-length vectors."""
    if len(a) != len(b):
        raise ValueError(f"length mismatch: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def check_coherence(
    vectors: Dict[str, List[float]],
    *,
    threshold: float = 0.6,
) -> CoherenceScore:
    """Check coherence across a set of named vectors.

    Args:
        vectors: dict of name -> vector. Vectors must be the same length.
        threshold: minimum cosine similarity for "consistent." Below this,
            the pair is reported as a contradiction.

    Returns:
        CoherenceScore with the average cosine similarity (mapped to [0,1])
        plus a list of contradiction descriptions.
    """
    names = list(vectors.keys())
    n = len(names)
    if n < 2:
        return CoherenceScore(value=1.0, n_vectors=n, pairs_compared=0)

    pairs = 0
    sim_sum = 0.0
    contradictions: List[str] = []
    for i in range(n):
        for j in range(i + 1, n):
            a_name, b_name = names[i], names[j]
            a, b = vectors[a_name], vectors[b_name]
            try:
                sim = _cosine(a, b)
            except ValueError:
                # Length mismatch — record as a contradiction.
                contradictions.append(
                    f"{a_name} (dim {len(a)}) vs {b_name} (dim {len(b)})"
                )
                continue
            pairs += 1
            sim_sum += sim
            if sim < threshold:
                contradictions.append(
                    f"{a_name} <-> {b_name}: cosine={sim:.2f} (< {threshold})"
                )

    if pairs == 0:
        avg_sim = 0.0
    else:
        avg_sim = sim_sum / pairs

    # Map cosine from [-1, 1] to [0, 1] (cosine -1 = contradictory, +1 = aligned).
    mapped = (avg_sim + 1.0) / 2.0
    return CoherenceScore(value=mapped, n_vectors=n, pairs_compared=pairs,
                         contradictions=contradictions)


def cross_axis_coherence(
    axis_values: Dict[str, float],
    *,
    weights: Optional[Dict[str, float]] = None,
) -> CoherenceScore:
    """Check coherence of axis values against each other.

    Each axis is treated as a 1-D vector (the value itself). Coherence
    is measured by the weighted average cosine similarity across all
    pairs. For 1-D vectors, cosine similarity reduces to sign agreement:
    - both positive or both negative → similarity = 1
    - one positive, one negative → similarity = -1

    This is a simple sanity check: do the axes agree in direction?
    """
    names = list(axis_values.keys())
    n = len(names)
    if n < 2:
        return CoherenceScore(value=1.0, n_vectors=n, pairs_compared=0)

    pairs = 0
    sim_sum = 0.0
    contradictions: List[str] = []
    for i in range(n):
        for j in range(i + 1, n):
            a_name, b_name = names[i], names[j]
            a = axis_values[a_name]
            b = axis_values[b_name]
            # 1-D cosine.
            sim = 1.0 if (a >= 0 and b >= 0) or (a <= 0 and b <= 0) else -1.0
            if a == 0 or b == 0:
                sim = 0.0
            pairs += 1
            sim_sum += sim
            if sim < 0:
                contradictions.append(
                    f"{a_name} ({a:.2f}) <-> {b_name} ({b:.2f}): opposing"
                )

    avg_sim = sim_sum / pairs if pairs > 0 else 0.0
    mapped = (avg_sim + 1.0) / 2.0
    return CoherenceScore(value=mapped, n_vectors=n, pairs_compared=pairs,
                         contradictions=contradictions)


__all__ = ["CoherenceScore", "check_coherence", "cross_axis_coherence"]
