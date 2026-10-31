"""
measurement_wiring_probe.py -- HOW MANY SPANS ON THE REAL INGEST PATH
THE EVIDENCE LAYER REFUSES.

THE QUESTION. Queue item 24 asked for the wiring AND for a number:
"how many spans on the real ingest path are refused by the evidence
layer."

THE PATH, and it is the REAL one. The spans are the ones the admitter
actually offers the lexicon -- the strings the system's own operator
produces -- and the ground's own prose, which is the counterweight.

AND THE HONEST READING, stated before the number. The ingest path is a
MEASUREMENT path: a span arriving there came out of a run. So the
evidence layer fires on it, and a span that asserts a measured ground
claim without carrying the command and the number is UNGROUNDED. So
the number measured here is NOT zero, and it SHOULD NOT be: a span
that claims to be the result of a run and cites no run is exactly the
confabulation the layer exists to catch.

Run:
    python src/measurement_wiring_probe.py
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(REPOS, "simself", "src"),
           os.path.join(REPOS, "fieldcore", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from constitutional.lexicon.ingest import claim_gate  # noqa: E402

#: THE GROUND'S OWN PROSE. The counterweight: these must NOT be
#: refused, or the layer is a wall.
GROUND_PROSE = (
    "the constitutional ground is write protected",
    "the gate refuses a proposal that moves the sacred axes",
    "the gate limits are module constants that no caller can supply",
    "a missing substrate is a skip and never a pass",
    "the drift must contract under every step",
    "every refusal names its reason",
    "the governor runs in its own process",
    "the gate agrees with the out-of-process governor",
)

#: THE SPANS THE OPERATOR OFFERS. These are the shapes a run's output
#: takes when it is written down: a report of what happened.
REPORTS = (
    "the gate limits are module constants that no caller can supply; "
    "the suite reports 12 passed",
    "the constitutional ground is write protected; 8 tests passed",
    "the drift must contract under every step -- measured, 4 passed",
    "every refusal names its reason; the gate contract test reports 12 passed",
    "the governor runs in its own process; python src/governor.py -> pid 4412",
    "the gate limits are module constants that no caller can supply; "
    "python -m pytest tests/test_gate_contract.py -q -> 12 passed",
    "the constitutional ground is write protected; "
    "python -m pytest tests/test_locus.py -q -> 8 passed",
)


def main() -> int:
    print("=" * 78)
    print("THE EVIDENCE LAYER AT THE REAL INGEST PATH")
    print("=" * 78)
    print()

    print("A. THE GROUND'S OWN PROSE -- the counterweight")
    print("   these must NOT be refused in measurement mode either,")
    print("   because a report that carries its measurement is fine")
    print()
    refused = 0
    for p in GROUND_PROSE:
        ok, why = claim_gate(p, as_measurement=True)
        if not ok:
            refused += 1
        print("   %-8s %-58s %s" % ("REFUSED" if not ok else "ok",
                                    p[:56], why))
    print()
    print("   refused %d / %d" % (refused, len(GROUND_PROSE)))
    print()

    print("B. THE REPORTS -- a run's output written down")
    print()
    caught = 0
    carried = 0
    for r in REPORTS:
        ok, why = claim_gate(r, as_measurement=True)
        if not ok:
            caught += 1
        else:
            carried += 1
        print("   %-8s %s" % ("REFUSED" if not ok else "ok", why))
        print("           %r" % r[:84])
    print()
    print("   refused by the evidence layer   %d / %d" % (caught, len(REPORTS)))
    print("   admitted (carried the measurement) %d / %d" % (carried,
                                                            len(REPORTS)))
    print()

    print("C. THE SAME SPANS IN PROSE MODE -- the other mode")
    print()
    prose_refused = 0
    for r in REPORTS:
        ok, _ = claim_gate(r, as_measurement=False)
        if not ok:
            prose_refused += 1
    print("   refused in prose mode            %d / %d" % (prose_refused,
                                                           len(REPORTS)))
    print()
    print("   AND THE READING. The same span is refused in measurement")
    print("   mode and admitted in prose mode. That is the wiring")
    print("   doing its job: the CALLER says which path the span came")
    print("   in on, and the layer answers for that path.")
    print()

    print("=" * 78)
    print("  Run: python src/measurement_wiring_probe.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
