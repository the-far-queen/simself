#!/usr/bin/env python3
"""
mutation_check_robot_wiring.py -- THE CHECK MUST GO RED ON A BROKEN
WIRING, AND THIS FILE PROVES IT.

CENTRAL-RULES.md rule 7: a test that cannot fail is not a test. And the
rule the queue item 61 carried: **the check must be able to go RED on a
broken wiring**, the way the projection and the tolerance checks do
now.

**AND THE MUTATIONS ARE WRITTEN AGAINST THE BODY'S OWN SOURCE**, so a
mutation is a real break in the wiring and not a change to the
checker. The body is `godot_sim/scripts/robot_control.gd`, and each
mutation removes or reverses ONE mechanism from it.

THE MUTATIONS
--------------
    M1  the drive's step loses the fc's ETA factor
        -> the drive must stop being the fc's own step
    M2  the drive's projection is removed
        -> the fc's constraint must bite, and the kernel must differ
    M3  the impulse is applied to the position TWICE
        -> a command must move the body by exactly its impulse
    M4  the impulse's sign is flipped for the vertical moves
        -> `move_up` must move the body UP
    M5  the arm's translate is ignored
        -> the second body must answer the manipulation group
    M6  the seek does not drive until it arrives
        -> a seek must ACTUALLY ARRIVE
    M7  the refusal of an unknown operation loses its reason
        -> a refusal without a reason is not a refusal
    M8  the `cause` commit is not recorded
        -> the sim cannot be asked why it moved
    M9  the head's rotate is ignored
        -> the sensing group must answer
    M10 the gripper does not hold what it grasped
        -> the constraint must hold
    M11 the battery never drains
        -> the body must consume its charge as it moves
    M12 the `hold` does not stop the body
        -> `stop_moving` must stop the body
    M13 the session gate is gone
        -> a command before `sim.start` must be refused
    M14 the impulse is applied by the drive and not by the command
        -> a command must move the body by exactly its impulse
    M15 the `seek_red` is confirmed by the distance sensor
        -> the three seeks must be three commands over the same sensors

AND THE HARNESS ITSELF, which is the project's own:
  * the baseline must be GREEN FIRST -- a mutation run against a red
    baseline proves nothing;
  * the mutation must APPLY -- each one RAISES if its anchor text is
    not in the file, because a mutation that silently does nothing
    reports "the check survived", which reads like a result and is not
    one;
  * the source must have CHANGED, by digest -- the same lesson the
    jepa harness learned;
  * the MUTATED SOURCE MUST STILL PARSE -- **and this is the rule the
    first version of the GDScript harness got wrong**: a mutation that
    does not compile is a FAILURE of the harness, not a caught
    mutation. So the harness asks Godot to load the mutated body and
    checks that it did not report a parse error;
  * the files are restored in a FINALLY block, so a red mutation does
    not leave the tree broken;
  * and it REPORTS WHICH CHECK CAUGHT IT, so "the check went red" is
    not mistaken for "the mechanism was removed".

Run:
    python tools/mutation_check_robot_wiring.py
Exit: 0 when every mutation went RED, 1 otherwise.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Callable, List, Tuple

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
GODOT_SIM = REPO / "godot_sim"
BODY = GODOT_SIM / "scripts" / "robot_control.gd"
CHECK = HERE / "check_robot_wiring.py"

#: THE PYTHON, and the venv carries numpy -- the fc's kernel needs it.
#:
#: **AND IT IS NAMED, NOT INHERITED.** MEASURED 2026-11-12: under the
#: hermes venv (python 3.11, no numpy) this harness could not even
#: reach its baseline -- the check it drives raised `ModuleNotFoundError:
#: No module named 'numpy'`. So the harness picks the interpreter that
#: HAS numpy, and the check it drives re-execs into the same one.
def _python() -> pathlib.Path:
    """The interpreter that carries numpy, and the project venv if it
    has one."""
    try:
        import numpy                                      # noqa: F401
        return pathlib.Path(sys.executable)
    except Exception:                                   # noqa: BLE001
        pass
    try:
        import _project_python as PP
        venv = PP.project_venv()
        if venv is not None:
            return venv
    except Exception:                                   # noqa: BLE001
        pass
    return pathlib.Path(sys.executable)


PYTHON = _python()


class Mutation:
    """ONE mutation, and the anchor it must find."""

    def __init__(self, name: str, what: str, anchor: str,
                 replacement: str) -> None:
        self.name = name
        self.what = what
        self.anchor = anchor
        self.replacement = replacement

    def apply(self, text: str) -> str:
        if self.anchor not in text:
            raise AssertionError("the anchor for %s is not in the body:\n%s"
                                 % (self.name, self.anchor))
        return text.replace(self.anchor, self.replacement, 1)


MUTATIONS: List[Mutation] = [
    Mutation(
        "M1", "the drive's step loses the fc's ETA factor",
        "\treturn _project(x - ETA * (x - GROUND_X), y - ETA * (y - GROUND_Y))",
        "\treturn _project(x - 0.5 * (x - GROUND_X), y - 0.5 * (y - GROUND_Y))"),
    Mutation(
        "M2", "the drive's projection is removed",
        "\tif d <= RADIUS or d == 0.0:\n\t\treturn [x, y]",
        "\tif true:\n\t\treturn [x, y]"),
    Mutation(
        "M3", "the impulse is applied to the position twice",
        "\tvar pr := _project(_px + _imp_x, _py + _imp_y)",
        "\tvar pr := _project(_px + 2.0 * _imp_x, _py + 2.0 * _imp_y)"),
    Mutation(
        "M4", "the impulse's sign is flipped for the vertical moves",
        "\t\tif verb == \"move_up\" or verb == \"up\":\n\t\t\tdy = cm",
        "\t\tif verb == \"move_up\" or verb == \"up\":\n\t\t\tdy = -cm"),
    Mutation(
        "M5", "the arm's translate is ignored",
        "\t\t_set_arm_tip(_arm_tip_x() + dx, _arm_tip_y() + dy)",
        "\t\t_set_arm_tip(_arm_tip_x(), _arm_tip_y())"),
    Mutation(
        "M6", "the seek does not drive until it arrives",
        "\tvar limit := MAX_TICKS if _drive_until_arrival else DRIVE_TICKS",
        "\tvar limit := DRIVE_TICKS"),
    Mutation(
        "M7", "the refusal of an unknown operation loses its reason",
        "\treturn (\"the operation %s is not one the body knows\" % op)",
        "\treturn \"\""),
    Mutation(
        "M8", "the `cause` commit is not recorded",
        "\t\t_causes.append({\"effect\": str(args.get(\"effect\", \"\")),\n"
        "\t\t\t\"cause\": str(args.get(\"cause\", \"\")),\n"
        "\t\t\t\"at\": [_r(_px), _r(_py)]})",
        "\t\t# THE COMMIT IS GONE, and the sim cannot be asked why\n"
        "\t\t# it moved, because nothing was recorded.\n"
        "\t\treturn \"\""),
    Mutation(
        "M9", "the head's rotate is ignored",
        "\t\tif verb == \"look_up\" or verb == \"look_down\":\n"
        "\t\t\t_pitch += delta2\n\t\telse:\n\t\t\t_yaw += delta2",
        "\t\tif false:\n\t\t\tpass"),
    Mutation(
        "M10", "the gripper does not hold what it grasped",
        "\t\t_grip = \"closed\"\n\t\t_held = obj\n\t\t_carried = false",
        "\t\t_grip = \"closed\"\n\t\t_held = \"\"\n\t\t_carried = false"),
    Mutation(
        "M11", "the battery never drains",
        "\t_batt = maxf(0.0, _batt - BATTERY_PER_CM\n"
        "\t\t* sqrt(_imp_x * _imp_x + _imp_y * _imp_y))",
        "\t_batt = _batt"),
    Mutation(
        "M12", "the `hold` does not stop the body",
        "\t\tif _hold:\n\t\t\tpath.append([_px, _py])\n"
        "\t\t\tran += 1\n\t\t\tcontinue",
        "\t\tif false:\n\t\t\tpath.append([_px, _py])\n"
        "\t\t\tran += 1\n\t\t\tcontinue"),
    Mutation(
        "M13", "the session gate is gone: a command acts before it starts",
        "\tif _session == \"new\" and op != \"sim.start\":\n"
        "\t\treturn (\"the session has not started, so %s cannot be acted on\"\n"
        "\t\t\t% verb)",
        "\tif false:\n\t\tpass"),
    Mutation(
        "M14", "the impulse is applied by the DRIVE and not by the command",
        "\tvar pr := _project(_px + _imp_x, _py + _imp_y)\n"
        "\t_px = float(pr[0])\n\t_py = float(pr[1])",
        "\t# THE IMPULSE IS NEVER APPLIED, and the drive does the work.\n"
        "\tvar pr := _project(_px, _py)\n"
        "\t_px = float(pr[0])\n\t_py = float(pr[1])"),
    Mutation(
        "M15", "the seek_red is confirmed by the DISTANCE sensor",
        "\tif _last_op == \"body.seek_colour\":\n"
        "\t\treturn \"colour:\" + _colour_reading()",
        "\tif _last_op == \"body.seek_colour\":\n"
        "\t\treturn \"distance:%.9f\" % _hole_distance()"),
]


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_check(godot_sim: pathlib.Path) -> Tuple[int, str]:
    """RUN THE CHECK against a body, and report its verdict."""
    env = dict(os.environ)
    env["FC_GODOT_SIM"] = str(godot_sim)
    try:
        proc = subprocess.run(
            [str(PYTHON), str(CHECK)], capture_output=True, text=True,
            timeout=300, env=env, cwd=str(REPO))
    except subprocess.TimeoutExpired:
        return 1, "the check timed out"
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def run_loop_check(godot_sim: pathlib.Path) -> Tuple[int, str]:
    """RUN THE LOOP CHECK against a body, and report its verdict.

    **AND THE LOOP CHECK IS A SECOND INSTRUMENT, NOT A SECOND COPY.**
    MEASURED 2026-11-12, and the first claim about this was WRONG: I
    wrote that M14 -- the impulse applied by the drive instead of by
    the command -- was caught only by the loop check. It was caught by
    the WIRING check, because that check compares the body's `post`
    against the command's own impulse, and a body that does not move
    when the command says to move fails that comparison.

    **So the loop check is a SECOND INSTRUMENT because it measures
    something the first does not**: it reads the English's path to the
    body -- the span, the bridge, the validation, the refusal -- and
    it is the check that caught the wrong-reason refusal in step 5.
    **A second instrument is worth having when it measures a different
    thing, and not because it was asserted to.** So the harness runs
    both and reports which one caught the mutation, and a mutation
    caught by NEITHER is a hole in the checks.
    """
    env = dict(os.environ)
    env["FC_GODOT_SIM"] = str(godot_sim)
    try:
        proc = subprocess.run(
            [str(PYTHON), str(HERE / "check_robot_loop.py")],
            capture_output=True, text=True, timeout=300, env=env,
            cwd=str(REPO))
    except subprocess.TimeoutExpired:
        return 1, "the loop check timed out"
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def parse_errors(text: str) -> List[str]:
    """THE PARSE ERRORS, and a mutation that does not compile is a
    FAILURE of the harness and not a caught mutation."""
    out = []
    for line in text.splitlines():
        if "Parse Error" in line or "SCRIPT ERROR" in line \
                or "Failed to load script" in line:
            out.append(line.strip())
    return out


def main() -> int:
    if not BODY.exists():
        print("RED -- the body is not at %s" % BODY)
        return 1

    # -- 1. THE BASELINE MUST BE GREEN FIRST -------------------------
    print("=" * 74)
    print("THE WIRING CHECK, AND ITS MUTATIONS")
    print("=" * 74)
    code, out = run_check(GODOT_SIM)
    if code != 0:
        print("RED -- the baseline is not GREEN, so a mutation run against "
              "it proves nothing:")
        print(out)
        return 1
    print("  the baseline: GREEN")
    # **AND THE BASELINE RUNS BOTH CHECKS, OR A MUTATION CAUGHT BY THE
    # SECOND ONE IS A MUTATION MEASURED AGAINST A RED BASELINE.**
    loop_code, loop_out = run_loop_check(GODOT_SIM)
    if loop_code != 0:
        print("RED -- the loop check's baseline is not GREEN, so a mutation "
              "run against it proves nothing:")
        print(loop_out)
        return 1
    print("  the loop check's baseline: GREEN")

    # -- 2. EACH MUTATION, IN ITS OWN COPY OF THE WORLD --------------
    original = BODY.read_text(encoding="utf-8")
    original_digest = digest(BODY)
    caught = 0
    failures: List[str] = []
    for mut in MUTATIONS:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="wiring_mut_"))
        try:
            world = tmp / "godot_sim"
            shutil.copytree(GODOT_SIM, world)
            body = world / "scripts" / "robot_control.gd"
            before = digest(body)
            try:
                mutated = mut.apply(body.read_text(encoding="utf-8"))
            except AssertionError as exc:
                failures.append("%s did not apply: %s" % (mut.name, exc))
                continue
            body.write_text(mutated, encoding="utf-8")
            after = digest(body)
            if before == after:
                failures.append("%s did not change the file" % mut.name)
                continue
            # AND THE MUTATED BODY MUST STILL PARSE, or the check went
            # red because the file is broken and not because the wiring
            # is broken.
            probe = subprocess.run(
                [str(pathlib.Path(os.environ.get(
                    "HERMES_HOME", str(pathlib.Path.home() / "AppData" /
                                        "Local" / "hermes")))
                  / "tools" / "godot" /
                  "Godot_v4.4.1-stable_win64_console.exe"),
                 "--headless", "--path", str(world),
                 "res://scenes/RobotControl.tscn"],
                capture_output=True, text=True, timeout=120,
                env=dict(os.environ, FC_COMMANDS=""))
            parse_bad = parse_errors(probe.stdout + probe.stderr)
            if parse_bad:
                failures.append("%s does not compile, so it is a FAILURE "
                                "of the harness and not a caught mutation: "
                                "%s" % (mut.name, "; ".join(parse_bad[:2])))
                continue
            code, out = run_check(world)
            # **AND THE LOOP CHECK RUNS TOO, AND THE ONE THAT CAUGHT IT
            # IS NAMED.** MEASURED 2026-11-12: mutation M14 was NOT
            # caught by the wiring check alone -- the drive that applies
            # the impulse itself is still the fc's own step, so the
            # wiring check was GREEN on it. The loop check reads the
            # body's own receipt, where the command's effect is
            # separate from the drive's, and it caught it.
            who = "check_robot_wiring"
            if code == 0:
                code2, out2 = run_loop_check(world)
                if code2 != 0:
                    code, out, who = code2, out2, "check_robot_loop"
            if code == 0:
                failures.append("%s did NOT go red -- the check survived "
                                "the broken wiring" % mut.name)
                print("    %-4s NOT CAUGHT  %s" % (mut.name, mut.what))
            else:
                caught += 1
                reason = _first_problem(out)
                print("    %-4s CAUGHT      %s" % (mut.name, mut.what))
                print("           %s" % reason)
                print("           caught by %s" % who)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # -- 3. AND THE TREE MUST BE UNCHANGED --------------------------
    if digest(BODY) != original_digest:
        BODY.write_text(original, encoding="utf-8")
        failures.append("the body was left modified")

    print("")
    print("  the mutations:        %d" % len(MUTATIONS))
    print("  the mutations caught: %d" % caught)
    if failures:
        print("RED -- %d problem(s)" % len(failures))
        for f in failures:
            print("   - %s" % f)
        return 1
    print("GREEN -- every mutation of the wiring went RED, and the body "
          "is unchanged")
    return 0


def _first_problem(out: str) -> str:
    """THE FIRST PROBLEM THE CHECK NAMED, and it is how the harness
    reports WHICH check caught the mutation."""
    for line in out.splitlines():
        t = line.strip()
        if t.startswith("- "):
            return t[2:][:150]
    return "the check went red"


if __name__ == "__main__":
    raise SystemExit(main())
