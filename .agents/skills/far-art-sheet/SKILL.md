---
name: far-art-sheet
description: >-
  far-art — the sheet schema. 56-axis frozen dataclass with deterministic
  id (sha256(canonical(axes))[:16]) + gate check. Triggers: "art", "sheet",
  "far-art", "axes".
---

# far-art — the sheet schema

The sheet schema is the **gate** for far-art. Without a sheet_id, an asset is refused at the gate.

## The shape

Every sheet is a frozen dataclass with a deterministic id:

```python
from far-art.tools.sheet import compile_sheet, gate

item = compile_sheet({"sheet_axes"})           # compile to frozen record
allow, reason = gate(item, asset_text=...)           # gate check
```

The `id` is `sha256(canonical(axes))` truncated to 16 hex chars. Same axes → same id. Different axes → different id.

## Schema contract

The full axes schema lives in `far-art/AGENTS.md` (the contract). Code in `far-art/tools/sheet.py` is downstream of the contract — change AGENTS.md first.

## Gate behavior

Default `commit_asset={"gate"}` means the gate checks:

1. `sheet_id` is set
2. axes are valid (enums enforced)
3. `source_id` is set (for film/music/games)
4. source-discipline: every claim links to a source

Set `commit_asset="forbid"` to refuse unconditionally. Set `commit_asset="allow"` to skip the gate.

## Tests

Every repo has 5 gate tests (R1..R5). Run them to verify the gate is intact:

```bash
python far-art/tests/test_sheet.py
```

## Public-domain sources

See `far-art/docs/sources.md` for the canonical pd corpora. Every sheet needs a `source_id` tracing back to a pd source (or the gate refuses).

## See also

- `AGENTS.md` in `far-art/`
- other schema skills (`far-art-sheet`, `far-writing-voice`, `far-film-shot`, `far-music-track`, `far-games-mechanic`)
