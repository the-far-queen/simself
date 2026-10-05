---
name: far-writing-voice
description: >-
  far-writing — the voice schema. 56-axis frozen dataclass with deterministic
  id (sha256(canonical(axes))[:16]) + gate check. Triggers: "writing", "voice",
  "far-writing", "axes".
---

# far-writing — the voice schema

The voice schema is the **gate** for far-writing. Without a voice_id, an asset is refused at the gate.

## The shape

Every voice is a frozen dataclass with a deterministic id:

```python
from far-writing.tools.voice import compile_voice, gate

item = compile_voice({"voice_axes"})           # compile to frozen record
allow, reason = gate(item, asset_text=...)           # gate check
```

The `id` is `sha256(canonical(axes))` truncated to 16 hex chars. Same axes → same id. Different axes → different id.

## Schema contract

The full axes schema lives in `far-writing/AGENTS.md` (the contract). Code in `far-writing/tools/voice.py` is downstream of the contract — change AGENTS.md first.

## Gate behavior

Default `commit_asset={"gate"}` means the gate checks:

1. `voice_id` is set
2. axes are valid (enums enforced)
3. `source_id` is set (for film/music/games)
4. source-discipline: every claim links to a source

Set `commit_asset="forbid"` to refuse unconditionally. Set `commit_asset="allow"` to skip the gate.

## Tests

Every repo has 5 gate tests (W1..W5). Run them to verify the gate is intact:

```bash
python far-writing/tests/test_voice.py
```

## Public-domain sources

See `far-writing/docs/sources.md` for the canonical pd corpora. Every voice needs a `source_id` tracing back to a pd source (or the gate refuses).

## See also

- `AGENTS.md` in `far-writing/`
- other schema skills (`far-art-sheet`, `far-writing-voice`, `far-film-shot`, `far-music-track`, `far-games-mechanic`)
