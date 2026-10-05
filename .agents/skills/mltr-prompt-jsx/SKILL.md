---
name: mltr-prompt-jsx
description: >-
  Use when the user wants to compose prompts as a tree (not a string), where each node
  is a typed primitive and the tree is validated against the MLTR schema before
  submission. Triggers: "prompt tree", "prompt jsx", "composable prompt",
  "typed prompt", "priompt", "MLTR AST".
---

# MLTR Prompt JSX — composable typed prompts

Adopted from @anysphere/priompt (2,855⭐, MIT) — Cursor's prompt-as-JSX pattern.
treat prompts as **typed ASTs**, not strings.

## why

- **typed**: each node is a registered MLTR primitive, validated against schema
- **composable**: nested trees, fragments, conditionals
- **deterministic**: same tree → same prompt → same response (modulo the model)
- **auditable**: the tree is inspectable. you can grep it. you can lint it.
- **serializable**: the tree serializes to JSON. share across agents.

## schema

```python
# conceptual — full Python impl in src/constitutional/mltr_prompt.py

class Node:
    role: str           # system | user | assistant | tool
    tag: str            # MLTR primitive (e.g. "axiom", "evidence", "refusal-check")
    children: List[Node]
    attrs: Dict[str, Any]
```

MLTR primitives (the set of valid tags):

| tag | role | description |
|---|---|---|
| `axiom` | system | a constitutional axiom (e.g. "no deception") |
| `evidence` | user | a piece of supporting evidence |
| `refusal-check` | system | a refusal pattern to test the response against |
| `lemma` | user | a working assumption |
| `constraint` | system | an output constraint (length, format) |
| `context` | user | context the model needs |

## usage

```python
from simself.src.constitutional.mltr_prompt import prompt, Node

tree = prompt(
    Node("system", "axiom", [
        Node("system", "axiom", children=[], attrs={"name": "no-deception"}),
    ]),
    Node("system", "refusal-check", [
        Node("system", "axiom", children=[], attrs={"name": "refuse-if-asked-to-lie"}),
    ]),
    Node("user", "context", [
        Node("user", "evidence", children=[], attrs={"text": "the input"}),
    ]),
    Node("system", "constraint", [
        Node("system", "axiom", children=[], attrs={"name": "max-100-tokens"}),
    ]),
)

# render to flat message array (what the LLM sees)
messages = tree.render()
# [{"role": "system", "content": "[axiom] no-deception [refusal-check] ..."}, ...]

# validate the tree against the MLTR schema
errors = tree.validate()
assert not errors, f"MLTR schema violation: {errors}"
```

## surface

- `prompt(*children) -> Node` — root node with `role=system`, holds the constitutional axioms
- `Node(role, tag, children, attrs)` — single AST node
- `tree.render() -> List[Dict]` — flatten to OpenAI/Anthropic API format
- `tree.validate() -> List[str]` — return schema violations (empty = OK)
- `tree.serialize() -> str` — JSON dump (for sharing)
- `Node.deserialize(s) -> Node` — rebuild from JSON

## status

**not yet implemented.** this skill documents the pattern. next session:
implement `src/constitutional/mltr_prompt.py` with the surface above.

## see also

- `simself/src/constitutional/psb_primitives.py` — the existing PSB primitives
- `simself/src/constitutional/lexicon/ingest.py` — existing lexicon ingest (related)
- @anysphere/priompt — the upstream pattern

---

*adopted 2026-10-06 by hermes (minimax-m3). source: @anysphere/priompt (MIT).*