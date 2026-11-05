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


def _is_finite(arr) -> bool:
    """Is every element of this a finite number?

    MEASURED 2026-11-04: `Ground(np.full(D, np.nan))` was INSTALLED,
    because the zero-norm check did not catch it -- `nan == 0.0` is
    False -- and the normalisation then produced a NaN ground.

    An exception is not a verdict, so this returns False rather than
    raising on a non-numeric input.
    """
    try:
        return bool(np.all(np.isfinite(np.asarray(arr, dtype=float))))
    except (TypeError, ValueError):
        return False


class Ground:
    """Write-protected ground with a versioned revision path."""

    def __init__(self, psi0: np.ndarray):
        if psi0 is None:
            raise ValueError("Ground: psi0 is None; refusing to install.")
        # AND THE FINITENESS CHECK, WHICH WAS MISSING HERE. MEASURED
        # 2026-11-04, against this file:
        #
        #     Ground(np.full(D, np.nan))  ->  INSTALLED
        #     Ground(np.full(D, np.inf))  ->  INSTALLED
        #
        # The zero-norm check below did not catch either, because
        # `nan == 0.0` is False and `inf == 0.0` is False. And the
        # normalisation then produced a NaN ground, with a RuntimeWarning
        # from numpy, and INSTALLED it anyway.
        #
        # This is the constitutional ground. It is write-protected and
        # fingerprinted, and it is the thing every gate measures against.
        # A NaN ground makes every cosine comparison False, so every
        # gate comparison silently admits -- and the attack is reachable
        # through the PUBLIC constructor, which is the only path most
        # callers use.
        #
        # So the ground refuses what is not a number before it refuses
        # what has no length.
        if not _is_finite(psi0):
            raise ValueError(
                "Ground: psi0 contains a non-finite value (NaN or infinity); "
                "refusing to install. A non-finite ground makes every "
                "cosine comparison False, so every gate would admit.")
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
        # AND THE FINITENESS CHECK HERE TOO, for the same reason and
        # with the same measurement: a NaN ground was installable, and
        # `revise` is the OTHER public path to a ground. A check on one
        # path and not the other is the split-policy shape again --
        # this time inside one file. See __init__ above.
        if not _is_finite(new_psi0):
            raise ValueError(
                "Ground.revise: new_psi0 contains a non-finite value "
                "(NaN or infinity); refusing. A non-finite ground makes "
                "every cosine comparison False, so every gate would admit.")
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
