"""
test_handoff_void.py — H1..H6 for HandoffProtocol, V1..V5 for VoidIntegration.

Handoff and the void were both advertised in this repo's docs since
August and neither existed as code. These tests are the reason they do.

The load-bearing ones:
- H3: a receiving system with a DIFFERENT ψ₀ refuses the packet.
- H4: a packet written from an unready state is refused.
- V4: the void basis is deterministic. A random probe would be defect E
  wearing a different hat.

Run:  python tests/test_handoff_void.py
"""

from __future__ import annotations

import os
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constitutional.handoff import (  # noqa: E402
    HandoffProtocol, Readiness, SCHEMA_VERSION,
)
from constitutional.simself import SimSelf  # noqa: E402
from constitutional.constitution import Constitution  # noqa: E402
from constitutional.ground import Ground  # noqa: E402
from constitutional.void import VoidIntegration, VOID_DIM  # noqa: E402

DIM = 16


def make_simself(dim: int = DIM, seed: int = 5):
    """A SimSelf with a deterministic ground."""
    rng = np.random.RandomState(seed)
    psi0 = rng.randn(dim)
    psi0 /= np.linalg.norm(psi0)
    return SimSelf(constitution=Constitution(), ground=Ground(psi0))


def warmed(dim: int = DIM, ticks: int = 12) -> SimSelf:
    s = make_simself(dim)
    for i in range(ticks):
        s.observe(np.ones(dim) * 0.4)
        s.tick(dt=0.05)
    return s


# ---------------------------------------------------------------- handoff

def t_H1_readiness_measures():
    """readiness reports numbers, not adjectives."""
    s = warmed()
    h = HandoffProtocol(s)
    r = h.readiness()
    assert isinstance(r, Readiness)
    assert 0.0 <= r.stability <= 1.5, r
    assert r.drift >= 0.0
    assert r.ticks == 12, r
    print(f"H1: ok (stability={r.stability:.3f} drift={r.drift:.3f} "
          f"ticks={r.ticks} ready={r.ready})")


def t_H2_fresh_system_is_not_ready():
    """nothing ticked, no handoff."""
    s = make_simself()
    r = HandoffProtocol(s).readiness()
    assert not r.ready
    assert "no_ticks" in r.reasons, r.reasons
    print(f"H2: ok (unticked system refused: {r.reasons})")


def t_H3_packet_roundtrips():
    """write then receive restores the transferable state."""
    a = warmed()
    ha = HandoffProtocol(a)
    assert ha.readiness().ready, ha.readiness().reasons

    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "packet.json")
        ha.write(path)

        b = make_simself()                 # same ground, fresh process
        hb = HandoffProtocol(b)
        info = hb.receive(path)

    assert info["restored"]
    assert b.ticks == a.ticks, (b.ticks, a.ticks)
    assert b.mode == a.mode
    assert np.allclose(b.psi_current, a.psi_current)
    # and the ground never moved
    assert np.allclose(b.ground.psi_0, a.ground.psi_0)
    print(f"H2-> ok (restored ticks={b.ticks} mode={b.mode} "
          f"drift={b.drift():.3e})")


def t_H4_different_psi0_is_refused():
    """THE invariant: a handoff may move ψ, never ψ₀."""
    a = warmed()
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "packet.json")
        HandoffProtocol(a).write(path)

        other = make_simself(seed=99)      # a different constitutional subject
        try:
            HandoffProtocol(other).receive(path)
            raise AssertionError("a packet from a different ψ₀ was accepted")
        except ValueError as e:
            assert "fingerprint mismatch" in str(e), str(e)

        # and the refusal left it untouched
        assert np.allclose(other.psi_current, other.psi0)
    print("H4: ok (cross-subject handoff refused, ψ untouched)")


