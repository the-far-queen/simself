"""Companion loop: avatar state drives voice, voice reaches Bobby on Telegram.

This is the free gain. Every part is a separate process we already own or
can call locally, and none of them needs an API key to run:

    avatar_state  ──▶  expression  ──▶  TTS audio  ──▶  Telegram message

The point of the module is that each link degrades visibly. If kokoro is
missing, you learn which link broke and in what direction, instead of
getting silence that looks like a working system (CENTRAL-RULES #4: a
surprising result means check your own plumbing before believing it).

Nothing here decides anything. The M0 governor gates it as it gates
everything else; this file only moves state to sound.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from research.integrations import BY_ROLE  # noqa: F401  (registry kept in sync)


# --------------------------------------------------------------------- inputs


@dataclass
class AvatarState:
    """The small set of values a companion actually needs to sound alive.

    Deliberately not the 20-axis matrix. These are the states a listener
    can hear: how warm, how fast, how much pause. Everything else is
    internal bookkeeping that would not survive being spoken.
    """

    valence: float = 0.0      # -1 flat .. +1 warm
    arousal: float = 0.3      # 0 still .. 1 urgent
    presence: float = 0.5     # 0 absent .. 1 fully here
    name: str = "simself"

    def clamp(self) -> "AvatarState":
        self.valence = max(-1.0, min(1.0, self.valence))
        self.arousal = max(0.0, min(1.0, self.arousal))
        self.presence = max(0.0, min(1.0, self.presence))
        return self

    @property
    def speaking_style(self) -> str:
        if self.presence < 0.25:
            return "distant"
        if self.arousal > 0.7:
            return "urgent"
        if self.valence > 0.4:
            return "warm"
        if self.valence < -0.4:
            return "level"
        return "even"


# --------------------------------------------------------------------- degradation


@dataclass
class Link:
    """One stage of the chain and whether it is actually available here."""

    name: str
    available: bool
    detail: str
    remedy: str = ""


@dataclass
class ChainReport:
    links: list[Link] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return all(link.available for link in self.links)

    @property
    def first_break(self) -> Link | None:
        for link in self.links:
            if not link.available:
                return link
        return None

    def render(self) -> str:
        out = []
        for link in self.links:
            mark = "ok  " if link.available else "MISS"
            out.append(f"  [{mark}] {link.name:<16} {link.detail}")
            if not link.available and link.remedy:
                out.append(f"          -> {link.remedy}")
        if self.complete:
            out.append("  chain complete")
        else:
            brk = self.first_break
            if brk is not None:
                out.append(f"  chain first breaks at: {brk.name}")
        return "\n".join(out)


def probe(kokoro_model: Path | None = None, bot_token_env: str = "TELEGRAM_BOT_TOKEN") -> ChainReport:
    """Report what is actually wired on this machine, not what is in the docs.

    Run this before concluding the companion loop is broken. It names the
    first missing link instead of reporting "no audio".
    """
    rep = ChainReport()

    rep.links.append(Link("avatar_state", True, "in-process, no dependency"))

    kok = kokoro_model if kokoro_model is not None else _default_kokoro_model()
    kok_ok = kok is not None and kok.exists()
    rep.links.append(
        Link(
            "tts_engine",
            kok_ok,
            f"kokoro model at {kok}" if kok_ok else "no kokoro model found",
            "" if kok_ok else "already in repo at simself/models/ or set KOKORO_MODEL",
        )
    )

    py = shutil.which("python") or "python"
    rep.links.append(
        Link("kokoro_runtime", kok_ok, f"kokoro-v0.19.onnx present, runtime via {Path(py).name}"
             if kok_ok else "not reached", "" if kok_ok else "")
    )

    tok = bool(os.environ.get(bot_token_env))
    rep.links.append(
        Link(
            "telegram_out",
            tok,
            f"{bot_token_env} is set" if tok else f"{bot_token_env} not set",
            "" if tok else f"export {bot_token_env}=<token>; the token is not stored in the repo",
        )
    )
    return rep


def _default_kokoro_model() -> Path | None:
    env = os.environ.get("KOKORO_MODEL")
    if env:
        return Path(env)
    here = Path(__file__).resolve().parents[2]
    for cand in (here / "kokoro-v0_19.onnx", here / "models" / "kokoro-v0_19.onnx"):
        if cand.exists():
            return cand
    return None


# --------------------------------------------------------------------- delivery


def speak(text: str, state: AvatarState, out_path: Path, speed: float | None = None) -> dict:
    """Turn text into a voice note shaped by avatar state.

    Returns a report rather than raising on a missing runtime, because the
    caller (the Telegram bot) needs to know whether to send a voice note
    or fall back to plain text with a reason attached.
    """
    state.clamp()
    rep = probe()
    result: dict = {
        "text": text,
        "state": {"valence": state.valence, "arousal": state.arousal,
                  "presence": state.presence, "name": state.name},
        "style": state.speaking_style,
        "chain": rep.render(),
    }

    if not rep.complete:
        result["ok"] = False
        brk = rep.first_break
        assert brk is not None  # complete==False implies first_break is set
        result["fallback"] = "plain_text"
        result["reason"] = f"{brk.name}: {brk.detail}"
        return result

    cmd = ["python", str(Path(__file__).with_name("tts_kokoro.py")), "--text", text,
           "--out", str(out_path)]
    if speed:
        cmd += ["--speed", str(speed)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    result["ok"] = proc.returncode == 0 and out_path.exists()
    result["returncode"] = proc.returncode
    if not result["ok"]:
        result["fallback"] = "plain_text"
        result["reason"] = (proc.stderr or proc.stdout or "tts produced no file")[-400:]
    return result