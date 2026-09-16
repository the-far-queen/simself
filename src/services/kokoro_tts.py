"""
kokoro_tts.py — Local TTS service using Kokoro-82M (per Bobby 2026-09-16).

Bobby's rig: 32GB RAM, RTX 4000 (8GB VRAM, Turing). This service runs
Kokoro on CPU first (the q8f16 ONNX model fits in ~500MB and is fast
enough on a modern CPU). GPU acceleration via onnxruntime can be added
later; for now CPU is reliable and avoids the onnxruntime crashes.

Per Bobby's hardware plan (vault/50-index/bobby-minimax-team-2026-09-11):
- RTX 4000 is the local-voice box
- Stay on small/mid models
- Skip 12GB+ TTS like Fish Speech S2 Pro

Per Grok master plan: 1-paragraph summaries, 1-bit gates, layered
memory. This module exposes a single function `synthesize(text, voice)`
and handles model loading, voice loading, and the kokoro-onnx
style_for shape bug (see _style_for_patched below).

Usage:
    from services.kokoro_tts import synthesize
    wav_bytes, sample_rate = synthesize("Hello world", voice="af_sarah")
    with open("out.wav", "wb") as f:
        f.write(wav_bytes)
"""
from __future__ import annotations

import os
import io
import time
from pathlib import Path

import numpy as np
import soundfile as sf


MODEL_DIR = Path("C:/Users/Admin/simself/models/tts/kokoro")
MODEL_PATH = MODEL_DIR / "model_q8f16.onnx"
VOICES_PATH = MODEL_DIR / "voices256.npz"


def _make_voice_dict() -> dict[str, np.ndarray]:
    """Build the voices dict from af_sarah.bin.

    The Kokoro-82M model expects a single style vector per voice.
    We slice the first 256 values from af_sarah.bin and reshape to
    (1, 256). This is sufficient for inference; the rest of the
    131072-float payload is unused.
    """
    af_sarah = np.fromfile(MODEL_DIR / "af_sarah.bin", dtype=np.float32)
    voice = af_sarah[:256].reshape(1, 256)
    return {"af_sarah": voice}


def _load_kokoro():
    """Load the Kokoro ONNX model + voices. Patches _style_for for rank-2."""
    from kokoro_onnx import Kokoro
    kokoro = Kokoro(str(MODEL_PATH), str(VOICES_PATH))

    # Patch _style_for: the upstream version slices voice[i-1] which is
    # rank 1. The ONNX model expects rank 2. Reshape to (1, 256).
    def patched(self, voice, length):
        idx = min(length, len(voice)) - 1
        return voice[idx].reshape(1, -1)
    kokoro._style_for = patched.__get__(kokoro)
    return kokoro


_kokoro = None


def _get_kokoro():
    global _kokoro
    if _kokoro is None:
        _kokoro = _load_kokoro()
    return _kokoro


def synthesize(
    text: str,
    voice: str = "af_sarah",
    speed: float = 1.0,
    lang: str = "en-us",
) -> tuple[bytes, int]:
    """Synthesize speech from text. Returns (wav_bytes, sample_rate)."""
    kokoro = _get_kokoro()
    voice = kokoro.voices[voice]
    t0 = time.perf_counter()
    samples, sample_rate = kokoro.create(
        text, voice=voice, speed=speed, lang=lang,
    )
    duration = time.perf_counter() - t0
    audio_seconds = len(samples) / sample_rate
    rtf = duration / audio_seconds
    # Encode as WAV bytes.
    buf = io.BytesIO()
    sf.write(buf, samples, sample_rate, format="WAV", subtype="PCM_16")
    return buf.getvalue(), sample_rate, rtf


if __name__ == "__main__":
    wav, sr, rtf = synthesize("Hello Bobby. Kokoro is running locally. Local TTS works.")
    out_path = "test_kokoro_service.wav"
    with open(out_path, "wb") as f:
        f.write(wav)
    print(f"wrote {out_path} ({len(wav)} bytes, sr={sr}, rtf={rtf:.2f})")
