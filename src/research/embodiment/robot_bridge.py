"""
robot_bridge.py -- THE SEAM BETWEEN THE ENGLISH AND THE ROBOT.

Bobby, 2026-11-07: *"lets chat we have self coding ie nothing exists
if not coded, then simself and fc and godot to become a robot and mte
to decipher english"*, and *"temporarily just insert a call to minimax
llm for mte"*.

**AND THIS FILE IS THAT SEAM, AND IT IS THREE PIECES:**

    the ROBOT'S OWN VOCABULARY   50 commands, each with its PSB type,
                                 its Godot operation and its arguments
                                 (`robot_vocabulary.py`)

    the MTE'S DECIPHERING         English in, a structured command out.
                                 TEMPORARILY by asking the MiniMax LLM,
                                 because the deterministic
                                 slot-pattern compiler needs a PATTERN
                                 for every sentence shape and
                                 "move up 1cm" has a magnitude slot
                                 nobody has written a pattern for yet

    THE SUBSTRATE'S VALIDATION    the model's answer is a PROPOSAL.
                                 The verb must be in the registry, the
                                 arguments must match their declared
                                 kinds, and the magnitudes must be
                                 inside the bounds. **THE LLM PROPOSES
                                 AND THE SUBSTRATE DISPOSES.**

**AND THE SPEND GUARD IS THE FC'S OWN, AND IT IS CLOSED BY DEFAULT.**
Bobby, 2026-10-25: *"do not use my credit card pls"*. So a live call
needs `allow_live=True` on the client, or `GABRIELLE_ALLOW_LIVE=1` in
the environment -- and **the guard is checked in the client, not at the
call site, so that no caller can bypass it by accident.**

**AND WITH THE GUARD CLOSED THIS STILL WORKS**, because the vocabulary's
own exact-verb lookup is the deterministic path and it needs no model at
all. **A SEAM THAT ONLY WORKS WHEN THE MONEY WORKS IS NOT A SEAM.**

Run:
    python src/research/embodiment/robot_bridge.py --ask "move up 1cm"
    python src/research/embodiment/robot_bridge.py --check
Exit: 0 from --check when every command round-trips and every refusal
names a reason.
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import robot_vocabulary as RV   # noqa: E402

#: THE BOUNDS, and they are BOBBY'S: *"2d seek from bounds 10,10,
#: -10,-10"*. So the world is x in [-10, 10] and y in [-10, 10].
BOUNDS_MIN = -10.0
BOUNDS_MAX = 10.0
#: AND THE MAXIMUM A SINGLE COMMAND MAY MOVE, because a command that
#: moves 10^9 cm is not a command, it is a confabulation with a number.
MAX_STEP_CM = 10.0


@dataclass
class Reading:
    """WHAT THE BRIDGE READ, and it always says how it read it."""
    #: The English that was read.
    span: str = ""
    #: The command's verb, or "" if nothing was read.
    verb: str = ""
    #: The command's arguments.
    args: Dict[str, Any] = field(default_factory=dict)
    #: How it was read: "exact", "model", or "refused".
    how: str = "refused"
    #: WHY, and a refusal without a reason is not a refusal.
    reason: str = ""
    #: The model's own words, when a model was asked.
    raw: str = ""
    #: What it would have cost. **AND IT IS REPORTED EVEN WHEN IT WAS
    #: NOT SPENT, because a cost nobody was told about is a cost
    #: somebody will find on a statement.**
    would_spend: bool = False

    @property
    def ok(self) -> bool:
        return self.verb != "" and self.how != "refused"

    def to_json(self) -> Dict[str, Any]:
        return {"span": self.span, "verb": self.verb, "args": self.args,
                "how": self.how, "reason": self.reason,
                "would_spend": self.would_spend}


# ---------------------------------------------------------------------------
# THE DETERMINISTIC PATH -- and it needs no model at all
# ---------------------------------------------------------------------------

def read_exact(span: str) -> Reading:
    """Read the span against the vocabulary's OWN verbs, exactly.

    **AND THIS IS THE PATH THAT WORKS WITH THE SPEND GUARD CLOSED**, and
    it is the floor the model path must not fall below.

    MEASURED 2026-11-07: the reflex's `_content_words` strips every
    pronoun and every interrogative, so an identity question was
    invisible to any word-matching selection -- **and the same trap
    waits here.** So the exact path matches the VERB, not the words:
    the span must START with a verb the registry holds.
    """
    s = (span or "").strip().lower()
    if not s:
        return Reading(span=span, how="refused",
                       reason="the span is empty")
    # THE VERB, and it is the FIRST word.
    first = re.findall(r"[a-z_]+", s)
    if not first:
        return Reading(span=span, how="refused",
                       reason="the span carries no word")
    cmd = RV.lookup(first[0])
    if cmd is None:
        # AND THE CONTRACTION, because "move up 1cm" has the verb
        # "move" and the registry's verbs are "move_up", "move_left" and
        # so on -- so the SECOND word may complete it.
        if len(first) > 1:
            cmd = RV.lookup("%s_%s" % (first[0], first[1]))
        if cmd is None:
            return Reading(
                span=span, how="refused",
                reason="no verb in the robot's vocabulary begins %r -- the "
                       "registry holds %d commands and this is not one of "
                       "them" % (first[0], len(RV.COMMANDS)))
    args = _extract_args(cmd, s)
    bad = _validate(cmd, args)
    if bad:
        return Reading(span=span, verb=cmd.verb, args=args, how="refused",
                       reason=bad)
    return Reading(span=span, verb=cmd.verb, args=args, how="exact")


def _extract_args(cmd: "RV.Command", span: str) -> Dict[str, Any]:
    """The arguments the command declares, read out of the span."""
    args: Dict[str, Any] = {}
    if not cmd.args:
        return args
    nums = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", span)]
    words = re.findall(r"[a-z_]+", span)
    for name, kind in cmd.args:
        if kind == "float":
            if nums:
                args[name] = nums.pop(0)
            else:
                args[name] = 0.0
        elif kind == "string":
            # THE OBJECT, and it is the word that is not the verb and
            # not a direction.
            skip = {"move", "up", "down", "left", "right", "go", "stop",
                    "start", "grasp", "release", "drop", "place", "carry",
                    "the", "a", "an", "of", "by", "to", "at", "on", "in"}
            cands = [w for w in words if w not in skip]
            args[name] = cands[0] if cands else ""
        else:
            args[name] = ""
    return args


def _validate(cmd: "RV.Command", args: Dict[str, Any]) -> str:
    """Validate a proposed command against the SUBSTRATE, and return the
    reason it is refused -- or "" if it holds.

    **AND THIS IS WHERE THE MODEL'S ANSWER GETS THE SUBSTRATE'S VETO.**
    The LLM proposes; the registry and the bounds dispose.
    """
    declared = {n: k for n, k in cmd.args}
    for name in args:
        if name not in declared:
            return ("the command %r takes %s, and %r is not one of them"
                    % (cmd.verb, ", ".join(sorted(declared)) or "no "
                       "arguments", name))
    for name, kind in declared.items():
        if name not in args:
            return ("the command %r needs the argument %r" % (cmd.verb, name))
        v = args[name]
        if kind == "float":
            try:
                fv = float(v)
            except (TypeError, ValueError):
                return ("the argument %r of %r is not a number: %r"
                        % (name, cmd.verb, v))
            if abs(fv) > MAX_STEP_CM:
                return ("the argument %r of %r is %g, and the maximum a "
                        "single command may move is %g"
                        % (name, cmd.verb, fv, MAX_STEP_CM))
            args[name] = fv
    return ""


# ---------------------------------------------------------------------------
# THE MODEL PATH -- TEMPORARY, AND GUARDED
# ---------------------------------------------------------------------------

_PROMPT = """\
You translate one robot instruction into one structured command.

