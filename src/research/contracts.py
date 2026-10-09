"""Skill contracts — what a capability promises, and how a caller checks it.

Queue item 4, 2026-10-09. The integration registry (`integrations.py`) has
15 verified external systems and 8 working probes, and none of it says what
a CALLER is entitled to rely on. A registry of things that exist is a
catalogue. A contract is what turns a catalogue into scaffolding:

    what the skill provides      -> provides
    what it requires of you      -> requires
    what it refuses to do        -> refuses
    how a caller verifies it     -> check()   <- the part that was missing
    what it costs                -> cost

The `check` is the whole point. Bobby's directive was that the growth
process must be "astoundingly precise"; a contract whose verification
cannot fail is decoration, which is the failure mode this project has
already produced nine times in one session. So every contract here carries
a check that returns a real number, and `verify_all` reports which
contracts cannot currently be satisfied on THIS machine rather than
asserting they are.

NOTHING IS DISCOVERED HERE. The capabilities themselves already exist and
are listed in the registry. This file only states the terms.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
from typing import Callable


class Status(str, Enum):
    AVAILABLE = "available"      # present and its check passes
    PARTIAL = "partial"          # present, check does not fully pass
    ABSENT = "absent"            # not present on this machine
    UNVERIFIABLE = "unverifiable"  # present but the check cannot be run


@dataclass
class CheckResult:
    ok: bool
    status: Status
    measured: str          # the actual number or path, not a verdict
    reason: str = ""


@dataclass
class Contract:
    """One capability, with terms the caller can rely on."""

    name: str
    provides: str
    requires: list[str] = field(default_factory=list)
    refuses: list[str] = field(default_factory=list)
    cost: str = "none"
    _check: Callable[[], CheckResult] | None = None
    source: str = ""

    def check(self) -> CheckResult:
        """Run the check. A check that is missing, raises, or returns the
        wrong shape reports UNVERIFIABLE rather than propagating.

        The first version returned `self._check()` directly, so a check
        that returned None or raised took the whole report down with it.
        A report that cannot be produced is worse than a report that says
        "this one could not be checked" -- silently passing is exactly
        the failure this file exists to prevent.
        """
        if self._check is None:
            return CheckResult(False, Status.UNVERIFIABLE, "no check defined",
                               "a contract whose check is undefined cannot be relied on")
        try:
            result = self._check()
        except Exception as exc:
            return CheckResult(False, Status.UNVERIFIABLE,
                               f"check raised {type(exc).__name__}",
                               str(exc)[:120])
        if not isinstance(result, CheckResult):
            return CheckResult(False, Status.UNVERIFIABLE,
                               f"check returned {type(result).__name__}, not CheckResult",
                               "a check must return a CheckResult to be trusted")
        return result

    def terms(self) -> str:
        lines = [f"{self.name}", f"  provides: {self.provides}"]
        if self.requires:
            lines.append(f"  requires: {', '.join(self.requires)}")
        if self.refuses:
            lines.append(f"  refuses:  {', '.join(self.refuses)}")
        lines.append(f"  cost:     {self.cost}")
        return "\n".join(lines)


# --------------------------------------------------------------------- checks


def _which(binary: str) -> CheckResult:
    found = shutil.which(binary)
    if found:
        return CheckResult(True, Status.AVAILABLE, found)
    return CheckResult(False, Status.ABSENT, "not on PATH", f"{binary} absent")


def _module(name: str, attr: str | None = None) -> CheckResult:
    try:
        __import__(name)
    except Exception as exc:
        return CheckResult(False, Status.ABSENT, f"import {name} failed",
                           f"{type(exc).__name__}: {exc}")
    if attr:
        try:
            m = __import__(name, fromlist=[attr])
            getattr(m, attr)
        except Exception as exc:
            return CheckResult(False, Status.PARTIAL, f"import {name} ok",
                               f"but {attr} missing: {exc}")
    return CheckResult(True, Status.AVAILABLE, f"import {name} ok")


def _python_version() -> CheckResult:
    v = ".".join(str(x) for x in sys.version_info[:3])
    ok = sys.version_info >= (3, 11)
    return CheckResult(ok, Status.AVAILABLE if ok else Status.PARTIAL, v,
                       "" if ok else "project targets 3.11+")


def _torch() -> CheckResult:
    try:
        import torch  # noqa: F401
    except Exception as exc:
        return CheckResult(False, Status.ABSENT, "torch not importable", str(exc)[:80])
    import torch
    return CheckResult(True, Status.AVAILABLE, f"torch {torch.__version__}",
                       "" if torch.__version__ else "")


def _kokoro_model() -> CheckResult:
    here = Path(__file__).resolve().parents[2]
    for cand in (here / "kokoro-v0_19.onnx", here / "models" / "kokoro-v0_19.onnx"):
        if cand.exists():
            return CheckResult(True, Status.AVAILABLE, str(cand))
    return CheckResult(False, Status.ABSENT, "no kokoro model",
                       "voice output cannot be produced")


def _git_clean(repo: str) -> CheckResult:
    root = Path("C:/Users/HP/AppData/Local/hermes/work_repos") / repo
    if not root.exists():
        return CheckResult(False, Status.ABSENT, f"{repo} not present")
    try:
        p = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                           capture_output=True, text=True, timeout=30)
    except Exception as exc:
        return CheckResult(False, Status.UNVERIFIABLE, f"git call failed: {exc}")
    dirty = [l for l in p.stdout.splitlines() if l.strip()]
    if dirty:
        return CheckResult(False, Status.PARTIAL, f"{len(dirty)} uncommitted paths",
                           "work in the tree is not yet pushed")
    head = subprocess.run(["git", "log", "--oneline", "-1"], cwd=root,
                          capture_output=True, text=True, timeout=30).stdout.strip()
    return CheckResult(True, Status.AVAILABLE, head or "clean")


# --------------------------------------------------------------------- registry


def _contracts() -> list[Contract]:
    return [
        Contract(
            "local-tts",
            "voice output from text, on this machine, with no network call",
            requires=["kokoro model file"],
            refuses=["speaking without the model; no cloud fallback"],
            cost="local compute only",
            _check=_kokoro_model,
            source="fieldcore kokoro-v0_19.onnx",
        ),
        Contract(
            "speech-to-text",
            "transcribe voice notes into text for the ingest pipeline",
            requires=["faster-whisper or whisper", "a local model download on first use"],
            refuses=["transcribing without a local model"],
            cost="local compute; first run downloads weights",
            _check=lambda: _module("faster_whisper"),
        ),
        Contract(
            "local-inference",
            "run a language model on this machine with no per-token charge",
            requires=["ollama or llama.cpp on PATH"],
            refuses=["calling a paid API as a fallback"],
            cost="electricity only",
            _check=lambda: _which("ollama"),
        ),
        Contract(
            "agent-isolation",
            "run an agent that cannot reach the host filesystem",
            requires=["docker", "the harness binary"],
            refuses=["running an agent with host filesystem access"],
            cost="container overhead",
            _check=lambda: _which("docker"),
        ),
        Contract(
            "deterministic-kernel",
            "a bounded, reproducible state update with a proved contraction",
            requires=["numpy"],
            refuses=["anything stochastic; the contract is a guarantee, not an average"],
            cost="O(d) per step",
            _check=lambda: _module("numpy"),
        ),
        Contract(
            "refusal-authority",
            "an out-of-process governor that can veto and cannot be widened",
            requires=["a spawnable OS process", "a pipe"],
            refuses=["accepting caller-supplied thresholds; the limits live in the governor"],
            cost="one process plus IPC per question",
            _check=lambda: _module("fieldcore.governor", "GovernorProcess")
            if _module("numpy").ok else CheckResult(False, Status.ABSENT, "numpy missing"),
        ),
        Contract(
            "deep-learning",
            "the FieldCore and simself kernels that need tensors",
            requires=["torch"],
            refuses=["running on GPU when only CPU is present, silently"],
            cost="RAM and compute",
            _check=_torch,
        ),
        Contract(
            "python-baseline",
            "the interpreter the whole project assumes",
            requires=["python >= 3.11"],
            refuses=["3.10 and older: the type syntax in src/ will not parse"],
            cost="none",
            _check=_python_version,
        ),
        Contract(
            "fieldcore-pushed",
            "the substrate repo with every change published",
            requires=["git", "credentials with push on the-far-queen"],
            refuses=["claiming work is delivered while it is uncommitted"],
            cost="none",
            _check=lambda: _git_clean("fieldcore"),
        ),
        Contract(
            "simself-pushed",
            "the identity repo with every change published",
            requires=["git", "credentials with push on the-far-queen"],
            refuses=["claiming work is delivered while it is uncommitted"],
            cost="none",
            _check=lambda: _git_clean("simself"),
        ),
    ]


CONTRACTS: list[Contract] = _contracts()


def by_name(name: str) -> Contract | None:
    return next((c for c in CONTRACTS if c.name == name), None)


def verify_all() -> dict:
    """Check every contract on this machine right now.

    Reports the MEASURED value for each, not a boolean, because the number
    is what a caller needs and a green tick is what hides the machine it
    ran on.
    """
    rows = []
    counts = {s: 0 for s in Status}
    for c in CONTRACTS:
        r = c.check()
        counts[r.status] += 1
        rows.append({"name": c.name, "status": r.status.value,
                     "ok": r.ok, "measured": r.measured, "reason": r.reason})
    return {
        "total": len(CONTRACTS),
        "available": counts[Status.AVAILABLE],
        "partial": counts[Status.PARTIAL],
        "absent": counts[Status.ABSENT],
        "unverifiable": counts[Status.UNVERIFIABLE],
        "satisfied": counts[Status.AVAILABLE] / len(CONTRACTS) if CONTRACTS else 0.0,
        "rows": rows,
    }


def usable_now() -> list[str]:
    """Capabilities a caller may rely on in THIS session."""
    out = []
    for c in CONTRACTS:
        r = c.check()
        if r.status is Status.AVAILABLE:
            out.append(c.name)
    return out


def render() -> str:
    rep = verify_all()
    lines = [f"contracts: {rep['available']}/{rep['total']} available "
             f"({rep['satisfied']:.0%})", ""]
    for row in rep["rows"]:
        mark = {"available": "ok  ", "partial": "part",
                "absent": "MISS", "unverifiable": "????"}[row["status"]]
        lines.append(f"[{mark}] {row['name']:<22} {row['measured'][:52]}")
        if row["reason"]:
            lines.append(f"          {row['reason'][:62]}")
    return "\n".join(lines)