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
from constitutional.lexicon.ingest import gate_m0  # noqa: E402

MIN_COS = 0.4  # harness.gate.MIN_COS, duplicated deliberately: this is the
                # threshold being measured against, and if it moves the
                # finding needs re-measuring, so a silent move should fail.

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


def test_psi_0_is_currently_a_single_axis():
    """The geometric fact behind the finding. If this changes, re-measure."""
    nz = np.nonzero(np.abs(_psi0()) > 1e-9)[0]
    assert list(nz) == [0], (
        f"psi_0 nonzero axes changed to {list(nz)} — the finding in "
        f"MYSELF/14-2026-10-16-psi-zero-single-axis.md must be re-measured"
    )


def test_psi_0_is_unit_norm():
    assert abs(float(np.linalg.norm(_psi0())) - 1.0) < 1e-9


def test_mean_cosine_to_real_spans_is_below_the_threshold():
    """The cost, pinned. 0.244 measured; asserted with tolerance."""
    psi0 = _psi0()
    coss = [float(np.dot(embed_text(p), psi0)) for p in PROBES]
    mean = statistics.mean(coss)
    assert mean == pytest.approx(0.2135, abs=0.04), (
        f"mean cos drifted to {mean:.3f} — re-measure and update the note"
    )


def test_most_real_spans_are_refused_at_the_current_geometry():
    """3/12 measured. If this starts passing broadly, psi_0 changed."""
    psi0 = _psi0()
    passed = sum(
        1 for p in PROBES if gate_m0(embed_text(p), psi0, 4.0, MIN_COS)[0]
    )
    assert passed <= 7, (
        f"{passed}/{len(PROBES)} now pass the gate — the single-axis ground "
        f"is no longer blocking language. Re-measure and update the note."
    )


def test_a_mean_direction_ground_would_admit_most_spans():
    """The comparison that makes the finding a finding, not a complaint.

    Same embedder, same threshold, different ground. If this stops holding,
    the diagnosis ("the ground, not the threshold") is wrong.
    """
    vecs = [embed_text(p) for p in PROBES]
    mean_dir = np.mean(vecs, axis=0)
    mean_dir = mean_dir / np.linalg.norm(mean_dir)
    coss = [float(np.dot(v, mean_dir)) for v in vecs]
    passed = sum(1 for c in coss if c > MIN_COS)
    # MEASURED on the neutral 24-word list: mean 0.4020, 14/24 pass.
    # (An earlier version of this test asserted mean > 0.45 and passed only
    # against a hand-picked, gate-friendly sample. The corrected sample is
    # harder and the conclusion survived it — which is the part that matters.)
    assert statistics.mean(coss) > 0.35, "mean-direction ground no longer helps"
    assert passed >= len(PROBES) - 10, (
        f"mean-direction ground only admits {passed}/{len(PROBES)}"
    )


def test_single_axis_ground_provides_no_ranking():
    """A lookup table is not a governor.

    Against one axis almost every span scores exactly 0.000, so the gate
    cannot distinguish "near" from "far" — only in/out.
    """
    psi0 = _psi0()
    coss = [float(np.dot(embed_text(p), psi0)) for p in PROBES]
    at_zero = sum(1 for c in coss if abs(c) < 1e-9)
    assert at_zero >= len(PROBES) - 8, (
        f"only {at_zero}/{len(PROBES)} collapsed to zero — the single-axis "
        f"ground has started ranking, so this finding is stale"
    )


def test_gate_still_discriminates_on_the_axis_it_tests():
    """Whatever is wrong with the geometry, the veto is real.

    If this fails, the gate has become a wall (refuse everything) or a
    rubber stamp (allow everything), and every other assertion here is moot.
    """
    psi0 = _psi0()
    assert gate_m0(embed_text("form"), psi0, 4.0, MIN_COS)[0] is True
    assert gate_m0(embed_text("truth"), psi0, 4.0, MIN_COS)[0] is False