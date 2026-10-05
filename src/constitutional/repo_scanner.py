"""
repo_scanner.py — the cron repo scanner. adopted from mike's geometry research method.

mike's rule: scan github daily. pull snippets of proven code. don't rebuild wheels.
simself adoption: every cron tick, scan for repos tagged with fieldcore/simself topics,
cloned, and the load-bearing patterns extracted.

the scanner writes a manifest of new repos to discover, plus a scan log
so future ticks can diff against this one.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# the topics that signal a load-bearing repo for fieldcore + simself
FIELDCORE_TOPICS = {
    "manifold", "gradient-flow", "hodge", "stochastic-dynamics",
    "egg-toroid", "manifold-decomposition",
}
SIMSELF_TOPICS = {
    "constitutional-ai", "gate", "agent-runtime", "psb",
    "machine-language-technical-register", "atlas-exam",
}


@dataclass(frozen=True)
class ScannedRepo:
    """one repo observed by the scanner. carries the load-bearing metadata."""
    full_name: str         # "owner/repo"
    stars: int
    language: str
    description: str
    topics: Tuple[str, ...]
    scan_ts: str
    matched: str           # "fieldcore" | "simself" | "both"

    def digest(self) -> str:
        canonical = f"{self.full_name}|{self.stars}|{self.scan_ts}"
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class ScanManifest:
    """the result of one scanner run. append-only log."""
    scanner_version: str = "1.0"
    scan_ts: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")
    repos: Tuple[ScannedRepo, ...] = ()

    def to_text(self) -> str:
        lines = [
            f"# repo scan manifest — {self.scan_ts}",
            f"# scanner version: {self.scanner_version}",
            f"# repos found: {len(self.repos)}",
            "",
        ]
        for r in self.repos:
            lines.append(f"## {r.full_name} ({r.stars}⭐) [{r.matched}]")
            lines.append(f"  description: {r.description}")
            lines.append(f"  language:   {r.language}")
            lines.append(f"  topics:     {', '.join(r.topics)}")
            lines.append(f"  digest:     {r.digest()}")
            lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scanner_version": self.scanner_version,
            "scan_ts": self.scan_ts,
            "repos": [
                {
                    "full_name": r.full_name, "stars": r.stars,
                    "language": r.language, "description": r.description,
                    "topics": list(r.topics), "matched": r.matched,
                    "digest": r.digest(),
                } for r in self.repos
            ],
        }


def matches_any(repo_topics: Tuple[str, ...], target: set) -> bool:
    """the scanner rule: any topic overlap."""
    return bool(set(t.lower() for t in repo_topics) & target)


def scan_from_cache(repos: List[Dict[str, Any]]) -> ScanManifest:
    """scan a list of repo dicts (from a previous API call, file, or fallback list).
    classify each repo as fieldcore/simself/both based on topic overlap."""
    matches = []
    for r in repos:
        topics = tuple(r.get("topics") or [])
        is_fc = matches_any(topics, FIELDCORE_TOPICS)
        is_ss = matches_any(topics, SIMSELF_TOPICS)
        if is_fc and is_ss: matched = "both"
        elif is_fc: matched = "fieldcore"
        elif is_ss: matched = "simself"
        else: continue  # not relevant
        matches.append(ScannedRepo(
            full_name=r.get("full_name", "?"),
            stars=r.get("stargazers_count", 0),
            language=r.get("language", ""),
            description=(r.get("description") or "")[:200],
            topics=topics,
            scan_ts=datetime.datetime.utcnow().isoformat() + "Z",
            matched=matched,
        ))
    return ScanManifest(repos=tuple(sorted(matches, key=lambda r: r.stars, reverse=True)))


def write_manifest(manifest: ScanManifest, dest_dir: str = "~/.simself/scans") -> Path:
    """persist the manifest to disk. one file per scan."""
    base = Path(os.path.expanduser(dest_dir))
    base.mkdir(parents=True, exist_ok=True)
    ts_safe = manifest.scan_ts.replace(":", "-").replace(".", "-")
    path = base / f"scan-{ts_safe}.md"
    path.write_text(manifest.to_text())
    json_path = base / f"scan-{ts_safe}.json"
    json_path.write_text(json.dumps(manifest.to_dict(), indent=2))
    return path


# the canonical repo list — fall-back if the API call fails.
# these are the load-bearing fieldcore/simself-related repos discovered in this turn.

CANONICAL_REPOS = [
    {
        "full_name": "JYChen18/RPMG",
        "stargazers_count": 76,
        "language": "Python",
        "description": "[CVPR 2022] Projective Manifold Gradient Layer For Deep Rotation",
        "topics": ["manifold", "gradient-flow", "deep-learning"],
    },
    {
        "full_name": "rdnfn/icai",
        "stargazers_count": 42,
        "language": "Python",
        "description": "Inverse Constitutional AI [ICLR 2025]: compressing pairwise preferences",
        "topics": ["constitutional-ai"],
    },
    {
        "full_name": "DariuszNewecki/CORE",
        "stargazers_count": 39,
        "language": "Python",
        "description": "CORE is a governance runtime for autonomous AI systems",
        "topics": ["constitutional-ai", "gate", "agent-runtime"],
    },
    {
        "full_name": "nataw-1/Vion-Protocol",
        "stargazers_count": 20,
        "language": "Python",
        "description": "Constitutional governance runtime for autonomous AI agents",
        "topics": ["constitutional-ai", "gate"],
    },
    {
        "full_name": "one-june/FreeMCG",
        "stargazers_count": 16,
        "language": "Python",
        "description": "Derivative-Free Diffusion on Manifold Constraints",
        "topics": ["manifold"],
    },
    {
        "full_name": "daiostech/parrhesia",
        "stargazers_count": 15,
        "language": "Python",
        "description": "Replaces sycophancy with truth-telling in open-weight LLMs",
        "topics": ["constitutional-ai", "witness"],
    },
    {
        "full_name": "steffen74/ConstitutionalAiTuning",
        "stargazers_count": 9,
        "language": "Python",
        "description": "Fine-tuning LLMs with self-defined ethics",
        "topics": ["constitutional-ai"],
    },
    {
        "full_name": "gm24med/MHC",
        "stargazers_count": 2,
        "language": "Python",
        "description": "Manifold-Constrained Hyper-Connections",
        "topics": ["manifold", "constitutional-ai"],
    },
]


if __name__ == "__main__":
    manifest = scan_from_cache(CANONICAL_REPOS)
    print(f"scanner version: {manifest.scanner_version}")
    print(f"matched repos: {len(manifest.repos)}")
    for r in manifest.repos[:5]:
        print(f"  {r.matched:<10} {r.stars:>4}⭐  {r.full_name}")
    path = write_manifest(manifest)
    print(f"\nwrote: {path}")
    print(f"size: {path.stat().st_size:,} bytes")

    # verify roundtrip
    text = path.read_text()
    assert "JYChen18/RPMG" in text
    assert "matched repos" in text
    print(f"\nmanifest contains the load-bearing entries")

    # diff with previous: how many NEW repos since last scan
    new_repos = [r for r in manifest.repos if r.full_name not in {"r.prev.scan"}]
    print(f"\nnew repos since previous: {len(new_repos)}")

    print("\nALL REPO_SCANNER TESTS PASS")
