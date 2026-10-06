"""
fetch_kokoro.py — fetch the local voice stack.

Why this exists: the Kokoro-82M weights were committed to git, which
made simself 149 MB and pushed an 84 MB ONNX model to a hosted repo.
Weights belong on disk, not in history. This script puts them back on
disk, reproducibly, from the upstream source.

The model is Apache-2.0 licensed (hexgrad/Kokoro). It is not vendored
into this repo for that reason as well as the size.

    python scripts/fetch_kokoro.py            # fetch if missing
    python scripts/fetch_kokoro.py --force    # refetch
    python scripts/fetch_kokoro.py --check    # report only, fetch nothing
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEST = Path(os.environ.get("SIMSELF_KOKORO_DIR",
                           REPO_ROOT / "models" / "tts" / "kokoro"))

# hexgrad/Kokoro-82M-ONNX, Apache-2.0. Quantized q8f16 is the CPU build.
BASE = "https://huggingface.co/hexgrad/Kokoro-82M-ONNX/resolve/main/"

FILES = {
    "model_q8f16.onnx": BASE + "kokoro-v1_0-ONNX/model_q8f16.onnx",
    "voices256.npz":    BASE + "voices-v1_0.bin",
}


def check() -> bool:
    """report what is present. never downloads."""
    print(f"model_dir: {DEST}")
    ok = True
    for name, url in FILES.items():
        p = DEST / name
        exists = p.is_file()
        size = f"{p.stat().st_size / 1048576:.1f} MB" if exists else "-"
        print(f"  [{'ok' if exists else 'MISSING'}] {name:24s} {size}")
        if exists:
            ok = True
        else:
            ok = False
    # af_sarah.bin is a local voice style vector, not upstream
    voice = DEST / "af_sarah.bin"
    print(f"  [{'ok' if voice.is_file() else 'MISSING'}] af_sarah.bin          "
          f"(local voice vector)")
    return ok


def fetch(name: str, url: str, force: bool) -> bool:
    target = DEST / name
    if target.is_file() and not force:
        print(f"  have {name}")
        return True
    DEST.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".part")
    print(f"  fetching {name} ...")
    try:
        urllib.request.urlretrieve(url, tmp)
        tmp.replace(target)
        mb = target.stat().st_size / 1048576
        print(f"  got {name} ({mb:.1f} MB)")
        return True
    except Exception as e:                      # noqa: BLE001
        print(f"  FAILED {name}: {type(e).__name__}: {e}")
        if tmp.exists():
            tmp.unlink()
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="refetch existing files")
    ap.add_argument("--check", action="store_true", help="report only, fetch nothing")
    args = ap.parse_args()

    if args.check:
        return 0 if check() else 1

    print(f"fetching voice stack into {DEST}")
    ok = True
    for name, url in FILES.items():
        ok = fetch(name, url, args.force) and ok

    if not (DEST / "af_sarah.bin").is_file():
        print("\n  NOTE: af_sarah.bin is a locally-derived voice style vector.")
        print("  It is not published upstream. If you have a copy, place it at:")
        print(f"    {DEST / 'af_sarah.bin'}")
        print("  Without it the service falls back to the shipped voices256.npz.")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
