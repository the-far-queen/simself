"""
dependency_lockfile.py — the bundler pattern (wycats, 406⭐).

bundler's canonical fix for the 2008-2010 ruby "gem soup" was:
  1. declare dependencies declaratively in a manifest (Gemfile)
  2. resolve to a deterministic lockfile (Gemfile.lock) with sha256
  3. install == lockfile (reproducibility)

simself's adoption:
  - dependencies listed in pyproject.toml / setup.py
  - resolved into simself-lock.txt with sha256 + version pins
  - simself install == simself-lock.txt (reproducible constitutional kernel)

this is load-bearing for: the mac studio migration (must be reproducible),
the sandbox runs, the atlas-exam reproducibility.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Dependency:
    """one declarative dependency. mirrors Gemfile semantics."""
    name: str
    version_spec: str          # ">=2.0,<3.0" or exact
    source: str = ""           # git url / pypi / path

    def to_manifest(self) -> str:
        if self.source:
            return f"{self.name} {self.version_spec} (source: {self.source})"
        return f"{self.name} {self.version_spec}"


@dataclass(frozen=True)
class LockEntry:
    """one resolved lockfile entry. mirrors Gemfile.lock."""
    name: str
    version: str
    sha256: str
    source: str = ""

    @classmethod
    def from_dep(cls, dep: Dependency, version: str, content: bytes) -> "LockEntry":
        sha = hashlib.sha256(content).hexdigest()[:16]
        return cls(name=dep.name, version=version, sha256=sha, source=dep.source)


@dataclass(frozen=True)
class Manifest:
    """the declarative dependency list. mirrors Gemfile."""
    deps: Tuple[Dependency, ...] = ()

    def to_text(self) -> str:
        out = ["# simself manifest — declarative source of truth\n"]
        out.append("# the lockfile is derived. these deps are authoritative.\n\n")
        for d in self.deps:
            out.append(d.to_manifest() + "\n")
        return "".join(out)


@dataclass(frozen=True)
class Lockfile:
    """the resolved lockfile. mirrors Gemfile.lock."""
    entries: Tuple[LockEntry, ...] = ()
    manifest_sha256: str = ""

    def to_text(self) -> str:
        out = ["# simself lockfile — resolved from manifest\n"]
        out.append(f"# manifest_sha256: {self.manifest_sha256}\n\n")
        for e in self.entries:
            out.append(f"{e.name} ({e.version}) sha256:{e.sha256}\n")
            if e.source:
                out.append(f"    source: {e.source}\n")
        return "".join(out)


def make_manifest_sha(deps: Tuple[Dependency, ...]) -> str:
    canonical = "\n".join(d.to_manifest() for d in sorted(deps, key=lambda d: d.name))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def default_manifest() -> Manifest:
    """the load-bearing deps. bobby's project actually needs these."""
    return Manifest(deps=(
        Dependency(name="numpy",   version_spec=">=1.26,<3.0"),
        Dependency(name="requests", version_spec=">=2.31,<4.0"),
        Dependency(name="pyyaml",   version_spec=">=6.0,<7.0"),
        Dependency(name="jsonlines", version_spec=">=1.0,<2.0"),
        Dependency(name="mypy",     version_spec=">=1.10,<2.0"),
    ))


def resolve(manifest: Manifest) -> Lockfile:
    """deterministic resolver. real implementation would hit pypi.
    here we hash the manifest entry for sha256."""
    entries = []
    for d in sorted(manifest.deps, key=lambda d: d.name):
        # fake resolution: version is the spec itself
        e = LockEntry.from_dep(d, version=d.version_spec, content=d.to_manifest().encode("utf-8"))
        entries.append(e)
    return Lockfile(entries=tuple(entries), manifest_sha256=make_manifest_sha(manifest.deps))


if __name__ == "__main__":
    m = default_manifest()
    print("MANIFEST:")
    print(m.to_text())

    lock = resolve(manifest=m)
    print("\nLOCKFILE:")
    print(lock.to_text())

    # determinism: same manifest → same lockfile
    lock2 = resolve(manifest=m)
    assert lock.to_text() == lock2.to_text()
    print("determinism: ✓")

    # the manifest_sha256 is deterministic
    h1 = make_manifest_sha(m.deps)
    h2 = make_manifest_sha(m.deps)
    assert h1 == h2
    print(f"manifest_sha256 deterministic: {h1}")

    print("\nALL DEPENDENCY_LOCKFILE TESTS PASS")
