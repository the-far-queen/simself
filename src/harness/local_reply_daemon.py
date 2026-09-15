"""
Local reply daemon — polls telegram inbox, calls LM Studio (localhost:1234),
writes reply to outbox. Bot picks up and sends.

LM Studio server runs OpenAI-compatible API. Model: qwen2.5-coder-7b@q4_k_m
(loaded by 'lms load'). No tokens billed to minimax.

Usage: python local_reply_daemon.py
Single instance: vault/40-scratch/local_reply_daemon.lock
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

INBOX_ROOT = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\inbox")
OUTBOX_ROOT = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\outbox")
LOCK_PATH = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\local_reply_daemon.lock")
SEEN_PATH = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\local_reply_daemon.seen")
LOG_PATH = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\local_reply_daemon.log")

LMSTUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL = "qwen2.5-coder-7b@q4_k_m"
POLL_SEC = 2.0
MAX_CHARS = 1000
SYSTEM_PROMPT = (
    "you are hermes, bobby's writing admin. terse, lowercase, no sycophancy. "
    "20-line reply cap. answer bobby's question directly. if unclear, ask one short question. "
    "no headers, no markdown decoration unless asked."
)


def _log(msg: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} {msg}\n"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line)
    print(line, end="")


def load_seen() -> set[str]:
    if SEEN_PATH.exists():
        return set(SEEN_PATH.read_text(encoding="utf-8").splitlines())
    return set()


def save_seen(seen: set[str]) -> None:
    SEEN_PATH.write_text("\n".join(sorted(seen)), encoding="utf-8")


def acquire_lock() -> bool:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(str(LOCK_PATH), flags)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        return False


def release_lock() -> None:
    try:
        if LOCK_PATH.exists() and LOCK_PATH.read_text().strip() == str(os.getpid()):
            LOCK_PATH.unlink()
    except OSError:
        pass


def call_llm(user_text: str) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text[:MAX_CHARS]},
        ],
        "temperature": 0.6,
        "max_tokens": 300,
        "stream": False,
    }
    req = urllib.request.Request(
        LMSTUDIO_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"].strip()


def main() -> int:
    if not acquire_lock():
        print(f"another local_reply_daemon holds {LOCK_PATH}. exiting.", file=sys.stderr)
        return 2

    INBOX_ROOT.mkdir(parents=True, exist_ok=True)
    OUTBOX_ROOT.mkdir(parents=True, exist_ok=True)
    _log("daemon started. polling every %.1fs" % POLL_SEC)

    seen = load_seen()
    try:
        while True:
            try:
                for chat_dir in INBOX_ROOT.iterdir():
                    if not chat_dir.is_dir():
                        continue
                    chat_id = chat_dir.name
                    out_chat = OUTBOX_ROOT / chat_id
                    out_chat.mkdir(parents=True, exist_ok=True)
                    for msg in sorted(chat_dir.glob("*.md")):
                        key = str(msg)
                        if key in seen:
                            continue
                        text = msg.read_text(encoding="utf-8").strip()
                        # strip the inbound header
                        body = text.split("\n\n", 1)[-1].strip()
                        if not body:
                            body = "(empty)"
                        seen.add(key)
                        save_seen(seen)

                        stem = msg.stem
                        reply_path = out_chat / f"{stem}.reply.md"
                        if reply_path.exists():
                            _log(f"skip {stem} (reply exists)")
                            continue

                        _log(f"replying to msg {stem}: {body[:80]!r}")
                        try:
                            reply = call_llm(body)
                        except urllib.error.URLError as e:
                            reply = f"(lmstudio unreachable: {e})"
                        except Exception as e:
                            reply = f"(llm error: {type(e).__name__}: {e})"

                        reply_path.write_text(reply + "\n", encoding="utf-8")
                        _log(f"wrote {reply_path.name} ({len(reply)} chars)")
            except Exception as e:
                _log(f"loop error: {e}")
            time.sleep(POLL_SEC)
    except KeyboardInterrupt:
        _log("daemon stopping")
    finally:
        release_lock()
    return 0


if __name__ == "__main__":
    sys.exit(main())