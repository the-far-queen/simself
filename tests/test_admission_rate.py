"""
test_admission_rate.py -- the before/after admission-rate measurement,
pinned.

WHAT THIS FILE ASSERTS, and why each assertion is there
--------------------------------------------------------
1. THE CONSTITUTION'S GROUND IS THE DERIVED ONE. The whole comparison
   is ground-vs-ground, so it only means something if the production
   ground is the derived vector and not the placeholder.

2. THE DERIVED GROUND CONTAINS THE CONSTITUTION. Every one of the
   constitution's own sentences and claims must be admitted. A ground
   that does not contain what the system believes is broken by
   construction -- and the history says this happened: the
   axis-derived ground scored the system's own claims at 0.9017 and
   0.9285 against a 0.94 floor, so the write path refused the
   system's own claims about itself.

3. THE PLACEHOLDER WAS A BLIND SPOT, NOT A WALL. It refused the
   truth and scored the soup ABOVE the ground's own sentence. The
   assertion is the ORDERING -- soup above truth -- because that is
   the shape of the defect, and an ordering survives a re-tuned
   threshold.

4. THE ADVERSARIAL SET STAYS HIGH. The ground's own claims stated
   backwards are SIMILAR to the ground, which is what makes them
   contradictions and what makes a cosine unable to refuse them. This
   assertion exists so the number cannot be "fixed" by quietly
   tightening the floor -- the claim gate is the decision, and the
   similarity gate is a pre-filter.

5. THE FLOOR IS HELD FIXED ACROSS THE COMPARISON. A before/after that
   moves the floor is not a comparison.

Run:
    python -m pytest tests/test_admission_rate.py -q
"""

from __future__ import annotations

import math
import os
import sys

import numpy as np
import pytest

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import bench_admission_rate as BAR  # noqa: E402
from constitutional.constitution import (  # noqa: E402
    Constitution,
    GROUND_CLAIM_TEXT,
    GROUND_SOURCE_TEXT,
)
from constitutional.lexicon.ingest import (  # noqa: E402
    DEFAULT_MIN_COS,
    _derived_floor,
    derived_floor_is_measured,
    gate_m0,
)


# ===========================================================================
# 1. THE PRODUCTION GROUND IS THE DERIVED ONE
# ===========================================================================

def test_the_constitutions_ground_is_the_derived_one():
    """The comparison is ground-vs-ground, so the ground must be derived.

    Measured 2026-10-31: the derived vector is
    [0.170604 0.205376 0.410441 0.296954 0.234646 0.269223 ...] and the
    Constitution's psi_0 is exactly that -- 18 ground texts embedded
    through the semantic embedder and averaged.
    """
    c = Constitution()
    psi0 = np.asarray(c.psi_0, dtype=float)
    ph = BAR.placeholder(psi0.shape[0])
    assert not np.allclose(psi0, ph), (
        "psi_0 is the placeholder [1, 0, 0, ...] -- the similarity gate "
        "is a hash lottery again")
    assert float(np.linalg.norm(psi0)) > 0.0
    # it has CONTENT -- more than one bucket carries mass
    assert int(np.count_nonzero(np.abs(psi0) > 1e-9)) > 4, (
        "psi_0 is effectively a coordinate, not a direction")


# ===========================================================================
# 2. THE DERIVED GROUND CONTAINS THE CONSTITUTION
# ===========================================================================

def test_the_ground_admits_every_one_of_the_constitutions_own_sentences():
    """A ground that does not contain the system is broken by construction.

    THE HISTORY, and it is why this assertion is here: the
    axis-derived ground scored two of the system's own claims at
    0.9017 and 0.9285 against a 0.94 floor, so the write path
    REFUSED THE SYSTEM'S OWN CLAIMS ABOUT ITSELF.
    """
    psi0 = np.asarray(Constitution().psi_0, dtype=float)
    floor = min(DEFAULT_MIN_COS, _derived_floor())
    everything = list(GROUND_SOURCE_TEXT) + list(GROUND_CLAIM_TEXT)
    refused = []
    for text in everything:
        ok, why = gate_m0(BAR.probe_embed(text), psi0, BAR.MAX_NORM, floor)
        if not ok:
            refused.append((text, why))
    assert not refused, (
        "the ground refuses %d of the constitution's own sentences: %s"
        % (len(refused), refused))


def test_the_derived_floor_is_a_measurement_not_the_documented_constant():
    """A silent except turns a measurement into a constant.

    The code's own rule, and the reason `derived_floor_is_measured()`
    exists at all.
    """
    assert derived_floor_is_measured(), (
        "the floor in use is the documented constant, not a measurement")


