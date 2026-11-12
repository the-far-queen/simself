"""
test_robot_checks.py -- THE ROBOT'S CHECKS MUST RUN SOMEWHERE, OR THEY
RUN NOWHERE.

**AND THE GATE REGISTRY SAYS THEY RUN IN "simself's own suite", AND
THAT WAS NOT TRUE.** MEASURED 2026-11-12: `grep -rn "check_robot_loop"
tests/` returned NOTHING, and the same for `check_steel_ball`. So the
registry's `runs_in` field was prose that named a runner which did not
exist -- **and the registry's own `run_nowhere` finding could not see
it, because it only reports a check whose `runs_in` says NOWHERE.**

**THAT IS THE DEFECT CLASS ITEM 60 CLOSED, IN A NEW PLACE:** a claim
that reads as a fact and is checked by nothing. A check that runs
nowhere is a check that cannot fail.

**SO THIS FILE IS THE RUNNER, AND IT RUNS THE CHECKS AS SUBPROCESSES** --
the same way a gate runs them, so what the suite measures is what the
gate measures. And it runs them under the interpreter that carries
numpy, because the fc's own kernel needs it.

**AND THE RUNBOUND RULE APPLIES HERE TOO:** every command gets a
budget, so a check that hangs cannot hang the suite. `check_robot_loop`
used to TIME OUT at 240s -- Godot 4 has no `OS.get_stdin()`, so the
commands went in a file -- and a check that hangs is a check that
takes the suite with it.

Run:
    python -m pytest tests/test_robot_checks.py -q
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
TOOLS = REPO / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import _project_python as PP  # noqa: E402

#: THE INTERPRETER, and it is the one with numpy -- the fc's kernel
#: needs it, and the bridge reaches the PSB, which needs it too.
PYTHON = str(PP.project_venv() or pathlib.Path(sys.executable))

#: THE BUDGET, and it is the same 240s the gate registry measured the
#: old hang against.
TIMEOUT = 240


def _godot_available() -> bool:
    home = pathlib.Path(os.environ.get(
        "HERMES_HOME", str(pathlib.Path.home() / "AppData" / "Local" /
                            "hermes")))
    return (home / "tools" / "godot" /
            "Godot_v4.4.1-stable_win64_console.exe").exists()


requires_godot = pytest.mark.skipif(
    not _godot_available(),
    reason="godot is not installed, so the body cannot be run")


def _run(name: str) -> subprocess.CompletedProcess:
    """Run a check as a subprocess, the way the gate runs it."""
    return subprocess.run([PYTHON, str(TOOLS / name)],
                          capture_output=True, text=True, timeout=TIMEOUT,
                          cwd=str(REPO))


@requires_godot
def test_the_robot_loop_check_is_green():
    """THE LOOP, and it must finish AND be green.

    **AND IT MUST FINISH.** The registry recorded this check as
    TIME OUT at 240s and as running NOWHERE. Both are wrong now, and
    the second one was wrong because nothing ran it.
    """
    proc = _run("check_robot_loop.py")
    out = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, (
        "the robot loop check is not green:\n%s" % out[-4000:])
    assert "GREEN" in out, "the robot loop check said nothing:\n%s" % out[-2000:]


@requires_godot
def test_the_steel_ball_check_is_green():
    """THE BALL AND THE KERNEL MUST AGREE, step for step."""
    proc = _run("check_steel_ball.py")
    out = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, (
        "the steel ball check is not green:\n%s" % out[-4000:])


def test_the_registry_claims_a_runner_that_exists():
    """THE CLAIM MUST BE TRUE, AND THIS IS THE CHECK FOR THE CLAIM.

    **AND IT IS ABOUT THE CLAIMS THIS REPO MAKES.** The gate registry
    names a runner for every check it excludes from the daily gate,
    and this file is one of the runners it names. So the claim is
    checked against the tree: **a check whose only runner is a name in
    a list is a check that cannot fail.**

    **AND THE LIST IS THE PROJECT'S OWN, NOT A COPY.** It is read from
    `far-coding/src/gate_registry.py`, so a claim added there is
    checked here without a second list to keep in step.
    """
    registry = REPO.parent / "far-coding" / "src" / "gate_registry.py"
    if not registry.exists():
        pytest.skip("the gate registry is not beside this repo")
    src = registry.read_text(encoding="utf-8")
    claimed = []
    for path in ("check_robot_loop.py", "check_steel_ball.py",
                 "check_robot_wiring.py",
                 "mutation_check_robot_wiring.py"):
        if path in src:
            claimed.append(path)
    assert claimed, ("the gate registry names none of this repo's robot "
                     "checks, so the registry and the tree have drifted")
    for name in claimed:
        stem = name[:-3] if name.endswith(".py") else name
        # **AND THE TREE IS SCANNED, NOT THE INDEX.** MEASURED
        # 2026-11-12: the first version of this check used
        # `git grep -- tests/`, and it reported that NO test ran
        # `check_robot_loop` -- while the test that does run it was
        # sitting in tests/ UNTRACKED, because it had never been
        # committed. **`git grep` searches the INDEX, and the index is
        # not the tree** -- so the check could not see the very file
        # that made the claim true. The tree is what runs.
        runners = []
        for p in sorted((REPO / "tests").glob("test_*.py")):
            try:
                body = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if stem in body:
                runners.append(p.name)
        assert runners, (
            "the gate registry says %s runs in simself's own suite, and "
            "no test in tests/ runs it -- so it runs NOWHERE and the "
            "claim is false" % name)
