"""
test_plan_state.py -- the SUBSTRATE's own checks on the plan state
machine, and on the planner that produces plans.

WHY THIS FILE EXISTS
--------------------
MEASURED 2026-11-05: the atlas exam's area 22 asks whether a plan is
STATE, and its probe defined the `Plan` and `Step` classes INSIDE the
probe string. So the area graded the EXAM'S OWN CODE, and the
substrate's plan behaviour was never what it measured. The area was
named as the weakest of the eight for exactly that reason.

The state machine now lives HERE, at `simself/src/plan_state.py`, and
the substrate's own planner produces plans with it. So this file is
the substrate's own check on its own capability -- not a check the
exam happens to make.

AND A CHECK THAT CANNOT FAIL IS NOT A CHECK. The last test in this
file mutates the module's SOURCE in a scratch copy and asserts the
suite goes red. MEASURED 2026-11-05: the mutation harness for the
atlas areas once reported "0 of 8 mutations went RED" for eight
mutations that never applied -- which reads as a result and is the
opposite of one.

THE PROPERTIES, and what each one is for
----------------------------------------
    P1  the steps are ORDERED, and the order is the decomposition's
    P2  the dependencies are NAMED, and they resolve to real steps
    P3  a failed step leaves its dependents SKIPPED -- not run, not
        silently passed
    P4  the plan can be ABANDONED, with the reason on the record
    P5  a plan that can never be run is REFUSED at construction

Run: python -m pytest tests/test_plan_state.py -q
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pytest  # noqa: E402

from plan_state import Plan, PlanStatus, Step, StepStatus  # noqa: E402


# ---------------------------------------------------------------------------
# the state machine
# ---------------------------------------------------------------------------

def _chain(n: int = 3):
    """a plan of n steps, each needing the one before it."""
    return Plan([Step("s%d" % i, tuple("s%d" % j for j in range(i)),
                        "the %d-th thing" % i)
                 for i in range(n)])


def test_a_plan_keeps_its_steps_in_the_declared_order():
    plan = _chain(4)
    assert plan.names() == ["s0", "s1", "s2", "s3"]


def test_the_steps_name_what_they_need():
    plan = _chain(3)
    assert plan.step_named("s2").needs == ("s0", "s1")
    assert plan.step_named("s0").needs == ()


def test_a_failing_step_leaves_its_dependents_skipped_not_passed():
    plan = _chain(3)

    def runner(step):
        if step.name == "s0":
            raise RuntimeError("s0 failed on purpose")

    plan.run(runner)
    d = plan.to_dict()
    assert d["steps"][0]["status"] == StepStatus.FAILED.value
    assert d["steps"][1]["status"] == StepStatus.SKIPPED.value
    assert d["steps"][2]["status"] == StepStatus.SKIPPED.value
    assert d["status"] == PlanStatus.FAILED.value


def test_the_skip_names_the_unmet_dependency():
    plan = _chain(3)

    def runner(step):
        if step.name == "s0":
            raise RuntimeError("s0 failed on purpose")

    plan.run(runner)
    skipped = plan.step_named("s1")
    assert "s0" in skipped.error


def test_a_step_that_does_not_depend_on_the_failure_still_runs():
    """A failure is LOCAL. A step with no unmet dependency still runs."""
    plan = Plan([Step("a", (), "a"), Step("b", (), "b"),
                  Step("c", ("a",), "c")])

    def runner(step):
        if step.name == "a":
            raise RuntimeError("a failed on purpose")

    plan.run(runner)
    assert plan.step_named("b").status is StepStatus.DONE
    assert plan.step_named("c").status is StepStatus.SKIPPED


def test_a_plan_that_runs_to_completion_says_so():
    plan = _chain(3)
    plan.run(lambda step: None)
    d = plan.to_dict()
    assert d["status"] == PlanStatus.COMPLETED.value
    assert all(s["status"] == StepStatus.DONE.value for s in d["steps"])


def test_a_plan_can_be_abandoned_and_the_reason_is_on_the_record():
    plan = _chain(3)
    plan.abandon("the caller changed its mind")
    d = plan.to_dict()
    assert d["status"] == PlanStatus.ABANDONED.value
    assert d["abandon_reason"] == "the caller changed its mind"
    assert all(s["status"] != StepStatus.PENDING.value
               for s in d["steps"])


def test_an_abandonment_with_no_reason_is_refused():
    """An abandonment nobody can explain is indistinguishable from a
    failure, so the reason is required."""
    with pytest.raises(ValueError):
        _chain(2).abandon("   ")


def test_a_plan_that_can_never_be_run_is_refused_at_construction():
    """A cycle can never be run, and it is refused BEFORE any work."""
    with pytest.raises(ValueError):
        Plan([Step("a", ("b",), "a"), Step("b", ("a",), "b")])


def test_a_dependency_on_a_step_that_does_not_exist_is_refused():
    with pytest.raises(ValueError):
        Plan([Step("a", ("nope",), "a")])


def test_two_steps_with_one_name_are_refused():
    with pytest.raises(ValueError):
        Plan([Step("a"), Step("a")])


def test_a_plan_cannot_be_run_twice():
    plan = _chain(2)
    plan.run(lambda step: None)
    with pytest.raises(RuntimeError):
        plan.run(lambda step: None)


# ---------------------------------------------------------------------------
# the planner that produces the plans
# ---------------------------------------------------------------------------

def test_the_planner_produces_a_plan_with_named_dependencies():
    from executive_planner import SeniorEngineerPlanner

    plan = SeniorEngineerPlanner().plan_for(
        "Build a thing that reads files and writes a report")
    assert len(plan.steps) >= 2
    assert sum(len(s.needs) for s in plan.steps) >= 1


def test_the_planners_plan_order_is_the_decompositions_order():
    from executive_planner import SeniorEngineerPlanner

    planner = SeniorEngineerPlanner()
    d = planner.decompose("Build a thing that reads files and writes a report")
    plan = planner.plan_for(
        "Build a thing that reads files and writes a report")
    assert plan.names() == list(d.components)


def test_the_planner_produces_the_same_plan_twice():
    from executive_planner import SeniorEngineerPlanner

    planner = SeniorEngineerPlanner()
    req = "Build a thing that reads files and writes a report"
    a = planner.plan_for(req)
    b = planner.plan_for(req)
    assert a.names() == b.names()
    assert [s.needs for s in a.steps] == [s.needs for s in b.steps]


def test_a_failure_in_the_planners_plan_skips_the_layers_above_it():
    """The decomposition's milestones are the layers, so a failure in the
    Foundation SKIPS the Core and Polish steps above it."""
    from executive_planner import SeniorEngineerPlanner

    plan = SeniorEngineerPlanner().plan_for(
        "Build a thing that reads files and writes a report")
    foundation = [s for s in plan.steps if not s.needs]
    assert foundation, "the first layer must have no dependencies"

    def runner(step):
        if step.name == foundation[0].name:
            raise RuntimeError("the foundation failed on purpose")

    plan.run(runner)
    skipped = [s for s in plan.steps if s.status is StepStatus.SKIPPED]
    assert skipped, "the failure must propagate to the layers above it"
    assert all(s.status is not StepStatus.DONE
               for s in plan.steps
               if foundation[0].name in s.needs)


# ---------------------------------------------------------------------------
# THE MUTATION -- the check must be able to go RED
# ---------------------------------------------------------------------------

#: The mutation, and the file it applies to. The pattern is READ OUT of
#: the live source, not guessed: a guessed pattern is a mutation that
#: does not apply, which proves nothing.
MUTATION_FILE = "src/plan_state.py"
MUTATION_OLD = "                step.status = StepStatus.SKIPPED\n"
MUTATION_NEW = "                step.status = StepStatus.DONE\n"


def test_the_suite_goes_red_when_the_skip_is_turned_into_a_pass():
    """A check that has never been seen to fail has not been shown to
    work.

    So the module's SOURCE is mutated in a scratch copy -- the live file
    is never touched -- and the checks are run against the copy. The
    copy must go RED, or these checks are not checking anything.

    AND THE COPY IS RESTORED IN A FINALLY BLOCK, so a mutation that
    breaks the harness itself cannot leave a corrupt module behind.
    """
    src = _REPO / MUTATION_FILE
    original = src.read_text(encoding="utf-8")
    assert MUTATION_OLD in original, (
        "the mutation pattern is no longer in %s -- the code has drifted "
        "and the mutation must be rewritten" % MUTATION_FILE)

    tmp = Path(tempfile.mkdtemp(prefix="plan_state_mut_"))
    try:
        # A scratch tree holding the MUTATED module, laid out exactly
        # like the repo (src/ and tests/), so the checks can be run
        # against the COPY with no import-order games.
        #
        # AND WHY IT IS LAID OUT LIKE THE REPO. MEASURED 2026-11-05:
        # the first version put the mutated module in a flat temp dir
        # and put that dir on PYTHONPATH. The mutation then had NO
        # effect -- the suite passed -- because the test file does
        # `sys.path.insert(0, src)` at import time and pytest's own
        # `pythonpath = src` setting put the LIVE src first. The live
        # module won, so the harness measured nothing and the
        # "the mutation did not apply" case was INVISIBLE: it looked
        # exactly like a check that cannot fail.
        #
        # So the copy is run from a scratch ROOT, where the scratch
        # src/ is the only src/ there is, and the live tree is not on
        # the path at all.
        (tmp / "src").mkdir()
        (tmp / "tests").mkdir()
        (tmp / "src" / "plan_state.py").write_text(
            original.replace(MUTATION_OLD, MUTATION_NEW, 1),
            encoding="utf-8")
        assert (tmp / "src" / "plan_state.py").read_text(encoding="utf-8") != original, \
            "the mutation wrote nothing"
        # the planner is needed too -- it imports the plan state
        shutil.copy2(_SRC / "executive_planner.py", tmp / "src" / "executive_planner.py")
        # and the checks themselves, so they import the scratch src
        shutil.copy2(_HERE / "test_plan_state.py",
                     tmp / "tests" / "test_plan_state.py")

        env = dict(os.environ)
        # the scratch src FIRST, and the live src NOT on the path at
        # all, so the live module cannot win.
        env["PYTHONPATH"] = str(tmp / "src")

        proc = subprocess.run(
            [sys.executable, "-m", "pytest",
             str(tmp / "tests" / "test_plan_state.py"), "-q", "--no-header",
             "-p", "no:cacheprovider",
             # THE MUTATION TEST ITSELF IS EXCLUDED. It spawns a
             # pytest, and a pytest that runs this file would spawn
             # another one, and so on. MEASURED 2026-11-05: the first
             # version of this file hung on the recursion, and the
             # symptom looked like a slow test rather than an infinite
             # one. The other checks are what must go red.
             "-k", "not goes_red"],
            cwd=str(tmp), capture_output=True, text=True, env=env,
            timeout=300)
        assert proc.returncode != 0, (
            "the mutated module did NOT make the suite red -- these "
            "checks do not actually check the skip-on-failure rule:\n"
            + (proc.stdout or "")[-2000:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # and the LIVE module is untouched
    assert src.read_text(encoding="utf-8") == original
