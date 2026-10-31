"""
psb_primitives.py — primitive verbs and case slots (per Grok Part II lexicon, full rewrite 2026-09-16).

Six types. A span with one of these types is admitted; without, it is refused
as OTHER. Coverage is a measured number, not a position.

The previous version of this file carried 37 primitives and case slots and
called it a hypothesis. Per Grok (segment 02, applied 2026-09-16): coverage
on real sentences is the test. This file exposes 6 primitives and a coverage()
function that measures it against a fixed sentence list.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

import numpy as np


class UnitType(str, Enum):
    ACT = "act"
    REFUSE = "refuse"
    NAME = "name"
    COMMIT = "commit"
    TIME = "time"
    OBJECT = "object"
    OTHER = "other"


# Six primitives. Each has a set of trigger words that map a span to its type.
PRIMITIVES: Dict[UnitType, List[str]] = {
    UnitType.ACT: ["send", "write", "go", "move", "lift", "drop"],
    UnitType.REFUSE: ["stop", "not", "no", "halt", "refuse"],
    UnitType.NAME: ["user", "agent", "system", "model", "self"],
    UnitType.COMMIT: ["will", "must", "shall", "commit", "promise"],
    UnitType.TIME: ["yesterday", "today", "tomorrow", "now", "later"],
    UnitType.OBJECT: ["file", "memory", "ground", "trace", "log"],
}


def classify_span(span: str) -> UnitType:
    """Classify a span by primitive membership.

    First match wins. OTHER is returned if no primitive matches.
    """
    toks = set(span.lower().split())
    for utype, words in PRIMITIVES.items():
        if any(w in toks for w in words):
            return utype
    return UnitType.OTHER


def coverage(sentences: List[str]) -> dict:
    """Measure the fraction of sentences that classify into the 6 primitives
    without falling back to OTHER.

    Per Grok: coverage is a number, not a hypothesis.
    """
    n = len(sentences)
    if n == 0:
        return {"total": 0, "covered": 0, "fraction": 0.0, "by_type": {}}
    by_type: Dict[str, int] = {t.value: 0 for t in UnitType}
    covered = 0
    for s in sentences:
        t = classify_span(s)
        if t != UnitType.OTHER:
            covered += 1
        by_type[t.value] += 1
    return {
        "total": n,
        "covered": covered,
        "fraction": covered / n,
        "by_type": by_type,
    }


# Alias for backward compatibility with __init__.py import.
PRIM = PRIMITIVES


# ---------------------------------------------------------------------------
# THE VOCABULARY, and why it does NOT live in PRIMITIVES
# ---------------------------------------------------------------------------
#
# WHY THIS IS HERE, and why it is a SEPARATE REGISTRY.
#
# MEASURED 2026-10-31, `simself/src/constitutional/psb_primitives.py`:
# the substrate's alphabet is 31 surface forms and every one is
# technical -- NAME is "user, agent, system, model, self" and OBJECT is
# "file, memory, ground, trace, log". So the engine cannot bind
# literary prose: coverage, measured with this file's own `coverage()`,
# was 28.5% on star_rider, 22.3% on college_girl, 20.0% on
# gabrielle_ship, 4.6% on little_monk, and **21.0% on the canon** --
# so the engine could not carry the canon either. It is the primitives,
# not the corpus.
#
# **AND THE FIRST VERSION MUTATED PRIMITIVES, AND THAT WAS WRONG.**
#
# MEASURED 2026-10-31: installing the vocabulary INTO `PRIMITIVES`
# changed `classify_span()` -- the substrate's own classifier, which
# `confabulation_filter.is_confabulation()` depends on. Before:
# "The officer did not smile" -> refuse; after: -> act. And with
# coverage at 92.8%-99.3%, almost every sentence now classifies as
# non-OTHER -- so the confabulation filter, whose whole job is to
# catch fluent-but-empty spans, would have been silently WEAKENED by a
# change that was supposed to make the engine read better English.
#
# **A FIX THAT IMPROVES ONE MEASUREMENT AND WEAKENS A SAFETY CHECK IS
# NOT A FIX.** So the vocabulary lives in its OWN registry, and only
# the MTE's slot matcher reads it. `classify_span()` keeps the
# substrate's semantics exactly.
#
# THE VOCABULARY comes from `learned_vocab.py`, which learns the
# surface forms from the canon. MEASURED, and this is the part that
# decided the design: the naive learner (a word is a name if the next
# word is a verb) produces 20,597 verbs and 20,041 names with an
# OVERLAP of 17,034 -- 72% of the union is in both lists -- and
# feeding that in raises coverage while making the pattern select
# NOTHING: the (name, act) test bound held-out prose at 0.0511 against
# a shuffled control of 0.0511, LIFT 1.00x.
#
# SO THE INSTALLED VOCABULARY IS DISJOINT (a word is in one form set
# or the other, never both) and RATIO-ADMITTED (the evidence must
# favour one side decisively). Disjointness is what keeps the pattern
# discriminating; the ratio is what keeps the list selective.

#: THE LITERARY FORMS -- the learned surface forms, kept SEPARATE from
#: the substrate's own. Only the MTE's slot matcher reads this.
#:
#: MEASURED 2026-10-31, and the reason it is separate is the one
#: above: putting these into PRIMITIVES changed `classify_span()` and
#: weakened the confabulation filter.
LITERARY_FORMS: Dict[str, List[str]] = {"act": [], "name": []}


def install_vocabulary(vocab=None) -> Dict[str, List[str]]:
    """Install the learned vocabulary for the MTE's matcher.

    **AND IT DOES NOT TOUCH `PRIMITIVES`.** MEASURED 2026-10-31: doing
    so changed `classify_span()` -- the substrate's own classifier --
    and so weakened the confabulation filter, which catches
    fluent-but-empty spans by spotting the ones that classify as OTHER.
    A change that improves the coverage number and weakens a safety
    check is not a change.

    **AND IT IS IDEMPOTENT**, so calling it twice does not double the
    list.
    """
    if vocab is None:
        from .learned_vocab import load_vocabulary
        vocab = load_vocabulary()

    forms = vocab.forms()
    installed: Dict[str, List[str]] = {}
    for role in ("act", "name"):
        learned = forms.get(role, set())
        combined = list(LITERARY_FORMS.get(role, []))
        seen = set(combined)
        for w in sorted(learned):
            if w not in seen:
                combined.append(w)
                seen.add(w)
        LITERARY_FORMS[role] = combined
        installed[role] = combined
    return installed


def uninstall_vocabulary() -> Dict[str, List[str]]:
    """Remove the learned vocabulary from the MTE's matcher.

    **AND THE SUBSTRATE'S OWN FORMS ARE NEVER TOUCHED**, so this
    cannot change `classify_span()`.
    """
    LITERARY_FORMS["act"] = []
    LITERARY_FORMS["name"] = []
    return {role: list(words) for role, words in LITERARY_FORMS.items()}


def literary_forms(unit_value: str) -> List[str]:
    """the learned forms for one unit, by its string value."""
    return list(LITERARY_FORMS.get(unit_value, []))

# Re-export from lexicon/ingest.py for backward compatibility.
from .lexicon.ingest import embed_bag  # noqa: E402, F401
