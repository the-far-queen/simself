"""
grok_plaintext_ingest.py — Ingest plaintext Grok chats (per Bobby 2026-09-16).

Pipeline (mirroring the manual split done for grok1.txt and grok2.txt):
1. Read a plaintext chat .txt file from Desktop/Grok/.
2. Split by topic — heuristic uses ## headers and "Thoughts" / numbered
   "1." / "2." markers that Grok produces.
3. For each section: generate a 1-paragraph summary (heuristic: first
   meaningful sentence after the section break).
4. Chrono-number sections (01-, 02-, ...).
5. Write section files to:
   - Desktop/Grok/md/<chrono>-<date>-<topic>.md
   - vault/50-index/notes/chat-transcripts/grok/<chrono>-<date>-<topic>.md
6. Append a per-file ingestion note to MYSELF.md.
7. Preserve the original .txt untouched.

Per Bobby 2026-09-15 standing directive: chat transcripts are PRIVATE.
Never push chat content to public repos. Never modify the source .txt.

Usage:
    python grok_plaintext_ingest.py <path-to-txt>
    python grok_plaintext_ingest.py Desktop/Grok/grok3.txt
"""

from __future__ import annotations

import hashlib
import os
import re
import sys
from datetime import datetime
from pathlib import Path


HERE = Path(__file__).resolve().parent
DESKTOP_GROK = Path("C:/Users/Admin/Desktop/Grok")
DESKTOP_GROK_MD = DESKTOP_GROK / "md"
VAULT_GROK = Path("C:/Users/Admin/AppData/Local/hermes/vault/10-minimax/50-index/notes/chat-transcripts/grok")
MYSELF_PATH = Path("C:/Users/Admin/AppData/Local/hermes/vault/10-minimax/50-index/MYSELF.md")


SECTION_BREAK_PATTERNS = [
    re.compile(r"^#+\s+(.+)$", re.MULTILINE),  # markdown headers
    re.compile(r"^\d+\.\s+(.+)$", re.MULTILINE),  # numbered lists
    re.compile(r"^Thoughts\s*$", re.MULTILINE),  # Grok's "Thoughts" markers
    re.compile(r"^ok good|^ok so|^now let.s|^let me ", re.MULTILINE | re.IGNORECASE),
]


def find_section_breaks(text: str) -> list[tuple[int, str, str]]:
    """Return [(offset, kind, heading)] for each detected section break."""
    breaks = []
    for pattern in SECTION_BREAK_PATTERNS:
        for m in pattern.finditer(text):
            breaks.append((m.start(), pattern.pattern[:30], m.group(0).strip()))
    breaks.sort(key=lambda x: x[0])
    return breaks


def split_into_sections(text: str) -> list[str]:
    """Split text into sections using detected breaks."""
    breaks = find_section_breaks(text)
    if not breaks:
        return [text]
    sections = []
    prev = 0
    for offset, kind, heading in breaks:
        if offset > prev:
            section_text = text[prev:offset].rstrip()
            if section_text:
                sections.append(section_text)
        prev = offset
    # Tail.
    tail = text[prev:].rstrip()
    if tail:
        sections.append(tail)
    return sections


def summarize(section_text: str, max_chars: int = 600) -> str:
    """Generate a 1-paragraph summary. Heuristic: first meaningful sentence."""
    # Strip whitespace.
    text = section_text.strip()
    # Find the first sentence-ending punctuation after the first 50 chars.
    if len(text) < 50:
        return text
    start = 50
    for punct in [". ", "! ", "? ", "\n\n"]:
        idx = text.find(punct, start)
        if idx > 0:
            return text[start:idx + 1].strip()[:max_chars]
    return text[:max_chars].strip()


def chrono_name(idx: int, source_date: str) -> str:
    """Format: NN-<date>-<topic>.md. Topic is auto-derived from heading or 'topic'."""
    return f"{idx:02d}-{source_date}-topic.md"


def write_section(
    section_text: str,
    summary: str,
    chrono: str,
    source_file: str,
    dest_paths: list[Path],
) -> None:
    """Write a section file to all destinations, md5-identical.

    Normalizes line endings to LF before writing so Windows CRLF doesn't
    cause a mismatch between the computed md5 and the on-disk md5.
    """
    header = f"""# {chrono}

**Source:** {source_file}
**Captured:** {datetime.now().isoformat()}
**Status:** PRIVATE — Grok chat transcript. Never push to public repos.

## 1-paragraph summary

{summary}

## Full text

{section_text}
"""
    # Normalize: replace CRLF with LF.
    normalized = header.replace("\r\n", "\n").replace("\r", "\n")
    md5 = hashlib.md5(normalized.encode("utf-8")).hexdigest()
    for p in dest_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(normalized.encode("utf-8"))
        if hashlib.md5(p.read_bytes()).hexdigest() != md5:
            raise RuntimeError(f"md5 mismatch on {p}")


def append_myself_note(source_file: str, n_sections: int) -> None:
    """Append a per-file ingestion note to MYSELF.md."""
    if not MYSELF_PATH.exists():
        return
    note = (
        f"\n\n---\n\n## Grok ingest — {source_file} — "
        f"{datetime.now().strftime('%Y-%m-%d')}\n\n"
        f"{n_sections} sections written to Desktop/Grok/md/ + vault/50-index/notes/chat-transcripts/grok/.\n"
    )
    with MYSELF_PATH.open("a", encoding="utf-8") as f:
        f.write(note)


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: grok_plaintext_ingest.py <path-to-txt>")
        return 1
    src = Path(argv[0]).resolve()
    if not src.exists():
        print(f"not found: {src}")
        return 1
    text = src.read_text(encoding="utf-8", errors="replace")
    sections = split_into_sections(text)
    if not sections:
        print("no sections detected; aborting")
        return 1
    # Source date from filename or file mtime.
    source_date = datetime.fromtimestamp(src.stat().st_mtime).strftime("%Y-%m-%d")
    name = src.name
    for idx, section_text in enumerate(sections, 1):
        summary = summarize(section_text)
        chrono = chrono_name(idx, source_date)
        dest_paths = [
            DESKTOP_GROK_MD / chrono,
            VAULT_GROK / chrono,
        ]
        write_section(section_text, summary, chrono, name, dest_paths)
    append_myself_note(name, len(sections))
    print(f"wrote {len(sections)} sections for {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
