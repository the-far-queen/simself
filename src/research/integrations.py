"""Registry of external systems SimSelf integrates or refers to.

Every entry is a real repository, verified against the GitHub API on
2026-10-09, with the fields that decide integration: licence, activity,
and what part of SimSelf it serves. Nothing here is vendored. An entry
that cannot be legally or cleanly used is marked and kept, exactly as a
Layer C claim is kept (see far-math).

Verdict vocabulary
------------------
VENDOR    may be copied into this repo under its own licence
ADAPT     patterns may be reimplemented here, attribution kept
WRAP      may be called as an external process or HTTP service
REFERENCE read and learn from, never copied, never called

Licence reasoning is the load-bearing field. A GPL repo called by an MIT
system is fine (separate processes, no linking). A GPL repo *copied* into
an MIT repo is not.
"""
from __future__ import annotations

from dataclasses import dataclass, field

VENDOR = "VENDOR"
ADAPT = "ADAPT"
WRAP = "WRAP"
REFERENCE = "REFERENCE"


@dataclass(frozen=True)
class External:
    slug: str
    name: str
    stars: int
    licence: str
    pushed: str
    language: str
    role: str
    verdict: str
    serves: str
    note: str = ""
    licence_issue: str = ""

    @property
    def url(self) -> str:
        return f"https://github.com/{self.slug}"

    @property
    def usable(self) -> bool:
        """Whether SimSelf may put this to work at all."""
        return self.verdict in (VENDOR, ADAPT, WRAP)


# --------------------------------------------------------------------- harnesses

HARNESSES: tuple[External, ...] = (
    External(
        "openclaw/openclaw", "OpenClaw", 391478, "MIT", "2026-10-09", "TypeScript",
        "reference agent harness: the largest of the four, TypeScript, multi-platform",
        REFERENCE,
        "the shape of a working agent loop at scale — tool dispatch, session model",
        "391k stars makes it the ecosystem's centre of gravity. Read for patterns, do not depend on it.",
    ),
    External(
        "bytedance/deer-flow", "DeerFlow", 83534, "MIT", "2026-10-09", "Python",
        "long-horizon SuperAgent harness: sandboxed execution + memory",
        WRAP,
        "the long-horizon pattern SimSelf's learning loop wants: research → code → create",
        "MIT and Python, so its harness patterns can be adapted directly. Closest fit to SimSelf's own shape.",
        "",
    ),
    External(
        "nanocoai/nanoclaw", "NanoClaw", 30902, "MIT", "2026-10-06", "TypeScript",
        "container-isolated agent, minimal OpenClaw alternative",
        WRAP,
        "the isolation pattern: an agent you can audit because it cannot reach the host",
        "MIT. Container isolation is the answer to 'agent with filesystem access is terrifying'.",
        "",
    ),
    External(
        "sipeed/picoclaw", "PicoClaw", 30018, "MIT", "2026-09-24", "Go",
        "tiny agent that runs anywhere, including Raspberry Pi",
        WRAP,
        "the small-footprint pattern: an agent that fits on a device rather than a server",
        "MIT. Go. 30k stars. The proof that agent scaffolding can be small enough to embed.",
        "",
    ),
)


# --------------------------------------------------------------------- avatars and companions

AVATARS: tuple[External, ...] = (
    External(
        "Scthe/ai-iris-avatar", "AI Iris Avatar", 200, "GPL-3.0", "2024-12-22", "C#",
        "LLM + TTS + Unity + lip sync avatar",
        REFERENCE,
        "the avatar pipeline shape Bobby wanted: one repo, LLM to TTS to face",
        "Last pushed Dec 2024, and the licence is the deciding fact, not the age.",
        "GPL-3.0. Cannot be copied into MIT simself. Read the pipeline design; build our own. "
        "A separate process calling it would be fine; vendoring it is not.",
    ),
    External(
        "Silverhand83/sengu", "Sengu", 1, "NONE", "2026-09-11", "HTML",
        "continuity of recorded life: an offline companion trained on your chat history",
        REFERENCE,
        "exactly SimSelf's goal — a companion that persists across sessions",
        "This is the closest existing thing to Bobby's stated aim for SimSelf.",
        "NO LICENSE GRANTED (c) 2026 Vera Corp, all rights reserved. Cannot be integrated in any form. "
        "Concepts preserved in SimSelf's own design; code never read or copied.",
    ),
    External(
        "KlingAIResearch/LivePortrait", "LivePortrait", 19178, "NOASSERTION", "2026-06-01", "Python",
        "portrait animation from a single source image and a driving clip",
        REFERENCE,
        "avatar expression driven by state rather than by a script",
        "Licence is NOASSERTION on the API, so the actual terms are unclear. Read only.",
        "Licence unverified. Do not vendor. Resolve the licence before any real use.",
    ),
)


