"""
test_found_by.py -- the scanner records which topic found each repo.

Bobby, 2026-11-06/07: the FC's hierarchy of timescales, and the second
half of it -- the slow level must be able to decide which QUERY TOPICS
are worth making, not just which repos are worth reading.

**AND THE MISSING LINK WAS MEASURED.** MEASURED 2026-11-07: the
scanner's own loop knows which topic produced each hit -- the topic is
the loop variable -- and the hit was stored WITHOUT it. So the day's
records said "96 topics queried, 199 repos found" and NOTHING said which
topic found which repo.

**AND THAT IS THE MISSING LINK.** The slow level cannot decide which
topics are worth querying if it cannot see which topics produced the
repos that CHANGED. **A LEVEL THAT CANNOT SEE THE CAUSE CANNOT DROP THE
CAUSE.**

**AND WHAT IS BEING PROVEN:**

    1  THE SCANNER RECORDS THE TOPIC, and a repo found by two topics
       carries both -- because a repo that two topics both find is a
       repo both topics would have to keep.
    2  IT SURVIVES THE MANIFEST, and the json, and the loader.
    3  AND IT IS NOT IN THE DIGEST, because the digest is PROVENANCE --
       it says "this repo as observed at THIS scan" -- and the found-by
       set is a property of the QUERY and not of the observation.
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = os.path.join(REPO, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constitutional.repo_scanner import ScannedRepo, scan_from_cache  # noqa: E402
from constitutional.repo_scanner_live import latest_manifest  # noqa: E402


RAW = [{
    "full_name": "a/repo", "stargazers_count": 10, "language": "Python",
    "description": "an agent runtime", "topics": ["agent-runtime", "llm"],
    "found_by": ["agent-runtime", "sheaf"],
}]


# ---------------------------------------------------------------------------
# 1. the scanner records the topic
# ---------------------------------------------------------------------------

def test_the_found_by_survives_scan_from_cache():
    m = scan_from_cache(list(RAW))
    assert m.repos, "the repo was dropped"
    assert m.repos[0].found_by == ("agent-runtime", "sheaf"), m.repos[0].found_by


def test_a_repo_with_no_found_by_is_not_an_error():
    raw = [dict(RAW[0])]
    raw[0].pop("found_by")
    m = scan_from_cache(raw)
    assert m.repos[0].found_by == (), m.repos[0].found_by


def test_the_field_exists_on_the_dataclass():
    """**AND A NEW FIELD ON A FROZEN DATACLASS DEFAULTS TO EMPTY**, so
    every existing construction site keeps working."""
    r = ScannedRepo(full_name="a/b", stars=1, language="",
                    description="", topics=(), scan_ts="", matched="")
    assert r.found_by == ()


# ---------------------------------------------------------------------------
# 2. it survives the manifest, the json, and the loader
# ---------------------------------------------------------------------------

def test_the_manifest_carries_it():
    m = scan_from_cache(list(RAW))
    d = m.to_dict()
    assert d["repos"][0].get("found_by") == ["agent-runtime", "sheaf"], d["repos"][0]


def test_it_survives_json():
    m = scan_from_cache(list(RAW))
    d = json.loads(json.dumps(m.to_dict()))
    assert d["repos"][0].get("found_by") == ["agent-runtime", "sheaf"]


def test_the_loader_restores_it(tmp_path):
    """**AND THE LOADER IS THE OTHER END OF THE SAME ROUND TRIP.**"""
    m = scan_from_cache(list(RAW))
    path = tmp_path / "scan-2026-11-07T00-00-00.json"
    path.write_text(json.dumps(m.to_dict()), encoding="utf-8")
    back = latest_manifest(str(tmp_path))
    assert back is not None, "the loader found nothing"
    assert back.repos[0].found_by == ("agent-runtime", "sheaf"), back.repos[0]


# ---------------------------------------------------------------------------
# 3. it is NOT in the digest
# ---------------------------------------------------------------------------

def test_the_found_by_is_not_in_the_digest():
    """**THE DIGEST IS PROVENANCE** -- it says "this repo as observed at
    THIS scan" -- and the found-by set is a property of the QUERY and not
    of the observation. So two scans of the same repo with different
    found-by sets carry the SAME digest when the stars and the timestamp
    match."""
    a = ScannedRepo(full_name="a/b", stars=10, language="", description="",
                    topics=(), scan_ts="T", matched="simself",
                    found_by=("one",))
    b = ScannedRepo(full_name="a/b", stars=10, language="", description="",
                    topics=(), scan_ts="T", matched="simself",
                    found_by=("one", "two"))
    assert a.digest() == b.digest(), "the found-by set changed the digest"
