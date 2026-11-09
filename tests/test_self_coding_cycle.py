"""
test_self_coding_cycle.py -- THE FOUR SHAPES ARE WIRED, AND THE WIRING
IS PINNED.

**AND THIS FILE EXISTS BECAUSE OF THE PROJECT'S OWN REPEATED LESSON.**
MEASURED, repeatedly: "an instrument that is built and never run is a
piece of documentation". `autocode/self_coding_cycle.py` carries the
sandbox, the comparison, the rollback and the stop rule -- and if
nothing reaches it, it is a document.

**SO THIS FILE PINS THE ROUTE, not just the behaviour.** Three things:

  1. the CYCLE MODULE is reachable from the surface the atlas exam's
     area 18 measures -- `coding_operator_object.py` -- because area 18
     says "self-coding must run in a sandbox, compare against the
     current version, and roll back on invariant violation", and a
     requirement nothing reaches cannot be established;
  2. the ROUTE WORKS in BOTH import forms, because this module is
     consumed two ways and the relative import fails in one of them
     (the same defect the gate import in that file documents);
  3. and the route LANDS NOTHING when the variant does not hold -- so
     the wiring is not a decoration that runs the machinery and
     ignores the verdict.

AND THE FOUR SHAPES THEMSELVES ARE CHECKED by
`tools/check_self_coding_cycle.py`, and proved able to go red by
`tools/mutation_check_self_coding_cycle.py`. This file is the WIRING
check; those two are the BEHAVIOUR checks.

Run:
    cd simself && python -m pytest tests/test_self_coding_cycle.py -q
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import coding_operator_object as coo  # noqa: E402


def _git(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", repo] + list(args),
                          capture_output=True, text=True, timeout=120)


def _fixture_repo(root: str, name: str = "tree") -> str:
    """A real git repository with a real marker file."""
    dest = os.path.join(root, name)
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "marker.txt"), "w", encoding="utf-8") as fh:
        fh.write("2\n")
    _git(dest, "init", "-q")
    _git(dest, "config", "user.email", "wiring@fixture.invalid")
    _git(dest, "config", "user.name", "the wiring fixture")
    _git(dest, "config", "commit.gpgsign", "false")
    _git(dest, "add", "-A")
    _git(dest, "commit", "-q", "-m", "the fixture's first commit")
    return dest


def _diff(value: str) -> str:
    return ("diff --git a/marker.txt b/marker.txt\n"
            "--- a/marker.txt\n"
            "+++ b/marker.txt\n"
            "@@ -1 +1 @@\n"
            "-2\n"
            "+%s\n" % value)


# ---------------------------------------------------------------------------
# 1. THE ROUTE EXISTS
# ---------------------------------------------------------------------------

def test_the_cycle_is_reachable_from_the_operator_surface():
    """The surface area 18 measures can reach the cycle.

    AND AREA 18 SAYS: "self-coding must run in a sandbox, compare
    against the current version, and roll back on invariant violation".
    A requirement nothing reaches cannot be established, and the
    project's own census has found 25 modules like that.
    """
    assert hasattr(coo.CodingOperatorObject, "propose_change"), (
        "the operator surface has no route into the self-coding cycle, "
        "so the sandbox, the comparison and the rollback are "
        "unreachable from the surface the exam measures")


def test_the_cycle_resolves_in_the_bare_module_form():
    """The bare-module form resolves the cycle.

    AND THIS IS THE FORM EVERY TEST IN THIS REPO USES: `sys.path
    .insert(0, "src")` then `import coding_operator_object`. And the
    cycle lives one level DOWN in `src/autocode/`, so the bare form's
    path is `autocode.self_coding_cycle` and the relative form
    `.autocode.self_coding_cycle` cannot resolve. MEASURED: the first
    version of the route used the relative form only and raised
    ImportError on every call.
    """
    goal_contract, run_cycle = coo._resolve_cycle()
    assert goal_contract.__name__ == "GoalContract"
    assert callable(run_cycle)


def test_the_package_member_form_also_resolves():
    """The package-member form resolves the cycle too.

    AND THE TWO FORMS ARE DIFFERENT CODE PATHS, so one of them
    working proves nothing about the other.
    """
    probe = ("import sys; sys.path.insert(0, %r);"
             "from src.coding_operator_object import _resolve_cycle;"
             "print(_resolve_cycle()[0].__name__)" % str(ROOT))
    proc = subprocess.run([sys.executable, "-c", probe],
                          capture_output=True, text=True, cwd=str(ROOT),
                          timeout=120)
    assert proc.returncode == 0, proc.stderr
    assert "GoalContract" in proc.stdout


# ---------------------------------------------------------------------------
# 2. THE ROUTE WORKS, AND IT LANDS NOTHING WHEN THE VARIANT DOES NOT HOLD
# ---------------------------------------------------------------------------

def test_the_route_lands_a_variant_that_holds():
    """A variant that holds is landed by the operator's route."""
    tmp = tempfile.mkdtemp(prefix="wire_ok_")
    try:
        repo = _fixture_repo(tmp, "ok")
        operator = coo.CodingOperatorObject()
        tasks = ()
        out = operator.propose_change(_diff("3"), repo, tasks=tasks,
                                      max_rounds=1)
        assert out["adopted"] is True, out
        with open(os.path.join(repo, "marker.txt"), encoding="utf-8") as fh:
            assert fh.read().strip() == "3"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_the_route_lands_nothing_when_the_variant_does_not_hold():
    """A variant that does NOT hold changes nothing.

    AND THIS IS THE POINT OF THE ROUTE. A wiring that runs the
    machinery and ignores the verdict is a decoration, and a
    decoration that commits is worse than no wiring at all.
    """
    tmp = tempfile.mkdtemp(prefix="wire_no_")
    try:
        repo = _fixture_repo(tmp, "no")
        before = _git(repo, "rev-parse", "HEAD").stdout.strip()
        operator = coo.CodingOperatorObject()
        # A diff that does not apply at all: the context is wrong.
        bad = ("diff --git a/marker.txt b/marker.txt\n"
               "--- a/marker.txt\n"
               "+++ b/marker.txt\n"
               "@@ -1 +1 @@\n"
               "-99\n"
               "+7\n")
        out = operator.propose_change(bad, repo, tasks=(), max_rounds=1)
        assert out["adopted"] is False, out
        after = _git(repo, "rev-parse", "HEAD").stdout.strip()
        assert after == before, "the head moved: %s -> %s" % (before, after)
        with open(os.path.join(repo, "marker.txt"), encoding="utf-8") as fh:
            assert fh.read().strip() == "2"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_the_route_names_its_stop_reason():
    """The route reports a NAMED stop reason.

    AND A STOP REASON THAT SAYS NOTHING CANNOT BE ACTED ON, and the
    loop's own rule is that every refusal names its reason.
    """
    tmp = tempfile.mkdtemp(prefix="wire_reason_")
    try:
        repo = _fixture_repo(tmp, "reason")
        operator = coo.CodingOperatorObject()
        out = operator.propose_change(_diff("3"), repo, tasks=(),
                                      max_rounds=1)
        assert out["stop_reason"], "the route reported no stop reason"
        assert out["stop_reason"] in ("adopted", "round_cap",
                                      "no_candidate", "diff_does_not_apply",
                                      "reservation_failed", "stale_round",
                                      "rolled_back", "goal_not_a_contract")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_the_route_refuses_a_goal_that_is_not_a_contract():
    """A goal with no measurable stop rule is REFUSED by the route.

    AND THE FC'S OWN WORKED EXAMPLE: "Keep improving the code"
    describes effort and never ends, so it is not a completion
    contract and the route must not start.
    """
    tmp = tempfile.mkdtemp(prefix="wire_goal_")
    try:
        repo = _fixture_repo(tmp, "goal")
        operator = coo.CodingOperatorObject()
        goal_contract, _ = coo._resolve_cycle()
        effort = goal_contract(
            end_state="better code",
            proof="the tests",
            boundaries=("the ground does not move",),
            loop="one round per candidate",
            stop_rule="keep improving the code",
        )
        out = operator.propose_change(_diff("3"), repo, goal=effort,
                                      tasks=(), max_rounds=1)
        assert out["adopted"] is False, out
        assert out["stop_reason"] == "goal_not_a_contract", out
        assert any("stop rule" in r for r in out["refusals"]), out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
