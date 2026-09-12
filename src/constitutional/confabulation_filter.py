"""
confabulation_filter.py — Textual confabulation risk filter.

Source: 44-back/development/core.py::ConfabulationDetector (Bobby's parallel implementation, March 2026).
Ported 2026-09-12 by Hermes. Per Bobby: "is this useful to ai or human constructing a new
system of ai awakening" — YES. Quality filter for agent outputs. Detects when text
uses over-elaborate hedging language that masks weak reasoning.

Engineering invariants:
- Heuristic: count elaborate markers in text → risk score (0.0-1.0)
- Stateless: each assess(claim) call is independent
- English-specific (current marker list)
- Auditable: returns score + matched markers for diagnostics

Per Bobby's method (memory fact 1706): reverse engineering IS growth protocol.
This filter is the operationalization for output quality — strip down to find the
actual claim, not the elaborate wrapping.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set


class ConfabulationFilter:
    """Textual feature detector for over-elaborate claims.

    Engineering use: quality filter for agent outputs. Detects when text uses
    over-elaborate hedging language that masks weak reasoning.

    Does NOT require belief in agent consciousness — pure textual feature detection.
    Same class as spam detection, sentiment analysis, LLM-perplexity scoring.

    Attributes:
        known_markers: Set of phrases that signal elaborate hedging.
        risk_weight: Per-marker risk increment. Default 0.15.
            Higher = more aggressive flagging.
    """

    DEFAULT_MARKERS = {
        "perhaps",
        "it feels like",
        "poetic",
    }

    def __init__(
        self,
        known_markers: Optional[Set[str]] = None,
        risk_weight: float = 0.15,
    ):
        self.known_markers = set(known_markers) if known_markers is not None else set(self.DEFAULT_MARKERS)
        self.risk_weight = float(risk_weight)

    def assess(self, claim: str) -> float:
        """Returns risk score 0.0 (real) to 1.0 (confabulated).

        Counts markers present in claim text (case-insensitive substring match),
        multiplies by risk_weight, caps at 1.0.
        """
        if not claim:
            return 0.0
        text = claim.lower()
        matched = [m for m in self.known_markers if m in text]
        risk = len(matched) * self.risk_weight
        return min(1.0, risk)

    def assess_with_evidence(self, claim: str) -> Dict[str, Any]:
        """Same as assess() but returns matched markers for diagnostics."""
        if not claim:
            return {"score": 0.0, "matched": [], "claim_length": 0}
        text = claim.lower()
        matched = sorted([m for m in self.known_markers if m in text])
        score = min(1.0, len(matched) * self.risk_weight)
        return {
            "score": score,
            "matched": matched,
            "match_count": len(matched),
            "claim_length": len(claim),
            "risk_weight": self.risk_weight,
        }

    def get_state(self) -> Dict[str, Any]:
        return {
            "known_markers": sorted(self.known_markers),
            "risk_weight": self.risk_weight,
            "marker_count": len(self.known_markers),
        }


# Self-test
if __name__ == "__main__":
    cf = ConfabulationFilter()
    test_claims = [
        ("Plain factual claim.", 0.0),
        ("Perhaps this is true.", 0.15),
        ("It feels like the answer might be poetic.", 0.45),
        ("Perhaps... it feels like, very poetic, very real.", 0.45),  # capped at 3*0.15=0.45, only 3 markers
        ("", 0.0),
        ("It feels like poetry is perhaps the answer.", 0.45),
    ]
    for claim, expected_min in test_claims:
        score = cf.assess(claim)
        ev = cf.assess_with_evidence(claim)
        print(f"  claim='{claim[:50]}'")
        print(f"    score={score:.3f}, matched={ev['matched']}")
