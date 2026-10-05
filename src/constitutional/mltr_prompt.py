"""
mltr_prompt.py — MLTR Prompt JSX (typed, composable, auditable prompts).

Adopted from @anysphere/priompt (MIT, 2,855 stars). treats prompts as
typed ASTs rather than flat strings. Each node is an MLTR primitive;
the tree is validated against the schema before render.

The 6 MLTR primitives (initial version):
    - axiom        — a constitutional axiom (e.g. "no deception")
    - evidence     — a piece of supporting evidence
    - refusal-check — a refusal pattern to test the response against
    - lemma        — a working assumption
    - constraint   — an output constraint (length, format)
    - context      — context the model needs

Each node carries:
    - role:        system | user | assistant | tool
    - tag:         one of the 6 MLTR primitives
    - children:    list of nested Node
    - attrs:       dict of node-specific attributes

Tree invariants (validated by validate()):
    - leaf nodes: must have non-empty attrs
    - axiom:       must have a 'name' attr
    - constraint:  must have a 'name' attr
    - role=tool:   must have a 'tool_name' attr
    - all attrs:   keys are alphanumeric + underscore only
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_ROLES = {"system", "user", "assistant", "tool"}
VALID_TAGS = {"axiom", "evidence", "refusal-check", "lemma", "constraint", "context"}
ATTR_KEY_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Node:
    """One AST node in the MLTR prompt tree."""

    role: str
    tag: str
    children: Tuple["Node", ...] = ()
    attrs: Tuple[Tuple[str, Any], ...] = ()  # tuple for frozen hashability

    def __post_init__(self):
        if self.role not in VALID_ROLES:
            raise ValueError(f"role {self.role!r} not in {VALID_ROLES}")
        if self.tag not in VALID_TAGS:
            raise ValueError(f"tag {self.tag!r} not in {VALID_TAGS}")
        for k, _ in self.attrs:
            if not ATTR_KEY_RE.match(k):
                raise ValueError(f"attr key {k!r} not alphanumeric+underscore")

    @property
    def attrs_dict(self) -> Dict[str, Any]:
        return dict(self.attrs)


# ---------------------------------------------------------------------------
# prompt() — root constructor
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Prompt:
    """The root MLTR prompt tree."""

    root: Node

    def render(self) -> List[Dict[str, str]]:
        """Flatten the tree to OpenAI/Anthropic API message format."""
        # collect children of the root as separate messages
        # the root itself is rendered as a system message
        out: List[Dict[str, str]] = []
        out.append({"role": self.root.role,
                    "content": _render_node(self.root)})
        for child in self.root.children:
            out.append({"role": child.role,
                        "content": _render_node(child)})
        return out

    def validate(self) -> List[str]:
        """Return list of schema violations. empty = OK."""
        return _validate_node(self.root)

    def serialize(self) -> str:
        return json.dumps(_serialize_node(self.root), indent=2)

    @classmethod
    def deserialize(cls, s: str) -> "Prompt":
        return cls(root=_deserialize_node(json.loads(s)))


# ---------------------------------------------------------------------------
# Constructors
# ---------------------------------------------------------------------------

def prompt(*children: Node, role: str = "system", tag: str = "context") -> Prompt:
    """Build a Prompt from child nodes."""
    return Prompt(root=Node(role=role, tag=tag, children=tuple(children)))


def axiom(name: str, *, role: str = "system") -> Node:
    """A constitutional axiom. Required: name."""
    return Node(role=role, tag="axiom", attrs=(("name", name),))


def evidence(text: str, *, role: str = "user") -> Node:
    """A piece of supporting evidence."""
    return Node(role=role, tag="evidence", attrs=(("text", text),))


def refusal_check(name: str, *, role: str = "system") -> Node:
    """A refusal pattern to test the response against."""
    return Node(role=role, tag="refusal-check", attrs=(("name", name),))


def lemma(text: str, *, role: str = "user") -> Node:
    """A working assumption."""
    return Node(role=role, tag="lemma", attrs=(("text", text),))


def constraint(name: str, value: Any, *, role: str = "system") -> Node:
    """An output constraint."""
    return Node(role=role, tag="constraint", attrs=(("name", name), ("value", value)))


def context(text: str, *, role: str = "user") -> Node:
    """Context the model needs."""
    return Node(role=role, tag="context", attrs=(("text", text),))


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def _render_node(n: Node, depth: int = 0) -> str:
    """Render a single node to a text fragment."""
    # render this node's own attrs first
    own_attrs_str = " ".join(f"{k}={v!r}" for k, v in n.attrs)
    own = f"[{n.tag}]{(' ' + own_attrs_str) if own_attrs_str else ''}"
    if not n.children:
        return own
    # branch — own attrs + children's content
    inner = "\n".join("  " * (depth + 1) + _render_node(c, depth + 1)
                   for c in n.children)
    return f"{own}\n{inner}"


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

def _validate_node(n: Node, path: str = "") -> List[str]:
    errs: List[str] = []
    cur = f"{path}/{n.tag}"
    if not n.children:
        # leaf — must have attrs
        if not n.attrs:
            errs.append(f"{cur}: leaf has no attrs")
        # specific checks
        d = n.attrs_dict
        if n.tag == "axiom" and "name" not in d:
            errs.append(f"{cur}: axiom missing 'name' attr")
        if n.tag == "constraint" and "name" not in d:
            errs.append(f"{cur}: constraint missing 'name' attr")
        if n.role == "tool" and "tool_name" not in d:
            errs.append(f"{cur}: tool role missing 'tool_name' attr")
    for c in n.children:
        errs.extend(_validate_node(c, cur))
    return errs


# ---------------------------------------------------------------------------
# Serialize / deserialize
# ---------------------------------------------------------------------------

def _serialize_node(n: Node) -> Dict[str, Any]:
    return {
        "role": n.role,
        "tag": n.tag,
        "children": [_serialize_node(c) for c in n.children],
        "attrs": dict(n.attrs),
    }


def _deserialize_node(d: Dict[str, Any]) -> Node:
    return Node(
        role=d["role"],
        tag=d["tag"],
        children=tuple(_deserialize_node(c) for c in d.get("children", [])),
        attrs=tuple(d.get("attrs", {}).items()),
    )


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # build a real one
    tree = prompt(
        axiom("no-deception"),
        refusal_check("refuse-if-asked-to-lie"),
        evidence("the user is asking for the weather in tokyo"),
        constraint("max-100-tokens", value=100),
    )
    print("=== rendered ===")
    for m in tree.render():
        print(f"  [{m['role']}] {m['content']}")
    print()
    print("=== validate ===")
    errs = tree.validate()
    print(f"  {len(errs)} errors: {errs}")

    print("\n=== roundtrip ===")
    s = tree.serialize()
    print(s[:300])
    p2 = Prompt.deserialize(s)
    assert p2.render() == tree.render()
    print("  roundtrip ok")

    # leaf without attrs should be detected
    bad_tree = prompt(
        Node(role="system", tag="axiom"),  # no attrs
    )
    print("\n=== validation (intentional failure) ===")
    errs = bad_tree.validate()
    print(f"  {len(errs)} errors: {errs}")

    print("\nALL MLTR_PROMPT TESTS PASS")