THE ROBOT'S VOCABULARY -- use one of these verbs, exactly:
%s

THE ARGUMENTS each verb takes:
%s

BOUNDS: a movement is at most %g cm. The world is x %g..%g and y %g..%g.

THE INSTRUCTION: %s

ANSWER WITH ONE JSON OBJECT AND NOTHING ELSE:
{"verb": "<one verb from the list>", "args": {<the arguments, numbers as
numbers, strings as strings>}}

IF THE INSTRUCTION IS NOT A ROBOT COMMAND, ANSWER:
{"verb": "", "args": {}}
"""


def read_with_model(span: str) -> Reading:
    """Ask the MiniMax LLM what the instruction means.

    **AND THIS IS TEMPORARY, AND IT IS GUARDED, AND IT IS NOT THE POINT.**

    Bobby, 2026-11-07: *"temporarily just insert a call to minimax llm
    for mte"*. The MTE's deterministic compiler needs a PATTERN for
    every sentence shape, and "move up 1cm" has a magnitude slot that
    nobody has written a pattern for -- so the model reads it for now.

    **AND THE SPEND GUARD IS THE FC'S OWN AND IT IS CHECKED IN THE
    CLIENT, NOT HERE**, so no caller can bypass it. **AND WITH THE GUARD
    CLOSED THIS RAISES `ModelUnavailable` AND THE CALLER FALLS BACK TO
    THE DETERMINISTIC PATH**, which needs no money at all.
    """
    verbs = ", ".join(c.verb for c in RV.COMMANDS)
    arglines = "\n".join(
        "  %s: %s" % (c.verb, ", ".join("%s:%s" % (n, k) for n, k in c.args)
                      or "(none)")
        for c in RV.COMMANDS)
    prompt = _PROMPT % (verbs, arglines, MAX_STEP_CM, BOUNDS_MIN, BOUNDS_MAX,
                        BOUNDS_MIN, BOUNDS_MAX, span)
    # THE CLIENT, from the fc, so the credential and the guard are the
    # fc's and not a second implementation of them.
    fc_src = os.path.abspath(os.path.join(_SRC, "..", "fieldcore", "src"))
    if fc_src not in sys.path:
        sys.path.insert(0, fc_src)
    from minimax_client import MiniMaxClient, ModelUnavailable  # type: ignore
    client = MiniMaxClient(max_tokens=300, timeout=45.0, allow_live=False)
    try:
        raw = client.generate(prompt)
    except ModelUnavailable as exc:
        return Reading(span=span, how="refused",
                       reason="the spend guard is closed (%s), so the model "
                              "did not read it" % exc,
                       would_spend=False)
    except Exception as exc:  # noqa: BLE001
        return Reading(span=span, how="refused",
                       reason="the model did not answer: %r" % (exc,),
                       would_spend=False)
    # AND THE PARSE, and it is strict: the model's JSON is a PROPOSAL
    # and it is checked against the registry.
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        return Reading(span=span, how="refused", raw=raw or "",
                       reason="the model's answer carried no JSON object")
    try:
        obj = json.loads(m.group(0))
    except Exception as exc:  # noqa: BLE001
        return Reading(span=span, how="refused", raw=raw or "",
                       reason="the model's JSON did not parse: %r" % (exc,))
    verb = str(obj.get("verb") or "").strip().lower()
    args = obj.get("args") or {}
    if not isinstance(args, dict):
        return Reading(span=span, how="refused", raw=raw or "",
                       reason="the model's arguments are not an object")
    if not verb:
        return Reading(span=span, how="refused", raw=raw or "",
                       reason="the model read no verb -- the instruction is "
                              "not a robot command")
    cmd = RV.lookup(verb)
    if cmd is None:
        return Reading(span=span, verb=verb, args=dict(args),
                       how="refused", raw=raw or "",
                       reason="the model proposed %r, which is not in the "
                              "robot's vocabulary of %d commands"
                              % (verb, len(RV.COMMANDS)))
    bad = _validate(cmd, dict(args))
    if bad:
        return Reading(span=span, verb=cmd.verb, args=dict(args),
                       how="refused", raw=raw or "", reason=bad)
    return Reading(span=span, verb=cmd.verb, args=dict(args), how="model",
                   raw=raw or "", would_spend=True)


# ---------------------------------------------------------------------------
# THE BRIDGE
# ---------------------------------------------------------------------------

def decipher(span: str, prefer_model: bool = True) -> Reading:
    """Read an English instruction as a robot command.

    **AND THE ORDER IS THE DETERMINISTIC PATH FIRST.** MEASURED: the
    exact path handles "move up 1cm" with no model and no money, so
    there is no reason to spend a credit to read something the registry
    can read. **THE MODEL IS THE FALLBACK, NOT THE FIRST CHOICE** --
    and that is the opposite of what a language model is usually for,
    and it is the right way round for a control system.
    """
    exact = read_exact(span)
    if exact.ok:
        return exact
    if not prefer_model:
        return exact
    model = read_with_model(span)
    if model.ok:
        return model
    # AND THE MODEL'S REFUSAL DOES NOT OVERRIDE THE EXACT PATH'S
    # REASON -- the exact path's reason is the SUBSTRATE'S, and the
    # substrate's reason is the one that stands.
    if exact.reason:
        exact.would_spend = model.would_spend
        return exact
    return model


def check() -> int:
    """Every command round-trips, and every refusal names a reason."""
    problems: List[str] = []

    # -- 1. EVERY COMMAND'S OWN VERB READS ITSELF ---------------------
    for c in RV.COMMANDS:
        r = read_exact(c.verb.replace("_", " "))
        if not r.ok:
            problems.append("%s did not read itself: %s" % (c.verb, r.reason))

    # -- 2. AND THE NAMED ONES WITH THEIR ARGUMENTS ------------------
    for span, verb in (("move up 1cm", "move_up"), ("move left 2cm",
                                                  "move_left"),
                       ("grasp the cup", "grasp"), ("start", "start"),
                       ("stop", "stop"), ("cause the arm to rise", "cause")):
        r = read_exact(span)
        if not r.ok:
            problems.append("%r did not read: %s" % (span, r.reason))
        elif r.verb != verb:
            problems.append("%r read as %r, not %r" % (span, r.verb, verb))

    # -- 3. AND A SPAN THAT IS NOT A COMMAND IS REFUSED WITH A REASON -
    for span in ("what is the weather in Bangkok tomorrow",
                 "please write a poem about rain"):
        r = read_exact(span)
        if r.ok:
            problems.append("%r read as %r, and it is not a command"
                            % (span, r.verb))
        elif not r.reason:
            problems.append("%r was refused without a reason" % span)

    # -- 4. AND THE BOUNDS HOLD --------------------------------------
    r = read_exact("move up 9999cm")
    if r.ok:
        problems.append("a 9999cm move was accepted")
    elif "maximum" not in r.reason:
        problems.append("the bound's reason does not say why: %s" % r.reason)

    # -- 5. AND THE MODEL PATH FALLS BACK WITH THE GUARD CLOSED -------
    r = decipher("please move the arm upward by one centimetre",
                 prefer_model=True)
    if r.ok and r.how == "model":
        # The guard is closed by default, so a model read here would be
        # a SPEND. And it is not, so this is not a failure -- but it
        # must be reported, because a silent fallback is a silent
        # difference.
        problems.append("the model path ran with the spend guard closed")

    print("=" * 70)
    print("THE ROBOT BRIDGE")
    print("=" * 70)
    print("  the commands:          %d" % len(RV.COMMANDS))
    print("  the bounds:            x %g..%g, y %g..%g"
          % (BOUNDS_MIN, BOUNDS_MAX, BOUNDS_MIN, BOUNDS_MAX))
    print("  the maximum a move:    %g cm" % MAX_STEP_CM)
    print("")
    for span in ("move up 1cm", "grasp the cup", "start", "stop",
                 "what is the weather in Bangkok tomorrow"):
        r = decipher(span, prefer_model=False)
        print("  %-38s -> %-10s %s" % (repr(span), r.verb or "-", r.reason))
    print("")
    if problems:
        print("RED -- %d problem(s)" % len(problems))
        for p in problems:
            print("   - %s" % p)
        return 1
    print("GREEN -- every command round-trips and every refusal names a "
          "reason")
    return 0


def main(argv: List[str]) -> int:
    if "--check" in argv:
        return check()
    if "--ask" in argv:
        i = argv.index("--ask")
        span = argv[i + 1] if i + 1 < len(argv) else ""
        r = decipher(span)
        print(json.dumps(r.to_json(), indent=2))
        return 0 if r.ok else 1
    print("THE ROBOT BRIDGE -- ask it something")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
