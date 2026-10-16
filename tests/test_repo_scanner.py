"""
test_repo_scanner.py — area 17 (extraction) had no testable target.

WHY THIS FILE EXISTS (2026-10-16, Hermes).

atlas-exam area 17 reports `constitutional/repo_scanner.py` as UNWIRED —
imports cleanly, zero inbound callers. Unlike area 18 that report was
accurate: this module is fine, it is simply never called.

So this file does NOT wire it into a runtime path. Wiring a GitHub scanner
into a substrate on an autonomous agent's initiative, with network calls and
filesystem writes, is not a call to make unprompted. It writes to
~/.simself/scans and needs credentials to be useful at all.

What this file does is make the module MEASURABLE and its behaviour
pinned, so that when a caller does exist, the properties it relies on are
already known rather than discovered:

  - classification is correct (fieldcore / simself / both / dropped)
  - results are ordered by stars, which is Bobby's SNR criterion
  - a repo matching nothing is dropped rather than recorded as irrelevant
  - the module is import-clean and does not need the network to be exercised

scan_from_cache is the seam that exists for exactly this: it takes a list of
dicts and never touches the network, so the whole classifier is testable
offline. Using it also means these tests do not rate-limit GitHub or need a
token.

WHAT THIS DOES NOT ESTABLISH

That extraction works. That the scanner finds real repos. That anything is
on a runtime path. Area 17 still fails and should.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from constitutional.repo_scanner import (  # noqa: E402
    FIELDCORE_TOPICS,
    SIMSELF_TOPICS,
    ScannedRepo,
    matches_any,
    scan_from_cache,
)


def _repo(name, topics, stars=0, **kw):
    d = {"full_name": name, "topics": list(topics), "stargazers_count": stars}
    d.update(kw)
    return d


def test_matches_any_is_topic_intersection():
    assert matches_any(("hodge", "gate"), FIELDCORE_TOPICS) is True
    assert matches_any(("gate",), FIELDCORE_TOPICS) is False
    assert matches_any((), FIELDCORE_TOPICS) is False


def test_fieldcore_only_repo_is_classified_fieldcore():
    m = scan_from_cache([_repo("a/fc", ["hodge"])])
    assert [r.matched for r in m.repos] == ["fieldcore"]


def test_simself_only_repo_is_classified_simself():
    m = scan_from_cache([_repo("a/ss", ["constitutional-ai"])])
    assert [r.matched for r in m.repos] == ["simself"]


def test_repo_matching_both_is_classified_both():
    """Order matters here: checking fc then ss and returning early would
    misreport every dual-topic repo as fieldcore-only."""
    m = scan_from_cache([_repo("a/both", ["hodge", "constitutional-ai"])])
    assert [r.matched for r in m.repos] == ["both"]


def test_irrelevant_repo_is_dropped_not_recorded():
    """A manifest full of noise is worse than an empty one — the scanner's
    whole value is that a hit means something."""
    m = scan_from_cache([_repo("a/nope", ["cooking", "gardening"])])
    assert m.repos == ()


def test_results_are_ordered_by_stars():
    """Bobby's SNR criterion: reach is the ranking signal."""
    m = scan_from_cache([
        _repo("a/low", ["hodge"], stars=3),
        _repo("a/high", ["gate"], stars=900),
        _repo("a/mid", ["psb"], stars=50),
    ])
    assert [r.stars for r in m.repos] == [900, 50, 3]


def test_manifest_serialises_and_round_trips_the_fields():
    m = scan_from_cache([_repo("a/b", ["hodge"], stars=7,
                               description="x" * 300)])
    d = m.to_dict()
    # No "count" key: the real shape is scanner_version / scan_ts / repos.
    assert sorted(d.keys()) == ["repos", "scan_ts", "scanner_version"]
    assert len(d["repos"]) == 1
    text = m.to_text()
    assert "a/b" in text
    # description is truncated to 200 by the scanner, not carried whole
    assert len(d["repos"][0]["description"]) <= 200


def test_digest_is_stable_and_content_addressed():
    r = ScannedRepo(full_name="a/b", stars=1, language="Python",
                    description="d", topics=("hodge",), scan_ts="T",
                    matched="fieldcore")
    same = ScannedRepo(full_name="a/b", stars=1, language="Python",
                       description="different text", topics=("hodge",),
                       scan_ts="T", matched="fieldcore")
    changed = ScannedRepo(full_name="a/b", stars=2, language="Python",
                          description="d", topics=("hodge",), scan_ts="T",
                          matched="fieldcore")
    # NOTE: digest is a METHOD, not a property. r.digest without parens is a
    # bound method, and two bound methods never compare equal -- so the first
    # version of this test passed for the wrong reason. Calling it is the
    # point: an earlier draft wrote `r.digest == same.digest` and got
    # False==False, i.e. it was asserting that two different bound-method
    # objects are not equal. Call the method.
    assert r.digest() == same.digest(), "digest must ignore description"
    assert r.digest() != changed.digest(), "digest must change with stars"


def test_missing_fields_do_not_raise():
    """A live API response omits fields. The scanner must not be the thing
    that breaks when GitHub changes a payload."""
    m = scan_from_cache([{"full_name": "a/bare"}])
    assert m.repos == ()          # no topics -> not relevant
    m2 = scan_from_cache([{"full_name": "a/x", "topics": ["hodge"]}])
    assert m2.repos[0].stars == 0
    assert m2.repos[0].description == ""


def test_no_network_access_in_the_offline_path():
    """These tests must never rate-limit GitHub or need a token.

    scan_from_cache is the offline seam; this asserts the module does not
    reach out at import or during classification.
    """
    import constitutional.repo_scanner as rs

    src = Path(rs.__file__).read_text(encoding="utf-8")
    for forbidden in ("requests.get", "urlopen", "urllib.request"):
        assert forbidden not in src, (
            f"{forbidden} found in repo_scanner — the offline path must not "
            f"touch the network"
        )