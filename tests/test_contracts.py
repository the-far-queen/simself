"""Tests for the skill contracts.

Queue item 4. The point of a contract is that a caller can rely on it, and
the only part of that which is worth anything is the CHECK. These tests
guard that the checks can fail, that the status vocabulary is honest, and
that a contract without a check reports itself as unverifiable rather than
passing.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from research.contracts import (  # noqa: E402
    CONTRACTS, CheckResult, Contract, Status, by_name, usable_now, verify_all,
)


# --------------------------------------------------------------------- shape


def test_every_contract_states_what_it_provides():
    for c in CONTRACTS:
        assert c.name
        assert c.provides, f"{c.name} provides nothing"
        assert c.cost, f"{c.name} has no stated cost"


def test_every_contract_has_a_check():
    for c in CONTRACTS:
        assert c._check is not None, f"{c.name} has no check"


def test_names_are_unique():
    names = [c.name for c in CONTRACTS]
    assert len(names) == len(set(names))


def test_by_name_finds_and_misses_correctly():
    assert by_name(CONTRACTS[0].name) is CONTRACTS[0]
    assert by_name("no-such-capability") is None


# --------------------------------------------------------------------- honesty


def test_a_contract_with_no_check_is_unverifiable_not_passed():
    """The failure mode this whole file exists to prevent: a check that
    cannot run reporting as a pass.
    """
    c = Contract(name="empty", provides="nothing at all")
    r = c.check()
    assert r.ok is False
    assert r.status is Status.UNVERIFIABLE
    assert "no check defined" in r.measured


def test_a_check_that_returns_nothing_is_not_available():
    """A check returning the wrong shape is caught, not propagated.

    The first version of check() called the check directly, so a broken
    one took the whole report down. It now reports UNVERIFIABLE, which is
    the difference between "I could not check this" and "the report is
    gone".
    """
    c = Contract(name="broken", provides="x", _check=lambda: None)
    r = c.check()
    assert r.ok is False
    assert r.status is Status.UNVERIFIABLE
    assert "not CheckResult" in r.measured


def test_a_check_that_raises_is_caught():
    def explodes():
        raise RuntimeError("probe failed")
    c = Contract(name="raiser", provides="x", _check=explodes)
    r = c.check()
    assert r.ok is False
    assert r.status is Status.UNVERIFIABLE
    assert "RuntimeError" in r.measured
    assert "probe failed" in r.reason


def test_status_vocabulary_is_complete():
    assert {s.value for s in Status} == {
        "available", "partial", "absent", "unverifiable"}


# --------------------------------------------------------------------- the report


def test_verify_all_counts_add_up():
    rep = verify_all()
    assert rep["total"] == len(CONTRACTS)
    assert (rep["available"] + rep["partial"] + rep["absent"]
            + rep["unverifiable"]) == rep["total"]


def test_verify_all_reports_a_measured_value_for_every_row():
    """A boolean without a number is a tick box, not a measurement.
    """
    for row in verify_all()["rows"]:
        assert row["measured"], f"{row['name']} reported no measured value"
        assert row["status"] in {s.value for s in Status}


def test_satisfied_fraction_matches_the_counts():
    rep = verify_all()
    assert rep["satisfied"] == pytest.approx(rep["available"] / rep["total"])


def test_verify_all_can_report_a_failure():
    """Guard against a checker that always says yes. At least one contract
    must be checkable-absent on any given machine, or this suite is
    measuring nothing.
    """
    rep = verify_all()
    assert rep["absent"] + rep["partial"] > 0, rep["rows"]


def test_usable_now_is_a_subset_of_available():
    rep = {r["name"]: r["status"] for r in verify_all()["rows"]}
    for name in usable_now():
        assert rep[name] == "available"


def test_report_is_stable_across_calls():
    """Two consecutive checks on an idle machine must agree. A check that
    flickers is a check with a race in it.
    """
    a = {r["name"]: r["status"] for r in verify_all()["rows"]}
    b = {r["name"]: r["status"] for r in verify_all()["rows"]}
    assert a == b


# --------------------------------------------------------------------- terms


def test_terms_render_includes_the_refusals():
    c = next(c for c in CONTRACTS if c.refuses)
    text = c.terms()
    assert c.name in text
    assert "provides:" in text
    assert "refuses:" in text


def test_python_baseline_contract_is_actually_checked():
    """The one contract this suite is certain about: the interpreter
    running the tests. If it ever reports PARTIAL the suite is running on
    something the project does not target.
    """
    c = by_name("python-baseline")
    assert c is not None
    r = c.check()
    assert r.status is Status.AVAILABLE
    assert r.measured.count(".") == 2


def test_deterministic_kernel_is_available_here():
    """numpy is what the test suite itself is running on, so this contract
    cannot be anything else. It also proves the report is not hard-coded.
    """
    r = by_name("deterministic-kernel").check()
    assert r.status is Status.AVAILABLE
    assert "numpy" in r.measured


def test_a_failing_check_reports_a_reason():
    """Every non-available row must say why, so the caller knows whether it
    can fix it.
    """
    for row in verify_all()["rows"]:
        if row["status"] in ("absent", "partial", "unverifiable"):
            assert row["reason"], f"{row['name']} is {row['status']} with no reason"


# --------------------------------------------------------------------- synthetic


def test_a_passing_synthetic_contract():
    c = Contract(name="ok-one", provides="a thing",
                 _check=lambda: CheckResult(True, Status.AVAILABLE, "measured 1.0"))
    r = c.check()
    assert r.ok and r.status is Status.AVAILABLE
    assert r.measured == "measured 1.0"


def test_a_failing_synthetic_contract():
    c = Contract(name="bad-one", provides="a thing",
                 _check=lambda: CheckResult(False, Status.ABSENT, "0", "not here"))
    r = c.check()
    assert not r.ok and r.status is Status.ABSENT
    assert r.reason == "not here"


def test_contract_requirements_are_listed():
    c = Contract(name="needs-things", provides="x", requires=["a", "b"])
    assert c.requires == ["a", "b"]
    assert "requires: a, b" in c.terms()