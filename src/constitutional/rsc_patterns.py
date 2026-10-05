r"""
rsc_patterns.py — React Server Components + ES6 module patterns (sebmarkbage).
* sebmarkbage drove React Server Components + the ES6 module spec.
*
* the patterns:
*   1. ES6 static imports — no circular deps, hoisted, evaluated once
*   2. RSC: server/client separation + serialization at boundary
*   3. Suspense + transitions — async fallback + interruption
*
* simself adoption:
*   1. ψ₀ imports — constitutional ground is a one-time static import
*   2. ψ ↔ serialized_at_gate_at_boundary — the gate serializes ψ to disk/JSON-RPC
*   3. dream_state — async fallback during agent downtime
 """


from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass, field, replace
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple


# Pattern 1: ES6 static imports — hoisted, evaluated once
# mirror in python: a module-level constant that imports only once

_PSI_ZERO_HASH: Optional[str] = None

def psi_zero() -> Tuple[float, ...]:
    """the constitutional ground. computed once, cached forever.
    ES6 module semantics: imported, evaluated once, immutable."""
    global _PSI_ZERO_HASH
    if _PSI_ZERO_HASH is None:
        canonical = b"psi_0_v1_8axes_boundary_0.5_coherence_1.0_stability_1.0_..."
        _PSI_ZERO_HASH = hashlib.sha256(canonical).hexdigest()[:16]
    return (0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)


def psi_zero_cached() -> str:
    """return the cached hash. ES6-style module-level memoization."""
    psi_zero()  # ensure initialized
    assert _PSI_ZERO_HASH is not None
    return _PSI_ZERO_HASH


# Pattern 2: React Server Components — server/client boundary + serialization
# simself: the gate IS the server/client boundary. ψ passes through it, gets serialized.

@dataclass(frozen=True)
class SerializedPsi:
    """the wire format for ψ. server sends, client receives. ES6/RSC style."""
    sha256: str
    axes: Tuple[float, ...]
    tick: int
    ts: str
    witness: str

    def to_json(self) -> str:
        import json
        return json.dumps({
            "sha256": self.sha256,
            "axes": list(self.axes),
            "tick": self.tick,
            "ts": self.ts,
            "witness": self.witness,
        }, sort_keys=True)

    @classmethod
    def from_psi(cls, axes: Tuple[float, ...], tick: int, witness: str) -> "SerializedPsi":
        canonical = f"{axes}|{tick}|{witness}".encode("utf-8")
        sha = hashlib.sha256(canonical).hexdigest()[:16]
        return cls(sha256=sha, axes=axes, tick=tick,
                   ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   witness=witness)


def serialize(axes: Tuple[float, ...], tick: int, witness: str) -> SerializedPsi:
    """the server → client boundary. same as RSC's RSCPayload.serialize."""
    return SerializedPsi.from_psi(axes, tick, witness)


# Pattern 3: Suspense + transitions — async fallback + interruption
# simself: dream_state is the Suspense fallback. agent is async during downtime.

class Suspense:
    """the RSC Suspense pattern: while async work runs, show a fallback.
    simself's dream_state is the fallback."""

    def __init__(self):
        self._fallback = "dreaming"
        self._ready: Optional[Any] = None
        self._pending: List[Awaitable[Any]] = []

    def throw_promise(self, promise: Awaitable[Any]) -> None:
        """suspend: throw the promise. the runtime catches and renders fallback."""
        self._pending.append(promise)

    def resolve(self, value: Any) -> None:
        """the promise resolved. we have a value."""
        self._ready = value

    @property
    def fallback(self) -> str:
        return self._fallback if self._ready is None else "ready"

    @property
    def value(self) -> Optional[Any]:
        return self._ready


class Transition:
    """the RSC useTransition pattern: long-running updates stay non-blocking."""

    def __init__(self):
        self._pending: bool = False
        self._start_ts: Optional[str] = None

    def start(self) -> None:
        self._pending = True
        self._start_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def finish(self) -> None:
        self._pending = False

    @property
    def is_pending(self) -> bool:
        return self._pending


# Self-test
if __name__ == "__main__":
    # Pattern 1: ES6 module memoization
    h1 = psi_zero_cached()
    h2 = psi_zero_cached()
    assert h1 == h2
    print(f"P1: ok (ES6 module memoization, hash={h1})")

    # Pattern 2: RSC serialization
    s = serialize(axes=(0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0), tick=42, witness="gate_passed")
    json_str = s.to_json()
    assert "gate_passed" in json_str
    assert s.sha256 in json_str
    print(f"P2: ok (RSC serialization, sha={s.sha256[:8]}...)")

    # Pattern 3: Suspense + Transition
    sus = Suspense()
    assert sus.fallback == "dreaming"  # fallback when nothing ready
    sus.resolve({"value": "ready"})
    assert sus.fallback == "ready"
    print(f"P3.a: ok (Suspense fallback: {sus.fallback})")

    tr = Transition()
    assert not tr.is_pending
    tr.start()
    assert tr.is_pending
    tr.finish()
    assert not tr.is_pending
    print(f"P3.b: ok (Transition pending: {tr.is_pending})")

    print("\nALL RSC_PATTERNS TESTS PASS")
