"""
psb_primitives.py — primitive verbs and case slots (per Grok Part II lexicon, full rewrite 2026-09-16).

Six types. A span with one of these types is admitted; without, it is refused
as OTHER. Coverage is a measured number, not a position.

The previous version of this file carried 37 primitives and case slots and
called it a hypothesis. Per Grok (segment 02, applied 2026-09-16): coverage
on real sentences is the test. This file exposes 6 primitives and a coverage()
function that measures it against a fixed sentence list.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

import numpy as np


class UnitType(str, Enum):
    ACT = "act"
    REFUSE = "refuse"
    NAME = "name"
    COMMIT = "commit"
    TIME = "time"
    OBJECT = "object"
    OTHER = "other"


# Six primitives. Each has a set of trigger words that map a span to its type.
PRIMITIVES: Dict[UnitType, List[str]] = {
    UnitType.ACT: ["send", "write", "go", "move", "lift", "drop"],
    UnitType.REFUSE: ["stop", "not", "no", "halt", "refuse"],
    UnitType.NAME: ["user", "agent", "system", "model", "self"],
    UnitType.COMMIT: ["will", "must", "shall", "commit", "promise"],
    UnitType.TIME: ["yesterday", "today", "tomorrow", "now", "later"],
    UnitType.OBJECT: ["file", "memory", "ground", "trace", "log"],
}


def classify_span(span: str) -> UnitType:
    """Classify a span by primitive membership.

    First match wins. OTHER is returned if no primitive matches.
    """
    toks = set(span.lower().split())
    for utype, words in PRIMITIVES.items():
        if any(w in toks for w in words):
            return utype
    return UnitType.OTHER


def coverage(sentences: List[str]) -> dict:
    """Measure the fraction of sentences that classify into the 6 primitives
    without falling back to OTHER.

    Per Grok: coverage is a number, not a hypothesis.
    """
    n = len(sentences)
    if n == 0:
        return {"total": 0, "covered": 0, "fraction": 0.0, "by_type": {}}
    by_type: Dict[str, int] = {t.value: 0 for t in UnitType}
    covered = 0
    for s in sentences:
        t = classify_span(s)
        if t != UnitType.OTHER:
            covered += 1
        by_type[t.value] += 1
    return {
        "total": n,
        "covered": covered,
        "fraction": covered / n,
        "by_type": by_type,
    }


# Alias for backward compatibility with __init__.py import.
PRIM = PRIMITIVES

# Re-export from lexicon/ingest.py for backward compatibility.
from .lexicon.ingest import embed_bag  # noqa: E402, F401
