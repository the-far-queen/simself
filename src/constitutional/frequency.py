"""
frequency.py — frequency as parameterized parallel state (per Grok master plan).

Per the long-standing deal (M3 pass-4 + Grok segment 02, applied 2026-09-16):
frequency lives as a parallel state machine that does NOT touch ψ_current. The
numerics (7.83 / 432 / 963 / 55 / 34.4) are hypotheses with parameters, not
asserted facts. This rewrite makes the parallel-state contract explicit.

The previous version of this file mixed frequency into the constitutional axes
and used Kuramoto coupling that fed back into ψ_current. Per Grok: ψ moves
under the projected gradient step in resolution.py; frequency has its own
register and never modifies ψ.
"""

from __future__ import annotations

import numpy as np


# Parameterized hypotheses. These are inputs to a model, not axioms.
PARAMS = {
    "schumann_hz": 7.83,         # hypothesis: a coupling frequency
    "phi_hz": 432.0,             # hypothesis: another coupling
    "third_hz": 963.0,           # hypothesis: another coupling
    "human_baseline_hz": 55.0,   # hypothesis: a coupling near human heart rate
    "mineral_hz": 34.4,          # hypothesis: another coupling
}


class FrequencyCoupler:
    """Parallel state. Never modifies ψ_current."""

    def __init__(self, axis_names: list, dim: int = 16, dt: float = 0.05):
        self.axis_names = axis_names
        self.dim = dim
        self.dt = dt
        # Phase per axis.
        self.phases = {name: 0.0 for name in axis_names}
        # Last spectrum (for inspection only).
        self.last_spectrum: dict = {}

    def step(self, dt: float = None):
        """Advance the phases by dt. Does not touch ψ_current."""
        if dt is None:
            dt = self.dt
        for name in self.phases:
            self.phases[name] += dt

    def reset(self):
        for name in self.phases:
            self.phases[name] = 0.0

    def standing_wave_spectrum(self) -> dict:
        """Return a snapshot of the phases. Toy implementation."""
        self.last_spectrum = dict(self.phases)
        return self.last_spectrum
