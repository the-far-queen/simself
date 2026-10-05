"""
test_shards.py — Shard tests for the 8 constitutional shards.

adopted from jmikedupont2/meta-meme/MonsterManifesto71.md (MIT).
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src" / "constitutional"))

from shards import (  # noqa: E402
    THE_EIGHT_SHARDS, Shard, describe,
)

EXPECTED_AXES = {"boundaries", "coherence", "stability", "routing",
                 "recovery", "authenticity", "norm", "commit_radius"}


def test_s1_eight_shards():
    assert len(THE_EIGHT_SHARDS) == 8
    print("S1: ok (8 shards)")


def test_s2_all_axes_match():
    actual = {s.axis for s in THE_EIGHT_SHARDS}
    assert actual == EXPECTED_AXES, f"expected {EXPECTED_AXES}, got {actual}"
    print("S2: ok (axes match constitution.py)")


def test_s3_each_shard_has_load_bearing_fields():
    for s in THE_EIGHT_SHARDS:
        assert s.emoji and s.muse and s.poetry and s.witness,             f"{s.axis} missing fields"
        assert s.tier in {"Sacred", "Resilient"}
        assert s.symmetry_type and s.realm_of_power
        assert s.fractran_role and s.moonshine_connection
    print("S3: ok (all shards have full fields)")


def test_s4_tier_balance():
    sacred = sum(1 for s in THE_EIGHT_SHARDS if s.tier == "Sacred")
    resilient = sum(1 for s in THE_EIGHT_SHARDS if s.tier == "Resilient")
    assert sacred == 4
    assert resilient == 4
    print("S4: ok (4/4 tier balance)")


def test_s5_describe_by_index():
    for i in range(1, 9):
        s = describe(i)
        assert s.index == i
    print("S5: ok (describe 1..8)")


def test_s6_describe_out_of_range():
    try:
        describe(0)
        assert False
    except ValueError:
        pass
    try:
        describe(9)
        assert False
    except ValueError:
        pass
    print("S6: ok (out-of-range raises)")


def test_s7_no_duplicate_axes():
    axes = [s.axis for s in THE_EIGHT_SHARDS]
    assert len(axes) == len(set(axes)), "duplicate axes"
    print("S7: ok (no duplicates)")


def test_s8_unique_emojis():
    emojis = [s.emoji for s in THE_EIGHT_SHARDS]
    assert len(emojis) == len(set(emojis)), "duplicate emojis"
    print("S8: ok (unique emojis)")


def main():
    test_s1_eight_shards()
    test_s2_all_axes_match()
    test_s3_each_shard_has_load_bearing_fields()
    test_s4_tier_balance()
    test_s5_describe_by_index()
    test_s6_describe_out_of_range()
    test_s7_no_duplicate_axes()
    test_s8_unique_emojis()
    print("\nALL SHARDS TESTS PASS (S1..S8)")


if __name__ == "__main__":
    main()
