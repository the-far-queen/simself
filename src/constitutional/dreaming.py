"""
dreaming.py — Constitutional dreaming with a quality gate.

Extracted from SimSelf.dream in the v8.0-grok file. The original:
1. sampled 1-3 memories
2. computed a "novelty" and "consonance" score
3. added a frequency perturbation to psi_current if frequency_mode was set
4. applied random axis deltas if score >= 0.36
5. stored the dream and recorded it in the decision log

We keep (1), (2), (4), (5). We drop (3) — frequency perturbation is a
frequency-module concern, not a constitutional one. The constitutional
dreaming is a recombination of existing memories + small constitutional
drift, with a quality gate to prevent the dream log from filling with
noise.
"""
from __future__ import annotations

import random
import time
from typing import Any, Dict, List, Optional

import numpy as np

from .constitution import cosine, embed_text
from .memory import RelationalMemory


class ConstitutionalDreaming:
    """Memory-recombination dreaming with a quality gate.

    Quality score = 0.45 * novelty + 0.35 * consonance + 0.20 * intensity.
    A dream is "kept" iff score >= 0.36 (the v8 threshold; kept as-is
    since the empirical threshold is not addressed in this file).
    """

    def __init__(self, memory: RelationalMemory, axis_names: List[str], dim: int):
        self.memory = memory
        self.axis_names = axis_names
        self.dim = dim
        self.dream_log: List[Dict] = []

    def dream(self, intensity: float = 0.5) -> Dict[str, Any]:
        intensity = max(0.15, min(1.0, intensity))
        mems = self.memory.retrieve("", top_n=5, hops=1)

        if len(mems) < 2:
            narrative = "Sparse field. Constitutional axes flickered against empty horizon."
            novelty = 0.45
            consonance = 0.50
            source_ids = []
        else:
            chosen = random.sample(mems, k=min(3, len(mems)))
            source_ids = [m["id"] for m in chosen]
            fragments = [m["text"][:90] for m in chosen]
            narrative = f"Dream recombination: {' XOR '.join(fragments)} ... interference resolved toward ground."
            novelty = 0.55
            core_emb = embed_text("coherent grounded authentic presence")
            dream_emb = embed_text(narrative)
            consonance = max(0.0, cosine(core_emb, dream_emb))

        score = 0.45 * novelty + 0.35 * consonance + 0.20 * intensity
        kept = score >= 0.36

        deltas = {}
        if kept:
            for name in random.sample(self.axis_names, k=min(4, len(self.axis_names))):
                delta = random.uniform(-0.05, 0.05) * intensity
                deltas[name] = round(delta, 4)

        entry = {
            "timestamp": time.time(),
            "narrative": narrative,
            "source_ids": source_ids,
            "deltas": deltas,
            "novelty": round(novelty, 4),
            "consonance": round(consonance, 4),
            "score": round(score, 4),
            "kept": kept,
        }
        if kept:
            self.dream_log.append(entry)
            self.memory.store(f"Dream: {narrative[:120]}", tags=["dream"])
        return entry

    def stats(self) -> Dict[str, Any]:
        return {"total_dreams": len(self.dream_log), "kept_dreams": sum(1 for d in self.dream_log if d.get("kept", d.get("score", 0) >= 0.36))}
