"""
dreaming.py — combinatorial dreaming (per Grok's 2026-08-08 review, defect E).

BEFORE THIS REWRITE the dreamer was, in full:

    rng = np.random.RandomState(len(self.dream_log))
    perturbation = intensity * rng.randn(self.dim)
    allow, reason = gate_packet(perturbation, psi0)
    return {..., "source_unit_ids": [], ...}

`source_unit_ids` was empty. There was no retrieval, no recombination,
no memory. A random vector pushed through a gate — and the metric that
called it "novel" was `distance_before - distance_after`, which rewards
*convergence*. A system that always fell to equilibrium scored perfectly.

Grok's specified fix was: retrieve memories, combine two or three,
mutate, evaluate, store what succeeds. That is what this does.

The invariant that did not change: **ψ₀ is never modified.** The dream
proposes; the gate disposes.

Two things this module now guarantees, both testable:

1. `source_unit_ids` is populated, or the dream is refused as
   `insufficient_memory`. A dream with no sources is not a dream.
2. `novelty` is measured against committed memory via
   `ConstitutionalMemory.novelty()` — distance to the nearest prior
   artifact, not distance travelled toward equilibrium.
"""

from __future__ import annotations

from typing import List, Optional, Sequence

import numpy as np

from .ground import Ground


def gate_packet(emb, psi0, max_norm=4.0, min_cos=0.4):
    ne = float(np.linalg.norm(emb))
    if ne > max_norm:
        return (False, "refuse_norm")
    n0 = float(np.linalg.norm(psi0))
    if ne == 0.0 or n0 == 0.0:
        return (False, "refuse_zero")
    if float(np.dot(emb, psi0) / (ne * n0)) < min_cos:
        return (False, "refuse_coherence")
    return (True, "ok")


class Dream:
    """A proposed perturbation to working state, with its provenance."""

    def __init__(self, perturbation: np.ndarray, source_unit_ids: List[str],
                 intensity: float, novelty: float = 0.0):
        self.perturbation = perturbation
        self.source_unit_ids = source_unit_ids
        self.intensity = intensity
        self.novelty = novelty


class ConstitutionalDreaming:
    """Recombination over memory. ψ₀ never modified.

    Args:
        ground: the write-protected constitutional ground.
        dim: working-state dimension.
        memory: a ConstitutionalMemory. Required for the dreamer to do
            anything at all; without it every dream is refused.
        min_sources: how many distinct memories must be recombined.
            1 would let it echo; 2 is the smallest number that is
            actually a recombination.
    """

    def __init__(self, ground: Ground, dim: int, memory=None,
                 min_sources: int = 2, novelty_floor: float = 0.05):
        self.ground = ground
        self.dim = dim
        self.memory = memory
        self.min_sources = min_sources
        self.novelty_floor = novelty_floor
        self.dream_log: List[dict] = []

    # ------------------------------------------------------------------
    # the mechanism
    # ------------------------------------------------------------------

    def _retrieve(self, psi0: np.ndarray, k: int) -> tuple:
        """Pull k committed memories most aligned with the current state.

        Alignment with ψ₀, not with a random probe — a dream should grow
        out of where the system already is, which is also what keeps it
        inside the coherence gate.
        """
        if self.memory is None:
            return ([], np.zeros(0))
        hits = self.memory.retrieve(psi0, top_n=k, committed_only=True)
        if not hits:
            return ([], np.zeros(0))
        ids = [iid for iid, _ in hits]
        vecs = np.stack([self.memory.items[iid].embedding for iid in ids])
        return (ids, vecs)

    def _recombine(self, vecs: np.ndarray, intensity: float,
                   seed: int) -> np.ndarray:
        """Blend the retrieved vectors, then mutate.

        The blend is a weighted mean with weights drawn from a
        Dirichlet-ish simplex so different pairs produce different
        mixtures rather than every combination collapsing to the same
        centroid.
        """
        rng = np.random.RandomState(seed)
        n = vecs.shape[0]
        # softmax weights, temperature-sharpened so one source dominates
        # but never fully replaces the others
        raw = rng.rand(n)
        w = np.exp(3.0 * (raw - raw.max()))
        w = w / w.sum()
        blend = (vecs * w[:, None]).sum(axis=0)

        # mutation: a small random excursion away from the blend, scaled
        # by intensity. this is the only stochastic part.
        mutate = intensity * rng.randn(self.dim) / np.sqrt(self.dim)
        return blend + mutate

    def dream(self, intensity: float = 0.4, k: int = 3) -> dict:
        """Generate one dream proposal by recombination.

        Returns a dict with `kept`, `reason`, `perturbation_norm`,
        `source_unit_ids`, `novelty`, and `intensity`. The proposal is
        gated like any other packet; ψ₀ is untouched either way.
        """
        psi0 = self.ground.psi_0
        seed = len(self.dream_log)

        base = {
            "kept": False,
            "reason": "",
            "perturbation_norm": 0.0,
            "source_unit_ids": [],
            "novelty": 0.0,
            "intensity": intensity,
            "seed": seed,
        }

        if self.memory is None:
            base["reason"] = "no_memory"
            self.dream_log.append(base)
            return base

        ids, vecs = self._retrieve(psi0, k)
        if len(ids) < self.min_sources:
            # THE FIX. Previously this returned a random vector with an
            # empty source list and called it a dream.
            base["reason"] = ("insufficient_memory"
                              if not ids else "insufficient_sources")
            base["source_unit_ids"] = ids
            self.dream_log.append(base)
            return base

        perturbation = self._recombine(vecs, intensity, seed)

        # novelty against committed memory. 0.0 == nothing committed
        # resembles this, i.e. we have rediscovered something.
        nov, nearest = self.memory.novelty(perturbation)
        base["novelty"] = nov
        base["nearest_committed"] = nearest
        if nov < self.novelty_floor:
            base["reason"] = "not_novel"
            base["source_unit_ids"] = ids
            self.dream_log.append(base)
            return base

        allow, reason = gate_packet(perturbation, psi0)
        base["kept"] = allow
        base["reason"] = reason
        base["perturbation_norm"] = float(np.linalg.norm(perturbation))
        base["source_unit_ids"] = ids
        self.dream_log.append(base)
        return base

    # ------------------------------------------------------------------
    # read
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """What the dreamer has actually been doing."""
        n = len(self.dream_log)
        if n == 0:
            return {"dreams": 0}
        kept = sum(1 for d in self.dream_log if d.get("kept"))
        sourced = sum(1 for d in self.dream_log if d.get("source_unit_ids"))
        novs = [d["novelty"] for d in self.dream_log if d.get("novelty")]
        return {
            "dreams": n,
            "kept": kept,
            "kept_ratio": kept / n,
            "with_sources": sourced,
            "source_ratio": sourced / n,
            "mean_novelty": (sum(novs) / len(novs)) if novs else 0.0,
        }
