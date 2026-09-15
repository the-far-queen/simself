"""
Kokoro TTS — one-shot voice generator for bobby-video-pipeline.
Usage: python tts_kokoro.py --text "..." --out path.wav [--voice af_heart]
"""
import argparse
import sys
from pathlib import Path
import soundfile as sf
from kokoro_onnx import Kokoro

DEFAULT_MODEL = Path(r"C:\Users\Admin\kokoro_models\kokoro-v1.0.onnx")
DEFAULT_VOICES = Path(r"C:\Users\Admin\kokoro_models\voices-v1.0.bin")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--text", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--voice", default="af_heart")
    p.add_argument("--speed", type=float, default=1.0)
    p.add_argument("--model", default=str(DEFAULT_MODEL))
    p.add_argument("--voices", default=str(DEFAULT_VOICES))
    args = p.parse_args()

    kokoro = Kokoro(args.model, args.voices)
    samples, sample_rate = kokoro.create(
        args.text, voice=args.voice, speed=args.speed, is_phonemes=False
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), samples, sample_rate)
    dur = len(samples) / sample_rate
    print(f"wrote {out} ({len(samples)} samples, {dur:.2f}s, {sample_rate}Hz)")
    return 0


if __name__ == "__main__":
    sys.exit(main())