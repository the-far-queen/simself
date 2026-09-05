"""
resolution.py — Bounded MLP that maps a delta vector to a correction.

The ResolutionOperator is the "bounded correction" step from FieldCore.md §1:
given the current displacement from psi_0, produce a bounded update. The
output is ALPHA-scaled and norm-clamped to 0.45 so a runaway input cannot
knock psi_current off the constitutional manifold.

Uses torch if available, otherwise a 2-layer tanh linear stack in numpy.
"""
from __future__ import annotations

import math
from typing import Optional

import numpy as np

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from .constitution import ALPHA, DIM


class ResolutionOperator:
    """Bounded MLP: linear -> activation -> linear, ALPHA-scaled, norm-clamped."""

    def __init__(self, dim: int = DIM, use_torch: bool = True, seed: int = 42):
        self.dim = dim
        self.use_torch = use_torch and TORCH_AVAILABLE
        if self.use_torch:
            torch.manual_seed(seed)
            self.torch_module = nn.Sequential(
                nn.Linear(dim, dim),
                nn.GELU(),
                nn.Linear(dim, dim),
            )
        else:
            rng = np.random.default_rng(seed)
            self._w1 = rng.normal(0, 1.0 / math.sqrt(dim), size=(dim, dim))
            self._w2 = rng.normal(0, 1.0 / math.sqrt(dim), size=(dim, dim))

    def __call__(self, delta: np.ndarray) -> np.ndarray:
        if self.use_torch:
            with torch.no_grad():
                t = torch.tensor(delta, dtype=torch.float32).unsqueeze(0)
                out = self.torch_module(t).squeeze(0).numpy()
        else:
            h = np.tanh(self._w1 @ delta)
            out = self._w2 @ h
        out = ALPHA * out
        mag = np.linalg.norm(out)
        if mag > 0.45:
            out *= 0.45 / mag
        return out
