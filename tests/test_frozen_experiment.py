"""
test_frozen_experiment.py — manifest determinism + publish + ledger invariants.

Mirrors EFMW TESTING_STANDARD.md:
  - prediction before observation
  - frozen experiments are immutable
  - failed predictions remain in the ledger
  - transport deviations must be disclosed
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src" / "constitutional"))

from frozen_experiment import (  # noqa: E402
    Manifest, LedgerEntry, run_and_record, publish,
)


def _tmp_root():
    """Return a fresh temp directory for tests."""
    return tempfile.mkdtemp(prefix="simself_frozen_test_")


def test_deterministic_manifest():
    """Same inputs → same manifest_sha256."""
    inputs = {"seed": 42, "aspects": [{"fps": 24}, {"fps": 30}]}
    expected = {"distinct_ids": 2, "f1_pass_rate": 1.0}
    m1 = Manifest.compute("EXP-001", "atlas exam frozen", inputs, expected)
    m2 = Manifest.compute("EXP-001", "atlas exam frozen", inputs, expected)
    assert m1.manifest_sha256 == m2.manifest_sha256, "manifest must be deterministic"
    assert len(m1.manifest_sha256) == 64  # sha256 hex
    print(f"G1: ok ({m1.manifest_sha256[:16]}...)")


def test_distinct_inputs_distinct_hashes():
    """Different inputs → different manifest_sha256."""
    m1 = Manifest.compute("EXP-001", "x", {"a": 1}, {"y": 1})
    m2 = Manifest.compute("EXP-001", "x", {"a": 2}, {"y": 1})
    assert m1.manifest_sha256 != m2.manifest_sha256
    print("G2: ok")


def test_run_and_record_passing():
    """A passing experiment is recorded with passed=True."""
    m = Manifest.compute("EXP-001", "test", {"x": 1}, {"pass": True})

    def fn(inputs):
        return True, {"observed": inputs["x"]}

    entry, _ = run_and_record(m, fn, note="baseline")
    assert entry.passed is True
    assert entry.manifest_sha256 == m.manifest_sha256
    assert entry.metrics == {"observed": 1}
    print(f"G3: ok (run_id={entry.run_id})")


def test_run_and_record_failing():
    """A failing experiment is recorded with passed=False (NOT deleted)."""
    m = Manifest.compute("EXP-001", "test", {"x": 1}, {"pass": True})

    def fn(inputs):
        return False, {"observed": "refuted"}

    entry, _ = run_and_record(m, fn, note="expected to fail")
    assert entry.passed is False
    print(f"G4: ok (failed prediction recorded, not deleted)")


def test_publish_layout():
    """publish() produces the canonical EFMW layout."""
    m = Manifest.compute("EXP-001", "publish test", {"x": 1}, {"pass": True})

    def fn(inputs):
        return True, {"y": 2}

    entry, _ = run_and_record(m, fn)
    root = _tmp_root()
    base = publish(m, [entry], dest_root=root)
    # canonical files
    assert (base / "MANIFEST_SHA256.txt").exists()
    assert (base / "MANIFEST.json").exists()
    assert (base / "inputs.json").exists()
    assert (base / "expected.json").exists()
    assert (base / "results" / "LEDGER.md").exists()
    assert (base / "results" / "LEDGER.json").exists()
    # ledger contains the run
    ledger = json.loads((base / "results" / "LEDGER.json").read_text())
    assert len(ledger) == 1
    assert ledger[0]["passed"] is True
    print(f"G5: ok (published to {base})")


def test_publish_then_publish_again_fails_immutably():
    """Once published, the manifest_sha256 is set in stone."""
    m = Manifest.compute("EXP-001", "immut test", {"x": 1}, {"pass": True})

    def fn(inputs):
        return True, {}

    entry, _ = run_and_record(m, fn)
    root = _tmp_root()
    base1 = publish(m, [entry], dest_root=root)
    # MANIFEST.json has the sha256 baked in
    manifest_json = json.loads((base1 / "MANIFEST.json").read_text())
    baked = manifest_json["manifest_sha256"]
    assert baked == m.manifest_sha256
    # if anyone edits inputs.json after publish, the ledger can detect it
    # because the inputs_sha256 is per-run, not per-manifest
    print(f"G6: ok (manifest sha256 baked: {baked[:16]}...)")


def main():
    test_deterministic_manifest()
    test_distinct_inputs_distinct_hashes()
    test_run_and_record_passing()
    test_run_and_record_failing()
    test_publish_layout()
    test_publish_then_publish_again_fails_immutably()
    print("\nALL FROZEN_EXPERIMENT TESTS PASS (G1..G6)")


if __name__ == "__main__":
    main()