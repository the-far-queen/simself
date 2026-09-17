# Freeze-gate fork — what we use (2026-09-17)

**Source:** [github.com/Geminatrix/freeze-gate](https://github.com/Geminatrix/freeze-gate)
**Forked to:** `C:\Users\Admin\freeze-gate-fork\` (local)
**Mirror:** `vault/30-art/bobby-forks-2026-09-17/`
**Bobby directive:** "fork utilize what we need"

## What we use

### 1. Freeze manifest schema

**Source:** `freeze-gate/schema/freeze-manifest.schema.json`
**Adopted in:** `simself/schemas/freeze-manifest.schema.json`

This is the JSON Schema for "honest labeling + verifiable manifests"
of a frozen core. SimSelf's Sacred Library + constitutional ground
should emit compatible manifests. The schema covers:
- `manifest_version` (1.0)
- `core` (id, version, frozen_at)
- `labeling` (base_model, modifications, intended_use)
- `provenance` (parent_core, frozen_by)
- `artifacts` (path, sha256, bytes)

**Why useful:** SimSelf's constitutional ground (ψ₀) is exactly a
"frozen core with honest labeling + verifiable manifests." The freeze-gate
schema formalizes this.

### 2. 5-check gate pattern (FG-001..FG-005)

**Source:** `freeze-gate/src/freeze_gate/verify.py`
**Adopted in:** `simself/schemas/freeze-gate-verify-reference.py`

The 5 checks are:
- FG-001: Manifest version is supported
- FG-002: All artifacts present + digests match
- FG-003: Honest labels complete (degrades to WARN if missing)
- FG-004: Provenance chain valid (parent_core declared if frozen)
- FG-005: No tampering since freeze (any byte change = FAIL)

**Why useful:** SimSelf's `constitutional/ground.py` should follow this
pattern. The ψ₀ immutability check = FG-002 + FG-005. The honest-labeling
check = FG-003. The provenance check = FG-004.

### 3. SPEC + NOTES (for the team to read)

**Adopted in:**
- `simself/docs/freeze-gate-SPEC.md` (the full spec)
- `simself/docs/freeze-gate-NOTES.md` (the implementation notes)

**Why:** SimSelf's constitutional ground concept is the same shape as
freeze-gate's frozen core concept. Reading freeze-gate's spec helps the
team design SimSelf's equivalent.

## What we don't use

- **The Python implementation itself** — freeze-gate is a CLI tool for
  freezing model weights / persona files. SimSelf's constitutional
  ground is in-memory at runtime. Different surface.
- **The example `ara-core-example/core/`** — that's Geminatrix's
  example, not relevant to SimSelf directly.
- **The CLI (`cli.py`)** — SimSelf doesn't expose freeze-gate's CLI
  commands; it has its own harness.

## License

MIT (per freeze-gate's LICENSE). Compatible with our MIT repos.

## Provenance

- Upstream: github.com/Geminatrix/freeze-gate (MIT, original)
- Forked: 2026-09-17 by Hermes (per Bobby directive)
- Local: `C:\Users\Admin\freeze-gate-fork\`
- Vault: `vault/30-art/bobby-forks-2026-09-17/`
- SimSelf integration: `simself/schemas/` + `simself/docs/`

## Sister files

- `vault/10-minimax/50-index/notes/geminatrix-fork-review-2026-09-17.md` —
  the original fork review
- `simself/schemas/freeze-manifest.schema.json` — the adopted schema
- `simself/docs/freeze-gate-SPEC.md` — the spec for the team
- `simself/docs/freeze-gate-NOTES.md` — the implementation notes

## Last updated

2026-09-17T10:47:36
