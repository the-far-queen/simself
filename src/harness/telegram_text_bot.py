"""
Telegram gateway for Hermes — TEXT ONLY (step 1 of voice-stack rollout).

Differences from telegram_bot.py:
- text only, no STT/TTS, fast startup
- file-based handoff to Hermes session
- single-instance guard (refuses to start if another bot holds the chat_id)
- drops pending updates on start so old missed messages don't replay
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes,
)

TOKEN_PATH = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\50-index\.env.telegram")
INBOX_DIR = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\inbox")
OUTBOX_DIR = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\outbox")
POLL_INTERVAL_SEC = 1.5
REPLY_TIMEOUT_SEC = 600

LOCK_PATH = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\telegram_text_bot.lock")


def load_kv(path: Path) -> dict:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        k, _, v = line.partition("=")
        if k and v:
            out[k.strip()] = v.strip()
    return out


KV = load_kv(TOKEN_PATH)
TOKEN = KV.get("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = int(KV.get("TELEGRAM_BOT_CHAT_ID", "0"))
if not TOKEN:
    raise SystemExit("TELEGRAM_BOT_TOKEN missing in .env.telegram")
if not ALLOWED_CHAT_ID:
    raise SystemExit("TELEGRAM_BOT_CHAT_ID missing in .env.telegram")

INBOX_DIR.mkdir(parents=True, exist_ok=True)
OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
(INBOX_DIR / str(ALLOWED_CHAT_ID)).mkdir(parents=True, exist_ok=True)
(OUTBOX_DIR / str(ALLOWED_CHAT_ID)).mkdir(parents=True, exist_ok=True)

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
log = logging.getLogger("telegram_text_bot")


def acquire_lock():
    """Single-instance guard using atomic file create (O_CREAT|O_EXCL)."""
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(str(LOCK_PATH), flags)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
    except FileExistsError:
        # lock exists — check if owner is alive
        try:
            old_pid = int(LOCK_PATH.read_text().strip())
        except (ValueError, OSError):
            old_pid = 0
        if old_pid and _pid_alive(old_pid):
            print(f"another bot is running (pid {old_pid}). refusing to start.", file=sys.stderr)
            sys.exit(2)
        else:
            print(f"removing stale lock (pid {old_pid} gone)")
            LOCK_PATH.unlink()
            fd = os.open(str(LOCK_PATH), flags)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)


def release_lock():
    try:
        if LOCK_PATH.exists() and LOCK_PATH.read_text().strip() == str(os.getpid()):
            LOCK_PATH.unlink()
    except OSError:
        pass


def _pid_alive(pid: int) -> bool:
    try:
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not h:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(h)
        return code.value == STILL_ACTIVE
    except Exception:
        return False


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return
    await update.message.reply_text(
        "Hermes online (text mode). drop_pending_updates on start = clean queue. "
        "single-instance guard = no duplicate bot fights."
    )


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id != ALLOWED_CHAT_ID:
        log.warning(f"rejected text from chat_id={chat_id}")
        return

    msg = update.message
    text = msg.text or ""
    msg_id = msg.message_id

    inbox_file = INBOX_DIR / str(chat_id) / f"{msg_id}.md"
    inbox_file.write_text(
        f"# inbound | chat_id={chat_id} | msg_id={msg_id} | ts={datetime.now(timezone.utc).isoformat()}\n\n{text}\n",
        encoding="utf-8",
    )
    log.info(f"inbox wrote {inbox_file.name} ({len(text)} chars)")

    sent_msg = await msg.reply_text("⏳ thinking...")
    sent_msg_id = sent_msg.message_id

    asyncio.create_task(wait_for_reply(chat_id, msg_id, sent_msg_id, ctx))


async def wait_for_reply(chat_id: int, msg_id: int, ack_msg_id: int, ctx: ContextTypes.DEFAULT_TYPE):
    outbox_file = OUTBOX_DIR / str(chat_id) / f"{msg_id}.reply.md"
    pending_file = OUTBOX_DIR / str(chat_id) / f"{msg_id}.pending"
    start = time.time()
    pending_file.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
    try:
        while time.time() - start < REPLY_TIMEOUT_SEC:
            if outbox_file.exists():
                reply_text = outbox_file.read_text(encoding="utf-8").strip()
                if reply_text.startswith("# "):
                    lines = reply_text.split("\n")
                    body_start = 0
                    for i, ln in enumerate(lines):
                        if not ln.strip():
                            body_start = i + 1
                            break
                    reply_text = "\n".join(lines[body_start:]).strip()
                if not reply_text:
                    reply_text = "(empty reply)"
                try:
                    await ctx.bot.edit_message_text(
                        chat_id=chat_id, message_id=ack_msg_id, text=reply_text[:4000],
                    )
                    log.info(f"reply delivered for msg_id={msg_id} ({len(reply_text)} chars)")
                except Exception as e:
                    log.error(f"edit failed for msg_id={msg_id}: {e}")
                    try:
                        await ctx.bot.send_message(chat_id=chat_id, text=reply_text[:4000])
                    except Exception as e2:
                        log.error(f"send fallback failed: {e2}")
                finally:
                    outbox_file.unlink(missing_ok=True)
                return
            await asyncio.sleep(POLL_INTERVAL_SEC)
        await ctx.bot.edit_message_text(
            chat_id=chat_id, message_id=ack_msg_id,
            text=f"⏱️ no reply within {REPLY_TIMEOUT_SEC // 60} min — Hermes session may be inactive.",
        )
        log.warning(f"reply timeout for msg_id={msg_id}")
    finally:
        pending_file.unlink(missing_ok=True)


def main():
    acquire_lock()
    log.info(f"starting telegram text bot. chat_id={ALLOWED_CHAT_ID}")
    log.info(f"inbox:  {INBOX_DIR / str(ALLOWED_CHAT_ID)}")
    log.info(f"outbox: {OUTBOX_DIR / str(ALLOWED_CHAT_ID)}")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    try:
        log.info("bot ready. send /start from @far_queen_bot on iPhone.")
        # drop_pending_updates=True = clear the getUpdates backlog, no replay of old messages
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    finally:
        release_lock()


if __name__ == "__main__":
    main()
