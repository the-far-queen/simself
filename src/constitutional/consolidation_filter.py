"""
consolidation_filter.py — Multi-cycle stability gate for promoting artifacts
to the privileged library (Module L).

Extracted from Bobby's `8-Filter.txt` (2026-09-07 batch ingest). Originally a
documentation snippet in `simself/docs/8-filter.md`; extracted to a real
module so SimSelf can call it.

The gate enforces 5 conditions before promoting an artifact:
  1. History depth ≥ STABILITY_WINDOW (default 3 cycles)
  2. Content is non-empty
  3. Worst-case stability across window ≥ MIN_WORST_CASE_STABILITY (0.88)
  4. Average norm alignment across window ≥ MIN_NORM_STABILITY (0.85)
  5. Somatic grounding score ≥ 0.8 (from grounding_map)

A pass promotes the artifact to the privileged library with a monotonic UID,
sha256 content signature, and revocable metadata linking to any superseded UID.

The somatic grounding vocabulary is Bobby's bio-affect tier:
  serenity: 1.0, clarity: 0.9, mastery: 0.85
  apprehension: 0.5, confusion: 0.3, dissonance: 0.0
  default (unknown bias): 0.5

Status enum:
  STASIS       — insufficient history depth
  DENIED       — one or more gates failed
  DUPLICATE    — content already in library
  CONSOLIDATED — promoted to library
"""
from __future__ import annotations

import hashlib
import time
from typing import Any, Dict, List, Optional, Sequence


# Status enum (string literals — no enum dependency).
STASIS = "STASIS"
DENIED = "DENIED"
DUPLICATE = "DUPLICATE"
CONSOLIDATED = "CONSOLIDATED"


# Default somatic grounding map (Bobby's bio-affect tiers).
DEFAULT_GROUNDING_MAP: Dict[str, float] = {
    "serenity": 1.0,
    "clarity": 0.9,
    "mastery": 0.85,
    "apprehension": 0.5,
    "confusion": 0.3,
    "dissonance": 0.0,
}


class StabilityConsolidationFilter:
    """Multi-cycle temporal gate for promoting artifacts to privileged store.

    The filter observes a chronological window of artifacts (logged by an
    upstream harness), then decides whether the latest artifact is stable
    enough to be consolidated into the privileged library.

    Parameters
    ----------
    privileged_library : list
        Mutable list that stores consolidated entries. Each entry is a dict
        with keys: uid, timestamp_wall, signature, content, metadata.
    stability_window : int
        Number of recent artifacts required (default 3).
    min_worst_case_stability : float
        Minimum stability ratio (score/threshold) across the window (default 0.88).
        "No lucky cycles permitted."
    min_norm_stability : float
        Minimum average norm_alignment_score across the window (default 0.85).
    grounding_map : dict, optional
        Maps somatic bias labels to grounding scores. Defaults to Bobby's tiers.
    """

    def __init__(
        self,
        privileged_library: List[Dict[str, Any]],
        stability_window: int = 3,
        min_worst_case_stability: float = 0.88,
        min_norm_stability: float = 0.85,
        grounding_map: Optional[Dict[str, float]] = None,
    ):
        self.library = privileged_library
        self.STABILITY_WINDOW = stability_window
        self.MIN_WORST_CASE_STABILITY = min_worst_case_stability
        self.MIN_NORM_STABILITY = min_norm_stability
        self.grounding_map = grounding_map if grounding_map is not None else dict(DEFAULT_GROUNDING_MAP)

    def evaluate_consolidation(self, history_window: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify chronological window before promotion.

        Parameters
        ----------
        history_window : sequence of dict
            Recent artifacts. Each must contain:
              - "score", "threshold" (for stability ratio)
              - "norm_alignment_score" (for norm adherence)
              - "content", "bias", "level" (for content + grounding + ladder rung)
              - "supersedes_uid" (optional, links to replaced artifact)

        Returns
        -------
        dict with keys "status" (STASIS|DENIED|DUPLICATE|CONSOLIDATED)
        and additional context fields.
        """
        if len(history_window) < self.STABILITY_WINDOW:
            return {"status": STASIS, "reason": "insufficient_history_depth"}

        latest = history_window[-1]

        # 1. Empty content guard.
        content = str(latest.get("content", "")).strip()
        if not content:
            return {"status": DENIED, "reason": "empty_or_trivial_content"}

        # 2. Worst-case stability (bottleneck check).
        try:
            stability_scores = [
                float(h["score"]) / float(h["threshold"]) for h in history_window
            ]
        except (KeyError, TypeError, ZeroDivisionError) as e:
            return {"status": DENIED, "reason": f"missing_or_invalid_score: {e}"}
        worst_case_stability = min(stability_scores)

        # 3. Norm adherence (averaged over window).
        norm_scores = [float(h.get("norm_alignment_score", 0)) for h in history_window]
        avg_norm = sum(norm_scores) / len(norm_scores) if norm_scores else 0.0

        # 4. Graded somatic grounding.
        current_bias = latest.get("bias", "neutral")
        grounding_score = self.grounding_map.get(current_bias, 0.5)

        # 5. The gate logic.
        if (
            worst_case_stability >= self.MIN_WORST_CASE_STABILITY
            and avg_norm >= self.MIN_NORM_STABILITY
            and grounding_score >= 0.8
        ):
            return self.promote_to_privileged_store(latest, worst_case_stability)

        return {
            "status": DENIED,
            "stability_min": worst_case_stability,
            "norm_avg": avg_norm,
            "grounding": grounding_score,
        }

    def promote_to_privileged_store(
        self,
        artifact: Dict[str, Any],
        confidence: float,
    ) -> Dict[str, Any]:
        """Consolidate artifact with monotonic UID and content signature.

        The artifact is checked for duplicate content (by sha256 of content)
        before being added. Each entry has a `revocable=True` flag in metadata
        to allow later reversal.
        """
        content = str(artifact.get("content", "")).strip()
        content_sig = hashlib.sha256(content.encode("utf-8")).hexdigest()

        if any(item.get("signature") == content_sig for item in self.library):
            return {"status": DUPLICATE, "signature": content_sig}

        entry = {
            "uid": f"mono_{time.monotonic_ns()}",
            "timestamp_wall": time.time(),
            "signature": content_sig,
            "content": content,
            "metadata": {
                "confidence_score": confidence,
                "ladder_rung": artifact.get("level"),
                "revocable": True,
                "supersedes": artifact.get("supersedes_uid"),
            },
        }
        self.library.append(entry)
        return {"status": CONSOLIDATED, "uid": entry["uid"]}

    def revoke(self, uid: str) -> bool:
        """Mark an entry as revoked (does not delete — preserves history).

        Returns True if the entry was found and marked, False otherwise.
        """
        for entry in self.library:
            if entry.get("uid") == uid:
                entry.setdefault("metadata", {})["revocable"] = False
                entry["metadata"]["revoked_at"] = time.time()
                return True
        return False

    def stats(self) -> Dict[str, Any]:
        """Return library stats: total, active, revoked counts."""
        total = len(self.library)
        revoked = sum(
            1 for e in self.library
            if e.get("metadata", {}).get("revocable") is False
        )
        return {
            "total_entries": total,
            "active_entries": total - revoked,
            "revoked_entries": revoked,
        }


__all__ = [
    "StabilityConsolidationFilter",
    "STASIS", "DENIED", "DUPLICATE", "CONSOLIDATED",
    "DEFAULT_GROUNDING_MAP",
]