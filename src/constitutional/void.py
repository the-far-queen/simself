"""
void.py — the void region as a teacher (defect F's sibling).

What "the void" is here, precisely, so nothing drifts into metaphor:

In the egg-toroid geometry the void is the region of the state space
that the dynamics cannot reach. The apex is high-curvature and stiff;
the base is where the system settles. The void is the *unreachable
interior* — a set of states with no trajectory to them.

Bobby's claim is that reaching for it is instructive. The engineering
reading, which is what this implements: **a proposal that projects onto
the void region is maximally distant from anything the system already
believes, so it carries more information than one that lands near
current state.** The void is where new structure has to come from.

So the mechanism is a *distance probe*, not an oracle:

    void_projection(x) = 1 - max over the void basis of |⟨x, v⟩|

Properties that make it a real module rather than a name:

- the void basis is a fixed, seeded orthogonal frame — deterministic,
  inspectable, and NOT random (a random probe is defect E again)
- `distance_to_void` is a genuine metric value in [0, 1]
- `void_lesson()` refuses when the proposal is not actually distant,
  so it cannot be used to rubber-stamp novelty
- **it cannot write ψ₀.** the void is consulted, never installed.

What it will not do: it will not claim to observe anything. It computes
a projection. The name is the tradition's; the arithmetic is ours, and
the two should be kept visible rather than blended.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

import numpy as np

# how many void directions to span. 4 gives a frame with a well-defined
# orthogonal complement in any dim >= 8, which every dim we use clears.
VOID_DIM = 4

# a proposal must be at least this far from the void frame to count as
# reaching into it. below that, it is ordinary state and we say so.
VOID_REACH = 0.30


def _seed_for(dim: int) -> int:
    """Deterministic seed from the dimension.

    Randomness here would make every measurement irreproducible, which is
    the exact failure the repo has already paid for twice.
    """
    return int(hashlib.sha256(f"void/{dim}".encode()).hexdigest()[:8], 16)


class VoidIntegration:
    """A distance probe into the unreachable region. Read-only."""

    def __init__(self, dim: int, void_dim: int = VOID_DIM):
        if void_dim >= dim:
            raise ValueError(
                f"VoidIntegration: void_dim {void_dim} must be < dim {dim}")
        self.dim = dim
        self.void_dim = void_dim
        self.frame = self._build_frame()
        # cached projection history, for the audit trail
        self.readings: List[Dict[str, Any]] = []

    def _build_frame(self) -> np.ndarray:
        """An orthonormal void basis, seeded and reproducible.

        Gram-Schmidt on a seeded Gaussian, so the frame is orthogonal but
        still an irregular basis of the void subspace.
        """
        rng = np.random.RandomState(_seed_for(self.dim))
        raw = rng.randn(self.dim, self.void_dim)
        q, _ = np.linalg.qr(raw)          # q is (dim, k), columns orthonormal
        # Store ROWS as the basis vectors, shape (k, dim). Then the
        # projector is B.T @ (B @ v) and B @ B.T == I_k, both of which
        # the tests assert. The earlier version kept (dim, k) and wrote
        # frame.T @ (frame @ v), which is a shape error - not a small one,
        # because it would have projected into the wrong subspace if the
        # shapes had happened to line up.
        B = q.T
        assert B.shape == (self.void_dim, self.dim), B.shape
        return B

    # ------------------------------------------------------------------
    # measurement
    # ------------------------------------------------------------------

    def project(self, vector) -> np.ndarray:
        """The component of `vector` that lies in the void subspace."""
        v = np.asarray(vector, dtype=np.float64).reshape(-1)
        if v.shape[0] != self.dim:
            raise ValueError(
                f"VoidIntegration.project: got length {v.shape[0]}, "
                f"expected {self.dim}")
        B = self.frame                       # (k, dim), rows are basis vectors
        return B.T @ (B @ v)                 # (dim,k)@(k,dim)->(dim,)

    def distance_to_void(self, vector) -> float:
        """1.0 = fully inside the void subspace, 0.0 = orthogonal to it.

        A proposal deep in the void shares nothing with the void's
        orthogonal complement, which is where everything the system has
        already organised lives.
        """
        v = np.asarray(vector, dtype=np.float64).reshape(-1)
        n = float(np.linalg.norm(v))
        if n < 1e-12:
            return 0.0
        p = self.project(v)
        return float(min(1.0, np.linalg.norm(p) / n))

    def reach(self, vector) -> Dict[str, Any]:
        """Full reading, recorded."""
        d = self.distance_to_void(vector)
        reading = {
            "distance_to_void": d,
            "reaching": d >= VOID_REACH,
            "void_dim": self.void_dim,
            "dim": self.dim,
        }
        self.readings.append(reading)
        return reading

    # ------------------------------------------------------------------
    # the lesson
    # ------------------------------------------------------------------

    def void_lesson(self, vector, intensity: float = 0.15,
                    min_reach: float = VOID_REACH) -> Dict[str, Any]:
        """A proposal pulled toward the void, or a refusal.

        Returns {"kept", "reason", "vector", "reading"}. `kept` is False
        whenever the proposal was not actually reaching into the void —
        the module refuses to manufacture novelty it did not find.

        **Never writes ψ₀.** The caller decides what, if anything, to do
        with the returned vector, through the ordinary gate.
        """
        reading = self.reach(vector)
        base = np.asarray(vector, dtype=np.float64).reshape(-1).copy()

        if not reading["reaching"]:
            return {
                "kept": False,
                "reason": "not_reaching",
                "vector": base,
                "reading": reading,
            }

        p = self.project(base)
        n = float(np.linalg.norm(base))
        if n < 1e-12:
            return {"kept": False, "reason": "refuse_zero",
                    "vector": base, "reading": reading}

        # renormalize toward the void component. the working state moves;
        # the ground is not touched and has no code path here.
        pulled = base + intensity * (p / (np.linalg.norm(p) + 1e-12)) * n
        return {
            "kept": True,
            "reason": "ok",
            "vector": pulled / (np.linalg.norm(pulled) + 1e-12),
            "reading": reading,
        }

    def stats(self) -> Dict[str, Any]:
        if not self.readings:
            return {"readings": 0}
        ds = [r["distance_to_void"] for r in self.readings]
        return {
            "readings": len(ds),
            "mean_distance": sum(ds) / len(ds),
            "max_distance": max(ds),
            "reaching": sum(1 for r in self.readings if r["reaching"]),
        }
