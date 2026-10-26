"""
test_admit_seam.py — the route from a model proposal to a committed unit.

WHY THIS FILE EXISTS (2026-10-16, Hermes).

`coding_operator_object` (the model's gated I/O surface) and
`constitutional.lexicon.ingest` (documented as the ONLY write path for
language) both existed and neither could reach the other. `constitutional/
admit.py` is the seam. Three defects were found while building it and each
one is pinned here, because all three produced plausible-looking output:

  1. WRONG VERDICT FIELD. The seam first read `verdict.status`, which does
     not exist on the dataclass. getattr returned None for every span, so
     every ALLOWED span fell into the refusal branch: 100% refusal, index
     never grew, no exception, no output that looked wrong. A gate that
     refuses everything is a wall.

  2. DOUBLE APPEND. ingest() appends the unit itself in each of its three
     return branches. The seam passed in its own index and then appended
     AGAIN, so one admit() produced the span twice and the index grew at 2x.
     Duplicated units corrupt nearest_committed() costs for every later
     admission — drift that would surface weeks later as "the gate got
     stricter" with no obvious cause.

  3. UNSTABLE EMBEDDING. embed_bag used Python's builtin hash(), randomized
     per process, so the same span landed on a different axis each run. The
     fix is in ingest.py (blake2b); the test below pins the reproducibility
     because it is the property that made defects 1 and 2 invisible.

WHAT THIS DOES NOT ESTABLISH

That self-coding works. Sandbox execution, version comparison and rollback
are still absent and atlas-exam area 18 is right to fail. This establishes
reachability plus a veto that bites in both directions.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from constitutional.admit import Admitter  # noqa: E402
from constitutional.lexicon.ingest import embed_bag  # noqa: E402

# Measured axis-0 cosines under the stable hash. These are the words the
# substrate's own psi_0 = [1,0,...,0] actually aligns with.
#: THE ALIGNED SPANS, RE-DERIVED FOR THE DERIVED GROUND.
#:
#: "form", "gate", "core", "allow" were near the PLACEHOLDER's axis 0
#: by construction -- those words were picked because they hashed into
#: bucket 0. Against the derived ground they are not near it, so every
#: one of them is refused and the test's own assertion fires:
#: "every aligned span was refused -- the gate is a wall".
#:
#: And that assertion is CORRECT and worth keeping -- a gate that
#: refuses everything IS a wall. So the fix is to give the test spans
#: that are genuinely aligned with the CURRENT ground, chosen by
#: MEASURING.
ALIGN_CANDIDATES = (
    "the constitutional ground is write protected",
    "the gate refuses a packet below the coherence threshold",
    "the drift is non increasing under every tick",
    "a span is admitted only when the gate passes",
    "the embedding norm is bounded and a packet above it is refused",
)


def _aligned_spans():
    """The spans nearest the ground, chosen by measuring."""
    import numpy as np
    from constitutional.constitution import Constitution
    from constitutional.lexicon.ingest import semantic_embed

    psi0 = np.asarray(Constitution().psi_0, dtype=float)

    def cos(text):
        v = np.asarray(semantic_embed(text), dtype=float)
        return float(np.dot(v, psi0) / (np.linalg.norm(v) * np.linalg.norm(psi0)))

    return tuple(sorted(ALIGN_CANDIDATES, key=cos, reverse=True)[:4])


ALIGNS = _aligned_spans()
OFF_AXIS = ("truth", "verdict", "unit")


def test_one_admit_adds_exactly_one_unit():
    """Defect 2. One span in, one unit out."""
    a = Admitter()
    a.admit("form")
    assert len(a.index) == 1, f"index grew by {len(a.index)} for one admit"


def test_no_duplicate_spans_in_the_index():
    a = Admitter()
    for s in ("form", "gate", "core"):
        a.admit(s)
    spans = [u.span for u in a.index]
    assert len(spans) == len(set(spans)), f"duplicated spans: {spans}"


def test_allowed_spans_are_actually_committed():
    """Defect 1. If this passes with 0 admitted, the gate is a wall."""
    a = Admitter()
    admitted = 0
    for s in ALIGNS:
        unit, verdict = a.admit(s)
        if unit is not None:
            admitted += 1
            assert verdict is not None and verdict.allow is True
    assert admitted > 0, "every aligned span was refused — the gate is a wall"


def test_off_axis_spans_are_refused_and_recorded():
    a = Admitter()
    for s in OFF_AXIS:
        assert a.admit(s)[0] is None, f"{s!r} should not have been admitted"
    assert len(a.refuse_log()) == len(OFF_AXIS)


def test_refusal_log_names_the_stage():
    """A refusal must say WHICH gate refused it, or it cannot be debugged."""
    a = Admitter()
    a.admit("truth")
    stages = {stage for _, stage, _ in a.refuse_log()}
    assert stages <= {"pre_gate", "propose", "ingest", "ingest_error"}
    assert stages, "a refusal with no recorded stage is invisible"


def test_empty_span_never_reaches_a_gate():
    a = Admitter()
    unit, verdict = a.admit("   ")
    assert unit is None and verdict is None
    assert a.refuse_log()[0][1] == "pre_gate"


def test_embedding_is_reproducible_across_processes():
    """Defect 3, pinned. Two fresh interpreters must agree exactly.

    This is the property whose absence made defects 1 and 2 look like
    working code. Under Python's randomized builtin hash these two runs
    disagreed on which axis the span landed on.
    """
    code = (
        "import sys; sys.path.insert(0, r'%s');"
        "from constitutional.lexicon.ingest import embed_bag;"
        "print([round(float(x), 9) for x in embed_bag('the ground self')])"
    ) % (ROOT / "src")
    runs = [
        subprocess.run([sys.executable, "-c", code], capture_output=True,
                       text=True, timeout=120).stdout.strip()
        for _ in range(2)
    ]
    assert runs[0] == runs[1] and runs[0], f"embedder is unstable: {runs}"


def test_same_span_embeds_to_a_nonzero_vector():
    """Guards the degenerate case: a zero vector would pass every norm test."""
    v = np.asarray(embed_bag("form"), dtype=float)
    assert v.shape == (16,)
    assert float(np.linalg.norm(v)) > 0.0