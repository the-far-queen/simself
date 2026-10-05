"""
test_dependency_lockfile.py — bundler pattern (wycats) tests.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src" / "constitutional"))

from dependency_lockfile import (  # noqa: E402
    Dependency, LockEntry, Lockfile, Manifest,
    default_manifest, resolve, make_manifest_sha,
)


def test_l1_manifest_is_text():
    m = default_manifest()
    text = m.to_text()
    assert "numpy" in text
    assert "mypy" in text
    print("L1: ok (manifest text)")


def test_l2_lockfile_resolves_manifest():
    m = default_manifest()
    lock = resolve(manifest=m)
    assert len(lock.entries) == len(m.deps)
    for e in lock.entries:
        assert len(e.sha256) == 16  # sha256[:16]
    print(f"L2: ok ({len(lock.entries)} entries resolved)")


def test_l3_lockfile_deterministic():
    m = default_manifest()
    l1 = resolve(manifest=m)
    l2 = resolve(manifest=m)
    assert l1.to_text() == l2.to_text()
    print("L3: ok (deterministic)")


def test_l4_manifest_sha_deterministic():
    m = default_manifest()
    h1 = make_manifest_sha(m.deps)
    h2 = make_manifest_sha(m.deps)
    assert h1 == h2
    assert len(h1) == 16
    print(f"L4: ok (manifest_sha = {h1})")


def test_l5_sorted_entries():
    """lockfile entries are sorted alphabetically by name."""
    m = default_manifest()
    lock = resolve(manifest=m)
    names = [e.name for e in lock.entries]
    assert names == sorted(names), f"not sorted: {names}"
    print(f"L5: ok (sorted: {names})")


def test_l6_dependency_to_manifest():
    d = Dependency(name="foo", version_spec=">=1.0", source="git@github.com:x/y")
    text = d.to_manifest()
    assert "foo" in text and ">=1.0" in text and "git@github.com" in text
    print(f"L6: ok (manifest format)")


def test_l7_lock_entry_from_dep():
    d = Dependency(name="x", version_spec="1.0")
    e = LockEntry.from_dep(d, version="1.0", content=b"hello")
    assert e.name == "x" and e.version == "1.0"
    assert len(e.sha256) == 16
    print(f"L7: ok (sha256[:16] = {e.sha256})")


def main():
    test_l1_manifest_is_text()
    test_l2_lockfile_resolves_manifest()
    test_l3_lockfile_deterministic()
    test_l4_manifest_sha_deterministic()
    test_l5_sorted_entries()
    test_l6_dependency_to_manifest()
    test_l7_lock_entry_from_dep()
    print("\\nALL DEPENDENCY_LOCKFILE TESTS PASS (L1..L7)")


if __name__ == "__main__":
    main()