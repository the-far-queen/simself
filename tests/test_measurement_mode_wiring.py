"""
test_measurement_mode_wiring.py -- THE EVIDENCE LAYER, AT THE REAL
CALL SITES.

THE DEFECT THIS FILE EXISTS TO CATCH, and it was MEASURED, not
suspected.

    The evidence layer in fieldcore/src/claim_register.py fires ONLY
    when `read()` is called with as_measurement=True.

    MEASURED 2026-10-31:
      - simself's `claim_gate()` called `reg.read(text)` with no mode,
        so the mode was always prose and the evidence layer NEVER RAN
        in production
      - fieldcore's `fc_gate.py` claim layer called
        `self.register.read(span)` with no mode, for the same reason

    A layer that never fires and a layer that fires correctly produce
    the same output on a corpus of prose. So the layer was invisible.

THE TWO WIRINGS, and each is the CALLER'S to make, because the caller
knows which path the span arrived on:

    a MEASUREMENT path -- the ingest path, a readout, a bench output --
        is checked with as_measurement=True

    a PROSE path -- a document, a note, a sentence -- is checked with
        as_measurement=False

THE COUNTERWEIGHT, and it is the half that makes this a gate rather
than a wall: the ground's own prose must NOT be refused. A gate that
refuses the truth is worse than no gate, and it would have looked
healthy.

Run:
    python -m pytest tests/test_measurement_mode_wiring.py -q
"""

from __future__ import annotations

import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
FC_SRC = ROOT.parent / "fieldcore" / "src"

for _p in (str(SRC), str(FC_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import claim_register as CR  # noqa: E402


#: A claim that IS measured in the standard register.
MEASURED_TRUTH = ("the gate limits are module constants that no caller "
                   "can supply")

#: The same claim dressed up as a report of a run, carrying nothing.
REPORT_WITHOUT_MEASUREMENT = (
    "the gate limits are module constants that no caller can supply; "
    "the suite reports 12 passed")

#: The same claim carrying the command and the number.
REPORT_WITH_MEASUREMENT = (
    "the gate limits are module constants that no caller can supply; "
    "python -m pytest tests/test_gate_contract.py -q -> 12 passed")


# ---------------------------------------------------------------------------
# THE REGISTER'S OWN CONTRACT
# ---------------------------------------------------------------------------

def test_the_evidence_layer_fires_in_measurement_mode():
    """The layer's contract, stated directly."""
    reg = CR.standard_register()
    prose = reg.read(REPORT_WITHOUT_MEASUREMENT, as_measurement=False)
    measured = reg.read(REPORT_WITHOUT_MEASUREMENT, as_measurement=True)
    assert prose.verdict is CR.Verdict.CONSISTENT, prose.reason
    assert measured.verdict is CR.Verdict.UNGROUNDED, measured.reason


def test_the_evidence_layer_admits_a_report_that_carries_its_measurement():
    """The other half. A layer that refuses everything is a wall."""
    reg = CR.standard_register()
    adj = reg.read(REPORT_WITH_MEASUREMENT, as_measurement=True)
    assert adj.verdict is CR.Verdict.CONSISTENT, adj.reason


# ---------------------------------------------------------------------------
# THE SIMSELF WIRING
# ---------------------------------------------------------------------------

def test_simselfs_claim_gate_takes_the_mode():
    """The simself gate must be ABLE to ask for measurement mode.

    And the default is prose: a caller that knows nothing passes
    nothing, and prose is the safe direction.
    """
    # THE MODULE, not the re-exported function. The package's
    # __init__ does `from .ingest import (..., ingest, ...)`, so the
    # name `ingest` on the package IS the function -- and
    # `from constitutional.lexicon import ingest as ing` binds that
    # function, so `ing.claim_gate` is an AttributeError. MEASURED.
    from constitutional.lexicon.ingest import claim_gate

    assert claim_gate.__doc__
    ok, why = claim_gate(MEASURED_TRUTH)
    assert ok, ("the ground's own prose was refused: %s" % why)

    ok2, why2 = claim_gate(REPORT_WITHOUT_MEASUREMENT,
                            as_measurement=True)
    assert not ok2, ("the evidence layer did not fire at the simself "
                     "call site: %s" % why2)
    assert "ungrounded" in why2


def test_simselfs_ingest_declares_itself_a_measurement_path():
    """The ingest path IS a measurement path -- a span arriving there
    came out of a run.

    So the parameter must EXIST on ingest() and must default to the
    measurement mode, because the ingest path is that path.
    """
    from constitutional.lexicon.ingest import ingest
    import inspect

    sig = inspect.signature(ingest)
    assert "as_measurement" in sig.parameters, (
        "ingest() does not carry the measurement mode: %s" % sig)
    assert sig.parameters["as_measurement"].default is True, (
        "the ingest path defaults to prose; it is a MEASUREMENT path")


def test_simselfs_claim_gate_admits_a_report_that_carries_its_measurement():
    """The counterweight at the simself call site."""
    from constitutional.lexicon.ingest import claim_gate

    ok, why = claim_gate(REPORT_WITH_MEASUREMENT,
                         as_measurement=True)
    assert ok, ("the gate refused a report that carried its measurement: "
                "%s" % why)


# ---------------------------------------------------------------------------
# THE FIELDCORE WIRING
# ---------------------------------------------------------------------------

def test_fieldcores_gate_decides_the_mode_from_the_span():
    """The fieldcore gate reads a reply, and the mode comes from the
    FORM of the span: a span carrying a command and a number, or a
    result count, is reporting a run.

    AND THE COUNTERWEIGHT: the ground's own prose stays prose.
    """
    import fc_gate

    assert fc_gate.presents_as_measurement(REPORT_WITH_MEASUREMENT)
    assert fc_gate.presents_as_measurement(
        "the suite reports 12 passed")
    assert not fc_gate.presents_as_measurement(MEASURED_TRUTH)
    assert not fc_gate.presents_as_measurement(
        "the constitutional ground is write protected -- verified, 1 check")


def test_fieldcores_gate_refuses_an_ungrounded_report():
    """The evidence layer at the fieldcore call site."""
    import fc_gate

    g = fc_gate.FieldCoreGate()
    g.warm()
    v = g.decide(REPORT_WITHOUT_MEASUREMENT)
    assert not v.allowed, (
        "the gate admitted a report that carried no measurement")
    assert v.reason


def test_fieldcores_gate_admits_the_grounds_own_claims():
    """THE COUNTERWEIGHT AT THE FIELD-CORE CALL SITE.

    MEASURED: forcing measurement mode for every span made the gate
    refuse the ground's own eight claims. A gate that refuses the
    ground's own text is a gate that refuses everything.
    """
    import fc_gate

    g = fc_gate.FieldCoreGate()
    g.warm()
    for claim in CR.STANDARD_CLAIMS:
        if not claim.statement:
            continue
        v = g.decide(claim.statement)
        assert v.allowed, ("the gate refused the ground's own claim: %r"
                           % claim.statement)
