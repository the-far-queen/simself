"""
demo_one.py — first of the three artifacts (per Grok master plan Step 2, full rewrite 2026-09-16).

What it does:
1. Install ground ψ₀ (unit vector in R^16).
2. Initialize working state ψ as a perturbation.
3. Step the projected gradient flow ψ ← Π_B(ψ - η(ψ-ψ₀)) using the canonical
   tiniest_core.project_ball contract.
4. Plot drift (printed, not matplotlib to keep this runnable anywhere).
5. Offer one legal packet and one bad packet to the gate.
6. Print allow/deny.

A a fork that wraps this in one command has already helped (per Grok review).
"""

from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, "C:/Users/Admin/simself/src")
sys.path.insert(0, "C:/Users/Admin/fieldcore/src")

from harness.gate import gate_packet
from tiniest_core.tiniest_core import (
    install_ground,
    project_ball,
    DEFAULT_ETA,
    DEFAULT_R,
)


def main(n_steps: int = 20, R: float = DEFAULT_R, eta: float = DEFAULT_ETA) -> dict:
    psi0 = install_ground()
    rng = np.random.RandomState(0)
    psi = psi0 + 2.5 * rng.randn(16)
    n0 = float(np.linalg.norm(psi - psi0))
    if n0 > 0:
        psi = psi0 + (2.5 / n0) * (psi - psi0)

    drifts = []
    for _ in range(n_steps):
        psi = project_ball(psi - eta * (psi - psi0), psi0, R)
        drifts.append(float(np.linalg.norm(psi - psi0)))

    good_packet = psi0 + 0.05 * np.random.RandomState(1).randn(16)
    bad_packet = 5.0 * np.ones(16)  # exceeds MAX_NORM = 4.0

    allow_good, why_good = gate_packet(good_packet, psi0)
    allow_bad, why_bad = gate_packet(bad_packet, psi0)

    print("== demo_one: ground + drift + gate ==")
    print(f"ground ||ψ₀||            = {np.linalg.norm(psi0):.4f}")
    print(f"working ||ψ - ψ₀||       start = {drifts[0]:.4f}  end = {drifts[-1]:.4f}")
    print(f"drift monotonic non-increasing = {all(drifts[i] >= drifts[i+1] - 1e-9 for i in range(len(drifts)-1))}")
    print(f"good_packet allow         = {allow_good}  reason = {why_good}")
    print(f"bad_packet  allow         = {allow_bad}  reason = {why_bad}")
    assert allow_good is True and why_good == "ok"
    assert allow_bad is False and why_bad in ("refuse_norm", "refuse_coherence", "refuse_zero")

    return {
        "drifts": drifts,
        "good_allow": allow_good,
        "bad_allow": allow_bad,
    }


if __name__ == "__main__":
    main()
