"""
operators.py — Field transformation operators + FFT holographic encoder.

Source: 44-back/operators/core.py (Bobby's parallel implementation, March 2026).
Ported 2026-09-12 by Hermes. Per Bobby: "is this useful to ai or human constructing
a new system of ai awakening" — YES. Operators are the substrate's primitives for
field transformation. Emergent capability = composition of operators.

Engineering invariants:
- Operator ABC: base class for all field transformations (apply(packets) -> Optional[packet])
- CentroidOperator: compresses packet sets into representative centroids
- HolographicEncoder: FFT-based text-to-vector encoding
- CausalPSB: foundational CAUSE primitive with crystallize threshold
- Stateless: each call is independent
- Composable: operators chain (output of one is input of next)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================================
# BASE OPERATOR
# ============================================================================

class Operator(ABC):
    """Abstract Base Class for all field operators.

    Per Bobby: emergent capability = composition of operators.
    Each operator transforms a set of packets into (optionally) a new packet.
    Operators compose: output of one operator feeds into the next.
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    def cost(self) -> float:
        """Default cost. Override for expensive operations."""
        return 0.1

    @abstractmethod
    def apply(self, packets: List[Any]) -> Optional[Any]: ...

    def __call__(self, packets: List[Any]) -> Optional[Any]:
        return self.apply(packets)


# ============================================================================
# FIELD OPERATORS
# ============================================================================

class CentroidOperator(Operator):
    """Compresses a set of packets into their centroid.

    Engineering use: collapse similar packets into a representative. Reduces
    field cardinality while preserving the geometric center.
    """

    @property
    def name(self) -> str:
        return "centroid"

    def apply(self, packets: List[Any]) -> Optional[Any]:
        if not packets:
            return None
        embeddings = [p.embedding for p in packets if hasattr(p, "embedding")]
        if not embeddings:
            return None
        try:
            import numpy as np
            centroid = np.mean(embeddings, axis=0)
            centroid = centroid / (np.linalg.norm(centroid) + 1e-8)
        except ImportError:
            # Pure-Python fallback
            dim = len(embeddings[0])
            n = len(embeddings)
            centroid = [sum(e[i] for e in embeddings) / n for i in range(dim)]
            norm = sum(c ** 2 for c in centroid) ** 0.5 + 1e-8
            centroid = [c / norm for c in centroid]

        # Construct result preserving packet type
        try:
            return type(packets[0])(
                id=f"centroid_{id(centroid)}",
                embedding=centroid,
                metadata={"type": "compressed", "source_count": len(packets)},
            )
        except (TypeError, ValueError):
            # Fallback: return raw centroid if packet constructor signature differs
            return centroid


# ============================================================================
# PRIMITIVES (PSBs)
# ============================================================================

@dataclass
class CausalPSB:
    """The foundational CAUSE primitive.

    Per Bobby's method (memory fact 1644): generalize seemingly unrelated
    geometries → derive simple engineering statements. CAUSE is the PSB that
    generalizes force, energy, and dependency across all substrates.

    Crystallizes when enough grounding events accumulate. Once crystallized,
    it's an immutable substrate primitive.
    """

    symbol: str = "CAUSE"
    coherence: float = 0.0
    crystallized: bool = False
    grounding_events: List[Dict[str, Any]] = field(default_factory=list)
    crystallize_threshold: float = 0.95
    min_groundings: int = 20

    def ground(self, data: Any, context: str) -> float:
        """Ground CAUSE with new observations. Returns updated coherence."""
        self.grounding_events.append({"data": data, "context": context})
        self.coherence = min(1.0, self.coherence + 0.05)
        if self.coherence > self.crystallize_threshold and len(self.grounding_events) > self.min_groundings:
            self.crystallized = True
        return self.coherence

    def is_ready(self) -> bool:
        return self.crystallized

    def get_state(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "coherence": self.coherence,
            "crystallized": self.crystallized,
            "grounding_count": len(self.grounding_events),
        }


# ============================================================================
# HOLOGRAPHIC ENCODER (FFT-based)
# ============================================================================

class HolographicEncoder:
    """FFT-based text representation.

    Different encoding than holographic memory store (per memory fact 1660 +
    hermes-agent/plugins/memory/holographic/holographic.py uses HRR phase encoding).
    This is a simpler FFT-based alternative for fast text-to-vector without training.

    Engineering use: lightweight text encoder for prototyping. Not load-bearing
    for canonical production (which uses learned embeddings); useful for tests.
    """

    def __init__(self, n_components: int = 128):
        self.n_components = int(n_components)

    def encode(self, text: str) -> List[float]:
        """Encode text via FFT of character ordinals."""
        chars = [ord(c) for c in text[: self.n_components]]
        if len(chars) < self.n_components:
            chars += [0] * (self.n_components - len(chars))

        try:
            import numpy as np
            fft_result = np.fft.fft(chars)
            embedding = np.abs(fft_result).astype(np.float32)
            norm = float(np.linalg.norm(embedding)) + 1e-8
            return (embedding / norm).tolist()
        except ImportError:
            # Pure-Python DFT fallback (slow but works)
            n = len(chars)
            real = [0.0] * n
            imag = [0.0] * n
            for k in range(n):
                for j in range(n):
                    angle = -2 * 3.14159265 * k * j / n
                    real[k] += chars[j] * (angle and math.cos(angle) or 1.0)
                    imag[k] += chars[j] * math.sin(-angle)
            mags = [math.sqrt(real[k] ** 2 + imag[k] ** 2) for k in range(n)]
            norm = math.sqrt(sum(m ** 2 for m in mags)) + 1e-8
            return [m / norm for m in mags]

    def get_state(self) -> Dict[str, Any]:
        return {"n_components": self.n_components, "type": "fft-encoder"}


# Pure-Python math import for the DFT fallback (avoid name collision)
import math  # noqa: E402


# Self-test
if __name__ == "__main__":
    # CentroidOperator test
    @dataclass
    class P:
        id: str
        embedding: Any
        metadata: Dict[str, Any] = field(default_factory=dict)

    co = CentroidOperator()
    packets = [
        P(id="1", embedding=[1.0, 0.0, 0.0]),
        P(id="2", embedding=[0.9, 0.1, 0.0]),
        P(id="3", embedding=[0.0, 0.0, 1.0]),
    ]
    result = co(packets)
    print(f"Centroid of 3 packets: type={type(result).__name__}")

    # CausalPSB test
    cpsb = CausalPSB()
    for i in range(25):
        cpsb.ground(data=i, context="test")
    print(f"CausalPSB after 25 groundings: crystallized={cpsb.is_ready()}, coherence={cpsb.coherence:.2f}")

    # HolographicEncoder test
    he = HolographicEncoder(n_components=16)
    emb = he.encode("Hello world")
    print(f"HolographicEncoder: dim={len(emb)}, norm={sum(x**2 for x in emb)**0.5:.4f}")
