"""
test_constitution_owl.py — verify the OWL file parses and the 8 axes are present.

Source: jmikedupont2/gcc-ontology (MIT) — OWL/RDF pattern for tool structure.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
OWL = HERE / "ontology" / "constitution.owl"

AXES = ["boundaries", "coherence", "stability", "routing", "recovery",
        "authenticity", "norm", "commit_radius"]

ATLAS_ITEMS = ["constitutional_integrity", "gate_behavior", "persistence",
               "recovery_atlas", "mltr_coverage"]


def test_owl_file_exists():
    assert OWL.is_file(), f"missing {OWL}"
    print(f"O1: ok ({OWL.stat().st_size:,} bytes)")


def test_owl_is_xml():
    """OWL is XML/RDF. Check the prolog and root element."""
    text = OWL.read_text()
    assert text.startswith("<?xml"), "must start with <?xml prolog"
    assert "<rdf:RDF" in text, "must have rdf:RDF root"
    assert "</rdf:RDF>" in text, "must close rdf:RDF"
    print("O2: ok")


def test_owl_namespaces_declared():
    text = OWL.read_text()
    namespaces = re.findall(r'xmlns:(\w+)="([^"]+)"', text)
    assert ("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#") in namespaces
    assert ("owl", "http://www.w3.org/2002/07/owl#") in namespaces
    assert ("rdfs", "http://www.w3.org/2000/01/rdf-schema#") in namespaces
    print(f"O3: ok (namespaces: {[n[0] for n in namespaces]})")


def test_all_8_axes_present():
    """All 8 axes must be NamedIndividuals in the OWL file."""
    text = OWL.read_text()
    missing = [a for a in AXES if f'simself:{a}"' not in text and f'simself:{a}>' not in text]
    assert not missing, f"missing axes: {missing}"
    print(f"O4: ok (8 axes)")


def test_all_5_atlas_items_present():
    """All 5 atlas exam items must be NamedIndividuals."""
    text = OWL.read_text()
    missing = [i for i in ATLAS_ITEMS if f'simself:{i}"' not in text and f'simself:{i}>' not in text]
    assert not missing, f"missing atlas items: {missing}"
    print(f"O5: ok (5 atlas items)")


def test_sacred_vs_resilient_tier():
    """Each axis must declare its tier (Sacred or Resilient)."""
    text = OWL.read_text()
    sacred = ["boundaries", "coherence", "stability", "authenticity"]
    resilient = ["routing", "recovery", "norm", "commit_radius"]
    for a in sacred:
        assert f'simself:{a}">' in text, f"sacred axis {a} missing"
        # find its rdf:type
        idx = text.index(f'simself:{a}"')
        chunk = text[idx:idx+400]
        assert "SacredAxis" in chunk, f"{a} not typed as SacredAxis"
    for a in resilient:
        assert f'simself:{a}"' in text, f"resilient axis {a} missing"
        idx = text.index(f'simself:{a}"')
        chunk = text[idx:idx+400]
        assert "ResilientAxis" in chunk, f"{a} not typed as ResilientAxis"
    print("O6: ok (tier types correct)")


def test_axis_low_high_within_range():
    """Each axis's [low, high] interval must satisfy low < high."""
    text = OWL.read_text()
    intervals = {}
    for a in AXES:
        m = re.search(rf'simself:{a}"[^>]*>.*?</owl:NamedIndividual>', text, re.DOTALL)
        assert m, f"no NamedIndividual block for {a}"
        block = m.group(0)
        low = re.search(r'simself:low[^>]*>([^<]+)', block)
        high = re.search(r'simself:high[^>]*>([^<]+)', block)
        assert low and high, f"{a} missing low/high"
        lo, hi = float(low.group(1)), float(high.group(1))
        assert lo < hi, f"{a}: low={lo} not < high={hi}"
        intervals[a] = (lo, hi)
    print(f"O7: ok (intervals: {intervals})")


def main():
    test_owl_file_exists()
    test_owl_is_xml()
    test_owl_namespaces_declared()
    test_all_8_axes_present()
    test_all_5_atlas_items_present()
    test_sacred_vs_resilient_tier()
    test_axis_low_high_within_range()
    print("\nALL OWL TESTS PASS (O1..O7)")


if __name__ == "__main__":
    main()