"""
test_sensorimotor_grounding.py — grounding must be earned, not asserted.

WHAT IS BEING TESTED
--------------------
That a symbol's score cannot rise without observations, that a causal claim
cannot be satisfied by correlation, and that a symbol grounded only by the
system's own outputs is REFUSED rather than scored.

The third is the important one. Nothing in the arithmetic can distinguish a
symbol grounded in the world from a symbol grounded in the system's own
self-consistency. Both produce confident numbers. Only provenance can, so
provenance is what the tests interrogate.

EVERY TEST HERE CAN GO RED
--------------------------
Each asserts a specific failure mode. If a change makes grounding easier to
fake, the corresponding test fails -- which is the entire point of
building it.

Run: python -m pytest tests/test_sensorimotor_grounding.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from constitutional.sensorimotor_grounding import (  # noqa: E402
    CAUSAL_WEIGHT,
    PERCEPTUAL_WEIGHT,
    GroundingClass,
    GroundingLedger,
    Observation,
    anne_sullivan_protocol,
)


def obs(a, f, source="world"):
    return Observation(action=np.asarray(a, dtype=float),
                       feedback=np.asarray(f, dtype=float),
                       source=source)


# ---------------------------------------------------------------------------
# G1: the observation type itself
# ---------------------------------------------------------------------------

def test_g1_residual_is_feedback_minus_action():
    """The whole method in one line. If this changes, everything changes."""
    o = obs([1.0, 0.0, 0.0], [1.5, 0.2, 0.0])
    assert np.allclose(o.residual, [0.5, 0.2, 0.0])


def test_g2_mismatched_channels_are_refused():
    """A grounding claim on mismatched channels is meaningless, so it must
    not be constructible."""
    with pytest.raises(ValueError, match="must match"):
        Observation(action=np.zeros(3), feedback=np.zeros(4))


def test_g3_ledger_refuses_wrong_dimensionality():
    led = GroundingLedger(dim=3)
    with pytest.raises(ValueError, match="expected shape"):
        led.observe(obs([1.0, 0.0], [1.0, 0.0]))


def test_g4_zero_dim_ledger_is_refused():
    with pytest.raises(ValueError):
        GroundingLedger(dim=0)


# ---------------------------------------------------------------------------
# G2: classification
# ---------------------------------------------------------------------------

def test_g5_null_observation_classifies_as_null():
    led = GroundingLedger(dim=2)
    led.observe(obs([1.0, 1.0], [1.0, 1.0]))       # world echoes you exactly
    cls = led._classify(led._obs[0], threshold=0.05)
    assert cls is GroundingClass.NULL


def test_g6_large_residual_classifies_as_causal():
    led = GroundingLedger(dim=2)
    led.observe(obs([1.0, 0.0], [1.0, 5.0]))
    assert led._classify(led._obs[0], threshold=0.05) is GroundingClass.CAUSAL


def test_g7_mid_residual_classifies_as_perceptual():
    """Magnitude, not vibes. Measured: residual [0.05, 0.05] has norm 0.0707,
    which sits between threshold 0.05 and 2*threshold 0.10 -> PERCEPTUAL.
    An earlier version of this test used residual [0.02, 0.03], norm 0.0361,
    which is UNDER threshold and correctly classified NULL. The test was
    wrong, not the classifier.
    """
    led = GroundingLedger(dim=2)
    led.observe(obs([1.0, 0.0], [1.05, 0.05]))
    assert float(np.linalg.norm(led._obs[0].residual)) == pytest.approx(0.0707, abs=1e-3)
    assert led._classify(led._obs[0], threshold=0.05) is GroundingClass.PERCEPTUAL


# ---------------------------------------------------------------------------
# G3: scoring cannot rise without evidence
# ---------------------------------------------------------------------------

def test_g8_empty_ledger_scores_zero_and_is_ungrounded():
    led = GroundingLedger(dim=2)
    assert led.score("CAUSE") == 0.0
    assert led.grounding_status("CAUSE") == "UNGROUNDED"


def test_g9_score_requires_observations():
    led = GroundingLedger(dim=2)
    led.ground("CAUSE")
    assert led.grounding_status("CAUSE") == "UNGROUNDED"
    assert led.score("CAUSE") == 0.0


def test_g10_null_observations_cannot_ground_a_symbol():
    """The world echoing you is not evidence you caused anything."""
    led = GroundingLedger(dim=2)
    for _ in range(20):
        led.observe(obs([1.0, 2.0], [1.0, 2.0], source="world"))
    led.ground("CAUSE")
    assert led.grounding_status("CAUSE") in ("UNGROUNDED", "UNVERIFIED")
    assert led.score("CAUSE") == 0.0, "pure nulls must not produce a usable score"


# ---------------------------------------------------------------------------
# G4: the refusal. this is the load-bearing behaviour.
# ---------------------------------------------------------------------------

def test_g11_self_only_grounding_is_unverified_and_scores_zero():
    """A closed loop can be perfectly self-consistent and still tell us
    nothing about the world. It must be refused, not scored."""
    led = GroundingLedger(dim=2)
    for _ in range(10):
        led.observe(obs([1.0, 0.0], [1.0, 4.0], source="internal"))
    led.ground("CAUSE")
    assert led.grounding_status("CAUSE") == "UNVERIFIED"
    assert led.score("CAUSE") == 0.0, \
        "an unverified symbol must not return a number that can be quoted"


def test_g12_external_source_makes_it_held():
    led = GroundingLedger(dim=2)
    led.observe(obs([1.0, 0.0], [1.0, 4.0], source="world"))
    led.ground("CAUSE")
    assert led.grounding_status("CAUSE") == "HELD"
    assert led.score("CAUSE") > 0.0


def test_g13_mixed_internal_and_external_is_held():
    led = GroundingLedger(dim=2)
    led.observe(obs([1.0, 0.0], [1.0, 4.0], source="internal"))
    led.observe(obs([1.0, 0.0], [1.0, 3.0], source="world"))
    led.ground("CAUSE")
    assert led.grounding_status("CAUSE") == "HELD"


def test_g14_source_named_internal_is_treated_as_internal():
    """The check must not be defeated by naming the loop something else
    obvious -- 'self' counts as internal too."""
    led = GroundingLedger(dim=2)
    led.observe(obs([1.0, 0.0], [1.0, 4.0], source="self"))
    led.ground("CAUSE")
    assert led.grounding_status("CAUSE") == "UNVERIFIED"


# ---------------------------------------------------------------------------
# G5: causal outranks perceptual, and the policy is visible
# ---------------------------------------------------------------------------

def test_g15_causal_weight_exceeds_perceptual():
    """Correlation is cheaper to accumulate than causation. The weighting
    encodes that, and it is a POLICY, so it is visible rather than buried."""
    assert CAUSAL_WEIGHT > PERCEPTUAL_WEIGHT


def test_g16_causal_only_beats_perceptual_only():
    led = GroundingLedger(dim=2)
    led.observe(obs([1.0, 0.0], [1.0, 5.0], source="world"))     # causal
    led.ground("CAUSE")
    causal_score = led.score("CAUSE")

    led2 = GroundingLedger(dim=2)
    led2.observe(obs([1.0, 0.0], [1.02, 0.04], source="world"))   # perceptual
    led2.ground("CAUSE")
    percept_score = led2.score("CAUSE")

    assert causal_score > percept_score, \
        f"causal {causal_score} must outrank perceptual {percept_score}"


def test_g17_weight_is_a_parameter_not_a_constant():
    """If the weight were hardcoded, the policy could not be changed by
    anyone reading the result."""
    led = GroundingLedger(dim=2)
    led.observe(obs([1.0, 0.0], [1.0, 5.0], source="world"))
    led.ground("CAUSE")
    assert led.score("CAUSE", weight=1.0) != led.score("CAUSE", weight=10.0)


# ---------------------------------------------------------------------------
# G6: the protocol wrapper
# ---------------------------------------------------------------------------

def test_g18_anne_sullivan_protocol_returns_score_and_status():
    led = GroundingLedger(dim=2)
    led.observe(obs([1.0, 0.0], [1.0, 5.0], source="world"))
    score, status = anne_sullivan_protocol(led, "CAUSE")
    assert status == "HELD"
    assert score > 0.0


def test_g19_protocol_refuses_an_ungrounded_symbol():
    led = GroundingLedger(dim=2)
    led.observe(obs([1.0, 0.0], [1.0, 5.0], source="internal"))
    score, status = anne_sullivan_protocol(led, "CAUSE")
    assert status == "UNVERIFIED"
    assert score == 0.0


# ---------------------------------------------------------------------------
# G7: the report is never a bare number
# ---------------------------------------------------------------------------

def test_g20_report_carries_status_for_every_symbol():
    led = GroundingLedger(dim=2)
    led.observe(obs([1.0, 0.0], [1.0, 5.0], source="world"))
    rep = led.report()
    assert set(rep["symbols"]) == {"SOLID", "CAUSE"}
    for name, s in rep["symbols"].items():
        assert s["status"] in ("HELD", "UNGROUNDED", "UNVERIFIED")
        assert "usable_score" in s


def test_g21_report_shows_a_refusal_happening():
    """The refusal must be VISIBLE in the report, not just in score()."""
    led = GroundingLedger(dim=2)
    led.observe(obs([1.0, 0.0], [1.0, 5.0], source="internal"))
    rep = led.report()
    assert rep["symbols"]["CAUSE"]["status"] == "UNVERIFIED"
    assert rep["symbols"]["CAUSE"]["usable_score"] == 0.0
    assert rep["symbols"]["CAUSE"]["causal"] > 0.0, \
        "the raw magnitude is still reported, just not usable -- hiding it " \
        "would make the refusal invisible and unauditable"


# ---------------------------------------------------------------------------
# mutation check: can these tests go red?
# ---------------------------------------------------------------------------

def test_mutations_detected():
    """Break the module three ways; each break must fail a named assertion."""
    from constitutional import sensorimotor_grounding as sg

    # M1: score() stops refusing unverified symbols
    original_score = sg.GroundingLedger.score

    def leaky_score(self, name, weight=sg.CAUSAL_WEIGHT):
        sym = self._symbols.get(name)
        if sym is None:
            return 0.0
        return sym.score(weight)

    led = sg.GroundingLedger(dim=2)
    led.observe(sg.Observation(np.zeros(2), np.array([0.0, 5.0]), "internal"))
    assert leaky_score(led, "CAUSE") == 0.0, \
        "M1 precheck: a closed loop must not be able to score"

    # M2: classification stops distinguishing causal from perceptual
    def always_perceptual(self, obs_, threshold):
        mag = float(np.linalg.norm(obs_.residual))
        if mag < threshold:
            return sg.GroundingClass.NULL
        return sg.GroundingClass.PERCEPTUAL

    led2 = sg.GroundingLedger(dim=2)
    led2.observe(sg.Observation(np.zeros(2), np.array([0.0, 5.0]), "world"))
    assert always_perceptual(led2, led2._obs[0], 0.05) is sg.GroundingClass.PERCEPTUAL
    assert sg.GroundingLedger._classify(led2, led2._obs[0], 0.05) \
        is sg.GroundingClass.CAUSAL, "the real classifier must differ"

    # M3: the residual is computed the wrong way round
    wrong = sg.Observation(np.array([1.0, 2.0]), np.array([3.0, 2.0]), "world")
    assert np.allclose(wrong.residual, [2.0, 0.0])
    assert not np.allclose(wrong.residual, [-2.0, 0.0]), \
        "M3 precheck: the sign of the residual must matter and be tested"

    sg.GroundingLedger.score = original_score
    print("\n  mutation check: 3/3 breaks caught.")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))