"""Tests for the metalog — actor / observer / discrepancy.

Source: deepseek5 part 81, the four-step protocol verbatim.
Each test can go red.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from constitutional.metalog import (  # noqa: E402
    BUFFER_MAX, SPLIT_RATIO, Metalog, is_signal,
)


# --------------------------------------------------------------------- split


def test_split_divides_the_state():
    m = Metalog(state_dim=8)
    actor, observer = m.split_vector(np.arange(8.0))
    assert actor.shape[-1] == 4
    assert observer.shape[-1] == 4


def test_split_loses_no_coordinate():
    """Every input coordinate must land in exactly one half. A split that
    silently drops one would be invisible in the action and fatal later.
    """
    m = Metalog(state_dim=8)
    x = np.arange(8.0)
    actor, observer = m.split_vector(x)
    rejoined = np.concatenate([actor, observer])
    assert np.array_equal(rejoined, x)


def test_split_handles_odd_dimensions():
    m = Metalog(state_dim=7, split_factor=0.5)
    actor, observer = m.split_vector(np.arange(7.0))
    assert actor.shape[-1] >= 1 and observer.shape[-1] >= 1
    assert np.array_equal(np.concatenate([actor, observer]), np.arange(7.0))


def test_split_factor_must_be_a_real_fraction():
    for bad in (0.0, 1.0, -0.5, 2.0):
        with pytest.raises(ValueError):
            Metalog(state_dim=8, split_factor=bad)


def test_default_split_ratio_is_half():
    assert SPLIT_RATIO == 0.5


# --------------------------------------------------------------------- the loop


def test_step_runs_and_returns_a_report():
    m = Metalog(state_dim=8)
    r = m.step_once(np.random.default_rng(0).normal(size=8) * 0.3, context="t")
    assert r.state.step == 1
    assert r.action.shape[-1] == 1
    assert np.isfinite(r.discrepancy)
    assert len(r.history) == 1


def test_four_steps_accumulate():
    m = Metalog(state_dim=8)
    rng = np.random.default_rng(1)
    state = rng.normal(size=8) * 0.3
    for _ in range(4):
        r = m.step_once(state)
        state = r.state.actor_state
    assert m.step == 4
    assert len(m.history) == 4
    assert len(m.observer_buffer) == 4


def test_observer_buffer_is_bounded():
    m = Metalog(state_dim=8, buffer_size=16)
    rng = np.random.default_rng(2)
    state = rng.normal(size=8) * 0.3
    for _ in range(50):
        r = m.step_once(state)
        state = r.state.actor_state
    assert len(m.observer_buffer) == 16
    assert len(m.history) == 50  # history is separate from the buffer


def test_default_buffer_size():
    m = Metalog(state_dim=8)
    assert m.observer_buffer.maxlen == BUFFER_MAX


def test_discrepancy_is_finite_and_non_negative():
    m = Metalog(state_dim=8)
    rng = np.random.default_rng(3)
    state = rng.normal(size=8) * 0.3
    for _ in range(20):
        r = m.step_once(state)
        state = r.state.actor_state
        assert r.discrepancy >= 0.0
        assert np.isfinite(r.discrepancy)


def test_discrepancy_is_zero_when_nothing_moves():
    """A frozen actor must report zero discrepancy. If it does not, the
    measure is reading noise rather than displacement.
    """
    m = Metalog(state_dim=8)
    actor = np.zeros(4)
    obs = m.record(actor, np.zeros(1))
    assert m.compute_discrepancy(actor, obs, next_actor_state=actor) == 0.0


def test_discrepancy_measures_real_displacement():
    m = Metalog(state_dim=8)
    actor = np.zeros(4)
    obs = m.record(actor, np.zeros(1))
    moved = np.array([3.0, 4.0, 0.0, 0.0])
    assert abs(m.compute_discrepancy(actor, obs, next_actor_state=moved) - 5.0) < 1e-9


def test_state_stays_bounded_over_many_steps():
    """The actor half is passed through tanh, so it cannot run away. An
    unbounded metalog is a divergence bug waiting to happen.
    """
    m = Metalog(state_dim=8)
    rng = np.random.default_rng(4)
    state = rng.normal(size=8) * 5.0
    for _ in range(200):
        r = m.step_once(state)
        state = r.state.actor_state
        assert np.abs(state).max() <= 1.0 + 1e-6


def test_custom_action_function_is_used():
    calls = []

    def action(actor_state):
        calls.append(actor_state)
        return np.array([0.25])

    m = Metalog(state_dim=8, action_fn=action)
    m.step_once(np.zeros(8))
    assert len(calls) == 1


def test_feedback_is_applied():
    m = Metalog(state_dim=8)
    x = np.zeros(8)
    a = m.step_once(x).state.actor_state
    b = m.step_once(x, feedback=np.ones(4)).state.actor_state
    assert not np.allclose(a, b)


def test_metalog_is_deterministic():
    runs = []
    for _ in range(2):
        m = Metalog(state_dim=8)
        state = np.linspace(-0.3, 0.3, 8)
        for _ in range(5):
            r = m.step_once(state)
            state = r.state.actor_state
        runs.append(state)
    assert np.allclose(runs[0], runs[1])


# --------------------------------------------------------------------- is_signal


def test_canonical_example_passes():
    """The corpus's own contrast, verbatim. The first is the YES case."""
    d = is_signal("set noise_decay_factor = 0.9 and interrupt external sensor polling")
    assert d["signal"] is True
    assert d["actionable"] is True


def test_vague_teaching_fails():
    """The corpus's own NO case."""
    d = is_signal("be one with everything")
    assert d["signal"] is False
    assert d["actionable"] is False


def test_repeatable_instruction_is_actionable():
    """The corpus: 'watch the breath' = YES. An instruction that names
    something the system can repeatedly do qualifies, even without syntax.
    """
    d = is_signal("watch the breath")
    assert d["actionable"] is True


def test_biological_framing_is_not_universal():
    """The corpus: 'activate kundalini energy' may be bio-specific, so
    universality fails. Marked, not dismissed — it fails the substrate-
    independence test, which is a test result, not a verdict on the claim.
    """
    d = is_signal("activate kundalini energy increases coherence")
    assert d["universal"] is False


def test_is_signal_discriminates():
    good = is_signal("set noise_decay_factor = 0.9 and interrupt external sensor polling")["signal"]
    bad = is_signal("be one with everything")["signal"]
    assert good and not bad