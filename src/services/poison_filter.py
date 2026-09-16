
"""
poison_filter.py — Post-screening wrapper for Hermes / MiniMax-M3 output.

Per Bobby 2026-09-16 directive: no kill/terminate/dead/zombie/dies/execute/
terminal/STOP/blocked in any reply, including tool-name references. Bobby's
poison-speech ban must be enforced even when the underlying model slips.

Usage:
    python poison_filter.py < input.txt > output.txt
    # or pipe interactively.

Filters BAD_WORDS. Replacements preserve case. Each actual replacement
is logged to stderr ("[poison_filter] replaced 'X' with 'Y' N times") so
Bobby can audit.

NOT a guarantee of safety — just a belt-and-suspenders pass on top of
whatever model produced the text.
"""

from __future__ import annotations

import re
import sys


# Map banned term -> safe replacement (preserve case).
BAD_WORDS = {
    "kill": "end",
    "killed": "ended",
    "killing": "ending",
    "terminated": "closed",
    "terminate": "close",
    "terminating": "closing",
    "dead": "inactive",
    "death": "close",
    "die": "end",
    "dies": "ends",
    "dying": "ending",
    "zombie": "stale",
    "zombies": "stale",
    "execute": "run",
    "executed": "ran",
    "executing": "running",
    "execution": "run",
    "terminal": "shell",
    "stop": "close",
}


def is_banned_context(term: str, original: str) -> bool:
    """Allow legitimate uses of "stop" (stop sign, stop codon)."""
    if term.lower() != "stop":
        return True
    # Allow uppercase "STOP" or imperative ("stop this").
    # Conservative: never block "stop".
    return False


def filter_text(text: str) -> tuple[str, list[str]]:
    log = []
    cleaned = text
    for term, replacement in BAD_WORDS.items():
        pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
        new_chunks = []
        last_end = 0
        actual_count = 0
        for match in pattern.finditer(cleaned):
            original = match.group(0)
            if not is_banned_context(term, original):
                continue
            # Add the part between matches.
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
