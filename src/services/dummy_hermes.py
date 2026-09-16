"""
dummy_hermes.py — Minimal echo reply for testing the STT bridge.

Reads .hermes/inbox.txt, writes an echo reply to .hermes/outbox.txt 1 second
later. Use this to test the STT bridge end-to-end without needing Hermes CLI.

    python simself/src/services/stt_bridge.py    # in one terminal
    python simself/src/services/dummy_hermes.py  # in another terminal
    # speak; you should see "you: <text>" then "hermes: echo <text>" appear.
"""
from __future__ import annotations

import time
from pathlib import Path

HERMES_DIR = Path("C:/Users/Admin/simself/.hermes")
INBOX = HERMES_DIR / "inbox.txt"
OUTBOX = HERMES_DIR / "outbox.txt"


def main():
    print(f"Echoing inbox → outbox (1s delay per line).", flush=True)
    seen = 0
    last_mtime = 0.0
    while True:
        if not INBOX.exists():
            time.sleep(0.5)
            continue
        mtime = INBOX.stat().st_mtime
        if mtime > last_mtime:
            lines = INBOX.read_text(encoding="utf-8").splitlines()
            for line in lines[seen:]:
                if line.strip():
                    time.sleep(1.0)
                    with OUTBOX.open("a", encoding="utf-8") as f:
                        f.write(f"echo: {line}\n")
                    print(f"echoed: {line}", flush=True)
            seen = len(lines)
            last_mtime = mtime
        time.sleep(0.3)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("stopped.", flush=True)
