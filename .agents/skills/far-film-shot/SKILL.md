---
name: far-film-shot
description: >-
  far-film — the shot schema. 56-axis frozen dataclass with deterministic
  id (sha256(canonical(axes))[:16]) + gate check. Triggers: "movie", "shot",
  "far-film", "axes".
---

# far-film — the shot schema

The shot schema is the **gate** for far-film. Without a shot_id, an asset is refused at the gate.

## The shape

Every shot is a frozen dataclass with a deterministic id:

```python
from far-film.tools.shot import compile_shot, gate

item = compile_shot({"shot_axes"})           # compile to frozen record
allow, reason = gate(item, asset_text=...)           # gate check
```

The `id` is `sha256(canonical(axes))` truncated to 16 hex chars. Same axes → same id. Different axes → different id.

## Schema contract

The full axes schema lives in `far-film/AGENTS.md` (the contract). Code in `far-film/tools/shot.py` is downstream of the contract — change AGENTS.md first.

## Gate behavior

Default `commit_asset={"gate"}` means the gate checks:

1. `shot_id` is set
2. axes are valid (enums enforced)
3. `source_id` is set (for film/music/games)
4. source-discipline: every claim links to a source

Set `commit_asset="forbid"` to refuse unconditionally. Set `commit_asset="allow"` to skip the gate.

## Tests

Every repo has 5 gate tests (F1..F5). Run them to verify the gate is intact:

```bash
python far-film/tests/test_shot.py
```

## Public-domain sources

See `far-film/docs/sources.md` for the canonical pd corpora. Every shot needs a `source_id` tracing back to a pd source (or the gate refuses).

## See also

- `AGENTS.md` in `far-film/`
- other schema skills (`far-art-sheet`, `far-writing-voice`, `far-film-shot`, `far-music-track`, `far-games-mechanic`)
