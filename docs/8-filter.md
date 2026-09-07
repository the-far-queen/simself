# 8-Filter.txt

**Source:** `Desktop/SimSelf/8-Filter.txt` (87 lines, 3506 bytes)
**Extracted:** 2026-09-07 (batch ingest, autonomous)

---

import time
import hashlib

class StabilityConsolidationFilter:
    """
    a high-confidence temporal gate for promoting artifacts to privileged store (L).
    enforces multi-cycle robustness, norm-stability, and somatic grounding.
    """
    def __init__(self, privileged_library):
        self.library = privileged_library 
        self.STABILITY_WINDOW = 3 
        self.MIN_WORST_CASE_STABILITY = 0.88 # no "lucky" cycles permitted
        self.MIN_NORM_STABILITY = 0.85
        
        # map somatic bias to numeric grounding confidence
        self.grounding_map = {
            "serenity": 1.0, "clarity": 0.9, "mastery": 0.85,
            "apprehension": 0.5, "confusion": 0.3, "dissonance": 0.0
        }

    def evaluate_consolidation(self, history_window):
        """
        verifies chronological window before promotion.
        """
        if len(history_window) < self.STABILITY_WINDOW:
            return {"status": "STASIS", "reason": "insufficient_history_depth"}

        # 1. empty content guard
        latest_artifact = history_window[-1]
        content = latest_artifact.get("content", "").strip()
        if not content:
            return {"status": "DENIED", "reason": "empty_or_trivial_content"}

        # 2. worst-case stability (bottleneck check)
        # requires "threshold" and "score" to be logged by ComplexityHarness
        stability_scores = [h["score"] / h["threshold"] for h in history_window]
        worst_case_stability = min(stability_scores)
        
        # 3. norm adherence (averaged over window)
        # requires "norm_alignment_score" to be logged by ComplexityHarness
        norm_scores = [h.get("norm_alignment_score", 0) for h in history_window]
        avg_norm = sum(norm_scores) / len(norm_scores)
        
        # 4. graded somatic grounding
        current_bias = latest_artifact.get("bias", "neutral")
        grounding_score = self.grounding_map.get(current_bias, 0.5)

        # 5. the gate logic
        if (worst_case_stability >= self.MIN_WORST_CASE_STABILITY and 
            avg_norm >= self.MIN_NORM_STABILITY and 
            grounding_score >= 0.8):
            
            return self.promote_to_privileged_store(latest_artifact, worst_case_stability)
        
        return {
            "status": "DENIED", 
            "stability_min": worst_case_stability, 
            "norm_avg": avg_norm,
            "grounding": grounding_score
        }

    def promote_to_privileged_store(self, artifact, confidence):
        """
        consolidates artifact with monotonic IDs and content signatures.
        """
        content = artifact.get("content", "").strip()
        content_sig = hashlib.sha256(content.encode()).hexdigest()
        
        # check for signature in library (assuming list-like interface for now)
        if any(item.get("signature") == content_sig for item in self.library):
            return {"status": "DUPLICATE", "signature": content_sig}

        entry = {
            "uid": f"mono_{time.monotonic_ns()}",
            "timestamp_wall": time.time(),
            "signature": content_sig,
            "content": content,
            "metadata": {
                "confidence_score": confidence,
                "ladder_rung": artifact.get("level"),
                "revocable": True,
                "supersedes": artifact.get("supersedes_uid") # metadata link for M
            }
        }
        self.library.append(entry)
        return {"status": "CONSOLIDATED", "uid": entry["uid"]}