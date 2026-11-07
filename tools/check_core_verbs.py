#!/usr/bin/env python3
"""
check_core_verbs.py -- BOBBY'S FIFTEEN CORE VERBS MUST BE BOUND BY
SOMETHING, AND THE COMPOSER MUST BIND.

**AND THE MEASUREMENT THIS EXISTS TO CATCH, MEASURED 2026-11-07:**

    bobby's 15 core verbs, through the CURRENT psb_primitives
    .classify_span:
        go, stop, move              -> admitted        (3 of 15)
        see, make, work, care, love, know, build, conduct, transfer,
        cause, up, left             -> REFUSED as other (12 of 15)

    bobby's 15 core verbs in the MLTR register (416 terms):
        care, love, build, transfer -> present         (4 of 15)
        the other eleven            -> ABSENT

    **THE UNION OF THE TWO CURRENT REGISTRIES COVERED 7 OF 15, AND EIGHT
    OF BOBBY'S OWN CORE VERBS WERE IN NO VOCABULARY ANYWHERE IN THE
    SUBSTRATE.**

**AND `compose()` WAS GONE**, and `compose()` is the engine: Bobby's
method 1644 is *"all words + meanings bounded by primitive set, not
grammar"*, and the composer is what did the bounding.

**SO THE VERBS ARE RESTORED** -- `src/constitutional/core_verbs.py`, from
commit `b8e72bc` (2026-09-12, Bobby's directive), which the 2026-09-16
Grok rewrite removed -- **IN THEIR OWN FILE, AND
`psb_primitives.py` IS NOT TOUCHED**, because the current file's own
docstring says why: *"putting new vocabulary into PRIMITIVES changed
classify_span() and silently weakened the confabulation filter."*

**AND THE CHECK MUST BE ABLE TO GO RED.** The RED version is the one
where `resolve_primitive()` looks only in the table and not in the
related sets -- and that is not a hypothetical: MEASURED 2026-11-07, the
restored `compose()` raised `KeyError('Unknown primitive: move')`
because "move" was only ever a RELATED word of "go", never a primitive.
**A COMPOSER THAT CANNOT USE A RELATED WORD IS NOT BOUNDING THE WORDS,
IT IS BOUNDING THE TABLE.**

Run:
    python tools/check_core_verbs.py
Exit: 0 when all fifteen are bound and the composer binds.
"""
from __future__ import annotations

import os
import pathlib
import sys
from typing import Dict, List

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def primitive_word(p) -> str:
    """The word of a primitive, and the restored class names it
    `symbol` while the current PSB's names it `word` -- so BOTH are
    read and the difference is not a failure."""
    return str(getattr(p, "symbol", None) or getattr(p, "word", ""))


def main() -> int:
    print("=" * 74)
    print("BOBBY'S FIFTEEN CORE VERBS")
    print("=" * 74)
    problems: List[str] = []

    try:
        from constitutional import core_verbs as CV
    except Exception as exc:                        # noqa: BLE001
        print("the core verbs could not be imported: %r" % (exc,))
        print("RED -- the registry is missing")
        return 1

    print("the registry: %d primitives, %d categories"
          % (CV.primitive_count(), len(CV.PSBCategory)))
    for cat in CV.PSBCategory:
        names = [primitive_word(p) for p in CV.primitives_by_category(cat)]
        print("   %-12s %s" % (cat.value, ", ".join(names)))
    print()

    cov = CV.coverage()
    print("  %-12s %-8s %-10s %-10s" % ("the verb", "in the PSB",
                                       "in the core", "in the MLTR"))
    for v, c in cov["the_detail"].items():
        print("  %-12s %-8s %-10s %-10s"
              % (v, "yes" if c["in_psb"] else "no",
                 "yes" if c["in_core"] else "no",
                 "yes" if c["in_mltr"] else "no"))
    print()
    print("  the bound:   %d of %d" % (cov["the_bound"], cov["the_total"]))
    print("  the unbound: %s" % (", ".join(cov["the_unbound"]) or "none"))
    print()

    # -- 1. EVERY VERBOUND ------------------------------------------------
    print("[1] every one of bobby's fifteen is bound by SOMETHING")
    if cov["the_unbound"]:
        problems.append("unbound: %s" % ", ".join(cov["the_unbound"]))
        print("    RED  -- %s is in no vocabulary"
              % ", ".join(cov["the_unbound"]))
    else:
        print("    GREEN -- all %d are bound" % cov["the_total"])

    # -- 2. THE COMPOSER BINDS -------------------------------------------
    print()
    print("[2] the composer binds, and it binds a RELATED word")
    try:
        composed = CV.compose("see", "cause", "move")
        print("    GREEN -- compose(see, cause, move) -> %d primitives"
              % len(composed.primitives))
    except Exception as exc:                        # noqa: BLE001
        problems.append("compose() raised: %r" % (exc,))
        print("    RED  -- compose() raised: %r" % (exc,))

    # -- 3. THE COMPOSITION PATH ------------------------------------------
    print()
    print("[3] the composition path is found")
    try:
        path = CV.find_composition_path("build")
        if path:
            print("    GREEN -- path to 'build': %s" % (path,))
        else:
            problems.append("find_composition_path('build') found nothing")
            print("    RED  -- no path found")
    except Exception as exc:                        # noqa: BLE001
        problems.append("find_composition_path() raised: %r" % (exc,))
        print("    RED  -- find_composition_path() raised: %r" % (exc,))

    # -- 4. THE PSB IS NOT TOUCHED ---------------------------------------
    print()
    print("[4] the PSB's own primitives are NOT the core verbs' home")
    try:
        from constitutional import psb_primitives as PSB
        n = len(PSB.PRIMITIVES)
        print("    the PSB's own table: %d entries" % n)
        if n > 20:
            problems.append("the PSB's table has %d entries -- the core "
                            "verbs have leaked into it" % n)
            print("    RED  -- the core verbs leaked into the PSB")
        else:
            print("    GREEN -- the PSB's table is its own")
    except Exception as exc:                        # noqa: BLE001
        problems.append("the PSB could not be imported: %r" % (exc,))
        print("    RED  -- the PSB could not be imported")

    print()
    print("=" * 74)
    if problems:
        print("RED -- %d problem(s)" % len(problems))
        for p in problems:
            print("   - %s" % p)
        return 1
    print("GREEN -- all fifteen are bound, the composer binds, and the "
          "PSB's own table is untouched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
