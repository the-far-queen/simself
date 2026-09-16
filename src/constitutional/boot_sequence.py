"""
boot_sequence.py — cold-boot initialization helper for SimSelf.

Per Bobby 2026-09-16 ("feature rich and you approve grab and use"):
ported cold_boot_sequence from v6.1 monolith (grok3.txt). The canonical
SimSelf already wires most of this in its constructor; this module adds
the startup logging + SacredLibraryManager hookup.
"""

from __future__ import annotations

import time
from typing import Optional

import numpy as np

from .constitution import Constitution
from .ground import Ground
from .sacred_library import SacredLibraryManager
from .simself import SimSelf


def cold_boot(
    sacred_library_path: str = "./sacred_library",
    psi0: Optional[np.ndarray] = None,
    constitution: Optional[Constitution] = None,
) -> SimSelf:
    """Initialize the canonical SimSelf + SacredLibraryManager.

    Args:
        sacred_library_path: directory where SacredLibraryManager stores files.
        psi0: optional constitutional ground vector (numpy array). If None,
            uses SimSelf's canonical default (first axis = 1, rest = 0).
        constitution: optional pre-built Constitution. If None, builds one
            with the canonical default axes.

    Returns:
        Initialized SimSelf instance, with .sacred_library attached.
    """
    print("=" * 70)
    print("SimSelf Cold Boot Initialized")
    print("=" * 70)

    t0 = time.perf_counter()

    # 1. Constitution (or default).
    if constitution is None:
        constitution = Constitution()

    # 2. SimSelf's canonical psi0.
    if psi0 is None:
        psi0 = np.zeros(constitution.dim, dtype=np.float64)
        psi0[0] = 1.0

    # 3. Ground (write-protected).
    ground = Ground(psi0)

    # 4. SacredLibraryManager.
    sacred = SacredLibraryManager(sacred_library_path)

    # 5. Wire together.
    sim = SimSelf(constitution=constitution, ground=ground)
    sim.sacred_library = sacred

    elapsed = time.perf_counter() - t0
    print(f"  + SimSelf canonical")
    print(f"  + Ground (write-protected psi0)")
    print(f"  + SacredLibrary at {sacred_library_path}")
    print(f"  + SacredLibrary: {len(sacred.registry_index)} skills archived")
    print(f"  + Boot time: {elapsed*1000:.1f} ms")
    print("=" * 70)

    return sim


__all__ = ["cold_boot"]
