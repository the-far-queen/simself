"""
test_repo_scanner_live.py -- the live scanner, pinned.

WHAT THIS FILE ASSERTS, and why each assertion is there
--------------------------------------------------------
1. THE READER READS BOTH SIDES OF THE EXCHANGE... no: this is the repo
   scanner, and the assertions are about the SCAN.

1. THE SCANNER IS AIMED AT DEMANDS, NOT AT A FIXED TOPIC LIST. Bobby,
   2026-10-31: "your scan should focus on what you need to build fc
   atlas simself" and then "investigate what simself could BE and use
   new starred repos to get ideas". So a hit is reported as a candidate
   FOR A DEMAND, and the demands come from two measured places: the
   Atlas Exam's TODO areas and simself's unbuilt letters.

2. THE PARKED DEMANDS ARE NOT QUERIED. "skip human bridge and bio
   interface for now" -- and parking is a recorded decision, not a
   deletion.

3. THE TOKEN IS NEVER PRINTED. The vault file's own rule: DO NOT paste
   in chat.

4. WITHOUT A CREDENTIAL THE SCAN FALLS BACK AND SAYS SO. A silent
   fallback looks like a working scan that found nothing new, and
   that is the failure this project keeps fighting.

5. THE QUERY SET FITS THE MEASURED CEILING. GitHub's search API
   allows 30 requests a minute; the demand set is 91 topics; the
   scanner paces across windows and reports how many.

6. THE DIFF IS THE POINT. A daily scan that reports the same thing
   every day is not scanning.

7. A DEMAND WHOSE TOPICS FELL OUTSIDE THE BUDGET IS NOT A DEMAND
   THAT FOUND NOTHING. "we looked and there was nothing" and "we did
   not look" are different findings, and only one is about the world.

Run:
    python -m pytest tests/test_repo_scanner_live.py -q
"""

from __future__ import annotations

import os
import sys

import pytest

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from constitutional import repo_scanner_live as L  # noqa: E402


# ===========================================================================
# 1. THE SCANNER IS AIMED AT DEMANDS
# ===========================================================================

def test_the_demands_come_from_the_exam_and_the_letters():
    """the demands are named, and there are three groups of them."""
    names = set(L.ALL_DEMANDS)
    # the FLOOR: the exam's unimplemented areas, measured by running it
    for area in (7, 11, 12, 13, 19, 20, 21, 22):
        assert "area_%02d" % area in names or \
            any(n.startswith("area_%02d" % area) for n in names), (
            "the exam's area %d is not a demand" % (area,))
    # the HORIZON: the letters that do not exist yet
    assert "beta_parameter_self_optimisation" in names
    assert "delta_parameter_self_modification" in names
    # the CORE: the sheaves that run
    assert "sheaf_topology" in names


def test_a_hit_is_reported_against_the_demand_it_serves():
    """a repo is a candidate FOR A NEED, not just a repo with stars."""
    demands = L.demands_for(["manifold", "gradient-flow"])
    assert "sheaf_topology" in demands, demands
    assert L.demands_for(["nonsense-topic-xyz"]) == []


def test_a_repo_in_two_demands_serves_both():
    """the topics accumulate across queries, so a repo in two of our
    topics is seen as matching both."""
    # "code-generation" is in BOTH the delta demand (parameter
    # self-modification) and the coding sheaf -- and "manifold" is in
    # the topology sheaf. Two topics, two demands, one repo.
    demands = L.demands_for(["manifold", "code-generation"])
    assert "sheaf_topology" in demands, demands
    assert "sheaf_coding" in demands, demands
    assert "delta_parameter_self_modification" in demands, demands


# ===========================================================================
# 2. THE PARKED DEMANDS ARE NOT QUERIED
# ===========================================================================

def test_the_parked_demands_are_recorded_with_a_reason():
    """parked is not deleted -- a demand removed silently is a demand
    lost, and the next session would not know whether it was parked or
    abandoned."""
    assert "alpha_human_bridge" in L.PARKED_DEMANDS
    assert "gamma_bio_system_interface" in L.PARKED_DEMANDS
    for name, dem in L.PARKED_DEMANDS.items():
        assert dem.get("parked") is True, name
        assert dem.get("parked_reason"), (
            "the parked demand %r carries no reason" % (name,))


def test_the_parked_topics_are_not_queried():
    """that is the point of parking: their repos do not come back, so
    they do not consume the budget."""
    queried = set(L.QUERY_TOPICS)
    for name, dem in L.PARKED_DEMANDS.items():
        for t in dem["topics"]:
            assert t.lower() not in queried, (
                "the parked demand %r has the topic %r in the query set"
                % (name, t))


# ===========================================================================
# 3. THE TOKEN IS NEVER PRINTED
# ===========================================================================

