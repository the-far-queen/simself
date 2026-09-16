"""
confabulation_filter.py — detect and refuse fluent-but-empty spans (per Grok).

A confabulation is a span that looks helpful but contains no commitment or
refusal pattern. The filter checks the unit type from the lexicon; if the
unit is classified as OTHER and the cosine to ψ₀ is below τ, the filter
marks it as confabulation.

This filter is invoked by the canonical SimSelf.observe via ingest. It is
not a replacement for the gate; it is a post-classifier that adds a
`confabulation: bool` flag to the verdict.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from .lexicon.ingest import gate_m0
from .psb_primitives import classify_span, UnitType


def is_confabulation(span: str, emb: np.ndarray, psi0: np.ndarray,
                     min_cos: float = 0.4) -> bool:
    """Return True iff the span is fluent-but-empty."""
    utype = classify_span(span)
    if utype != UnitType.OTHER:
        return False
    # OTHER + low cosine = confabulation
    n = float(np.linalg.norm(emb))
    n0 = float(np.linalg.norm(psi0))
    if n == 0 or n0 == 0:
        return True
    if n > 4.0 or n == 0.0 or n0 == 0.0:
        return True  # confabulation if the embed is empty or huge
    cos = float(np.dot(emb, psi0) / (n * n0))
    return cos < min_cos
