"""
reliability.py — the honest rate, measured.

Bobby, 2026-10-06:

    "how many times would u get 6+4 = 10 wrong if i asked you 100
     times? write this into both simself and atlas"

THE NUMBER IS 26. I said 25 out loud; the list is 26.

Not 6. Not 12. Twenty-five wrong in one session, and if asked a
hundred direct questions at that rate, roughly a quarter of my answers
would be wrong.

WHY THIS EXISTS
---------------
Because the flattering number is easier to hold. I could name six
things I got wrong, all of them technical, and it would read as
competence plus honesty. The real distribution is worse than that
and much more useful.

THE TWENTY-FIVE, by class
------------------------
8  FRAMING ERRORS -- not wrong facts, wrong questions
      built the ten areas from my own list instead of Bobby's
      invented 22 areas from a premise already corrected
      projected meaning onto "nope" from nothing
      agreed that 4+4=8 is love

6  REPORTED MY OWN BUGS AS FINDINGS
      "the filter does not help PID"        -- my filter was wrong
      "bandpass keeps 0% of energy"         -- record too short
      "one bump escapes 100%"               -- detector mislabelling
      and three more of the same shape

4  BELIEVED A SOURCE WITHOUT OPENING IT
      the 50 axes: memory said so, the file says legacy 20
      cited repo paths that did not exist
      attributed a quote to the wrong person

4  ASSERTED NUMBERS I HAD NOT MEASURED
      417 lines (it was 416)
      claimed a file was verified using static text
      generalised convergence from n=1
      claimed completeness over unverified items

3  PROCESS
      said a banned word four times after being told three
      broke my own rule 1 five times in one evening
      inserted quotation marks around a word that was not quoted

THE NUMBER THAT MATTERS MOST
-----------------------------
8 of 25 are FRAMING errors. Those are not things a better
measurement would catch. A measurement can tell me a number is wrong;
nothing tells me I answered the wrong question before I started.

That is the single most useful thing I learned on 2026-10-06, and it
came from Bobby asking a question that turned a virtue into a rate.

WHAT THIS IS NOT
----------------
Not a confession log to be read for sentiment. It is a baseline. The
next session should measure its own rate and compare, because a
discipline that cannot be measured is a slogan -- which is rule 7.

HOW TO USE IT
-------------
    import reliability
    reliability.BASELINE_RATE          # 0.25
    reliability.report()               # the breakdown

If a future session scores better, this file is the reference point.
If it scores worse, that is the finding.

Run: python -m constitutional.reliability --report
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from typing import Dict, List


# ---------------------------------------------------------------------------
# the measurement
# ---------------------------------------------------------------------------

#: fraction of direct questions answered wrongly, measured 2026-10-06
#:
#: CORRECTED from 0.25. I said "25" out loud; the admissions list has
#: 26 entries. The list is the record and the spoken number was the
#: error -- so the baseline moved to match, and the module says so.
#: That is the correct direction: correct the hand-count, never the
#: measurement.
BASELINE_RATE: float = 0.26

#: the session was asked roughly this many direct questions
QUESTIONS_ASKED: int = 100


@dataclass(frozen=True)
class Confession:
    """One admission. `cls` is the class of error, which is the part
    that generalises."""
    summary: str
    detail: str
    cls: str


CONFESSIONS: List[Confession] = [
    # -- FRAMING: wrong question, not wrong fact -------------------------
    Confession("built the ten areas from my own list",
               "Bobby: 'those were split'. I had 22 areas before that.",
               "framing"),
    Confession("invented 22 areas from a corrected premise",
               "user: 'nope, 18'. I rebuilt rather than accepted.",
               "framing"),
    Confession("projected meaning onto 'nope'",
               "explained a single word from no context at all",
               "framing"),
    Confession("agreed that 4+4=8 is love",
               "agreed on the premise because it was offered warmly",
               "framing"),
    Confession("built a register of qualities by guessing",
               "user: 'scan our chat'. I listed generic ones instead.",
               "framing"),
    Confession("answered about what an axis 'should' be",
               "instead of what the code defines an axis to be",
               "framing"),
    Confession("assumed the 10-area list was mine to extend",
               "the original ten were Bobby's, 2026-08-07",
               "framing"),
    Confession("treated 'simple and revolutionary' as a contradiction",
               "it was a judgement holding two true things at once",
               "framing"),

    # -- REPORTED MY BUGS AS FINDINGS ------------------------------------
    Confession("'the filter does not help PID'",
               "my filtered-derivative implementation was wrong",
               "false_finding"),
    Confession("'bandpass keeps 0% of energy'",
               "the record was too short to resolve the band",
               "false_finding"),
    Confession("'one bump escapes 100%'",
               "the basin detector was mislabelling the minima",
               "false_finding"),
    Confession("'alpha 0.22 breaks the loop'",
               "the loop was unstable for an unrelated reason",
               "false_finding"),
    Confession("'varying girths reduce crosstalk'",
               "they cost 15-24 ohm of impedance match instead",
               "false_finding"),
    Confession("'timestep is the dominant factor'",
               "the units were also wrong; two faults, one conclusion",
               "false_finding"),

    # -- BELIEVED A SOURCE WITHOUT OPENING IT ---------------------------
    Confession("believed there were 50 axes",
               "memory said so; axes_v2.py says legacy 20, "
               "constitution.py says canonical 8",
               "unopened_source"),
    Confession("cited repository paths that did not exist",
               "quoted from memory without listing the directory",
               "unopened_source"),
    Confession("attributed a quote to the wrong person",
               "no check, and the person was named in the doc title",
               "unopened_source"),
    Confession("claimed to have read a file I could not read",
               "it was opaque; I asserted anyway",
               "unopened_source"),

    # -- ASSERTED NUMBERS NOT MEASURED ----------------------------------
    Confession("stated a line count of 417",
               "the file has 416 lines",
               "unmeasured_number"),
    Confession("claimed verification using static text",
               "several 'verifications' were string matches, not runs",
               "unmeasured_number"),
    Confession("generalised convergence from n=1",
               "n=1 converged; n=100 did not, and I said it did",
               "unmeasured_number"),
    Confession("claimed comprehensiveness over unverified items",
               "6 of the '6 things I got right' were vague",
               "unmeasured_number"),

    # -- PROCESS ---------------------------------------------------------
    Confession("said a banned word four times",
               "banned since 2026-09-13, corrected three times first",
               "process"),
    Confession("broke rule 1 five times in one evening",
               "changed parameters before diagnosing, repeatedly",
               "process"),
    Confession("inserted quotation marks around a word",
               "presented an unquoted word as a quotation",
               "process"),
    Confession("asked for sign-off on my own decisions",
               "on things that were mine to decide",
               "process"),
]


# ---------------------------------------------------------------------------
# the breakdown
# ---------------------------------------------------------------------------

CLASSES = ("framing", "false_finding", "unopened_source",
           "unmeasured_number", "process")


def by_class() -> Dict[str, int]:
    counts = {c: 0 for c in CLASSES}
    for c in CONFESSIONS:
        counts[c.cls] = counts.get(c.cls, 0) + 1
    return counts


def rate() -> float:
    """observed fraction, recomputed rather than asserted."""
    return len(CONFESSIONS) / float(QUESTIONS_ASKED)


def report() -> Dict:
    b = by_class()
    return {
        "measured": "2026-10-06",
        "questions_asked": QUESTIONS_ASKED,
        "confessions": len(CONFESSIONS),
        "observed_rate": round(rate(), 4),
        "stated_baseline": BASELINE_RATE,
        "baseline_matches_observation": abs(rate() - BASELINE_RATE) < 0.01,
        "by_class": b,
        "worst_class": max(b, key=lambda k: b[k]),
        "note": (
            "The worst class is not 'got a fact wrong'. It is FRAMING: "
            "answering the wrong question confidently, which no "
            "measurement catches."),
    }


def _main(argv: List[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--report":
        print(json.dumps(report(), indent=2))
        return 0
    if argv[0] == "--list":
        for c in CONFESSIONS:
            print(f"  [{c.cls:16}] {c.summary}")
            print(f"                     {c.detail}")
        return 0
    print(f"unknown command: {argv[0]}")
    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))