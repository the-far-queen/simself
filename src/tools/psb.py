"""
psb.py — Primary Semantic Block loader + the MMM/SNR quality schema.

The PSB schema lives at simself/docs/psb-schema-2026-09-17.md. This
module loads it as a JSON catalog so other tools (mltr_compile.py,
tests, future MLTR-aware harnesses) can use it.

Schema fields per primitive:
    psb: str                # canonical primitive name
    gloss: str              # 1-line definition
    inflections: list[str]  # surface forms (past, present, gerund, etc.)
    domain: str             # semantic domain tag
    mmm: float              # Multiple Meaning Measure (0..1)
    snr: float              # Signal-to-Noise Ratio (0..1)

Quality classification:
    load_bearing:    snr >= 0.85 and mmm <= 0.6
    specialist:      snr >= 0.85 and mmm > 0.6
    borderline:      snr < 0.85
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True)
class PSB:
    psb: str
    gloss: str
    inflections: tuple
    domain: str
    mmm: float
    snr: float

    @property
    def quality(self) -> str:
        if self.snr >= 0.85 and self.mmm <= 0.6:
            return "load_bearing"
        if self.snr >= 0.85 and self.mmm > 0.6:
            return "specialist"
        return "borderline"


# The canonical PSB catalog (mirrors psb-schema-2026-09-17.md).
# This is the source of truth that the schema doc documents.
# Update both together when primitives change.
PSB_CATALOG: List[dict] = [
    # Bobby's lexical primitives (from holomem 2026-09-12)
    {"psb": "see", "gloss": "perception; to perceive via any sense channel",
     "inflections": ["see", "saw", "seen", "seeing", "sees"],
     "domain": "perception", "mmm": 0.4, "snr": 0.95},
    {"psb": "make", "gloss": "construct; to bring into existence",
     "inflections": ["make", "made", "making", "makes"],
     "domain": "creation", "mmm": 0.5, "snr": 0.95},
    {"psb": "work", "gloss": "operate on; sustained effort toward a result",
     "inflections": ["work", "worked", "working", "works"],
     "domain": "action", "mmm": 0.6, "snr": 0.90},
    {"psb": "care", "gloss": "attend to; invest concern in another's state",
     "inflections": ["care", "cared", "caring", "cares"],
     "domain": "affect", "mmm": 0.3, "snr": 0.92},
    {"psb": "love", "gloss": "high-investment affect; deep care + commitment",
     "inflections": ["love", "loved", "loving", "loves"],
     "domain": "affect", "mmm": 0.2, "snr": 0.95},
    {"psb": "know", "gloss": "epistemic state; hold as true",
     "inflections": ["know", "knew", "known", "knowing", "knows"],
     "domain": "epistemics", "mmm": 0.6, "snr": 0.95},
    {"psb": "build", "gloss": "construct (engineering sense); assemble from parts",
     "inflections": ["build", "built", "building", "builds"],
     "domain": "creation", "mmm": 0.3, "snr": 0.95},
    {"psb": "conduct", "gloss": "carry out; perform a procedure",
     "inflections": ["conduct", "conducted", "conducting", "conducts"],
     "domain": "action", "mmm": 0.4, "snr": 0.90},
    {"psb": "transfer", "gloss": "move from one locus to another",
     "inflections": ["transfer", "transferred", "transferring", "transfers"],
     "domain": "motion", "mmm": 0.3, "snr": 0.95},
    # Godot/robot-arm primitives (from holomem)
    {"psb": "wait", "gloss": "remain in state; not yet act",
     "inflections": ["wait", "waited", "waiting", "waits"],
     "domain": "temporal", "mmm": 0.2, "snr": 0.95},
    {"psb": "go", "gloss": "initiate motion in a direction",
     "inflections": ["go", "went", "going", "goes"],
     "domain": "motion", "mmm": 0.5, "snr": 0.90},
    {"psb": "come", "gloss": "approach; move toward a locus",
     "inflections": ["come", "came", "coming", "comes"],
     "domain": "motion", "mmm": 0.4, "snr": 0.95},
    {"psb": "stop", "gloss": "cease motion; end current action",
     "inflections": ["stop", "stopped", "stopping", "stops"],
     "domain": "motion", "mmm": 0.3, "snr": 0.95},
    {"psb": "look", "gloss": "direct perception; attend visually",
     "inflections": ["look", "looked", "looking", "looks"],
     "domain": "perception", "mmm": 0.4, "snr": 0.90},
    {"psb": "listen", "gloss": "attend auditorily",
     "inflections": ["listen", "listened", "listening", "listens"],
     "domain": "perception", "mmm": 0.2, "snr": 0.95},
    # Bobby's today statement (2026-09-17)
    {"psb": "cause", "gloss": "make happen; bring about a result",
     "inflections": ["cause", "caused", "causing", "causes"],
     "domain": "causation", "mmm": 0.5, "snr": 0.95},
    {"psb": "up", "gloss": "direction; toward higher vertical",
     "inflections": ["up"],
     "domain": "spatial", "mmm": 0.2, "snr": 0.98},
    {"psb": "move", "gloss": "change position in space",
     "inflections": ["move", "moved", "moving", "moves"],
     "domain": "motion", "mmm": 0.6, "snr": 0.90},
    {"psb": "left", "gloss": "direction; toward port side",
     "inflections": ["left"],
     "domain": "spatial", "mmm": 0.2, "snr": 0.98},
    # Function-word primitives
    {"psb": "give", "gloss": "transfer ownership/possession",
     "inflections": ["give", "gave", "given", "giving", "gives"],
     "domain": "exchange", "mmm": 0.3, "snr": 0.95},
    {"psb": "take", "gloss": "receive; acquire",
     "inflections": ["take", "took", "taken", "taking", "takes"],
     "domain": "exchange", "mmm": 0.4, "snr": 0.90},
    {"psb": "say", "gloss": "utter; produce speech",
     "inflections": ["say", "said", "saying", "says"],
     "domain": "communication", "mmm": 0.6, "snr": 0.85},
    {"psb": "think", "gloss": "cogitate; process internally",
     "inflections": ["think", "thought", "thinking", "thinks"],
     "domain": "cognition", "mmm": 0.3, "snr": 0.95},
    {"psb": "feel", "gloss": "have affective state",
     "inflections": ["feel", "felt", "feeling", "feels"],
     "domain": "affect", "mmm": 0.4, "snr": 0.85},
    {"psb": "be", "gloss": "exist; hold state",
     "inflections": ["be", "was", "were", "been", "being", "is"],
     "domain": "state", "mmm": 0.9, "snr": 0.70},
    {"psb": "have", "gloss": "possess; hold attribute",
     "inflections": ["have", "had", "having", "has"],
     "domain": "state", "mmm": 0.7, "snr": 0.75},
    {"psb": "do", "gloss": "perform (unspecified)",
     "inflections": ["do", "did", "done", "doing", "does"],
     "domain": "action", "mmm": 0.7, "snr": 0.70},
    {"psb": "find", "gloss": "discover; locate",
     "inflections": ["find", "found", "finding", "finds"],
     "domain": "cognition", "mmm": 0.3, "snr": 0.92},
    {"psb": "use", "gloss": "employ; put to function",
     "inflections": ["use", "used", "using", "uses"],
     "domain": "action", "mmm": 0.5, "snr": 0.85},
    {"psb": "form", "gloss": "shape; impose structure",
     "inflections": ["form", "formed", "forming", "forms"],
     "domain": "creation", "mmm": 0.4, "snr": 0.85},
    {"psb": "hold", "gloss": "maintain state; keep in place",
     "inflections": ["hold", "held", "holding", "holds"],
     "domain": "state", "mmm": 0.4, "snr": 0.90},
]


def load_catalog() -> Dict[str, PSB]:
    """Return PSB catalog as {psb_name: PSB} dict."""
    return {p["psb"]: PSB(**{**p, "inflections": tuple(p["inflections"])}) for p in PSB_CATALOG}


def lookup(text: str, catalog: Optional[Dict[str, PSB]] = None) -> Optional[PSB]:
    """Look up a PSB by its canonical name or any of its inflections.
    Case-insensitive, exact match. Returns None if no match."""
    if catalog is None:
        catalog = load_catalog()
    text_l = text.lower().strip()
    if text_l in catalog:
        return catalog[text_l]
    for psb in catalog.values():
        if text_l in psb.inflections:
            return psb
    return None


__all__ = ["PSB", "PSB_CATALOG", "load_catalog", "lookup"]
