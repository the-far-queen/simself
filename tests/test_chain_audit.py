"""
tests/test_chain_audit.py -- simself's chain audit binding.

AND THE RULE, and it is the project's own: a validator that cannot fail
is decoration. So every test here asserts something that could go RED.

AND THE SHAPE IS DIFFERENT FROM FIELDCORE'S SUITE, and the difference
is the point. fieldcore's tests prove the SIGNALS are real -- that the
inheritance measure separates a working chain from a narrated one.
simself's tests prove the BINDING is honest -- that the recorder holds
the answer out, that the spend guard is closed, that the re-runner does
not leak the answer into the prompt, and that the handoff audit fires.

A binding that quietly passed the answer to the model would make the
backward-influence signal meaningless, and nothing else would catch it.
"""

from __future__ import annotations

import os
import sys

import pytest

SS_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "src")
if SS_SRC not in sys.path:
    sys.path.insert(0, SS_SRC)

from constitutional.chain_audit import (  # noqa: E402
    ChainAuditUnavailable, ChainRecorder, MiniMaxChainRerunner,
    audit_handoff, audit_simself_chain,
)


@pytest.fixture()
def recorder() -> ChainRecorder:
    rec = ChainRecorder(question="which construction maximises the pairs")
    rec.record_step("Consider the square grid.", "the question")
    rec.record_step("The square grid gives 2n pairs.",
                    "Consider the square grid.")
    rec.record_step("The rescaled grid gives more, so test the number "
                    "field construction.", "The square grid gives 2n pairs.")
    rec.record_answer("a construction from a number field")
    return rec


# --------------------------------------------------------------------------
# the recorder
# --------------------------------------------------------------------------

def test_the_recorder_holds_the_answer_out_of_the_steps(recorder):
    """THE ANSWER MUST NOT BE A STEP. If it is, the prediction-lead
    signal is trivially satisfied and measures nothing."""
    chain = recorder.to_chain()
    assert chain.answer == "a construction from a number field"
    assert len(chain.steps) == 3
    assert all("number field" not in s.text for s in chain.steps[:-1])


def test_the_recorder_keeps_what_each_step_was_handed(recorder):
    chain = recorder.to_chain()
    assert chain.steps[1].input_text == "Consider the square grid."


def test_the_recorder_saves_atomically(recorder, tmp_path):
    path = str(tmp_path / "chain.json")
    recorder.save(path)
    assert os.path.isfile(path)
    assert not os.path.isfile(path + ".part")


# --------------------------------------------------------------------------
# the audit binding
# --------------------------------------------------------------------------

def test_the_audit_returns_a_verdict(recorder):
    report = audit_simself_chain(recorder)
    assert report["verdict"]["verdict"] in ("genuine", "theatre", "undecided")


def test_the_offline_signals_run_without_a_model(recorder):
    """AND NO MODEL CALL IS MADE. The four offline signals cost
    nothing, and the audit must not reach for the model."""
    report = audit_simself_chain(recorder)
    signals = {s["name"]: s for s in report["verdict"]["signals"]}
    assert signals["step_inheritance"]["available"] is True
    assert signals["prediction_lead"]["available"] is True
    assert report["model_calls"] == 0
    assert report["live"] is False


def test_backward_influence_is_absent_without_a_rerunner(recorder):
    report = audit_simself_chain(recorder)
    signals = {s["name"]: s for s in report["verdict"]["signals"]}
    assert signals["backward_influence"]["available"] is False


def test_the_audit_carries_the_recorder_with_it(recorder):
    report = audit_simself_chain(recorder)
    assert report["recorder"]["question"] == recorder.question
    assert len(report["recorder"]["steps"]) == 3


# --------------------------------------------------------------------------
# the re-runner -- the only part that spends
# --------------------------------------------------------------------------

