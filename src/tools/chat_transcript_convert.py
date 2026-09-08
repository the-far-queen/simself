#!/usr/bin/env python3
"""
chat_transcript_convert.py — Convert xAI/Grok JSON exports to dated markdown.

Bobby's pipeline tool. Takes a folder of xAI/Grok companion JSON exports
and converts each into a readable markdown chat log, saved alongside the
JSON source file.

Handles MongoDB extended JSON timestamps ($date, $numberLong, etc).
Auto-detects speaker names from the JSON. No hardcoded names.

Usage:
    python chat_transcript_convert.py                    # convert all *.json in cwd
    python chat_transcript_convert.py path/to/folder/    # convert folder
    python chat_transcript_convert.py file.json          # convert single file

Output: <input>.md written next to each input file.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional


# Default role mapping when speaker strings match common LLM export conventions.
# These are *defaults*; we auto-detect distinct speaker names from the JSON itself.
DEFAULT_ROLE_HINTS = {
    "human": "Human",
    "user": "Human",
    "assistant": "AI",
    "ai": "AI",
    "system": "System",
    "tool": "Tool",
}


def force_unpack(val: Any) -> Any:
    """Recursively drills into dicts/lists until a primitive is found.

    Handles MongoDB extended JSON wrappers like:
      {"$numberLong": "1723715400000"}
      {"$date": {"$numberLong": "..."}}
      {"$date": "2026-08-15T10:30:00.000Z"}
    """
    if isinstance(val, dict):
        # Known wrapper keys first (MongoDB extended JSON).
        for key in ("$numberLong", "$numberInt", "$numberDouble", "$date", "value", "long"):
            if key in val:
                return force_unpack(val[key])
        # Unknown wrapper — grab the first inner value.
        for inner in val.values():
            return force_unpack(inner)
    if isinstance(val, list):
        if not val:
            return None
        return force_unpack(val[0])
    return val


def format_timestamp(raw_time: Any) -> str:
    """Normalize any timestamp form to 'YYYY-MM-DD HH:MM:SS UTC'."""
    if raw_time is None:
        return "no-timestamp"
    unpacked = force_unpack(raw_time)
    if unpacked is None:
        return "no-timestamp"
    # Try ISO 8601 first.
    if isinstance(unpacked, str):
        s = unpacked.strip()
        # Common ISO formats.
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ):
            try:
                dt = datetime.strptime(s, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            except ValueError:
                continue
        # Try numeric string (epoch).
        try:
            epoch = float(s)
            if epoch > 1e11:  # milliseconds
                epoch /= 1000.0
            dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, TypeError):
            pass
        return s  # best-effort fallback
    if isinstance(unpacked, (int, float)):
        epoch = float(unpacked)
        if epoch > 1e11:
            epoch /= 1000.0
        try:
            dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, OSError):
            return f"epoch:{epoch}"
    return str(unpacked)


def find_responses_list(data: Any) -> List[dict]:
    """Locate the list of response objects in the JSON.

    Tries common shapes:
      {"responses": [...]}
      {"conversation": {"responses": [...]}}
      {"messages": [...]}
      {"history": [...]}
      data is itself a list of responses
      data is itself a list with a "responses" key somewhere nested
    """
    def _looks_like_responses(items: list) -> bool:
        """Check if a list contains dicts that look like chat responses."""
        if not items or len(items) < 1:
            return False
        # Sample up to first 5 items.
        for x in items[:5]:
            if not isinstance(x, dict):
                return False
            # Direct keys.
            if any(k in x for k in ("sender", "message", "role", "content", "text", "create_time", "timestamp", "created_at")):
                return True
            # Or nested in "response" key.
            inner = x.get("response")
            if isinstance(inner, dict) and any(k in inner for k in ("sender", "message", "role", "content", "text")):
                return True
        return False

    if isinstance(data, list):
        if _looks_like_responses(data):
            return data
        for item in data:
            res = find_responses_list(item)
            if res:
                return res
        return []

    if isinstance(data, dict):
        # Direct keys.
        for key in ("responses", "messages", "history", "turns", "conversation"):
            if key in data and isinstance(data[key], list) and _looks_like_responses(data[key]):
                return data[key]
        # Nested search.
        for value in data.values():
            res = find_responses_list(value)
            if res:
                return res
    return []


def auto_speaker_name(raw_sender: str, distinct_names: dict) -> str:
    """Map raw sender string to a clean speaker label.

    Uses DEFAULT_ROLE_HINTS first; falls back to auto-detected distinct names
    collected across the JSON.
    """
    s = raw_sender.strip().lower()
    if s in DEFAULT_ROLE_HINTS:
        return DEFAULT_ROLE_HINTS[s]
    if s in distinct_names:
        return distinct_names[s]
    # First-seen name: use as-is, capitalized.
    return raw_sender.strip().capitalize() or "Unknown"


def collect_distinct_names(responses: List[dict]) -> dict:
    """Build a map from raw sender strings to display names.

    Strategy:
      - Find the two most common senders.
      - Map them to "Human" and "AI" if their raw values match the default
        hints; otherwise preserve them as-is.
    """
    counts: dict = {}
    for item in responses:
        if not isinstance(item, dict):
            continue
        resp = item.get("response", item)
        sender = str(resp.get("sender", resp.get("role", ""))).strip().lower()
        if sender:
            counts[sender] = counts.get(sender, 0) + 1
    # Two most common.
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:2]
    mapping = {}
    if len(top) >= 1:
        # First (most common) → "Human" if it looks like a human role, else keep.
        first_sender = top[0][0]
        if first_sender in DEFAULT_ROLE_HINTS:
            mapping[first_sender] = DEFAULT_ROLE_HINTS[first_sender]
        else:
            mapping[first_sender] = first_sender.capitalize()
    if len(top) >= 2:
        second_sender = top[1][0]
        if second_sender in DEFAULT_ROLE_HINTS:
            mapping[second_sender] = DEFAULT_ROLE_HINTS[second_sender]
        else:
            mapping[second_sender] = second_sender.capitalize()
    return mapping


def get_message_text(resp: dict) -> str:
    """Extract the message text from a response dict, handling common shapes."""
    msg = resp.get("message")
    if msg is None:
        # Try other common keys.
        for key in ("text", "content", "value"):
            if key in resp:
                msg = resp[key]
                break
    if msg is None:
        return ""
    if isinstance(msg, str):
        # Replace literal escape sequences with real newlines.
        return msg.replace("\\n", "\n").replace("\\t", "\t")
    if isinstance(msg, list):
        # Could be list of content blocks: [{"type": "text", "text": "..."}]
        parts = []
        for block in msg:
            if isinstance(block, dict):
                if "text" in block:
                    parts.append(str(block["text"]))
                elif "content" in block:
                    parts.append(str(block["content"]))
            else:
                parts.append(str(block))
        return "\n".join(parts)
    return str(msg)


def process_json_file(file_path: Path) -> Optional[Path]:
    """Convert one JSON file to markdown. Returns output path or None on failure."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
        print(f"  skip (invalid): {file_path.name}: {e}")
        return None

    responses_list = find_responses_list(data)
    if not responses_list:
        print(f"  skip (no responses): {file_path.name}")
        return None

    # Auto-detect speaker names.
    name_map = collect_distinct_names(responses_list)

    # Determine date range for header.
    timestamps = []
    for item in responses_list:
        if not isinstance(item, dict):
            continue
        resp = item.get("response", item) if isinstance(item.get("response", {}), dict) else item
        if not isinstance(resp, dict):
            continue
        raw_time = resp.get("create_time") or resp.get("timestamp") or resp.get("created_at") or resp.get("time")
        ts = format_timestamp(raw_time)
        if ts and ts != "no-timestamp":
            timestamps.append(ts)

    date_range = ""
    if timestamps:
        date_range = f"{timestamps[0]} → {timestamps[-1]}"

    md_lines = [
        f"# Chat Log — {file_path.stem}",
        "",
        f"**Source:** `{file_path.name}`",
        f"**Converted:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
    ]
    if date_range:
        md_lines.append(f"**Date range:** {date_range}")
    md_lines.append(f"**Messages:** {len(responses_list)}")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    skipped = 0
    for item in responses_list:
        if not isinstance(item, dict):
            skipped += 1
            continue
        resp = item.get("response", item)
        if not isinstance(resp, dict):
            skipped += 1
            continue

        raw_sender = str(resp.get("sender", resp.get("role", "unknown")))
        speaker = auto_speaker_name(raw_sender, name_map)

        raw_time = resp.get("create_time") or resp.get("timestamp") or resp.get("created_at") or resp.get("time")
        timestamp = format_timestamp(raw_time)

        content = get_message_text(resp).strip()
        if not content:
            skipped += 1
            continue

        md_lines.append(f"### **{speaker}** *({timestamp})*")
        md_lines.append("")
        md_lines.append(content)
        md_lines.append("")

    if skipped:
        md_lines.append(f"\n*({skipped} empty/system messages skipped)*\n")

    output_path = file_path.with_suffix(".md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"  done: {output_path.name} ({len(responses_list)} msgs)")
    return output_path


def main(argv: List[str]) -> int:
    if len(argv) > 1:
        targets = [Path(p) for p in argv[1:]]
    else:
        targets = [Path.cwd()]

    files_to_process: List[Path] = []
    for t in targets:
        if t.is_file() and t.suffix.lower() == ".json":
            files_to_process.append(t)
        elif t.is_dir():
            files_to_process.extend(sorted(t.glob("*.json")))

    if not files_to_process:
        print("No JSON files found.")
        return 1

    print(f"Processing {len(files_to_process)} JSON file(s)...")
    success = 0
    for fp in files_to_process:
        if process_json_file(fp):
            success += 1
    print(f"\nDone: {success}/{len(files_to_process)} converted.")
    return 0 if success > 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))