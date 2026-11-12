"""
test_robot_wiring.py -- THE FIFTY COMMANDS ARE CALLS ON THE BALL, AND
THE SUITE MUST HOLD IT.

THE RULE
--------
CENTRAL-RULES.md rule 7: a test that cannot fail is not a test. And the
queue item 61 carried: **the check must be able to go RED on a broken
wiring**.

**AND THIS FILE IS THE PYTEST WRAPPER AROUND THAT CHECK**, so the
suite -- not only the tool -- holds the wiring in place. The tool
`tools/check_robot_wiring.py` is the check; this file is the test that
RUNS it, so a broken wiring fails `pytest tests/ -q` and not only the
tool.

**AND THE MUTATION RUN IS A TEST TOO**, because the item's requirement
is not "the check passes" but "the check can go RED" -- and a check
that passes and cannot fail is a check that proves nothing.

**AND THE MUTATIONS RUN ON A COPY OF THE WORLD**, never on the tree:
the mutation harness copies `godot_sim/` into a temporary directory,
breaks the copy, and points the check at the copy. **THE TREE IS NEVER
BROKEN BY A TEST.**

Run:
    python -m pytest tests/test_robot_wiring.py -q
"""
from __future__ import annotations

import os
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
SRC = REPO / "src"
EMB = SRC / "research" / "embodiment"
TOOLS = REPO / "tools"
for _p in (str(SRC), str(EMB), str(TOOLS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import check_robot_wiring as CRW  # noqa: E402
import robot_vocabulary as RV    # noqa: E402


def _godot_available() -> bool:
    try:
        CRW._godot_exe()
    except FileNotFoundError:
        return False
    return True


requires_godot = pytest.mark.skipif(
    not _godot_available(),
    reason="godot is not installed, so the body cannot be run")


@requires_godot
def test_the_fifty_commands_are_wired():
    """THE WIRING, and it must hold."""
    code, out = CRW.check()
    assert code == 0, ("the fifty commands are not wired:\n%s" % out[-4000:])


@requires_godot
def test_every_registry_command_is_wired():
    """EVERY COMMAND IN THE REGISTRY MUST BE WIRED, and the plan is
    what says so -- so the plan and the registry cannot drift apart."""
    plan = CRW.build_plan(RV)
    issued = {c["verb"] for c in plan.cmds if "verb" in c}
    registry = {c.verb for c in RV.COMMANDS}
    assert registry <= issued, ("the plan does not issue: %s"
                                % ", ".join(sorted(registry - issued)))
    # AND EVERY COMMAND IN THE REGISTRY MUST HAVE AN EXPECTATION, or
    # the check would pass a command it never looked at.
    checked = {verb for _, verb, _ in plan.expect}
    assert registry <= checked, ("the check does not examine: %s"
                                 % ", ".join(sorted(registry - checked)))


def test_the_psb_is_untouched():
    """THE PSB MUST NOT KNOW ABOUT THE ROBOT'S VERBS, and the collision
    the registry records must be exactly the collision and no more."""
    from constitutional import psb_primitives as PSB

    robot_verbs = {c.verb for c in RV.COMMANDS}
    collide = set()
    for words in PSB.PRIMITIVES.values():
        for w in words:
            if w in robot_verbs:
                collide.add(w)
    assert collide == {"stop", "drop", "promise"}, (
        "the PSB's collision with the robot's verbs is %s and the registry "
        "records it as stop, drop and promise" % sorted(collide))
    for v in ("grasp", "cause", "seek", "arm_up", "start"):
        assert PSB.classify_span(v) == PSB.UnitType.OTHER, (
            "the PSB classifies %r as %s and it must stay OTHER"
            % (v, PSB.classify_span(v).value))


@requires_godot
def test_the_wiring_check_goes_red_on_a_broken_wiring():
    """THE MUTATIONS, and every one must go RED.

    **AND THE HARNESS COPIES THE WORLD FIRST**, so this test breaks a
    copy and never the tree.
    """
    import subprocess

    mut = REPO / "tools" / "mutation_check_robot_wiring.py"
    proc = subprocess.run([sys.executable, str(mut)], capture_output=True,
                          text=True, timeout=600, cwd=str(REPO))
    assert proc.returncode == 0, (
        "a broken wiring was not caught:\n%s"
        % ((proc.stdout or "") + (proc.stderr or ""))[-4000:])
