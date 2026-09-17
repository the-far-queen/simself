"""The gate: verification checks run against a frozen core before it is trusted.

Each check yields a CheckResult with status PASS, WARN, or FAIL. The overall
GateReport verdict is the worst status observed. The check IDs (FG-xxx) are
stable and documented in docs/SPEC.md — do not renumber them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from freeze_gate.manifest import (
    MANIFEST_FILENAME,
    MANIFEST_VERSION,
    hash_file,
)

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"

_SEVERITY = {PASS: 0, WARN: 1, FAIL: 2}


@dataclass
class CheckResult:
    check_id: str
    name: str
    status: str
    detail: str = ""


@dataclass
class GateReport:
    results: list[CheckResult] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        worst = PASS
        for result in self.results:
            if _SEVERITY[result.status] > _SEVERITY[worst]:
                worst = result.status
        return worst

    def add(self, check_id: str, name: str, status: str, detail: str = "") -> None:
        self.results.append(CheckResult(check_id, name, status, detail))


def _check_structure(report: GateReport, manifest: dict) -> bool:
    """FG-001: manifest carries the required top-level shape. Returns False if
    the manifest is too malformed for the remaining checks to run."""
    required = ("manifest_version", "core", "labeling", "provenance", "artifacts")
    missing = [key for key in required if key not in manifest]
    if missing:
        report.add("FG-001", "manifest structure", FAIL, f"missing keys: {', '.join(missing)}")
        return False

    if manifest["manifest_version"] != MANIFEST_VERSION:
        report.add(
            "FG-001",
            "manifest structure",
            FAIL,
            f"unsupported manifest_version {manifest['manifest_version']!r}"
            f" (gate speaks {MANIFEST_VERSION})",
        )
        return False

    core = manifest["core"]
    if not isinstance(core, dict):
        report.add("FG-001", "manifest structure", FAIL, "core block must be an object")
        return False
    core_missing = [key for key in ("id", "version", "frozen_at") if not core.get(key)]
    if core_missing:
        report.add("FG-001", "manifest structure", FAIL, f"core block missing: {', '.join(core_missing)}")
        return False

    if not isinstance(manifest.get("labeling"), dict) or not isinstance(manifest.get("provenance"), dict):
        report.add("FG-001", "manifest structure", FAIL, "labeling and provenance must be objects")
        return False

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        report.add("FG-001", "manifest structure", FAIL, "artifacts must be a non-empty list")
        return False

    report.add("FG-001", "manifest structure", PASS)
    return True


def _check_digests(report: GateReport, manifest: dict, core_dir: Path) -> None:
    """FG-002: every listed artifact exists and its sha256 matches."""
    mismatched, absent = [], []
    for artifact in manifest["artifacts"]:
        path = core_dir / artifact["path"]
        if not path.is_file():
            absent.append(artifact["path"])
        elif hash_file(path) != artifact["sha256"]:
            mismatched.append(artifact["path"])

    if absent or mismatched:
        parts = []
        if absent:
            parts.append(f"missing: {', '.join(absent)}")
        if mismatched:
            parts.append(f"digest mismatch: {', '.join(mismatched)}")
        report.add("FG-002", "artifact digests", FAIL, "; ".join(parts))
    else:
        report.add("FG-002", "artifact digests", PASS, f"{len(manifest['artifacts'])} artifacts verified")


def _check_no_strays(report: GateReport, manifest: dict, core_dir: Path) -> None:
    """FG-003: the core contains nothing beyond what was frozen. A stray file
    means the bundle mutated after freeze, so the freeze guarantee is void."""
    listed = {artifact["path"] for artifact in manifest["artifacts"]}
    strays = [
        path.relative_to(core_dir).as_posix()
        for path in sorted(core_dir.rglob("*"))
        if path.is_file()
        and path.name != MANIFEST_FILENAME
        and path.relative_to(core_dir).as_posix() not in listed
    ]
    if strays:
        report.add("FG-003", "freeze integrity", FAIL, f"unlisted files present: {', '.join(strays)}")
    else:
        report.add("FG-003", "freeze integrity", PASS)


def _unlabeled_fields(labeling: dict) -> list[str]:
    """Return honest-label fields that are absent or empty.

    An empty ``modifications`` list is an explicit "none" claim and is not
    unlabeled. ``base_model`` / ``intended_use`` must be present and non-empty.
    """
    missing: list[str] = []
    if not labeling.get("base_model"):
        missing.append("base_model")
    if labeling.get("modifications") is None:
        missing.append("modifications")
    if not labeling.get("intended_use"):
        missing.append("intended_use")
    return missing


def _check_labeling(report: GateReport, manifest: dict) -> None:
    """FG-004: honest labeling — the required label fields are present and
    non-empty. Missing labels degrade the core to WARN: it may still verify
    byte-for-byte, but it can no longer say what it is."""
    missing = _unlabeled_fields(manifest["labeling"])
    if missing:
        report.add("FG-004", "honest labeling", WARN, f"unlabeled fields: {', '.join(missing)}")
    else:
        report.add("FG-004", "honest labeling", PASS)


def _check_provenance(report: GateReport, manifest: dict) -> None:
    """FG-005: provenance chain is stated. A null parent_core is legitimate
    (a root freeze) but an absent frozen_by leaves no accountable freezer."""
    provenance = manifest["provenance"]
    if not provenance.get("frozen_by"):
        report.add("FG-005", "provenance chain", WARN, "frozen_by is unset; freeze is unattributed")
    else:
        report.add("FG-005", "provenance chain", PASS)


def run_gate(manifest: dict, core_dir: Path) -> GateReport:
    """Run all gate checks against a manifest and its core directory."""
    core_dir = Path(core_dir)
    report = GateReport()

    if not _check_structure(report, manifest):
        return report

    _check_digests(report, manifest, core_dir)
    _check_no_strays(report, manifest, core_dir)
    _check_labeling(report, manifest)
    _check_provenance(report, manifest)
    return report
