"""simself/src/constitutional/lexicon — geodesic lexicon (per Grok sharpen 2026-09-16).

This module ports the geodesic lexicon from the Grok review (grok2.txt segment 05)
into the SimSelf constitutional tree. It is the only write path for language. The
same gate_m0 predicate must be used by tool calls (K8 enforced via harness/gate.py).
"""
from .ingest import (
    Unit, Verdict, Status, UnitType,
    gate_m0, cost_pair, dist, nearest_committed,
    ingest, embed_bag, classify_span,
)
