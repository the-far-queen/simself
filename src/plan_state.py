"""
plan_state.py -- A PLAN IS STATE: ordered steps, named dependencies,
a represented partial failure, and a path that can be ABANDONED.

WHY THIS FILE EXISTS
--------------------
MEASURED 2026-11-05, the atlas exam's area 22. The area asks whether
a plan is STATE, and its probe defined the `Step` and `Plan` classes
INSIDE the probe string. So the area graded the EXAM's own code: the
substrate's plan behaviour was never what it measured, and the area was
named as the weakest of the eight.

That is a defect class this project keeps hitting -- a mechanism that
lives next to the thing it measures, so measuring it proves nothing.
So the state machine lives HERE, in the substrate, and the exam points
AT it. The exam supplies a scenario; the substrate supplies all of the
logic.

THE FOUR PROPERTIES, and why each one is load-bearing
------------------------------------------------------
    P1  ORDERED. The steps have a declared sequence, and the sequence
        is not an accident of a set's iteration order. The plan walks
        its steps in the order they were declared.

    P2  DEPENDENCIES ARE NAMED. A step says what it needs, and every
        name it gives must resolve to a step of the same plan. A plan
        whose steps all depend on nothing can be done in any order,
        and that is a list.

    P3  PARTIAL FAILURE IS REPRESENTED. A step that fails leaves the
        steps that depend on it SKIPPED -- not run, not silently
        passed. This is the property that separates a plan from a
        checklist. A failure that propagates nowhere is a failure in a
        list, and a list has no consequences.

    P4  THE PLAN CAN BE ABANDONED. There is a way to stop, and it
        leaves the plan in a state that says it was stopped, with the
        reason on the record. An abandonment nobody can explain is
        indistinguishable from a failure.

AND WHY P4 IS CHECKED FIRST
----------------------------
P1, P2 and P3 can all be satisfied by a structure that is only ever
run to completion. So P4 is the one that decides whether the thing is
a plan or a program.

THE FAILURE IS THE CALLER'S; THE CONSEQUENCE IS THIS MODULE'S
---------------------------------------------------------------
`Plan.run(runner)` calls the runner for each step. If the runner
raises, THAT STEP IS FAILED -- and what happens to the steps that
depend on it is decided here, not by the caller. A caller that wants a
different consequence has to say so by raising, and this module still
owns the bookkeeping.

SO THE HONEST QUESTION IS NOT "does a plan exist" BUT "what does the
plan DO when a step fails", and the answer must be observable from
outside.

Public API:
    from plan_state import Plan, Step, StepStatus, PlanStatus

    plan = Plan([Step("a", needs=()), Step("b", needs=("a",))])
    plan.run(lambda step: None)          # or raise, to fail that step
    plan.abandon("the reason")
    plan.to_dict()

Run: python src/plan_state.py --selftest
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


class StepStatus(str, Enum):
    """Where one step is. PENDING is the only state a step starts in."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanStatus(str, Enum):
    """Where the plan is.

    ABANDONED is a FIRST-CLASS outcome, not an error: a plan nobody
    can stop is a program.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


@dataclass
class Step:
    """One step of a plan, and what it needs.

    `needs` names the steps this one waits for. `produces` is what it
    hands on -- the reason the order matters.
    """

    name: str
    needs: Tuple[str, ...] = ()
    produces: str = ""
    status: StepStatus = StepStatus.PENDING
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "needs": list(self.needs),
            "produces": self.produces,
            "status": self.status.value,
            "error": self.error,
        }


class Plan:
    """An ordered set of steps that can be RUN, FAILED and ABANDONED."""

    def __init__(self, steps: Sequence[Step]) -> None:
        self.steps: List[Step] = list(steps)
        self.status: PlanStatus = PlanStatus.PENDING
        self.abandon_reason: str = ""
        self._by_name: Dict[str, Step] = {}
        for step in self.steps:
            if step.name in self._by_name:
                raise ValueError("two steps are named %r" % step.name)
            self._by_name[step.name] = step
        for step in self.steps:
            for need in step.needs:
                if need not in self._by_name:
                    raise ValueError(
                        "step %r needs %r, which is not a step of this plan"
                        % (step.name, need))
        self._check_no_cycle()

    # -- construction checks --------------------------------------------

    def _check_no_cycle(self) -> None:
        """A plan whose dependencies form a cycle can never be run.

        MEASURED 2026-11-05: this is checked at CONSTRUCTION, not at
        run time. A cycle discovered halfway through a run has already
        done half the work, and the plan's own record would then say
        some steps are DONE and others are SKIPPED for no reason a
        reader can see.
        """
        WHITE, GREY, BLACK = 0, 1, 2
        colour: Dict[str, int] = {s.name: WHITE for s in self.steps}

        def visit(name: str) -> None:
            colour[name] = GREY
            for need in self._by_name[name].needs:
                if colour[need] == GREY:
                    raise ValueError(
                        "the dependencies of this plan form a cycle at %r"
                        % need)
                if colour[need] == WHITE:
                    visit(need)
            colour[name] = BLACK

        for step in self.steps:
            if colour[step.name] == WHITE:
                visit(step.name)

    # -- reading ---------------------------------------------------------

    def step_named(self, name: str) -> Step:
        return self._by_name[name]

    def names(self) -> List[str]:
        """The step names, in DECLARED order."""
        return [s.name for s in self.steps]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "abandon_reason": self.abandon_reason,
            "steps": [s.to_dict() for s in self.steps],
        }

    # -- running ---------------------------------------------------------

    def run(self, runner: Callable[[Step], Any]) -> "Plan":
        """Run the steps in declared order.

        A step whose dependencies are not all DONE is SKIPPED, with the
        unmet dependency named. A step whose runner raises is FAILED,
        with the error recorded.

        The runner decides whether a step succeeds. This method decides
        what that means for the rest of the plan.
        """
        if self.status is not PlanStatus.PENDING:
            raise RuntimeError(
                "this plan is %s and cannot be run again" % self.status.value)
        self.status = PlanStatus.RUNNING
        for step in self.steps:
            unmet = [n for n in step.needs
                     if self._by_name[n].status is not StepStatus.DONE]
            if unmet:
                step.status = StepStatus.SKIPPED
                step.error = "unmet dependency: %s" % ",".join(unmet)
                continue
            step.status = StepStatus.RUNNING
            try:
                runner(step)
            except Exception as exc:  # noqa: BLE001 -- the failure is data
                step.status = StepStatus.FAILED
                step.error = "%s: %s" % (type(exc).__name__, exc)
                continue
            step.status = StepStatus.DONE
        self.status = (PlanStatus.FAILED
                       if any(s.status is StepStatus.FAILED for s in self.steps)
                       else PlanStatus.COMPLETED)
        return self

    # -- stopping --------------------------------------------------------

    def abandon(self, reason: str) -> "Plan":
        """Stop the plan, and leave the reason on the record.

        A plan that cannot be abandoned is not a plan. And an
        abandonment nobody can explain is indistinguishable from a
        failure, so the reason is required.
        """
        if not str(reason).strip():
            raise ValueError(
                "an abandonment with no reason cannot be told apart "
                "from a failure")
        self.status = PlanStatus.ABANDONED
        self.abandon_reason = str(reason)
        for step in self.steps:
            if step.status is StepStatus.PENDING:
                step.status = StepStatus.SKIPPED
                step.error = "the plan was abandoned"
        return self


# -----------------------------------------------------------------------------
# selftest
# ---------------------------------------------------------------------------

def _selftest() -> int:
    ok = True

    def check(label: str, cond: bool, extra: str = "") -> None:
        nonlocal ok
        ok = ok and cond
        print("  %-58s %s%s" % (label, "OK" if cond else "FAIL",
                                 (" -- " + extra) if extra and not cond else ""))

    print("=" * 70)
    print("1. a failing step leaves its dependents SKIPPED, not passed")
    print("=" * 70)
    plan = Plan([
        Step("a", needs=(), produces="the first thing"),
        Step("b", needs=("a",), produces="the second thing"),
        Step("c", needs=("b",), produces="the third thing"),
    ])

    def fail_a(step: Step) -> None:
        if step.name == "a":
            raise RuntimeError("a failed on purpose")

    plan.run(fail_a)
    d = plan.to_dict()
    check("the failed step is FAILED", d["steps"][0]["status"] == "failed",
          d["steps"][0]["status"])
    check("its dependent is SKIPPED", d["steps"][1]["status"] == "skipped",
          d["steps"][1]["status"])
    check("the dependent of the skipped is SKIPPED too",
          d["steps"][2]["status"] == "skipped", d["steps"][2]["status"])
    check("the plan is FAILED", d["status"] == "failed", d["status"])

    print()
    print("=" * 70)
    print("2. a plan can be abandoned, and the reason is on the record")
    print("=" * 70)
    plan2 = Plan([Step("x"), Step("y", needs=("x",))])
    plan2.abandon("the caller changed its mind")
    d2 = plan2.to_dict()
    check("the plan is ABANDONED", d2["status"] == "abandoned", d2["status"])
    check("the reason is recorded",
          d2["abandon_reason"] == "the caller changed its mind",
          repr(d2["abandon_reason"]))
    check("no step is left pending",
          all(s["status"] != "pending" for s in d2["steps"]))

    print()
    print("=" * 70)
    print("3. a plan that cannot be run is refused, not half-run")
    print("=" * 70)
    try:
        Plan([Step("p", needs=("q",))])
        check("an unknown dependency is refused", False)
    except ValueError as exc:
        check("an unknown dependency is refused", True, str(exc))
    try:
        Plan([Step("p", needs=("q",)), Step("q", needs=("p",))])
        check("a dependency cycle is refused", False)
    except ValueError as exc:
        check("a dependency cycle is refused", True, str(exc))
    try:
        Plan([Step("p"), Step("p")])
        check("two steps with one name are refused", False)
    except ValueError as exc:
        check("two steps with one name are refused", True, str(exc))
    try:
        Plan([Step("p")]).abandon("  ")
        check("an abandonment with no reason is refused", False)
    except ValueError as exc:
        check("an abandonment with no reason is refused", True, str(exc))

    print()
    print("=" * 70)
    print("4. a plan that runs to completion says so")
    print("=" * 70)
    plan3 = Plan([Step("m"), Step("n", needs=("m",))])
    plan3.run(lambda step: None)
    d3 = plan3.to_dict()
    check("the plan is COMPLETED", d3["status"] == "completed", d3["status"])
    check("both steps are DONE",
          all(s["status"] == "done" for s in d3["steps"]))

    print()
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys

    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    print(__doc__)
