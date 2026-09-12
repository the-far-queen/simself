"""
temporal_control.py — The "WHEN" layer for gated execution.

Source: 44-back/controller/core.py::TemporalController (Bobby's parallel implementation, March 2026).
Ported 2026-09-12 by Hermes. Per Bobby: "pliny in same class as stressors ie by reverse
engineering hacks we arrive at growth protocols." The TCL is the substrate's
application of the same principle — signal quality gates expensive operations.

Per Bobby's test (2026-09-12): "is this useful to ai or human constructing a new
system of ai awakening" — YES. Emergent capability requires that the substrate
NOT run every operation every tick. Novel signals deserve capacity; routine
signals do not. The TCL is the substrate's gating primitive for that distinction.

Engineering invariants:
- Heuristic: entropy + novelty > thresholds → trigger expensive operation
- Stateless: each should_trigger(state) call is independent
- Bounded: no internal rate-limiting beyond the heuristic
- Auditable: trigger_history is exposed for diagnostics
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


class TemporalController:
    """The "WHEN" layer: decides if signal quality warrants expensive operations.

    Per Bobby: gating on signal quality prevents the substrate from running every
    operation every tick. Capacity is preserved for novel signals.

    Heuristic:
        should_trigger(state) → entropy(state.embedding) > entropy_threshold
                                OR novelty(state) > novelty_threshold

    Engineering claim: a substrate that always runs every op is shallow; one that
    gates on quality is deep. This is the operationalization of "reverse engineering
    IS growth protocol" (memory fact id 1706) for temporal execution.

    Attributes:
        entropy_threshold: Variance threshold for triggering. Default 0.1.
            Higher = more selective. Lower = more eager to compute.
        novelty_threshold: Novelty threshold. Default 0.3.
            Higher = more selective. Lower = more eager.
        trigger_history: Append-only list of trigger decisions for diagnostics.
    """

    def __init__(self, entropy_threshold: float = 0.1, novelty_threshold: float = 0.3):
        self.entropy_threshold = float(entropy_threshold)
        self.novelty_threshold = float(novelty_threshold)
        self.trigger_history: List[bool] = []

    def should_trigger(self, state: Dict[str, Any]) -> bool:
        """Heuristic check for whether to run an expensive operation.

        Args:
            state: Dict with optional "embedding" (vector), "novelty" (scalar).
                   May include other keys; ignored here.

        Returns:
            True if signal quality warrants expensive operation; False otherwise.
        """
        embedding = state.get("embedding")
        if embedding is None:
            self.trigger_history.append(False)
            return False

        # Entropy: variance of embedding (uniform embedding has variance 0)
        entropy = float(_variance(embedding))

        # Novelty: external signal (caller computes); default 0.0 (NOT triggering)
        # Bobby's original used 0.5 as placeholder, but 0.5 > 0.3 default threshold
        # meant TCL always triggered — defeating the gating purpose.
        # Correct default: missing novelty means "don't have novelty signal" → don't trigger.
        novelty = float(state.get("novelty", 0.0))

        trigger = entropy > self.entropy_threshold or novelty > self.novelty_threshold
        self.trigger_history.append(trigger)
        return trigger

    def trigger_rate(self, recent: int = 100) -> float:
        """Fraction of recent triggers that fired. Useful for diagnostics."""
        if not self.trigger_history:
            return 0.0
        window = self.trigger_history[-recent:]
        return sum(window) / len(window)

    def get_state(self) -> Dict[str, Any]:
        return {
            "entropy_threshold": self.entropy_threshold,
            "novelty_threshold": self.novelty_threshold,
            "trigger_count": len(self.trigger_history),
            "trigger_rate_recent": self.trigger_rate(),
        }


def _variance(x: Any) -> float:
    """Variance of a 1-d sequence. NumPy optional."""
    if x is None:
        return 0.0
    try:
        import numpy as np
        arr = np.asarray(x, dtype=np.float64)
        return float(np.var(arr))
    except ImportError:
        # Pure-Python fallback
        try:
            seq = [float(v) for v in x]
        except (TypeError, ValueError):
            return 0.0
        if not seq:
            return 0.0
        mean = sum(seq) / len(seq)
        return sum((v - mean) ** 2 for v in seq) / len(seq)


# Self-test (run as: `python -m constitutional.temporal_control`)
if __name__ == "__main__":
    import random
    random.seed(42)
    tc = TemporalController()

    # Test 1: high-entropy state (random embedding) → should trigger
    high_entropy = [random.gauss(0, 1) for _ in range(16)]
    print(f"High-entropy: trigger={tc.should_trigger({'embedding': high_entropy})}")

    # Test 2: low-entropy state (uniform) → should NOT trigger
    low_entropy = [0.5] * 16
    print(f"Low-entropy: trigger={tc.should_trigger({'embedding': low_entropy})}")

    # Test 3: explicit novelty
    print(f"Novelty=0.9: trigger={tc.should_trigger({'embedding': [0.0]*16, 'novelty': 0.9})}")

    # Diagnostic
    print(f"State: {tc.get_state()}")
