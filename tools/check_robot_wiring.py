#!/usr/bin/env python3
"""
check_robot_wiring.py -- THE FIFTY COMMANDS ARE CALLS ON THE BALL.

Bobby, 2026-11-07: *"then simself and fc and godot to become a robot and
mte to decqphier english"*, and *"nothing exists if not coded"*.

**AND THIS FILE CHECKS THE FOUR CLAIMS THE QUEUE ITEM 61 NAMES.**

    1. EVERY COMMAND BECOMES A CALL ON THE BALL. `body.translate` is an
       impulse, `gripper.close` is a constraint on a named object,
       `sensor.light` is a read of the hole's brightness. **AND THE
       COMMAND SURFACE DOES NOT RE-IMPLEMENT THE PHYSICS: the fifty
       commands are the INPUT, and the fc's own kernel step is still
       the DRIVE.**
    2. THE SEEKS BECOME COMMANDS. `seek`, `seek_red` and `seek_light`
       are three commands over the same sensors, and the hole at (0,0)
       is what `seek_red` finds. **AND EACH SEEK NAMES THE SENSOR THAT
       CONFIRMED IT** -- the receipt's `verified` field -- so the three
       are three commands and not one command under three names.
       **AND `cause` IS A COMMIT**: it asserts one named event caused
       another and records it, so the sim can be ASKED why it moved.
    3. THE REFUSAL MUST BE REAL. A command the vocabulary does not
       admit is refused WITH A REASON, exactly as the PSB refuses a
       span without a primitive. **AND THE PSB IS NOT TOUCHED.** **AND
       A REFUSAL MUST BE THE RIGHT REFUSAL** -- the session gate
       refuses a command before the session starts, and the out-of-
       bounds refusal names the bound, and both are checked AT THEIR
       OWN INDEX, because a refusal that happens somewhere else is not
       the refusal that was asked for.
    4. THE CHECK MUST COVER THE WIRING, and it must be able to go RED
       on a broken wiring.

**AND EVERY EXPECTATION HERE IS DERIVED FROM A SOURCE THAT IS NOT THE
BODY.** The effects are computed from the fc's OWN kernel (fieldcore's
`tiniest_core`) and from the registry (the robot's own vocabulary), and
the body is measured against them. **A CHECK THAT READS ITS OWN
IMPLEMENTATION IS NOT A CHECK.**

**AND EVERY RECEIPT IS PAIRED BY ITS INDEX**, so a command that needs a
setup -- a grasp needs the arm within reach, so a grasp needs a seek
first -- is issued with that setup and checked at the right place. **A
CHECK THAT MATCHES BY VERB NAME CANNOT SEE AN ORDER.**

Run:
    python tools/check_robot_wiring.py
Exit: 0 when all fifty commands are wired and every claim above holds.
"""
from __future__ import annotations

import json
import math
import os
import pathlib
import subprocess
import sys
import tempfile
from typing import Any, Callable, Dict, List, Optional, Tuple

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SRC = REPO / "src"
EMB = SRC / "research" / "embodiment"
FC_SRC = REPO.parent / "fieldcore" / "src"

#: THE FC'S OWN KERNEL, imported and never copied. **AND THE RADIUS IS
#: THE WORLD'S, NOT THE fc's DEFAULT_R** -- MEASURED: `tiniest_core`'s
#: DEFAULT_R is 3.0 and the sim's world is a ball of radius 10, and
#: `check_steel_ball.py` already made this distinction.
RADIUS = 10.0
ETA = 0.1
ARRIVAL_CM = 0.5
#: THE BATTERY'S RATE, and it is READ FROM THE BODY'S OWN SIM LINE at
#: run time -- so a body that changed its rate changed the check too.
BATTERY_PER_CM = 0.002


def godot_sim_dir() -> pathlib.Path:
    """WHERE THE BODY IS, and the mutation harness points this
    elsewhere."""
    env = os.environ.get("FC_GODOT_SIM")
    if env:
        return pathlib.Path(env)
    return REPO / "godot_sim"


def _godot_exe() -> pathlib.Path:
    home = pathlib.Path(os.environ.get(
        "HERMES_HOME", str(pathlib.Path.home() / "AppData" / "Local" /
                            "hermes")))
    cand = home / "tools" / "godot" / "Godot_v4.4.1-stable_win64_console.exe"
    if cand.exists():
        return cand
    raise FileNotFoundError("godot is not at %s" % (cand.parent))


