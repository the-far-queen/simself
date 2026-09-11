"""
Telegram gateway for Hermes — voice in / voice out via local STT + TTS.

Block on @BotFather token (Bobby has provided). Chat_id set to Bobby only.
Local-only operation: no cloud APIs for STT/TTS.

Architecture:
  Bobby voice → Telegram .ogg
  → faster-whisper tiny (local) → text
  → POST to Hermes session → response text
  → piper-tts en_US-amy-medium (local) → .wav
  → Telegram voice message reply

Run: python telegram_bot.py
"""

import os
import sys
import asyncio
import logging
import tempfile
import subprocess
from pathlib import Path

from telegram import Update, Bot
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes,
)
from faster_whisper import WhisperModel
from piper import PiperVoice
import wave

# ----- CONFIG -----
TOKEN_PATH = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\50-index\.env.telegram")
VOICE_PATH = Path(r"C:\Users\Admin\.local\share\piper\voices\en_US-amy-medium.onnx")

def load_token():
    for line in TOKEN_PATH.read_text().splitlines():
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("token missing in .env.telegram")

def load_chat_id():
    for line in TOKEN_PATH.read_text().splitlines():
        if line.startswith("TELEGRAM_BOT_CHAT_ID="):
            return int(line.split("=", 1)[1].strip())
    raise SystemExit("chat_id missing in .env.telegram")

TOKEN = load_token()
ALLOWED_CHAT_ID = load_chat_id()

# ----- LOAD MODELS ONCE -----
print("loading faster-whisper tiny (local, CPU int8)...")
stt_model = WhisperModel("tiny", device="cpu", compute_type="int8")

print(f"loading piper voice {VOICE_PATH.name}...")
tts_voice = PiperVoice.load(str(VOICE_PATH))

# ----- PATHS -----
HERMES_SESSION = os.environ.get("HERMES_SESSION_PATH", "")
INBOX_DIR = Path(r"C:\Users\Admin\AppData\Local\hermes\vault\10-minimax\40-scratch\inbox")
INBOX_DIR.mkdir(parents=True, exist_ok=True)


def transcribe(ogg_path: Path) -> str:
    """Convert .ogg to .wav via ffmpeg, then transcribe."""
    wav_path = ogg_path.with_suffix(".wav")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(ogg_path), "-ar", "16000", "-ac", "1", str(wav_path)],
        capture_output=True, check=False,
    )
    if not wav_path.exists():
        return ""
    segments, info = stt_model.transcribe(str(wav_path), beam_size=5, language="en")
    return " ".join(s.text.strip() for s in segments).strip()


def synthesize(text: str, out_path: Path) -> Path:
    """Synthesize text → wav via piper."""
    with wave.open(str(out_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(tts_voice.config.sample_rate)
        tts_voice.synthesize(text, w)
    return out_path


def query_hermes(text: str) -> str:
    """Forward text to active Hermes session and get reply.

    Strategy (this version, simple): save text to inbox file, return ack.
    A separate Hermes session (or future integration) will process the inbox
    and write replies to an outbox folder.
    """
    inbox_file = INBOX_DIR / f"{ALLOWED_CHAT_ID}-{int(asyncio.get_event_loop().time())}.md"
    inbox_file.write_text(f"# inbound from Telegram chat_id={ALLOWED_CHAT_ID}\n\n{text}\n", encoding='utf-8')
    return (
        f"received: {text[:200]}\n\n"
        f"(saved to inbox: {inbox_file.name}. "
        f"this gateway writes to inbox; replies come from a separate "
        f"Hermes session reading inbox + writing outbox.)"
    )


# ----- HANDLERS -----
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return
    await update.message.reply_text(
        "Hermes online. Send text or voice. "
        "STT: faster-whisper tiny (local). TTS: piper en_US-amy-medium (local)."
    )


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return
    text = update.message.text
    reply = query_hermes(text)
    await update.message.reply_text(reply)


async def on_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return

    # download voice
    voice_file = await update.message.voice.get_file()
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        ogg_path = Path(tmp.name)
        await voice_file.download_to_drive(str(ogg_path))

    try:
        text = transcribe(ogg_path)
        if not text:
            await update.message.reply_text("(STT empty)")
            return
        reply = query_hermes(text)
        # synthesize reply audio
        wav_out = Path(tempfile.gettempdir()) / f"reply-{int(asyncio.get_event_loop().time()*1000)}.wav"
        synthesize(reply, wav_out)
        # send voice
        with open(wav_out, "rb") as f:
            await update.message.reply_voice(f)
        # also send text for accessibility
        await update.message.reply_text(f"📝 {text}\n\n💬 {reply}")
    finally:
        for p in [ogg_path, ogg_path.with_suffix(".wav"), wav_out]:
            try:
                if p.exists():
                    p.unlink()
            except OSError:
                pass


async def on_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Save incoming files to inbox for later ingest."""
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return
    doc = update.message.document
    target = INBOX_DIR / doc.file_name
    await (await doc.get_file()).download_to_drive(str(target))
    await update.message.reply_text(f"saved: {target}")


# ----- MAIN -----
def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(MessageHandler(filters.VOICE, on_voice))
    app.add_handler(MessageHandler(filters.Document.ALL, on_document))
    print(f"telegram gateway up. chat_id={ALLOWED_CHAT_ID}. STT+TTS local.")
    app.run_polling()


if __name__ == "__main__":
    main()
