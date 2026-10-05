"""
test_mltr_prompt.py — MLTR prompt tree tests.

Mirrors the surface: prompt() / axiom() / evidence() / refusal_check() / lemma() /
constraint() / context() + render() + validate() + serialize() + deserialize().
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src" / "constitutional"))

from mltr_prompt import (  # noqa: E402
    prompt, Prompt, Node, axiom, evidence, refusal_check, lemma, constraint, context,
)


def test_p1_render_minimal():
    """A prompt with one axiom renders."""
    tree = prompt(axiom("no-deception"))
    msgs = tree.render()
    assert len(msgs) == 2  # root + 1 child
    assert msgs[1]["role"] == "system"
    assert "no-deception" in msgs[1]["content"]
    print("P1: ok")


def test_p2_render_all_primitives():
    """All 6 MLTR primitives render correctly."""
    tree = prompt(
        axiom("no-deception"),
        refusal_check("refuse-if-asked-to-lie"),
        evidence("the user is asking for the weather in tokyo"),
        lemma("assume Tokyo is in Japan"),
        constraint("max-100-tokens", value=100),
    )
    msgs = tree.render()
    assert len(msgs) == 6  # root + 5 children
    contents = " ".join(m["content"] for m in msgs)
    for tag in ("axiom", "refusal-check", "evidence", "lemma", "constraint"):
        assert f"[{tag}]" in contents, f"missing {tag}"
    print("P2: ok (6 primitives)")


def test_p3_validate_good_tree():
    """A well-formed tree has no errors."""
    tree = prompt(
        axiom("no-deception"),
        refusal_check("refuse-if-asked-to-lie"),
    )
    assert tree.validate() == []
    print("P3: ok")


def test_p4_validate_bad_axiom_missing_name():
    """An axiom without 'name' attr is flagged."""
    bad = prompt(
        Node(role="system", tag="axiom", attrs=(("description", "no name"),)),
    )
    errs = bad.validate()
    assert any("missing 'name'" in e for e in errs), f"errs: {errs}"
    print(f"P4: ok (caught: {[e for e in errs if 'name' in e]})")


def test_p5_validate_tool_role_requires_tool_name():
    """role=tool without tool_name attr is flagged."""
    bad = prompt(
        Node(role="tool", tag="context", attrs=(("text", "x"),)),
    )
    errs = bad.validate()
    assert any("tool_name" in e for e in errs)
    print(f"P5: ok (caught: {[e for e in errs if 'tool_name' in e]})")


def test_p6_serialize_roundtrip():
    """serialize → deserialize roundtrips losslessly."""
    tree = prompt(
        axiom("no-deception"),
        evidence("the user is asking for the weather in tokyo"),
        constraint("max-100-tokens", value=100),
    )
    s = tree.serialize()
    tree2 = Prompt.deserialize(s)
    assert tree2.render() == tree.render()
    assert tree2.validate() == []
    print("P6: ok")


def test_p7_invalid_role_rejected():
    """Constructing a node with bad role raises."""
    try:
        Node(role="invalid", tag="axiom")
        assert False, "should have raised ValueError"
    except ValueError as e:
        assert "role" in str(e).lower()
    print("P7: ok")


def test_p8_invalid_tag_rejected():
    """Constructing a node with bad tag raises."""
    try:
        Node(role="system", tag="bogus")
        assert False, "should have raised"
    except ValueError:
        pass
    print("P8: ok")


def test_p9_invalid_attr_key_rejected():
    """Attr keys must be alphanumeric + underscore."""
    try:
        Node(role="system", tag="axiom", attrs=(("1bad", "x"),))
        assert False
    except ValueError:
        pass
    print("P9: ok")


def test_p10_nested_tree_renders():
    """A node with children renders recursively."""
    inner = Node(
        role="user", tag="evidence",
        attrs=(("text", "inner"),),
    )
    outer = Node(
        role="system", tag="context",
        children=(inner,),
        attrs=(("text", "outer"),),
    )
    tree = prompt(outer)
    msgs = tree.render()
    rendered = msgs[1]["content"]
    assert "[context]" in rendered
    assert "[evidence]" in rendered
    assert "inner" in rendered
    assert "outer" in rendered
    print(f"P10: ok (nested)")


def main():
    test_p1_render_minimal()
    test_p2_render_all_primitives()
    test_p3_validate_good_tree()
    test_p4_validate_bad_axiom_missing_name()
    test_p5_validate_tool_role_requires_tool_name()
    test_p6_serialize_roundtrip()
    test_p7_invalid_role_rejected()
    test_p8_invalid_tag_rejected()
    test_p9_invalid_attr_key_rejected()
    test_p10_nested_tree_renders()
    print("\nALL MLTR_PROMPT TESTS PASS (P1..P10)")


if __name__ == "__main__":
    main()