"""Tests for the growth metrics.

Queue item 5. These two numbers are the measurement of whether the daily
integration loop improves anything. The tests exist mostly to prove the
metrics CAN report bad news, because a growth dashboard that only ever
says "great" is the failure this file is meant to prevent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from research.growth import (  # noqa: E402
    fmt, measure_conversion, measure_latency, report,
)


# --------------------------------------------------------------------- conversion


def test_conversion_counts_add_up():
    c = measure_conversion()
    assert c.examined > 0
    assert (c.integrated + c.refused_on_licence + c.reference_only
            + c.unaccounted()) == c.examined, c.as_dict()


def test_conversion_rate_matches_its_counts():
    c = measure_conversion()
    assert c.conversion_rate == pytest.approx(c.integrated / c.examined)


def test_licence_refusals_are_counted_as_filter_success():
    """A refusal is the licence filter working, not a growth failure. If
    these were counted as failures the metric would punish correct
    behaviour.
    """
    c = measure_conversion()
    assert c.refused_on_licence > 0, c.as_dict()
    assert c.refusal_accuracy > 0.0


def test_selectivity_is_nonzero():
    """openclaw is 391k stars, MIT, and reference-only. If selectivity is
    zero the filter is not discriminating.
    """
    c = measure_conversion()
    assert c.selectivity > 0.0, c.as_dict()


def test_conversion_is_not_perfect():
    """A process that integrated everything has no filter. Assert the
    measured rate is below 1.
    """
    c = measure_conversion()
    assert c.conversion_rate < 1.0, c.as_dict()


def test_conversion_rows_name_every_examined_system():
    c = measure_conversion()
    assert len(c.rows) == c.examined
    for r in c.rows:
        assert r["slug"] and r["verdict"] and r["licence"]


def test_a_gpl_system_is_never_counted_as_integrated():
    c = measure_conversion()
    for r in c.rows:
        if r["licence"] == "GPL-3.0":
            assert r["verdict"] not in ("VENDOR", "ADAPT", "WRAP"), r


# --------------------------------------------------------------------- latency


def _write_queue(tmp_path: Path, items: list[dict]) -> Path:
    for i, d in enumerate(items, 1):
        (tmp_path / f"{i:04d}.json").write_text(json.dumps(d), encoding="utf-8")
    return tmp_path


def test_latency_ignores_unfinished_items(tmp_path):
    _write_queue(tmp_path, [
        {"title": "done", "status": "done",
         "created": "2026-01-01T00:00:00Z", "closed": "2026-01-01T01:00:00Z", "verify": "x"},
        {"title": "open", "status": "open",
         "created": "2026-01-01T00:00:00Z", "closed": "", "verify": "x"},
        {"title": "claimed", "status": "claimed",
         "created": "2026-01-01T00:00:00Z", "closed": "", "verify": "x"},
    ])
    lat = measure_latency(tmp_path)
    assert lat["items"] == 1
    assert lat["median_hours"] == pytest.approx(1.0)


def test_latency_of_a_single_item(tmp_path):
    _write_queue(tmp_path, [
        {"title": "solo", "status": "done",
         "created": "2026-01-01T00:00:00Z", "closed": "2026-01-01T00:30:00Z", "verify": ""}])
    lat = measure_latency(tmp_path)
    assert lat["items"] == 1
    assert lat["median_hours"] == pytest.approx(0.5)
    assert lat["min_hours"] == pytest.approx(0.5)
    assert lat["max_hours"] == pytest.approx(0.5)


def test_median_ignores_a_single_outlier(tmp_path):
    """The reason the median is used: one item open for a week must not
    make every other item look slow.
    """
    _write_queue(tmp_path, [
        {"title": "a", "status": "done",
         "created": "2026-01-01T00:00:00Z", "closed": "2026-01-01T00:10:00Z", "verify": ""},
        {"title": "b", "status": "done",
         "created": "2026-01-01T00:00:00Z", "closed": "2026-01-01T00:10:00Z", "verify": ""},
        {"title": "c", "status": "done",
         "created": "2026-01-01T00:00:00Z", "closed": "2026-01-01T00:20:00Z", "verify": ""},
        {"title": "outlier", "status": "done",
         "created": "2026-01-01T00:00:00Z", "closed": "2026-01-08T00:00:00Z", "verify": ""},
    ])
    lat = measure_latency(tmp_path)
    assert lat["max_hours"] > 100          # the outlier is still visible
    assert lat["median_hours"] < 1.0       # but it does not dominate


def test_latency_reports_stalled_items(tmp_path):
    _write_queue(tmp_path, [
        {"title": "stalled one", "status": "open",
         "created": "2026-01-01T00:00:00Z", "closed": "", "verify": ""},
        {"title": "failed one", "status": "failed",
         "created": "2026-01-01T00:00:00Z", "closed": "", "verify": ""},
    ])
    lat = measure_latency(tmp_path)
    assert len(lat["stalled"]) == 2


def test_latency_of_an_empty_queue(tmp_path):
    lat = measure_latency(tmp_path)
    assert lat["items"] == 0
    assert lat["median_hours"] is None
    assert lat["stalled"] == []


def test_latency_survives_a_corrupt_file(tmp_path):
    (tmp_path / "0001.json").write_text("{not json", encoding="utf-8")
    _write_queue(tmp_path, [])            # no-op, just ensure dir exists
    (tmp_path / "0002.json").write_text(json.dumps({
        "title": "ok", "status": "done",
        "created": "2026-01-01T00:00:00Z", "closed": "2026-01-01T01:00:00Z"}),
        encoding="utf-8")
    lat = measure_latency(tmp_path)
    assert lat["items"] == 1


def test_latency_handles_a_missing_queue(tmp_path):
    lat = measure_latency(tmp_path / "does-not-exist")
    assert lat["items"] == 0
    assert "no queue" in lat["note"]


# --------------------------------------------------------------------- report


def test_report_contains_both_metrics():
    rep = report()
    assert "conversion" in rep and "latency" in rep
    assert "honesty" in rep


def test_report_states_what_the_numbers_do_not_measure():
    """The honesty clause is the load-bearing part. A growth report with no
    caveat is a sales document.
    """
    assert "not the outcome" in report()["honesty"]


def test_formatting_is_readable():
    assert fmt(None) == "n/a"
    assert "min" in fmt(0.5)
    assert "h" in fmt(2.0)
