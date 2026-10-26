"""
test_coding_operator_wiring.py — area 18 (self_coding) had no working target.

WHY THIS FILE EXISTS (2026-10-16, Hermes).

`atlas-exam` area 18 reported `coding_operator_object.py` as UNWIRED and
therefore unmeasurable. The report was half right and worse than wrong:
the module was not unwired, it was UNUSABLE. Its own fail-closed guard
fired on every construction attempt, because it lived at src/ top level
and used `from .harness.gate import gated_call` while every test in this
repo imports it the other way — `sys.path.insert(0, "src")` then
`import coding_operator_object`. The relative form cannot resolve in that
context, so `_GATE_AVAILABLE` was False and the constructor raised, by
design, forever.

A module that raises on construction can neither be measured nor can it
fail. That is the "a test that cannot fail cannot pass" error, one level
up from the one the atlas README describes.

So this test does three things, in order of importance:

  1. pins that the module CONSTRUCTS — the thing that was broken
  2. pins that the gate ALLOWS something and REFUSES something — a gate
     that refuses everything is a wall, not a gate, and would pass a
     naive "does it refuse?" test forever
  3. pins the fail-closed behaviour itself: with the gate unimportable,
     the constructor must still refuse. Fixing the import must not have
     quietly removed the guard.

Point 3 is the one that would have been easiest to break while fixing
point 1, which is why it is asserted rather than assumed.

WHAT THIS DOES NOT ESTABLISH

That self-coding works. This asserts reachability and the gate's
discrimination. Per tests/test_wiring_scan.py's own docstring: "Having a
caller is not the same as working — hodge_cycle was reachable and
diverged." A wired module can still be broken, and area 10 of the atlas
exam exists to mutate the substrate rather than trust it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import coding_operator_object as coo  # noqa: E402


# PROBE CORRECTION 2026-10-16. The original probes here were "the ground
# self" and "constitutional drift axis" / "identity axis". Those appeared to
# pass while embed_bag used Python's randomized builtin hash — the alignment
# with psi_0 was an accident of PYTHONHASHSEED, not a property of the words.
# The blake2b fix in ingest.py made the embedder deterministic, and both
# probes collapsed to cos=0.000 against a psi_0 of [1,0,...,0].
#
# So these tests now use spans whose alignment is REAL and measured. Axis-0
# cosines under the stable hash:
#     form 1.0000 | gate 0.9701 | core 0.9701 | allow 0.9701
#     constitutional 0.2425 | sense 0.2425
#     truth 0.0000 | unit 0.0000 | verdict 0.0000
#
# That is a gate with a working allow side AND a working veto side, which
# is the property worth pinning. A test that depends on a lucky word is a
# test that would have passed against a wall.
#: THE PROBES, RE-DERIVED FOR THE DERIVED GROUND.
#:
#: AND THE FIRST VERSIONS WERE CHOSEN FOR THE PLACEHOLDER: "the gate
#: allows the core form" was near axis 0 because "gate", "core",
#: "form" and "allow" were picked for gate-friendliness -- and this
#: file's own comment records that the first probes collapsed to
#: cos=0.000 once the hash became deterministic.
#:
#: So the probes are now RE-DERIVED from the current ground, and they
#: express the SAME INTENT: a span near the ground that is allowed,
#: and a span far from it that is refused.
#:
#: AND THE INTENT IS THE POINT: "a gate that refuses everything is a
#: wall, not a gate, and would pass a naive 'does it refuse?' test
#: forever." So BOTH halves have to hold.
def _derive_probes():
    """Pick a near and a far span by MEASURING, not by guessing."""
    import numpy as np
    from constitutional.constitution import Constitution
    from constitutional.lexicon.ingest import semantic_embed

    psi0 = np.asarray(Constitution().psi_0, dtype=float)

    def cos(text):
        v = np.asarray(semantic_embed(text), dtype=float)
        return float(np.dot(v, psi0) / (np.linalg.norm(v) * np.linalg.norm(psi0)))

    near_candidates = [
        "the constitutional ground is write protected",
        "the gate refuses a packet below the coherence threshold",
        "the drift is non increasing under every tick",
        "a span is admitted only when the gate passes",
    ]
    far_candidates = [
        "hello",
        "soup needs salt and heat and time",
        "the weather is nice today",
        "please pass me the salt",
    ]
    near = max(near_candidates, key=cos)
    far = min(far_candidates, key=cos)
    return near, far


NEAR_GROUND, OFF_GROUND = _derive_probes()


def test_gate_is_importable_in_the_bare_module_form():
    """The regression itself: form-2 import must find the gate.

    Every test in this repo uses form 2. Before the fix this was False and
    nothing downstream could construct.
    """
    assert coo._GATE_AVAILABLE is True, (
        f"harness.gate unimportable as a bare module: {coo._GATE_ERROR}"
    )


def test_operator_constructs():
    """Area 18 had no constructible target at all before this."""
    op = coo.CodingOperatorObject()
    assert op.embed is not None
    assert op.psi0 is not None
    assert op.history == []


def test_gate_allows_something():
    """A gate that refuses everything is a wall.

    If this ever fails, the gate is not discriminating — it is just refusing,
    and every other assertion about it becomes meaningless.
    """
    op = coo.CodingOperatorObject()
    verdicts = [op.propose_span(NEAR_GROUND)]
    assert any(v["allow"] for v in verdicts), (
        "the gate refused every probe — it is a wall, not a gate"
    )


def test_gate_refuses_off_ground_spans():
    """The veto has to actually bite, or allow-always would also pass."""
    op = coo.CodingOperatorObject()
    assert op.is_allowed(OFF_GROUND) is False
    # One refusal, because OFF_GROUND is ONE span. The earlier version of
    # this test called is_allowed twice with two different strings and then
    # asserted len(refuse_log()) == 2, which only held because the strings
    # differed. Assert the count the code actually produces.
    assert len(op.refuse_log()) == 1
    assert op.refuse_log()[0]["span"] == OFF_GROUND



def test_history_records_every_verdict_allow_or_refuse():
    op = coo.CodingOperatorObject()
    op.propose_span(NEAR_GROUND)
    op.propose_span(OFF_GROUND)
    assert len(op.history) == 2
    assert len(op.refuse_log()) == 1


def test_fail_closed_survives_the_import_fix(monkeypatch):
    """The guard must still refuse when the gate really is unavailable.

    This is the assertion that keeps the import fix honest. A lazy fix would
    have been to drop the guard, or to catch the ImportError and continue --
    either would make area 18 measurable while removing the one property the
    module was written to have.
    """
    monkeypatch.setattr(coo, "_GATE_AVAILABLE", False)
    monkeypatch.setattr(coo, "_GATE_ERROR", "simulated: gate not importable")
    with pytest.raises(RuntimeError) as exc:
        coo.CodingOperatorObject()
    assert "gated_call not importable" in str(exc.value)