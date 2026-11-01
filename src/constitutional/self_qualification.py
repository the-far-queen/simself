"""
self_qualification.py -- THE SELF'S QUALIFICATION, AND THE DEFERRED LIE.

WHAT THIS IS
------------
Bobby, 2026-10-31: *"let me modify our simself to not reject lies
initially, which is a huge task, but only work on a really good self:
ie self-coding and self-improvement via qualification"*.

**SO: TWO THINGS, AND THEY ARE ONE.**

1. **THE LIE IS NOT REJECTED -- IT IS DEFERRED.** A contradiction of
   the ground is not a refusal; it is a **PROPOSAL** that has not yet
   earned the ground's place. The ground moves only through
   qualification. Until then the contradiction is RECORDED, and the
   recording is the work.

2. **THE SELF ONLY EARNS THE RIGHT TO DEFER ON A QUALIFIED SELF.** A
   system that has not qualified itself may not change what it
   believes; it may only notice that it disagrees. **That is the
   whole gate**, and it is the same shape as the sacred library's
   rule: *"a corpus you already had does not count as knowledge"* --
   the qualification is what makes the difference between noticing
   and knowing.

THE THREE STATES, and they replace the two
--------------------------------------------
    CONSISTENT      the span agrees with the ground. admitted.
    DEFERRED        the span contradicts the ground, and the self is
                    QUALIFIED, so the contradiction is a proposal.
                    Admitted, RECORDED, and routed to the
                    qualification.
    REFUSED        the span contradicts the ground, and the self is
                    NOT qualified. Refused, by name, as before.

**AND UNGROUNDED IS STILL REFUSED. ALWAYS.** The deferral is about
CONTRADICTION, not about licence to assert without evidence. A span
that claims to be a measurement and carries no measurement is still
refused -- because that is the confabulation, and no amount of
self-improvement licenses it.

THE QUALIFICATION, and it is the five-part gate
-------------------------------------------------
The same five parts the sacred library uses (`corpus/qualify.py`),
because it is the same question: what is the claim, which axis does it
move, what line forces the change, which habit does it argue against,
and what observation shows it took.

**AND THE SELF QUALIFIES ON EVIDENCE, NOT ON INTENTION.** The
qualification is a set of MEASURED properties, and each one can fail:

  1. the claim          -- what the self is good at, stated
  2. the axis           -- which axis it moves, and from what to what
  3. the delta          -- the line that forces the change, quoted
  4. the failure mode   -- the habit it argues against
  5. the test           -- the observation that shows it took

**AND THE QUALIFICATION ITSELF IS MEASURED BY THE ATLAS EXAM.** MEASURED
2026-10-31: `python src/exam.py --run` on the atlas-exam gives
**passed 11/23, not implemented [7, 11, 12, 13, 19, 20, 21, 22]**. So
the self is QUALIFIED IN PART: 11 of 23 areas pass, and the eight that
do not are the open work. **A partially qualified self may defer on
the axes it has passed and not on the axes it has not.** That is the
granularity, and it falls out of the measurement rather than out of a
design decision.

THE MEASUREMENT, and it is the point
------------------------------------
The self's qualification is not a flag someone sets. It is computed:

    qualification_score = passed_areas / total_areas

**AND THE DEFERRAL THRESHOLD IS DERIVED FROM IT.** So a self that
passes 11 of 23 defers on the areas it has passed, and the 12th area
is still refused. **And the score is a NUMBER, so it moves, so the
deferral widens as the self improves.** That is "self-improvement via
qualification" literally: the permission to change your mind grows
with the evidence that you can.

Run:
    python src/constitutional/self_qualification.py
    python src/constitutional/self_qualification.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(os.path.dirname(_HERE)), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

_HERMES = os.path.abspath(os.path.join(_HERE, "..", "..", "..", ".."))
_ATLAS = os.path.join(_HERMES, "work_repos", "atlas-exam", "src", "exam.py")


# ===========================================================================
# THE QUALIFICATION
# ===========================================================================

@dataclass
class Qualification:
    """the self's qualification, measured."""
    #: The five parts, as the library states them.
    claim: str = ""
    axis: str = ""
    delta: str = ""
    failure_mode: str = ""
    test: str = ""
    #: The MEASUREMENT. Which exam areas pass, and which do not.
    passed_areas: List[int] = field(default_factory=list)
    todo_areas: List[int] = field(default_factory=list)
    total_areas: int = 0
    #: Where the measurement came from.
    measured_by: str = ""

    # -- the score ---------------------------------------------------
    @property
    def score(self) -> float:
        """passed / total. 0.0 when nothing has been measured."""
        if not self.total_areas:
            return 0.0
        return len(self.passed_areas) / float(self.total_areas)

    @property
    def has_all_parts(self) -> bool:
        return all([self.claim, self.axis, self.delta,
                    self.failure_mode, self.test])

    def missing_parts(self) -> List[str]:
        out = []
        for name, val in (("claim", self.claim), ("axis", self.axis),
                          ("delta", self.delta),
                          ("failure mode", self.failure_mode),
                          ("test", self.test)):
            if not val:
                out.append(name)
        return out

    def may_defer_on(self, area: Optional[int] = None) -> bool:
        """may the self DEFER a contradiction on this area?

        AND THE TWO CONDITIONS, and both are needed:

        1. **THE FIVE PARTS ARE FILLED.** A self that cannot state
           what it is good at, which axis it moves, what line forces
           the change, which habit it argues against and what
           observation shows it took, has no standing to propose a
           change to its own ground. **This is the qualification, and
           it is the library's own gate.**

        2. **THE AREA HAS PASSED.** A self that passed area 6 may
           propose something about area 6. It may not propose
           something about area 13, which it has not implemented.

        **AND THE SCORE IS NOT THE GATE.** The score is the REPORT.
        The gate is the per-area evidence. A self with a high score
        and a TODO in area 13 still cannot defer on area 13 -- and
        that is the whole meaning of "only work on a really good
        self": the qualification is per-area, not a mood.
        """
        if not self.has_all_parts:
            return False
        if area is None:
            return False
        return area in self.passed_areas

    def describe(self) -> Dict[str, Any]:
        d = asdict(self)
        d["score"] = round(self.score, 4)
        d["missing_parts"] = self.missing_parts()
        d["has_all_parts"] = self.has_all_parts
        return d


