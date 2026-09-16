"""
semantic_chunking_layer.py — language intake is intact spans (per Grok Part II).

The chunker yields an intact span. Embed, classify, cost to ground, admit/commit/
refuse. BPE may exist inside the external model; it is not the stored unit.

This file is the chunker; the gate/ingest lives in constitutional/lexicon/ingest.py.
"""

from __future__ import annotations

from typing import List


def chunk(text: str) -> List[str]:
    """Split text into intact spans.

    The previous version tried to align with BPE subword boundaries. Per Grok
    (segment 02): the stored unit is a span, not a subword. Whitespace split
    is the smallest clean unit.
    """
    return [s.strip() for s in text.splitlines() if s.strip()]


def chunk_sentences(text: str) -> List[str]:
    """Sentence-level chunking. Naive but adequate for the lexicon."""
    out: List[str] = []
    buf: List[str] = []
    for tok in text.split():
        buf.append(tok)
        if tok.endswith((".", "!", "?")):
            out.append(" ".join(buf).strip())
            buf = []
    if buf:
        out.append(" ".join(buf).strip())
    return [s for s in out if s]
