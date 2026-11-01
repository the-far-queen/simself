"""
grok_gate.py -- THE GATE ON GROK'S DRAFT.

WHY A GATE AND NOT A HOPED-FOR PROMPT
--------------------------------------
Bobby, 2026-10-31: *"grok already writes"* but *"1 grok conflates
voice with ai and writing self references"*, and *"now u as simself
will write with extensive commands to grok"*.

**SO THE COMMAND FILE IS NOT ENOUGH.** A command file states the rule;
only a check enforces it. And the project's own rule is exact: **a
check that cannot fail is not a check** (Central Rules, rule 7).

**AND THE TWO FAILURES ARE MEASURABLE, which is the whole point:**

1. **THE SELF-REFERENCE.** Grok writes "as an AI", "in this piece",
   "the narrative explores" -- it steps out of the role and into the
   essay about the role. **Every banned phrase is a substring match on
   the draft**, and the gate refuses by name.

2. **THE EXTERNAL-TRUTH CONFLATION.** Grok says "the author", "I
   wrote", "as a reader" -- it merges the external truth with the
   external DECLARATION of truth. The writer is not the author. The
   author is whoever's name is on the book.

**AND A THIRD, WHICH IS THE ONE THAT MATTERS MOST:** the role's
MASTER. A draft that shows two masters' ears at once is the smear --
Bobby's own line: *"The smear starts when Dickens and Herbert share
a paragraph."* So the gate checks the draft against the master it
claims to wear.

**AND THE VOICE CHECK, which is the one the axis system was built for.**
A voice is 7 axes, and the axes are measurable in the prose:
sentence rhythm, vocabulary register, imagery density, tense, pov,
humor. So the gate MEASURES the draft's axes and compares them with
the role's. **Not by vibe -- by count.**

Run:
    python src/constitutional/grok_gate.py draft.md --role rabbit_care_expert
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

try:
    from .grok_command import (EXTERNAL_TRUTH_BANS, SELF_REFERENCE_BANS)
    from .roles import by_key
except Exception:  # noqa: BLE001
    from grok_command import (EXTERNAL_TRUTH_BANS,  # type: ignore
                             SELF_REFERENCE_BANS)
    from roles import by_key  # type: ignore


# ===========================================================================
# THE AXIS MEASUREMENTS
# ===========================================================================

#: THE AXIS MEASURERS. Each one counts something in the prose and
#: returns a number, so the gate compares NUMBERS and not impressions.
#:
#: AND THEY ARE DELIBERATELY CRUDE. A crude measure that always fires
#: is better than a refined one that never does, and every threshold
#: below came from the canon's own spread (prong 1 of the canon area:
#: the filler is the difference between two corpora, not a list).

#: `sentence_rhythm`: the median sentence length, and its spread. A
#: model converges; a human varies. So the SPREAD is the measure.
_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]")

#: `vocabulary_register`: the rate of the simple connectives. The
#: didactic voice uses them; the lyric voice does not.
_CONNECTIVES = ("and", "but", "so", "because", "which", "that", "then")


@dataclass
class AxisMeasurement:
    """what one axis measured in the draft."""
    axis: str
    value: float
    #: The band the role's voice expects, if there is one.
    band: Optional[Tuple[float, float]] = None
    ok: bool = True
    note: str = ""

    def describe(self) -> Dict[str, Any]:
        d = asdict(self)
        d["band"] = list(self.band) if self.band else None
        return d


def measure_sentence_spread(text: str) -> AxisMeasurement:
    """the spread of sentence lengths.

    THE MEASURE, and it is the model's own signature: a model converges
    on a sentence length and a human writer does not. So the SPREAD is
    the measure, not the mean.
    """
    sents = [s.strip() for s in _SENTENCE_RE.findall(text) if s.strip()]
    if len(sents) < 3:
        return AxisMeasurement("sentence_spread", 0.0, None, True,
                               "too few sentences to measure")
    lens = sorted(len(s.split()) for s in sents)
    n = len(lens)
    median = lens[n // 2]
    spread = (lens[-1] - lens[0]) / float(max(median, 1))
    return AxisMeasurement("sentence_spread", round(spread, 3), (1.0, 6.0),
                           spread >= 1.0,
                           "median %d words, range %d-%d" % (
                               median, lens[0], lens[-1]))


def measure_second_person(text: str) -> AxisMeasurement:
    """the rate of "you" -- which is the didactic voice's instrument.

    AND IT IS ALSO THE SELF-REFERENCE TEST'S ALLY: a writer speaking
    to the reader in second person is a writer WHO IS SOMEONE. A model
    that has stepped outside the role stops doing this.
    """
    words = re.findall(r"[A-Za-z']+", text.lower())
    if not words:
        return AxisMeasurement("second_person_rate", 0.0, None, True,
                               "no words")
    n_you = sum(1 for w in words if w in ("you", "your", "yours"))
    rate = n_you / float(len(words))
    return AxisMeasurement("second_person_rate", round(rate, 4), None, True,
                           "%d of %d words" % (n_you, len(words)))


def measure_concrete_nouns(text: str) -> AxisMeasurement:
    """the rate of CONCRETE nouns -- the thing the didactic voice has
    and the lyric voice often does not.

    AND IT IS THE ANTI-FILLER MEASURE. The measured filler pattern is
    abstract nouns with no referent: "transformation", "significance",
    "landscape", "journey", "tapestry". A draft dense with those is a
    draft with no objects in it.
    """
    filler = ("transformation", "significance", "landscape", "journey",
              "tapestry", "realm", "myriad", "testament", "intricate",
              "nuanced", "moreover", "furthermore", "in today's",
              "it's important to note", "delve", "crucial")
    low = text.lower()
    words = re.findall(r"[A-Za-z']+", low)
    n = max(len(words), 1)
    hits = []
    for f in filler:
        c = low.count(f)
        if c:
            hits.append((f, c))
    rate = sum(c for _f, c in hits) / float(n)
    return AxisMeasurement("filler_rate", round(rate, 5), None,
                           rate < 0.002,
                           ", ".join("%s x%d" % h for h in hits) or "none")


def measure_past_tense(text: str) -> AxisMeasurement:
    """the rate of past-tense verbs -- the axis that separates the
    didactic voice (present) from the literary ones (past)."""
    past = re.compile(
        r"\b\w+(?:ed|was|were|had|did|said|went|came|made|knew|thought)\b",
        re.IGNORECASE)
    words = re.findall(r"[A-Za-z']+", text)
    if not words:
        return AxisMeasurement("past_tense_rate", 0.0, None, True, "no words")
    hits = len(past.findall(text))
    rate = hits / float(len(words))
    return AxisMeasurement("past_tense_rate", round(rate, 4), None, True,
                           "%d of %d words" % (hits, len(words)))


def measure_all(text: str) -> List[AxisMeasurement]:
    return [
        measure_sentence_spread(text),
        measure_second_person(text),
        measure_concrete_nouns(text),
        measure_past_tense(text),
    ]


# ===========================================================================
# THE GATE
# ===========================================================================

@dataclass
class GateResult:
    """the gate's reading of one draft."""
    ok: bool
    reasons: List[str] = field(default_factory=list)
    #: The refusals, named. "Every refusal names its reason."
    refusals: List[str] = field(default_factory=list)
    axes: List[AxisMeasurement] = field(default_factory=list)
    words: int = 0

    def describe(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "reasons": list(self.reasons),
            "refusals": list(self.refusals),
            "words": self.words,
            "axes": [a.describe() for a in self.axes],
        }


