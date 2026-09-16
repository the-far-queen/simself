"""
faster_whisper_stt.py — Local STT service using faster-whisper (per Bobby 2026-09-16).

Per Bobby's hardware plan: RTX 4000 (8GB VRAM). faster-whisper runs on
CPU with int8 quantization; the tiny.en model (~75MB) fits comfortably.

Per Grok master plan: 1-bit gates, modular services. This module exposes
`transcribe(audio_path_or_bytes)` and handles model loading + transcription.

Usage:
    from services.faster_whisper_stt import transcribe
    text = transcribe("audio.wav")
    print(text)
"""
from __future__ import annotations

import io
import os
import time
from pathlib import Path

import numpy as np


DEFAULT_MODEL = "tiny.en"
DEFAULT_DEVICE = "cpu"
DEFAULT_COMPUTE_TYPE = "int8"


_whisper = None


def _get_whisper(model: str = DEFAULT_MODEL, device: str = DEFAULT_DEVICE,
                 compute_type: str = DEFAULT_COMPUTE_TYPE):
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel
        _whisper = WhisperModel(model, device=device, compute_type=compute_type)
    return _whisper


def transcribe(
    audio: str | bytes | Path | np.ndarray,
    model: str = DEFAULT_MODEL,
    beam_size: int = 5,
    language: str | None = None,
) -> tuple[str, dict]:
    """Transcribe audio. Returns (text, info).

    audio can be a file path (str/Path), WAV bytes, or a numpy float32 array.
    """
    model_obj = _get_whisper(model)
    # Handle byte input (WAV).
    if isinstance(audio, (bytes, bytearray)):
        # Write to a temp file. faster_whisper expects a path.
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio)
            audio = f.name
    if isinstance(audio, np.ndarray):
        import tempfile, soundfile as sf
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f, audio, 24000)
            audio = f.name
    t0 = time.perf_counter()
    segments_iter, info = model_obj.transcribe(str(audio), beam_size=beam_size, language=language)
    parts = []
    for seg in segments_iter:
        parts.append(seg.text)
    text = " ".join(parts).strip()
    elapsed = time.perf_counter() - t0
    info_dict = {
        "language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration,
        "elapsed": elapsed,
        "rtf": elapsed / info.duration if info.duration > 0 else 0,
    }
    return text, info_dict


if __name__ == "__main__":
    audio_path = "test_kokoro_service.wav"
    if os.path.exists(audio_path):
        text, info = transcribe(audio_path)
        print(f"text: {text!r}")
        print(f"info: {info}")
