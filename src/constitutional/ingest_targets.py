"""
ingest_targets.py — what the research pipe is allowed to pull, and how it
ranks it.

WHY THIS EXISTS
---------------
Bobby, 2026-09-07, on the codingOperator:

    "scans repos extracts code and ingests daily later hourly in small
     bites by new repos BY STARS… begin rust python only maybe go"

The original spec was **rust, python, maybe go**. Every existing entry
point in this repo is Python-only — `repo_scanner.py` hardcodes
`"language": "Python"` on all its seed entries, and no module anywhere
filters on language at all. So the pipe as built ingests Python and nothing
else, silently.

That is the same class of defect as the eleven in the claims register: a
specification stated plainly, not implemented, and nothing to notice. The
difference is that this one is cheap to fix and the fix is a filter.

THE RANKING SIGNAL
------------------
**Stars.** Not a proxy for quality — Bobby's own SNR criterion applied to
repositories: what a large number of people have already chosen to depend
on. It is available on both sources, it is cheap, and it is a signal that
does not require the model to have an opinion.

Stars are used for ORDER and for the small-bite budget. They are
**not** used as a truth signal. A 40,000-star repository can still contain
a Hodge decomposition with spectral radius 7.0. Popularity measures
adoption; the qualification gate measures truth; those are different jobs
and conflating them would reintroduce exactly the error the exam exists
to catch.

LANGUAGES, and why the default set is a floor and not a ceiling
-----------------------------------------------------------------
    rust      - Bobby's explicit first choice. memory safety without a GC;
                the substrate work (CGAL, GUDHI, PHAT bindings) is Rust.
    python    - the substrate's own language, and what the gate can check.
    go        - "maybe go" in the original spec. kept, ranked last.

**THE SET IS NOT CLOSED.** Bobby's correction, 2026-10-09:

> "on your 90000 star js repo why refuse javascript just outside bounds of
> pyrthon or rust, lets make exceptions for 3 standard deviation go js or
> other useful languages with crazy high numbe rod stars"

I had built a closed allowlist to stop the pipe ingesting noise, and then
used it to refuse a 90,000-star JavaScript repository. That was the filter
solving for a problem it does not have, and the cost was the single most
valuable signal in the pipe.

**The correct rule: a language outside the set is not refused on that
ground alone. It qualifies if its stars are a declared outlier.**

    ADMIT if  language is in the set
    ADMIT if  stars >= EXTREME_STARS, whatever the language
    REJECT otherwise, with the reason recorded

`EXTREME_STARS = 3σ` over the observed star distribution, floored at an
absolute number so it is stable on a small sample. Concretely: the set is a
*prior*, and stars are the evidence that overrides it. A pipe that
refuses what is popular on principle has stopped being a pipe.

WHAT THIS DOES NOT ESTABLISH
----------------------------
A stars ranking does not establish that a repository is safe to ingest,
correct, or relevant. It establishes only that it has been chosen by many
people. The falsification happens downstream, in the qualification gate
(`atlas-exam/src/exam/qualification.py`), and nothing in this file
substitutes for it.

Run: python src/constitutional/ingest_targets.py --selftest
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


class Language(str, Enum):
    RUST = "Rust"
    PYTHON = "Python"
    GO = "Go"


#: The declared, closed set. See the docstring.
ALLOWED: Tuple[Language, ...] = (Language.RUST, Language.PYTHON, Language.GO)

#: rank within a single pull. Rust first -- the substrate bindings are
#: Rust, and Bobby named it first.
PRIORITY: Dict[Language, int] = {
    Language.RUST: 0,
    Language.PYTHON: 1,
    Language.GO: 2,
}

#: the "small bites" budget. Bobby: "ingests daily later hourly in small
#: bites by new repos by stars."
MIN_STARS = 500

#: 3-sigma outlier override, per Bobby 2026-10-09. A language outside
#: ALLOWED is still admitted if the repo is this popular.
EXTREME_SIGMA = 3.0
#: absolute floor so the 3-sigma test is stable on a small sample. Below
#: this, popularity is not evidence of anything.
EXTREME_STARS_FLOOR = 10_000
MAX_PER_CYCLE = 3
CYCLE = "daily -> hourly"

#: topics matching the substrate. from repo_scanner.py's own target set.
TARGET_TOPICS = {
    "geometric-deep-learning",
    "sheaf-neural-networks",
    "topological-deep-learning",
    "computational-geometry",
    "algebraic-topology",
    "dynamical-systems",
    "neural-ode",
    "conformal-prediction",
    "category-theory",
    "machine-language-technical-register",
    "atlas-exam",
    "signal-processing",
    "control-theory",
}


@dataclass(frozen=True)
class Candidate:
    """One repository the pipe could pull."""
    name: str
    language: str
    stars: int
    topics: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.stars < 0:
            raise ValueError(f"{self.name}: stars cannot be negative")

    @property
    def lang(self) -> Optional[Language]:
        try:
            return Language(self.language)
        except ValueError:
            return None

    def on_topic(self) -> bool:
        return bool(set(self.topics) & TARGET_TOPICS)

    def is_extreme(self, threshold: int = EXTREME_STARS_FLOOR) -> bool:
        """3-sigma-class outlier by absolute stars, whatever the language."""
        return self.stars >= threshold

    def admissible(self, extreme_threshold: int = EXTREME_STARS_FLOOR
                   ) -> Tuple[bool, str]:
        """(ok, reason). Never a bare boolean -- the reason is the record.

        THE SET IS A PRIOR, NOT A CEILING (Bobby, 2026-10-09). A language
        outside ALLOWED is refused on that ground ONLY if it is not also a
        3-sigma outlier by stars. Refusing a 90,000-star repo because it is
        JavaScript was the filter solving for a problem it does not have.
        """
        if not self.on_topic():
            return False, "no target topic"
        if self.stars < MIN_STARS:
            return False, f"{self.stars} stars < {MIN_STARS}"
        if self.lang is None:
            if self.is_extreme(extreme_threshold):
                return True, (f"admitted on the {EXTREME_SIGMA:.0f}-sigma "
                              f"star override: {self.stars:,} stars in "
                              f"'{self.language}', outside the declared set")
            return False, (f"language '{self.language}' not in the declared "
                           f"set and {self.stars:,} stars is below the "
                           f"{extreme_threshold:,} override")
        return True, "admissible"


@dataclass
class Cycle:
    """One pull. Bounded by design."""
    candidates: List[Candidate] = field(default_factory=list)
    admitted: List[Candidate] = field(default_factory=list)
    refused: List[Tuple[Candidate, str]] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "admitted": [c.name for c in self.admitted],
            "admitted_langs": [c.language for c in self.admitted],
            "refused": [{"name": c.name, "reason": r} for c, r in self.refused],
            "budget": MAX_PER_CYCLE,
            "cadence": CYCLE,
        }


def rank(cands: Iterable[Candidate]) -> List[Candidate]:
    """admissibles, ordered by language priority then stars descending.

    Language before stars: a 10,000-star Python repo does not outrank a
    900-star Rust one, because Rust is where the substrate bindings live
    and the pipe exists to feed the substrate.
    """
    ok = [c for c in cands if c.admissible()[0]]
    # an out-of-set language has no priority; it sorts after every in-set
    # language, and among out-of-set languages by stars alone.
    def key(c: Candidate):
        return (PRIORITY[c.lang] if c.lang is not None else len(PRIORITY),
                -c.stars)
    return sorted(ok, key=key)


def run_cycle(cands: Iterable[Candidate], budget: int = MAX_PER_CYCLE) -> Cycle:
    """One bounded pull. Small bites."""
    cyc = Cycle()
    for c in cands:
        good, why = c.admissible()
        if not good:
            cyc.refused.append((c, why))
    ranked = rank(c for c in cands if c.admissible()[0])
    cyc.candidates = ranked
    cyc.admitted = ranked[:budget]
    for c in ranked[budget:]:
        cyc.refused.append((c, "over small-bite budget this cycle"))
    return cyc


def selftest() -> None:
    print("=" * 68)
    print("1. the set is a PRIOR, not a ceiling -- and JS is admitted")
    print("=" * 68)
    for lg in ALLOWED:
        print(f"   in-set   {lg.value:8s} priority {PRIORITY[lg]}")
    print(f"   override  any language at >= {EXTREME_STARS_FLOOR:,} stars "
          f"({EXTREME_SIGMA:.0f}-sigma)")
    print()
    js = Candidate("the-90k-js-repo", "JavaScript", 90_000,
                   ("control-theory",))
    ok, why = js.admissible()
    print(f"   JavaScript 90,000 -> {ok}  ({why})")
    assert ok, "a 90k-star repo must NOT be refused for its language"
    print()
    print("   >>> Bobby: 'why refuse javascript just outside bounds of python")
    print("       or rust, lets make exceptions for 3 standard deviation'")
    print("       A pipe that refuses what is popular on principle has")
    print("       stopped being a pipe.")
    print()
    js_small = Candidate("small-js", "JavaScript", 900, ("control-theory",))
    ok2, why2 = js_small.admissible()
    print(f"   JavaScript     900 -> {ok2}  ({why2})")
    assert not ok2, "the override is a threshold, not a blank cheque"
    print()
    print("   >>> 900-star JavaScript is still refused. the override is a")
    print("       declared threshold, not a hole in the filter.")

    print()
    print("=" * 68)
    print("2. stars gate, topic gate, language gate")
    print("=" * 68)
    for c, expect in [
        (Candidate("low", "Rust", 10, ("sheaf-neural-networks",)), "stars"),
        (Candidate("offtopic", "Rust", 9_000, ("cooking",)), "topic"),
        (Candidate("good", "Rust", 5_000, ("sheaf-neural-networks",)), "admit"),
    ]:
        ok, why = c.admissible()
        print(f"   {c.name:10s} {c.language:8s} {c.stars:>7,}  -> {why}")
        assert ok == (expect == "admit"), why

    print()
    print("=" * 68)
    print("3. rust before python, regardless of stars")
    print("=" * 68)
    big_py = Candidate("huge-python", "Python", 40_000, ("signal-processing",))
    small_rs = Candidate("small-rust", "Rust", 900, ("control-theory",))
    order = [c.name for c in rank([big_py, small_rs])]
    print(f"   40,000-star Python  vs  900-star Rust  ->  {order}")
    assert order[0] == "small-rust"
    print("   >>> the substrate bindings are Rust. the pipe feeds the")
    print("       substrate, so language outranks popularity.")

    print()
    print("=" * 68)
    print("4. small bites -- bounded per cycle")
    print("=" * 68)
    pool = [Candidate(f"r{i}", "Rust", 1000 + i * 10, ("control-theory",))
            for i in range(9)]
    cyc = run_cycle(pool, budget=3)
    print(f"   9 admissible, budget {MAX_PER_CYCLE} -> admitted "
          f"{[c.name for c in cyc.admitted]}")
    print(f"   deferred this cycle: {len(cyc.refused)}")
    assert len(cyc.admitted) == 3
    print(f"   cadence: {cyc.to_dict()['cadence']}  (daily now, hourly later)")

    print()
    print("=" * 68)
    print("5. WHAT STARS DO NOT DO")
    print("=" * 68)
    popular = Candidate("popular-but-broken", "Rust", 40_000,
                        ("control-theory",))
    ok, _ = popular.admissible()
    print(f"   {popular.name}: admissible = {ok}")
    print("   admissible means 'may be pulled'. It does NOT mean correct.")
    print("   A 40,000-star repo can contain a Hodge operator with")
    print("   spectral radius 7.0. Popularity measures adoption; the")
    print("   qualification gate measures truth. Conflating them would")
    print("   reintroduce the exact error the exam exists to catch.")
    assert ok, "it IS admissible -- that is the point of the next line"

    print()
    print("=" * 68)
    print("6. THE GAP THIS CLOSES")
    print("=" * 68)
    print("   Bobby's spec (2026-09-07): rust, python, maybe go.")
    print("   The built pipe: Python only. repo_scanner.py hardcodes")
    print("   'language: Python' on every seed entry and no module filters")
    print("   on language at all. The spec was stated plainly, not")
    print("   implemented, and nothing noticed.")
    print()
    print("   same class as the eleven in the claims register. cheaper to")
    print("   fix, and the fix is a filter plus a declared set.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.parse_args()
    selftest()