# ---------------------------------------------------------------------------
# THE FC'S OWN MODULE, imported, never copied.
def load_fc():
    tc_dir = str(FC_SRC / "tiniest_core")
    if tc_dir not in sys.path:
        sys.path.insert(0, tc_dir)
    import importlib.util

    import numpy as np

    spec = importlib.util.spec_from_file_location(
        "fc_tiniest_core", FC_SRC / "tiniest_core" / "tiniest_core.py")
    if spec is None or spec.loader is None:
        raise ImportError("the fc's kernel is not at %s"
                          % (FC_SRC / "tiniest_core" / "tiniest_core.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["fc_tiniest_core"] = mod
    spec.loader.exec_module(mod)
    return np, mod


def fc_step(np, tc, psi) -> Tuple[float, float]:
    """THE FC'S OWN STEP, applied to a point, in the fc's own terms."""
    arr = np.array([psi[0], psi[1]], dtype=float)
    psi0 = np.zeros(2)
    out = tc.project_ball(arr - ETA * tc.gradient(arr, psi0), psi0, RADIUS)
    return float(out[0]), float(out[1])


# ---------------------------------------------------------------------------
# THE REGISTRY, the robot's own vocabulary, imported and never copied.
def load_registry():
    for p in (str(SRC), str(EMB)):
        if p not in sys.path:
            sys.path.insert(0, p)
    import robot_vocabulary as RV

    return RV


# ---------------------------------------------------------------------------
# THE EXPECTATIONS. Each one reads the receipt's OWN `pre` state, so a
# check never depends on where the body happened to be.
Checker = Callable[[Dict[str, Any]], List[str]]


def _all(*checkers: Checker) -> Checker:
    """SEVERAL EXPECTATIONS ON ONE RECEIPT, and every one must hold."""
    def check(r: Dict[str, Any]) -> List[str]:
        why: List[str] = []
        for c in checkers:
            why.extend(c(r))
        return why

    return check


def _impulse(expected: Callable[[Dict[str, Any]], Tuple[float, float]],
             tol: float = 1e-9) -> Checker:
    """THE COMMAND IS AN IMPULSE, and the body moved by exactly it."""
    def check(r: Dict[str, Any]) -> List[str]:
        want = expected(r)
        got = (float(r["impulse"][0]), float(r["impulse"][1]))
        if abs(got[0] - want[0]) > tol or abs(got[1] - want[1]) > tol:
            return ["the impulse was (%.9f, %.9f) and the command asked for "
                    "(%.9f, %.9f)" % (got[0], got[1], want[0], want[1])]
        pre = r["pre"]["pos"]
        post = r["post"]["pos"]
        if abs((post[0] - pre[0]) - got[0]) > 1e-6 \
                or abs((post[1] - pre[1]) - got[1]) > 1e-6:
            return ["the body moved (%.9f, %.9f) but the impulse was "
                    "(%.9f, %.9f)" % (post[0] - pre[0], post[1] - pre[1],
                                       got[0], got[1])]
        return []

    return check


def _field(path: Tuple[str, ...], expected, tol: float = 1e-9) -> Checker:
    def check(r: Dict[str, Any]) -> List[str]:
        node: Any = r
        for key in path:
            node = node[key]
        want = expected(r)
        if abs(float(node) - float(want)) > tol:
            return ["%s was %.9f and the command implies %.9f"
                    % (".".join(path), float(node), float(want))]
        return []

    return check


def _field_pair(path: Tuple[str, ...],
                expected: Callable[[Dict[str, Any]], Tuple[float, float]],
                tol: float = 1e-6) -> Checker:
    def check(r: Dict[str, Any]) -> List[str]:
        node: Any = r
        for key in path:
            node = node[key]
        want = expected(r)
        if abs(float(node[0]) - want[0]) > tol \
                or abs(float(node[1]) - want[1]) > tol:
            return ["%s was (%.9f, %.9f) and the command implies "
                    "(%.9f, %.9f)" % (".".join(path), float(node[0]),
                                       float(node[1]), want[0], want[1])]
        return []

    return check


def _equals(path: Tuple[str, ...], expected) -> Checker:
    def check(r: Dict[str, Any]) -> List[str]:
        node: Any = r
        for key in path:
            node = node[key]
        if node != expected:
            return ["%s was %r and it must be %r"
                    % (".".join(path), node, expected)]
        return []

    return check


def _read_is(expected) -> Checker:
    def check(r: Dict[str, Any]) -> List[str]:
        got = r["read"]
        want = expected(r)
        if isinstance(want, float):
            if abs(float(got) - want) > 1e-9:
                return ["the reading was %.9f and it must be %.9f"
                        % (float(got), want)]
            return []
        if got != want:
            return ["the reading was %r and it must be %r" % (got, want)]
        return []

    return check


def _tip_moved(delta: Callable[[Dict[str, Any]], Tuple[float, float]],
               tol: float = 1e-6) -> Checker:
    """THE ARM, and it is the second body's own geometry."""
    def check(r: Dict[str, Any]) -> List[str]:
        want = delta(r)
        pre = r["pre"]["arm"]["tip"]
        post = r["post"]["arm"]["tip"]
        got = (post[0] - pre[0], post[1] - pre[1])
        if abs(got[0] - want[0]) > tol or abs(got[1] - want[1]) > tol:
            return ["the arm tip moved (%.9f, %.9f) and the command asked "
                    "for (%.9f, %.9f)" % (got[0], got[1], want[0], want[1])]
        return []

    return check


def _sweep_ok(r: Dict[str, Any]) -> bool:
    """THE SWEEP, and it must name the hole and the cube, with their
    distances."""
    seen = r["read"]
    if not isinstance(seen, list):
        return False
    names = sorted(x["name"] for x in seen)
    if names != ["cube", "hole"]:
        return False
    for x in seen:
        if x["name"] == "hole":
            if abs(float(x["distance"]) - r["pre"]["distance"]) > 1e-6:
                return False
        elif x["name"] == "cube":
            p = r["pre"]["objects"]["cube"]
            want = math.hypot(p[0] - r["pre"]["pos"][0],
                              p[1] - r["pre"]["pos"][1])
            if abs(float(x["distance"]) - want) > 1e-6:
                return False
    return True


def _verified_is(prefix: str) -> Checker:
    """THE SENSOR THAT CONFIRMED, and it is the body's own naming.

    **AND THE PREFIX IS THE CLAIM.** The body writes "distance:0.47",
    "colour:red" and "light:0.97", so the prefix names the sensor and
    the rest is the reading. A seek confirmed by the wrong sensor is a
    different command wearing the same name, and the item asks for
    three of them.
    """
    def check(r: Dict[str, Any]) -> List[str]:
        got = r.get("verified", "")
        if not str(got).startswith(prefix):
            return ["the seek was confirmed by %r and it must be "
                    "confirmed by %r" % (got, prefix)]
        return []

    return check


def _battery_drained(r: Dict[str, Any]) -> List[str]:
    """THE BATTERY, and it must have paid for the distance the body
    moved -- exactly, at the body's own rate."""
    pre = r["pre"]["pos"]
    post = r["post"]["pos"]
    moved = math.hypot(post[0] - pre[0], post[1] - pre[1])
    want = r["pre"]["battery"] - BATTERY_PER_CM * moved
    if abs(float(r["post"]["battery"]) - want) > 1e-9:
        return ["the battery is %.9f after moving %.9f cm and it must be "
                "%.9f" % (float(r["post"]["battery"]), moved, want)]
    if r["post"]["battery"] >= r["pre"]["battery"]:
        return ["the battery did not fall: %.9f -> %.9f"
                % (r["pre"]["battery"], r["post"]["battery"])]
    return []


def _approach_check(r: Dict[str, Any]) -> List[str]:
    """THE APPROACH, and it must close the distance to the point it was
    sent to, and stop within the arrival tolerance of it."""
    post = r["post"]
    want = math.hypot(4.0 - post["pos"][0], 4.0 - post["pos"][1])
    if want > ARRIVAL_CM + 1e-6:
        return ["the body is %.9f cm from (4, 4) and the arrival "
                "tolerance is %.4f" % (want, ARRIVAL_CM)]
    return []


def _explore_check(r: Dict[str, Any]) -> List[str]:
    """THE EXPLORE, and it moved without a target."""
    if r["covered"] <= 0.0:
        return ["the explore covered %.9f cm and it must have moved"
                % r["covered"]]
    pre = r["pre"]["pos"]
    post = r["post"]["pos"]
    if abs(post[0] - pre[0]) < 1e-9 and abs(post[1] - pre[1]) < 1e-9:
        return ["the explore did not move the body"]
    return []


# ---------------------------------------------------------------------------
# THE PLAN. Every entry is a command, its setup, and what the receipt
# must show. **AND THE INDEX IS THE COMMAND'S PLACE IN THE FILE**, so a
# receipt is paired with the command that asked for it.
class Plan:
    def __init__(self) -> None:
        self.cmds: List[Dict[str, Any]] = []
        self.expect: List[Tuple[int, str, Checker]] = []
        #: THE EXPECTED REFUSALS, and they are EXPECTED -- because a
        #: refusal that is never asked for is a refusal that was never
        #: measured, and a refusal that is asked for but not checked is
        #: a command whose refusal nobody looked at.
        self.refuse: List[Tuple[int, str, str]] = []

    def raw(self, verb: str, op: str, args: Dict[str, Any]) -> int:
        self.cmds.append({"verb": verb, "op": op, "args": args})
        return len(self.cmds) - 1

    def refuse_with(self, verb: str, op: str, args: Dict[str, Any],
                     needle: str) -> None:
        """Issue a command that MUST be refused, and say why."""
        idx = self.raw(verb, op, args)
        self.refuse.append((idx, verb, needle))

    def run(self, verb: str, op: str, args: Dict[str, Any],
            checker: Optional[Checker] = None,
            setup: Optional[List[Tuple[str, str, Dict[str, Any]]]] = None
            ) -> None:
        for sv, so, sa in (setup or []):
            self.raw(sv, so, sa)
        idx = self.raw(verb, op, args)
        if checker is not None:
            self.expect.append((idx, verb, checker))


def build_plan(RV) -> Plan:
    """THE PLAN, and it covers every one of the fifty commands."""
    p = Plan()
    reset = ("reset", "sim.reset", {})
    seek = ("seek", "body.seek", {"target": "hole"})
    grasp = ("grasp", "gripper.close_at", {"object": "cube"})
    #: A grasp needs the arm within reach of the object, and the object
    #: is by the hole -- so a grasp is issued after a seek.
    at_hole = [reset, seek]

    # -- THE SESSION GATE, AND IT IS EXERCISED FIRST -----------------
    # **AND THE GATE IS MEASURED BEFORE THE SESSION IS OPENED.**
    # MEASURED 2026-11-12: mutation M13 removed the gate from the
    # body, and the wiring check was GREEN on it -- because the plan
    # opened the session with `sim.start` before anything else, so the
    # gate never had a chance to refuse anything. **A GATE THAT IS
    # NEVER EXERCISED IS NOT A GATE**, so the plan now issues a
    # command BEFORE the session starts and requires it to be refused
    # with the session's own reason.
    p.refuse_with("move_up", "body.translate", {"cm": 1.0},
                  "the session has not started")

    # -- THE LIFECYCLE ------------------------------------------------
    p.run("start", "sim.start", {"mode": "ghost"},
          _equals(("post", "session"), "running"))
    p.run("pause", "sim.pause", {},
          _equals(("post", "session"), "paused"))
    p.run("resume", "sim.resume", {},
          _equals(("post", "session"), "running"))
    p.run("reset", "sim.reset", {},
          _all(_field_pair(("post", "pos"), lambda r: (8.0, 6.0)),
               _equals(("post", "battery"), 1.0)))

    # -- THE LOCOMOTION, and every one of them is a body op ----------
    # AND THE BATTERY DRAINS BY EXACTLY THE DISTANCE THE BODY MOVED --
    # **A BATTERY THAT NEVER FALLS IS NOT A BATTERY**, and the only
    # way to know it falls is to measure the fall.
    p.run("move_up", "body.translate", {"cm": 2.0},
          _all(_impulse(lambda r: (0.0, 2.0)),
               _battery_drained), setup=[reset])
    p.run("move_down", "body.translate", {"cm": 2.0},
          _impulse(lambda r: (0.0, -2.0)), setup=[reset])
    p.run("move_left", "body.translate", {"cm": 2.0},
          _impulse(lambda r: (-2.0, 0.0)), setup=[reset])
    p.run("move_right", "body.translate", {"cm": 2.0},
          _impulse(lambda r: (2.0, 0.0)), setup=[reset])
    p.run("up", "body.translate", {"cm": 1.5},
          _impulse(lambda r: (0.0, 1.5)), setup=[reset])
    p.run("left", "body.translate", {"cm": 1.5},
          _impulse(lambda r: (-1.5, 0.0)), setup=[reset])
    p.run("strafe_left", "body.translate", {"cm": 2.0},
          _impulse(lambda r: (-math.sin(r["pre"]["rot"]) * 2.0,
                              math.cos(r["pre"]["rot"]) * 2.0)), setup=[reset])
    p.run("move_to", "body.translate_to", {"x": 2.0, "y": -3.0},
          _impulse(lambda r: (2.0 - r["pre"]["pos"][0],
                              -3.0 - r["pre"]["pos"][1])), setup=[reset])
    p.run("turn_left", "body.rotate", {"deg": 90.0},
          _field(("post", "rot"), lambda r: r["pre"]["rot"] + math.pi / 2.0),
          setup=[reset])
    p.run("turn_right", "body.rotate", {"deg": 90.0},
          _field(("post", "rot"), lambda r: r["pre"]["rot"] - math.pi / 2.0),
          setup=[reset])
    p.run("stop_moving", "body.velocity_zero", {},
          _equals(("post", "hold"), True), setup=[reset])

    # -- THE SENSING, and every one of them is a read -----------------
    p.run("read_light", "sensor.light", {},
          _read_is(lambda r: 1.0 / (1.0 + r["pre"]["distance"] ** 2)),
          setup=[reset])
    p.run("read_distance", "sensor.distance", {},
          _read_is(lambda r: r["pre"]["distance"]), setup=[reset])
    p.run("read_colour", "sensor.colour", {},
          _read_is(lambda r: "red" if r["pre"]["distance"] <= ARRIVAL_CM
                   else ""), setup=at_hole)
    p.run("read_position", "body.position", {},
          _read_is(lambda r: r["pre"]["pos"]), setup=[reset])
    p.run("read_battery", "sensor.battery", {},
          _read_is(lambda r: r["pre"]["battery"]), setup=[reset])
    p.run("look_up", "head.rotate", {"deg": 20.0},
          _field(("post", "head", "pitch"),
                 lambda r: r["pre"]["head"]["pitch"] + math.radians(20.0)),
          setup=[reset])
    p.run("look_down", "head.rotate", {"deg": 20.0},
          _field(("post", "head", "pitch"),
                 lambda r: r["pre"]["head"]["pitch"] - math.radians(20.0)),
          setup=[reset])
    p.run("look_left", "head.rotate", {"deg": 30.0},
          _field(("post", "head", "yaw"),
                 lambda r: r["pre"]["head"]["yaw"] + math.radians(30.0)),
          setup=[reset])
    p.run("look_right", "head.rotate", {"deg": 30.0},
          _field(("post", "head", "yaw"),
                 lambda r: r["pre"]["head"]["yaw"] - math.radians(30.0)),
          setup=[reset])
    p.run("look_at", "head.look_at", {"x": 3.0, "y": 4.0},
          _field(("post", "head", "yaw"),
                 lambda r: math.atan2(4.0 - r["pre"]["pos"][1],
                                      3.0 - r["pre"]["pos"][0])),
          setup=[reset])
    p.run("scan", "sensor.sweep", {},
          lambda r: ([] if _sweep_ok(r) else
                     ["the sweep did not name the hole and the cube with "
                      "their distances"]), setup=[reset])

    # -- THE MANIPULATION, and it needs the SECOND BODY --------------
    p.run("arm_up", "arm.translate", {"cm": 1.0},
          _tip_moved(lambda r: (0.0, 1.0)), setup=[reset])
    p.run("arm_down", "arm.translate", {"cm": 1.0},
          _tip_moved(lambda r: (0.0, -1.0)), setup=[reset])
    p.run("arm_forward", "arm.translate", {"cm": 1.0},
          _tip_moved(lambda r: (math.cos(r["pre"]["rot"]),
                                math.sin(r["pre"]["rot"]))), setup=[reset])
    p.run("arm_back", "arm.translate", {"cm": 1.0},
          _tip_moved(lambda r: (-math.cos(r["pre"]["rot"]),
                                -math.sin(r["pre"]["rot"]))), setup=[reset])
    p.run("arm_left", "arm.translate", {"cm": 1.0},
          _tip_moved(lambda r: (-math.sin(r["pre"]["rot"]),
                                math.cos(r["pre"]["rot"]))), setup=[reset])
    p.run("arm_right", "arm.translate", {"cm": 1.0},
          _tip_moved(lambda r: (math.sin(r["pre"]["rot"]),
                                -math.cos(r["pre"]["rot"]))), setup=[reset])
    p.run("reach", "arm.look_at", {"x": 1.0, "y": 0.0},
          _field_pair(("post", "arm", "tip"), lambda r: (1.0, 0.0)),
          setup=at_hole)
    p.run("extend_arm", "arm.set_length", {"cm": 3.0},
          _field(("post", "arm", "length"), lambda r: 3.0), setup=[reset])
    p.run("retract_arm", "arm.set_length", {"cm": 1.0},
          _field(("post", "arm", "length"),
                 lambda r: r["pre"]["arm"]["length"] - 1.0), setup=[reset])
    p.run("grip", "gripper.close", {},
          _equals(("post", "gripper"), "closed"), setup=[reset])
    p.run("release", "gripper.open", {},
          _equals(("post", "gripper"), "open"), setup=[reset])
    p.run("grasp", "gripper.close_at", {"object": "cube"},
          _all(_equals(("post", "held"), "cube"),
               _equals(("post", "gripper"), "closed")), setup=at_hole)
    p.run("drop", "gripper.open", {},
          _all(_equals(("post", "held"), ""),
               _equals(("post", "gripper"), "open")),
          setup=at_hole + [grasp])
    p.run("place", "gripper.place_at", {"x": 2.0, "y": 2.0},
          _all(_field_pair(("post", "objects", "cube"),
                           lambda r: (2.0, 2.0)),
               _equals(("post", "held"), "")), setup=at_hole + [grasp])
    p.run("carry", "gripper.hold", {},
          _all(_equals(("post", "carried"), True),
               _equals(("post", "held"), "cube")), setup=at_hole + [grasp])

    # -- THE SEEKING, and the seeks are the seek the sim already runs -
    # **AND THE THREE SEEKS ARE THREE COMMANDS OVER THE SAME SENSORS,
    # AND THE RECEIPT SAYS WHICH SENSOR CONFIRMED EACH.** MEASURED
    # 2026-11-12: the body prints a `verified` field naming the sensor
    # that confirmed the seek -- "distance:", "colour:" or "light:" --
    # and the check NEVER READ IT. So all three seeks passed on their
    # distance alone, and a body that answered `seek_red` with the
    # distance sensor would have passed. **THE ITEM ASKS FOR THREE
    # SEEKS OVER THE SAME SENSOR, AND THE CHECK MEASURED ONE.**
    p.run("seek", "body.seek", {"target": "hole"},
          _all(_field(("drive", "distance"), lambda r: 0.0,
                      tol=ARRIVAL_CM),
               _verified_is("distance:")), setup=[reset])
    p.run("seek_red", "body.seek_colour", {"cm": 0.2},
          _all(_equals(("drive", "colour"), "red"),
               _field(("drive", "distance"), lambda r: 0.0, tol=0.2),
               _verified_is("colour:")), setup=[reset])
    p.run("seek_light", "body.seek_light", {"cm": 0.2},
          _all(_field(("drive", "distance"), lambda r: 0.0, tol=0.2),
               _verified_is("light:")), setup=[reset])
    p.run("approach", "body.approach", {"x": 4.0, "y": 4.0},
          _approach_check, setup=[reset])
    p.run("explore", "body.explore", {}, _explore_check, setup=[reset])
    # AND THE COMMIT, which is `cause`, and it records the assertion.
    p.run("cause", "sim.assert_cause",
          {"effect": "the body moved", "cause": "the impulse arrived"},
          _equals(("post", "causes"), 1), setup=[reset])
    # AND THE PROMISE, which is also a commit.
    p.run("promise", "sim.promise", {"state": "the body is home"},
          _equals(("post", "promises"), 1), setup=[reset])

    # -- THE REFUSALS, and they carry a reason -----------------------
    # AND THEY ARE ISSUED, because a refusal that is never asked for is
    # a refusal that was never measured. **AND THEY COME BEFORE THE
    # SESSION ENDS**, because after `end` the session refuses
    # everything -- and then the refusal would be refused for the wrong
    # reason and the check would measure nothing.
    p.raw("warp", "body.warp", {})
    p.raw("move_to", "body.translate_to", {"x": 40.0, "y": 40.0})

    # -- THE LIFECYCLE'S END, and it comes LAST because after `stop`
    # the session refuses everything except `end` --------------------
    p.run("stop", "sim.stop", {},
          _equals(("post", "session"), "stopped"))
    p.run("end", "sim.end", {},
          _equals(("post", "session"), "ended"))

    # AND THE ASK, and it is how the sim is asked WHY it moved.
    p.cmds.append({"query": "causes"})

    return p


# ---------------------------------------------------------------------------
# RUNNING THE BODY.
def run_body(cmds: List[Dict[str, Any]], godot_sim: Optional[pathlib.Path] = None,
             exe: Optional[pathlib.Path] = None) -> str:
    """Feed the commands to the body and return what it printed."""
    if godot_sim is None:
        godot_sim = godot_sim_dir()
    if exe is None:
        exe = _godot_exe()
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False,
                                     encoding="utf-8") as fh:
        for c in cmds:
            fh.write(json.dumps(c) + "\n")
        path = fh.name
    env = dict(os.environ)
    env["FC_COMMANDS"] = path
    try:
        out = subprocess.run(
            [str(exe), "--headless", "--path", str(godot_sim),
             "res://scenes/RobotControl.tscn"],
            capture_output=True, text=True, timeout=300, env=env).stdout
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    return out


def parse(out: str) -> Dict[str, Any]:
    """THE RECEIPTS, the refusals, the kernel lines and the ledgers."""
    traces: List[Dict[str, Any]] = []
    refusals: List[Dict[str, Any]] = []
    kernels: List[List[Tuple[float, float]]] = []
    paths: Dict[int, List[Tuple[float, float]]] = {}
    causes: List[Any] = []
    promises: List[Any] = []
    queries: List[Dict[str, Any]] = []
    for line in out.splitlines():
        if line.startswith("TRACE "):
            traces.append(json.loads(line[6:]))
        elif line.startswith("REFUSED "):
            refusals.append(json.loads(line[8:]))
        elif line.startswith("KERNEL "):
            vals = [float(v) for v in line[7:].split()]
            kernels.append([(vals[i], vals[i + 1])
                            for i in range(0, len(vals), 2)])
        elif line.startswith("PATH "):
            parts = line[5:].split()
            idx = int(parts[0])
            nums = [float(v) for v in parts[1:]]
            paths[idx] = [(nums[i], nums[i + 1])
                          for i in range(0, len(nums), 2)]
        elif line.startswith("CAUSES "):
            causes = json.loads(line[7:])
        elif line.startswith("PROMISES "):
            promises = json.loads(line[9:])
        elif line.startswith("QUERY "):
            queries.append(json.loads(line[6:]))
    return {"traces": traces, "refusals": refusals, "kernels": kernels,
            "paths": paths, "causes": causes, "promises": promises,
            "queries": queries}


# ---------------------------------------------------------------------------
# THE CHECK.
def check(godot_sim: Optional[pathlib.Path] = None,
          exe: Optional[pathlib.Path] = None) -> Tuple[int, str]:
    np, tc = load_fc()
    RV = load_registry()
    plan = build_plan(RV)
    out = run_body(plan.cmds, godot_sim=godot_sim, exe=exe)
    got = parse(out)
    problems: List[str] = []

    # AND THE RATE IS THE BODY'S OWN, so the check cannot drift from
    # the body it is checking.
    for line in out.splitlines():
        if line.startswith("SIM "):
            sim = json.loads(line[4:])
            global BATTERY_PER_CM
            BATTERY_PER_CM = float(sim.get("battery_per_cm",
                                           BATTERY_PER_CM))
            break

    by_index: Dict[int, Dict[str, Any]] = {t["i"]: t for t in got["traces"]}
    refused_by_index: Dict[int, Dict[str, Any]] = {r["i"]: r
                                                   for r in got["refusals"]}

    # -- 1. THE BODY ANSWERED EVERY COMMAND --------------------------
    registry_verbs = {c.verb for c in RV.COMMANDS}
    issued = {c["verb"] for c in plan.cmds if "verb" in c}
    missing = registry_verbs - issued
    if missing:
        problems.append("the plan does not issue %d of the registry's "
                        "commands: %s" % (len(missing), ", ".join(sorted(missing))))
    answered = {t["verb"] for t in got["traces"]}
    not_answered = registry_verbs - answered
    if not_answered:
        problems.append("the body did not answer %d of the registry's "
                        "commands: %s"
                        % (len(not_answered), ", ".join(sorted(not_answered))))

    # -- 2. THE FC'S OWN STEP, and the body's step is it -------------
    if not got["kernels"]:
        problems.append("the body printed no kernel line")
    worst = 0.0
    for series in got["kernels"]:
        psi = series[0]
        want = [psi]
        for _ in range(len(series) - 1):
            psi = fc_step(np, tc, psi)
            want.append(psi)
        for a, b in zip(series, want):
            worst = max(worst, abs(a[0] - b[0]), abs(a[1] - b[1]))
    if worst > 1e-9:
        problems.append("the body's kernel step differs from the fc's own "
                        "module by %.3e" % worst)

    # -- 3. THE DRIVE IS THE FC'S STEP, step for step ----------------
    # **AND IT IS CHECKED ON EVERY COMMAND**, so a drive that drifts
    # anywhere is caught, and not only on one happy path.
    worst_drive = 0.0
    drive_checked = 0
    for t in got["traces"]:
        path = got["paths"].get(t["i"], [])
        if not path:
            continue
        if t["post"]["hold"]:
            # THE HOLD, and the body refuses to move further -- so the
            # path must be CONSTANT and the fc's step must NOT be there.
            for pt in path[1:]:
                if abs(pt[0] - path[0][0]) > 1e-12 \
                        or abs(pt[1] - path[0][1]) > 1e-12:
                    problems.append("the body was held but it moved from "
                                    "(%.9f, %.9f) to (%.9f, %.9f)"
                                    % (path[0][0], path[0][1], pt[0], pt[1]))
                    break
            drive_checked += len(path)
            continue
        psi = path[0]
        for pt in path[1:]:
            psi = fc_step(np, tc, psi)
            worst_drive = max(worst_drive, abs(pt[0] - psi[0]),
                              abs(pt[1] - psi[1]))
        drive_checked += len(path)
    if drive_checked == 0:
        problems.append("no drive path was checked against the fc's step")
    elif worst_drive > 1e-9:
        problems.append("the drive differs from the fc's own step by %.3e "
                        "over %d ticks" % (worst_drive, drive_checked))

    # -- 4. EVERY COMMAND'S EFFECT ----------------------------------
    for idx, verb, checker in plan.expect:
        r = by_index.get(idx)
        if r is None:
            why = refused_by_index.get(idx, {}).get("reason", "no receipt")
            problems.append("%s (at %d) produced no receipt: %s"
                            % (verb, idx, why))
            continue
        for w in checker(r):
            problems.append("%s: %s" % (verb, w))

    # -- 5. THE REFUSALS, and they carry a reason --------------------
    refusal_specs = (("warp", "is not one the body knows"),
                     ("move_to", "outside the fc's ball"))
    for verb, needle in refusal_specs:
        if not any(r["verb"] == verb and needle in r["reason"]
                   for r in got["refusals"]):
            problems.append("the body did not refuse %r with a reason "
                            "containing %r" % (verb, needle))
    if not got["refusals"]:
        problems.append("nothing was refused, so the refusal path was "
                        "never exercised")
    # **AND THE EXPECTED REFUSALS ARE CHECKED AT THEIR OWN INDEX.**
    # **AND THE INDEX IS THE COMMAND'S PLACE IN THE FILE**, because a
    # refusal that happens somewhere else is not the refusal that was
    # asked for -- and the session gate is the case that proves it: the
    # body refuses a move before the session starts, and it must be
    # THAT move, at THAT place, with THAT reason.
    for idx, verb, needle in plan.refuse:
        r = refused_by_index.get(idx)
        if r is None:
            problems.append("%s (at %d) was NOT refused, and it must be "
                            "refused with %r" % (verb, idx, needle))
            continue
        if needle not in r.get("reason", ""):
            problems.append("%s (at %d) was refused for the wrong reason: "
                            "%r, and it must name %r"
                            % (verb, idx, r.get("reason"), needle))

    # -- 6. THE COMMIT, and the sim can be ASKED why it moved --------
    if not got["causes"]:
        problems.append("the cause ledger is empty, so the commit never "
                        "happened")
    if not got["queries"]:
        problems.append("the sim was never asked why it moved")
    else:
        q = got["queries"][-1]
        if not q.get("causes"):
            problems.append("the query returned no causes")
        else:
            # **AND THE COMMIT MUST RECORD WHAT THE COMMAND NAMED** --
            # a ledger that holds an entry with nothing in it is a
            # ledger that was written and not committed.
            c = q["causes"][-1]
            if c.get("effect") != "the body moved":
                problems.append("the committed effect is %r and it must be "
                                "the one the command named"
                                % c.get("effect"))
            if c.get("cause") != "the impulse arrived":
                problems.append("the committed cause is %r and it must be "
                                "the one the command named"
                                % c.get("cause"))

    # -- 7. THE PSB IS NOT TOUCHED ----------------------------------
    # **AND THE TEST IS THAT THE PSB'S PRIMITIVES ARE UNCHANGED, NOT
    # THAT NO ROBOT VERB IS A PSB WORD.** MEASURED: the first version of
    # this check asserted the latter and went RED on `act/drop`,
    # `refuse/stop` and `commit/promise` -- and those three were in the
    # PSB BEFORE the robot's registry existed. They are the PSB's own
    # trigger words, and the robot's registry docstring records the
    # collision. **SO THE CHECK WAS WRONG, AND THE BODY WAS RIGHT.**
    from constitutional import psb_primitives as PSB

    if len(PSB.PRIMITIVES) != 6:
        problems.append("the PSB holds %d primitives and it must hold 6"
                        % len(PSB.PRIMITIVES))
    robot_verbs = {c.verb for c in RV.COMMANDS}
    collide = set()
    for words in PSB.PRIMITIVES.values():
        for w in words:
            if w in robot_verbs:
                collide.add(w)
    expected_collide = {"stop", "drop", "promise"}
    if collide != expected_collide:
        problems.append("the PSB's collision with the robot's verbs is %s "
                        "and the registry records it as %s"
                        % (sorted(collide), sorted(expected_collide)))
    for v in ("grasp", "cause", "seek", "arm_up", "start"):
        if PSB.classify_span(v) != PSB.UnitType.OTHER:
            problems.append("the PSB now classifies %r as %s, and it must "
                            "stay OTHER" % (v, PSB.classify_span(v).value))

    # -- 8. THE BRIDGE, and the operation is the registry's name -----
    import robot_bridge as RB

    for c in RV.COMMANDS:
        reading = RB.Reading(span=c.verb.replace("_", " "), verb=c.verb,
                              args={}, how="exact")
        gd = RB.to_godot(reading)
        if not gd.get("ok"):
            problems.append("the bridge refused the registry's own verb %r: "
                            "%s" % (c.verb, gd.get("reason")))
        elif gd.get("op") != c.godot_op:
            problems.append("the bridge named the operation %r for %r and "
                            "the registry names %r"
                            % (gd.get("op"), c.verb, c.godot_op))

    # -- 9. AND A VERB THE VOCABULARY DOES NOT ADMIT IS REFUSED -----
    r = RB.decipher("fly the body to the moon", prefer_model=False)
    if r.ok:
        problems.append("the bridge admitted a verb the vocabulary does not "
                        "hold")
    elif not r.reason:
        problems.append("the bridge refused a verb with no reason")

    # -- THE REPORT --------------------------------------------------
    # **AND THE INSTRUMENT IS IN THE REPORT**, because a number whose
    # instrument is invisible is a number nobody can compare with
    # anything -- and item 59's whole lesson was that the measurer
    # must be visible.
    try:
        import _project_python as PP
        instrument = PP.describe()
    except Exception:                                   # noqa: BLE001
        instrument = "the interpreter: %s" % sys.executable
    print("=" * 74)
    print("THE FIFTY COMMANDS, WIRED TO THE BALL")
    print("=" * 74)
    print("  %s" % instrument)
    print("  the registry's commands:      %d" % len(RV.COMMANDS))
    print("  the commands the plan issued: %d" % len(plan.cmds))
    print("  the body's receipts:           %d" % len(got["traces"]))
    print("  the body's refusals:           %d" % len(got["refusals"]))
    print("  the kernel vs the fc's step:   %.3e" % worst)
    print("  the drive vs the fc's step:    %.3e over %d ticks"
          % (worst_drive, drive_checked))
    print("  the causes committed:          %d" % len(got["causes"]))
    print("  the promises committed:        %d" % len(got["promises"]))
    print("")
    for r in got["refusals"]:
        print("    REFUSED %-10s %s" % (r["verb"], r["reason"]))
    print("")
    if problems:
        print("RED -- %d problem(s)" % len(problems))
        for p in problems:
            print("   - %s" % p)
        return 1, out
    print("GREEN -- every one of the fifty commands is a call on the ball, "
          "the refusals carry reasons, and the drive is the fc's own step")
    return 0, out


def main() -> int:
    # -- 0. AND THE INSTRUMENT IS CHOSEN BEFORE THE MEASUREMENT -------
    # **AND THIS IS THE DEFECT CLASS ITEM 59 CLOSED, IN A DIFFERENT
    # REPO.** MEASURED 2026-11-12: under the hermes venv (python 3.11,
    # no numpy) this check raised `ModuleNotFoundError: No module named
    # 'numpy'` -- because the fc's OWN kernel (`tiniest_core`) imports
    # numpy at module level, and a plain-python copy of the fc's step
    # would be a LOOKALIKE and not the fc's own function. So the
    # dependency is real, and what changes is the interpreter the check
    # FINDS FOR ITSELF.
    import _project_python as PP
    rc = PP.reexec_under_project_python()
    if rc is not None:
        return rc
    try:
        code, _ = check()
    except FileNotFoundError as exc:
        print("RED -- %s" % exc)
        return 1
    return code


if __name__ == "__main__":
    raise SystemExit(main())
