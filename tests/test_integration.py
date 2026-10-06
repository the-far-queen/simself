"""
test_integration.py — I1..I5. Does an observation actually enter the state?

Found by tools/control_parity.py, which reported drift = 0.0000 across
200 steps with 128 accepted observations. A system that accepts input
and does not move is not convergent, it is inert.

The bug in one line, in observe():

    psi_current = _project_ball(
        psi_current - eta * (psi_current - psi0), psi0, R)

`obs` was gated and then discarded. Starting from
psi_current == psi0, that expression returns exactly psi0 forever. The
observation never entered the state.

This file is the regression net for that. I1 is the one that matters.

Run:  python tests/test_integration.py
"""

from __future__ import annotations

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constitutional.ground import Ground            # noqa: E402
from constitutional.simself import SimSelf          # noqa: E402
from constitutional.constitution import Constitution  # noqa: E402

DIM = 16


def make(seed: int = 3) -> SimSelf:
    base = np.random.RandomState(seed).randn(DIM)
    base /= np.linalg.norm(base)
    return SimSelf(constitution=Constitution(), ground=Ground(base.copy()))


def t_I1_accepted_observation_moves_state():
    """THE test. If this fails, observe() is decorative.

    The observation is aligned with psi0 on purpose: an all-ones vector
    is refused by the coherence gate, which is the gate working. This
    test is about what happens AFTER an accept, not about the gate.
    """
    s = make()
    obs = s.psi0 + 0.2 * np.random.RandomState(1).randn(DIM)
    obs /= np.linalg.norm(obs)

    r = s.observe(obs)
    assert r["allow"], f"observation refused for no reason: {r}"
    drift = s.drift()
    assert drift > 1e-6, (
        f"observation accepted but state did not move. drift={drift:.3e}. "
        f"obs is being gated and then discarded."
    )
    print(f"I1: ok (accepted observation moved state, drift={drift:.3e})")


def t_I2_many_observations_accumulate():
    """128 accepts that never accumulate is the bug that was there."""
    s = make()
    rng = np.random.RandomState(11)
    accepted = 0
    for i in range(60):
        obs = s.psi0 + 0.3 * rng.randn(DIM)      # near-manifold
        obs /= np.linalg.norm(obs)
        if s.observe(obs)["allow"]:
            accepted += 1
        s.tick(dt=0.05)
    assert accepted > 0, "nothing was accepted; test is not exercising anything"
    drift = s.drift()
    assert drift > 1e-6, f"{accepted} accepts, drift {drift:.3e} — inert again"
    print(f"I2: ok ({accepted} accepts -> drift {drift:.4f})")


def t_I3_state_stays_inside_the_ball():
    """integration must not leak norm. the ball is the whole constraint."""
    s = make()
    rng = np.random.RandomState(5)
    for _ in range(300):
        obs = s.psi0 + 3.0 * rng.randn(DIM)     # deliberately large
        obs /= np.linalg.norm(obs) * 3.0
        s.observe(obs)
        s.tick(dt=0.05)
        d = s.drift()
        assert d <= s.R + 1e-6, f"state escaped the ball: drift {d} > R {s.R}"
    print(f"I3: ok (300 steps, drift {s.drift():.4f} <= R {s.R})")


def t_I4_refused_observation_does_not_move_state():
    """the veto has to be real, not decorative in the other direction."""
    s = make()
    first = s.psi0 + 0.2 * np.random.RandomState(2).randn(DIM)
    s.observe(first / np.linalg.norm(first))  # one accepted step first
    before = s.drift()

    # far off-manifold: should be refused
    wild = np.random.RandomState(99).randn(DIM)
    wild /= np.linalg.norm(wild)
    r = s.observe(wild)
    if not r["allow"]:
        after = s.drift()
        assert abs(after - before) < 1e-9, (
            f"observation refused but state moved: {before} -> {after}")
        print("I4: ok (refused observation left the state untouched)")
    else:
        print("I4: skipped (wild vector was within the ball)")


def t_I5_psi0_still_untouched():
    """the invariant that outranks all of the above."""
    s = make()
    g0 = s.ground.psi_0.copy()
    rng = np.random.RandomState(8)
    for _ in range(200):
        obs = s.psi0 + 0.3 * rng.randn(DIM)
        s.observe(obs / np.linalg.norm(obs))
        s.tick()
        s.dream() if hasattr(s, "dream") else None
    assert np.array_equal(s.ground.psi_0, g0), "ψ₀ was modified by operation"
    print("I5: ok (ψ₀ byte-identical after 200 operations)")


def main():
    t_I1_accepted_observation_moves_state()
    t_I2_many_observations_accumulate()
    t_I3_state_stays_inside_the_ball()
    t_I4_refused_observation_does_not_move_state()
    t_I5_psi0_still_untouched()
    print("\nINTEGRATION TESTS PASS (I1..I5)")


if __name__ == "__main__":
    main()
