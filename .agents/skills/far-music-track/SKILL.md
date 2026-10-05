---
name: far-music-track
description: >-
  far-music — the track schema. 56-axis frozen dataclass with deterministic
  id (sha256(canonical(axes))[:16]) + gate check. Triggers: "music", "track",
  "far-music", "axes".
---

# far-music — the track schema

The track schema is the **gate** for far-music. Without a track_id, an asset is refused at the gate.

## The shape

Every track is a frozen dataclass with a deterministic id:

```python
from far-music.tools.track import compile_track, gate

item = compile_track({"track_axes"})           # compile to frozen record
allow, reason = gate(item, asset_text=...)           # gate check
```

The `id` is `sha256(canonical(axes))` truncated to 16 hex chars. Same axes → same id. Different axes → different id.

## Schema contract

The full axes schema lives in `far-music/AGENTS.md` (the contract). Code in `far-music/tools/track.py` is downstream of the contract — change AGENTS.md first.

## Gate behavior

Default `commit_asset={"gate"}` means the gate checks:

1. `track_id` is set
2. axes are valid (enums enforced)
3. `source_id` is set (for film/music/games)
4. source-discipline: every claim links to a source

Set `commit_asset="forbid"` to refuse unconditionally. Set `commit_asset="allow"` to skip the gate.

## Tests

Every repo has 5 gate tests (M1..M5). Run them to verify the gate is intact:

```bash
python far-music/tests/test_track.py
```

## Public-domain sources

See `far-music/docs/sources.md` for the canonical pd corpora. Every track needs a `source_id` tracing back to a pd source (or the gate refuses).

## See also

- `AGENTS.md` in `far-music/`
- other schema skills (`far-art-sheet`, `far-writing-voice`, `far-film-shot`, `far-music-track`, `far-games-mechanic`)
