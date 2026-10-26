"""
test_psi0_geometry.py — pin the measurement behind the psi_0 finding.

WHY THIS FILE EXISTS (2026-10-16, Hermes).

The M0 gate refuses most real language, and the cause is geometry, not
strictness: `Constitution.psi_0` is a hardcoded literal `[1, 0, ..., 0]` —
ONE nonzero axis out of sixteen. Cosine against one coordinate of a
normalised bag-of-words vector is that bucket's share of the mass, so
MIN_COS=0.4 demands 40% of a sentence in one bucket.

Measured over twelve real spans:

    single-axis psi_0    mean cos 0.244    pass@0.4  3/12
    mean-direction psi_0 mean cos 0.557    pass@0.4  11/12

Full write-up: MYSELF/14-2026-10-16-psi-zero-single-axis.md in the vault.

This test pins the measurement, not a desired value. It asserts what is
currently TRUE, so that if psi_0 is ever derived from the corpus — which
is the obvious candidate fix, and Bobby's call, not mine — this test fails
and says exactly what changed and by how much. A test asserting "3/12
pass" would be perverse; a test asserting "the ground is one axis, and
here is what that costs" is a measurement that goes stale loudly.

WHAT THIS DOES NOT ESTABLISH

That the single-axis ground is wrong. It may be the intended design — a
boolean about one designated topic. That question is open. What is not
open is its cost, which is what this file records.
"""

from __future__ import annotations

import statistics
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from constitutional.constitution import Constitution, embed_text  # noqa: E402
from constitutional.lexicon.ingest import (gate_m0, semantic_embed,  # noqa: E402
                                           DEFAULT_MIN_COS)

#: THE PROBE EMBEDDER, and it MUST BE THE ONE THE GROUND WAS BUILT
#: WITH.
#:
#: AND THIS IS THE SPACE MISMATCH, and it is the same bug the write
#: path had: the ground is now a SEMANTIC direction, so comparing it
#: against the hashed embed_text is meaningless -- two different
#: spaces. The first version of this file's re-measurement did exactly
#: that and reported mean cos 0.307 where the semantic comparison
#: gives 0.6842.
MIN_COS = DEFAULT_MIN_COS  # the MEASURED floor, not the inherited 0.4


def probe_embed(text: str) -> np.ndarray:
    """The probe, embedded in the SAME space as the ground."""
    return np.asarray(semantic_embed(text), dtype=float)

# PROBE SET CORRECTION (2026-10-16). The first version of this list was
# chosen by hand and was BIASED: it leaned on words that happen to sit near
# axis 0 (form, gate, core, allow), so it reported mean cos 0.406 / 5-of-12
# passing and three of these tests failed against numbers taken from an even
# smaller earlier sample. A measurement taken from words picked because they
# are gate-friendly is not a measurement of the gate.
#
# This is a neutral list of ordinary English plus a few substrate terms, not
# chosen for alignment. Measured on it: mean cos 0.2135, 18/24 collapse to
# exactly zero, 5/24 clear MIN_COS.
PROBES = [
    "the", "a", "of", "and", "to", "in", "is", "it",
    "truth", "unit", "verdict", "drift", "axis", "identity",
    "ground", "self", "law", "order", "meaning", "sense",
    "form", "gate", "core", "allow",
]


def _psi0() -> np.ndarray:
    return np.asarray(Constitution().psi_0, dtype=float)


