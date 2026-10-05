---
name: constitutional-extension
description: >-
  Use when the user wants to extend simself with a new tool, command, or
  hook. Triggers: "new tool", "add command", "extension", "constitutional
  extension", ".agents/extensions/".
---

# Constitutional extensions (Pi-style extension.ts model)

Adopted from badlogic/pi-mono (MIT). Pi ships the agent as TypeScript you
can read, modify, ship as `.pi/extensions/<name>.ts`. simself adopts the same
shape for the constitutional layer.

## pattern

an extension is a single file in `.agents/extensions/<name>.py` (or `.ts`).
it exposes one or more of:

  - **tools**: callable from the gate (returns `(allow, reason)`)
  - **commands**: invoked by the user (slash commands or skill triggers)
  - **hooks**: lifecycle hooks (pre/post gate, pre/post tick, pre/post save/load)
  - **skills**: SKILL.md files the agent can load on demand

## example: a watcher tool that refuses secret-style reveals

```python
# .agents/extensions/no_secret_reveal.py

from simself.src.constitutional.quantum_collapse import (
    Superposed, Collapsed, Secured, observe_with_witness, is_secure
)
from simself.src.constitutional.pi_tools import gate, ToolCall, WITNESS_REQUIRED

def watch_no_secret_reveal(call: ToolCall) -> tuple[bool, str]:
    """the watch: refuse any tool call that mentions 'secret' or 'token'."""
    forbidden = ["secret", "token", "private_key", "credential"]
    target = call.target.lower()
    for f in forbidden:
        if f in target:
            return False, f"forbidden_term:{f}"
    return gate(call)

def on_pre_tool_call(call: ToolCall) -> tuple[bool, str]:
    """hook: enforce the watch before every tool call."""
    return watch_no_secret_reveal(call)
```

## file layout

```
.agents/extensions/
├── constitutional-extension/SKILL.md       # this file
├── no_secret_reveal.py                     # the watch example
├── mcp_bridge.py                            # the MCP server (step 4)
└── minimal_loop.py                          # the agent loop (step 5)
```

## when to use

any time the user wants to add a new tool or command without modifying
the canonical gate. the extension is opt-in via `.agents/settings.json`
(in Pi) or `.agents/config.json` (in simself — TBD).

## see also

- `simself/src/constitutional/pi_tools.py` — the 4-tool gate
- `simself/src/constitutional/quantum_collapse.py` — the 3-state model
- `badlogic/pi-mono` — the upstream pattern

---

*adopted 2026-10-06 by hermes (minimax-m3). source: badlogic/pi-mono (MIT).*
