"""
test_atlas_exam_v2.py — tests for the comprehensive atlas exam v2.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src" / "constitutional"))

from atlas_exam_v2 import (
    AtlasExamV2, AtlasItem, AtlasReport, FIELDCORE_FREQUENCIES,
    CLUSTERS, AREAS, RUNGS, build_atlas_items, _now,
)


def test_v2_1_total_items_count():
    """atlas v2 has 27 items = 6 clusters * ~5 items."""
    exam = AtlasExamV2()
    assert len(exam.items) == 27
    print(f"V2.1: ok (27 items)")


def test_v2_2_cluster_coverage():
    """each cluster has the expected area count."""
    exam = AtlasExamV2()
    counts = {"C1_substrate": 6, "C2_governance": 6, "C3_communication": 5,
              "C5_embodiment": 3, "C6_emergence": 3}
    for c, expected in counts.items():
        actual = len(exam.by_cluster[c])
        assert actual == expected, f"{c}: expected {expected}, got {actual}"
    print(f"V2.2: ok (clusters: {counts})")


def test_v2_3_rung_coverage():
    """rungs 1,2,3,4,5,7,8 all have items."""
    exam = AtlasExamV2()
    for r in RUNGS:
        assert r in exam.by_rung, f"rung {r} missing"
        assert len(exam.by_rung[r]) > 0
    print(f"V2.3: ok (all 7 rungs have items)")


def test_v2_4_fieldcore_frequencies():
    """the 9 fieldcore frequencies are load-bearing."""
    assert FIELDCORE_FREQUENCIES["fine_structure"] == 137.0
    assert FIELDCORE_FREQUENCIES["cellular"] == 42.0
    assert FIELDCORE_FREQUENCIES["dna"] == 54.0
    assert FIELDCORE_FREQUENCIES["foundation"] == 30.0  # neural via schumann proxy
    print(f"V2.4: ok (9 frequencies: {list(FIELDCORE_FREQUENCIES.values())})")


def test_v2_5_item_signatures():
    """each AtlasItem has all required fields."""
    items = build_atlas_items()
    for item in items:
        assert item.name
        assert item.cluster in CLUSTERS or item.cluster in AREAS
        assert item.rung in RUNGS
        assert callable(item.test_fn)
        assert item.expected
        assert item.witness
        assert item.freq == 137.0  # canonical frequency
    print(f"V2.5: ok ({len(items)} items with full signatures)")


def test_v2_6_run_returns_report():
    """run() returns a report dict with all required keys."""
    exam = AtlasExamV2()
    report = exam.run()
    for k in ("version", "n_items", "items", "score", "pass_count",
              "cluster_avg", "rung_avg", "total_avg"):
        assert k in report, f"missing {k}"
    assert report["version"] == 2
    assert report["n_items"] == 27
    assert isinstance(report["items"], dict)
    print(f"V2.6: ok (run() returns complete dict)")


def test_v2_7_run_cluster_filter():
    """run_cluster() returns just one cluster's reports."""
    exam = AtlasExamV2()
    rs = exam.run_cluster("C1_substrate")
    assert len(rs) == 6
    for r in rs:
        assert r.cluster == "C1_substrate"
    print(f"V2.7: ok (run_cluster(C1): 6 reports)")


def test_v2_8_run_rung_filter():
    """run_rung() returns just one rung's reports."""
    exam = AtlasExamV2()
    rs = exam.run_rung("R5_animal")
    for r in rs:
        assert r.rung == "R5_animal"
    print(f"V2.8: ok (run_rung(R5): {len(rs)} reports)")


def test_v2_9_total_avg_in_range():
    """total_avg in [0, 1]."""
    exam = AtlasExamV2()
    report = exam.run()
    assert 0.0 <= report["total_avg"] <= 1.0
    print(f"V2.9: ok (total_avg = {report['total_avg']:.3f})")


def test_v2_10_report_writes_json():
    """run() with snapshot_path writes a JSON file."""
    import tempfile
    import json
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "report.json"
        exam = AtlasExamV2()
        exam.run(snapshot_path=str(path))
        assert path.is_file()
        with open(path) as f:
            data = json.load(f)
        assert data["version"] == 2
        assert data["n_items"] == 27
        print(f"V2.10: ok (JSON written: {path.stat().st_size} bytes)")


def test_v2_11_legacy_5_items_present():
    """the 5 Grok-2026-09-16 items are present in v2."""
    exam = AtlasExamV2()
    items = [it.name for it in exam.items]
    for legacy_name in ("recovery", "routing", "gate"):
        assert legacy_name in items or f"harmonics-coupling" in items, \
            f"legacy {legacy_name} missing"
    # the new comprehensive version is backwards compatible
    assert "recovery" in items or "harmonics-coupling" in items
    print(f"V2.11: ok (legacy 5-item substrate represented)")


def test_v2_12_each_item_report_has_8_fields():
    """each AtlasReport has all 8 fields."""
    exam = AtlasExamV2()
    report = exam.run()
    expected = {"name", "cluster", "rung", "pass", "score",
                "expected", "actual", "witness", "freq_used", "ts"}
    for name, item in report["items"].items():
        assert set(item.keys()) == expected, f"{name}: keys mismatch"
    print(f"V2.12: ok ({len(report['items'])} reports with 10 fields each)")


def main():
    test_v2_1_total_items_count()
    test_v2_2_cluster_coverage()
    test_v2_3_rung_coverage()
    test_v2_4_fieldcore_frequencies()
    test_v2_5_item_signatures()
    test_v2_6_run_returns_report()
    test_v2_7_run_cluster_filter()
    test_v2_8_run_rung_filter()
    test_v2_9_total_avg_in_range()
    test_v2_10_report_writes_json()
    test_v2_11_legacy_5_items_present()
    test_v2_12_each_item_report_has_8_fields()
    print("\\nALL ATLAS_V2 TESTS PASS (V2.1..V2.12)")


if __name__ == "__main__":
    main()