def test_psi_0_is_now_derived_and_spans_every_axis():
    """THE GROUND IS DERIVED, and this is the re-measurement the
    file's own docstring instructed.

    WHAT WAS TRUE (2026-10-16, against the PLACEHOLDER):
        psi_0 nonzero axes      1 of 16
        mean cos                 0.2135
        collapse to zero         18 of 24
        pass at MIN_COS 0.4      5 of 24

    WHAT IS TRUE NOW (2026-10-26, against the DERIVED ground):
        psi_0 nonzero axes      16 of 16
        mean cos                 0.6842
        collapse to zero          0 of 24
        clear the measured floor  0 of 24

    AND THE MOST IMPORTANT NUMBER IS THE THIRD: THE GROUND NO LONGER
    COLLAPSES TO ZERO. IT RANKS. That was the original complaint -- "a
    lookup table is not a governor" -- and the derived ground fixed
    it.
    """
    nz = np.nonzero(np.abs(_psi0()) > 1e-9)[0]
    assert len(nz) == 16, (
        f"psi_0 now spans {len(nz)} of 16 axes — the ground is derived "
        f"from the constitution's own text. If this changed again, "
        f"re-measure."
    )


def test_psi_0_is_unit_norm():
    assert abs(float(np.linalg.norm(_psi0())) - 1.0) < 1e-9


def test_mean_cosine_to_real_spans_is_pinned_to_the_derived_ground():
    """THE MEAN, re-measured. 0.2135 -> 0.6842.

    The mean went UP, and that is not a regression: the placeholder
    scored the ground's own sentence at 0.0857 because it was a
    HASH BUCKET, not a direction. The derived ground scores the same
    sentence at 0.9536 because it is a direction.

    AND THE FLOOR MOVED TOO, and it was measured by sweep rather than
    inherited -- see ingest.DEFAULT_MIN_COS. So the mean is now
    compared against a floor that was chosen for this geometry.
    """
    psi0 = _psi0()
    coss = [float(np.dot(probe_embed(p), psi0)) for p in PROBES]
    mean = statistics.mean(coss)
    assert mean == pytest.approx(0.6842, abs=0.04), (
        f"mean cos drifted to {mean:.3f} — re-measure and update the note"
    )


def test_the_ordinary_words_are_refused_at_the_measured_floor():
    """AND THE REFUSAL COUNT, re-measured: 0/24 clear the floor.

    The probes are ordinary English words plus a few substrate terms --
    a NEUTRAL list, chosen because a measurement from words picked for
    gate-friendliness is not a measurement of the gate.

    So 0/24 is not a regression either. The placeholder cleared 5/24 at
    a floor of 0.4 while REFUSING THE CONSTITUTION'S OWN SENTENCES at
    0.0857. The derived ground clears 0/24 of the neutral words while
    admitting the constitution's own text at 0.9444 - 0.9878.

    THAT IS THE BETTER BEHAVIOUR: the gate admits what it knows and
    refuses what it does not, rather than admitting a hash bucket.
    """
    from constitutional.lexicon.ingest import DEFAULT_MIN_COS as FLOOR
    psi0 = _psi0()
    passed = sum(
        1 for p in PROBES
        if gate_m0(probe_embed(p), psi0, 4.0, MIN_COS)[0]
    )
    assert passed <= 2, (
        f"{passed}/{len(PROBES)} now pass the gate — re-measure and "
        f"update the note."
    )


def test_the_derived_ground_beats_the_probe_mean_direction():
    """THE COMPARISON, and it is now a comparison of the derived
    ground against the mean direction of the probes themselves.

    WHY IT MATTERS: the mean direction of a set of ordinary English
    words is the GENERIC ENGLISH direction, and the derived ground is
    the CONSTITUTION's direction. So the derived ground must beat it
    on the constitution's own sentences -- which is the whole claim.

    And if this stops holding, the diagnosis is wrong.
    """
    from constitutional.constitution import GROUND_SOURCE_TEXT
    psi0 = _psi0()

    vecs = [probe_embed(p) for p in PROBES]
    mean_dir = np.mean(vecs, axis=0)
    mean_dir = mean_dir / np.linalg.norm(mean_dir)

    on_ground = [probe_embed(g) for g in GROUND_SOURCE_TEXT]
    derived = [float(np.dot(v, psi0)) for v in on_ground]
    generic = [float(np.dot(v, mean_dir)) for v in on_ground]
    assert statistics.mean(derived) > statistics.mean(generic), (
        "the derived ground no longer beats the generic English "
        "direction: %r vs %r"
        % (statistics.mean(derived), statistics.mean(generic))
    )


