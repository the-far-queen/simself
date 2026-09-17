"""
persistence.py — Thin wrapper exposing canonical SimSelf save/load.

Per Grok master plan Step 3 (2026-09-16). The canonical SimSelf class in
constitutional/simself.py already has .save() and .load() that round-trip ψ₀,
ψ, committed unit ids, last verdicts, mode, ticks, time, R, and eta. This
module is a convenience wrapper so callers can use:

    from harness.persistence import save, load
    save(sim, "snapshot.json")
    sim2.load("snapshot.json")  # ψ₀ is verified immutable

The legacy PersistenceManager.save_agent_state / load_agent_state for the
SimSelfAgent class is removed — it was a stub for an agent class that does
not exist in the canonical SimSelf runtime.

The constitutional contract from constitutional.simself.load is preserved:
a load that tries to overwrite the installed ψ₀ with a snapshot's ψ₀ raises
ValueError ("constitutional edit through fluency"). This module adds nothing
that violates that contract.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from constitutional.simself import SimSelf


def save(sim: "SimSelf", path: str) -> str:
    """Save canonical SimSelf state to a JSON file. Returns the path.

    Persisted fields: dim, ψ₀, ψ_current, committed_unit_ids (re-derived),
    last_verdicts (last 20 decision log records), mode, ticks, time, R, eta.

    Use sim.dump(path) directly if you want the same behavior with the
    auto-generated filename.
    """
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    sim.save(path)
    return path


def load(sim: "SimSelf", path: str) -> None:
    """Load canonical SimSelf state from a JSON file.

    Verifies that the snapshot's ψ₀ matches the installed ψ₀ within atol=1e-9.
    Raises ValueError on mismatch (constitutional edit through fluency).

    Use sim.load(path) directly if you prefer.
    """
    sim.load(path)


__all__ = ["save", "load"]
