"""
hermes_watcher.py — Poll the Hermes outbox and print new lines.

Run this in a separate terminal alongside stt_bridge.py to see replies
as they arrive (without polling).

    python simself/src/services/hermes_watcher.py

Reads .hermes/outbox.txt. When the file grows (size or mtime change),
prints the new lines.

Per Bobby 2026-09-16: "minimax replies text we have channel."
"""
from __future__ import annotations

import os
import time
from pathlib import Path

HERMES_DIR = Path("C:/Users/Admin/simself/.hermes")
OUTBOX = HERMES_DIR / "outbox.txt"
INBOX = HERMES_DIR / "inbox.txt"

# Track how many lines we've already printed.
last_count = 0
last_mtime = 0.0


def main():
    global last_count, last_mtime
    print(f"Watching {OUTBOX} for new replies...", flush=True)
    while True:
        if not OUTBOX.exists():
            time.sleep(0.5)
            continue
        mtime = OUTBOX.stat().st_mtime
        if mtime > last_mtime:
            lines = OUTBOX.read_text(encoding="utf-8").splitlines()
            for line in lines[last_count:]:
                if line.strip():
                    print(f"hermes: {line}", flush=True)
            last_count = len(lines)
            last_mtime = mtime
        time.sleep(0.3)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("stopped.", flush=True)
