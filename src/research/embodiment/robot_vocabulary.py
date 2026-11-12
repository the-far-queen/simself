"""
robot_vocabulary.py -- THE ROBOT SHEAF'S FIFTY COMMANDS, in its OWN
registry, bound to the PSB's types.

Bobby, 2026-11-07: *"godot introduces psb ie start stop up 1cm left cause
grasp"*, and *"choose 50 basic robot commands easy to sim in godot can u
seek a red dot at 0,0 2d seek from bounds 0,10, -10,-10"*.

AND WHY THIS FILE IS ITS OWN REGISTRY AND NOT A SET OF TRIGGER WORDS IN
`constitutional/psb_primitives.py`.

**MEASURED 2026-11-07, bobby's own six commands through the PSB's own
`classify_span`:**

    stop            -> refuse     (a PSB trigger word)
    move up 1cm     -> act        (via "move")
    move left 1cm   -> act        (via "move")
    start           -> other      REFUSED
    up              -> other      REFUSED
    left            -> other      REFUSED
    cause           -> other      REFUSED
    grasp           -> other      REFUSED
    1cm             -> other      REFUSED

**SO THE PSB ADMITS ONE OF BOBBY'S SIX VERBS AND REFUSES FIVE, AND THE
REFUSAL IS CORRECT: A SPAN WITHOUT A PRIMITIVE IS REFUSED AS OTHER.**
That is the PSB's own rule and it is the fc's own rule, and it is the
right answer for a sentence.

**AND IT IS THE WRONG ANSWER FOR A ROBOT.** A robot's verbs are not
English sentences. "grasp" is not a sentence about grasping a file; it is
an actuator. So the robot's vocabulary is a SEPARATE REGISTRY -- exactly
like LITERARY_FORMS and exactly like the MLTR's own register -- and the
reason is the PSB's own docstring, quoted:

    "putting new vocabulary into PRIMITIVES changed classify_span() and
     silently weakened the confabulation filter."

**SO THE FIFTY COMMANDS LIVE HERE, AND EACH ONE BINDS TO A PSB UnitType
WITHOUT ADDING A WORD TO THE PSB.** The confabulation filter is
untouched, and the robot gets its verbs.

AND THE FIFTY ARE CHOSEN BY ONE RULE: **EASY TO SIMULATE IN GODOT.** So
each one names a Godot-side operation that is a node transform, a sensor
read, or a lifecycle call -- and none of them needs physics that a 2D
scene cannot do.

AND EACH ONE CARRIES ITS PROVENANCE, because the PSB schema says so
about the PSBs and the rule is the rule: a field cannot be asserted into
existence.

Run:
    python src/research/embodiment/robot_vocabulary.py --list
    python src/research/embodiment/robot_vocabulary.py --check
Exit: 0 when every command names its type, its Godot operation and its
provenance.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

#: THE PSB'S TYPES, and they are IMPORTED and never re-declared, because
#: a second UnitType would be a second schema.
#:
#: AND THE PATH IS SET HERE, because this module lives three directories
#: down in `src/research/embodiment/` and the PSB lives at
#: `src/constitutional/`. MEASURED: the first version tried the import
#: and it raised ModuleNotFoundError for BOTH forms, because nothing had
#: put `src/` on the path -- and a module that cannot be imported is a
#: module that cannot be used.
import os as _os
import sys as _sys

#: THE INTERPRETER IS CHOSEN BEFORE THE PSB IS IMPORTED, and it has to
#: be here -- at the TOP of the module -- because the PSB imports numpy
#: at module level, and a numpy-less interpreter cannot reach the
#: `__main__` block below. MEASURED 2026-11-12: running this registry
#: under the hermes venv (python 3.11, no numpy) raised
#: `ModuleNotFoundError: No module named 'psb_primitives'` -- which
#: was the FALLBACK's error, and the fallback pointed at the wrong
#: directory, so it named a module that was never missing. **THE REAL
#: ERROR WAS THE NUMPY ONE UNDERNEATH IT.**
#:
#: **SO THE RE-RUN HAPPENS FIRST, AND ONLY WHEN THIS FILE IS THE
#: SCRIPT BEING RUN.** A module that is imported does not re-exec: that
#: would replace the importing process, and an import is not a run.
if __name__ == "__main__":
    import importlib.util as _ilu
    _here = _os.path.dirname(_os.path.abspath(__file__))
    for _up in range(1, 6):
        _pp = _os.path.join(_here, *([_os.pardir] * _up), "tools",
                            "_project_python.py")
        if _os.path.isfile(_pp):
            _spec = _ilu.spec_from_file_location("fc_project_python", _pp)
            if _spec is not None and _spec.loader is not None:
                _mod = _ilu.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)
                _rc = _mod.reexec_under_project_python()
                if _rc is not None:
                    raise SystemExit(_rc)
            break

#: `src/research/embodiment/robot_vocabulary.py` -> up three directories
#: from the FILE (not its dir) lands on `src/`.
#: `src/research/embodiment/robot_vocabulary.py` -- up TWO directories
#: from the module's own directory lands on `src/`. MEASURED: three
#: landed on the repo root (`simself/`) and the import raised
#: ModuleNotFoundError for BOTH forms, and a fourth was no better --
#: so the arithmetic is now WALKED UP until the PSB is found, and the
#: count is not a constant at all.
_SRC = None
for _up in range(1, 6):
    _candidate = _os.path.abspath(_os.path.join(
        _os.path.dirname(_os.path.abspath(__file__)), *([".."] * _up)))
    if _os.path.isfile(_os.path.join(_candidate, "constitutional",
                                     "psb_primitives.py")):
        _SRC = _candidate
        break
if _SRC is None:
    raise ImportError("the PSB was not found walking up from %s"
                      % __file__)
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

#: THE PSB'S OWN DIRECTORY, and it is a SEPARATE path entry because the
#: fallback below needs it. **AND THE FALLBACK WAS BROKEN.** MEASURED
#: 2026-11-12: the fallback was `from psb_primitives import UnitType`,
#: but `_SRC` is `src/` and `psb_primitives.py` lives in
#: `src/constitutional/` -- so the fallback could never have worked, and
#: the second error it raised was "No module named 'psb_primitives'"
#: rather than the numpy error that actually caused the first. **A
#: FALLBACK THAT CANNOT WORK IS NOT A FALLBACK.**
_PSB_DIR = _os.path.join(_SRC, "constitutional")
if _PSB_DIR not in _sys.path:
    _sys.path.insert(0, _PSB_DIR)

try:
    from constitutional.psb_primitives import UnitType
except Exception:                                   # noqa: BLE001
    from psb_primitives import UnitType             # type: ignore


@dataclass(frozen=True)
class Command:
    """One robot command, and the four things it must name."""
    verb: str
    #: The PSB type this command is admitted as. The robot's verbs are
    #: not English sentences, so they do not go through classify_span --
    #: they are BOUND to a type, and the binding is the reviewable fact.
    unit: UnitType
    #: The Godot-side operation. This is the "easy to simulate" half:
    #: a node transform, a sensor read, or a lifecycle call.
    godot_op: str
    #: What it does, in one line.
    about: str
    #: The argument names it takes, and their kinds.
    args: Tuple[Tuple[str, str], ...] = ()
    #: WHERE THE COMMAND COMES FROM. Never empty -- the PSB schema says
    #: provenance is required for every admitted PSB, and the rule does
    #: not stop at the PSB's boundary.
    provenance: str = ("Bobby, 2026-11-07: the six named verbs, and the "
                       "fifty chosen by the easy-to-simulate rule")

    @property
    def id(self) -> str:
        return self.verb

    def describe(self) -> Dict[str, object]:
        return {
            "verb": self.verb, "unit": self.unit.value,
            "godot_op": self.godot_op, "about": self.about,
            "args": [{"name": n, "kind": k} for n, k in self.args],
            "provenance": self.provenance,
        }


#: THE FIFTY. Grouped by what they do, because a robot's surface is
#: four kinds of thing: LOCOMOTION, MANIPULATION, SENSING, and the
#: lifecycle and the epistemic verbs the PSB already names.
def _c(verb, unit, op, about, args=()):
    return Command(verb, unit, op, about, tuple(args))


COMMANDS: List[Command] = [
    # -- THE LIFECYCLE: six --------------------------------------------
    _c("start", UnitType.ACT, "sim.start",
       "begin the simulation session",
       (("mode", "ghost|real"),)),
    _c("stop", UnitType.REFUSE, "sim.stop",
       "refuse further action and end the session"),
    _c("pause", UnitType.REFUSE, "sim.pause", "hold the sim, keep the state"),
    _c("resume", UnitType.ACT, "sim.resume", "continue a paused sim"),
    _c("reset", UnitType.REFUSE, "sim.reset",
       "return the world to its initial state"),
    _c("end", UnitType.COMMIT, "sim.end",
       "commit the session's outcome and close it"),

    # -- THE LOCOMOTION, 2D: eleven ----------------------------------
    _c("move_up", UnitType.ACT, "body.translate",
       "move the body up by a distance in centimetres",
       (("cm", "float"),)),
    _c("move_down", UnitType.ACT, "body.translate",
       "move the body down by a distance in centimetres",
       (("cm", "float"),)),
    _c("move_left", UnitType.ACT, "body.translate",
       "move the body left by a distance in centimetres",
       (("cm", "float"),)),
    _c("move_right", UnitType.ACT, "body.translate",
       "move the body right by a distance in centimetres",
       (("cm", "float"),)),
    _c("move_to", UnitType.ACT, "body.translate_to",
       "move the body to an absolute 2D point",
       (("x", "float"), ("y", "float"))),
    _c("turn_left", UnitType.ACT, "body.rotate",
       "rotate the body left by degrees", (("deg", "float"),)),
    _c("turn_right", UnitType.ACT, "body.rotate",
       "rotate the body right by degrees", (("deg", "float"),)),
    _c("strafe_left", UnitType.ACT, "body.translate",
       "move left without turning the body", (("cm", "float"),)),
    _c("stop_moving", UnitType.REFUSE, "body.velocity_zero",
       "refuse to move further, without ending the session"),
    _c("up", UnitType.ACT, "body.translate",
       "the named verb for move_up", (("cm", "float"),)),
    _c("left", UnitType.ACT, "body.translate",
       "the named verb for move_left", (("cm", "float"),)),

    # -- THE MANIPULATION: fifteen -------------------------------------
    _c("arm_up", UnitType.ACT, "arm.translate",
       "raise the arm by a distance", (("cm", "float"),)),
    _c("arm_down", UnitType.ACT, "arm.translate",
       "lower the arm by a distance", (("cm", "float"),)),
    _c("arm_forward", UnitType.ACT, "arm.translate",
       "extend the arm forward", (("cm", "float"),)),
    _c("arm_back", UnitType.ACT, "arm.translate",
       "withdraw the arm", (("cm", "float"),)),
    _c("arm_left", UnitType.ACT, "arm.translate",
       "move the arm left", (("cm", "float"),)),
    _c("arm_right", UnitType.ACT, "arm.translate",
       "move the arm right", (("cm", "float"),)),
    _c("reach", UnitType.ACT, "arm.look_at",
       "reach toward an absolute 2D point", (("x", "float"), ("y", "float"))),
    _c("extend_arm", UnitType.ACT, "arm.set_length",
       "set the arm's extension", (("cm", "float"),)),
    _c("retract_arm", UnitType.ACT, "arm.set_length",
       "shorten the arm's extension", (("cm", "float"),)),
    _c("grip", UnitType.ACT, "gripper.close", "close the gripper"),
    _c("release", UnitType.ACT, "gripper.open", "open the gripper"),
    _c("grasp", UnitType.ACT, "gripper.close_at",
       "close the gripper on a named object, and hold it",
       (("object", "string"),)),
    _c("drop", UnitType.ACT, "gripper.open",
       "open the gripper and let go of what it holds"),
    _c("place", UnitType.ACT, "gripper.place_at",
       "put the held object down at an absolute 2D point",
       (("x", "float"), ("y", "float"))),
    _c("carry", UnitType.ACT, "gripper.hold",
       "hold the grasped object with the body"),

    # -- THE SENSING: eleven -----------------------------------------
    _c("read_light", UnitType.OBJECT, "sensor.light",
       "read the light sensor's intensity at the body"),
    _c("read_distance", UnitType.OBJECT, "sensor.distance",
       "read the distance sensor's range in centimetres"),
    _c("read_colour", UnitType.OBJECT, "sensor.colour",
       "read the colour sensor's reading"),
    _c("read_position", UnitType.OBJECT, "body.position",
       "read the body's own 2D position"),
    _c("read_battery", UnitType.OBJECT, "sensor.battery",
       "read the battery's charge"),
    _c("look_up", UnitType.ACT, "head.rotate",
       "tilt the head up", (("deg", "float"),)),
    _c("look_down", UnitType.ACT, "head.rotate",
       "tilt the head down", (("deg", "float"),)),
    _c("look_left", UnitType.ACT, "head.rotate",
       "turn the head left", (("deg", "float"),)),
    _c("look_right", UnitType.ACT, "head.rotate",
       "turn the head right", (("deg", "float"),)),
    _c("look_at", UnitType.ACT, "head.look_at",
       "aim the head at an absolute 2D point",
       (("x", "float"), ("y", "float"))),
    _c("scan", UnitType.ACT, "sensor.sweep",
       "sweep the sensor over the world and report what it sees"),

    # -- THE SEEKING, and the seek is THE TASK: seven ------------------
    _c("seek", UnitType.ACT, "body.seek",
       "move toward the sought target until it is reached or refused",
       (("target", "string"),)),
    _c("seek_red", UnitType.ACT, "body.seek_colour",
       "seek the red thing in the world", (("cm", "float"),)),
    _c("seek_light", UnitType.ACT, "body.seek_light",
       "seek the brightest thing in the world", (("cm", "float"),)),
    _c("approach", UnitType.ACT, "body.approach",
       "close the distance to an absolute 2D point",
       (("x", "float"), ("y", "float"))),
    _c("explore", UnitType.ACT, "body.explore",
       "move without a target, to cover the world"),
    _c("cause", UnitType.COMMIT, "sim.assert_cause",
       "assert that one named event caused another, and record it",
       (("effect", "string"), ("cause", "string"))),
    _c("promise", UnitType.COMMIT, "sim.promise",
       "commit the agent to a named end state", (("state", "string"),)),
]

#: THE GROUPS, AND THEY ARE DATA AND NOT PROSE.
#:
#: **AND THE COUNTS IN THE SECTION HEADERS ABOVE WERE WRONG.** MEASURED
#: 2026-11-12, by counting the entries under each header: the headers
#: said LOCOMOTION fourteen, SENSING thirteen and SEEKING eight, and
#: the true counts are eleven, eleven and seven. **A HEADER THAT
#: STATES A NUMBER THE CODE DOES NOT HAVE IS A CLAIM NOBODY CHECKED**,
#: and the registry's own `check()` did not look at the grouping at
#: all -- so the wrong numbers sat there and read as true.
#:
#: **SO THE GROUPING IS HERE, AS DATA, AND THE COUNTS ARE DERIVED.**
#: The mapping is the truth and the section headers above are a
#: reading aid; `check()` proves the two agree -- every command is in
#: exactly one group, and every group is in this mapping.
GROUPS: Dict[str, Tuple[str, ...]] = {
    "LIFECYCLE": ("start", "stop", "pause", "resume", "reset", "end"),
    "LOCOMOTION": ("move_up", "move_down", "move_left", "move_right",
                   "move_to", "turn_left", "turn_right", "strafe_left",
                   "stop_moving", "up", "left"),
    "MANIPULATION": ("arm_up", "arm_down", "arm_forward", "arm_back",
                     "arm_left", "arm_right", "reach", "extend_arm",
                     "retract_arm", "grip", "release", "grasp", "drop",
                     "place", "carry"),
    "SENSING": ("read_light", "read_distance", "read_colour",
                "read_position", "read_battery", "look_up", "look_down",
                "look_left", "look_right", "look_at", "scan"),
    "SEEKING": ("seek", "seek_red", "seek_light", "approach", "explore",
                "cause", "promise"),
}

#: THE ORDER, and it is the order the groups are built in: LOCOMOTION
#: first (the body alone), then SENSING, then MANIPULATION (which needs
#: a second body), then SEEKING (which is the seek the sim already
#: runs). **AND IT IS THE ORDER THE PLAN ISSUES THEM IN**, so the
#: check's own order is the item's order.
GROUP_ORDER: Tuple[str, ...] = ("LIFECYCLE", "LOCOMOTION", "SENSING",
                                 "MANIPULATION", "SEEKING")


#: THE INDEX, and it is built once so the lookup is a dict and not a
#: scan.
BY_VERB: Dict[str, Command] = {c.verb: c for c in COMMANDS}

#: THE COUNT, and it is asserted rather than hoped for.
EXPECTED = 50

#: THE SIX BOBBY NAMED, and they are here because he named them, not
#: because the count worked out.
NAMED_BY_BOBBY = ("start", "stop", "up", "left", "cause", "grasp")


def lookup(verb: str) -> Optional[Command]:
    """The command for a verb, or None.

    AND THE LOOKUP IS EXACT, because a command surface that fuzzy-matches
    is a command surface where `grasp` and `grasps` and `grasping` are
    three different things, and the refusal has to be exact too.
    """
    return BY_VERB.get(verb.strip().lower())


def check() -> int:
    """Every command names its type, its Godot operation and its
    provenance. And there are fifty of them."""
    problems: List[str] = []
    if len(COMMANDS) != EXPECTED:
        problems.append("there are %d commands, not %d"
                        % (len(COMMANDS), EXPECTED))
    if len(BY_VERB) != len(COMMANDS):
        problems.append("two commands share a verb")
    for c in COMMANDS:
        if not c.unit:
            problems.append("%s has no PSB type" % c.verb)
        if not c.godot_op:
            problems.append("%s has no Godot operation" % c.verb)
        if not c.provenance:
            problems.append("%s has no provenance" % c.verb)
        if not c.about:
            problems.append("%s has no description" % c.verb)
    for v in NAMED_BY_BOBBY:
        if v not in BY_VERB:
            problems.append("the verb bobby named, %r, is missing" % v)
    problems.extend(group_problems())
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("   - %s" % p)
        return 1
    print("CLEAN -- %d commands, every one names its type, its Godot "
          "operation and its provenance" % len(COMMANDS))
    for name in GROUP_ORDER:
        print("   %-14s %2d" % (name, len(GROUPS[name])))
    return 0


def group_problems() -> List[str]:
    """THE GROUPS MUST PARTITION THE FIFTY, and the header counts must
    agree with the code.

    **AND THIS IS THE CHECK THAT WAS MISSING.** MEASURED 2026-11-12:
    the section headers claimed LOCOMOTION fourteen, SENSING thirteen
    and SEEKING eight, and the true counts are eleven, eleven and
    seven. The registry's own `check()` never looked at the grouping,
    so three wrong numbers sat in the file and read as true -- which
    is the same defect class as the wrong count in the gate registry
    that item 60 closed.

    **AND THREE THINGS ARE PROVED, NOT ONE:**
      1. EVERY COMMAND IS IN EXACTLY ONE GROUP -- so a command cannot
         be in none (which would make it unwired by the plan) and
         cannot be in two (which would double-count it).
      2. EVERY GROUP'S MEMBERS ARE REAL COMMANDS -- so a typo in a
         group name is caught instead of quietly shrinking the count.
      3. EVERY GROUP IS EMPTY OF NONSENSE -- the groups partition the
         fifty exactly, so the counts are DERIVED and not stated.
    """
    problems: List[str] = []
    seen: Dict[str, List[str]] = {}
    for name, verbs in GROUPS.items():
        for v in verbs:
            seen.setdefault(v, []).append(name)
    for v in sorted(seen):
        if len(seen[v]) > 1:
            problems.append("the verb %r is in %d groups: %s"
                            % (v, len(seen[v]), ", ".join(seen[v])))
    for name, verbs in GROUPS.items():
        for v in verbs:
            if v not in BY_VERB:
                problems.append("the group %s names %r, which is not a "
                                "command" % (name, v))
    ungrouped = sorted(set(BY_VERB) - set(seen))
    if ungrouped:
        problems.append("the commands in no group: %s"
                        % ", ".join(ungrouped))
    extra = sorted(set(seen) - set(BY_VERB))
    if extra:
        problems.append("the groups name %d verbs that are not commands: %s"
                        % (len(extra), ", ".join(extra)))
    if set(GROUPS) != set(GROUP_ORDER):
        problems.append("the group order names %s and the groups are %s"
                        % (sorted(GROUP_ORDER), sorted(GROUPS)))
    return problems


def main(argv: List[str]) -> int:
    if "--check" in argv:
        return check()
    print("THE ROBOT SHEAF'S COMMANDS (%d)" % len(COMMANDS))
    print("=" * 78)
    for c in COMMANDS:
        args = (" " + " ".join("%s:%s" % (n, k) for n, k in c.args)) if c.args else ""
        print("  %-14s %-8s %-22s%s" % (c.verb, c.unit.value, c.godot_op, args))
    return 0


if __name__ == "__main__":
    # **AND THE INTERPRETER WAS ALREADY CHOSEN, AT THE TOP OF THIS
    # MODULE** -- before the PSB was imported, because the PSB imports
    # numpy and a numpy-less interpreter cannot reach this block. See
    # the note beside the import.
    raise SystemExit(main(sys.argv[1:]))
