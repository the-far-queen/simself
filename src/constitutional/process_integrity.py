"""
process_integrity.py — area 0, living inside simself.

INDEPENDENT OF ATLAS-EXAM, BY DESIGN.

atlas-exam is a separate repo that POINTS AT this one. It cannot import
simself -- by architecture, so that a bug in simself cannot become a
passing grade in the exam. So the check cannot live there and be
trusted to be running.

This module is the same rule, enforced locally, with no dependency on
anything outside this repository except the standard library.

THE FAILURE THIS EXISTS FOR
---------------------------
2026-10-06. On a PID loop I made five consecutive attempts -- change the
plant model, change the gains, change the plant model again, add a
"filter" -- without once asking whether my own arithmetic was wrong. A
five-line trace would have shown the derivative term spiking on the
first run. It was in my hand the whole time.

    substituting a plausible next attempt
        for a check on the current one

Three times in that session I reported a surprising result as a finding
when it was my own bug:

    "the filter does not help PID"  -> my filtered derivative was wrong
    "bandpass keeps 0% of energy"   -> record too short to resolve
    "one bump escapes 100%"         -> the detector was mislabelling

THE SEVEN RULES
---------------
1  diagnose before adjusting  -- run it AS-IS, read the output, BEFORE
                                 changing a parameter
2  instrument before adjusting -- trace first, then act
3  no number without the command that produced it, run AFTER the change
4  surprising result = suspect MY code first
5  two derivations must agree   -- if they disagree, one is wrong;
                                 find which before reporting either
6  stability is a basin, not a knife edge -- sweep it
7  a test that cannot fail is not a test -- mutation-test every claim

WHAT THIS MODULE CAN AND CANNOT DO
----------------------------------
It CAN establish that the rules are written, that this module exists,
and that the checks below pass.

It CANNOT establish that the process was followed. That is not
measurable from inside the run that followed it. Stated here rather
than implied, because a check that claims more than it delivers is the
exact defect this area is about.

Run: python -m constitutional.process_integrity --check
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
if SRC not in sys.path:
    sys.path.insert(0, SRC)

RULES_FILENAME = "CENTRAL-RULES.md"


@dataclass
class Rule:
    """One rule, with the failure it prevents."""
    number: int
    title: str
    rule: str
    prevents: str


RULES: List[Rule] = [
    Rule(1, "diagnose before adjusting",
         "Run it as-is and read the output BEFORE changing a parameter.",
         "Changing plant, then gains, then plant again -- five attempts "
         "on one PID loop without asking whether my arithmetic was "
         "wrong."),
    Rule(2, "instrument before adjusting",
         "Print the trace and inspect intermediate state before acting.",
         "Inverting diagnose/adjust four times in a row."),
    Rule(3, "no number without its command",
         "Every figure carries the command that produced it, run AFTER "
         "the change.",
         "Quoting a number measured before the fix it was supposed to "
         "justify."),
    Rule(4, "surprising result means my code is wrong",
         "When a result contradicts expectation, suspect the code "
         "first. Not 'this is a finding'.",
         "Reporting 'the filter does not help PID' when the filter was "
         "coded wrong."),
    Rule(5, "two derivations must agree",
         "Derive the same quantity two independent ways. Disagreement "
         "means one is wrong; find which before reporting either.",
         "Reporting one method's output when a second method would "
         "have contradicted it."),
    Rule(6, "stability is a basin",
         "Sweep it. A result that works at exactly one parameter "
         "setting is not a result.",
         "A loop that only locked in one knife-edge regime, which "
         "should have revealed the plant model was wrong."),
    Rule(7, "a test that cannot fail is not a test",
         "Mutation-test every claim. Show it going red.",
         "23 self-scoring exam items reporting 15/27 while reacting to "
         "nothing."),
]


REPO_ROOT = os.path.dirname(SRC)


def rules_path() -> str:
    """where CENTRAL-RULES.md is expected.

    DIAGNOSIS, recorded because getting this wrong on the first run is
    exactly the shape of failure these rules exist to stop: I wrote
    os.path.join(SRC, "docs", ...) where SRC is .../simself/src, so it
    searched src/docs/ and reported the file missing. The file was
    there the whole time at the repo root. I looked at the PATH, not
    at the filesystem.

    A check that fails must first be believed, not tuned.
    """
    return os.path.join(REPO_ROOT, "docs", RULES_FILENAME)


def check(verbose: bool = False) -> Dict:
    """Run the checks. Returns a verdict; never raises."""
    path = rules_path()
    exists = os.path.isfile(path)
    size = os.path.getsize(path) if exists else 0

    checks = {
        "module_present": os.path.isfile(__file__),
        "rules_file_present": exists,
        "rules_file_non_trivial": size > 1500,
        "seven_rules_declared": len(RULES) == 7,
        "every_rule_states_what_it_prevents":
            all(r.prevents.strip() for r in RULES),
        "every_rule_states_its_limit_or_reason":
            all(len(r.rule) > 30 for r in RULES),
    }
    bad = [k for k, v in checks.items() if not v]

    result = {
        "area": "process_integrity",
        "location": "simself/src/constitutional/process_integrity.py",
        "independent_of_atlas_exam": True,
        "rules_file": path,
        "rules_file_bytes": size,
        "checks": checks,
        "failed": bad,
        "verdict": "PASS" if not bad else "FAIL",
        "does_not_establish": (
            "that the process was FOLLOWED. it establishes only that "
            "the rules are written and these checks pass. compliance is "
            "not measurable from inside the run that followed it."
        ),
        "rules": [{"n": r.number, "title": r.title, "rule": r.rule}
                  for r in RULES],
    }
    if verbose and not bad:
        print("\n  the seven rules:")
        for r in RULES:
            print(f"\n  {r.number}. {r.title}")
            print(f"     {r.rule}")
            print(f"     prevents: {r.prevents}")
    return result


def passed() -> bool:
    return check()["verdict"] == "PASS"


def _main(argv: List[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    verbose = "--verbose" in argv or "-v" in argv
    res = check(verbose=verbose)
    print(json.dumps(res, indent=2))
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))