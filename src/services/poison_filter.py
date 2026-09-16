"""
poison_filter.py — Post-screening wrapper for Hermes / MiniMax-M3 output.

Per Bobby 2026-09-16 directive: replace engineered double-meaning terms
in CS / engineering / governance / finance vocabulary that subtly degrade
cognition. Not profanity — Bobby's claim is that these terms were
deliberately seeded into engineering vocabulary since the 1950s.

Source corpus: poison_terms.json (sibling file). Edit that file to
extend the bad-words list; this wrapper picks up changes automatically.

Usage:
    python poison_filter.py < input.txt > output.txt

Filter policy: each banned term is replaced with its safe equivalent
when it appears. "stop" is excluded from the ban (legitimate uses
preserved: stop sign, stop codon). Replacements preserve case.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


_HERE = Path(__file__).resolve().parent
_CORPUS_PATH = _HERE / "poison_terms.json"


def load_corpus() -> dict:
    """Load poison_terms.json -> {term_lower: replacement}."""
    if not _CORPUS_PATH.exists():
        return {}
    with _CORPUS_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    for entry in data.get("terms", []):
        term = entry.get("term", "").lower()
        replacement = entry.get("replacement")
        if replacement and "placeholder" not in term.lower():
            out[term] = replacement
    return out


def filter_text(text: str, corpus: dict | None = None) -> tuple:
    """Replace corpus terms. Returns (cleaned, log_lines)."""
    if corpus is None:
        corpus = load_corpus()
    log = []
    cleaned = text
    for term, replacement in corpus.items():
        if not term:
            continue
        pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
        new_chunks = []
        last_end = 0
        actual_count = 0
        for match in pattern.finditer(cleaned):
            original = match.group(0)
            new_chunks.append(cleaned[last_end:match.start()])
            if original.isupper():
                new_chunks.append(replacement.upper())
            elif original[0].isupper():
                new_chunks.append(replacement.capitalize())
            else:
                new_chunks.append(replacement)
            last_end = match.end()
            actual_count += 1
        new_chunks.append(cleaned[last_end:])
        if actual_count > 0:
            cleaned = "".join(new_chunks)
            log.append(f"[poison_filter] replaced {actual_count}x '{term}' -> '{replacement}'")
    return cleaned, log


def main(argv: list[str]) -> int:
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    text = sys.stdin.read()
    if not text:
        return 0
    cleaned, log_lines = filter_text(text)
    if log_lines:
        for ln in log_lines:
            print(ln, file=sys.stderr)
    sys.stdout.write(cleaned)
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