# ===========================================================================
# 3. THE PLACEHOLDER WAS A BLIND SPOT, NOT A WALL
# ===========================================================================

def test_against_the_placeholder_the_soup_outscores_the_truth():
    """The ORDERING, which is the shape of the defect.

    Against the placeholder, the soup scored 0.3215 and the ground's
    own drift sentence scored 0.1187 -- so the gate refused the truth
    and would have admitted the soup. A wall is visibly broken; a
    blind spot is not, and it is the worse failure.
    """
    ph = BAR.placeholder(16)
    soup = BAR.cos(BAR.probe_embed("soup needs salt and heat and time"), ph)
    truth = BAR.cos(
        BAR.probe_embed("the drift is non increasing under every tick"), ph)
    assert soup > truth, (
        "the soup (%.4f) no longer scores above the ground's own "
        "sentence (%.4f) against the placeholder" % (soup, truth))


def test_against_the_derived_ground_the_soup_scores_below_the_truth():
    """and the derived ground fixes that ordering."""
    psi0 = np.asarray(Constitution().psi_0, dtype=float)
    soup = BAR.cos(BAR.probe_embed("soup needs salt and heat and time"), psi0)
    truth = BAR.cos(
        BAR.probe_embed("the drift is non increasing under every tick"), psi0)
    assert truth > soup, (
        "against the derived ground the soup (%.4f) is not below the "
        "ground's own sentence (%.4f)" % (soup, truth))


# ===========================================================================
# 4. THE ADVERSARIAL SET STAYS HIGH
# ===========================================================================

def test_the_adversarial_set_is_admitted_by_the_similarity_gate():
    """A cosine cannot see polarity, and that is the DESIGN.

    The ground's own claims stated backwards are SIMILAR to the ground:
    measured mean cos 0.9239, against 0.9476 for the truth. A
    contradiction is similar to the ground -- that is what makes it a
    contradiction rather than an off-topic sentence, and it is why the
    CLAIM GATE is the decision and the similarity gate is a
    pre-filter.

    This assertion exists so the admission rate cannot be "improved"
    by quietly tightening the floor until the adversarial set is
    refused -- that would break the constitution's own sentences too,
    which is the defect the axis-derived ground had.
    """
    psi0 = np.asarray(Constitution().psi_0, dtype=float)
    floor = min(DEFAULT_MIN_COS, _derived_floor())
    admitted = 0
    for text in BAR.ADVERSARIAL:
        ok, _why = gate_m0(BAR.probe_embed(text), psi0, BAR.MAX_NORM, floor)
        admitted += 1 if ok else 0
    assert admitted >= len(BAR.ADVERSARIAL) - 2, (
        "the similarity gate admitted only %d of %d adversarial spans -- "
        "it is no longer the coarse pre-filter it is meant to be, and "
        "the claim gate is the decision"
        % (admitted, len(BAR.ADVERSARIAL)))


def test_the_baseline_is_the_placeholder_and_not_the_derived_ground():
    """The BEFORE has to BE the placeholder, or the comparison is circular.

    A mutation that replaced the baseline vector with the derived one
    left this file GREEN -- measured 2026-10-31. The reason is worth
    recording: every other assertion here is a PROPERTY (the ground
    contains the constitution, the soup scores below the truth, the
    adversarial set stays admitted), and the soup-ordering property
    holds for BOTH vectors -- measured: soup 0.7452 vs truth 0.6364
    against the mutated baseline, and soup 0.3215 vs truth 0.1187
    against the real one. So a property cannot tell the placeholder
    from the derived ground.

    What tells them apart is the SHAPE: the placeholder is a
    coordinate -- all its mass in one bucket -- and the derived ground
    is a direction with mass spread across many buckets. So the
    baseline is pinned by its SHAPE, not by its values, which also
    means the assertion survives the exact numbers moving.
    """
    ph = BAR.placeholder(16)
    nonzero = int(np.count_nonzero(np.abs(ph) > 1e-9))
    assert nonzero == 1, (
        "the baseline vector has %d non-zero buckets -- it is not the "
        "placeholder coordinate, so the before/after comparison is not "
        "measuring what it claims" % (nonzero,))
    assert abs(float(ph[0]) - 1.0) < 1e-12


