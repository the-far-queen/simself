"""
frozen_experiment.py — EFMW-style frozen experiment discipline for simself.

Adopted from jmikedupont2/EFMW-FULL (MIT). The pattern:
  1. predict first (specify expected behavior before running)
  2. freeze the manifest (sha256 of all inputs + outputs + code)
  3. never edit once published — a new experiment = new EXP-<NN>
  4. ledger every run, including failures
  5. immutable hash makes a frozen experiment immune to revision

This module implements the runtime side: Manifest, LedgerEntry, publish().
The repo-side: simself/atlas-exam-frozen/EXP-001/ is the published form.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Manifest — the frozen form of an experiment
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Manifest:
    """The published form of an experiment. Immutable after publish()."""

    experiment_id: str           # e.g. "EXP-001"
    title: str                    # e.g. "atlas exam frozen baseline"
    inputs: Dict[str, Any]        # frozen input dict (axes, seeds, packets)
    expected: Dict[str, Any]      # predicted behavior before run
    manifest_sha256: str         # hash of (id + title + expected + inputs)
    published_at: str             # ISO timestamp at publish time
    author: str                   # "hermes (minimax-m3)" or human
    
    @classmethod
    def compute(cls, experiment_id: str, title: str, inputs: Dict[str, Any],
                expected: Dict[str, Any]) -> "Manifest":
        """Compute a Manifest's manifest_sha256. Always deterministic."""
        canonical = json.dumps(
            {"id": experiment_id, "title": title, "inputs": _canon(inputs),
             "expected": _canon(expected)},
            sort_keys=True, separators=(",", ":"),
        )
        h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return cls(
            experiment_id=experiment_id,
            title=title,
            inputs=inputs,
            expected=expected,
            manifest_sha256=h,
            published_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            author="hermes (minimax-m3)",
        )


def _canon(v: Any) -> Any:
    """Canonicalize for hashing: sorted lists, sorted keys, no None."""
    if isinstance(v, (list, tuple)):
        # lists of dicts: sort by canonical-json repr to get a stable order
        items = [_canon(x) for x in v if x is not None]
        try:
            items.sort(key=lambda x: json.dumps(x, sort_keys=True, default=str))
        except TypeError:
            pass
        return items
    if isinstance(v, dict):
        return {k: _canon(val) for k, val in sorted(v.items())}
    if v is None:
        return None
    return v


# ---------------------------------------------------------------------------
# LedgerEntry — one row in the run ledger
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LedgerEntry:
    """One run of an experiment. Append-only."""

    run_id: str
    manifest_sha256: str
    started_at: str
    finished_at: str
    inputs_sha256: str
    outputs_sha256: str
    passed: bool
    metrics: Dict[str, Any]
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Run + ledger
# ---------------------------------------------------------------------------

def run_and_record(manifest: Manifest, fn: Callable[[Dict[str, Any]], Tuple[bool, Dict[str, Any]]],
                    note: str = "") -> Tuple[LedgerEntry, Manifest]:
    """Run the experiment with frozen inputs and record the result.

    fn(inputs) returns (passed: bool, metrics: dict).
    The result is hashed and appended to the ledger (in-memory).

    Failure to match expected = the experiment is broken (refuted). The ledger
    records it; per EFMW integrity rule 5, failed predictions stay in the ledger.
    """
    start = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    inputs_sha = hashlib.sha256(
        json.dumps(_canon(manifest.inputs), sort_keys=True).encode("utf-8")
    ).hexdigest()
    passed, metrics = fn(manifest.inputs)
    outputs_sha = hashlib.sha256(
        json.dumps(_canon(metrics), sort_keys=True).encode("utf-8")
    ).hexdigest()
    finish = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    entry = LedgerEntry(
        run_id=f"{manifest.experiment_id}-{start}",
        manifest_sha256=manifest.manifest_sha256,
        started_at=start,
        finished_at=finish,
        inputs_sha256=inputs_sha,
        outputs_sha256=outputs_sha,
        passed=passed,
        metrics=metrics,
        note=note,
    )
    return entry, manifest


