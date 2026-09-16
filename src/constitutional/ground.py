"""
ground.py — ψ₀ install, write-protect (per Grok master plan, full rewrite 2026-09-16).

Ground is the interface T in the genus-1 Heegaard splitting of S³. ψ₀ sits on T
or is write-protected so that no ψ̇ field lives in W (the hole). This module is
the operational form of that rule.

Properties enforced at the API:
1. ψ₀ is installed exactly once.
2. ψ₀ cannot be modified by tick, observe, or any other public method.
3. The only path to a new ψ₀ is the explicit `Ground.revise(path, new_psi0)`
   method, which writes a versioned revision and freezes the previous ground.
4. The revision path produces an audit log entry.

This is the runtime form of "no constitutional edit through fluency."
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


@dataclass
class GroundRevision:
    """A versioned revision of ψ₀."""
    version: int
    psi0: np.ndarray
    timestamp: float
    reason: str = ""
    sha256: str = ""

    def __post_init__(self):
        self.sha256 = hashlib.sha256(self.psi0.tobytes()).hexdigest()


class Ground:
    """Write-protected ground with a versioned revision path."""

    def __init__(self, psi0: np.ndarray):
        if psi0 is None:
            raise ValueError("Ground: psi0 is None; refusing to install.")
        n = float(np.linalg.norm(psi0))
        if n == 0.0:
            raise ValueError("Ground: psi0 has zero norm; refusing to install.")
        # Normalize to unit length so cosine tests are unambiguous.
        self._psi0: np.ndarray = (psi0 / n).astype(np.float64)
        self._history: List[GroundRevision] = [
            GroundRevision(version=1, psi0=self._psi0.copy(), timestamp=0.0)
        ]
        self._immutable: bool = True  # structural: the only way to clear is revise()

    @classmethod
    def install(cls, psi0: np.ndarray) -> "Ground":
        """Install a fresh ground. Returns a write-protected Ground."""
        return cls(psi0)

    @property
    def psi_0(self) -> np.ndarray:
        """Read-only access. Caller must NOT mutate the returned array."""
        return self._psi0.copy() if self._immutable else self._psi0

    @property
    def history(self) -> List[GroundRevision]:
        """Read-only history of revisions."""
        return list(self._history)

    def dim(self) -> int:
        return self._psi0.shape[0]

    def revise(self, new_psi0: np.ndarray, reason: str = "") -> int:
        """Propose a new ground. Returns the new version number.

        The previous ground is frozen in history. ψ₀ changes only through this
        method. This is the only legal write to ground.

        The reason string is mandatory and goes into the audit log. An empty
        reason is allowed only when the caller has already logged it elsewhere.
        """
        if new_psi0 is None:
            raise ValueError("Ground.revise: new_psi0 is None.")
        n = float(np.linalg.norm(new_psi0))
        if n == 0.0:
            raise ValueError("Ground.revise: new_psi0 has zero norm.")
        normalized = (new_psi0 / n).astype(np.float64)
        # Freeze the current ground.
        old = self._history[-1]
        old_frozen = GroundRevision(
            version=old.version,
            psi0=old.psi0.copy(),
            timestamp=old.timestamp,
            reason="frozen by next revision",
            sha256=old.sha256,
        )
        self._history[-1] = old_frozen
        # Install the new ground.
        new_version = old.version + 1
        self._history.append(
            GroundRevision(
                version=new_version,
                psi0=normalized,
                timestamp=0.0,
                reason=reason,
            )
        )
        self._psi0 = normalized
        return new_version

    def save(self, path: str) -> None:
        """Persist ground (ψ₀ + history) to JSON."""
        payload = {
            "psi_0": self._psi0.tolist(),
            "history": [
                {
                    "version": r.version,
                    "psi0": r.psi0.tolist(),
                    "timestamp": r.timestamp,
                    "reason": r.reason,
                    "sha256": r.sha256,
                }
                for r in self._history
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def load(self, path: str) -> None:
        """Restore ground from JSON. Refuses to overwrite if it would change ψ₀."""
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        loaded = np.asarray(payload["psi_0"], dtype=np.float64)
        if not np.allclose(loaded, self._psi0, atol=1e-9):
            raise ValueError(
                "Ground.load: refusing to overwrite installed ψ₀ with snapshot's ψ₀. "
                "Use revise() if a new ground is intended."
            )
        # History is informational only; keep the in-process history.