def t_H5_unready_packet_is_refused():
    """a broken state must not be transferable."""
    a = make_simself()                      # never ticked -> not ready
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "packet.json")
        HandoffProtocol(a).write(path)       # writing is allowed
        b = make_simself()
        try:
            HandoffProtocol(b).receive(path)
            raise AssertionError("an unready packet was accepted")
        except ValueError as e:
            assert "unready" in str(e), str(e)
    print("H5: ok (unready packet refused)")


def t_H6_packet_records_its_own_policy():
    """a packet must state the thresholds that judged it."""
    a = warmed()
    pkt = HandoffProtocol(a).build_packet()
    assert pkt["schema"] == SCHEMA_VERSION
    assert "stability_floor" in pkt["policy"]
    assert "psi0_sha256" in pkt
    assert "psi_0" not in pkt, "a handoff must not carry a ground payload"
    print(f"H6: ok (schema={pkt['schema']} policy recorded, "
          f"no ψ₀ payload)")


# ------------------------------------------------------------------- void

def t_V1_frame_is_orthonormal():
    """frame is (k, dim): basis vectors are ROWS, so B @ B.T == I."""
    vi = VoidIntegration(dim=DIM)
    f = vi.frame
    assert f.shape == (VOID_DIM, DIM), f.shape
    g = f @ f.T
    assert np.allclose(g, np.eye(VOID_DIM), atol=1e-8), g
    print(f"V1: ok (frame orthonormal, {VOID_DIM}x{DIM}, rows are basis)")


def t_V2_distance_is_bounded():
    vi = VoidIntegration(dim=DIM)
    rng = np.random.RandomState(1)
    for _ in range(20):
        v = rng.randn(DIM)
        d = vi.distance_to_void(v)
        assert 0.0 <= d <= 1.0 + 1e-9, d
    print("V2: ok (distance stays in [0,1] over 20 random probes)")


def t_V3_orthogonal_complement_scores_zero():
    """a vector outside the void shares nothing with it."""
    vi = VoidIntegration(dim=DIM)
    # project a random vector out of the void, then check distance ~ 0
    v = np.random.RandomState(4).randn(DIM)
    outside = v - vi.project(v)
    assert vi.distance_to_void(outside) < 1e-8
    print(f"V3: ok (complement distance "
          f"{vi.distance_to_void(outside):.2e})")


def t_V4_basis_is_deterministic():
    """a random probe would be defect E again."""
    a = VoidIntegration(dim=DIM)
    b = VoidIntegration(dim=DIM)
    assert np.array_equal(a.frame, b.frame), "void frame is not reproducible"
    print("V4: ok (void basis reproducible across instances)")


def t_V5_lesson_refuses_when_not_reaching():
    """the module must not manufacture novelty."""
    vi = VoidIntegration(dim=DIM)
    v = np.random.RandomState(4).randn(DIM)
    outside = v - vi.project(v)            # deliberately orthogonal
    out = vi.void_lesson(outside)
    assert out["kept"] is False
    assert out["reason"] == "not_reaching", out

    # and something inside the void does get kept. frame rows ARE
    # dim-length basis vectors, so row 0 is a genuine void direction.
    inside = vi.frame[0] * 1.0
    assert inside.shape == (DIM,), inside.shape
    ok = vi.void_lesson(inside)
    assert ok["kept"] is True, ok
    print(f"V5: ok (refuses non-reaching, accepts reaching: {ok['reason']})")


def main():
    t_H1_readiness_measures()
    t_H2_fresh_system_is_not_ready()
    t_H3_packet_roundtrips()
    t_H4_different_psi0_is_refused()
    t_H5_unready_packet_is_refused()
    t_H6_packet_records_its_own_policy()
    t_V1_frame_is_orthonormal()
    t_V2_distance_is_bounded()
    t_V3_orthogonal_complement_scores_zero()
    t_V4_basis_is_deterministic()
    t_V5_lesson_refuses_when_not_reaching()
    print("\nHANDOFF + VOID TESTS PASS (H1..H6, V1..V5)")


if __name__ == "__main__":
    main()
