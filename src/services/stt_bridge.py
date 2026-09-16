"""
stt_bridge.py — Voice → text → Hermes inbox (per Bobby 2026-09-16).

Bobby wants to speak and have the transcript land in the same Hermes inbox
file that the Telegram bot reads. No TTS — Bobby reads the reply in the
terminal.

Pipeline:
1. Capture audio from the microphone (sounddevice).
2. Voice-activity detection: record while the user is speaking; stop on
   silence (RMS below threshold for N seconds).
3. faster-whisper transcription.
4. Append the transcript to .hermes/inbox.txt (one line per utterance).
5. Print the latest outbox.txt entry to the terminal.
6. Repeat.

Hermes-side:
- Some process (Hermes CLI, a Claude/GPT/DeepSeek session, or a Telegram
  text bot) reads .hermes/inbox.txt, processes each line, and writes replies
  to .hermes/outbox.txt.
- This bridge writes to inbox. The other side writes to outbox. We poll
  outbox and print new lines.

Run:
    python simself/src/services/stt_bridge.py
    # speak. transcriptions appear in the terminal as "you: <text>".
    # replies appear as "hermes: <text>".
    # Ctrl+C to stop.
"""
from __future__ import annotations

import os
import sys
import time
import wave
import tempfile
from pathlib import Path

import numpy as np
import sounddevice as sd


HERMES_DIR = Path("C:/Users/Admin/simself/.hermes")
INBOX = HERMES_DIR / "inbox.txt"
OUTBOX = HERMES_DIR / "outbox.txt"

# Mic device: Microphone (Realtek HD Audio Mic input) — index 6 on this box.
DEFAULT_INPUT_DEVICE = 1  # Line In (Realtek HD) — Zoom H1 headphone-out

# Audio params.
SAMPLE_RATE = 16000  # Whisper expects 16kHz.
CHANNELS = 1
DTYPE = "int16"

# Voice activity detection.
SILENCE_THRESHOLD = 500  # RMS amplitude threshold (int16, 0..32767).
SILENCE_DURATION = 1.5    # Seconds of silence before stopping.
MIN_RECORD_SECONDS = 0.5  # Don't stop before this.
MAX_RECORD_SECONDS = 30.0  # Cap utterance length.

# Whisper model (override via env WHISPER_MODEL).
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "tiny.en")
WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")


def list_input_devices():
    import sounddevice as sd
    print("Input devices:", flush=True)
    for i, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] > 0:
            print(f"  [{i}] {dev['name']} (sr={int(dev['default_samplerate'])})", flush=True)


def ensure_dirs():
    HERMES_DIR.mkdir(parents=True, exist_ok=True)
    if not INBOX.exists():
        INBOX.touch()
    if not OUTBOX.exists():
        OUTBOX.touch()


def record_utterance(device: int) -> np.ndarray:
    """Record until SILENCE_DURATION seconds of silence or MAX_RECORD_SECONDS."""
    print("listening...", flush=True)
    chunks = []
    silence_start = None
    started_at = time.time()
    last_voice_at = started_at
    block_size = int(SAMPLE_RATE * 0.1)  # 100ms blocks.
    with sd.InputStream(
        device=device,
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=DTYPE,
        blocksize=block_size,
    ) as stream:
        while True:
            block, _ = stream.read(block_size)
            chunks.append(block.copy())
            rms = float(np.sqrt(np.mean(block.astype(np.float32) ** 2)))
            now = time.time()
            if rms > SILENCE_THRESHOLD:
                last_voice_at = now
                silence_start = None
            else:
                if silence_start is None:
                    silence_start = now
                elapsed_silence = now - silence_start
                elapsed_total = now - started_at
                elapsed_voice = now - last_voice_at
                if (elapsed_silence >= SILENCE_DURATION and
                    elapsed_total >= MIN_RECORD_SECONDS and
                    elapsed_voice >= MIN_RECORD_SECONDS):
                    break
                if elapsed_total >= MAX_RECORD_SECONDS:
                    break
    if not chunks:
        return np.zeros((0,), dtype=np.int16)
    audio = np.concatenate(chunks).flatten()
    return audio


def transcribe(audio: np.ndarray) -> str:
    """Transcribe int16 PCM audio at 16kHz via faster-whisper."""
    if audio.size == 0:
        return ""
    # Lazy import to keep startup fast.
    from faster_whisper import WhisperModel
    if not hasattr(transcribe, "_model"):
        transcribe._model = WhisperModel(
            WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE,
        )
    # Write to a temp WAV.
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
        with wave.open(f, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # int16
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio.tobytes())
    try:
        segments_iter, info = transcribe._model.transcribe(path, beam_size=5)
        parts = [seg.text for seg in segments_iter]
        return " ".join(parts).strip()
    finally:
        os.unlink(path)


def append_inbox(text: str):
    if not text:
        return
    with INBOX.open("a", encoding="utf-8") as f:
        f.write(text.strip() + "\n")
    print(f"you: {text}", flush=True)


def poll_outbox() -> str | None:
    """Return the last line of outbox, or None if empty."""
    if not OUTBOX.exists():
        return None
    text = OUTBOX.read_text(encoding="utf-8")
    if not text.strip():
        return None
    return text.strip().splitlines()[-1]


def main():
    ensure_dirs()
    list_input_devices()
    print(f"\nUsing input device [{DEFAULT_INPUT_DEVICE}].", flush=True)
    print("Speak. Ctrl+C to stop.\n", flush=True)
    try:
        while True:
            audio = record_utterance(DEFAULT_INPUT_DEVICE)
            if audio.size == 0:
                continue
            text = transcribe(audio)
            if not text:
                continue
            append_inbox(text)
            # Poll outbox briefly.
            time.sleep(0.3)
            reply = poll_outbox()
            if reply:
                print(f"hermes: {reply}", flush=True)
    except KeyboardInterrupt:
        print("\nstopped.", flush=True)


if __name__ == "__main__":
    main()
