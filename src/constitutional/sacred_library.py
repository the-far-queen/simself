"""
sacred_library.py — Non-volatile semantic memory (NVSM) with MVCC version control.

Per Bobby 2026-09-16 directive ("feature rich and you approve grab and
use"): ported from the v6.1 monolith source (grok3.txt). The canonical
SimSelf did not have a curated knowledge store; the monolith did.

Purpose: a single-file append-only knowledge store with:
- Content-addressable storage (SHA256, first 12 chars as filename).
- MVCC-style version tracking (per skill, ordered list).
- Certification levels q0 (untrusted) → q4 (canonical).
- JSON index for human readability.
- Thread-safe (single-writer pattern via lock).

Used by: the substrate when curated knowledge needs to persist (per
Bobby's "sacred library" / "MVCC" schema in the legacy canonical docs).
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Optional


CERTIFICATION_LEVELS = ["q0", "q1", "q2", "q3", "q4"]


class SacredLibraryManager:
    """Non-volatile semantic memory (NVSM).

    Manages growth, versioning, and certification of skills / knowledge
    items. Implements MVCC-style version control.

    Args:
        storage_path: directory where archived items are stored.
    """

    def __init__(self, storage_path: str | Path = "./sacred_library"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.registry_index: dict[str, dict] = {}
        self.versions: dict[str, list[dict]] = {}
        self.current_version: dict[str, int] = {}
        self._lock = threading.Lock()
        self._load_index()

    # ------------------------------------------------------------------
    # Index persistence
    # ------------------------------------------------------------------

    def _index_path(self) -> Path:
        return self.storage_path / "index.json"

    def _load_index(self) -> None:
        p = self._index_path()
        if not p.exists():
            return
        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self.registry_index = data.get("registry", {})
            self.versions = data.get("versions", {})
            self.current_version = data.get("current", {})
        except (OSError, json.JSONDecodeError):
            # Corrupted index; start fresh.
            self.registry_index = {}
            self.versions = {}
            self.current_version = {}

    def _save_index(self) -> None:
        p = self._index_path()
        data = {
            "registry": self.registry_index,
            "versions": self.versions,
            "current": self.current_version,
        }
        with p.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ------------------------------------------------------------------
    # Archive / retrieve
    # ------------------------------------------------------------------

    def archive_skill(
        self,
        skill_name: str,
        code: str,
        cert_level: str = "q0",
    ) -> str:
        """Archive skill with versioning.

        Returns: "archive_success" on success, or "archive_error:<reason>".
        """
        if cert_level not in CERTIFICATION_LEVELS:
            return f"archive_error: invalid_certification {cert_level!r}"

        with self._lock:
            file_hash = hashlib.sha256(code.encode()).hexdigest()[:12]
            filename = f"{skill_name}_{file_hash}.py"
            full_path = self.storage_path / filename

            with full_path.open("w", encoding="utf-8") as f:
                f.write(code)

            self.registry_index[skill_name] = {
                "hash": file_hash,
                "q_level": cert_level,
                "timestamp": time.time(),
                "path": str(full_path),
            }

            if skill_name not in self.versions:
                self.versions[skill_name] = []
                self.current_version[skill_name] = 0

            version_num = len(self.versions[skill_name])
            self.versions[skill_name].append({
                "version": version_num,
                "hash": file_hash,
                "timestamp": time.time(),
                "cert_level": cert_level,
            })
            self.current_version[skill_name] = version_num

            self._save_index()

        print(f"sacred_library: skill {skill_name!r} archived at {cert_level} (v{version_num})")
        return "archive_success"

    def retrieve_skill(
        self,
        skill_name: str,
        version: Optional[int] = None,
    ) -> Optional[str]:
        """Retrieve skill code.

        If version specified, retrieves that version. Otherwise retrieves
        the current version.
        """
        if skill_name not in self.registry_index:
            return None

        if version is not None and skill_name in self.versions:
            if version < len(self.versions[skill_name]):
                version_info = self.versions[skill_name][version]
                filename = f"{skill_name}_{version_info['hash']}.py"
                path = self.storage_path / filename
                if path.exists():
                    return path.read_text(encoding="utf-8")
                return None
            return None

        # Current version.
        info = self.registry_index[skill_name]
        path = Path(info["path"])
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def list_skills(self) -> list[str]:
        return sorted(self.registry_index.keys())

    def versions_of(self, skill_name: str) -> list[dict]:
        return list(self.versions.get(skill_name, []))

    def certification_of(self, skill_name: str) -> Optional[str]:
        info = self.registry_index.get(skill_name)
        if info is None:
            return None
        return info.get("q_level")

    def stats(self) -> dict:
        return {
            "storage_path": str(self.storage_path),
            "n_skills": len(self.registry_index),
            "total_versions": sum(len(v) for v in self.versions.values()),
            "certification_levels": CERTIFICATION_LEVELS,
        }


__all__ = ["SacredLibraryManager", "CERTIFICATION_LEVELS"]