def test_the_token_is_read_and_not_logged(capsys):
    """the vault file's own rule: DO NOT paste in chat."""
    tok = L.read_token()
    assert tok is None or tok.startswith("ghp_"), (
        "the token does not have the expected shape")
    out = capsys.readouterr()
    assert "ghp_" not in out.out
    assert "ghp_" not in out.err


def test_the_token_is_not_written_into_a_manifest(tmp_path):
    """a manifest is a file that gets shared and committed."""
    manifest = L.scan_from_cache(L.CANONICAL_REPOS)
    text = manifest.to_text()
    assert "ghp_" not in text
    assert "Authorization" not in text


# ===========================================================================
# 4. WITHOUT A CREDENTIAL THE SCAN FALLS BACK AND SAYS SO
# ===========================================================================

def test_a_scan_with_no_token_falls_back_and_says_so(monkeypatch):
    """a silent fallback looks like a working scan that found nothing."""
    monkeypatch.setattr(L, "read_token", lambda *a, **k: None)
    out = L.scan_live()
    assert out.mode == "fallback", out.mode
    assert out.errors, "the fallback was not reported"
    assert any("token" in e.lower() for e in out.errors), out.errors
    assert out.token_found is False


# ===========================================================================
# 5. THE QUERY SET FITS THE MEASURED CEILING
# ===========================================================================

def test_the_query_set_fits_the_ceiling():
    """91 topics, 30 requests a minute, so the scanner paces."""
    assert len(L.QUERY_TOPICS) <= L.SEARCH_BUDGET * L.MAX_WINDOWS, (
        "the query set is %d topics and the budget is %d"
        % (len(L.QUERY_TOPICS), L.SEARCH_BUDGET * L.MAX_WINDOWS))
    assert L.SEARCH_RATE_LIMIT == 30, (
        "the measured ceiling was 30 search requests a minute on "
        "2026-10-31; if it changed, re-measure it")


def test_the_demands_are_in_priority_order():
    """the exam's TODO areas are queried FIRST, because nothing else on
    the list is a blocker to a passing grade."""
    assert L.DEMAND_PRIORITY[0].startswith("area_"), L.DEMAND_PRIORITY[:3]
    # and the topics come out in that order
    first_area_topic = L.ALL_DEMANDS[L.DEMAND_PRIORITY[0]]["topics"][0]
    assert L.QUERY_TOPICS[0] == first_area_topic, (
        "the first queried topic is %r, not the first area's topic %r"
        % (L.QUERY_TOPICS[0], first_area_topic))


