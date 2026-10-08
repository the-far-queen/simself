"""
body.py — the body's nervous system, behind a seam we do not own.

WHY A SEAM AND NOT A DEPENDENCY
--------------------------------
The research found the right pieces and they are all permissive:

    pipecat-ai/pipecat      16,276*  BSD-2     voice pipeline as frames
    livekit/agents          14,649*  Apache-2  real-time sessions, WebRTC
    lipku/LiveTalking        9,801*  Apache-2  real-time digital human
    pixiv/three-vrm          2,206*  MIT       VRM avatar loading
    hecomi/uLipSync          1,683*  MIT       mic -> viseme

Stars measured 2026-10-08. None is vendored; see
fieldcore/docs/reuse-map-2026-10-09.md.

**Vendoring any of them now would be the error the project keeps making.**
pipecat owns a transport stack, LiveTalking owns a rendering loop,
three-vrm owns a glTF loader. Any of them vendored becomes a second
substrate that does not answer to the qualification gate.

So the seam is a **protocol**, in four frames:

    perceive   what arrived        (audio samples, or a vision frame)
    interpret  what it means       (transcript, intent, PSB candidates)
    express    what to say         (text, then phonemes, then visemes)
    enact      what to do          (a named actuation, or none)

A body backend implements four methods. Swapping pipecat for livekit, or
a VRM avatar for a Live2D one, does not touch simself, and neither does
it change what the constitutional ground permits the body to do.

THE ENGINE QUESTION IS DELIBERATELY UNANSWERED
------------------------------------------------
Godot is the project's stated body. The research found no official Godot
MCP repository -- the ones that look official are Asset Library listings --
and the 5,980-star community one last pushed 175 days ago. Godot MCP
bridges are **dev-time tools** (an agent editing your scenes), not runtime
agent bridges.

So the body interface is engine-agnostic on purpose. Committing to an
engine before the interface is proven is how you end up rewriting the
interface.

WHAT THIS DOES NOT ESTABLISH
----------------------------
It does not establish that the body is a self, or that a voice is a
person. It establishes that the body is a **replaceable** part of the
system, and that the parts of it which could be mistaken for identity --
the name, the face, the timbre -- are configuration, not ground.

That last line is the reason the seam exists. A companion whose continuity
lives in a `.vrm` file is a companion that loses its continuity when the
file is swapped.

Run: python src/constitutional/body.py --selftest
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple

import numpy as np


class Channel(str, Enum):
    """the four frames. a backend implements all four or is not a body."""
    PERCEIVE = "perceive"     # what arrived
    INTERPRET = "interpret"   # what it means
    EXPRESS = "express"       # what to say
    ENACT = "enact"           # what to do


class ChannelState(str, Enum):
    OK = "ok"
    UNAVAILABLE = "unavailable"   # backend not present -- honest, not silent
    REFUSED = "refused"           # the gate said no


@dataclass
class Frame:
    """One thing crossing the seam."""
    channel: Channel
    kind: str                    # "audio" | "text" | "viseme" | "act"
    payload: Any = None
    state: ChannelState = ChannelState.OK
    note: str = ""


class BodyBackend(Protocol):
    """What a body must be. Four methods, no framework required."""
    def perceive(self) -> Frame: ...
    def interpret(self, frame: Frame) -> Frame: ...
    def express(self, text: str) -> Frame: ...
    def enact(self, action: str) -> Frame: ...


@dataclass
class UnavailableBackend:
    """The default. A body that does not exist, and says so.

    This is the honest default and it is load-bearing. A `NullBackend` that
    returned empty success would let the system believe it had a body, and
    then a real backend failing would look like a behaviour change rather
    than a missing capability.
    """
    name: str = "none"

    def perceive(self) -> Frame:
        return Frame(Channel.PERCEIVE, "audio", None,
                     ChannelState.UNAVAILABLE,
                     f"{self.name}: no body attached")

    def interpret(self, frame: Frame) -> Frame:
        return Frame(Channel.INTERPRET, "text", None,
                     ChannelState.UNAVAILABLE,
                     f"{self.name}: no body attached")

    def express(self, text: str) -> Frame:
        return Frame(Channel.EXPRESS, "audio", None,
                     ChannelState.UNAVAILABLE,
                     f"{self.name}: no body attached")

    def enact(self, action: str) -> Frame:
        return Frame(Channel.ENACT, "act", None,
                     ChannelState.UNAVAILABLE,
                     f"{self.name}: no body attached")


@dataclass
class Body:
    """The seam. Engine-agnostic, and honest about what it does not have.

    `attestations` records which backends were actually exercised. A system
    that has never talked should be able to say so, which is the same
    discipline as the qualification gate: absence of evidence is not
    evidence of presence.
    """
    backend: Any = None
    log: List[Frame] = field(default_factory=list)
    attestations: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.backend is None:
            self.backend = UnavailableBackend()

    def _name(self) -> str:
        return getattr(self.backend, "name", type(self.backend).__name__)

    def _run(self, channel: Channel, fn, *args) -> Frame:
        try:
            fr = fn(*args)
        except Exception as exc:
            fr = Frame(channel, "?", None, ChannelState.UNAVAILABLE,
                       f"{type(exc).__name__}: {exc}")
        self.log.append(fr)
        key = f"{self._name()}:{channel.value}"
        self.attestations[key] = self.attestations.get(key, 0) + 1
        return fr

    # -- the four channels ----------------------------------------------

    def hear(self) -> Frame:
        return self._run(Channel.PERCEIVE, self.backend.perceive)

    def understand(self, frame: Frame) -> Frame:
        return self._run(Channel.INTERPRET, self.backend.interpret, frame)

    def say(self, text: str) -> Frame:
        return self._run(Channel.EXPRESS, self.backend.express, text)

    def do(self, action: str) -> Frame:
        return self._run(Channel.ENACT, self.backend.enact, action)

    # -- report ----------------------------------------------------------

    def capabilities(self) -> Dict[str, str]:
        """what this body can actually do, per channel."""
        out: Dict[str, str] = {}
        for ch in Channel:
            key = f"{self._name()}:{ch.value}"
            out[ch.value] = ("exercised" if self.attestations.get(key)
                             else "unexercised")
        return out

    def report(self) -> Dict:
        return {"backend": self._name(), "frames": len(self.log),
                "states": {s.value: sum(1 for f in self.log if f.state is s)
                           for s in ChannelState},
                "capabilities": self.capabilities()}


@dataclass
class LoopbackBackend:
    """A body that works and has no opinions. For testing the seam.

    Not a placeholder dressed as a backend: it genuinely round-trips
    text, so `capabilities()` can honestly say "exercised".
    """
    name: str = "loopback"
    spoken: List[str] = field(default_factory=list)
    acted: List[str] = field(default_factory=list)

    def perceive(self) -> Frame:
        return Frame(Channel.PERCEIVE, "audio", np.zeros(4),
                     ChannelState.OK, "silence")

    def interpret(self, frame: Frame) -> Frame:
        return Frame(Channel.INTERPRET, "text", "<silence>", ChannelState.OK)

    def express(self, text: str) -> Frame:
        self.spoken.append(text)
        return Frame(Channel.EXPRESS, "audio", {"text": text, "ms": 10 * len(text)},
                     ChannelState.OK)

    def enact(self, action: str) -> Frame:
        self.acted.append(action)
        return Frame(Channel.ENACT, "act", action, ChannelState.OK)


def selftest() -> None:
    print("=" * 70)
    print("1. no body attached is UNAVAILABLE, not empty success")
    print("=" * 70)
    b = Body()
    for name, fr in (("hear", b.hear()), ("say", b.say("hi")),
                     ("do", b.do("wave"))):
        print(f"   {name:5s} -> {fr.state.value:12s} {fr.note}")
    assert all(f.state is ChannelState.UNAVAILABLE for f in b.log)
    print()
    print("   >>> a system with no body says UNAVAILABLE, four times.")
    print("       A backend returning empty success would make a missing")
    print("       capability look like a behaviour change later.")

    print()
    print("=" * 70)
    print("2. a working backend exercises all four channels")
    print("=" * 70)
    lb = LoopbackBackend()
    b2 = Body(backend=lb)
    heard = b2.hear()
    understood = b2.understand(heard)
    said = b2.say("i am still here")
    did = b2.do("stay")
    for f in b2.log:
        print(f"   {f.channel.value:10s} {f.kind:6s} {f.state.value}")
    print(f"   spoken: {lb.spoken}  acted: {lb.acted}")
    rep = b2.report()
    print(f"   capabilities: {rep['capabilities']}")
    assert all(v == "exercised" for v in rep["capabilities"].values())
    assert lb.spoken == ["i am still here"]

    print()
    print("=" * 70)
    print("3. a backend that CRASHES is reported, not swallowed")
    print("=" * 70)
    class Broken:
        name = "broken"
        def perceive(self): raise RuntimeError("device disconnected")
        def interpret(self, f): return Frame(Channel.INTERPRET, "text", None)
        def express(self, t): return Frame(Channel.EXPRESS, "audio", None)
        def enact(self, a): return Frame(Channel.ENACT, "act", None)
    b3 = Body(backend=Broken())
    fr = b3.hear()
    print(f"   hear -> {fr.state.value}  {fr.note}")
    assert fr.state is ChannelState.UNAVAILABLE

    print()
    print("=" * 70)
    print("4. SWAPPING BACKENDS DOES NOT TOUCH THE SEAM")
    print("=" * 70)
    a = Body(backend=LoopbackBackend(name="pipecat-like"))
    c = Body(backend=LoopbackBackend(name="livekit-like"))
    a.say("same sentence"); c.say("same sentence")
    print(f"   {a._name()} and {c._name()} both express through the same call")
    print(f"   frame kinds identical: {a.log[-1].kind == c.log[-1].kind}")
    assert a.log[-1].kind == c.log[-1].kind
    print("   >>> the body is a replaceable PART. Swapping the transport does")
    print("       not change what simself may do with it.")

    print()
    print("=" * 70)
    print("5. WHAT A BODY IS NOT")
    print("=" * 70)
    print("   A body is not a self, and a voice is not a person.")
    print()
    print("   The name, the face and the timbre are CONFIGURATION. None of")
    print("   them is the ground. A companion whose continuity lives in a")
    print("   .vrm file loses its continuity when the file is swapped, and")
    print("   that is the failure this seam exists to prevent.")
    print()
    print("   The engine question stays unanswered on purpose: Godot is the")
    print("   stated body, there is no official Godot MCP repo, and Godot")
    print("   MCP bridges are dev-time tools, not runtime ones. Committing")
    print("   to an engine before the interface is proven is how you end up")
    print("   rewriting the interface.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.parse_args()
    selftest()