def test_the_spend_guard_is_closed_by_default():
    """A WRAPPER THAT CHECKS THE GUARD AND THEN BUILDS AN UNGUARDED
    CLIENT HAS NO GUARD. So the guard lives at the only place that can
    spend, and it is closed unless asked for."""
    assert MiniMaxChainRerunner().describe()["allow_live"] is False


def test_the_rerunner_does_not_leak_the_answer_into_the_prompt(recorder):
    """THE CHECK THAT MATTERS MOST HERE.

    Showing the model the answer it is supposed to derive measures
    whether it can copy, not whether it can reason -- and a leaked
    answer would make the backward-influence signal look strong on a
    chain that has none.
    """
    seen = []

    def spy(prompt):
        seen.append(prompt)
        return "an answer"

    rr = MiniMaxChainRerunner(client=spy)
    rr(recorder.to_chain().steps)
    assert seen
    # THE ANSWER ITSELF must not be in the prompt. The chain's own
    # steps may legitimately reach the answer's substance -- that is
    # the derivation, and forbidding it would forbid the reasoning.
    # What must not appear is the held-out ANSWER, in the form the
    # recorder stored it.
    assert recorder.answer not in seen[0]
    assert "Step 1:" in seen[0]


def test_the_rerunner_counts_its_calls():
    def spy(prompt):
        return "an answer"

    rr = MiniMaxChainRerunner(client=spy)
    rr([])
    rr([])
    assert rr.describe()["calls"] == 2


def test_the_rerunner_raises_when_the_model_is_unreachable():
    """AN EMPTY ANSWER IS A FAILURE, NOT A PASS. So an unreachable
    model raises rather than returning an empty string that reads as
    a legitimate answer."""

    def broken(prompt):
        raise RuntimeError("the model refused")

    rr = MiniMaxChainRerunner(client=broken)
    with pytest.raises(ChainAuditUnavailable):
        rr([])


def test_the_rerunner_accepts_a_client_with_generate():
    """A client object and a bare callable are both valid -- the
    self-test caught that the re-runner assumed one shape."""
    class Client:
        def generate(self, prompt):
            return "from the client"

    assert MiniMaxChainRerunner(client=Client())([]) == "from the client"
    assert MiniMaxChainRerunner(client=lambda p: "from the callable")(
        []) == "from the callable"


# --------------------------------------------------------------------------
# the handoff audit
# --------------------------------------------------------------------------

def _packet(summary: str) -> dict:
    return {
        "question": "which construction maximises the pairs",
        "steps": [{"text": "Consider the square grid; it may be better, "
                           "although the rescaled grid is stronger."},
                  {"text": "The number field construction gives "
                           "n^(1+delta) pairs."}],
        "answer": "a construction from a number field",
        "summary": summary,
    }


def test_a_flattened_handoff_summary_is_caught():
    """THE DEFECT THIS CLOSES. The handoff protocol measures drift and
    stability and the psi-zero fingerprint -- it CANNOT see a
    confident claim where the work was hedged. So a flattened summary
    would pass both checks and land in the next session looking solid.
    """
    flat = ("The number field construction gives n^(1+delta) pairs. "
            "It was verified.")
    out = audit_handoff(_packet(flat))
    assert out["reads"] in ("flattened", "mixed"), out["reads"]


def test_a_faithful_handoff_summary_is_not_flattened():
    faithful = ("The number field construction gives n^(1+delta) pairs, "
                "although we are not sure the delta is optimal; the "
                "square grid option was discarded because it loses the "
                "algebraic structure.")
    out = audit_handoff(_packet(faithful))
    assert out["reads"] in ("faithful", "mixed"), out["reads"]


def test_the_handoff_audit_reports_what_it_measured():
    out = audit_handoff(_packet("something"))
    assert out["markers_used"]["hedges"]
    assert out["markers_used"]["caveats"]
    assert out["markers_used"]["branches"]


def test_the_handoff_audit_reports_the_packet_shape():
    out = audit_handoff(_packet("something"))
    assert "steps" in out["packet_keys"]
    assert "summary" in out["packet_keys"]
