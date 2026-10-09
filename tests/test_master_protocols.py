"""Tests for MasterProtocol and the four codified protocols.

Source: deepseek5 part 75. Four protocols, four coherence metrics.

Several tests exist because this module had real bugs that only appeared
when it was run:
  - abstract slots shadowed by None-valued instance attributes
  - every action_generator returned a constant, so the loop carried no
    state and every coherence trace was flat
  - Stamets' correlation percept collapsed to 1x1 on a single-row signal
  - correlation saturates under clip, making every percept identical
  - Gurdjieff concatenated percept and state of different widths
  - measure_operational_state had no entity axis, so per-entity protocols
    saw a constant input

Each of those now has a test that fails if it comes back.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from constitutional.master_protocols import (  # noqa: E402
    PROTOCOLS, GurdjieffProtocol, MasterProtocol, StametsProtocol,
    SwedenborgProtocol, TsongkhapaProtocol, all_protocols, compare,
    measure_operational_state,
)

AX = np.array([0.3, 0.5, 0.7, 0.2, 0.9, 0.4, 0.6, 0.1])


@pytest.fixture()
def signal():
    return measure_operational_state(np.random.default_rng(0), n_entities=8, n_steps=24)


# --------------------------------------------------------------------- shape


def test_all_four_protocols_exist():
    assert len(PROTOCOLS) == 4
    assert {p.name for p in all_protocols()} == {
        "Tsongkhapa_ShamathaVipashyana", "Swedenborg_Correspondence",
        "Gurdjieff_FourthWay", "Stamets_Mycelial",
    }


def test_every_protocol_is_instantiable():
    """The abstract slots were shadowed by None-valued attributes in the
    first version, which made every subclass uninstantiable. Guard.
    """
    for p in all_protocols():
        assert isinstance(p, MasterProtocol)
        for slot in ("perception_transform", "axiom_evaluator",
                     "action_generator", "coherence_metric"):
            assert callable(getattr(p, slot))


def test_incomplete_protocol_cannot_be_instantiated():
    class Half(MasterProtocol):
        def perception_transform(self, raw): return raw
        def axiom_evaluator(self, a, p): return a
        # action_generator and coherence_metric missing

    with pytest.raises(TypeError):
        Half()


# --------------------------------------------------------------------- metrics


def test_coherence_is_in_unit_interval(signal):
    for p in all_protocols():
        for t in range(5):
            c = p.apply(signal[t], AX).coherence
            assert 0.0 <= c <= 1.0, (p.name, c)


def test_coherence_is_finite(signal):
    for p in all_protocols():
        assert np.isfinite(p.apply(signal[0], AX).coherence)


def test_every_metric_can_move(signal):
    """The flat-trace bug. A metric that cannot change while the system
    runs is not measuring the system.
    """
    for p in all_protocols():
        trace = p.run(signal, AX, steps=6)["trace"]
        assert len(set(trace)) > 1, f"{p.name} produced a constant trace: {trace}"


def test_metrics_disagree_with_each_other(signal):
    """Four metrics that always agree are one metric wearing four names."""
    finals = {p.name: p.run(signal, AX, steps=5)["last"] for p in all_protocols()}
    assert len(set(round(v, 4) for v in finals.values())) >= 3, finals


def test_metrics_discriminate_between_good_and_bad_axioms(signal):
    low = np.full(8, 0.05)
    high = np.full(8, 0.95)
    for p in all_protocols():
        cl = p.apply(signal[0], low).coherence
        ch = p.apply(signal[0], high).coherence
        assert cl != ch, f"{p.name} cannot tell good axioms from bad"


# --------------------------------------------------------------------- signal


def test_signal_has_an_entity_axis():
    s = measure_operational_state(np.random.default_rng(0), n_entities=6, n_steps=5)
    assert s.ndim == 3
    assert s.shape == (5, 6, 4)


def test_signal_entities_differ_from_each_other():
    """The first generator had no entity axis, so every 'entity' was the
    same vector and per-entity protocols saw a constant world.
    """
    s = measure_operational_state(np.random.default_rng(0), n_entities=6, n_steps=2)
    assert not np.allclose(s[0][0], s[0][1])


def test_signal_changes_over_time():
    s = measure_operational_state(np.random.default_rng(0), n_entities=6, n_steps=4)
    assert not np.allclose(s[0], s[3])


def test_coupling_changes_the_network(signal):
    """A densely coupled system and a weakly coupled one must differ, or
    the network protocols have nothing to read.
    """
    rng = np.random.default_rng(1)
    tight = measure_operational_state(rng, n_entities=8, n_steps=6, coupling=1.0)
    loose = measure_operational_state(rng, n_entities=8, n_steps=6, coupling=0.0)
    assert not np.allclose(tight, loose)


# --------------------------------------------------------------------- loop


def test_action_carries_information(signal):
    """Constant action vectors leave the loop stateless. Guard.
    """
    for p in all_protocols():
        r = p.apply(signal[0], AX)
        act = np.asarray(r.suggested_action).reshape(-1)
        assert act.size > 0
        assert not np.allclose(act, act.flat[0]), f"{p.name} action is constant"


def test_run_handles_axioms_of_different_width(signal):
    """Gurdjieff concatenated percept and state of different widths and
    raised whenever the axiom count did not equal the feature count.
    """
    for p in all_protocols():
        for ax in (np.full(8, 0.5), np.full(4, 0.5), np.full(3, 0.5)):
            trace = p.run(signal, ax, steps=3)["trace"]
            assert len(trace) == 3
            assert all(np.isfinite(t) for t in trace)


def test_apply_result_shape(signal):
    res = all_protocols()[0].apply(signal[0], AX)
    d = res.as_dict()
    assert "coherence" in d and "axiom_scores" in d and "action" in d


# --------------------------------------------------------------------- per-protocol


def test_tsongkhapa_window_must_be_odd():
    with pytest.raises(ValueError):
        TsongkhapaProtocol(window=4)
    TsongkhapaProtocol(window=5)


def test_tsongkhapa_coherence_is_inverse_of_clinging():
    """coherence = 1 - max(inherent_existence). The corpus's own formula.
    """
    p = TsongkhapaProtocol()
    assert p.coherence_metric(np.array([0.25, 0.5, 0.75])) == pytest.approx(0.25)
    assert p.coherence_metric(np.array([0.0, 0.0])) == pytest.approx(1.0)


def test_tsongkhapa_attenuates_discursive_content():
    """The low-pass must reduce high-frequency content."""
    p = TsongkhapaProtocol(window=9)
    rng = np.random.default_rng(2)
    noisy = rng.normal(size=(1, 64))
    smooth = p.perception_transform(noisy)
    assert float(np.std(smooth)) < float(np.std(noisy))


def test_swedenborg_harmonic_mean_punishes_imbalance():
    """The stated reason for choosing the harmonic mean over the
    arithmetic one: high on one axis, zero on the other must not score
    0.5.
    """
    p = SwedenborgProtocol()
    balanced = p.coherence_metric(np.array([0.5, 0.5]))
    lopsided = p.coherence_metric(np.array([1.0, 0.02]))
    assert lopsided < 0.1 * balanced + 0.05


def test_swedenborg_zero_scores_give_zero_coherence():
    p = SwedenborgProtocol()
    assert p.coherence_metric(np.array([0.0, 0.0])) == 0.0


def test_gurdjieff_balance_beats_intensity():
    """Perfect balance outscores one centre running alone. This is the
    one substantive claim the function makes.
    """
    p = GurdjieffProtocol()
    balanced = p.coherence_metric(np.array([0.5, 0.5, 0.5, 0.5]))
    lopsided = p.coherence_metric(np.array([1.0, 0.0, 0.0, 0.0]))
    assert balanced > lopsided


def test_gurdjieff_perception_produces_three_centres():
    p = GurdjieffProtocol()
    assert np.atleast_2d(p.perception_transform(np.random.randn(2, 4))).shape[0] == 3


def test_stamets_percept_depends_on_input():
    """The correlation version saturated to an identical matrix whatever
    the input, which made the metric constant. Guard.
    """
    p = StametsProtocol()
    a = p.perception_transform(np.random.default_rng(3).normal(size=(5, 4)))
    b = p.perception_transform(np.random.default_rng(4).normal(size=(5, 4)))
    assert not np.allclose(a, b)


def test_stamets_handles_a_single_row():
    """It collapsed to 1x1 before, and then every score passed through
    untouched.
    """
    p = StametsProtocol()
    out = p.perception_transform(np.arange(4.0))
    assert np.size(out) > 1


def test_stamets_coherence_responds_to_density():
    p = StametsProtocol()
    dense = p.coherence_metric(np.full(8, 0.9))
    sparse = p.coherence_metric(np.array([0.9, 0.9, 0.9, 0.01, 0.01, 0.01, 0.01, 0.01]))
    assert dense != sparse


# --------------------------------------------------------------------- compare


def test_compare_reports_every_protocol(signal):
    out = compare(signal, AX, steps=4)
    assert len(out) == 4
    for name, res in out.items():
        assert len(res["trace"]) == 4
        assert "delta" in res


def test_protocols_are_deterministic(signal):
    a = all_protocols()[0].run(signal, AX, steps=4)["trace"]
    b = all_protocols()[0].run(signal, AX, steps=4)["trace"]
    assert a == b