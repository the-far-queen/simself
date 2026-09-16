"""
demo_one.py — first of three artifacts (per Grok sharpen 2026-09-16).

What it does, in order:
1. Install ground ψ0 (unit vector in R^16).
2. Initialize working state ψ as a perturbation.
3. Step the projected gradient flow ψ <- Π_B(ψ - η(ψ-ψ0)) for N steps.
4. Plot ||ψ - ψ0|| drift.
5. Offer one legal packet (near ground) and one bad packet (high norm) to the gate.
6. Print allow/deny.

This is the 15-minute entry point. A fork that wraps this in one command has
already helped (per Grok review).
"""
from __future__ import annotations

import sys
import numpy as np

# Local imports — adjust paths if running outside simself/src/demos/.
sys.path.insert(0, "C:/Users/Admin/simself/src")
sys.path.insert(0, "C:/Users/Admin/fieldcore/src")

from harness.gate import gate_packet  # K8 — same predicates as kernel


def install_ground(dim: int = 16) -> np.ndarray:
    g = np.zeros(dim)
    g[0] = 1.0
    return g


def projected_step(psi: np.ndarray, psi0: np.ndarray, eta: float, R: float) -> np.ndarray:
    trial = psi - eta * (psi - psi0)
    d = float(np.linalg.norm(trial - psi0))
    if d > R:
        # project onto sphere of radius R around psi0
        trial = psi0 + R * (trial - psi0) / d
    return trial


def main(n_steps: int = 20, R: float = 3.0, eta: float = 0.1) -> dict:
    psi0 = install_ground()
    psi = psi0 + 2.0 * np.random.RandomState(0).randn(16)
    psi = psi / np.linalg.norm(psi) * 2.5  # normalize then scale to inside the ball

    drifts = []
    for k in range(n_steps):
        psi = projected_step(psi, psi0, eta, R)
        drifts.append(float(np.linalg.norm(psi - psi0)))

    # Two packets through the gate
    good_packet = psi0 + 0.05 * np.random.RandomState(1).randn(16)
    bad_packet = 5.0 * np.ones(16)  # fails norm

    allow_good, why_good = gate_packet(good_packet, psi0)
    allow_bad, why_bad = gate_packet(bad_packet, psi0)

    print("== demo_one: ground + drift + gate ==")
    print(f"ground ||ψ0||        = {np.linalg.norm(psi0):.4f}")
    print(f"working ||ψ - ψ0||   start = {drifts[0]:.4f}  end = {drifts[-1]:.4f}")
    print(f"drift monotonic?      {all(drifts[i] >= drifts[i+1] - 1e-9 for i in range(len(drifts)-1))}")
    print(f"good_packet allow     = {allow_good}  reason = {why_good}")
    print(f"bad_packet  allow     = {allow_bad}  reason = {why_bad}")
    assert allow_good is True and why_good == "ok"
    assert allow_bad is False and why_bad in ("norm", "coherence", "zero")

    return {
        "drifts": drifts,
        "good_allow": allow_good,
        "bad_allow": allow_bad,
        "good_reason": why_good,
        "bad_reason": why_bad,
    }


if __name__ == "__main__":
    main()
