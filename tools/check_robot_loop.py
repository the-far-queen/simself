#!/usr/bin/env python3
"""
check_robot_loop.py -- THE WHOLE LOOP, END TO END, AND THE BALL MOVES.

Bobby, 2026-11-07: *"then simself and fc and godot to become a robot
and mte to decqphier english"*, and *"nothing exists if not coded"*.

**AND THIS FILE IS THE PROOF THAT THE THREE ARE ONE THING AND NOT
THREE FILES THAT MENTION EACH OTHER.**

The loop, in order:

    ENGLISH      "move up 1cm"
      |
    the MTE      the agent reads the English -- Bobby: *"you minimax llm
                 are mte for now"* -- and the substrate's registry says
                 what the verb means
      |
    VALIDATION   the verb must be in the registry of 50; the arguments
                 must be the ones the command declares; a movement is at
                 most 10 cm; the world is x -10..10 and y -10..10
      |
    GODOT        the ball is a RigidBody2D with mass and friction and
                 bounce; the operation is the REGISTRY'S name, so the
                 model never names one
      |
    THE MEASUREMENT   where the ball ended up, printed by Godot

**AND THE SEEK IS STILL THE DRIVE**, so a command MOVES the ball and the
fc's own step KEEPS it home. **THE COMMAND IS THE INTENT AND THE SEEK
IS THE BODY.**

**AND A COMMAND THAT WOULD CARRY THE BALL OUT OF THE WORLD IS REFUSED
WITH A REASON AND NOT CLAMPED**, because the walls are real and the
fc's `project_ball` is the same constraint.

Run:
    python tools/check_robot_loop.py
Exit: 0 when the ball moved, and when the out-of-bounds move was
refused with a reason.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
from typing import Dict, List, Tuple

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SRC = REPO / "src"
EMB = SRC / "research" / "embodiment"
for p in (str(SRC), str(EMB)):
    if p not in sys.path:
        sys.path.insert(0, p)

GODOT = pathlib.Path(os.environ.get(
    "HERMES_HOME", str(pathlib.Path.home() / "AppData" / "Local" / "hermes")
)) / "tools" / "godot" / "Godot_v4.4.1-stable_win64_console.exe"
GODOT_SIM = REPO / "godot_sim"


def run_godot(commands: List[Dict]) -> Tuple[int, str]:
    """The body, fed the commands, and what it says."""
    if not GODOT.exists():
        return 0, ""
    payload = "\n".join(json.dumps(c) for c in commands) + "\n"
    try:
        out = subprocess.run(
            [str(GODOT), "--headless", "--path", str(GODOT_SIM),
             "res://scenes/RobotControl.tscn"],
            input=payload, capture_output=True, text=True, timeout=300).stdout
    except Exception as exc:                        # noqa: BLE001
        return 1, "the godot run raised: %r" % (exc,)
    return 0, out


def main() -> int:
    print("=" * 74)
    print("THE ROBOT LOOP")
    print("=" * 74)
    problems: List[str] = []

    import robot_bridge as RB

    # -- 1. THE ENGLISH BECOMES A COMMAND -----------------------------
    print()
    print("[1] the English becomes a command, and the substrate validates it")
    reading = RB.decipher("move up 1cm", prefer_model=False)
    print("    %r -> %s (%s)" % (reading.span, reading.verb or "-",
                                 reading.how))
    if not reading.ok:
        problems.append("the English did not read: %s" % reading.reason)
    gd = RB.to_godot(reading)
    print("    the godot action: %s" % json.dumps(gd))
    if not gd.get("ok"):
        problems.append("the godot action did not build: %s"
                        % gd.get("reason"))

    # -- 2. AND A SPAN THAT IS NOT A COMMAND IS REFUSED ---------------
    print()
    print("[2] a span that is not a command is refused with a reason")
    r2 = RB.decipher("what is the weather in Bangkok tomorrow",
                     prefer_model=False)
    print("    %r -> %s" % (r2.span, r2.reason[:96]))
    if r2.ok:
        problems.append("a non-command was accepted")
    elif not r2.reason:
        problems.append("the refusal named no reason")

    # -- 3. AND THE OUT-OF-BOUNDS MOVE IS REFUSED, NOT CLAMPED ---------
    print()
    print("[3] the out-of-bounds move is refused with a reason")
    r3 = RB.decipher("move up 9999cm", prefer_model=False)
    print("    %r -> %s" % (r3.span, r3.reason[:96]))
    if r3.ok:
        problems.append("a 9999cm move was accepted")
    elif "maximum" not in r3.reason:
        problems.append("the bound's reason does not say why")

    # -- 4. AND THE BALL MOVES ----------------------------------------
    print()
    print("[4] the ball moves")
    if not GODOT.exists():
        print("    (godot is not at %s -- the body was not run)" % GODOT)
        problems.append("godot is not available, so the body did not run")
    else:
        cmds = []
        for span in ("move up 1cm", "move left 1cm", "move up 1cm"):
            rd = RB.decipher(span, prefer_model=False)
            if rd.ok:
                cmds.append(RB.to_godot(rd))
        rc, out = run_godot(cmds)
        for line in out.splitlines():
            print("    ", line[:112])
        moved = False
        for m in re.finditer(r"before \((-?[\d.]+), (-?[\d.]+)\) "
                             r"after \((-?[\d.]+), (-?[\d.]+)\)", out):
            if m.group(1) != m.group(3) or m.group(2) != m.group(4):
                moved = True
        if not moved:
            problems.append("the ball did not move")
        else:
            print("    GREEN -- the ball moved")

        # -- 5. AND THE OUT-OF-BOUNDS MOVE IS REFUSED BY THE BODY -----
        print()
        print("[5] the body refuses the out-of-bounds move with a reason")
        bad = RB.to_godot(RB.Reading(span="move up 9999cm",
                                     verb="move_up",
                                     args={"cm": 9999.0}, how="exact"))
        rc2, out2 = run_godot([bad])
        refused = "REFUSED" in out2
        for line in out2.splitlines():
            if "REFUSED" in line:
                print("    ", line.strip()[:112])
        if not refused:
            problems.append("the body accepted an out-of-bounds move")
        else:
            print("    GREEN -- the body refused it")

    print()
    print("=" * 74)
    if problems:
        print("RED -- %d problem(s)" % len(problems))
        for p in problems:
            print("   - %s" % p)
        return 1
    print("GREEN -- the English reaches the ball and the ball moves")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