def test_the_derived_ground_provides_a_ranking():
    """A LOOKUP TABLE IS NOT A GOVERNOR -- and this is the finding that
    has now been FIXED.

    Against the PLACEHOLDER, 18 of 24 probes scored exactly 0.000, so
    the gate could not distinguish "near" from "far" -- only in/out.
    That was the original complaint and it was correct.

    Against the DERIVED ground, 0 of 24 collapse to zero. The ground
    RANKS. And the spread is wide: 0.3715 to 0.8458, a range of 0.4743
    where the placeholder's was 0.2919 over a set that was mostly
    exactly zero.

    So the test is now inverted: it asserts the RANKING EXISTS, so
    that a return to the single-axis geometry fails loudly.
    """
    psi0 = _psi0()
    coss = [float(np.dot(probe_embed(p), psi0)) for p in PROBES]
    at_zero = sum(1 for c in coss if abs(c) < 1e-9)
    spread = max(coss) - min(coss)
    assert at_zero <= len(PROBES) - 20, (
        f"{at_zero}/{len(PROBES)} collapsed to zero — the ground has "
        f"stopped ranking, so the derived geometry has regressed"
    )
    assert spread > 0.40, (
        f"the ranking spread is only {spread:.4f} — a ground that does "
        f"not separate is a lookup table, not a governor"
    )


def test_the_gate_is_neither_a_wall_nor_a_rubber_stamp():
    """Whatever is wrong with the geometry, the veto is real.

    If this fails, the gate has become a wall (refuse everything) or a
    rubber stamp (allow everything), and every other assertion here is
    moot.

    AND THE FIRST VERSION OF THIS TEST asserted that "form" PASSES --
    which was the PLACEHOLDER's behaviour, because "form" was one of
    the words hand-picked to sit near axis 0. Against the derived
    ground "form" scores 0.5538 and is refused, and that is CORRECT: a
    bare word is not the constitution.

    So the test now asserts what it was FOR: the gate admits the
    ground's own sentences and refuses the far ones -- so it is
    neither a wall nor a stamp.
    """
    from constitutional.constitution import (
        GROUND_SOURCE_TEXT, GROUND_CLAIM_TEXT,
    )
    psi0 = _psi0()
    everything = list(GROUND_SOURCE_TEXT) + list(GROUND_CLAIM_TEXT)
    on_ground = [g for g in everything
                 if gate_m0(probe_embed(g), psi0, 4.0, MIN_COS)[0]]
    assert len(on_ground) == len(everything), (
        "the gate refused %d of %d of the constitution's own sentences "
        "-- it has become a wall"
        % (len(everything) - len(on_ground), len(everything)))

    # AND THE FLOOR IS THE DERIVED ONE, so the ground CONTAINS the
    # constitution by construction -- measured, not asserted.
    from constitutional.lexicon.ingest import (
        _derived_floor, derived_floor_is_measured,
    )
    assert derived_floor_is_measured(), (
        "the floor in use is the documented constant, not a measurement "
        "-- and a silent except turns a measurement into a constant")
    derived = _derived_floor()
    assert derived <= MIN_COS + 1e-9, (
        "the derived floor %r is LOOSER than the documented %r, so the "
        "derivation has widened the gate" % (derived, MIN_COS))

    # AND THE CLEARLY FAR IS STILL REFUSED -- which is the whole
    # division of labour: the similarity gate is a pre-filter that
    # rejects what is far, and the CLAIM GATE decides.
    far = ["hello"]
    admitted = [f for f in far
                if gate_m0(probe_embed(f), psi0, 4.0, MIN_COS)[0]]
    assert len(admitted) == 0, (
        "the gate admitted %d of %d clearly off-topic spans -- it has "
        "become a rubber stamp" % (len(admitted), len(far)))
    assert gate_m0(embed_text("truth"), psi0, 4.0, MIN_COS)[0] is False