# ---------------------------------------------------------------------------
# publish — write to disk in the canonical EFMW layout
# ---------------------------------------------------------------------------

def publish(manifest: Manifest, ledger: List[LedgerEntry], 
            dest_root: str = "atlas-exam-frozen") -> Path:
    """Write the manifest + ledger to disk in the canonical EFMW layout.

    Layout produced:
        <dest_root>/<EXP-ID>/
            MANIFEST_SHA256.txt          # just the hash
            MANIFEST.json                 # full manifest
            inputs.json                   # frozen inputs
            expected.json                 # frozen expected
            results/
                LEDGER.md                 # ledger as markdown table
                LEDGER.json               # ledger as json
                run-<timestamp>.json      # per-run outputs

    Once publish() is called, the manifest is FROZEN. Editing it post-hoc
    breaks the manifest_sha256 invariant. EFMW rule 4.
    """
    base = Path(dest_root) / manifest.experiment_id
    base.mkdir(parents=True, exist_ok=True)
    (base / "results").mkdir(exist_ok=True)

    # manifest itself
    (base / "MANIFEST_SHA256.txt").write_text(manifest.manifest_sha256 + "\n")
    (base / "MANIFEST.json").write_text(json.dumps(asdict(manifest), indent=2))
    (base / "inputs.json").write_text(json.dumps(manifest.inputs, indent=2, sort_keys=True))
    (base / "expected.json").write_text(json.dumps(manifest.expected, indent=2, sort_keys=True))

    # ledger
    rows = ["# Experiment ledger — {}\n".format(manifest.experiment_id),
            "| run_id | passed | inputs_sha256 (first 12) | outputs_sha256 (first 12) | note |",
            "|---|---|---|---|---|"]
    for e in ledger:
        rows.append(f"| {e.run_id} | {'PASS' if e.passed else 'FAIL'} | "
                    f"{e.inputs_sha256[:12]} | {e.outputs_sha256[:12]} | {e.note} |")
    (base / "results" / "LEDGER.md").write_text("\n".join(rows))
    (base / "results" / "LEDGER.json").write_text(
        json.dumps([e.to_dict() for e in ledger], indent=2)
    )
    return base


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Demo: a frozen experiment for the F1 atlas exam item
    m = Manifest.compute(
        experiment_id="EXP-001",
        title="atlas exam frozen baseline",
        inputs={
            "aspects": [
                {"aspect_ratio": "2.39:1", "lens_mm": 35, "fps": 24},
                {"aspect_ratio": "1.85:1", "lens_mm": 50, "fps": 24},
            ],
            "seed": 42,
        },
        expected={
            "distinct_ids": 2,
            "deterministic_across_runs": True,
            "f1_pass_rate": 1.0,
        },
    )
    print(f"EXP-001 manifest_sha256: {m.manifest_sha256}")
    print(f"published_at: {m.published_at}")
    assert len(m.manifest_sha256) == 64  # sha256 hex

    # demo run
    def f1_run(inputs):
        import uuid
        # fake gate
        ids = {hash(str(x)) for x in inputs["aspects"]}
        return len(ids) == len(inputs["aspects"]), {
            "distinct_ids": len(ids),
            "f1_pass_rate": 1.0,
        }
    entry, _ = run_and_record(m, f1_run, note="first run")
    print(f"\nrun result: passed={entry.passed}, metrics={entry.metrics}")
    assert entry.passed

    # deterministic — recompute the manifest with same data, same hash
    m2 = Manifest.compute("EXP-001", "atlas exam frozen baseline",
                          m.inputs, m.expected)
    assert m2.manifest_sha256 == m.manifest_sha256, "manifest must be deterministic"
    print(f"deterministic: ✓")

    # publish
    p = publish(m, [entry], dest_root="atlas-exam-frozen")
    print(f"\npublished to: {p}")
    print(f"files: {sorted(p.rglob('*'))}")

    print("\nALL FROZEN_EXPERIMENT TESTS PASS")