# --------------------------------------------------------------------- runtimes

RUNTIMES: tuple[External, ...] = (
    External(
        "ggml-org/llama.cpp", "llama.cpp", 130548, "MIT", "2026-10-08", "C++",
        "local LLM inference on CPU",
        WRAP,
        "local inference for the voice pipeline and avatar, no cloud round trip",
        "MIT. The standard. SimSelf already carries kokoro-0.19.onnx; llama.cpp is the same idea for text.",
        "",
    ),
    External(
        "ollama/ollama", "Ollama", 182415, "MIT", "2026-10-08", "Go",
        "local model serving with a simple HTTP API",
        WRAP,
        "a local endpoint SimSelf can call instead of a hosted one",
        "MIT. Already-installed model runs for free; no per-token cost.",
        "",
    ),
    External(
        "karpathy/llm.c", "llm.c", 31121, "MIT", "2025-06-26", "Cuda",
        "LLM training in plain C",
        REFERENCE,
        "the training roadmap's implementation reference, not a dependency",
        "MIT but Cuda-only and static since 2025. A teaching artefact, not a runtime.",
        "",
    ),
    External(
        "karpathy/LLM101n", "LLM101n", 37479, "NONE", "2024-08-01", "None",
        "17-chapter build-an-LLM-from-scratch course",
        REFERENCE,
        "the training roadmap: ch1 bigram through ch17 multimodal",
        "Archived by Karpathy in favour of Eureka Labs' course. Syllabus still the roadmap.",
        "No licence file. Reference only.",
    ),
)


# --------------------------------------------------------------------- voice

VOICE: tuple[External, ...] = (
    External(
        "SYSTRAN/faster-whisper", "faster-whisper", 25763, "MIT", "2026-10-06", "Python",
        "fast speech-to-text",
        WRAP,
        "STT for the Telegram voice pipeline Bobby asked for",
        "MIT, active. The obvious STT choice.",
        "",
    ),
    External(
        "openai/whisper", "whisper", 110163, "MIT", "2026-08-31", "Python",
        "reference speech-to-text model",
        WRAP,
        "STT when faster-whisper's speed is not needed",
        "MIT. Same family as faster-whisper, slower.",
        "",
    ),
    External(
        "Stability-AI/stable-audio-tools", "stable-audio-tools", 3874, "MIT", "2026-10-07", "Python",
        "audio generation and processing",
        REFERENCE,
        "audio output for the avatar beyond plain TTS",
        "MIT and active.",
        "",
    ),
)


# --------------------------------------------------------------------- engines

ENGINES: tuple[External, ...] = (
    External(
        "godotengine/godot", "Godot", 0, "MIT", "2026-10-09", "C++",
        "open-source game engine",
        WRAP,
        "the body: physics, FSM, save/load, NPCs, rendering — none of it reimplemented",
        "Bobby's stated choice. SimSelf is the brain, Godot is the body. The .gd bridge files are in docs/.",
    ),
)


ALL: tuple[External, ...] = HARNESSES + AVATARS + RUNTIMES + VOICE + ENGINES

BY_ROLE: dict[str, tuple[External, ...]] = {
    "harness": HARNESSES,
    "avatar": AVATARS,
    "runtime": RUNTIMES,
    "voice": VOICE,
    "engine": ENGINES,
}


def licence_blocked() -> tuple[External, ...]:
    """Entries that cannot be used as code in any form."""
    return tuple(e for e in ALL if e.licence in ("GPL-3.0", "NONE", "NOASSERTION"))


def integrable() -> tuple[External, ...]:
    """Entries SimSelf may actually put to work."""
    return tuple(e for e in ALL if e.usable)


def total_stars() -> int:
    return sum(e.stars for e in ALL)


def summary() -> dict:
    blocked = licence_blocked()
    return {
        "entries": len(ALL),
        "integrable": len(integrable()),
        "licence_blocked": len(blocked),
        "blocked_names": [e.name for e in blocked],
        "total_stars_reference": total_stars(),
        "by_role": {k: len(v) for k, v in BY_ROLE.items()},
    }