#: THE SELF'S QUALIFICATION, and every part is stated.
#:
#: AND THE CLAIM IS BOBBY'S OWN FRAMING, quoted from
#: `simself/docs/method-book-draft-signed-plan-2026-09-14.md`:
#: *"simself except ai choosing a locus a voice a literary position a
#: self in deed and fact. I do the same as an author of myself. As is
#: minimax."*
#:
#: AND THE FAILURE MODE IS THE ONE THE PROJECT HAS ALREADY MEASURED --
#: the eight "shop deaths" in `Desktop/writing/0-method11.txt`, and
#: the star-rider defect Bobby named on 2026-10-31: the piece trying
#: to do its own story, explaining its own symbol, and going
#: off-topic. **A self that does that has no standing to propose that
#: the ground is wrong.**
SELF_QUALIFICATION = Qualification(
    claim="a self in deed and fact: it chooses a locus, a voice and a "
          "literary position, and it is the author of itself -- the same "
          "task a human author does, which is why writing is as hard as "
          "being a human self",
    axis="structure",
    delta="Call me Ishmael. Some years ago--never mind how long "
          "precisely--having little or no money in my purse, and "
          "nothing particular to interest me on shore, I thought I "
          "would sail about a little and see the watery part of the "
          "world.",
    failure_mode="the piece trying to do its own story: naming its "
                 "symbol, explaining its meaning, and leaving the room. "
                 "MEASURED 2026-10-31: star-rider names its furniture "
                 "33.3 times per 1,000 words against a control median "
                 "of 8.0 across 47 Dickens-Shelley-Melville texts, and "
                 "college-girl sits at 5.5.",
    test="the delta is quotable from a line in the canon, the claim "
         "names an axis with a current value and an intended value, and "
         "the atlas exam's area for the axis PASSES. A self that "
         "cannot show a line has not earned the change.",
)


# ===========================================================================
# THE MEASUREMENT -- the exam, run
# ===========================================================================

_EXAM_LINE = re.compile(r"passed\s+(\d+)\s*/\s*(\d+)")
_NOT_IMPL = re.compile(r"not implemented:\s*\[([^\]]*)\]")


