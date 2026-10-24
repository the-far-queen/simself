---
name: far-art-shot
description: >-
  far-art — the shot schema for video coverage. 56-axis frozen dataclass
  with deterministic id (sha256(canonical(axes))[:16]) + gate check.
  Triggers: "movie", "shot", "film", "axes".
---

# far-art — the shot schema

The shot schema is the **gate** for video coverage. Without a shot_id, an asset is refused at the gate.

It lived in the far-film repo until 2026-10-24, when that repo was deleted.
The schema moved to `far-art/tools/shot.py` — video is the writing again in
a different container, and far-art is the media entity.

## The shape

Every shot is a frozen dataclass with a deterministic id:

```python
from shot import compile_shot, gate

item = compile_shot({"shot_axes"})           # compile to frozen record
allow, reason = gate(item, asset_text=...)           # gate check
```

The `id` is `sha256(canonical(axes))` truncated to 16 hex chars. Same axes → same id. Different axes → different id.

## Schema contract

The full axes schema lives in `far-art/AGENTS.md` (the contract, under "The shot schema"). Code in `far-art/tools/shot.py` is downstream of the contract — change AGENTS.md first.

## Gate behavior

Default `commit_asset={"gate"}` means the gate checks:

1. `shot_id` is set
2. axes are valid (enums enforced)
3. `source_id` is set (for film/music/games)
4. source-discipline: every claim links to a source

Set `commit_asset="forbid"` to refuse unconditionally. Set `commit_asset="allow"` to skip the gate.

## Tests

The shot schema has 6 gate tests (F1..F6). Run them to verify the gate is intact:

```bash
python far-art/tests/test_shot.py
```

## Public-domain sources

See `far-art/docs/film-sources.md` for the canonical pd corpora. Every shot needs a `source_id` tracing back to a pd source (or the gate refuses).

## See also

- `AGENTS.md` in `far-art/` (the shot schema section)
- other schema skills (`far-art-sheet`, `far-art-shot`, `far-writing-voice`, `far-music-track`, `far-games-mechanic`)
