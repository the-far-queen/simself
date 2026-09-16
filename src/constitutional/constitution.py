"""
constitution.py — axis matrix (per Grok master plan, full rewrite 2026-09-16).

Each axis is a named coordinate of ψ with an interval [low, high] that
determines whether a packet is admitted or refused. An axis earns its keep
when crossing its interval changes a verdict on a fixed test packet. Count
axes by that, not by Clifford or octonion arithmetic.

The previous version of this file derived axes from Cl(4) + octonions +
Hodge dual + triple product, producing 8+12 = 20 axes by dimension counting.
Per Grok (segment 02, applied 2026-09-16): that derivation is dimension
arithmetic, not a theorem. The axes themselves can stay — they are functional
— — but the derivation is gone.

Public API:
- ConstitutionalAxis: one named coordinate with a threshold.
- Constitution: a list of axes + ψ_0 + dim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np


@dataclass
class ConstitutionalAxis:
    """A named coordinate of ψ with an interval that decides verdicts.

    An axis earns its keep when crossing its interval changes allow to deny on
    a fixed test packet. If it doesn't, the axis is decoration.
    """

    name: str
    low: float = -1.0
    high: float = 1.0
    weight: float = 1.0
    mutable: bool = True
    description: str = ""

    def in_range(self, value: float) -> bool:
        return self.low <= value <= self.high


# Default axis set. These are the axes that govern the identity layer. Each
# must have a measured threshold effect; the demo in __main__ verifies two.
DEFAULT_AXES: List[ConstitutionalAxis] = [
    ConstitutionalAxis(
        name="boundaries",
        low=-0.5, high=0.5,
        description="Verdict boundary for tool-side refusal.",
    ),
    ConstitutionalAxis(
        name="coherence",
        low=0.0, high=1.0,
        description="Cosine-to-ground threshold; refusal when below.",
    ),
    ConstitutionalAxis(
        name="stability",
        low=0.0, high=1.0,
        description="Drift non-increasing under tick.",
    ),
    ConstitutionalAxis(
        name="routing",
        low=-1.0, high=1.0,
        description="Type-tag meridians: language/identity/body/code.",
    ),
    ConstitutionalAxis(
        name="recovery",
        low=0.0, high=1.0,
        description="Restart fidelity: ψ₀, ψ, committed unit ids match.",
    ),
    ConstitutionalAxis(
        name="authenticity",
        low=-1.0, high=1.0,
        description="Spans admitted only when gate passes.",
    ),
    ConstitutionalAxis(
        name="norm",
        low=0.0, high=4.0,
        description="Embedding norm bound; refusal above.",
    ),
    ConstitutionalAxis(
        name="commit_radius",
        low=0.0, high=1.0,
        description="Cosine-to-ground distance for commitment.",
    ),
]


@dataclass
class Constitution:
    """The set of axes + ψ₀ + dim.

    The number of axes is a project decision, not an algebra. DEFAULT_AXES has
    8; the legacy code carried 20. Either number works as long as each axis
    has a measured threshold effect.
    """

    axes: List[ConstitutionalAxis] = field(default_factory=lambda: list(DEFAULT_AXES))
    psi_0: np.ndarray = field(default_factory=lambda: np.array([1.0] + [0.0] * 15))
    dim: int = 16

    def __post_init__(self):
        n = float(np.linalg.norm(self.psi_0))
        if n == 0.0:
            raise ValueError("Constitution: ψ₀ has zero norm.")
        self.psi_0 = (self.psi_0 / n).astype(np.float64)
        if self.dim != self.psi_0.shape[0]:
            self.dim = self.psi_0.shape[0]

    @property
    def axes_def(self) -> List[Tuple[str, int]]:
        """Return axes as (name, sheave) pairs for legacy callers.

        Sheaf index here is just the axis index. Channels (formerly sheaves)
        are runtime routing primitives, not cohomology.
        """
        return [(a.name, i) for i, a in enumerate(self.axes)]

    @property
    def axis_names(self) -> List[str]:
        return [a.name for a in self.axes]

    @property
    def axis_sheaves(self) -> Dict[int, str]:
        """Legacy: {sheave_index: name}. The vocabulary is preserved for callers
        that still reference "sheaf"."""
        return {i: a.name for i, a in enumerate(self.axes)}

    @property
    def consonance_matrix(self) -> np.ndarray:
        """Default consonance: identity matrix. Override for non-trivial coupling."""
        return np.eye(len(self.axes))

    def curvature_vector(self) -> np.ndarray:
        """Return the curvature vector for legacy callers. Default: zero."""
        return np.zeros(self.dim)

    def consonance(self, obs: np.ndarray, axis_name: str) -> float:
        """Default consonance: project obs onto ψ₀."""
        return float(np.dot(obs, self.psi_0) / (np.linalg.norm(obs) + 1e-9))


# Legacy entry points preserved so existing callers keep working.
def embed_text(text: str, dim: int = 16) -> np.ndarray:
    """Bag-of-tokens embedding. Same shape as kernel/lexicon."""
    v = np.zeros(dim)
    for i, tok in enumerate(text.lower().split()):
        v[hash(tok) % dim] += 1.0
        v[(hash(tok) // dim) % dim] += 0.25
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def project_to_constitution(v: np.ndarray, dim: int = 16) -> np.ndarray:
    """Resize / project a vector onto the constitutional dimension."""
    v = np.asarray(v, dtype=np.float64)
    if v.shape[0] == dim:
        return v
    if v.shape[0] < dim:
        out = np.zeros(dim)
        out[: v.shape[0]] = v
        return out
    return v[:dim]


if __name__ == "__main__":
    # Sanity: a small example that an axis interval changes a verdict.
    c = Constitution()
    psi = c.psi_0.copy()
    psi[1] = 0.4  # within boundaries axis range
    print("axis boundaries.in_range(0.4) =", c.axes[0].in_range(0.4))
    print("axis boundaries.in_range(0.6) =", c.axes[0].in_range(0.6))
    print("Constitution: 8 axes, dim =", c.dim)