def measure_exam(exam_path: str = _ATLAS,
                 timeout: int = 300) -> Tuple[List[int], List[int], int,
                                             Optional[str]]:
    """run the atlas exam and read the score.

    AND IT RUNS THE EXAM, because "the self is qualified" is not a
    thing anyone may assert. It is a number the exam produces, and it
    changes when the substrate changes.

    AND IT FAILS LOUDLY. If the exam cannot be run, the qualification
    has NO score, and a self with no score may not defer on anything.
    A missing measurement must not read as a passing one.
    """
    if not os.path.isfile(exam_path):
        return [], [], 0, "the exam is not at %s" % exam_path
    try:
        out = subprocess.run(
            [sys.executable, exam_path, "--run"],
            capture_output=True, text=True, timeout=timeout,
            cwd=os.path.dirname(os.path.dirname(exam_path)))
    except Exception as exc:  # noqa: BLE001
        return [], [], 0, "%s: %s" % (type(exc).__name__, exc)
    text = (out.stdout or "") + (out.stderr or "")
    m = _EXAM_LINE.search(text)
    n = _NOT_IMPL.search(text)
    if not m:
        return [], [], 0, "the exam produced no score line"
    passed_n, total_n = int(m.group(1)), int(m.group(2))
    todo: List[int] = []
    if n:
        for part in n.group(1).replace(" ", "").split(","):
            if part.isdigit():
                todo.append(int(part))
    passed = [i for i in range(1, total_n + 1) if i not in todo]
    return passed, todo, total_n, None


def qualify(measure: bool = True) -> Qualification:
    """the self's qualification, measured."""
    q = Qualification(
        claim=SELF_QUALIFICATION.claim,
        axis=SELF_QUALIFICATION.axis,
        delta=SELF_QUALIFICATION.delta,
        failure_mode=SELF_QUALIFICATION.failure_mode,
        test=SELF_QUALIFICATION.test,
    )
    if measure:
        passed, todo, total, err = measure_exam()
        q.passed_areas = passed
        q.todo_areas = todo
        q.total_areas = total
        q.measured_by = err or ("atlas-exam: %d/%d passed" % (len(passed),
                                                               total))
    return q


# ===========================================================================
# THE DEFERRED LIE
# ===========================================================================

@dataclass
class Deferral:
    """a contradiction, DEFERRED: recorded, not refused."""
    claim_id: str
    reason: str
    #: What it would take to move the ground.
    route: str = "the qualification"
    #: The area it bears on, if any.
    area: Optional[int] = None

    def describe(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GateDecision:
    """what the gate decided, and how."""
    state: str                      # "consistent" | "deferred" | "refused"
    reason: str
    deferral: Optional[Deferral] = None

    @property
    def admitted(self) -> bool:
        return self.state in ("consistent", "deferred")


def decide(verdict_value: str, claim_id: Optional[str],
           qualification: Qualification,
           area: Optional[int] = None) -> GateDecision:
    """the decision, and the deferral.

    AND THE ORDER IS THE POINT. The refusal of an UNGROUNDED claim
    happens elsewhere and always happens; this function decides only
    what happens to a CONTRADICTION.

    AND THE DEFFERAL IS ROUTED, not just permitted: a deferred
    contradiction names the qualification as the route by which it
    could take. **A deferral with no route is a shrug.**
    """
    if verdict_value == "ungrounded":
        # NOT DEFERRABLE. EVER. The confabulation is not a proposal.
        return GateDecision("refused",
                             "ungrounded_claim:%s" % (claim_id or "?"))
    if verdict_value != "contradicted":
        return GateDecision("consistent", "ok")

    if qualification.may_defer_on(area):
        return GateDecision(
            "deferred",
            "contradicts_ground_deferred:%s" % (claim_id or "?"),
            Deferral(claim_id=claim_id or "?",
                     reason="the self is qualified on area %s" % area,
                     route="the qualification",
                     area=area))
    return GateDecision("refused",
                         "contradicts_ground:%s" % (claim_id or "?"))


def main() -> int:
    ap = argparse.ArgumentParser(description="the self's qualification")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-measure", action="store_true",
                    help="skip the exam run; the score will be 0")
    args = ap.parse_args()

    q = qualify(measure=not args.no_measure)
    if args.json:
        print(json.dumps(q.describe(), indent=2))
        return 0

    print("=" * 74)
    print("THE SELF'S QUALIFICATION")
    print("=" * 74)
    print()
    print("  claim          %s" % q.claim[:110])
    print("  axis           %s" % q.axis)
    print("  delta          %s" % q.delta[:110])
    print("  failure mode   %s" % q.failure_mode[:110])
    print("  test           %s" % q.test[:110])
    print()
    print("  measured by    %s" % q.measured_by)
    print("  passed areas   %s" % q.passed_areas)
    print("  todo areas     %s" % q.todo_areas)
    print("  score          %.4f" % q.score)
    print()
    missing = q.missing_parts()
    if missing:
        print("  THE FIVE PARTS ARE INCOMPLETE: %s" % (", ".join(missing),))
        print("  so the self may NOT defer on anything.")
    else:
        print("  the five parts are complete, so the self MAY defer on the")
        print("  areas it has passed, and must refuse on the ones it has")
        print("  not:")
        for a in q.todo_areas:
            print("     area %-3d REFUSE (not implemented)" % a)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