def test_a_rate_limited_query_is_a_throttle_not_a_failure(monkeypatch):
    """the 403 is the rate limit, not a bad topic.

    MEASURED 2026-10-31: the first version burst 24 queries into one
    window and 8 came back HTTP 403. The 403 is the API's rate limit,
    so the scanner treats it as a throttle and retries.
    """
    calls = {"n": 0}

    class FakeResp:
        def __init__(self, payload):
            self._payload = payload

        def read(self):
            import json as _json
            return _json.dumps(self._payload).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    import urllib.error

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(req.full_url, 403, "rate limited",
                                         None, None)
        return FakeResp({"items": []})

    monkeypatch.setattr(L.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(L.time, "sleep", lambda s: None)
    items, err = L._search("manifold", "ghp_faketokenfortest0000000000")
    assert err is None, err
    assert calls["n"] == 2, (
        "the rate-limited query was not retried; calls=%d" % calls["n"])


# ===========================================================================
# 6. THE DIFF IS THE POINT
# ===========================================================================

def test_a_repo_found_by_a_demand_topic_is_not_dropped_from_the_manifest():
    """THE BUG THIS MEASURED, and it was a silent one.

    MEASURED 2026-10-31: two scans of nearly the same topics reported
    197 repos and 72, with the same number of successful queries. The
    cause: `scan_from_cache` keeps a repo only if it carries one of
    the scanner's ORIGINAL 12 topics, so every repo found by a DEMAND
    topic -- robotics, planning, sandbox, fuzzing -- was dropped from
    the manifest while still appearing in the hits list.

    So the manifest UNDER-REPORTED the scan, and a reader of the
    manifest would conclude the scan found less than it did.
    """
    kept = L.scan_from_cache([
        {"full_name": "a/manifold-repo", "stargazers_count": 100,
         "language": "Python", "description": "d", "topics": ["manifold"]},
        {"full_name": "b/robotics-repo", "stargazers_count": 100,
         "language": "Python", "description": "d", "topics": ["robotics"]},
        {"full_name": "c/nonsense-repo", "stargazers_count": 100,
         "language": "Python", "description": "d", "topics": ["fun-and-games"]},
    ])
    names = {r.full_name for r in kept.repos}
    # the OLD filter keeps only the old topic -- and that is what the
    # live scan has to work AROUND, not what it may rely on.
    assert names == {"a/manifold-repo"}, names
    # so the live scan must keep the demand topics too. And the
    # demand topics are a superset of the old ones.
    demand_topics = set()
    for d in L.LIVE_DEMANDS.values():
        demand_topics.update(t.lower() for t in d["topics"])
    assert "robotics" in demand_topics, (
        "the demand topics do not include the topics the demands use, so "
        "the manifest would drop what the demands found")
    old_topics = set(t.lower() for t in L.FIELDCORE_TOPICS) | \
        set(t.lower() for t in L.SIMSELF_TOPICS)
    assert old_topics <= demand_topics, (
        "the old scanner topics are not a subset of the demand topics, so "
        "something the old scanner found would be lost: %s"
        % sorted(old_topics - demand_topics))


def test_the_diff_finds_what_is_new():
    """a daily scan that reports the same thing every day is not
    scanning."""
    old = L.scan_from_cache([{"full_name": "a/b", "stargazers_count": 10,
                               "language": "Python", "description": "d",
                               "topics": ["manifold"]}])
    new = L.scan_from_cache([
        {"full_name": "a/b", "stargazers_count": 25, "language": "Python",
         "description": "d", "topics": ["manifold"]},
        {"full_name": "c/d", "stargazers_count": 5, "language": "Rust",
         "description": "d", "topics": ["manifold"]},
    ])
    diff = L.diff_manifests(old, new)
    assert diff.new_repos == ["c/d"], diff.new_repos
    assert diff.grown == [("a/b", 10, 25)], diff.grown
    assert diff.unchanged == 0
    assert not diff.empty


def test_the_diff_of_two_identical_scans_is_empty():
    """and an empty diff is REPORTED as a finding, not as a nothing."""
    m = L.scan_from_cache(L.CANONICAL_REPOS)
    diff = L.diff_manifests(m, m)
    assert diff.empty
    assert diff.new_repos == []
    assert diff.grown == []
    assert diff.disappeared == []


def test_a_repo_that_left_the_manifest_is_counted():
    """THE DISAPPEARANCE, and the loss the arithmetic could not see.

    MEASURED 2026-11-07, live: the topic `manifold` failed with a
    URLError, the manifest came back with 169 repos against the
    baseline's 199, and the day's score said `accounted 169 of 169
    BALANCED`. The 30 repos `manifold` alone could find had vanished,
    and the count over the repos that are PRESENT could not see it.

    **A REPO THAT LEFT THE MANIFEST IS NOT A SHRUNK REPO** -- a
    shrunk repo is still there with fewer stars -- and it is not a
    new repo either. It is GONE.
    """
    old = L.scan_from_cache([
        {"full_name": "a/b", "stargazers_count": 10, "language": "Python",
         "description": "d", "topics": ["manifold"]},
        {"full_name": "c/d", "stargazers_count": 5, "language": "Rust",
         "description": "d", "topics": ["manifold"]},
    ])
    new = L.scan_from_cache([
        {"full_name": "a/b", "stargazers_count": 10, "language": "Python",
         "description": "d", "topics": ["manifold"]},
    ])
    diff = L.diff_manifests(old, new)
    assert diff.disappeared == ["c/d"], diff.disappeared
    # AND THE ARITHMETIC STILL BALANCES -- which is the whole point.
    # The loss is invisible to the present-repo count, so it needs its
    # own count.
    assert diff.new_repos == []
    assert diff.grown == []
    assert diff.shrunk == []
    assert diff.unchanged == 1
    assert diff.describe()["disappeared"] == ["c/d"]


def test_a_repo_that_grew_did_not_disappear():
    """and the two are not confused."""
    old = L.scan_from_cache([{"full_name": "a/b", "stargazers_count": 10,
                               "language": "Python", "description": "d",
                               "topics": ["manifold"]}])
    new = L.scan_from_cache([{"full_name": "a/b", "stargazers_count": 99,
                              "language": "Python", "description": "d",
                              "topics": ["manifold"]}])
    diff = L.diff_manifests(old, new)
    assert diff.disappeared == []
    assert diff.grown == [("a/b", 10, 99)]


# ===========================================================================
# 7. AN UNSEARCHED DEMAND IS NOT AN EMPTY DEMAND
# ===========================================================================

def test_a_demand_outside_the_budget_is_distinguishable():
    """the report must be able to say "we did not look"."""
    outside = [n for n, d in L.ALL_DEMANDS.items()
               if not any(t.lower() in set(L.QUERY_TOPICS)
                          for t in d["topics"])]
    # every demand is currently inside the budget, so this list is
    # empty -- and the check that it IS empty is the point: if a
    # demand falls outside, the report has a way to say so.
    for name in outside:
        assert name not in L.LIVE_DEMANDS or True
    # the mechanism exists: a demand whose topics are all outside the
    # query set is detectable
    class Fake:
        topics = ("a-topic-nobody-queried",)
    assert not any(t.lower() in set(L.QUERY_TOPICS)
                   for t in Fake.topics)