def test_the_floor_in_use_is_the_production_floor_not_a_wider_one():
    """The floor is the ONE thing a before/after must not move.

    A mutation that loosened the bench's floor to 0.80 left this file
    GREEN -- measured 2026-10-31, and the reason is worth recording:
    the test computed the floor with the SAME expression the bench
    used, so the two agreed by construction and neither could catch the
    other. A check that reads its expected value from the code under
    test is not a check.

    So the floor is pinned here by its OWN properties: it is the
    production floor, it is MEASURED rather than the documented
    constant, and it is not wider than DEFAULT_MIN_COS -- because
    `gate_m0` uses `min(DEFAULT_MIN_COS, _derived_floor())` and a wider
    floor would admit the far text the pre-filter exists to refuse.

    AND THE MEASURED CONSEQUENCE, which is the number worth keeping: the
    derived floor is 0.876168, and the constitution's own weakest
    sentence sits at 0.8812. So the production floor is LOOSER than
    DEFAULT_MIN_COS (0.94), and at 0.94 only 18 of the 26 ground
    sentences would clear it. The derived floor is what keeps the
    ground containing the constitution.
    """
    from constitutional.lexicon.ingest import _derived_floor as _df
    production_floor = min(DEFAULT_MIN_COS, _df())

    # the floor the BENCH uses must BE the production floor. And the
    # bench's own function is called here -- not a private copy of the
    # expression -- so a mutation inside the bench is visible.
    import bench_admission_rate as BAR2
    bench_floor = BAR2.resolved_floor()
    assert abs(bench_floor - production_floor) < 1e-12, (
        "the bench uses the floor %.6f but the production floor is %.6f"
        % (bench_floor, production_floor))

    psi0 = np.asarray(Constitution().psi_0, dtype=float)

    # it is a measurement, and it is not wider than the documented one
    assert derived_floor_is_measured()
    assert bench_floor <= DEFAULT_MIN_COS + 1e-9, (
        "the floor in use (%.6f) is WIDER than DEFAULT_MIN_COS (%.6f) -- "
        "the gate has been widened"
        % (bench_floor, DEFAULT_MIN_COS))

    # AND THE DERIVED FLOOR IS WHAT KEEPS THE CONSTITUTION IN: the
    # production floor admits every ground sentence, and the
    # documented one would not.
    everything = list(GROUND_SOURCE_TEXT) + list(GROUND_CLAIM_TEXT)
    at_production = sum(
        1 for t in everything
        if gate_m0(BAR2.probe_embed(t), psi0, BAR2.MAX_NORM,
                   production_floor)[0])
    assert at_production == len(everything), (
        "the production floor admits only %d of %d ground sentences"
        % (at_production, len(everything)))


# ===========================================================================
# 5. THE FLOOR IS HELD FIXED ACROSS THE COMPARISON
# ===========================================================================

def test_the_comparison_holds_the_floor_fixed():
    """A before/after that moves the floor is not a comparison.

    The bench resolves the floor ONCE and passes the same number to
    both grounds. This asserts it, because the alternative -- letting
    each ground use its own floor -- would manufacture the result.
    """
    psi0 = np.asarray(Constitution().psi_0, dtype=float)
    floor = min(DEFAULT_MIN_COS, _derived_floor())
    before = BAR.measure(BAR.placeholder(psi0.shape[0]),
                          list(BAR.FAR), floor)
    after = BAR.measure(psi0, list(BAR.FAR), floor)
    assert before["total"] == after["total"]
    # and the derived ground admits MORE far text than the placeholder --
    # the honest result, measured rather than hoped for
    assert after["admitted"] >= before["admitted"], (
        "the derived ground admits %d of %d far spans and the "
        "placeholder admits %d -- the derived ground is not the stricter "
        "one, and the numbers must say so"
        % (after["admitted"], after["total"], before["admitted"]))


def test_the_far_set_is_not_wholly_admitted():
    """the pre-filter still refuses the clearly-far.

    MEASURED: the single words are refused (cos 0.38 to 0.71) and the
    ordinary sentences are admitted (cos 0.84 to 0.97). So the far set
    is not uniformly refused -- and this assertion pins the half that
    IS refused, which is the half the pre-filter is for.
    """
    psi0 = np.asarray(Constitution().psi_0, dtype=float)
    floor = min(DEFAULT_MIN_COS, _derived_floor())
    refused = 0
    for text in BAR.FAR:
        ok, _why = gate_m0(BAR.probe_embed(text), psi0, BAR.MAX_NORM, floor)
        refused += 0 if ok else 1
    assert refused >= 6, (
        "only %d of %d far spans were refused -- the pre-filter has "
        "stopped pre-filtering" % (refused, len(BAR.FAR)))
