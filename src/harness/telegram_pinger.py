"""
Telegram inbox notifier — writes a ping file when a new inbox .md arrives.
Bobby's CLI session sees the file in his next turn and checks inbox.

No LLM, no auto-reply. Just a 1-byte ping so Bobby knows there's a msg.
"""
import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path

INBOX = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\inbox")
PING = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\telegram_ping.txt")
LOCK = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\telegram_pinger.lock")
SEEN = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\telegram_pinger.seen")

CHAT_ID = "8736659200"
POLL_SEC = 1.5


def load_seen() -> set[str]:
    if SEEN.exists():
        return set(SEEN.read_text(encoding="utf-8").splitlines())
    return set()


def save_seen(seen: set[str]) -> None:
    SEEN.write_text("\n".join(sorted(seen)), encoding="utf-8")


def main() -> int:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(str(LOCK), flags)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
    except FileExistsError:
        return 2

    seen = load_seen()
    print(f"telegram_pinger started. chat={CHAT_ID} poll={POLL_SEC}s")
    try:
        while True:
            chat_dir = INBOX / CHAT_ID
            if chat_dir.is_dir():
                for msg in chat_dir.glob("*.md"):
                    key = str(msg)
                    if key in seen:
                        continue
                    seen.add(key)
                    save_seen(seen)
                    body = msg.read_text(encoding="utf-8").split("\n\n", 1)[-1].strip()
                    payload = {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "msg_id": msg.stem,
                        "preview": body[:120],
                    }
                    PING.write_text(json.dumps(payload), encoding="utf-8")
                    print(f"PING {msg.stem}: {body[:60]!r}")
            time.sleep(POLL_SEC)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            if LOCK.exists() and LOCK.read_text().strip() == str(os.getpid()):
                LOCK.unlink()
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())