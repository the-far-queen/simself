"""
Inbox watcher — bridges telegram_text_bot.py inbox files to this Hermes session.

Polls vault/40-scratch/inbox/<chat_id>/ for new *.txt files.
For each new message: prints to stdout (this CLI session sees it),
waits for the operator (me) to write a reply to outbox/<chat_id>/<same-stem>.txt,
then the telegram bot picks it up and sends.

Usage:
    python inbox_watcher.py

Single instance guard uses telegram_text_bot.lock path — same one bot holds.
"""
import os
import sys
import time
from pathlib import Path

INBOX_ROOT = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\inbox")
OUTBOX_ROOT = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\outbox")
LOCK_PATH = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\telegram_text_bot.lock")
SEEN = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\inbox_watcher.seen")

POLL_SEC = 1.5


def load_seen() -> set[str]:
    if SEEN.exists():
        return set(SEEN.read_text(encoding="utf-8").splitlines())
    return set()


def save_seen(seen: set[str]) -> None:
    SEEN.write_text("\n".join(sorted(seen)), encoding="utf-8")


def main() -> int:
    if not LOCK_PATH.exists():
        print(f"ERROR: telegram bot not running (no lock at {LOCK_PATH})", file=sys.stderr)
        return 2

    seen = load_seen()
    print(f"watcher started. inbox={INBOX_ROOT} outbox={OUTBOX_ROOT} poll={POLL_SEC}s")
    print(f"already seen: {len(seen)} files")

    while True:
        try:
            for chat_dir in INBOX_ROOT.iterdir():
                if not chat_dir.is_dir():
                    continue
                chat_id = chat_dir.name
                out_chat = OUTBOX_ROOT / chat_id
                out_chat.mkdir(parents=True, exist_ok=True)
                for msg in sorted(chat_dir.glob("*.txt")):
                    key = str(msg)
                    if key in seen:
                        continue
                    seen.add(key)
                    save_seen(seen)
                    text = msg.read_text(encoding="utf-8").strip()
                    stem = msg.stem
                    reply_path = out_chat / f"{stem}.txt"
                    print("\n" + "=" * 60)
                    print(f"INBOX {chat_id}/{msg.name}")
                    print("-" * 60)
                    print(text)
                    print("-" * 60)
                    print(f"reply path: {reply_path}")
                    print("=" * 60)
                    sys.stdout.flush()
        except KeyboardInterrupt:
            print("watcher stopping")
            return 0
        except Exception as e:
            print(f"watch error: {e}", file=sys.stderr)
        time.sleep(POLL_SEC)


if __name__ == "__main__":
    sys.exit(main())