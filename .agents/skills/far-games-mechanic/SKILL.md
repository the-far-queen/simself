---
name: far-games-mechanic
description: >-
  far-games — the mechanic schema. 56-axis frozen dataclass with deterministic
  id (sha256(canonical(axes))[:16]) + gate check. Triggers: "game", "mechanic",
  "far-games", "axes".
---

# far-games — the mechanic schema

The mechanic schema is the **gate** for far-games. Without a mechanic_id, an asset is refused at the gate.

## The shape

Every mechanic is a frozen dataclass with a deterministic id:

```python
from far-games.tools.mechanic import compile_mechanic, gate

item = compile_mechanic({"mechanic_axes"})           # compile to frozen record
allow, reason = gate(item, asset_text=...)           # gate check
```

The `id` is `sha256(canonical(axes))` truncated to 16 hex chars. Same axes → same id. Different axes → different id.

## Schema contract

The full axes schema lives in `far-games/AGENTS.md` (the contract). Code in `far-games/tools/mechanic.py` is downstream of the contract — change AGENTS.md first.

## Gate behavior

Default `commit_asset={"gate"}` means the gate checks:

1. `mechanic_id` is set
2. axes are valid (enums enforced)
3. `source_id` is set (for film/music/games)
4. source-discipline: every claim links to a source

Set `commit_asset="forbid"` to refuse unconditionally. Set `commit_asset="allow"` to skip the gate.

## Tests

Every repo has 5 gate tests (G1..G5). Run them to verify the gate is intact:

```bash
python far-games/tests/test_mechanic.py
```

## Public-domain sources

See `far-games/docs/sources.md` for the canonical pd corpora. Every mechanic needs a `source_id` tracing back to a pd source (or the gate refuses).

## See also

- `AGENTS.md` in `far-games/`
- other schema skills (`far-art-sheet`, `far-writing-voice`, `far-film-shot`, `far-music-track`, `far-games-mechanic`)
