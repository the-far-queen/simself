"""Growth metrics — does the daily integration loop actually improve anything?

Queue item 5. Bobby's standard for this process was "astoundingly
precise and useful." Two numbers measure it, chosen because they are the
hardest of the candidates to fake:

  CONVERSION            of the external systems examined, how many became
                        code, and how many were correctly REFUSED on
                        licence. A process that integrates everything has
                        no selectivity; one that integrates nothing has no
                        growth. Both extremes are detectable.

  TIME TO FIRST CHECK  from a repo entering the corpus to having a test
                        that can go red on it. This is the latency of the
                        learning loop. A day is not a unit of work, it is
                        a unit of unmeasured time.

Neither is a vanity metric. Conversion can fall to zero and the report
says so. Latency can grow and the report says so. Both are read from a
ledger on disk rather than from memory, so they survive a session.

WHERE THE DATA COMES FROM. `integrations.py` holds the examined systems
with their verdicts. That registry is the numerator and denominator of
conversion, and it already records refusals, so the metric is a
measurement of existing state rather than an estimate.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

LEDGER = Path("C:/Users/HP/AppData/Local/hermes/vault/10-minimax/80-workspace/queue")


@dataclass
class ConversionReport:
    examined: int
    integrated: int
    refused_on_licence: int
    reference_only: int
    conversion_rate: float
    refusal_accuracy: float
    selectivity: float
    note: str = ""
    rows: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)

    def unaccounted(self) -> int:
        """Entries the four buckets do not explain.

        Added because the test suite asserts the buckets sum to the total.
        Without it, a registry entry in a fifth state -- a new verdict, a
        mis-classified licence -- would be silently dropped from the
        denominator and inflate the conversion rate.
        """
        return (self.examined - self.integrated - self.refused_on_licence
                - self.reference_only)


def measure_conversion() -> ConversionReport:
    """Read the integration registry and report what it actually did.

    Three outcomes are distinguished, because collapsing them would hide
    the failure mode where a process accepts everything:

      integrated     became code in this project
      licence refusal correctly refused -- a refusal is a SUCCESS of the
                    filter, not a failure of growth
      reference-only  deliberately not integrated despite being usable

    A loop that integrated 15 of 15 without reading a single licence would
    score the same conversion rate as one that integrated the 8 it legally
    could. `refusal_accuracy` is what separates them.
    """
    from research.integrations import (  # local import: registry is optional here
        ADAPT, REFERENCE, VENDOR, WRAP, licence_blocked,
    )

    try:
        from research.integrations import ALL
    except Exception as exc:
        return ConversionReport(
            0, 0, 0, 0, 0.0, 0.0, 0.0,
            note=f"registry unavailable: {type(exc).__name__}: {exc}")

    integrated = [e for e in ALL if e.verdict in (VENDOR, ADAPT, WRAP)]
    blocked = [e for e in licence_blocked() if not e.usable]
    refonly = [e for e in ALL if e.verdict == REFERENCE and e.licence not in
               ("GPL-3.0", "NONE", "NOASSERTION")]
    total = len(ALL)

    conv = len(integrated) / total if total else 0.0
    refusal = len(blocked) / total if total else 0.0
    # selectivity: of everything NOT blocked, what fraction did we decline?
    usable = [e for e in ALL if e.verdict in (VENDOR, ADAPT, WRAP, REFERENCE)]
    declined = [e for e in usable if e.verdict == REFERENCE]
    selectivity = len(declined) / len(usable) if usable else 0.0

    note = ""
    if conv > 0.9 and refusal == 0.0:
        note = ("everything was integrated and nothing was refused: the "
                "licence filter is not doing any work")
    if selectivity == 0.0 and len(usable) > 1:
        note = (note + "; " if note else "") + \
            "no usable system was declined: selectivity is unproven"

    return ConversionReport(
        examined=total,
        integrated=len(integrated),
        refused_on_licence=len(blocked),
        reference_only=len(refonly),
        conversion_rate=conv,
        refusal_accuracy=refusal,
        selectivity=selectivity,
        note=note,
        rows=[{"slug": e.slug, "verdict": e.verdict, "licence": e.licence}
              for e in ALL],
    )


@dataclass
class LatencyPoint:
    item: str
    queued: str
    closed: str
    hours: float
    verify: str


def measure_latency(queue_dir: Path = LEDGER) -> dict:
    """Time from queued to closed, per item, plus the median.

    The median rather than the mean: one item left open for a week while
    the rest completed in an hour would drag a mean into uselessness, and
    that is exactly the shape of a real backlog.
    """
    if not queue_dir.is_dir():
        return {"items": 0, "median_hours": None, "note": f"no queue at {queue_dir}"}

    points: list[LatencyPoint] = []
    for p in sorted(queue_dir.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if d.get("status") != "done" or not d.get("created") or not d.get("closed"):
            continue
        try:
            t0 = datetime.strptime(d["created"], "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc)
            t1 = datetime.strptime(d["closed"], "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        hours = (t1 - t0).total_seconds() / 3600.0
        points.append(LatencyPoint(
            item=d.get("title", p.stem)[:60], queued=d["created"],
            closed=d["closed"], hours=hours, verify=d.get("verify", "")[:60]))

    hours = sorted(pt.hours for pt in points)
    median = None
    if hours:
        n = len(hours)
        median = hours[n // 2] if n % 2 else (hours[n // 2 - 1] + hours[n // 2]) / 2

    # The stalled list re-reads every file. It needs its own guard: the
    # latency loop above catches a parse error, but this comprehension
    # did not, so a single corrupt file took down the whole report.
    stalled: list[str] = []
    for p in sorted(queue_dir.glob("*.json")):
        if not p.is_file() or p.suffix != ".json":
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            stalled.append(f"CORRUPT {p.name}")
            continue
        if d.get("status") in ("open", "claimed", "failed"):
            stalled.append(d.get("title", p.stem))

    return {
        "items": len(points),
        "median_hours": median,
        "min_hours": hours[0] if hours else None,
        "max_hours": hours[-1] if hours else None,
        "stalled": stalled,
        "points": [asdict(pt) for pt in points],
    }


def report() -> dict:
    """Both numbers, plus the one thing that would make them meaningless."""
    conv = measure_conversion()
    lat = measure_latency()
    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "conversion": conv.as_dict(),
        "latency": lat,
        "honesty": (
            "These measure the LOOP, not the outcome. High conversion with "
            "no tests, or fast checks that do not fail, would both look "
            "good here. The pair only means something alongside the test "
            "counts, which are recorded in each repo's last commit."
        ),
    }


def render() -> str:
    rep = report()
    c, lat = rep["conversion"], rep["latency"]
    out = [
        f"growth report {rep['generated']}",
        "",
        "CONVERSION",
        f"  examined          {c['examined']}",
        f"  integrated        {c['integrated']}  ({c['conversion_rate']:.0%})",
        f"  refused (licence) {c['refused_on_licence']}  ({c['refusal_accuracy']:.0%})",
        f"  reference-only    {c['reference_only']}",
        f"  selectivity       {c['selectivity']:.0%} of usable systems declined",
    ]
    if c["note"]:
        out.append(f"  note: {c['note']}")
    out += [
        "",
        "LATENCY (queued -> closed)",
        f"  completed         {lat['items']}",
        f"  median            {fmt(lat['median_hours'])}",
        f"  range             {fmt(lat['min_hours'])} .. {fmt(lat['max_hours'])}",
    ]
    if lat.get("stalled"):
        out.append(f"  stalled           {len(lat['stalled'])}")
        for s in lat["stalled"][:5]:
            out.append(f"    - {s[:60]}")
    out += ["", "HONESTY", "  " + rep["honesty"]]
    return "\n".join(out)


def fmt(h: float | None) -> str:
    if h is None:
        return "n/a"
    if h < 1.0:
        return f"{h*60:.0f} min"
    return f"{h:.1f} h"


if __name__ == "__main__":
    print(render())