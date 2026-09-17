"""
test_mltr.py — PSB catalog + mltr_compile tests.

Catalog tests:
- 30+ primitives loaded
- each primitive has MMM, SNR in [0,1]
- inflections are non-empty tuples
- quality classification is correct

mltr_compile tests:
- known PSB tokens map to PSBs
- non-PSB tokens get the right role
- inflection forms match (e.g. "made" → make)
- case-insensitive lookup
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent / "src" / "tools"
sys.path.insert(0, str(TOOLS))

from psb import PSB_CATALOG, load_catalog, lookup  # noqa: E402
import mltr_compile  # noqa: E402


# ---------------------------------------------------------------------------
# Catalog tests
# ---------------------------------------------------------------------------

def test_catalog_loads():
    catalog = load_catalog()
    assert len(catalog) >= 30
    assert "see" in catalog
    assert "make" in catalog
    assert "cause" in catalog
    assert "up" in catalog
    assert "left" in catalog


def test_each_primitive_has_required_fields():
    for entry in PSB_CATALOG:
        for field in ("psb", "gloss", "inflections", "domain", "mmm", "snr"):
            assert field in entry, f"{entry.get('psb', '?')} missing {field}"
        assert 0.0 <= entry["mmm"] <= 1.0, f"{entry['psb']} mmm={entry['mmm']} out of range"
        assert 0.0 <= entry["snr"] <= 1.0, f"{entry['psb']} snr={entry['snr']} out of range"
        assert len(entry["inflections"]) >= 1, f"{entry['psb']} has no inflections"


def test_inflections_lowercase_strings():
    for entry in PSB_CATALOG:
        for infl in entry["inflections"]:
            assert isinstance(infl, str)
            assert infl == infl.lower(), f"{entry['psb']} inflection {infl!r} not lowercase"


def test_quality_classification():
    catalog = load_catalog()
    # see is load_bearing (snr=0.95, mmm=0.4)
    assert catalog["see"].quality == "load_bearing"
    # be is borderline (snr=0.70)
    assert catalog["be"].quality == "borderline"
    # say is borderline (snr=0.85 — actually load_bearing at exactly 0.85)
    # Check: mmm=0.6, snr=0.85 → load_bearing (snr >= 0.85 and mmm <= 0.6)
    assert catalog["say"].quality == "load_bearing"


def test_lookup_canonical():
    catalog = load_catalog()
    psb = lookup("make", catalog)
    assert psb is not None
    assert psb.psb == "make"


def test_lookup_inflection():
    catalog = load_catalog()
    psb = lookup("made", catalog)
    assert psb is not None
    assert psb.psb == "make"


def test_lookup_case_insensitive():
    catalog = load_catalog()
    psb = lookup("MADE", catalog)
    assert psb is not None
    assert psb.psb == "make"


def test_lookup_miss():
    catalog = load_catalog()
    psb = lookup("xyzzy", catalog)
    assert psb is None


# ---------------------------------------------------------------------------
# mltr_compile tests
# ---------------------------------------------------------------------------

def test_compile_simple_span():
    triples = mltr_compile.compile_span("I made a thing")
    assert len(triples) == 4
    assert triples[0]["psb"] is None and triples[0]["role"] == "pronoun"  # I
    assert triples[1]["psb"] == "make" and triples[1]["domain"] == "creation"  # made
    assert triples[2]["psb"] is None and triples[2]["role"] == "article"  # a
    assert triples[3]["psb"] is None and triples[3]["role"] == "noun-or-unknown"  # thing


def test_compile_godot_primitive():
    # Bobby's godot primitives
    for verb in ["go", "stop", "wait", "come", "look", "listen"]:
        triples = mltr_compile.compile_span(verb)
        assert triples[0]["psb"] == verb, f"{verb!r} did not map to {verb}"


def test_compile_robot_arm_primitive():
    # Bobby's robot-arm primitives
    for verb in ["cause", "move", "up", "left"]:
        triples = mltr_compile.compile_span(verb)
        assert triples[0]["psb"] == verb, f"{verb!r} did not map to {verb}"


def test_compile_lexical_primitives():
    for verb in ["see", "make", "work", "care", "love", "know", "build", "conduct", "transfer"]:
        triples = mltr_compile.compile_span(verb)
        assert triples[0]["psb"] == verb, f"{verb!r} did not map to {verb}"


def test_compile_function_words_have_role():
    triples = mltr_compile.compile_span("the cat sat on the mat")
    roles = [t["role"] for t in triples]
    assert "article" in roles  # the
    assert "preposition" in roles  # on
    # sat is "verb-out-of-schema" (snr < 0.85 in our catalog, but we have it via "set"? no)
    # actually "sat" is past of "sit" — not in schema. Should be noun-or-unknown or verb-out-of-schema.
    assert "noun-or-unknown" in roles  # cat, mat


def test_compile_punctuation_attached():
    triples = mltr_compile.compile_span("I made it.")
    # The last token should keep its trailing period and still classify
    assert triples[-1]["token"] == "it."
    assert triples[-1]["psb"] is None
    assert triples[-1]["role"] == "pronoun"


def test_compile_empty_span():
    triples = mltr_compile.compile_span("")
    assert triples == []


def test_compile_multi_sentence():
    triples = mltr_compile.compile_span("She sees him. He builds it.")
    # Just check no crash and reasonable classification
    psbs = [t["psb"] for t in triples if t["psb"]]
    assert "see" in psbs
    assert "build" in psbs


# ---------------------------------------------------------------------------
# Schema invariants
# ---------------------------------------------------------------------------

def test_no_duplicate_canonical_names():
    names = [p["psb"] for p in PSB_CATALOG]
    assert len(names) == len(set(names)), f"duplicate PSB names: {[n for n in names if names.count(n) > 1]}"


def test_no_inflection_collisions_across_primitives():
    catalog = load_catalog()
    infl_to_psb = {}
    for psb in catalog.values():
        for infl in psb.inflections:
            if infl in infl_to_psb:
                # Allow if same PSB (would be weird but legal)
                assert infl_to_psb[infl] == psb.psb, \
                    f"inflection {infl!r} claimed by both {infl_to_psb[infl]} and {psb.psb}"
            infl_to_psb[infl] = psb.psb


def test_schema_quality_distribution():
    catalog = load_catalog()
    counts = {"load_bearing": 0, "specialist": 0, "borderline": 0}
    for psb in catalog.values():
        counts[psb.quality] += 1
    # Most PSBs should be load_bearing (the schema's whole point)
    assert counts["load_bearing"] >= 20, f"too few load_bearing: {counts}"
    # Borderline PSBs should be a small minority
    assert counts["borderline"] <= 5, f"too many borderline: {counts}"
