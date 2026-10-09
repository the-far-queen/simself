"""Tests for the fixed twin-prime coupling.

Source of the spec: intake/2026-10-08/deepseek1-0d5de092/parts/97-*
ninemanifoldfieldcore-with-fixed-twin-prime-coup.md

Each test can go red. Several exist to prove the coupling is FIXED —
no learned parameters — because that is the whole claim.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from constitutional import twin_prime_coupling as T  # noqa: E402


# --------------------------------------------------------------------- primes


def test_is_prime_basics():
    assert T.is_prime(2) and T.is_prime(3) and T.is_prime(5)
    assert not T.is_prime(1) and not T.is_prime(4) and not T.is_prime(9)


def test_twin_pairs_are_correct():
    pairs = T.twin_pairs(30)
    assert (3, 5) in pairs and (5, 7) in pairs and (11, 13) in pairs
    assert (17, 19) in pairs
    assert all(T.is_prime(a) and T.is_prime(b) and b - a == 2 for a, b in pairs)


def test_is_prime_can_fail():
    """A composite must be rejected, or every downstream rank is wrong."""
    for composite in (9, 21, 25, 27, 49, 51, 121, 143):
        assert not T.is_prime(composite)


# --------------------------------------------------------------------- hierarchy


def test_hierarchy_is_ordered_twins_first():
    h = T.HIERARCHY
    assert (3, 5) in h and (5, 7) in h
    # the first seven entries are exactly the twin pairs below 64
    assert h[:7] == T.twin_pairs(64)


def test_hierarchy_has_no_duplicates():
    assert len(set(T.HIERARCHY)) == len(T.HIERARCHY)


def test_anchors_are_unique():
    """The load-bearing invariant. A tie between two manifolds would give
    them mutual coupling equal to the diagonal — i.e. no separation at all.
    This test failed twice during development, which is why it exists.
    """
    assert len(set(T.ANCHORS)) == T.N_MANIFOLDS
    assert len(T.ANCHORS) == T.N_MANIFOLDS


def test_anchors_are_non_negative():
    assert all(a >= 0 for a in T.ANCHORS)


def test_skip_index_respects_taken():
    taken = {0, 1, 2}
    r = T.skip_index(T.PRIME_SETS[0], taken)
    assert r not in taken


# --------------------------------------------------------------------- coupling


def test_diagonal_is_exactly_one():
    c = T.twin_prime_coupling()
    assert np.all(np.diag(c.matrix) == 1.0)


def test_coupling_is_symmetric():
    c = T.twin_prime_coupling()
    assert np.allclose(c.matrix, c.matrix.T)


def test_offdiagonal_is_strictly_below_one():
    """Proves the anchors are actually distinct. If two manifolds tied,
    this is exactly where it would show."""
    c = T.twin_prime_coupling()
    off = c.matrix[~np.eye(T.N_MANIFOLDS, dtype=bool)]
    assert off.max() < 1.0, f"tied manifolds: off-diagonal max {off.max()}"


def test_nearer_anchors_couple_more_strongly():
    c = T.twin_prime_coupling()
    r = np.asarray(T.ANCHORS)
    for i in range(T.N_MANIFOLDS):
        for j in range(i + 1, T.N_MANIFOLDS):
            di, dj = c.matrix[i, j], abs(int(r[i]) - int(r[j]))
            for k in range(T.N_MANIFOLDS):
                for m in range(k + 1, T.N_MANIFOLDS):
                    dk = c.matrix[k, m]
                    if abs(int(r[k]) - int(r[m])) > dj:
                        assert di > dk or np.isclose(di, dk), (i, j, k, m)


def test_sharper_decay_separates_more():
    soft = T.twin_prime_coupling(sharpness=0.5)
    hard = T.twin_prime_coupling(sharpness=2.0)
    assert hard.matrix.min() < soft.matrix.min()


def test_coupling_has_no_learned_parameters():
    """The claim: fixed coupling, not learned. Nothing in the module is a
    parameter object, nothing is fitted, and repeated construction is
    bit-identical.
    """
    a = T.twin_prime_coupling().matrix
    b = T.twin_prime_coupling().matrix
    assert np.array_equal(a, b)
    assert not hasattr(T.twin_prime_coupling(), "parameters")


# --------------------------------------------------------------------- curl gate


def test_curl_gate_zero_curl_contributes_nothing():
    ctrl = np.ones((T.N_MANIFOLDS, 5))
    gated = T.curl_gate(ctrl, np.zeros(T.N_MANIFOLDS)).gated
    assert np.allclose(gated, 0.0)


def test_curl_gate_suppresses_low_curl_more():
    ctrl = np.ones((T.N_MANIFOLDS, 5))
    curl = np.array([0.1, 0.5, 0.9] * 3)
    gated = T.curl_gate(ctrl, curl).gated
    for base in range(0, 9, 3):
        assert gated[base].sum() < gated[base + 1].sum() < gated[base + 2].sum()


def test_curl_gate_preserves_relative_order():
    """A manifold with higher curl must never end up with less authority."""
    ctrl = np.ones((T.N_MANIFOLDS, 5))
    curl = np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1])
    g = T.curl_gate(ctrl, curl).gated.sum(axis=1)
    assert list(g) == sorted(g, reverse=True)


# --------------------------------------------------------------------- fusion


def test_fuse_rejects_wrong_manifold_count():
    with pytest.raises(ValueError):
        T.fuse(np.ones((4, 5)), np.ones(4))


def test_nonlinear_fusion_requires_curl():
    with pytest.raises(ValueError):
        T.fuse(np.ones((T.N_MANIFOLDS, 5)), None, nonlinear=True)


def test_linear_fusion_is_weighted_sum():
    """fused_d = sum_i (sum_j w_ij * ctrl_j)_d  — i.e. apply the coupling
    across manifolds per control dimension, then sum the manifolds.
    """
    ctrl = np.ones((T.N_MANIFOLDS, 5))
    fused = T.fuse(ctrl, nonlinear=False)
    c = T.twin_prime_coupling()
    expected = c.matrix.sum(axis=1)          # total weight per manifold
    assert np.allclose(fused, expected.sum())  # uniform ctrl -> weight sum


def test_fusion_output_dim_is_preserved():
    ctrl = np.ones((T.N_MANIFOLDS, 5))
    curl = np.linspace(0.1, 1.0, T.N_MANIFOLDS)
    assert T.fuse(ctrl, curl).shape == (5,)
    assert T.fuse(ctrl, curl, nonlinear=False).shape == (5,)


def test_output_head_maps_five_to_four():
    f = np.ones(5)
    assert T.output_head(f).shape == (4,)


def test_output_head_rejects_wrong_dim():
    with pytest.raises(ValueError):
        T.output_head(np.ones(4))


def test_output_head_is_deterministic():
    f = np.array([0.2, -0.4, 0.7, 0.1, 0.9])
    assert np.array_equal(T.output_head(f), T.output_head(f))


def test_full_path_runs_end_to_end():
    """Nine manifolds -> fuse -> decision. The path the corpus describes."""
    rng = np.random.default_rng(3)
    ctrl = rng.normal(size=(T.N_MANIFOLDS, 5))
    curl = rng.uniform(0.05, 1.0, T.N_MANIFOLDS)
    fused = T.fuse(ctrl, curl, nonlinear=True)
    decision = T.output_head(fused)
    assert decision.shape == (4,)
    assert np.all(np.isfinite(decision))


def test_incoherent_manifold_changes_the_decision():
    """The curl gate must actually matter, or the nonlinear mode is
    decoration. Zeroing one manifold's curl must move the output.
    """
    rng = np.random.default_rng(11)
    ctrl = rng.normal(size=(T.N_MANIFOLDS, 5))
    curl = np.full(T.N_MANIFOLDS, 0.6)
    base = T.output_head(T.fuse(ctrl, curl))
    curl2 = curl.copy()
    curl2[0] = 0.0
    gated = T.output_head(T.fuse(ctrl, curl2))
    assert not np.allclose(base, gated)