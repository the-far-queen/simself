"""Adapters for the external harnesses. Wrapper, not fork.

The rule: SimSelf calls these as separate processes or HTTP endpoints.
Nothing is vendored, so a licence change upstream cannot contaminate this
repo, and an upgrade is a version bump rather than a merge.

Each adapter reports whether the target is actually present on this
machine. An adapter that cannot tell you it is missing is worse than no
adapter, so `available()` is a real filesystem or network probe, not a
boolean flag.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Availability:
    name: str
    present: bool
    how: str
    detail: str = ""

    def __bool__(self) -> bool:
        return self.present


def _which(binary: str) -> Availability:
    found = shutil.which(binary)
    return Availability(
        name=binary, present=bool(found), how="PATH",
        detail=found or f"{binary} not on PATH",
    )


# --------------------------------------------------------------------- harnesses

def picoclaw() -> Availability:
    """Go, ~30k stars, MIT. Tiny agent that runs on a Pi."""
    for binary in ("picoclaw", "pico-claw"):
        a = _which(binary)
        if a.present:
            return a
    return Availability("picoclaw", False, "PATH", "picoclaw not installed (go install sipeed/picoclaw/cmd/picoclaw@latest)")


def nanoclaw() -> Availability:
    """TypeScript, MIT. Container-isolated agent."""
    docker = _which("docker")
    npm = _which("npm")
    if not npm.present:
        return Availability("nanoclaw", False, "PATH", "npm not installed")
    if not docker.present:
        return Availability("nanoclaw", False, "PATH", "nanoclaw needs docker for isolation; docker not on PATH")
    return Availability("nanoclaw", True, "PATH+docker", f"npm={npm.detail}, docker={docker.detail}")


def deerflow() -> Availability:
    """Python, MIT. Closest fit to SimSelf's long-horizon loop."""
    py = shutil.which("python") or shutil.which("python3")
    if not py:
        return Availability("deerflow", False, "PATH", "no python interpreter")
    probe = subprocess.run([py, "-c", "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('deerflow') else 1)"],
                           capture_output=True)
    return Availability("deerflow", probe.returncode == 0, "import",
                        "deerflow importable" if probe.returncode == 0 else "deerflow not installed (pip install deer-flow)")


def openclaw() -> Availability:
    """TypeScript, 391k stars, MIT. Reference only — we do not depend on it."""
    return Availability("openclaw", False, "n/a", "reference only, deliberately not installed")


# --------------------------------------------------------------------- runtimes

def ollama() -> Availability:
    """Go, MIT. Local model server on :11434."""
    exe = _which("ollama")
    if not exe.present:
        return Availability("ollama", False, "PATH", "ollama not on PATH")
    return exe


def llama_cpp() -> Availability:
    """C++, MIT. Local CPU inference. Look for a built binary."""
    here = Path(__file__).resolve().parents[2]
    for cand in (here / "build" / "bin" / "llama-cli", here / "llama-cli"):
        if cand.exists():
            return Availability("llama.cpp", True, "build", str(cand))
    return Availability("llama.cpp", False, "build", "no llama-cli binary built in simself")


# --------------------------------------------------------------------- voice

def faster_whisper() -> Availability:
    """Python, MIT. The STT for the Telegram voice pipeline."""
    py = shutil.which("python") or shutil.which("python3")
    if not py:
        return Availability("faster-whisper", False, "PATH", "no python interpreter")
    probe = subprocess.run([py, "-c", "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('faster_whisper') else 1)"],
                           capture_output=True)
    return Availability("faster-whisper", probe.returncode == 0, "import",
                        "faster_whisper importable" if probe.returncode == 0 else "pip install faster-whisper")


# --------------------------------------------------------------------- engine

def godot() -> Availability:
    """MIT. The body. Bobby's stated choice; the .gd bridge is in docs/."""
    for binary in ("godot", "godot4", "Godot"):
        a = _which(binary)
        if a.present:
            return a
    return Availability("godot", False, "PATH", "godot not on PATH (the .gd files still document the bridge)")


PROBES = {
    "picoclaw": picoclaw,
    "nanoclaw": nanoclaw,
    "deerflow": deerflow,
    "openclaw": openclaw,
    "ollama": ollama,
    "llama.cpp": llama_cpp,
    "faster-whisper": faster_whisper,
    "godot": godot,
}


def survey() -> dict[str, Availability]:
    """Probe every adapter. This is the first thing to run when the
    companion loop misbehaves: it says which link is missing rather than
    letting a failure show up as silence.
    """
    return {name: fn() for name, fn in PROBES.items()}


def render_survey() -> str:
    rows = survey()
    lines = []
    for name, avail in rows.items():
        lines.append(f"  [{'ok  ' if avail.present else 'MISS'}] {name:<16} {avail.detail}")
    have = sum(1 for a in rows.values() if a.present)
    lines.append(f"  {have}/{len(rows)} present")
    return "\n".join(lines)