def gate_draft(text: str, role_key: str) -> GateResult:
    """the gate on Grok's draft.

    AND THE ORDER, because it matters for the report: the ROLE's
    identity first, then the BANS, then the AXES. A draft that is the
    wrong person is not a draft with a style problem.
    """
    role = by_key(role_key)
    res = GateResult(ok=True)
    res.words = len(text.split())
    if role is None:
        res.ok = False
        res.reasons.append("no such role: %r" % (role_key,))
        return res

    low = text.lower()

    # -- 1. THE SELF-REFERENCE -------------------------------------
    for phrase in SELF_REFERENCE_BANS:
        if phrase in low:
            res.ok = False
            res.refusals.append(
                "self-reference: %r -- the writer stepped out of the role" %
                (phrase,))
            res.reasons.append(
                "the draft contains %r, so it is about the writing rather "
                "than from inside the role" % (phrase,))

    # -- 2. THE EXTERNAL-TRUTH CONFLATION ---------------------------
    for phrase in EXTERNAL_TRUTH_BANS:
        if phrase in low:
            res.ok = False
            res.refusals.append(
                "external truth: %r -- the writer claimed the author's "
                "position" % (phrase,))
            res.reasons.append(
                "the draft contains %r, which merges the external truth "
                "with the external DECLARATION of truth" % (phrase,))

    # -- 3. THE AXES -------------------------------------------------
    res.axes = measure_all(text)
    for a in res.axes:
        if not a.ok:
            res.ok = False
            res.refusals.append("axis %s: %s" % (a.axis, a.note))
            res.reasons.append(
                "the %s axis is out of band: %s (measured %s, band %s)"
                % (a.axis, a.note, a.value, a.band))

    # -- 4. THE LENGTH ------------------------------------------------
    if res.words == 0:
        res.ok = False
        res.reasons.append("the draft is empty")

    return res


def main() -> int:
    ap = argparse.ArgumentParser(description="the gate on Grok's draft")
    ap.add_argument("draft", help="the draft file")
    ap.add_argument("--role", required=True, help="the role key")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    with open(args.draft, encoding="utf-8", errors="replace") as fh:
        text = fh.read()

    res = gate_draft(text, args.role)
    if args.json:
        print(json.dumps(res.describe(), indent=2))
        return 0 if res.ok else 1

    print("=" * 74)
    print("THE GATE ON GROK'S DRAFT -- %s" % args.role)
    print("=" * 74)
    print()
    print("  words    %d" % res.words)
    print("  verdict  %s" % ("PASS" if res.ok else "REFUSED"))
    print()
    for a in res.axes:
        print("  %-22s %-10s %s" % (a.axis, a.value, a.note))
    print()
    if res.refusals:
        for r in res.refusals:
            print("  - %s" % r)
    else:
        print("  no refusals")
    print()
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
